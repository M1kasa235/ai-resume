---
name: RAG Implementation Blueprint (updated with resume optimization)
description: Step-by-step implementation plan for the enterprise RAG system + AI resume optimization
type: project
---

# RAG 系统 + 简历优化 — 开发实施方案

## 总体架构

```
frontend/                          backend/
  features/                          agents/
    workbench/                         agent.py          ← 已有，改造
      index.tsx  ← + 优化 Tab          rag/             ← 新建
  services/                            __init__.py
    api.ts  ← + ragApi + optimizeApi   chroma_client.py  ← 向量库操作
  types/                               ingestion.py      ← 文档入库管线
    api.ts  ← + 新类型                 retriever.py      ← 检索（HyDE/Multi-Query）
                                       reranker.py       ← 重排
                                       generator.py      ← 问答生成
                                       resume_optimizer.py ← 简历优化引擎
                                       job_match.py      ← 岗位匹配
                                       evaluation.py     ← 评估
                                       schemas.py        ← 请求/响应
                                     api/v1/
                                       rag.py            ← RAG 接口
                                       resume_optimize.py ← 简历优化接口
```

---

## Step 1：环境准备

### 1.1 安装依赖

```bash
pip install chromadb
pip install sentence-transformers
pip install pypdf
pip install cross-encoder
pip install langchain-chroma
```

### 1.2 向量库初始化

文件：`app/agents/rag/chroma_client.py`

- @ 管理 Chroma 连接
- Collection 设计：

| Collection | 内容 | 权限 |
|-----------|------|------|
| `resume_chunks` | 简历分块 | user_id |
| `job_descriptions` | 岗位 JD | 公开 |

### 1.3 Embedding

- 模型：`BAAI/bge-large-zh-v1.5`
- query_instruction：`"为这个句子生成表示以用于检索相关文章："`
- normalize_embeddings: true

---

## Step 2：简历 PDF 解析管线

文件：`app/agents/rag/ingestion.py`

### 2.1 PDF 提取

```python
from pypdf import PdfReader

def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text
```

### 2.2 智能分块

简历天然结构：

```
个人信息 —— 姓名/电话/邮箱/地址
技能 —— 编程语言/框架/工具
工作经历 —— 公司A(时间/职位/职责) / 公司B / ...
项目经验 —— 项目A(技术栈/亮点) / 项目B / ...
教育背景 —— 学校/专业/学历/时间
```

分块策略：

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "；", "，", " ", ""],
)
```

同时尝试用 MarkdownHeaderTextSplitter 识别章节标题。

### 2.3 元数据

```python
{
    "chunk_id": "uuid",
    "user_id": 42,
    "doc_type": "resume",
    "chunk_index": 3,
    "total_chunks": 8,
    "section": "work_experience",   # 章节类型，优化引擎会用到
    "source": "resume_张三.pdf",
    "version": 2,                    # 简历版本号
    "created_at": "2026-05-10T12:00:00Z",
}
```

**section 可选值**：`personal_info` / `skills` / `work_experience` / `projects` / `education`

### 2.4 入库流程

```python
class IngestionPipeline:
    def process_resume(self, file_path: str, user_id: int, version: int = 1):
        # 1. 提取
        text = extract_text_from_pdf(file_path)
        
        # 2. 删除该用户旧 chunks
        self.delete_user_chunks(user_id)
        
        # 3. 分块 + 元数据
        documents = self.chunk_with_metadata(text, user_id, version)
        
        # 4. 写入向量库
        self.vector_store.add_documents(documents)
        
        return {"chunks_count": len(documents), "status": "success"}
```

---

## Step 3：检索层

文件：`app/agents/rag/retriever.py`

### 3.1 基础检索

```python
def retrieve(self, query: str, user_id: int, k: int = 10):
    return self.vector_store.similarity_search(
        query, k=k, filter={"user_id": user_id}
    )
