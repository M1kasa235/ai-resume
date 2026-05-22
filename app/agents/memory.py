"""长期记忆服务 — 跨会话用户档案持久化（SQLite + aiosqlite）

四类记忆：fact(硬事实) / preference(偏好) / insight(洞察) / goal(目标)
importance 1-5 驱动检索优先级和衰减周期
"""

import json
import math
import logging
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

MEMORY_DB_PATH = str(
    Path(__file__).resolve().parent.parent / "db" / "agent_sessions" / "memory.db"
)

# 衰减周期：importance → 保留天数 (-1 永不过期)
DECAY_DAYS = {1: 7, 2: 30, 3: 90, 4: 180, 5: -1}

# 注入用 category 排序（fact 和 preference 优先）
CATEGORY_ORDER = {"fact": 0, "preference": 1, "insight": 2, "goal": 3}

# 领域关键词映射：query 中出现左边 → 记忆 content 匹配右边也能通过
DOMAIN_MAP: dict[str, list[str]] = {
    "前端": ["react", "vue", "angular", "js", "javascript", "ts", "typescript", "css", "html", "web", "ui", "组件", "hooks", "小程序", "flutter", "react native", "uniapp", "jquery", "nextjs", "nuxt", "vite", "webpack"],
    "后端": ["python", "java", "go", "node", "django", "spring", "api", "sql", "数据库", "微服务", "redis", "kafka", "mq", "grpc", "restful", "mybatis", "gin", "fastapi", "flask", "nginx", "mq", "elasticsearch", "mongodb", "postgresql"],
    "移动端": ["android", "ios", "swift", "kotlin", "flutter", "react native", "uniapp", "小程序", "app"],
    "数据": ["sql", "数据分析", "数据仓库", "etl", "hadoop", "spark", "flink", "hive", "clickhouse", "tableau", "powerbi", "pandas", "数仓"],
    "AI算法": ["机器学习", "深度学习", "nlp", "cv", "算法", "pytorch", "tensorflow", "transformer", "llm", "大模型", "推荐系统", "模型", "训练", "推理"],
    "运维DevOps": ["docker", "kubernetes", "k8s", "ci", "cd", "jenkins", "devops", "linux", "shell", "监控", "prometheus", "grafana", "aws", "azure", "阿里云", "terraform", "ansible"],
    "测试": ["自动化测试", "性能测试", "selenium", "appium", "jmeter", "pytest", "单测", "回归", "测试用例"],
    "设计": ["ui", "ux", "figma", "sketch", "photoshop", "illustrator", "设计稿", "交互", "视觉"],
    "产品": ["产品经理", "需求分析", "prd", "原型", "axure", "用户研究", "竞品分析"],
    "项目管理": ["pmp", "敏捷", "scrum", "kanban", "项目管理", "进度", "排期", "协调"],
    "游戏": ["unity", "unreal", "ue4", "ue5", "cocos", "游戏", "渲染", "shader"],
    "嵌入式": ["c语言", "c++", "arm", "单片机", "stm32", "fpga", "linux内核", "驱动"],
    "面试": ["模拟", "评估", "自我介绍", "八股文", "准备", "笔试", "面经", "群面", "行为面试"],
    "简历": ["优化", "诊断", "匹配", "项目经验", "工作经历", "教育背景", "润色", "修改"],
    "薪资": ["月薪", "年薪", "待遇", "工资", "k", "万", "涨薪", "谈薪", "薪资"],
    "城市": ["北京", "上海", "深圳", "广州", "杭州", "成都", "远程", "南京", "武汉", "苏州", "西安", "长沙", "郑州", "天津", "重庆", "合肥", "厦门"],
    "岗位推荐": ["推荐", "搜索", "匹配", "投递", "职位", "招聘", "找工作", "内推", "猎头"],
    "校招实习": ["应届", "实习", "春招", "秋招", "校招", "管培生", "转正", "暑期", "寒假"],
    "外企英语": ["英语", "日语", "外企", "跨国公司", "远程办公", "海外", "留学", "global"],
    "转行": ["转行", "零基础", "培训", "自学", "转岗", "非科班", "入门"],
    "创业": ["创业", "融资", "startup", "合伙", "天使轮", "独立开发"],
    "自由职业": ["远程", "自由职业", "外包", "接单", "freelancer", "兼职"],
}

# 注入配额：总字符上限 + 各 category 占比
CONTEXT_MAX_CHARS = 500
CATEGORY_QUOTA = {"fact": 0.40, "preference": 0.30, "insight": 0.20, "goal": 0.10}

