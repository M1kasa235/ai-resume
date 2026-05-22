<p align="center">
  <h1 align="center">Offer Pilot</h1>
  <p align="center"><strong>AI 驱动的全栈求职助手</strong> — 多智能体协作 · 长期记忆 · RAG 检索增强 · AI 模拟面试</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/LangChain-Agent-orange.svg" alt="LangChain">
  <img src="https://img.shields.io/badge/React-18-blue.svg" alt="React">
  <img src="https://img.shields.io/badge/ChromaDB-0.4-purple.svg" alt="ChromaDB">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen.svg" alt="License">
</p>

---

<!-- 预留：产品主截图 -->
<!-- ![Offer Pilot 首页](./docs/screenshots/dashboard.png) -->

## 为什么选择 Offer Pilot？

传统求职平台只能**搜岗位和投简历**，Offer Pilot 在此基础上构建了一套完整的 AI 辅助体系：

| 痛点 | Offer Pilot 方案 |
|------|-----------------|
| 简历不知道怎么写 | **简历诊断** — 多维度评分 + 逐项改进建议 |
| 海投没针对性 | **岗位匹配** — 简历 vs JD 逐维度对比，量化差距 |
| 面试没底 | **AI 模拟面试** — 基于真实简历出题，逐题评估报告 |
| 每次对话像失忆 | **长期记忆** — 自动识别并持久化偏好/背景/洞察 |
| 搜岗位靠手动翻 | **智能搜索** — 自然语言搜岗位 + 个性化推荐 |

## 核心亮点

###  多智能体协作架构

```
                         ┌─────────────────────┐
                         │    Supervisor        │
                         │  (编排 + 降级容错)    │
                         └──────┬───┬──────┬───┘
                ┌───────────────┤   │      ├───────────────┐
                ▼               ▼   ▼      ▼               ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │ Resume      │  │ Career      │  │ Interview   │  │ Memory      │
     │ Agent       │  │ Agent       │  │ Agent       │  │ Agent       │
     │ 简历专家     │  │ 求职顾问     │  │ 面试官       │  │ 记忆管家     │
     └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
            │                │                │                │
    ┌───────┴───────┐  ┌────┴────┐  ┌────────┴────────┐  ┌───┴───┐
    │ 简历查询       │  │ 岗位搜索 │  │ 简历驱动出题     │  │ 增删改 │
    │ 诊断评分       │  │ 薪资分析 │  │ 逐题追问点评     │  │ 自主判断│
    │ 岗位优化       │  │ 个性化推荐│  │ 综合评估报告     │  │ 过期清理│
    │ 岗位匹配       │  │ 行业资讯 │  │                 │  │        │
    └───────────────┘  └─────────┘  └─────────────────┘  └────────┘
```

每个 Agent 拥有独立的 checkpointer 会话记忆，Supervisor 智能路由并支持跨领域并行调用（`both_agents_tool`）。

<!-- 预留：AI 顾问对话截图 -->
<!-- ![AI 顾问对话](./docs/screenshots/ai-advisor.png) -->

###  长期记忆系统

```
┌─────────────────────────────────────────────────────────┐
│                     记忆生命周期                          │
│                                                         │
│  写入               存储              注入               │
│  ──────            ──────           ──────              │
│  Memory Agent      SQLite           相关性评分           │
│  自主判断          分类存储          定向注入             │
│  ↓                 ↓                ↓                   │
│  覆盖/追加模式     fact/preference   下次对话             │
│  来源追踪          insight/goal     自动携带             │
│                                                         │
│  衰减: 级别1 (7天) → 级别5 (永不过期)                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

- **自主管理**: Memory Agent 分析对话后自主决定新增/更新/删除
- **3D 相关性评分**: 内容匹配度 × 时间衰减 × 访问频次加成
- **上下文注入**: 按意图分类 + 类别配额自动注入，单次注入 ≤ 500 字符
- **append 模式**: 同 key 写入时不覆盖，自动追加时间戳后缀（解决"多段工作经历"问题）

<!-- 预留：记忆管理截图 -->
<!-- ![记忆管理](./docs/screenshots/memory-management.png) -->

###  RAG 混合检索管道

```
文档摄入 → 分块 → 向量化 (ChromaDB) ─┐
                                     ├── 混合检索 → 重排序 → 生成
