---
name: Project Roadmap
description: Full product roadmap for AI Job Assistant, covering all phases from bugfix to production
type: project
---

# AI Job Assistant — 产品路线图

## Phase 1：补全已有功能（当前阶段）

### 1.1 AI 面试后端实现
- **现状**：数据库模型 `AIInterview`、`AIInterviewQA` 已存在，前端 `aiInterviewApi` 已完整实现，但 `app/api/v1/` 下缺少 `ai_interview.py`
- **需要实现**：4 个接口 — POST `/sessions`、POST `/messages`、GET `/sessions/:id`、POST `/sessions/:id/end`
- **AI 集成**：接入 LangChain / 直接调用 DeepSeek 生成面试题、评估答案、打分

### 1.2 设置页面接入后端
- **现状**：纯前端 UI，开关和保存按钮无任何网络请求
- **需要实现**：新增 UserSettings 模型 / 复用 User 扩展字段，实现 GET/PUT `/users/settings` 接口

### 1.3 头像上传修复
- **现状**：Upload 组件缺少 `action` URL，`onChange` 为空壳
- **需要实现**：后端 `/users/avatar` 接口，前端填入真实 action

### 1.4 AI 顾问工具修复
- **现状**：agent.py 系统提示词声明了 `search_jobs`、`analyze_salary`、`get_job_recommendations` 三个工具，但实际只注册了 `tavily` 搜索工具
- **需要实现**：将这三个工具实现为真实 LangChain Tool，查询本地数据库

### 1.5 个人资料求职信息从后端加载
- **现状**：求职信息 tab 显示硬编码假数据
- **需要实现**：后端已有 User 模型字段（current_city, target_city, work_years, education），前端需要从 `/users/profile` 加载并展示

## Phase 2：核心体验增强

### 2.1 简历解析与智能分析
- 上传简历后自动解析（PDF 提取），填充到用户资料字段
- AI 分析简历优劣势，生成优化建议
- 简历完整度检测与补全引导

### 2.2 岗位智能匹配推荐
- 基于简历内容（技能、经验、目标城市）自动匹配推荐岗位
- "为你推荐"算法：关键词匹配 + 薪资匹配 + 城市过滤
- 匹配度标签展示（85% 匹配等）

### 2.3 AI 模拟面试增强
- 面试结束后生成综合评估报告（优势/劣势/改进建议）
- 按技术面/HR面/综合面不同维度的评分
- 面试历史对比和进步趋势

### 2.4 投递记录管理完善
- 批量删除、状态批量更新
- 投递看板（Kanban 视图）：待处理 → 筛选中 → 面试 → 录用/拒绝
- 投递统计图表（按公司、城市、时间维度）

## Phase 3：智能求职助手

### 3.1 智能问答系统升级
- Agent 可以查询本地数据库（我的投递、我的面试、我的错题）
- 上下文感知：知道用户当前进度，给出个性化建议
- 多轮对话中的意图识别与主动引导

### 3.2 求职报告自动生成
- 每周求职报告：投递数量、面试邀请、进展汇总
- AI 分析：哪些岗位类型反馈好，哪些需要调整
- 简历优化建议：基于市场反馈

### 3.3 薪资分析与谈判助手
- 基于岗位数据的薪资区间分析
- 按城市、经验、技能维度的薪资对比
- 面试后的薪资谈判策略建议

## Phase 4：管理后台

### 4.1 管理员后台
- 用户管理（列表、禁用、角色管理）
- 岗位审核与管理
- 题目管理（新增/编辑/分类维护）
- 数据统计大盘（注册量、投递量、活跃度）

### 4.2 内容运营
- 热门岗位推荐位管理
- 题库批量导入（Excel/JSON）
- 公司库管理

## Phase 5：生产化

### 5.1 基础设施
- 启用限流中间件
- 敏感信息迁移到环境变量（JWT Secret、数据库密码等）
- 日志分级与日志轮转
- API 文档完善

### 5.2 部署
- Docker 容器化
- 数据库迁移脚本（Alembic）
- CI/CD 流水线
- HTTPS 证书

### 5.3 监控与告警
- 接口性能监控
- 错误追踪
- 用户行为分析

---

## 技术债务清理

- advisorApi 从原生 fetch 迁移到统一 http 客户端
- 简历字段从 avatar_url 迁移到独立 resume_url 字段
- 移除硬编码默认密钥
- 前端类型统一（types/index.ts 与 types/api.ts 合并）
- 添加请求/响应类型，移除大量 `as any` 类型断言
