"""Query-aware memory retrieval and injection formatting."""

import logging
import math
from datetime import datetime

from app.agents.memory.constants import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    CATEGORY_QUOTA,
    CONTEXT_MAX_CHARS,
    DOMAIN_MAP,
)
from app.agents.memory.base import MemoryStoreBase

logger = logging.getLogger(__name__)


class MemoryRetrievalMixin:

    @staticmethod
    def _compute_relevance(query: str, mem: dict) -> float:
        if not query:
            return 1.0
        content = (mem.get("content") or "").lower()
        q = query.lower()

        # 内容匹配
        terms: set[str] = set()
        for domain, aliases in DOMAIN_MAP.items():
            if domain in q:
                terms.add(domain)
                terms.update(aliases)
        kw_hit = any(t in content for t in terms) if terms else False
        q_grams = {q[i : i + 2] for i in range(len(q) - 1)} if len(q) >= 2 else {q}
        c_grams = {content[i : i + 2] for i in range(len(content) - 1)} if len(content) >= 2 else {content}
        gram_overlap = len(q_grams & c_grams) / max(1, len(q_grams))
        content_score = max(gram_overlap, 0.75 if kw_hit else 0.0)

        # 重要度
        importance = max(1, min(5, int(mem.get("importance") or 3)))
        importance_score = importance / 5.0

        # 时效
        updated = MemoryStoreBase._safe_parse_dt(mem.get("updated_at"))
        if updated is None:
            recency = 0.5
        else:
            days = max(0, (datetime.now() - updated).days)
            recency = 1.0 if days <= 7 else max(0.25, math.exp(-(days - 7) / 45))

        # 稳定度（被检索次数）
        access = int(mem.get("access_count") or 0)
        stability = min(1.0, access / 8.0)

        score = 0.45 * content_score + 0.20 * importance_score + 0.20 * recency + 0.15 * stability
        return max(0.0, min(1.0, score))

    async def retrieve_for_injection(
        self,
        user_id: int,
        query: str = "",
        category_priority: list[str] | None = None,
        budget_chars: int = CONTEXT_MAX_CHARS,
        max_items: int = 12,
        min_score: float = 0.18,
    ) -> dict:
        memories = await self.get_all(user_id)
        if not memories:
            return {"text": "", "selected": [], "truncated": 0, "total_candidates": 0}

        scored: list[tuple[float, dict]] = []
        for mem in memories:
            score = self._compute_relevance(query, mem)
            if query and score < min_score:
                continue
            scored.append((score, mem))

        if not scored:
            return {"text": "", "selected": [], "truncated": 0, "total_candidates": 0}

        scored.sort(
            key=lambda x: (
                x[0],
                int(x[1].get("importance") or 0),
                x[1].get("updated_at") or "",
            ),
            reverse=True,
        )

        groups: dict[str, list[tuple[float, dict]]] = {c: [] for c in CATEGORY_ORDER}
        for item in scored:
            category = self._normalize_category(item[1].get("category", "fact"))
            groups[category].append(item)

        ordered_categories = []
        if category_priority:
            for cat in category_priority:
                nc = self._normalize_category(cat)
                if nc not in ordered_categories:
                    ordered_categories.append(nc)
        for cat in CATEGORY_ORDER:
            if cat not in ordered_categories:
                ordered_categories.append(cat)

        selected: list[dict] = []
        selected_ids: list[int] = []
        used_chars = 0
        truncated = 0

        for cat in ordered_categories:
            items = groups.get(cat, [])
            if not items:
                continue
            quota = int(budget_chars * CATEGORY_QUOTA.get(cat, 0.25))
            quota = max(60, quota)
            quota_chars = 0

            for score, mem in items:
                text = (mem.get("content") or "").strip()
                if not text:
                    continue
                piece_len = len(text) + 3
                if len(selected) >= max_items or used_chars + piece_len > budget_chars:
                    truncated += 1
                    continue
                if quota_chars + piece_len > quota:
                    truncated += 1
                    continue
                selected.append(
                    {
                        "id": mem.get("id"),
                        "category": cat,
                        "mem_key": mem.get("mem_key"),
                        "content": text,
                        "importance": int(mem.get("importance") or 3),
                        "score": round(score, 4),
                    }
                )
                if mem.get("id") is not None:
                    selected_ids.append(int(mem["id"]))
                used_chars += piece_len
                quota_chars += piece_len

        # 兜底：query 命中过窄时，补充一条最高重要记忆
        if query and not selected:
            top = sorted(memories, key=lambda m: int(m.get("importance") or 0), reverse=True)[:1]
            for mem in top:
                text = (mem.get("content") or "").strip()
                if text:
                    selected.append(
                        {
                            "id": mem.get("id"),
                            "category": self._normalize_category(mem.get("category", "fact")),
                            "mem_key": mem.get("mem_key"),
                            "content": text,
                            "importance": int(mem.get("importance") or 3),
                            "score": 0.0,
                        }
                    )
                    if mem.get("id") is not None:
                        selected_ids.append(int(mem["id"]))

        by_category: dict[str, list[str]] = {c: [] for c in CATEGORY_ORDER}
        for item in selected:
            by_category[item["category"]].append(item["content"])

        lines = []
        for cat in ordered_categories:
            items = by_category.get(cat, [])
            if items:
                lines.append(f"[{CATEGORY_LABELS[cat]}: {' | '.join(items)}]")
        if truncated:
            lines.append(f"[还有{truncated}条候选记忆未注入]")

        if selected_ids:
            await self.bump_access(user_id, selected_ids)

        return {
            "text": "\n".join(lines),
            "selected": selected,
            "truncated": truncated,
            "total_candidates": len(scored),
        }

    async def format_context(self, user_id: int, query: str = "") -> str:
        """兼容旧接口：返回注入字符串。"""
        if not query:
            cached = self.get_cached_context(user_id)
            if cached is not None:
                return cached
        result = await self.retrieve_for_injection(user_id, query=query)
        text = result.get("text", "")
        if text and not query:
            self.set_cached_context(user_id, text)
        return text

    
