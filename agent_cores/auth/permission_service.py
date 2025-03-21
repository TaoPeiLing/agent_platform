"""
权限服务模块

提供基于角色的访问控制(RBAC)功能，管理用户角色和资源权限。
"""

import logging
from enum import Enum, auto
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass, field

# 配置日志
logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """权限类型"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    CREATE = "create"
    DELETE = "delete"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    ACCESS = "access"  # 访问权限


class ResourceType(str, Enum):
    """资源类型"""
    AGENT = "agent"
    WORKFLOW = "workflow"
    TOOL = "tool"
    CONVERSATION = "conversation"
    EXTERNAL_SYSTEM = "external_system"
    EXTERNAL_DATA = "external_data"


class Role(str, Enum):
    """角色类型"""
    ADMIN = "admin"  # 管理员角色
    USER = "user"    # 普通用户角色
    GUEST = "guest"  # 访客角色
    API = "api"      # API调用角色
    TOOL = "tool"    # 工具角色


@dataclass
class ResourcePolicy:
    """资源访问策略"""
    resource_id: str  # 资源ID
    resource_type: str  # 资源类型
    allowed_roles: List[str] = field(default_factory=list)  # 允许的角色
    allowed_operations: List[str] = field(default_factory=list)  # 允许的操作
    description: Optional[str] = None  # 策略描述
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def allows_role(self, role: str) -> bool:
        """检查是否允许特定角色访问"""
        # 管理员角色总是有权限
        if role == Role.ADMIN:
            return True
            
        return role in self.allowed_roles
        
    def allows_operation(self, operation: str) -> bool:
        """检查是否允许特定操作"""
        return operation in self.allowed_operations
        
    def check_permission(self, role: str, operation: str) -> bool:
        """检查特定角色是否可以执行特定操作"""
        return self.allows_role(role) and self.allows_operation(operation)


class PermissionService:
    """权限服务
    
    管理基于角色的访问控制(RBAC)策略。
    """
    
    def __init__(self):
        # 资源策略字典: (resource_type, resource_id) -> ResourcePolicy
        self.resource_policies: Dict[tuple, ResourcePolicy] = {}
        
        # 角色层次结构: role -> set(implied_roles)
        self.role_hierarchy: Dict[str, Set[str]] = {
            Role.ADMIN: {Role.USER, Role.GUEST, Role.API, Role.TOOL},
            Role.USER: {Role.GUEST},
            Role.API: set(),
            Role.TOOL: set(),
            Role.GUEST: set()
        }
        
        logger.info("权限服务已初始化")
        
    def add_resource_policy(self, policy: ResourcePolicy) -> None:
        """添加资源访问策略
        
        Args:
            policy: 资源访问策略
        """
        key = (policy.resource_type, policy.resource_id)
        self.resource_policies[key] = policy
        logger.info(f"已添加资源策略: {policy.resource_type}/{policy.resource_id}")
        
    def remove_resource_policy(self, resource_type: str, resource_id: str) -> None:
        """移除资源访问策略
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
        """
        key = (resource_type, resource_id)
        if key in self.resource_policies:
            del self.resource_policies[key]
            logger.info(f"已移除资源策略: {resource_type}/{resource_id}")
            
    def get_resource_policy(self, resource_type: str, resource_id: str) -> Optional[ResourcePolicy]:
        """获取资源访问策略
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            
        Returns:
            资源访问策略，如果不存在则返回None
        """
        key = (resource_type, resource_id)
        return self.resource_policies.get(key)
        
    def get_all_policies(self) -> List[ResourcePolicy]:
        """获取所有资源访问策略
        
        Returns:
            所有资源访问策略列表
        """
        return list(self.resource_policies.values())
        
    def get_implied_roles(self, role: str) -> Set[str]:
        """获取角色隐含的所有角色
        
        Args:
            role: 角色名
            
        Returns:
            隐含的角色集合，包括角色本身
        """
        result = {role}
        
        # 添加显式定义的下级角色
        if role in self.role_hierarchy:
            result.update(self.role_hierarchy[role])
            
            # 递归添加隐含的角色
            for implied_role in list(self.role_hierarchy[role]):
                result.update(self.get_implied_roles(implied_role))
                
        return result
        
    def get_effective_roles(self, roles: List[str]) -> Set[str]:
        """获取用户的有效角色集合
        
        Args:
            roles: 用户角色列表
            
        Returns:
            有效角色集合，包括所有隐含的角色
        """
        result = set()
        
        for role in roles:
            result.update(self.get_implied_roles(role))
            
        return result
        
    def check_permission(
        self, roles: List[str], resource_type: str, resource_id: str, operation: str
    ) -> bool:
        """检查用户是否有权限访问资源
        
        Args:
            roles: 用户角色列表
            resource_type: 资源类型
            resource_id: 资源ID
            operation: 操作类型
            
        Returns:
            如果有权限则返回True，否则返回False
        """
        # 首先检查是否存在资源策略
        policy = self.get_resource_policy(resource_type, resource_id)
        if not policy:
            logger.warning(f"未找到资源策略: {resource_type}/{resource_id}")
            return False
            
        # 检查是否是管理员角色
        if Role.ADMIN in roles:
            return True
            
        # 获取有效角色
        effective_roles = self.get_effective_roles(roles)
        
        # 检查是否有允许的角色和操作
        for role in effective_roles:
            if policy.check_permission(role, operation):
                return True
                
        return False
        
    def check_agent_permission(self, roles: List[str], agent_id: str, operation: str) -> bool:
        """检查用户是否有权限访问智能体
        
        Args:
            roles: 用户角色列表
            agent_id: 智能体ID
            operation: 操作类型
            
        Returns:
            如果有权限则返回True，否则返回False
        """
        return self.check_permission(roles, ResourceType.AGENT, agent_id, operation)
        
    def check_workflow_permission(self, roles: List[str], workflow_id: str, operation: str) -> bool:
        """检查用户是否有权限访问工作流
        
        Args:
            roles: 用户角色列表
            workflow_id: 工作流ID
            operation: 操作类型
            
        Returns:
            如果有权限则返回True，否则返回False
        """
        return self.check_permission(roles, ResourceType.WORKFLOW, workflow_id, operation)
        
    def check_tool_permission(self, roles: List[str], tool_id: str) -> bool:
        """检查用户是否有权限使用工具
        
        Args:
            roles: 用户角色列表
            tool_id: 工具ID
            
        Returns:
            如果有权限则返回True，否则返回False
        """
        return self.check_permission(roles, ResourceType.TOOL, tool_id, Permission.EXECUTE)
        
    def check_external_system_permission(self, roles: List[str], system_id: str) -> bool:
        """检查用户是否有权限访问外部系统
        
        Args:
            roles: 用户角色列表
            system_id: 外部系统ID
            
        Returns:
            如果有权限则返回True，否则返回False
        """
        return self.check_permission(roles, ResourceType.EXTERNAL_SYSTEM, system_id, Permission.ACCESS)
        
    def check_external_data_permission(self, roles: List[str], data_id: str, operation: str) -> bool:
        """检查用户是否有权限访问外部数据
        
        Args:
            roles: 用户角色列表
            data_id: 数据ID
            operation: 操作类型
            
        Returns:
            如果有权限则返回True，否则返回False
        """
        return self.check_permission(roles, ResourceType.EXTERNAL_DATA, data_id, operation)
        
    def create_default_policies(self) -> None:
        """创建默认的资源访问策略"""
        # 智能体默认策略
        self.add_resource_policy(ResourcePolicy(
            resource_id="default",
            resource_type=ResourceType.AGENT,
            allowed_roles=[Role.USER, Role.API],
            allowed_operations=[Permission.READ, Permission.EXECUTE]
        ))
        
        # 工作流默认策略
        self.add_resource_policy(ResourcePolicy(
            resource_id="default",
            resource_type=ResourceType.WORKFLOW,
            allowed_roles=[Role.USER, Role.API],
            allowed_operations=[Permission.READ, Permission.EXECUTE]
        ))
        
        # 工具默认策略
        self.add_resource_policy(ResourcePolicy(
            resource_id="default",
            resource_type=ResourceType.TOOL,
            allowed_roles=[Role.USER, Role.API],
            allowed_operations=[Permission.EXECUTE]
        ))
        
        logger.info("已创建默认资源访问策略")


# 全局实例
permission_service = PermissionService()
permission_service.create_default_policies() 