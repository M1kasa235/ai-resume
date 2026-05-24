# app/core/config.py
from functools import lru_cache
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 基础配置
    APP_NAME: str = "Offer Pilot"
    DEBUG: bool = False
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8080
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "ai_job"

    # 异步数据库URL
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"

    # JWT配置
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 密码加密
    BCRYPT_ROUNDS: int = 12

    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # LLM 配置
    DASHSCOPE_BASE_URL: str = ""
    DASHSCOPE_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = ""
    RAG_EMBEDDING_MODEL: str = "text-embedding-v4"
    RAG_RERANK_MODEL: str = "gte-rerank-v2"

    # 搜索引擎配置
    TAVILY_API_KEY: str = ""

    # 记忆事件后台处理
    MEMORY_EVENT_WORKER_ENABLED: bool = True
    MEMORY_EVENT_WORKER_INTERVAL_SECONDS: int = 20
    MEMORY_EVENT_WORKER_BATCH_SIZE: int = 20
    MEMORY_EVENT_MAX_RETRIES: int = 3

    # 上下文注入预算
    CONTEXT_USE_BUNDLE: bool = True
    CONTEXT_TOTAL_MAX_CHARS: int = 3000
    CONTEXT_SYSTEM_MAX_CHARS: int = 80
    CONTEXT_MEMORY_MAX_CHARS: int = 520
    CONTEXT_HISTORY_MAX_CHARS: int = 400
    CONTEXT_USER_MAX_CHARS: int = 2000
    CONTEXT_STRIP_API_DATE_PREFIX: bool = True

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if not v or v == "your-super-secret-key-change-this-in-production":
            raise ValueError("SECRET_KEY 必须设置为强密码，请修改 .env 文件")
        return v

    @field_validator("MYSQL_PASSWORD")
    @classmethod
    def mysql_password_must_be_set(cls, v: str) -> str:
        if not v:
            raise ValueError("MYSQL_PASSWORD 不能为空，请修改 .env 文件")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


@lru_cache()
def get_settings() -> Settings:
    """缓存配置，避免重复读取"""
    return Settings()


settings = get_settings()