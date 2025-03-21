"""
认证上下文模块

提供管理用户认证信息和外部系统令牌的功能。
"""

import time
from typing import Dict, Any, Optional, List, Set, Union
from dataclasses import dataclass, field


@dataclass
class ExternalSystemConfig:
    """外部系统认证配置"""
    system_id: str  # 系统唯一标识
    auth_type: str  # 认证类型: oauth2, api_key, jwt, basic
    auth_url: Optional[str] = None  # 认证URL（OAuth2等需要）
    auth_header_name: Optional[str] = None  # 认证头名称
    token_parameter_name: Optional[str] = None  # 令牌参数名称
    additional_params: Dict[str, Any] = field(default_factory=dict)  # 附加参数
    
    def get_auth_redirect_url(self, callback_url: Optional[str] = None) -> Optional[str]:
        """获取认证重定向URL"""
        if self.auth_type != 'oauth2' or not self.auth_url:
            return None
            
        url = self.auth_url
        if callback_url and '?' not in url:
            url = f"{url}?callback_url={callback_url}"
        elif callback_url:
            url = f"{url}&callback_url={callback_url}"
            
        return url


class AuthContext:
    """认证上下文
    
    管理用户身份和外部系统认证令牌。
    """
    
    def __init__(self, user_id: str, roles: List[str] = None):
        self.user_id = user_id
        self.roles = roles or []
        self.auth_tokens: Dict[str, str] = {}  # 外部系统令牌: system_id -> token
        self.auth_expiry: Dict[str, int] = {}  # 令牌过期时间: system_id -> timestamp
        self.metadata: Dict[str, Any] = {}  # 附加元数据
        
    def set_token(self, system_id: str, token: str, expiry: Optional[int] = None) -> None:
        """设置外部系统令牌
        
        Args:
            system_id: 外部系统ID
            token: 认证令牌
            expiry: 过期时间戳（秒）
        """
        self.auth_tokens[system_id] = token
        
        if expiry is not None:
            self.auth_expiry[system_id] = expiry
        else:
            # 默认1小时过期
            self.auth_expiry[system_id] = int(time.time()) + 3600
            
    def get_token(self, system_id: str) -> Optional[str]:
        """获取外部系统令牌
        
        Args:
            system_id: 外部系统ID
            
        Returns:
            认证令牌，如果不存在或已过期则返回None
        """
        if not self.is_token_valid(system_id):
            return None
            
        return self.auth_tokens.get(system_id)
        
    def remove_token(self, system_id: str) -> None:
        """删除外部系统令牌
        
        Args:
            system_id: 外部系统ID
        """
        if system_id in self.auth_tokens:
            del self.auth_tokens[system_id]
            
        if system_id in self.auth_expiry:
            del self.auth_expiry[system_id]
            
    def is_token_valid(self, system_id: str) -> bool:
        """检查令牌是否有效（存在且未过期）
        
        Args:
            system_id: 外部系统ID
            
        Returns:
            如果令牌有效则返回True，否则返回False
        """
        if system_id not in self.auth_tokens:
            return False
            
        expiry = self.auth_expiry.get(system_id)
        if expiry is None:
            return True  # 如果没有设置过期时间，则认为永不过期
            
        return expiry > int(time.time())
        
    def clear_expired_tokens(self) -> None:
        """清除所有已过期的令牌"""
        now = int(time.time())
        expired_systems = [
            system_id for system_id, expiry in self.auth_expiry.items()
            if expiry <= now
        ]
        
        for system_id in expired_systems:
            self.remove_token(system_id)
            
    def to_dict(self) -> Dict[str, Any]:
        """将认证上下文转换为字典"""
        return {
            "user_id": self.user_id,
            "roles": self.roles,
            "auth_tokens": self.auth_tokens,
            "auth_expiry": self.auth_expiry,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthContext":
        """从字典创建认证上下文"""
        context = cls(user_id=data["user_id"], roles=data.get("roles", []))
        context.auth_tokens = data.get("auth_tokens", {})
        context.auth_expiry = data.get("auth_expiry", {})
        context.metadata = data.get("metadata", {})
        return context


class SessionExtension:
    """会话扩展
    
    为会话对象提供认证上下文支持。
    """
    
    def __init__(self, auth_context: AuthContext):
        self.auth_context = auth_context
        
    @classmethod
    def from_session(cls, session) -> "SessionExtension":
        """从会话对象创建会话扩展
        
        Args:
            session: 会话对象
            
        Returns:
            会话扩展对象
        """
        # 尝试从现有会话获取认证上下文
        existing_auth_context = getattr(session, "auth_context", None)
        if existing_auth_context and isinstance(existing_auth_context, AuthContext):
            # 清除过期令牌
            existing_auth_context.clear_expired_tokens()
            return cls(existing_auth_context)
            
        # 创建新的认证上下文
        user_id = getattr(session, "user_id", "anonymous")
        roles = getattr(session, "roles", [])
        
        auth_context = AuthContext(user_id=user_id, roles=roles)
        return cls(auth_context)
        
    def update_session(self, session) -> None:
        """更新会话对象的认证上下文
        
        Args:
            session: 会话对象
        """
        # 设置会话的认证上下文
        setattr(session, "auth_context", self.auth_context)
        
        # 同步会话的用户ID和角色
        setattr(session, "user_id", self.auth_context.user_id)
        setattr(session, "roles", self.auth_context.roles) 