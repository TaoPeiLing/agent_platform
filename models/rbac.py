#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基于角色的访问控制(RBAC)模型

定义系统中使用的角色和权限结构。
"""

from enum import Enum, auto
from typing import List, Dict, Set, Optional, Union, Any


class Role(Enum):
    """系统角色定义"""
    # 系统角色
    ANONYMOUS = "anonymous"  # 未认证用户
    USER = "user"            # 基本用户
    DEVELOPER = "developer"  # 开发者
    ADMIN = "admin"          # 管理员
    SYSTEM = "system"        # 系统内部使用
    
    # 代理角色
    AGENT = "agent"          # 通用代理
    EXPERT_AGENT = "expert_agent"  # 专家代理
    TRIAGE_AGENT = "triage_agent"  # 分类代理
    
    # 自定义角色可在此处扩展
    
    def __str__(self) -> str:
        return self.value


class ResourceType(Enum):
    """资源类型定义"""
    TOOL = "tool"         # 工具
    AGENT = "agent"       # 代理
    SESSION = "session"   # 会话
    SYSTEM = "system"     # 系统
    DATA = "data"         # 数据
    API = "api"           # API
    USER = "user"         # 用户
    
    def __str__(self) -> str:
        return self.value


class Permission:
    """权限定义和助手类"""
    
    # API权限
    API_READ = "api.read"
    API_WRITE = "api.write"
    API_ADMIN = "api.admin"
    
    # 用户管理权限
    USER_READ = "user.read"
    USER_WRITE = "user.write"
    USER_ADMIN = "user.admin"
    
    # 代理权限
    AGENT_READ = "agent.read"
    AGENT_WRITE = "agent.write"
    AGENT_ADMIN = "agent.admin"
    AGENT_EXECUTE = "agent.execute"
    
    # 系统权限
    SYSTEM_READ = "system.read"
    SYSTEM_WRITE = "system.write"
    SYSTEM_ADMIN = "system.admin"
    
    @classmethod
    def get_default_permissions(cls, role: Role) -> List[str]:
        """获取角色的默认权限"""
        role_permissions = {
            Role.ANONYMOUS: [
                # 匿名用户只能进行有限的只读操作
            ],
            Role.USER: [
                cls.API_READ,
                cls.AGENT_READ,
                cls.AGENT_EXECUTE
            ],
            Role.DEVELOPER: [
                cls.API_READ,
                cls.API_WRITE,
                cls.AGENT_READ,
                cls.AGENT_WRITE,
                cls.AGENT_EXECUTE
            ],
            Role.ADMIN: [
                cls.API_READ,
                cls.API_WRITE,
                cls.API_ADMIN,
                cls.USER_READ,
                cls.USER_WRITE,
                cls.USER_ADMIN,
                cls.AGENT_READ,
                cls.AGENT_WRITE,
                cls.AGENT_ADMIN,
                cls.AGENT_EXECUTE,
                cls.SYSTEM_READ,
                cls.SYSTEM_WRITE
            ],
            Role.SYSTEM: [
                # 系统角色拥有所有权限
                cls.API_READ,
                cls.API_WRITE,
                cls.API_ADMIN,
                cls.USER_READ,
                cls.USER_WRITE,
                cls.USER_ADMIN,
                cls.AGENT_READ,
                cls.AGENT_WRITE,
                cls.AGENT_ADMIN,
                cls.AGENT_EXECUTE,
                cls.SYSTEM_READ,
                cls.SYSTEM_WRITE,
                cls.SYSTEM_ADMIN
            ],
            Role.AGENT: [
                cls.API_READ,
                cls.AGENT_READ,
                cls.AGENT_EXECUTE
            ],
            Role.EXPERT_AGENT: [
                cls.API_READ,
                cls.AGENT_READ,
                cls.AGENT_EXECUTE
            ],
            Role.TRIAGE_AGENT: [
                cls.API_READ,
                cls.AGENT_READ,
                cls.AGENT_EXECUTE
            ]
        }
        
        return role_permissions.get(role, [])
    
    @staticmethod
    def has_permission(required_permission: str, user_permissions: List[str]) -> bool:
        """检查用户是否拥有指定权限"""
        if not required_permission or not user_permissions:
            return False
            
        # 通配符权限检查
        parts = required_permission.split('.')
        if len(parts) != 2:
            return False
            
        # 检查精确匹配
        if required_permission in user_permissions:
            return True
            
        # 检查通配符匹配 (例如 "api.*" 匹配所有 "api." 开头的权限)
        wildcard = f"{parts[0]}.*"
        if wildcard in user_permissions:
            return True
            
        # 检查管理员权限
        admin = f"{parts[0]}.admin"
        if admin in user_permissions:
            return True
            
        return False


class RBACService:
    """RBAC服务，提供角色和权限管理功能"""
    
    @staticmethod
    def get_roles_permissions(roles: List[str]) -> List[str]:
        """获取角色列表的所有权限"""
        all_permissions = set()
        
        for role_str in roles:
            try:
                # 尝试将字符串转换为Role枚举
                role = Role(role_str)
                role_permissions = Permission.get_default_permissions(role)
                all_permissions.update(role_permissions)
            except ValueError:
                # 如果不是标准角色，则忽略
                continue
                
        return list(all_permissions)
    
    @staticmethod
    def has_role(required_role: Union[Role, str], user_roles: List[str]) -> bool:
        """检查用户是否拥有指定角色"""
        if isinstance(required_role, Role):
            required_role = required_role.value
            
        return required_role in user_roles
    
    @staticmethod
    def has_any_role(required_roles: List[Union[Role, str]], user_roles: List[str]) -> bool:
        """检查用户是否拥有任一指定角色"""
        for role in required_roles:
            if RBACService.has_role(role, user_roles):
                return True
        return False
    
    @staticmethod
    def has_all_roles(required_roles: List[Union[Role, str]], user_roles: List[str]) -> bool:
        """检查用户是否拥有所有指定角色"""
        for role in required_roles:
            if not RBACService.has_role(role, user_roles):
                return False
        return True
    
    @staticmethod
    def check_permission(required_permission: str, user_permissions: List[str]) -> bool:
        """检查用户是否拥有指定权限"""
        return Permission.has_permission(required_permission, user_permissions)
    
    @staticmethod
    def check_any_permission(required_permissions: List[str], user_permissions: List[str]) -> bool:
        """检查用户是否拥有任一指定权限"""
        for permission in required_permissions:
            if Permission.has_permission(permission, user_permissions):
                return True
        return False
    
    @staticmethod
    def check_all_permissions(required_permissions: List[str], user_permissions: List[str]) -> bool:
        """检查用户是否拥有所有指定权限"""
        for permission in required_permissions:
            if not Permission.has_permission(permission, user_permissions):
                return False
        return True


# 创建一个简单的RBAC管理器实例
class RBACManager:
    """RBAC管理器，提供资源权限管理和验证功能"""
    
    def __init__(self):
        """初始化RBAC管理器"""
        self._tool_permissions = {}  # 工具权限映射
        
    def has_permission(self, roles: List[Role], resource_type: ResourceType, resource_id: str, action: str) -> bool:
        """
        检查角色是否有权限对资源执行操作
        
        Args:
            roles: 角色列表
            resource_type: 资源类型
            resource_id: 资源ID
            action: 动作名称
            
        Returns:
            是否有权限
        """
        # 管理员角色有所有权限
        if Role.ADMIN in roles or Role.SYSTEM in roles:
            return True
            
        # 基于资源类型的简单权限检查
        if resource_type == ResourceType.TOOL:
            return self._check_tool_permission(roles, resource_id)
            
        # 可在此处添加更多资源类型的权限检查
        
        # 默认情况下，开发者对大多数资源有访问权限
        if Role.DEVELOPER in roles:
            return True
            
        # 默认拒绝
        return False
    
    def _check_tool_permission(self, roles: List[Role], tool_name: str) -> bool:
        """检查是否有权限使用工具"""
        # 如果没有特殊限制，允许以下角色使用工具
        allowed_roles = [Role.DEVELOPER, Role.ADMIN, Role.SYSTEM, Role.AGENT, Role.EXPERT_AGENT]
        
        for role in roles:
            if role in allowed_roles:
                return True
                
        # 可以在这里添加更细粒度的工具权限控制
        
        return False
    
    def get_allowed_tools(self, roles: List[Role]) -> Set[str]:
        """
        获取角色允许使用的工具集合
        
        Args:
            roles: 角色列表
            
        Returns:
            允许使用的工具集合，'*'表示所有工具
        """
        # 管理员和系统角色可以使用所有工具
        if Role.ADMIN in roles or Role.SYSTEM in roles:
            return {'*'}
            
        # 开发者也可以使用所有工具
        if Role.DEVELOPER in roles:
            return {'*'}
            
        # 默认工具集合
        allowed_tools = set()
        
        # 可以在这里基于角色添加更多允许的工具
        if Role.AGENT in roles or Role.EXPERT_AGENT in roles:
            allowed_tools.update([
                'search_knowledge',
                'search_web',
                'get_current_weather',
                'summarize_text',
                'analyze_code'
            ])
            
        if Role.USER in roles:
            allowed_tools.update([
                'search_knowledge',
                'get_current_weather'
            ])
            
        return allowed_tools


# 创建全局RBAC管理器实例
rbac_manager = RBACManager() 