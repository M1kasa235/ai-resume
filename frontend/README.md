# AI Job Assistant Frontend

一个功能完备、架构完善、性能优异的前端工程，基于 React 18 + TypeScript 5 + Vite 4 构建。

## 🚀 快速开始

### 环境要求

- Node.js >= 18.0.0
- npm >= 9.0.0

### 一键启动

```bash
# 克隆项目
git clone <repository-url>
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 可用脚本

```bash
# 开发
npm run dev          # 启动开发服务器 (http://localhost:5173)

# 构建
npm run build        # 构建生产版本
npm run preview      # 预览生产构建

# 代码质量
npm run lint         # ESLint 检查
npm run lint:fix     # ESLint 自动修复
npm run format       # Prettier 格式化代码
npm run format:check # Prettier 检查格式
npm run type-check   # TypeScript 类型检查

# 测试
npm run test         # 运行单元测试
npm run test:ui      # 运行测试 UI
npm run test:coverage # 运行测试覆盖率

# 组件文档
npm run storybook    # 启动 Storybook
npm run build-storybook # 构建 Storybook
```

## 📁 项目结构

```
frontend/
├── src/
│   ├── features/          # 业务功能模块
│   │   ├── auth/         # 认证相关
│   │   ├── dashboard/    # 仪表盘
│   │   ├── jobs/         # 岗位搜索
│   │   ├── questions/    # 题库练习
│   │   ├── workbench/    # 工作台
│   │   ├── profile/      # 个人中心
│   │   ├── settings/     # 设置
│   │   └── error/        # 错误页面
│   ├── components/       # 共享组件
│   │   ├── layouts/      # 布局组件
│   │   ├── AuthGuard/    # 权限守卫
│   │   ├── GuestGuard/   # 访客守卫
│   │   └── ErrorBoundary/ # 错误边界
│   ├── hooks/           # 自定义 Hooks
│   ├── services/        # API 服务
│   ├── stores/          # 状态管理
│   ├── utils/           # 工具函数
│   ├── types/           # TypeScript 类型
│   ├── constants/       # 常量定义
│   ├── router/          # 路由配置
│   ├── locales/         # 国际化
│   ├── styles/          # 样式文件
│   └── assets/          # 静态资源
├── public/              # 公共资源
├── tests/               # 测试文件
│   ├── unit/           # 单元测试
│   ├── e2e/            # E2E 测试
│   └── mocks/          # Mock 数据
├── .storybook/         # Storybook 配置
└── .husky/             # Git hooks
```

## 🛠️ 技术栈

### 核心框架
- **React 18** - 用户界面库
- **TypeScript 5** - 类型安全的 JavaScript
- **Vite 4** - 快速的前端构建工具

### 状态管理
- **Zustand** - 轻量级状态管理
- **React Query** - 服务端状态管理

### UI 组件
- **Ant Design 5** - 企业级 UI 组件库
- **Pro Components** - Ant Design 高级组件

### 路由
- **React Router v6** - 客户端路由

### 国际化
- **react-i18next** - 国际化解决方案

### HTTP 客户端
- **Axios** - HTTP 请求库

### 测试
- **Vitest** - 快速的单元测试框架
- **Testing Library** - 测试工具
- **Playwright** - E2E 测试

### 代码质量
- **ESLint** - 代码检查
- **Prettier** - 代码格式化
- **Husky** - Git hooks
- **lint-staged** - 提交前检查

### 监控
- **Sentry** - 错误监控
- **Web Vitals** - 性能监控

## 🔧 环境配置

### 开发环境

```bash
# 复制环境变量文件
cp .env.development .env.local

# 编辑环境变量
# .env.local
VITE_API_BASE_URL=http://localhost:8002/api/v1
VITE_APP_TITLE=AI Job Assistant
VITE_ENV=development
VITE_ENABLE_MOCK=true
VITE_LOG_LEVEL=debug
```

### 生产环境

```bash
# 复制环境变量文件
cp .env.production .env.local

