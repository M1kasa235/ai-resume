# Offer Pilot — AI Job Assistant

基于 FastAPI + LangChain 的全栈 AI 求职助手，提供多智能体协作、长期记忆、RAG 增强检索、AI 模拟面试等功能。

## 快速开始

### 环境要求

- Python 3.10+
- MySQL 8.0+
- [uv](https://docs.astral.sh/uv/) (推荐) 或 pip

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/M1kasa235/ai-resume.git
cd ai-resume
```

2. **安装依赖**
```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env，修改数据库密码、API Key 等配置
```

4. **创建数据库**
```sql
CREATE DATABASE ai_job CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

5. **数据库迁移**
```bash
alembic upgrade head
```

6. **启动服务**
```bash
python run.py
# 或: uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

服务启动后访问 http://127.0.0.1:8080

## API 文档

- Swagger UI: http://127.0.0.1:8080/docs
- ReDoc: http://127.0.0.1:8080/redoc

## Docker

```bash
docker build -t offer-pilot .
docker run -p 8080:8080 --env-file .env offer-pilot
```

## 技术栈

| 层次 | 技术 |
|------|------|
| Web 框架 | FastAPI 0.115 |
| 数据库 | MySQL + SQLAlchemy 2.0 (Async) + aiosqlite |
| 迁移 | Alembic |
| 认证 | JWT (python-jose) + bcrypt |
| 数据验证 | Pydantic V2 |
| AI Agent | LangChain (create_agent) |
| LLM | DashScope / DeepSeek |
| 向量库 | ChromaDB |
| RAG | 混合检索 (BM25 + 向量) + 重排序 |
| 前端 | React + TypeScript + Vite |

## 项目结构

```
app/
├── agents/             # AI Agent 多智能体架构
│   ├── supervisor.py   # 主管 Agent（编排）
│   ├── agent.py        # 求职顾问 Agent
│   ├── resume_agent.py # 简历专家 Agent
│   ├── interview_agent.py # 面试官 Agent
│   ├── memory_agent.py # 记忆管家 Agent
│   ├── memory.py       # 长期记忆服务
│   ├── pre_process.py  # 预处理（意图分类 + 上下文注入）
│   ├── config.py       # Agent 共享配置
│   ├── registry.py     # Agent 统一注册中心
│   ├── trace.py        # 结构化调用追踪
│   └── tools/          # Agent 工具集
├── api/v1/             # API 路由
│   ├── agent_chat.py   # 统一对话入口
│   ├── interview.py    # AI 面试
│   ├── memory.py       # 记忆管理
│   ├── rag.py          # RAG 知识库
│   ├── resume_optimize.py # 简历优化
│   └── ...             # 其他 API
├── core/               # 核心配置
├── models/             # 数据模型
├── schemas/            # Pydantic Schema
├── services/           # 业务逻辑
├── rag/                # RAG 管道
│   ├── core/           # 向量存储、分块、解析
│   ├── ingestion/      # 文档摄入
│   ├── retrieval/      # 混合检索 + 重排序
│   ├── pipeline/       # 简历优化 + 岗位匹配
│   └── services/       # RAG 服务层
└── db/                 # 数据库会话
```

## 多智能体架构

```
用户请求 → Supervisor → Resume Agent (简历诊断/优化/匹配)
                      → Career Agent (搜岗位/薪资/推荐/资讯)
                      → Memory Agent (长期记忆管理)
                      → Interview Agent (AI 模拟面试)
```

### 长期记忆系统

- **写入**: Memory Agent 自主判断新增/更新/删除，支持 overwrite 和 append 模式
- **注入**: 基于 3D 相关性评分（内容匹配 + 时间衰减 + 访问频次）定向注入上下文
- **衰减**: 按重要度分级自动过期清理（1级 7 天 ~ 4级 180 天）
- **分类**: fact / preference / insight / goal

## 配置说明

关键环境变量：

```env
# 数据库
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=ai_job

# JWT
SECRET_KEY=your-secret-key

# LLM
DASHSCOPE_API_KEY=your_api_key
DEEPSEEK_API_KEY=your_api_key

# 搜索
TAVILY_API_KEY=your_api_key

# CORS
CORS_ORIGINS=["http://localhost:5173"]
```

## 许可证

MIT License
