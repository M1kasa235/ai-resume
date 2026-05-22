# AI Job Assistant - Backend

AI 求职助手后端 API，基于 FastAPI + SQLAlchemy 构建，提供岗位管理、简历投递、AI 面试模拟等功能。

## 🚀 快速开始

### 环境要求

- Python 3.10+
- MySQL 8.0+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/M1kasa235/ai-resume.git
cd ai-resume
```

2. **创建虚拟环境**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
# 复制示例配置文件
cp .env.example .env  # Linux/Mac
# 或 copy .env.example .env  # Windows

# 编辑 .env 文件，修改数据库配置和 SECRET_KEY
# ⚠️ 重要：不要将 .env 文件提交到 Git！
```

5. **创建数据库**
```sql
CREATE DATABASE ai_job CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

6. **启动服务**
```bash
python run.py
```

服务将在 http://127.0.0.1:8002 启动

## 📚 API 文档

启动服务后访问：
- Swagger UI: http://127.0.0.1:8002/docs
- ReDoc: http://127.0.0.1:8002/redoc

## 🛠️ 技术栈

- **Web 框架**: FastAPI 0.115
- **数据库**: MySQL + SQLAlchemy 2.0 (Async)
- **认证**: JWT (python-jose)
- **数据验证**: Pydantic V2
- **密码加密**: bcrypt
- **AI Agent**: LangChain

## 📁 项目结构

```
app/
├── api/v1/          # API 路由
│   ├── auth.py      # 认证接口
│   ├── jobs.py      # 岗位接口
│   ├── user.py      # 用户接口
│   ├── dashboard.py # 数据统计
│   ├── workbench.py # 工作台
│   └── questions.py # 题库
├── core/            # 核心配置
│   ├── config.py    # 环境变量
│   ├── security.py  # 安全工具
│   └── exceptions.py# 异常处理
├── models/          # 数据模型
├── schemas/         # Pydantic 模型
├── services/        # 业务逻辑
└── db/              # 数据库会话
```

## 🔑 主要功能

- ✅ 用户注册/登录（JWT 认证）
- ✅ 岗位管理（CRUD + 多维度搜索）
- ✅ 简历上传与管理
- ✅ 投递记录跟踪
- ✅ Dashboard 数据统计
- ✅ 题库系统
- ✅ 收藏功能

## ⚙️ 配置说明

关键环境变量（`.env` 文件）：

```env
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=ai_job

# JWT 密钥（生产环境务必修改）
SECRET_KEY=your-secret-key

# CORS 配置
CORS_ORIGINS=["http://localhost:5173"]
```

生成强 SECRET_KEY：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🧪 测试

```bash
pytest
```

## 📝 注意事项

1. **首次运行**会自动创建数据库表（开发模式）
2. **生产环境**请修改 `SECRET_KEY` 为强密码
3. **上传文件**存储在 `uploads/` 目录
4. **限流中间件**默认禁用，需要时可在 `main.py` 中启用

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
