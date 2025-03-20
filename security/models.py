"""
安全系统数据模型

定义安全系统使用的数据结构，包括API密钥、JWT令牌信息等。
"""

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union


class KeyStatus(enum.Enum):
    """API密钥状态枚举"""
    ACTIVE = "active"     # 密钥有效且可用
    REVOKED = "revoked"   # 密钥被手动撤销
    EXPIRED = "expired"   # 密钥已过期


@dataclass
class APIKey:
    """API密钥模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    prefix: str  # 密钥前缀（公开部分，通常8个字符）
    secret_hash: str  # 密钥主体的哈希值（存储时使用）
    service_account_id: str  # 关联的服务账户ID
    description: str  # 密钥用途描述
    permissions: List[str] = field(default_factory=list)  # 权限列表
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None  # 过期时间，None表示永不过期
    last_used_at: Optional[datetime] = None  # 最后使用时间
    status: KeyStatus = KeyStatus.ACTIVE  # 密钥状态
    metadata: Dict[str, Any] = field(default_factory=dict)  # 附加元数据
    
    @property
    def is_active(self) -> bool:
        """判断密钥是否有效"""
        if self.status != KeyStatus.ACTIVE:
            return False
        
        if self.expires_at and self.expires_at < datetime.now():
            return False
            
        return True


@dataclass
class APIKeyResponse:
    """API密钥创建响应（包含完整密钥，仅在创建时返回一次）"""
    id: str
    prefix: str
    full_key: str  # 完整的API密钥（prefix.secret）
    service_account_id: str
    description: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]


@dataclass
class APIKeyInfo:
    """API密钥信息（不含密钥机密部分，用于列表展示）"""
    id: str
    prefix: str
    service_account_id: str
    description: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    status: KeyStatus
    metadata: Dict[str, Any]


@dataclass
class JWTTokenData:
    """JWT令牌数据"""
    sub: str  # 主题（通常是用户ID或服务账户ID）
    iss: str = "sss_agent_platform"  # 签发者
    iat: datetime = field(default_factory=datetime.now)  # 签发时间
    exp: Optional[datetime] = None  # 过期时间
    roles: List[str] = field(default_factory=list)  # 角色列表
    permissions: List[str] = field(default_factory=list)  # 权限列表
    metadata: Dict[str, Any] = field(default_factory=dict)  # 附加元数据


@dataclass
class AuthResult:
    """认证结果"""
    success: bool
    subject_id: Optional[str] = None  # 认证主体ID
    auth_type: Optional[str] = None  # 认证类型: "api_key", "jwt", "oauth", 等
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    error: Optional[str] = None  # 错误信息
    metadata: Dict[str, Any] = field(default_factory=dict)  # 附加元数据

    @property
    def is_authenticated(self) -> bool:
        """是否认证成功"""
        return self.success and self.subject_id is not None
        
    def has_permission(self, permission: str) -> bool:
        """检查是否拥有特定权限"""
        return permission in self.permissions
        
    def has_role(self, role: str) -> bool:
        """检查是否拥有特定角色"""
        return role in self.roles


@dataclass
class ServiceAccount:
    """服务账户"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # 服务账户名称
    description: str  # 描述
    owner_id: Optional[str] = None  # 所有者ID (可以是用户或组织)
    roles: List[str] = field(default_factory=list)  # 角色列表
    permissions: List[str] = field(default_factory=list)  # 权限列表
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)  # 附加元数据
    is_active: bool = True  # 是否活跃 