```

### 3.2 HyDE（假设性文档扩写）

```
查询: "我有什么项目经验？"
  → LLM 生成: "根据简历，该候选人的项目包括..."
  → 用假设文档去检索
  → 效果：短查询也能命中相关 Chunk
```

### 3.3 Multi-Query（多查询扩写）

```
查询: "我有什么优势？"
  → 扩写为 3 个: "核心技能" / "项目成果" / "工作亮点"
  → 分别检索 → 合并去重
```

### 3.4 组合检索器

```python
class RAGRetriever:
    def retrieve(self, query: str, user_id: int, k: int = 10):
        if len(query) < 10:
            return self.hyde.retrieve(query, user_id, k)
        elif len(query) > 30:
            return self.multi_query.retrieve(query, user_id, k)
        else:
            return self.base.retrieve(query, user_id, k)
```

---

## Step 4：Reranker 重排

文件：`app/agents/rag/reranker.py`

- 模型：`BAAI/bge-reranker-v2-m3`
- 输入：query + document pair → 输出相关性得分
- 流程：检索 Top-10 → Reranker 重排 → 取 Top-5

---

## Step 5：RAG 问答生成

文件：`app/agents/rag/generator.py`

### 5.1 问答 Prompt

```
你是一个专业的简历分析师。根据提供的简历片段回答用户问题。

=== 简历片段 ===
{context}

=== 用户问题 ===
{question}

要求：
1. 只基于简历片段回答
2. 没有相关信息时明确说"简历中未提及"
3. 引用具体简历内容作为依据
4. 用中文回答
```

### 5.2 回答 + 引用

```python
class RAGGenerator:
    def generate(self, query: str, context_docs: list) -> dict:
        context = "\n\n".join([
            f"[{doc.metadata['section']}]: {doc.page_content}"
            for i, doc in enumerate(context_docs)
        ])
        
        response = self.llm.invoke(self.qa_prompt.format(
            context=context, question=query
        ))
        
        return {
            "answer": response.content,
            "references": [
                {
                    "content": doc.page_content[:150],
                    "section": doc.metadata.get("section"),
                }
                for doc in context_docs
            ]
        }
```

---

## Step 6：简历优化引擎 ⭐（新增核心）

文件：`app/agents/rag/resume_optimizer.py`

### 6.1 功能矩阵

| 功能 | 说明 | 输入 | 输出 |
|------|------|------|------|
| **简历诊断** | 全面分析优劣势 | 完整简历文本 | 诊断报告 |
| **定向优化** | 针对 JD 优化简历 | 简历 + 目标 JD | 优化版简历 |
| **项目润色** | 重写项目描述（量化成果） | 单段项目描述 | 润色版 |
| **技能推荐** | 根据 JD 推荐补充技能 | 技能列表 + JD | 补充建议 |

### 6.2 简历诊断

```python
class ResumeDiagnoser:
    def diagnose(self, resume_text: str) -> dict:
        prompt = """你是一位资深HR。分析以下简历，输出诊断报告。

简历内容：
{resume_text}

请按以下格式输出JSON：
{{
    "overall_score": "7/10",
    "strengths": ["优势1", "优势2", ...],
    "weaknesses": ["不足1", "不足2", ...],
    "suggestions": [
        {{
            "section": "项目经验",
            "issue": "描述过于简单",
            "advice": "建议增加量化数据"
        }}
    ],
    "missing_fields": ["期望薪资", "到岗时间"],
    "keyword_density": {{
        "frontend": 5,
        "react": 3
    }}
}}"""
        
        result = self.llm.invoke(prompt.format(resume_text=resume_text))
        return self.parse_json(result.content)
```

### 6.3 定向优化（核心功能）

```
用户选择岗位 JD
       │
       ▼
检索该用户完整简历
       │
       ▼
简历 + JD 送入 LLM
       │
       ▼
LLM 输出优化后的简历全文
       │
       ▼
