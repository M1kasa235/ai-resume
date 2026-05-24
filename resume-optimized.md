# 教育背景
**2023.09 – 至今** | 云南师范大学 | 计算机科学与技术 | 本科
- 主修课程：数据结构、Python 数据分析、数据库技术、计算机网络、操作系统、算法设计、机器学习

---

# 技术栈
### AI & LLM
- **LangChain/LangGraph**：多 Agent 框架、Tool Calling、Middleware、Checkpointer 会话管理
- **RAG 全链路**：ChromaDB 向量化 → 混合检索（BM25+向量 RRF）→ 重排序（gte-rerank-v2）→ 生成
- **Prompt Engineering**：DeepSeek/DashScope API 提示优化

### 后端开发
- **FastAPI**：63 个 RESTful API、全链路 async/await
- **ORM**：SQLAlchemy 2.0 异步、Pydantic 校验

### 数据库与存储
- MySQL 8.0 | ChromaDB（向量） | SQLite（会话） | Redis（缓存）

### 认证与通信
- JWT 双 Token + RBAC | WebSocket + SSE 流式输出

### 工程化
- Docker 多阶段构建 | Git | Alembic 迁移

---

# 项目经验

## Offer Pilot — AI 求职助手 | 独立开发
**2026.03 – 2026.05**

基于大语言模型的智能求职平台，支持简历解析、岗位匹配、AI 模拟面试。

**技术栈**：FastAPI + LangChain + LangGraph + ChromaDB + DashScope + React + TypeScript + MySQL

### 核心成果

**多 Agent 协作系统**
- 设计中心化 5 Agent 架构（简历/求职/面试/记忆/主管），通过 asyncio.gather 并行调度，响应延迟降低约 45%
- 实现 AgentRegistry 统一注册中心 + AgentTrace 追踪机制，trace_id 串联完整调用链，异常定位从分钟级降至秒级
- 预处理管道实现零延迟意图分类（5 意图域 × 20+ 关键词规则）+ 3D 相关性评分记忆注入，延迟 < 10ms（对比 LangGraph 下降 20 倍）
- Memory Agent 三级触发机制（显式/自动/清理）+ 两级故障降级，任务完成率从 78% 提升至 94%

**混合检索引擎**
- 自研 BM25 内存索引（jieba + 100+ 术语词典）+ 向量检索并行，加权 RRF 融合，技术术语密度自适应调权，精确关键词 Top5 命中率 55% → 89%
- Parent/Child 分层分块：Child（400 字）精准匹配 + Parent（≤7000 字）完整上下文，解决检索精度与生成质量矛盾
- Section-aware 检索 + gte-rerank-v2 重排序，API 异常自动回退，幻觉率降低约 40%
- RAG 模块解耦：21 模块 4 层架构，单向依赖，支持增量更新

### 亮点
- 响应延迟降低 45%，预处理延迟 < 10ms
- 关键词命中率提升 34%（55% → 89%）
- 任务完成率提升 16%（78% → 94%）
- 幻觉率降低 40%

---

# 个人总结
- 热爱 AI 技术，具备扎实的计算机科学基础
- 熟练掌握 FastAPI、LangChain/LangGraph、RAG 检索增强
- 独立完成完整项目开发（架构设计 + Python 后端 + React 前端）
- 注重代码质量和工程化实践，熟悉 Docker、Git、数据库迁移
- 持续学习，具备快速学习和解决问题的能力