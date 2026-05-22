---
name: Enterprise RAG Plan
description: Enterprise-grade RAG system design for AI Job Assistant - resume analysis, job matching, interview prep
type: reference
---

# AI Job Assistant — 企业级 RAG 方案

## 一、业务场景

这个项目里有三个场景适合用 RAG：

| 场景 | 数据源 | 用户问题示例 |
|------|-------|------------|
| **简历分析** | 用户上传的 PDF 简历 | "根据我的简历，适合投哪些公司？" |
| **岗位匹配** | 数据库中的岗位 JD | "我这个简历和前端开发岗匹配度如何？" |
| **面试准备** | 题库 + 公司面经 | "针对我简历里的项目经验，会问什么？" |

---

## 二、整体架构

```
┌──────────────────────────────────────────────────────────┐
│                   用户查询 (Query)                        │
└─────────────────┬────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────┐
│               Query Transformation 层                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │ HyDE     │  │ Multi-   │  │ Query Rewrite        │   │
│  │ 扩写查询  │  │ Query    │  │ 纠错/补全/扩展       │   │
│  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘   │
│       └──────────────┼──────────────────┘               │
└──────────────────────┼──────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│                  检索层 (Retrieval)                      │
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │  Dense Search   │  │  Sparse Search  │              │
│  │  (向量相似度)    │  │  (BM25 关键词)   │              │
│  └────────┬────────┘  └────────┬────────┘              │
│           └──────────┬──────────┘                       │
│                      ▼                                  │
│            ┌─────────────────┐                          │
│            │   Hybrid Fusion │                          │
│            │   (RRF 合并)     │                          │
│            └────────┬────────┘                          │
│                      ▼                                  │
│            ┌─────────────────┐                          │
│            │   Reranker      │                          │
│            │   (Cohere/BGE)  │                          │
│            └────────┬────────┘                          │
└──────────────────────┼──────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│                    生成层 (Generation)                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Prompt Template + Context + Query → LLM Response │   │
│  │ + 引用标注 + 置信度打分 + 兜底策略                │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## 三、文档处理管线 (Ingestion Pipeline)

### 3.1 文档类型与解析

| 文档类型 | 解析方案 | 产出 |
|---------|---------|------|
| **PDF 简历** | PyMuPDF / Unstructured.io | Markdown 文本 + 结构化字段 |
| **岗位 JD** | 数据库已有结构化数据 | JSON 字段 |
| **面经/题库** | 数据库已有 | 结构化工位 |

### 3.2 分块策略

不只用一种分块，按文档类型差异化：

```
简历 PDF 分块:
┌────────────────────────────────────────────────┐
│  Chunk 1: 个人信息（姓名/电话/邮箱/地址）       │
│  Chunk 2: 技能树（编程语言/框架/工具列表）       │
│  Chunk 3: 工作经历1（公司/时间/职责/成果）       │
│  Chunk 4: 工作经历2                              │
│  Chunk 5: 项目经验1                               │
│  Chunk 6: 教育背景                                │
└────────────────────────────────────────────────┘
```

**分块方案选型**：

| 方案 | 适用场景 | 参数 |
|------|---------|------|
| RecursiveCharacterTextSplitter | 简历 PDF | chunk_size=500, overlap=100 |
| Semantic Chunker | 岗位 JD（按语义段落） | breakpoint_threshold=95 |
| MarkdownHeaderSplitter | 面经/题库（按标题） | 按 ## 分隔 |

### 3.3 元数据注入

每个 Chunk 必须携带元数据，这是企业级 RAG 的关键：

```python
{
  "chunk_id": "resume_001_chunk_03",
  "doc_type": "resume",          # resume / job / question
  "user_id": 42,
  "section": "work_experience",
  "chunk_index": 3,
  "total_chunks": 8,
  "source": "resume_2024.pdf",
  "created_at": "2024-01-01",
  "embedding_model": "text-embedding-3-small"
}
```

**元数据的价值**：
- 权限过滤：只检索当前用户的简历
- 来源追溯：告诉用户答案来自简历哪一段
- 增量更新：只重新索引有变动的文档

---

## 四、检索层设计 (Retrieval)

### 4.1 Embedding 选型

| 模型 | 维度 | 适用 | 成本 |
|------|------|------|------|
| text-embedding-3-small | 1536 | 通用，默认选择 | 低 |
| text-embedding-3-large | 3072 | 精度优先场景 | 中 |
| bge-large-zh-v1.5 | 1024 | 中文优化（可本地部署） | 零 |

**推荐**：开发用 `text-embedding-3-small`，生产用 `bge-large-zh-v1.5`（省钱且中文更好）

### 4.2 向量数据库选型

| 方案 | 适合场景 | 本项目选择 |
|------|---------|-----------|
| Chroma | 单机开发，快速原型 | ✅ 开发环境 |
| pgvector | 与业务数据共存 | ✅ 生产环境（已有 MySQL 可切 PostgreSQL） |
| Milvus | 大规模、分布式 | ❌ 本项目暂时不需要 |
| Pinecone | 全托管 SaaS | 看预算 |

**推荐**：开发用 Chroma，生产用 pgvector（PostgreSQL 插件，和业务数据放一起）

### 4.3 混合检索

```
用户查询: "找一份北京的前端开发工作，要求 React"

