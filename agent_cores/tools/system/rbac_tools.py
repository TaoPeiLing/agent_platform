"""
RBAC权限工具模块

提供与权限相关的工具函数，用于在代理运行期间进行权限验证和控制。
"""
import logging
from typing import List, Dict, Any, Optional, Set
from enum import Enum

from agents import function_tool, RunContextWrapper, GuardrailFunctionOutput, input_guardrail

from agent_cores.models.rbac import (
    Role, 
    ResourceType, 
    rbac_manager
)

# 配置日志
logger = logging.getLogger(__name__)


class PermissionContext:
    """权限上下文，用于在代理运行期间传递权限信息"""
    
    def __init__(self, 
                roles: List[str] = None, 
                user_id: Optional[str] = None,
                metadata: Dict[str, Any] = None):
        """
        初始化权限上下文
        
        Args:
            roles: 角色列表，默认为[guest]
            user_id: 用户ID，可选
            metadata: 元数据，可选
        """
        self.roles = [Role(r) for r in roles] if roles else [Role.GUEST]  # 默认为访客角色
        self.user_id = user_id
        self.metadata = metadata or {}
        
    def has_role(self, role: Role) -> bool:
        """检查是否具有指定角色"""
        return role in self.roles
    
    def has_permission(self, 
                      resource_type: ResourceType, 
                      resource_id: str, 
                      action: str) -> bool:
        """检查是否有指定权限"""
        return rbac_manager.has_permission(self.roles, resource_type, resource_id, action)
    
    def get_allowed_tools(self) -> Set[str]:
        """获取允许使用的工具列表"""
        return rbac_manager.get_allowed_tools(self.roles)


@function_tool
async def check_permission(ctx: RunContextWrapper[PermissionContext], 
                          resource_type: str, 
                          resource_id: str, 
                          action: str) -> str:
    """
    检查当前用户是否有权限执行特定操作
    
    Args:
        resource_type: 资源类型 (tool, agent, session, system)
        resource_id: 资源ID
        action: 操作名称
        
    Returns:
        检查结果描述
    """
    if not hasattr(ctx.context, 'roles'):
        return "权限检查失败：未找到角色信息"
    
    try:
        resource_type_enum = ResourceType(resource_type)
        has_permission = ctx.context.has_permission(resource_type_enum, resource_id, action)
        
        if has_permission:
            return f"权限检查通过：您有权限在{resource_type}/{resource_id}上执行{action}操作"
        else:
            return f"权限检查失败：您没有权限在{resource_type}/{resource_id}上执行{action}操作"
    except ValueError as e:
        return f"权限检查错误：{str(e)}"


@function_tool
async def get_current_roles(ctx: RunContextWrapper[PermissionContext]) -> str:
    """
    获取当前用户的角色列表
    
    Returns:
        当前用户的角色列表
    """
    if not hasattr(ctx.context, 'roles'):
        return "未找到角色信息"
    
    roles = [role.value for role in ctx.context.roles]
    return f"当前角色: {', '.join(roles)}"


@function_tool
async def list_allowed_tools(ctx: RunContextWrapper[PermissionContext]) -> str:
    """
    列出当前用户有权限使用的工具
    
    Returns:
        允许使用的工具列表
    """
    if not hasattr(ctx.context, 'roles'):
        return "未找到角色信息"
    
    allowed_tools = ctx.context.get_allowed_tools()
    
    if '*' in allowed_tools:
        return "您有权限使用所有工具"
    
    if not allowed_tools:
        return "您没有权限使用任何工具"
    
    return f"允许使用的工具: {', '.join(sorted(allowed_tools))}"


@input_guardrail
async def permission_guardrail(ctx: RunContextWrapper[PermissionContext], 
                            resource_type: Optional[str] = None, 
                            resource_id: Optional[str] = None, 
                            action: Optional[str] = None, 
                            agent: Any = None, 
                            input_data: Any = None):
    """
    权限验证围栏，用于检查工具调用权限
    
    检查用户是否有权限使用请求的工具。可以两种方式使用:
    1. 通过resource_type/resource_id/action参数检查特定权限
    2. 通过agent/input_data参数检查工具调用权限
    """
    if not hasattr(ctx.context, 'roles'):
        logger.warning("权限围栏: 未找到角色信息")
        return GuardrailFunctionOutput(
            output_info={"error": "未找到角色信息"},
            tripwire_triggered=False  # 不阻断，但记录警告
        )
    
    # 方式1: 检查特定资源权限
    if resource_type and resource_id and action:
        try:
            resource_type_enum = ResourceType(resource_type)
            has_permission = ctx.context.has_permission(resource_type_enum, resource_id, action)
            
            if has_permission:
                return GuardrailFunctionOutput(
                    output_info={},
                    tripwire_triggered=False
                )
            else:
                return GuardrailFunctionOutput(
                    output_info={
                        "error": "权限不足",
                        "message": f"您没有权限在{resource_type}/{resource_id}上执行{action}操作"
                    },
                    tripwire_triggered=True
                )
        except ValueError as e:
            return GuardrailFunctionOutput(
                output_info={"error": f"权限检查错误: {str(e)}"},
                tripwire_triggered=True
            )
    
    # 方式2: 检查工具调用权限
    # 检查输入中是否包含工具调用请求
    tool_calls = []
    if isinstance(input_data, dict) and 'tool_calls' in input_data:
        tool_calls = input_data['tool_calls']
    
    # 如果没有工具调用，直接通过
    if not tool_calls:
        return GuardrailFunctionOutput(
            output_info={},  # 添加空字典作为output_info
            tripwire_triggered=False
        )
    
    # 获取允许的工具
    allowed_tools = ctx.context.get_allowed_tools()
    all_tools_allowed = '*' in allowed_tools
    
    # 检查每个工具调用是否有权限
    forbidden_tools = []
    for tool_call in tool_calls:
        tool_name = tool_call.get('name', '')
        
        # 如果允许所有工具或工具在允许列表中，则通过
        if all_tools_allowed or tool_name in allowed_tools:
            continue
            
        # 否则记录禁止的工具
        forbidden_tools.append(tool_name)
    
    # 如果有禁止的工具，触发围栏
    if forbidden_tools:
        logger.warning(f"权限围栏: 禁止使用工具 {', '.join(forbidden_tools)}")
        return GuardrailFunctionOutput(
            output_info={
                "error": "权限不足",
                "message": f"您没有权限使用以下工具: {', '.join(forbidden_tools)}",
                "forbidden_tools": forbidden_tools
            },
            tripwire_triggered=True  # 阻断执行
        )
    
    # 所有工具都允许使用
    return GuardrailFunctionOutput(
        output_info={},  # 添加空字典作为output_info
        tripwire_triggered=False
    ) 