用户对比原版 → 确认 → 保存为新版本
```

```python
class ResumeOptimizer:
    def optimize_for_job(self, resume_text: str, job: dict) -> dict:
        prompt = """你是一位资深简历优化专家。针对目标岗位优化简历。

原始简历：
{resume_text}

目标岗位信息：
- 公司：{company}
- 岗位：{title}
- 要求：{requirements}
- 职责：{description}

优化要求：
1. 突出与岗位匹配的技能和经验
2. 项目描述改用 STAR 法则（情境→任务→行动→结果）
3. 增加量化数据（数字、百分比、规模）
4. 总长度与原版相近
5. 保持真实性，不编造经历

请输出：
{
    "optimized_sections": [
        {
            "section": "项目经验",
            "original": "...",
            "optimized": "...",
            "change_reason": "增加了量化指标"
        }
    ],
    "full_resume": "优化后的完整简历...",
    "summary": {
        "changes": ["改动1", "改动2"],
        "match_score_before": 6,
        "match_score_after": 8
    }
}"""

        result = self.llm.invoke(prompt.format(
            resume_text=resume_text,
            company=job.get("company_name", ""),
            title=job.get("title", ""),
            requirements=job.get("requirements", ""),
            description=job.get("description", "")
        ))
        return self.parse_json(result.content)
```

### 6.4 Prompt 分类

| 场景 | Prompt 重点 | temperature |
|------|------------|-------------|
| 简历诊断 | 结构化 JSON 输出，全面分析 | 0.3 |
| 定向优化 | STAR 法则，量化数据，匹配 JD | 0.5 |
| 项目润色 | 动词开头，数字量化，突出价值 | 0.6 |
| 技能推荐 | 基于 JD 分析差距 | 0.3 |

### 6.5 多版本管理

```python
class ResumeVersionManager:
    def save_version(self, user_id: int, version_data: dict):
        """保存简历版本"""
        # 存储到数据库或文件系统
        
    def get_versions(self, user_id: int) -> list:
        """获取版本历史"""
        
    def compare_versions(self, v1_id: int, v2_id: int) -> dict:
        """对比两个版本的差异"""
        # 返回逐段对照
```

---

## Step 7：岗位匹配

文件：`app/agents/rag/job_match.py`

### 7.1 匹配流程

```
1. 从向量库检索用户简历 chunks
2. 从数据库加载岗位 JD
3. 简历 + JD → LLM 逐维度打分
   - 技能匹配度 (1-10)
   - 经验匹配度 (1-10)
   - 城市匹配度 (1-10)
   - 薪资匹配度 (1-10)
4. 综合评分 + 分析 + 建议
```

### 7.2 匹配 Prompt

```
请分析候选人与岗位的匹配度。

简历摘要：{resume_chunks}
岗位要求：{job_description}

打分维度：
1. 技能匹配度（技术栈重合度）
2. 经验匹配度（年限、行业、项目）
3. 城市匹配度
4. 薪资匹配度

