#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安全与授权模块

提供API密钥管理、JWT认证、权限控制和内容安全保障功能。
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 设置日志
logger = logging.getLogger(__name__)

# 导入安全模块的服务组件
from .api_key import APIKeyManager
from .jwt_auth import JWTAuthService
from .middleware import AuthMiddleware
from .security_service import SecurityService
from .guardrails import GuardrailsService


# 获取配置目录
def _get_config_dir() -> Path:
    """获取配置目录"""
    # 尝试从环境变量获取
    config_dir = os.environ.get("SSS_CONFIG_DIR")
    if config_dir:
        return Path(config_dir)
    
    # 默认配置目录
    base_dir = Path(__file__).parent.parent.parent
    return base_dir / "configs"


def _load_security_config() -> Dict[str, Any]:
    """加载安全配置"""
    config_dir = _get_config_dir()
    config_file = config_dir / "security_config.json"
    
    # 默认配置
    default_config = {
        "api_key_settings": {
            "storage_dir": "data/security/keys",
            "default_expiry_days": 90,
            "key_prefix_length": 8,
            "key_secret_length": 32
        },
        "jwt_settings": {
            "secret_key": os.environ.get("JWT_SECRET_KEY", "default_secret_key_change_in_production"),
            "algorithm": "HS256",
            "access_token_expire_minutes": 30,
            "refresh_token_expire_days": 7
        },
        "guardrails": {
            "default_rate_limit": 10,
            "default_time_window": 60,
            "api_rate_limit": 100,
            "api_time_window": 60,
            "model_rate_limit": 20,
            "model_time_window": 60,
            "model_token_limit": 100000,
            "model_call_limit": 1000,
            "api_call_limit": 5000,
            "storage_limit_mb": 100
        }
    }
    
    # 如果配置文件存在，加载它
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                # 合并配置
                for section in default_config:
                    if section in file_config:
                        default_config[section].update(file_config[section])
                # 添加不在默认配置中的部分
                for section in file_config:
                    if section not in default_config:
                        default_config[section] = file_config[section]
        except Exception as e:
            logger.warning(f"加载安全配置文件失败: {e}")
    
    return default_config


# 加载配置
security_config = _load_security_config()

# 创建服务实例
api_key_manager = APIKeyManager(
    storage_dir=security_config["api_key_settings"]["storage_dir"],
    default_expiry_days=security_config["api_key_settings"].get("default_expiry_days", 90),
    key_prefix_length=security_config["api_key_settings"].get("key_prefix_length", 8),
    key_secret_length=security_config["api_key_settings"].get("key_secret_length", 32)
)

jwt_auth_service = JWTAuthService(
    secret_key=security_config["jwt_settings"]["secret_key"],
    algorithm=security_config["jwt_settings"].get("algorithm", "HS256"),
    access_token_expire_minutes=security_config["jwt_settings"].get("access_token_expire_minutes", 30),
    refresh_token_expire_days=security_config["jwt_settings"].get("refresh_token_expire_days", 7)
)

guardrails_service = GuardrailsService(config=security_config["guardrails"])

# 创建安全服务实例
security_service = SecurityService(
    api_key_manager=api_key_manager,
    jwt_auth_service=jwt_auth_service,
    guardrails_service=guardrails_service
)

# 导出公共组件
__all__ = [
    "security_service",       # 综合安全服务
    "api_key_manager",        # API密钥管理器
    "jwt_auth_service",       # JWT认证服务
    "guardrails_service",     # 内容安全服务
    "AuthMiddleware",         # 认证中间件
    "SecurityService",        # 安全服务类
    "APIKeyManager",          # API密钥管理器类
    "JWTAuthService",         # JWT认证服务类
    "GuardrailsService"       # 内容安全服务类
] 