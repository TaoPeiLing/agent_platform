"""
简化版RBAC（基于角色的访问控制）模型

此模块定义了基本的角色和权限模型，用于控制代理工具的访问权限。
"""
from enum import Enum
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field


class Role(str, Enum):
    """预定义的角色"""
    GUEST = "guest"        # 访客角色，最小权限
    USER = "user"          # 普通用户，基本权限
    POWER_USER = "power_user"  # 高级用户，更多权限
    ADMIN = "admin"        # 管理员，几乎所有权限
    SYSTEM = "system"      # 系统角色，完全权限
    DEVELOPER = "developer" # 开发者角色
    
class ResourceType(str, Enum):
    """资源类型"""
    TOOL = "tool"          # 工具资源
    AGENT = "agent"        # 代理资源
    SESSION = "session"    # 会话资源
    SYSTEM = "system"      # 系统资源


@dataclass
class Permission:
    """权限定义"""
    resource_type: ResourceType  # 资源类型
    resource_id: str = "*"       # 资源ID，*表示所有
    action: str = "*"            # 操作，*表示所有操作


@dataclass
class RolePermissions:
    """角色权限映射"""
    role: Role  # 角色
    permissions: List[Permission] = field(default_factory=list)  # 权限列表


# 预定义的角色-权限映射
DEFAULT_ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.GUEST: [
        Permission(ResourceType.TOOL, "search_weather", "execute"),
        Permission(ResourceType.TOOL, "calculate", "execute"),
    ],
    Role.USER: [
        Permission(ResourceType.TOOL, "*", "execute"),
        Permission(ResourceType.SESSION, "*", "read"),
    ],
    Role.POWER_USER: [
        Permission(ResourceType.TOOL, "*", "execute"),
        Permission(ResourceType.AGENT, "*", "use"),
        Permission(ResourceType.SESSION, "*", "read"),
    ],
    Role.ADMIN: [
        Permission(ResourceType.TOOL, "*", "*"),
        Permission(ResourceType.AGENT, "*", "*"),
        Permission(ResourceType.SESSION, "*", "*"),
    ],
    Role.SYSTEM: [
        Permission(ResourceType.TOOL, "*", "*"),
        Permission(ResourceType.AGENT, "*", "*"),
        Permission(ResourceType.SESSION, "*", "*"),
        Permission(ResourceType.SYSTEM, "*", "*"),
    ]
}


class RBACManager:
    """RBAC管理器
    
    管理角色和权限的关系，并提供权限检查功能
    """
    
    def __init__(self):
        # 初始化角色权限映射
        self.role_permissions: Dict[Role, List[Permission]] = {}
        # 加载预定义权限
        self.load_default_permissions()
        
    def load_default_permissions(self):
        """加载默认权限配置"""
        self.role_permissions = DEFAULT_ROLE_PERMISSIONS.copy()
    
    def has_permission(self, 
                      roles: List[Role], 
                      resource_type: ResourceType, 
                      resource_id: str, 
                      action: str) -> bool:
        """检查是否有权限
        
        Args:
            roles: 角色列表
            resource_type: 资源类型
            resource_id: 资源ID
            action: 操作
            
        Returns:
            是否有权限
        """
        # 如果是系统角色，直接返回True
        if Role.SYSTEM in roles:
            return True
        
        # 检查每个角色是否有权限
        for role in roles:
            if role not in self.role_permissions:
                continue
                
            permissions = self.role_permissions[role]
            for perm in permissions:
                # 检查资源类型
                if perm.resource_type != resource_type and perm.resource_type != "*":
                    continue
                
                # 检查资源ID
                if perm.resource_id != resource_id and perm.resource_id != "*":
                    continue
                
                # 检查操作
                if perm.action != action and perm.action != "*":
                    continue
                
                # 所有条件都满足，有权限
                return True
        
        # 没有找到匹配的权限
        return False
    
    def get_allowed_tools(self, roles: List[Role]) -> Set[str]:
        """获取角色允许访问的工具列表
        
        Args:
            roles: 角色列表
            
        Returns:
            允许访问的工具ID集合
        """
        allowed_tools = set()
        
        # 检查每个角色的权限
        for role in roles:
            if role not in self.role_permissions:
                continue
                
            permissions = self.role_permissions[role]
            for perm in permissions:
                # 只关心工具类型资源
                if perm.resource_type != ResourceType.TOOL:
                    continue
                
                # 通配符表示所有工具
                if perm.resource_id == "*":
                    # 这里实际应当返回所有工具ID，但为简化处理，我们仅返回特殊标记
                    allowed_tools.add("*")
                    continue
                
                # 添加特定工具
                allowed_tools.add(perm.resource_id)
        
        return allowed_tools


# 创建全局RBAC管理器实例
rbac_manager = RBACManager() 