输出JSON格式评分 + 理由 + 改进建议。
```

---

## Step 8：API 接口

### 8.1 RAG 接口

文件：`app/api/v1/rag.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/rag/resume/query` | 简历问答 |
| POST | `/rag/job/match` | 岗位匹配度分析 |

### 8.2 简历优化接口

文件：`app/api/v1/resume_optimize.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/resume/diagnose` | 简历诊断 |
| POST | `/resume/optimize` | 定向优化（传入 job_id） |
| POST | `/resume/polish` | 单段润色 |
| GET | `/resume/versions` | 版本列表 |
| GET | `/resume/versions/compare` | 版本对比 |
| POST | `/resume/versions` | 保存新版本 |

---

## Step 9：前端集成

### 9.1 工作台 - 简历优化 Tab

在 `frontend/src/features/workbench/index.tsx` 新增：

```
┌──────────────────────────────────────────┐
│  简历管理  │  投递记录  │  AI 简历优化  │  ← 新增 Tab
└──────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  诊断报告                               │
│  ┌──────────────────────────────────────┐│
│  │  综合评分: 7/10                      ││
│  │  优势: React 熟练 / 项目经验丰富      ││
│  │  不足: 缺少量化数据 / 技能描述笼统    ││
│  │  建议: 项目描述用 STAR 法则          ││
│  └──────────────────────────────────────┘│
│                                          │
│  定向优化                                │
│  选择目标岗位:  [下拉框]                 │
│  [开始优化]                              │
│                                          │
│  优化结果                                │
│  ┌───── 原版 ─────┬───── 优化版 ──────┐ │
│  │ 负责前端开发    │ 基于React+TS重构   │ │
│  │                 │ 后台系统，加载优化  │ │
│  │                 │ 40%，覆盖10w+用户  │ │
│  └────────────────┴───────────────────┘ │
│  [保存版本] [导出 PDF]                   │
└──────────────────────────────────────────┘
```

### 9.2 API 封装

```typescript
export const optimizeApi = {
  diagnose: () => http.post('/api/v1/resume/diagnose'),
  optimize: (jobId: number) => http.post('/api/v1/resume/optimize', { job_id: jobId }),
  polish: (section: string, text: string) => http.post('/api/v1/resume/polish', { section, text }),
  getVersions: () => http.get('/api/v1/resume/versions'),
  compareVersions: (v1: number, v2: number) => http.get('/api/v1/resume/versions/compare', { params: { v1, v2 } }),
  saveVersion: (data: any) => http.post('/api/v1/resume/versions', data),
};
```

---

## Step 10：评估体系

文件：`app/agents/rag/evaluation.py`

### 10.1 RAG 问答评估

- 构建 30 条测试集（问题 + 相关 Chunk）
- 指标：Hit Rate、MRR
- 每次修改检索逻辑后跑一遍

### 10.2 简历优化评估（主观）

- 收集 5 份简历 + 5 个 JD
- AI 优化后人工评分（1-5）：描述质量、匹配度、真实性
- 记录每次优化耗时

---

## 数据流全景

```
用户上传简历 → PDF解析 → 分块 → Chroma入库
                                  │
                     ┌────────────┼────────────┐
                     ▼            ▼            ▼
                RAG 问答      岗位匹配     简历优化引擎
                (检索+生成)   (简历+JD)     (诊断+优化)
                     │            │            │
                     ▼            ▼            ▼
                AI 顾问回答   匹配度评分   优化版简历
                     │            │            │
                     └────────────┼────────────┘
                                  ▼
                            用户确认/保存
```

---

## 文件清单（完整）

```
app/agents/rag/
├── __init__.py
├── chroma_client.py       # Chroma 初始化 + CRUD
├── ingestion.py           # PDF 解析 + 分块 + 入库
├── retriever.py           # HyDE + Multi-Query + 基础检索
├── reranker.py            # BGE Reranker 重排
├── generator.py           # 问答生成 + 引用标注
├── resume_optimizer.py    # 简历诊断 + 定向优化 + 润色
├── job_match.py           # 岗位匹配度分析
├── evaluation.py          # RAGAS 评估指标
└── schemas.py             # Pydantic 请求响应

app/api/v1/
├── rag.py                 # RAG 接口
└── resume_optimize.py     # 简历优化接口

frontend/src/
├── services/api.ts        # + ragApi + optimizeApi
├── types/api.ts           # + 新类型
└── features/workbench/    # + AI 简历优化 Tab
```

---

## 实施顺序

```
Day 1: 环境 + PDF解析 + 分块
Day 2: Chroma入库 + 基础检索
Day 3: Reranker
Day 4: 问答生成 + RAG API
Day 5: 简历诊断 + 定向优化引擎
Day 6: 岗位匹配 + HyDE/Multi-Query
Day 7: 前端集成 + 联调 + 评估
```
