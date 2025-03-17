"""配置模块。

提供环境变量和配置的加载功能。
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置设置。

    从环境变量加载配置，支持.env文件。
    """

    # OpenAI API设置
    OPENAI_API_KEY: str

    # 数据库设置
    DATABASE_URL: str

    # Redis设置
    REDIS_URL: str

    # 应用设置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str

    # 日志设置
    LOG_LEVEL: str = "INFO"

    # 文件路径
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    @field_validator("ENV")
    def env_must_be_valid(cls, v: str) -> str:
        """验证环境名称是否有效。"""
        valid_envs = ["development", "testing", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"ENV must be one of {valid_envs}")
        return v.lower()

    @field_validator("LOG_LEVEL")
    def log_level_must_be_valid(cls, v: str) -> str:
        """验证日志级别是否有效。"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    class Config:
        """Pydantic配置类。"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例，用于依赖注入。"""
    return settings