关键词索引 → BM25 稀疏检索 ──────────┘
```

- 简历解析 / 岗位分析 / 知识库问答均经 RAG 增强
- BM25 + 向量检索的混合策略，兼顾精确匹配与语义泛化
- 支持 PDF 简历自动解析与分块存储

<!-- 预留：RAG 管理后台截图 -->
<!-- ![RAG 管理后台](./docs/screenshots/admin-rag.png) -->

###  AI 模拟面试

```
选择面试类型 → 输入岗位信息 → AI 基于简历出题
                                    ↓
                          逐题追问 + 实时点评
                                    ↓
                          面试结束 → 生成评估报告
```

- 支持**技术面 / HR 面 / 综合面**三种类型
- 基于真实简历内容**个性化出题**，深入项目细节
- 每道题**实时点评**，指出亮点和不足
- 结束后生成完整**评估报告**: 逐题评分 + 综合评估 + 改进建议

<!-- 预留：AI 面试截图 -->
<!-- ![AI 面试](./docs/screenshots/ai-interview.png) -->

<!-- 预留：面试报告截图 -->
<!-- ![面试报告](./docs/screenshots/interview-report.png) -->

## 功能总览

| 模块 | 功能 | 状态 |
|------|------|------|
| 仪表盘 | 求职数据统计、投递追踪 | ✅ |
| 岗位管理 | CRUD、多维度搜索、收藏 | ✅ |
| 工作台 | 简历上传、解析、投递 | ✅ |
| 题库 | 面试题管理与分类 | ✅ |
| **AI 求职顾问** | 智能对话、岗位搜索、薪资分析、个性化推荐 | ✅ |
| **AI 简历优化** | 简历诊断、岗位匹配、针对 JD 优化、段落润色 | ✅ |
| **AI 模拟面试** | 技术面/HR面/综合面、逐题评估、综合报告 | ✅ |
| **长期记忆** | 自动捕获偏好/背景/洞察、智能衰减、上下文注入 | ✅ |
| **RAG 知识库** | 文档摄入、混合检索、增强生成 | ✅ |
| 管理后台 | 知识库管理、简历管理、分区管理 | ✅ |
| 个人中心 | 用户信息、简历版本管理 | ✅ |

## 快速开始

### 环境要求

- **Python** 3.10+
- **MySQL** 8.0+
- **Node.js** 18+ (前端)
- [uv](https://docs.astral.sh/uv/) (推荐包管理器)

### 后端

```bash
git clone https://github.com/M1kasa235/ai-resume.git
cd ai-resume

# 安装依赖
uv sync
# 或: pip install -r requirements.txt

# 配置环境
cp .env.example .env
# 编辑 .env，必填项:
#   MYSQL_PASSWORD — 数据库密码
#   SECRET_KEY — JWT 密钥
#   DASHSCOPE_API_KEY — LLM API Key
#   TAVILY_API_KEY — 搜索 API Key

# 创建数据库
mysql -u root -p -e "CREATE DATABASE ai_job CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 数据库迁移
alembic upgrade head

