"""Structured context blocks and prompt rendering."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContextBlock:
    kind: str
    content: str
    priority: int = 2
    char_budget: int = 0


@dataclass
class ContextBundle:
    blocks: list[ContextBlock] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def to_log_dict(self) -> dict:
        return {
            "intent": self.meta.get("intent"),
            "blocks": [
                {"kind": b.kind, "chars": len(b.content)}
                for b in self.blocks
                if b.content
            ],
            "truncated": self.meta.get("truncated_blocks", 0),
            "total_chars": sum(len(b.content) for b in self.blocks),
        }

    def render(self) -> str:
        parts: list[str] = []
        for block in self.blocks:
            if not block.content:
                continue
            if block.kind == "system":
                parts.append(block.content)
            elif block.kind == "memory":
                parts.append(block.content)
            elif block.kind == "history":
                parts.append(f"[对话历史摘要] {block.content}")
            elif block.kind == "user":
                parts.append(block.content)
        return "\n\n".join(parts)
