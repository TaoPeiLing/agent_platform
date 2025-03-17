"""
上下文工具模块 - 提供与代理上下文交互的工具

该模块包含用于与代理上下文交互的工具函数，例如获取用户信息、获取对话历史和检查权限。
这些工具让代理能够访问和操作当前运行环境的上下文信息。
"""
import logging
from typing import Dict, Any, List, Optional

from agent_cores.tools.core.tool_registry import register_tool
from agent_cores.tools.tool_utils import get_user_info, get_conversation_history, check_permission, process_context

# 配置日志
logger = logging.getLogger(__name__)


@register_tool(
    name="get_user_info_tool",
    description="获取当前用户信息",
    category="context",
    tags=["user", "context", "info"]
)
def get_user_info_tool(ctx: Any) -> Dict[str, Any]:
    """
    获取当前用户信息
    
    Args:
        ctx: 上下文对象
        
    Returns:
        用户信息字典，包含user_id, user_name等
    """
    try:
        # 使用工具辅助函数获取用户信息
        user_info = get_user_info(ctx)
        
        return {
            "success": True,
            "result": user_info
        }
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return {
            "success": False,
            "message": f"获取用户信息失败: {str(e)}"
        }


@register_tool(
    name="get_conversation_history_tool",
    description="获取对话历史",
    category="context",
    tags=["conversation", "context", "history"]
)
def get_conversation_history_tool(ctx: Any, limit: int = 5) -> Dict[str, Any]:
    """
    获取对话历史
    
    Args:
        ctx: 上下文对象
        limit: 返回的最大消息数
        
    Returns:
        对话历史列表
    """
    try:
        # 使用工具辅助函数获取对话历史
        history = get_conversation_history(ctx, limit)
        
        return {
            "success": True,
            "result": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"获取对话历史失败: {str(e)}")
        return {
            "success": False,
            "message": f"获取对话历史失败: {str(e)}"
        }


@register_tool(
    name="check_permission_tool",
    description="检查用户是否拥有特定权限",
    category="context",
    tags=["permission", "context", "security"]
)
def check_permission_tool(ctx: Any, permission: str) -> Dict[str, Any]:
    """
    检查用户是否拥有特定权限
    
    Args:
        ctx: 上下文对象
        permission: 权限名称
        
    Returns:
        权限检查结果
    """
    try:
        # 使用工具辅助函数检查权限
        has_permission = check_permission(ctx, permission)
        
        return {
            "success": True,
            "permission": permission,
            "has_permission": has_permission,
            "result": has_permission
        }
    except Exception as e:
        logger.error(f"检查权限失败: {str(e)}")
        return {
            "success": False,
            "message": f"检查权限失败: {str(e)}"
        } 