"""
认证服务模块

提供外部系统认证服务，管理认证配置、认证回调和认证流程。
"""

import logging
import time
from typing import Dict, Optional, Any, List, Tuple, Callable
from dataclasses import dataclass

from .auth_context import ExternalSystemConfig, AuthContext

# 配置日志
logger = logging.getLogger(__name__)


class AuthService:
    """认证服务
    
    管理外部系统认证配置、令牌验证和认证回调。
    """
    
    def __init__(self):
        # 系统配置: system_id -> ExternalSystemConfig
        self.external_systems: Dict[str, ExternalSystemConfig] = {}
        
        # 认证回调: system_id -> callback_function
        self.auth_callbacks: Dict[str, Callable] = {}
        
        # 认证验证器: system_id -> validator_function
        self.token_validators: Dict[str, Callable] = {}
        
        logger.info("认证服务已初始化")
        
    def register_external_system(self, config: ExternalSystemConfig) -> None:
        """注册外部系统
        
        Args:
            config: 外部系统配置
        """
        if config.system_id in self.external_systems:
            logger.info(f"更新外部系统认证配置: {config.system_id}")
        else:
            logger.info(f"注册新的外部系统: {config.system_id}")
            
        self.external_systems[config.system_id] = config
        
    def unregister_external_system(self, system_id: str) -> None:
        """取消注册外部系统
        
        Args:
            system_id: 系统ID
        """
        if system_id in self.external_systems:
            del self.external_systems[system_id]
            logger.info(f"已移除外部系统: {system_id}")
            
        # 同时清除相关的回调和验证器
        if system_id in self.auth_callbacks:
            del self.auth_callbacks[system_id]
            
        if system_id in self.token_validators:
            del self.token_validators[system_id]
            
    def get_external_system(self, system_id: str) -> Optional[ExternalSystemConfig]:
        """获取外部系统配置
        
        Args:
            system_id: 系统ID
            
        Returns:
            外部系统配置，如果不存在则返回None
        """
        return self.external_systems.get(system_id)
        
    def list_external_systems(self) -> List[str]:
        """列出所有注册的外部系统
        
        Returns:
            系统ID列表
        """
        return list(self.external_systems.keys())
        
    def register_auth_callback(
        self, system_id: str, callback: Callable[[str, Dict[str, Any]], Tuple[str, int]]
    ) -> None:
        """注册认证回调函数
        
        Args:
            system_id: 系统ID
            callback: 回调函数，接收用户ID和认证参数，返回(token, expiry)元组
        """
        self.auth_callbacks[system_id] = callback
        logger.info(f"已注册{system_id}系统的认证回调")
        
    def register_token_validator(
        self, system_id: str, validator: Callable[[str], bool]
    ) -> None:
        """注册令牌验证器
        
        Args:
            system_id: 系统ID
            validator: 验证函数，接收令牌并返回是否有效
        """
        self.token_validators[system_id] = validator
        logger.info(f"已注册{system_id}系统的令牌验证器")
        
    def validate_token(self, system_id: str, token: str) -> bool:
        """验证令牌是否有效
        
        Args:
            system_id: 系统ID
            token: 待验证的令牌
            
        Returns:
            如果令牌有效则返回True，否则返回False
        """
        # 检查是否有自定义验证器
        if system_id in self.token_validators:
            try:
                return self.token_validators[system_id](token)
            except Exception as e:
                logger.error(f"验证{system_id}令牌时出错: {e}")
                return False
                
        # 默认实现: 假设令牌非空即有效
        return bool(token)
        
    def authenticate(
        self, system_id: str, user_id: str, auth_params: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[int]]:
        """执行认证过程
        
        Args:
            system_id: 系统ID
            user_id: 用户ID
            auth_params: 认证参数
            
        Returns:
            (token, expiry)元组，如果认证失败则返回(None, None)
        """
        # 检查系统是否注册
        if system_id not in self.external_systems:
            logger.error(f"未注册的外部系统: {system_id}")
            return None, None
            
        # 检查是否有自定义认证回调
        if system_id in self.auth_callbacks:
            try:
                return self.auth_callbacks[system_id](user_id, auth_params)
            except Exception as e:
                logger.error(f"执行{system_id}认证回调时出错: {e}")
                return None, None
                
        # 默认实现: 生成简单令牌
        token = f"dummy_token_{system_id}_{user_id}_{int(time.time())}"
        expiry = int(time.time()) + 3600  # 1小时后过期
        
        logger.warning(f"使用默认认证机制为{system_id}生成令牌")
        return token, expiry
        
    def get_auth_url(self, system_id: str, callback_url: Optional[str] = None) -> Optional[str]:
        """获取认证URL
        
        Args:
            system_id: 系统ID
            callback_url: 认证完成后的回调URL
            
        Returns:
            认证URL，如果系统不存在或不支持则返回None
        """
        config = self.get_external_system(system_id)
        if not config:
            logger.error(f"未注册的外部系统: {system_id}")
            return None
            
        return config.get_auth_redirect_url(callback_url)
        
    def extract_auth_header(self, system_id: str, headers: Dict[str, str]) -> Optional[str]:
        """从请求头中提取认证信息
        
        Args:
            system_id: 系统ID
            headers: 请求头字典
            
        Returns:
            认证令牌，如果未找到则返回None
        """
        config = self.get_external_system(system_id)
        if not config or not config.auth_header_name:
            return None
            
        # 标准化头名称
        header_name = config.auth_header_name.lower()
        
        # 在请求头中查找
        for name, value in headers.items():
            if name.lower() == header_name:
                return value
                
        return None


# 全局实例
auth_service = AuthService() 