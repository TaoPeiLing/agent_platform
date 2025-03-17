"""
示例工具模块 - 展示如何正确使用上下文(Context)对象

这个模块演示了如何在工具函数中:
1. 接收和使用上下文对象
2. 从上下文中获取用户信息
3. 检查权限
4. 访问会话历史
"""
import logging
from typing import Dict, Any, Optional, Union, List, TYPE_CHECKING

# 类型检查时导入，避免循环导入
if TYPE_CHECKING:
    from agent_cores.core.agent_context import AgentContext
    from agents.run_context import RunContextWrapper

# 配置日志
logger = logging.getLogger(__name__)

# 导入工具注册装饰器和上下文处理函数
from agent_cores.tools.core.tool_registry import register_tool
from agent_cores.tools.tool_utils import process_context, get_user_info, get_conversation_history, check_permission


@register_tool(
    category="user",
    description="获取当前用户信息",
    tags=["user", "info"]
)
def get_user_info_tool(ctx: Optional[Any] = None) -> Dict[str, Any]:
    """
    获取用户信息工具 - 返回当前用户的信息
    
    Args:
        ctx: 上下文对象
        
    Returns:
        包含用户信息的字典
    """
    if not ctx:
        return {
            "success": False,
            "user_found": False,
            "message": "上下文对象为空，无法获取用户信息"
        }
    
    # 使用工具函数获取用户信息
    user_info = get_user_info(ctx)
    
    if user_info:
        return {
            "success": True,
            "user_found": True,
            "user_info": user_info,
            "message": "成功获取用户信息"
        }
    else:
        return {
            "success": False,
            "user_found": False,
            "message": "未找到用户信息"
        }


@register_tool(
    category="conversation",
    description="获取当前对话的历史记录",
    tags=["conversation", "history"]
)
def get_conversation_history_tool(
    limit: int = 5, 
    ctx: Optional[Any] = None
) -> Dict[str, Any]:
    """
    获取对话历史工具 - 返回最近的对话历史
    
    Args:
        limit: 返回的最大消息数
        ctx: 上下文对象
        
    Returns:
        包含对话历史的字典
    """
    if not ctx:
        return {
            "success": False,
            "history_found": False,
            "message": "上下文对象为空，无法获取对话历史"
        }
    
    # 使用工具函数获取对话历史
    history = get_conversation_history(ctx, limit)
    
    if not history:
        return {
            "success": False,
            "history_found": False,
            "message": "未找到对话历史或对话历史为空"
        }
            
    # 转换为可读格式
    formatted_history = []
    for msg in history:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        formatted_history.append({
            "role": role,
            "content": content[:100] + ('...' if len(content) > 100 else '')
        })
        
    return {
        "success": True,
        "history_found": True,
        "history": formatted_history,
        "message": f"成功获取 {len(formatted_history)} 条对话历史"
    }


@register_tool(
    category="permission",
    description="检查用户是否具有特定权限",
    tags=["permission", "security"]
)
def check_permission_tool(
    permission: str,
    ctx: Optional[Any] = None
) -> Dict[str, Any]:
    """
    检查权限工具 - 检查用户是否具有特定权限
    
    Args:
        permission: 要检查的权限名称
        ctx: 上下文对象
        
    Returns:
        包含权限检查结果的字典
    """
    if not ctx:
        return {
            "success": False,
            "permission_found": False,
            "has_permission": False,
            "message": "上下文对象为空，无法检查权限"
        }
    
    # 使用工具函数检查权限
    has_permission = check_permission(ctx, permission)
    
    return {
        "success": True,
        "permission_found": True,
        "has_permission": has_permission,
        "message": f"权限 '{permission}': {'允许' if has_permission else '拒绝'}"
    }