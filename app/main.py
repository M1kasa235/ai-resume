# app/main.py
from contextlib import asynccontextmanager
import logging

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1 import auth, user, jobs, dashboard, workbench, questions, rag, resume_optimize, agent_chat, resume_versions, admin, interview, memory
from app.db.session import engine
from app.db.base import Base
from app.core.exceptions import AppException
from app.core.limiter import RateLimitMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时：创建数据库表（开发环境）
    关闭时：清理资源
    """
    # 启动事件
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        if settings.DEBUG:
            print("数据库表已创建/确认")

        # 长期记忆：建表 + 清理过期
        try:
            from app.agents.memory import MemoryService
            ms = MemoryService()
            await ms._ensure_table()
            await ms.decay_all()
            if settings.DEBUG:
                print("长期记忆表已创建/确认，过期记忆已清理")
        except Exception as e:
            print(f"[WARNING] 记忆表初始化失败: {e}")

        # 恢复卡住的评估任务（服务重启后）
        try:
            from app.api.v1.interview import recover_stuck_evaluations
            await recover_stuck_evaluations()
        except Exception as e:
            print(f"[WARNING] 评估恢复失败（服务仍会启动）: {e}")
    except Exception as e:
        print(f"[WARNING] 数据库表创建失败（服务仍会启动）: {e}")

    yield

    # 关闭事件
    await engine.dispose()
    print("数据库连接已释放")


def create_application() -> FastAPI:
    """应用工厂"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI 求职助手后端 API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    

    # 添加限流中间件
    app.add_middleware(RateLimitMiddleware)

    # CORS 配置（从环境变量读取，生产环境应限制具体域名）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(auth.router, prefix=settings.API_V1_STR)
    app.include_router(user.router, prefix=settings.API_V1_STR)
    app.include_router(jobs.router, prefix=settings.API_V1_STR)
    app.include_router(dashboard.router, prefix=settings.API_V1_STR)
    app.include_router(workbench.router, prefix=settings.API_V1_STR)
    app.include_router(questions.router, prefix=settings.API_V1_STR)
    app.include_router(rag.router, prefix=settings.API_V1_STR)
    app.include_router(resume_optimize.router, prefix=settings.API_V1_STR)
    app.include_router(agent_chat.router, prefix=settings.API_V1_STR)
    app.include_router(resume_versions.router, prefix=settings.API_V1_STR)
    app.include_router(admin.router, prefix=settings.API_V1_STR)
    app.include_router(interview.router, prefix=settings.API_V1_STR)
    app.include_router(memory.router, prefix=settings.API_V1_STR)
    
    # 挂载静态文件目录（用于访问上传的简历 PDF）
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    # 注册全局异常处理器
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """处理自定义应用异常"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.detail,
                "data": exc.data
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理未捕获的通用异常"""
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"未捕获的异常:\n{error_detail}")
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "detail": str(exc) if settings.DEBUG else "服务器内部错误",
                "traceback": error_detail if settings.DEBUG else None
            }
        )

    @app.get("/health")
    async def health_check():
        """健康检查接口"""
        return {"status": "ok", "version": "1.0.0"}

    return app

app = create_application()