# 启动 (端口 8080)
python run.py
```

### 前端

```bash
cd frontend
npm install
npm run dev  # 端口 5173
```

### Docker

```bash
docker build -t offer-pilot .
docker run -p 8080:8080 --env-file .env offer-pilot
```

访问 http://localhost:8080/docs 查看 API 文档。

## 项目结构

```
├── app/
│   ├── agents/                # 多智能体系统
│   │   ├── supervisor.py      #   主管 Agent — 路由编排 + 降级容错
│   │   ├── agent.py           #   求职顾问 Agent — 搜索/推荐/资讯
│   │   ├── resume_agent.py    #   简历专家 Agent — 诊断/优化/匹配
│   │   ├── interview_agent.py #   面试官 Agent — 模拟面试
│   │   ├── memory_agent.py    #   记忆管家 Agent — 自主记忆管理
│   │   ├── memory.py          #   记忆存储服务 — CRUD/衰减/缓存
│   │   ├── pre_process.py     #   预处理 — 意图分类/上下文注入/历史压缩
│   │   ├── registry.py        #   Agent 统一注册中心
│   │   ├── trace.py           #   结构化调用追踪
│   │   ├── config.py          #   共享配置 (checkpointer/middleware)
│   │   └── tools/             #   Agent 工具集
│   ├── api/v1/                # REST API
│   │   ├── agent_chat.py      #   统一对话入口 (SSE 流式)
│   │   ├── interview.py       #   AI 面试 API
│   │   ├── memory.py          #   记忆管理 API
│   │   ├── rag.py             #   RAG 知识库 API
│   │   ├── resume_optimize.py #   简历优化 API
│   │   └── ...
│   ├── rag/                   # RAG 管道
│   │   ├── core/              #   向量存储/分块/解析
│   │   ├── ingestion/         #   文档摄入
│   │   ├── retrieval/         #   混合检索 + 重排序
│   │   ├── pipeline/          #   简历优化 + 岗位匹配
│   │   └── services/          #   RAG 服务层
│   ├── core/                  # 核心配置/安全/LLM
│   ├── models/                # SQLAlchemy 数据模型
│   ├── schemas/               # Pydantic Schema
│   └── services/              # 业务逻辑层
├── frontend/                  # React 前端
│   └── src/features/
│       ├── aiAdvisor/         #   AI 求职顾问页
│       ├── aiInterview/       #   AI 面试 + 报告 + 记录
│       ├── admin/             #   管理后台
│       ├── dashboard/         #   仪表盘
│       ├── jobs/              #   岗位列表/详情
│       └── ...
├── alembic/                   # 数据库迁移
├── Dockerfile                 # 多阶段构建
├── pyproject.toml             # 项目元数据 + 依赖
└── requirements.txt           # Pip 依赖
```

## Agent 工具矩阵

| Agent | 工具 | 说明 |
|-------|------|------|
| **Supervisor** | `resume_agent_tool` | 调用简历专家 |
| | `career_agent_tool` | 调用求职顾问 |
| | `both_agents_tool` | 并行调用双专家 |
| | `memory_agent_tool` | 调用记忆管家 |
| **Resume** | `query_resume` | 简历事实查询 |
| | `diagnose_resume` | 多维度诊断评分 |
| | `optimize_for_job` | 针对 JD 逐段优化 |
| | `match_resume_to_job` | 岗位匹配度分析 |
| | `polish_section` | 段落润色改写 |
| **Career** | `search_jobs` | 岗位搜索 |
| | `analyze_salary` | 薪资分析 |
| | `get_job_recommendations` | 个性化推荐 |
| | `search_knowledge` | 知识库检索 |
| | `tavily_search` | 互联网资讯搜索 |
| **Interview** | `query_resume` | 读取简历出题 |
| | `search_knowledge` | 获取面试题库 |
| **Memory** | `list_memories` | 查看全部记忆 |
| | `upsert_memory` | 新增/更新记忆 |
| | `delete_memory` | 删除过时记忆 |

## 记忆类别与衰减

| 类别 | 说明 | 示例 | 衰减周期 |
|------|------|------|---------|
| `fact` | 硬事实 | "React 3年经验"、"清华本科" | 180 天 |
| `preference` | 偏好 | "期望薪资 30K"、"只考虑北京" | 90 天 |
| `insight` | 行为洞察 | "系统设计偏弱"、"擅长算法" | 90 天 |
| `goal` | 目标 | "准备跳槽大厂"、"考 AWS 认证" | 30 天 |

## 环境变量参考

| 变量 | 必填 | 说明 |
|------|------|------|
| `APP_NAME` | 否 | 应用名称 (默认: Offer Pilot) |
| `DEBUG` | 否 | 调试模式 (默认: false) |
| `SERVER_HOST` | 否 | 监听地址 (默认: 127.0.0.1) |
| `SERVER_PORT` | 否 | 监听端口 (默认: 8080) |
| `MYSQL_HOST` | 否 | MySQL 地址 |
| `MYSQL_PORT` | 否 | MySQL 端口 |
| `MYSQL_USER` | 否 | MySQL 用户名 |
| `MYSQL_PASSWORD` | **是** | MySQL 密码 |
| `MYSQL_DB` | 否 | 数据库名 |
| `SECRET_KEY` | **是** | JWT 签名密钥 |
| `DASHSCOPE_API_KEY` | **是** | 阿里百炼 API Key |
| `DEEPSEEK_API_KEY` | 否 | DeepSeek API Key (备选) |
| `TAVILY_API_KEY` | **是** | Tavily 搜索 API Key |
| `CORS_ORIGINS` | 否 | 允许的前端域名 |

## 截图预留

> 请在 `docs/screenshots/` 目录下放置以下截图：

| 文件名 | 说明 |
|--------|------|
| `dashboard.png` | 仪表盘首页 |
| `ai-advisor.png` | AI 求职顾问对话页 |
| `ai-interview.png` | AI 模拟面试进行中 |
| `interview-report.png` | 面试评估报告 |
| `memory-management.png` | 记忆管理页面 |
| `admin-rag.png` | RAG 知识库管理后台 |
| `job-search.png` | 岗位搜索与列表 |

## 许可证

MIT License