_EXTRACTION_PROMPT = """你是记忆提取助手。分析对话并提取关于用户的记忆，只提取重要且持久的信息。

已有记忆（{existing_summary}）

规则：
- 只提取重要性 >= 3 的信息（3=有参考价值，4=重要，5=核心事实）
- 每次最多提取 5 条，无重要信息则返回空数组
- 如果新信息与已有记忆冲突，在 delete 中标注要删除的 mem_key
- 记忆内容简洁，不超过 30 字

输出纯 JSON（不要 markdown 代码块）：
{{"upsert": [{{"category": "preference|fact|insight|goal", "mem_key": "唯一键", "content": "记忆内容", "importance": 4}}], "delete": ["过时的mem_key"]}}"""


class MemoryService:
    """长期记忆服务 — 单例，全局共享一个 aiosqlite 连接"""

    _instance = None
    _context_cache: dict[int, str] = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = MEMORY_DB_PATH):
        if self._initialized:
            return
        self._db_path = db_path
        self._conn: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()
        self._initialized = True

    @classmethod
    def invalidate_cache(cls, user_id: int):
        cls._context_cache.pop(user_id, None)

    @classmethod
    def get_cached_context(cls, user_id: int) -> str | None:
        return cls._context_cache.get(user_id)

    @classmethod
    def set_cached_context(cls, user_id: int, ctx: str):
        cls._context_cache[user_id] = ctx

    async def _get_conn(self) -> aiosqlite.Connection:
        if self._conn is not None:
            return self._conn
        async with self._lock:
            if self._conn is not None:
                return self._conn
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = await aiosqlite.connect(self._db_path)
            self._conn.row_factory = aiosqlite.Row
            await self._ensure_table()
            return self._conn

    async def _ensure_table(self):
        conn = self._conn or await self._get_conn()
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_memories (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                category        TEXT NOT NULL,
                mem_key         TEXT NOT NULL,
                content         TEXT NOT NULL,
                importance      INTEGER DEFAULT 3,
                source          TEXT,
                access_count    INTEGER DEFAULT 0,
                last_accessed   TEXT,
                created_at      TEXT DEFAULT (datetime('now','localtime')),
                updated_at      TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(user_id, category, mem_key)
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_user "
            "ON user_memories(user_id)"
        )
        await conn.commit()

    # ── CRUD ──

    async def upsert(
        self, user_id: int, category: str, mem_key: str,
        content: str, importance: int = 3, source: str = "",
    ):
        conn = await self._get_conn()
        await conn.execute(
            """INSERT OR REPLACE INTO user_memories
               (user_id, category, mem_key, content, importance, source, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))""",
            (user_id, category, mem_key, content, importance, source),
        )
        await conn.commit()
        logger.debug(f"memory upsert: user={user_id} {category}/{mem_key}")

    async def delete(self, user_id: int, category: str, mem_key: str):
        conn = await self._get_conn()
        await conn.execute(
            "DELETE FROM user_memories WHERE user_id=? AND category=? AND mem_key=?",
            (user_id, category, mem_key),
        )
        await conn.commit()

    async def get_all(self, user_id: int) -> list[dict]:
        conn = await self._get_conn()
        rows = await conn.execute_fetchall(
            "SELECT * FROM user_memories WHERE user_id=? ORDER BY importance DESC",
            (user_id,),
        )
        return [dict(r) for r in rows]

    async def count(self, user_id: int) -> int:
        conn = await self._get_conn()
        row = await conn.execute_fetchall(
            "SELECT COUNT(*) as cnt FROM user_memories WHERE user_id=?",
            (user_id,),
        )
        return row[0]["cnt"] if row else 0

    async def bump_access(self, user_id: int):
        """标记该用户所有记忆为最近访问"""
        conn = await self._get_conn()
        await conn.execute(
            "UPDATE user_memories SET access_count = access_count + 1, "
            "last_accessed = datetime('now','localtime') WHERE user_id=?",
            (user_id,),
        )
        await conn.commit()

    @staticmethod
    def _compute_relevance(query: str, mem: dict) -> float:
        """计算 query 与单条记忆的相关性 (0~1)

        三维评分：
        1. 内容匹配：领域映射 + 2-gram 字面重叠
        2. 时间衰减：7天内满分，之后指数衰减（半衰期 30 天）
        3. 访问加成：被频繁检索的记忆获得额外权重
        """
        content = mem.get("content", "")
        if not query:
            return 1.0

        q = query.lower()
        c = content.lower()

        # ── 内容匹配 (0~1) ──
        keywords: set[str] = set()
        for domain, terms in DOMAIN_MAP.items():
            if domain in q:
                keywords.update(terms)
                keywords.add(domain)

        q_grams = {q[i:i+2] for i in range(len(q)-1)} if len(q) >= 2 else {q}
        c_grams = {c[i:i+2] for i in range(len(c)-1)} if len(c) >= 2 else {c}
        gram_overlap = len(q_grams & c_grams) / max(len(q_grams), 1)
        kw_hit = any(kw in c for kw in keywords) if keywords else False
        content_score = max(gram_overlap, 0.7 if kw_hit else 0.0)

        # ── 时间衰减 (0.3~1.0) ──
        updated = mem.get("updated_at", "")
        try:
            if updated:
                updated_date = datetime.strptime(updated[:10], "%Y-%m-%d")
                days = (datetime.now() - updated_date).days
                if days <= 7:
                    recency = 1.0
                else:
                    recency = max(0.3, math.exp(-(days - 7) / 43))  # 半衰期 ≈30天
            else:
                recency = 0.5  # 无时间戳按中等
        except (ValueError, TypeError):
            recency = 0.5

        # ── 访问加成 (0.8~1.2) ──
        access = mem.get("access_count", 0) or 0
        if access >= 10:
            access_boost = 1.2
        elif access >= 5:
            access_boost = 1.1
        elif access >= 2:
            access_boost = 1.0
        else:
            access_boost = 0.9

        return content_score * recency * access_boost

    # ── 注入 ──

    async def format_context(self, user_id: int, query: str = "") -> str:
        """将记忆压缩为紧凑的上下文字符串

        无 query：全量注入（向后兼容）
        有 query：相关性过滤 + 分类配额截断（≤500 chars）
        """
        memories = await self.get_all(user_id)
        if not memories:
            return ""

        # 相关性过滤 + importance 排序
        if query:
            scored = [
                (self._compute_relevance(query, m), m)
                for m in memories
            ]
            scored = [(s, m) for s, m in scored if s > 0.15]
            scored.sort(key=lambda x: (x[1]["importance"], x[0]), reverse=True)
            memories = [m for _, m in scored]

        # 按 category 分组，组内按 importance 降序
        groups: dict[str, list[dict]] = {"fact": [], "preference": [], "insight": [], "goal": []}
        for m in memories:
            cat = m["category"]
            if cat in groups:
                groups[cat].append(m)

        label = {"fact": "技能", "preference": "偏好", "insight": "洞察", "goal": "目标"}

        if query:
            # 配额截断
            parts: list[str] = []
            truncated = 0
            for cat in ("fact", "preference", "insight", "goal"):
                items = groups[cat]
                if not items:
                    continue
                budget = int(CONTEXT_MAX_CHARS * CATEGORY_QUOTA[cat])
                selected: list[str] = []
                char_count = 0
                for m in items:
                    piece = m["content"]
                    if char_count + len(piece) + 3 <= budget:  # 3 = " | "
                        selected.append(piece)
                        char_count += len(piece) + 3
                    else:
                        truncated += 1
                if selected:
                    parts.append(f"[{label[cat]}: {' | '.join(selected)}]")

            ctx = "\n".join(parts)
            if truncated:
                ctx += f"\n[还有{truncated}条相关记忆未展示]"
        else:
            # 无 query：全量，按旧格式
            parts = []
            for cat, items in groups.items():
                if items:
                    contents = [m["content"] for m in items]
                    parts.append(f"[{label[cat]}: {' | '.join(contents)}]")
            ctx = "\n".join(parts)

        await self.bump_access(user_id)
        return ctx

    # ── 提取 ──

    async def extract_from_transcript(
        self, user_id: int, transcript: str, source: str, llm,
    ) -> dict | None:
        """LLM 分析对话，提取记忆 delta，写入 DB

        Returns: {"upsert": [...], "delete": [...]} 或 None
        """
        existing = await self.get_all(user_id)
        existing_summary = "无"
        if existing:
            items = [f"{m['category']}/{m['mem_key']}: {m['content']}" for m in existing[:20]]
            existing_summary = "; ".join(items)

        prompt = _EXTRACTION_PROMPT.format(existing_summary=existing_summary)
        full_prompt = f"{prompt}\n\n来源：{source}\n对话内容：\n{transcript[-4000:]}"

        try:
            resp = await asyncio.wait_for(
                llm.ainvoke(full_prompt), timeout=30,
            )
            text = resp.content if hasattr(resp, "content") else str(resp)
            delta = self._parse_delta(text)
        except asyncio.TimeoutError:
            logger.warning("记忆提取超时")
            return None
        except Exception as e:
            logger.warning(f"记忆提取 LLM 失败: {e}")
            return None

        if not delta:
            return None

        # 执行删除
        for key in delta.get("delete", [])[:5]:
            # key 格式：category/mem_key 或仅 mem_key（按 user_id 模糊匹配）
            await self._delete_by_key(user_id, key)

        # 执行 upsert
        upserted = 0
        for item in delta.get("upsert", [])[:5]:
            imp = item.get("importance", 3)
            if imp < 3:
                continue
            await self.upsert(
                user_id=user_id,
                category=item.get("category", "fact"),
                mem_key=item.get("mem_key", ""),
                content=item.get("content", ""),
                importance=imp,
                source=source,
            )
            upserted += 1

        logger.info(f"记忆提取完成: user={user_id} source={source} upserted={upserted}")
        return delta

    async def _delete_by_key(self, user_id: int, key: str):
        """支持 category/mem_key 或仅 mem_key 格式"""
        conn = await self._get_conn()
        if "/" in key:
            cat, mk = key.split("/", 1)
            await conn.execute(
                "DELETE FROM user_memories WHERE user_id=? AND category=? AND mem_key=?",
                (user_id, cat, mk),
            )
        else:
            await conn.execute(
                "DELETE FROM user_memories WHERE user_id=? AND mem_key=?",
                (user_id, key),
            )
        await conn.commit()

    @staticmethod
    def _parse_delta(text: str) -> dict | None:
        """解析 LLM 返回的 JSON delta"""
        text = text.strip()
        # 剥离可能的 markdown 代码块
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:]) if len(lines) > 1 else text
            if text.endswith("```"):
                text = text[:-3]
        try:
            delta = json.loads(text)
            if "upsert" in delta or "delete" in delta:
                return delta
        except json.JSONDecodeError:
            logger.warning(f"记忆提取 JSON 解析失败: {text[:200]}")
        return None

    # ── 维护 ──

    async def consolidate(self, user_id: int, llm):
        """记忆 > 50 条时合并同类项、压缩低分项"""
        count = await self.count(user_id)
        if count <= 50:
            return

        memories = await self.get_all(user_id)
        items = [f"({m['importance']}) {m['category']}/{m['mem_key']}: {m['content']}" for m in memories]

        prompt = (
            f"合并以下用户记忆，规则：\n"
            f"1. 相似内容合并为一条（取最高 importance + 最完整表述）\n"
            f"2. importance 1-2 且创建超过 7 天的内容可以丢弃\n"
            f"3. 输出 JSON：{{'keep': ['mem_key1', ...], 'merge': [{{'mem_key': 'new', 'category': '..', 'content': '..', 'importance': 3}}]}}\n\n"
            f"记忆列表：\n" + "\n".join(items)
        )

        try:
            resp = await asyncio.wait_for(llm.ainvoke(prompt), timeout=30)
            text = resp.content if hasattr(resp, "content") else str(resp)
            plan = json.loads(text)
        except Exception as e:
            logger.warning(f"记忆整合失败: {e}")
            return

        # 执行合并计划（保守：只执行 merge，不直接删除未在 keep 中的条目）
        for item in plan.get("merge", [])[:10]:
            await self.upsert(
                user_id, item["category"], item["mem_key"],
                item["content"], item.get("importance", 3), "consolidation",
            )
        logger.info(f"记忆整合完成: user={user_id} before={count} after~{await self.count(user_id)}")

    async def decay(self, user_id: int):
        """清理过期记忆"""
        conn = await self._get_conn()
        today = datetime.now()
        for imp, days in DECAY_DAYS.items():
            if days < 0:
                continue  # 永不过期
            cutoff = (today - timedelta(days=days)).isoformat()
            await conn.execute(
                "DELETE FROM user_memories WHERE user_id=? AND importance=? AND created_at < ?",
                (user_id, imp, cutoff[:10]),
            )
        await conn.commit()

    async def decay_all(self):
        """清理所有用户的过期记忆（启动时调用）"""
        conn = await self._get_conn()
        today = datetime.now()
        total = 0
        for imp, days in DECAY_DAYS.items():
            if days < 0:
                continue
            cutoff = (today - timedelta(days=days)).isoformat()
            cursor = await conn.execute(
                "DELETE FROM user_memories WHERE importance=? AND created_at < ?",
                (imp, cutoff[:10]),
            )
            total += cursor.rowcount
        await conn.commit()
        if total:
            logger.info(f"decay_all: 清理 {total} 条过期记忆")
