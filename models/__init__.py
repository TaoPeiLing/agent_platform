"""
模型定义模块

包含数据模型和类型定义。
"""

# 导出RBAC模块
from .rbac import (
    Role,
    ResourceType,
    Permission,
    RolePermissions,
    RBACManager,
    rbac_manager
)

__all__ = [
    # RBAC相关
    'Role',
    'ResourceType',
    'Permission',
    'RolePermissions',
    'RBACManager',
    'rbac_manager'
] 