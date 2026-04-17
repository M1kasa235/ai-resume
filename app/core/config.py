# app/core/config.py
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 基础配置
    APP_NAME: str = "AI Job Assistant"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "mysql80"
    MYSQL_DB: str = "ai_job"

    # 异步数据库URL
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"

    # JWT配置
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"  # 与 .env 文件保持一致
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Access Token 30分钟
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Refresh Token 7天

    # 密码加密
    BCRYPT_ROUNDS: int = 12

    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


@lru_cache()
def get_settings() -> Settings:
    """缓存配置，避免重复读取"""
    return Settings()


settings = get_settings()