# 编辑环境变量
# .env.local
VITE_API_BASE_URL=/api/v1
VITE_APP_TITLE=AI Job Assistant
VITE_ENV=production
VITE_ENABLE_MOCK=false
VITE_SENTRY_DSN=your-sentry-dsn
VITE_LOG_LEVEL=error
```

## 🎯 功能特性

### 1. 认证与授权
- JWT 双 Token 认证
- 自动 Token 刷新
- 权限守卫组件
- 路由级权限控制

### 2. 用户界面
- 响应式设计
- 暗色主题支持
- 国际化多语言
- 移动端适配

### 3. 业务功能
- 仪表盘数据统计
- 岗位搜索与筛选
- 题库练习系统
- 工作台管理
- 个人中心设置

### 4. 性能优化
- 代码分割 (Code Splitting)
- 懒加载 (Lazy Loading)
- 缓存策略
- 图片优化
- Service Worker

### 5. 开发体验
- TypeScript 类型安全
- 热模块替换 (HMR)
- 代码格式化
- ESLint 检查
- 自动化测试

## 📊 性能指标

### 目标性能指标
- 首屏加载时间 ≤ 1.5s (3G 网络)
- Lighthouse 性能得分 ≥ 90
- JavaScript 包体积 ≤ 250 KB (gzipped)
- 语句覆盖率 ≥ 80%
- 分支覆盖率 ≥ 75%

### 当前状态
- ✅ 代码分割配置
- ✅ 懒加载实现
- ✅ 缓存策略
- ✅ 图片优化
- ⏳ 性能监控集成

## 🧪 测试

### 单元测试
```bash
# 运行所有测试
npm run test

# 运行测试并显示覆盖率
npm run test:coverage

# 运行测试 UI
npm run test:ui
```

### E2E 测试
```bash
# 运行 E2E 测试
npm run test:e2e

# 运行 E2E 测试并生成报告
npm run test:e2e -- --reporter=list
```

### 测试覆盖率要求
- 语句覆盖率 ≥ 80%
- 分支覆盖率 ≥ 75%
- 函数覆盖率 ≥ 80%
- 行覆盖率 ≥ 80%

## 📚 组件文档

### Storybook
```bash
# 启动 Storybook
npm run storybook

# 构建 Storybook
npm run build-storybook
```

### 组件开发规范
1. 使用 TypeScript 定义组件 Props
2. 编写单元测试
3. 添加 Storybook 故事
4. 确保可访问性

## 🌐 国际化

### 支持的语言
- 简体中文 (zh-CN)
- 繁体中文 (zh-TW)
- English (en)

### 使用示例
```tsx
import { useTranslation } from 'react-i18next';

const MyComponent = () => {
  const { t } = useTranslation();
  
  return <h1>{t('welcome.title')}</h1>;
};
```

## 🔍 监控与日志

### Sentry 错误监控
- 自动捕获 JavaScript 错误
- Source Map 上传
- 性能监控
- 用户行为追踪

### Web Vitals 性能监控
- FCP (First Contentful Paint)
- LCP (Largest Contentful Paint)
- CLS (Cumulative Layout Shift)
- FID (First Input Delay)
- TTI (Time to Interactive)

## 🐳 Docker 部署

### 开发环境
```bash
# 构建开发镜像
docker build -f Dockerfile.dev -t ai-job-frontend-dev .

# 运行开发容器
docker run -p 5173:5173 ai-job-frontend-dev
```

### 生产环境
```bash
# 构建生产镜像
docker build -t ai-job-frontend .

# 运行生产容器
docker run -p 80:80 ai-job-frontend
```

## 🚀 CI/CD

### GitHub Actions 工作流
- 自动化测试
- 代码质量检查
- 构建部署
- 缓存刷新

### 触发条件
- Push 到 main 分支
- Pull Request 创建
- Release 发布

## 📝 常见问题

### 1. 依赖安装失败
```bash
# 清除缓存
npm cache clean --force

# 删除 node_modules
rm -rf node_modules

# 重新安装
npm install
```

### 2. TypeScript 类型错误
```bash
# 检查类型错误
npm run type-check

# 生成类型声明
npm run type-check -- --noEmit
```

### 3. ESLint 错误
```bash
# 自动修复
npm run lint:fix

# 检查错误
npm run lint
```

### 4. 测试失败
```bash
# 运行测试并显示详细信息
npm run test -- --run

# 运行特定测试文件
npm run test -- tests/unit/utils.test.ts
```

## 🤝 贡献指南

### 开发流程
1. Fork 项目
2. 创建功能分支
3. 开发并测试
4. 提交 Pull Request
5. 代码审查

### 代码规范
- 使用 ESLint 和 Prettier
- 编写测试用例
- 更新文档
- 遵循 Git 提交规范

### 提交规范
```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式化
refactor: 重构
test: 测试相关
chore: 构建或辅助工具变动
```

## 📄 许可证

MIT License

## 📞 支持

如有问题，请提交 Issue 或联系开发团队。

---

**注意**: 这是一个企业级前端项目，请遵循开发规范和最佳实践。