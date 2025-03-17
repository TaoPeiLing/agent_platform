"""
工具工具模块 - 提供通用的工具函数装饰器和辅助功能

该模块包含统一的工具函数装饰器、错误处理和上下文处理机制，
用于简化工具函数的实现和标准化工具函数的行为。
"""
import logging
import functools
import traceback
from typing import Callable, Dict, Any, Optional, Union, TypeVar, cast, get_type_hints

# 配置日志
logger = logging.getLogger(__name__)

# 类型定义
T = TypeVar('T')
ToolFunction = Callable[..., Dict[str, Any]]


def tool_wrapper(
    func: ToolFunction,
) -> ToolFunction:
    """
    工具函数装饰器 - 统一工具函数的错误处理和日志记录
    
    Args:
        func: 原始工具函数
        
    Returns:
        包装后的工具函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        func_name = func.__name__
        logger.info(f"执行工具函数: {func_name}, 参数: {args}, 关键字参数: {kwargs}")
        
        try:
            # 尝试执行原始函数
            result = func(*args, **kwargs)
            # 确保返回值为字典格式
            if not isinstance(result, dict):
                result = {"result": result, "success": True}
            if "success" not in result:
                result["success"] = True
                
            logger.info(f"工具函数 {func_name} 执行成功: {result.get('message', '')}")
            return result
            
        except Exception as e:
            # 捕获并处理异常
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"工具函数 {func_name} 执行失败: {error_message}\n{stack_trace}")
            
            # 返回标准化的错误响应
            return {
                "success": False,
                "error": True,
                "message": f"工具执行错误: {error_message}",
                "error_type": type(e).__name__,
                "details": stack_trace
            }
            
    return wrapper


def process_context(ctx: Any) -> Any:
    """
    处理上下文对象 - 统一处理不同类型的上下文对象
    
    Args:
        ctx: 上下文对象，可能是AgentContext或RunContextWrapper
        
    Returns:
        处理后的上下文对象
    """
    # 如果上下文是RunContextWrapper，获取内部上下文
    if hasattr(ctx, "context"):
        return ctx.context
    return ctx


def get_user_info(ctx: Any) -> Dict[str, Any]:
    """
    从上下文获取用户信息 - 辅助函数
    
    Args:
        ctx: 上下文对象
        
    Returns:
        用户信息字典
    """
    ctx = process_context(ctx)
    
    if hasattr(ctx, "get_user_info"):
        # 使用专门的方法获取用户信息
        return ctx.get_user_info()
    
    # 从上下文属性组装用户信息
    user_info = {}
    
    # 尝试获取常见的用户属性
    for attr in ["user_id", "user_name", "user_email", "user_role", "metadata"]:
        if hasattr(ctx, attr):
            user_info[attr] = getattr(ctx, attr)
    
    return user_info


def get_conversation_history(ctx: Any, limit: int = 5) -> list:
    """
    从上下文获取对话历史 - 辅助函数
    
    Args:
        ctx: 上下文对象
        limit: 返回的最大消息数
        
    Returns:
        对话历史列表
    """
    ctx = process_context(ctx)
    
    if hasattr(ctx, "get_conversation_history"):
        # 使用专门的方法获取对话历史
        return ctx.get_conversation_history(limit=limit)
    
    # 从上下文属性获取消息历史
    if hasattr(ctx, "messages"):
        messages = getattr(ctx, "messages", [])
        # 返回最近的消息
        return messages[-limit:] if limit > 0 else messages
    
    # 无法获取消息历史
    return []


def check_permission(ctx: Any, permission: str) -> bool:
    """
    检查权限 - 辅助函数
    
    Args:
        ctx: 上下文对象
        permission: 权限名称
        
    Returns:
        是否有权限
    """
    ctx = process_context(ctx)
    
    if hasattr(ctx, "has_permission"):
        # 使用专门的方法检查权限
        return ctx.has_permission(permission)
    
    # 从上下文属性检查权限
    if hasattr(ctx, "permissions"):
        permissions = getattr(ctx, "permissions", {})
        return permissions.get(permission, False)
    
    # 无法检查权限，默认返回False
    return False 