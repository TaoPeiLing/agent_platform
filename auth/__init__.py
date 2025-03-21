"""
认证和授权模块

提供用户认证、权限管理和外部系统认证集成的功能。
"""

from .auth_context import (
    AuthContext,
    SessionExtension,
    ExternalSystemConfig
)
from .auth_service import (
    AuthService,
    auth_service
)
from .permission_service import (
    Permission,
    Role,
    ResourceType,
    ResourcePolicy,
    PermissionService,
    permission_service
)

__all__ = [
    # 认证上下文
    'AuthContext',
    'SessionExtension',
    'ExternalSystemConfig',
    
    # 认证服务
    'AuthService',
    'auth_service',
    
    # 权限服务
    'Permission',
    'Role',
    'ResourceType',
    'ResourcePolicy',
    'PermissionService',
    'permission_service'
]

__version__ = '0.1.0' 