Dense Search (向量):
  → "前端开发工程师 React 北京 大厂"  (语义相关)

Sparse Search (BM25):
  → "北京" + "前端" + "React"         (关键词命中)

RRF 合并:
  score = 1/(k + rank_dense) + 1/(k + rank_sparse)
  → 合并排序，取 Top-K

Reranker:
  → 对 Top-20 重新排序 → 取 Top-5
```

### 4.4 Reranker 选型

| 模型 | 质量 | 速度 | 成本 |
|------|------|------|------|
| Cohere Rerank v3 | ⭐⭐⭐⭐⭐ | 中 | 按量付费 |
| BGE-Reranker-v2-m3 | ⭐⭐⭐⭐ | 中 | 免费（本地） |
| 无 Reranker | ⭐⭐⭐ | 快 | 零 |

**企业级标配 Reranker** — 没有 Reranker 的 RAG 不是企业级。

---

## 五、查询优化 (Query Transformation)

### 5.1 HyDE (Hypothetical Document Embedding)

```
用户查询: "我适合什么工作？"

↓ HyDE

假设性文档: "用户有 3 年前端经验，熟悉 React/Vue/TypeScript，
             做过大型后台管理系统，寻求高级前端开发岗位..."

↓ 用假设文档去检索（而不是原始查询）

效果: 提升检索召回率 10-20%
```

### 5.2 Multi-Query

```
用户查询: "React 18 的新特性在面试中会怎么问？"

↓ 扩写为 3 个查询

1. "React 18 新特性面试题"
2. "useTransition 和 useDeferredValue 区别 面试"
3. "React 18 Concurrent Mode 常见问题"

↓ 分别检索后合并去重
```

### 5.3 Query Rewrite

```
"找北京的工作" → 补全 → "北京的前端开发工程师岗位"
"这个怎么样" → 加上上文 → "字节跳动前端岗位怎么样"
```

---

## 六、本项目的 RAG 场景具体设计

### 场景 1：简历分析 RAG

```
用户上传简历 PDF
  → PyMuPDF 提取文本
  → 按章节分块 (个人信息/技能/经历/项目/教育)
  → 每块生成 embedding + 写入向量库
  → 标记 user_id 权限隔离

面试官/用户提问: "我的简历里哪个项目最有竞争力？"
  → HyDE 扩写为 "评估项目经验的影响力和技术深度"
  → 检索该用户的简历 Chunks
  → Reranker 排序
  → LLM 生成分析 + 引用标注
```

### 场景 2：岗位匹配 RAG

```
用户提问: "这个岗位和我的匹配度如何？"

方案: 简历 Chunks + 岗位 JD → 一起送入 LLM 打分

检索:
  - 简历 Chunks（用户自己的）
  - 岗位 JD 详情（从数据库直接拿）

Prompt 结构:
  """
  简历信息: {简历 Chunks 拼接}
  岗位要求: {岗位 JD}
  
  请从以下维度分析匹配度并打分(1-10):
  1. 技能匹配度
  2. 经验匹配度
  3. 城市匹配度
  4. 薪资匹配度
  """
```

### 场景 3：面试准备 RAG

```
用户提问: "针对我的简历，模拟一场 Vue 技术面"

检索:
  1. 用户简历（技能部分 → 识别出 Vue 相关）
  2. 题库（按 Vue + 中高级 → 相关题目）
  3. 该用户的历史错题（针对性强化）

生成:
  AI 面试官根据简历问第一题
  → 用户回答
  → 检索参考答案 + 评估
  → 进入下一题
```

---

## 七、评估体系 (Evaluation)

没有评估的 RAG 是玩具。企业级必须能量化效果。

### 7.1 离线评估

| 指标 | 测量内容 | 目标值 |
|------|---------|--------|
| Hit Rate | 检索结果是否包含正确答案 | > 85% |
| MRR | 正确答案排在第几位 | > 0.8 |
| NDCG@10 | 排序质量 | > 0.75 |
| Faithfulness | 生成内容是否忠实于检索结果 | > 90% |
| Answer Relevance | 回答是否相关 | > 85% |

### 7.2 评估数据集构建

```
需要 50-100 条人工标注的 QA 对，例如：

问题: "我的简历里有哪些技术栈？"
相关 Chunk: "技能：React、TypeScript、Node.js、Python"
期望回答: "你的技术栈包括 React、TypeScript、Node.js、Python"
```

### 7.3 RAGAS 框架

用 RAGAS 做自动化评估，覆盖 Faithfulness、Answer Relevancy、Context Precision、Context Recall。每次修改管线后跑一遍，确保没退化。

---

## 八、生产化考虑

### 8.1 增量更新

```
用户更新简历:
  → 删除该用户所有旧 Chunks
  → 重新解析 PDF
  → 重新分块 + embedding
  → 写入新 Chunks
```

### 8.2 缓存策略

| 层级 | 缓存什么 | TTL |
|------|---------|-----|
| Embedding 缓存 | 相同文本的向量 | 7 天 |
| 检索结果缓存 | 相同查询的检索结果 | 5 分钟 |
| LLM 响应缓存 | 相同 Question+Context 的回答 | 1 小时 |

### 8.3 权限隔离

```
检索时必须携带 user_id / role 过滤条件:

vector_store.similarity_search(
  query,
  filter={"user_id": current_user.id},    # ← 权限过滤
  k=10
)
```

### 8.4 监控

| 监控项 | 工具 |
|--------|------|
| 检索延迟 | Prometheus + Grafana |
| Token 消耗 | LangSmith |
| 用户满意度 | 点赞/点踩反馈收集 |
| 空结果率 | 日志告警 |

### 8.5 降级策略

```
主链路: Hybrid Search → Reranker → LLM
降级 1: Hybrid Search → LLM (Reranker 挂了)
降级 2: Dense Search → LLM (BM25 挂了)  
降级 3: 关键词搜索 → 直接返回 (LLM 挂了)
```

---

## 九、技术栈推荐

| 组件 | 选择 | 原因 |
|------|------|------|
| Embedding | bge-large-zh-v1.5 | 中文好，可本地部署，免费 |
| 向量库 | Chroma → pgvector | 开发→生产平滑迁移 |
| 分块 | LangChain Text Splitters | 灵活，可组合 |
| Reranker | BGE-Reranker-v2-m3 | 免费，效果接近 Cohere |
| 评估 | RAGAS | 开源，社区活跃 |
| 监控 | LangSmith | 和 LangChain 无缝集成 |
| 编排 | LangGraph | 你已经准备学的 |

---

## 十、分阶段落地建议

### Phase 1：MVP（2 周）
- PDF 解析 + 基础分块
- Chroma + text-embedding-3-small
- 单场景：简历分析（用户问自己的简历）

### Phase 2：增强（+2 周）
- 引入 HyDE + Multi-Query
- 加入 Reranker
- 第二个场景：岗位匹配度分析

### Phase 3：企业级（+2 周）
- 切换 pgvector
- 增量更新 + 缓存
- RAGAS 评估体系
- 监控 + 权限隔离
