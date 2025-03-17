"""
上下文处理工具模块 - 提供统一的上下文处理功能

该模块提供了一系列用于处理和操作Agent上下文的工具函数，
包括上下文验证、用户信息提取、消息历史处理和权限检查等。
"""
import logging
from typing import Dict, Any, Optional, List, Union, TypeVar, Type, cast, Generic

# 配置日志
logger = logging.getLogger(__name__)

# 类型定义
T = TypeVar('T')
ContextType = TypeVar('ContextType')


class RunContextWrapper(Generic[ContextType]):
    """
    运行上下文包装器 - 包装代理上下文，提供统一的接口
    
    该类提供了对 AgentContext 的包装，使工具函数可以更方便地
    访问上下文信息，同时支持类型提示。
    
    Attributes:
        context: 被包装的上下文对象
    """
    
    def __init__(self, context: ContextType):
        """
        初始化运行上下文包装器
        
        Args:
            context: 要包装的上下文对象
        """
        self.context = context
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息
        
        Returns:
            用户信息字典
        """
        # 尝试使用上下文的get_user_info方法
        if hasattr(self.context, "get_user_info"):
            return getattr(self.context, "get_user_info")()
        
        # 否则从上下文属性组装用户信息
        user_info = {}
        for attr in ["user_id", "user_name", "user_email", "user_role", "metadata"]:
            if hasattr(self.context, attr):
                user_info[attr] = getattr(self.context, attr)
        
        return user_info
    
    def get_conversation_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            limit: 返回的最大消息数
            
        Returns:
            对话历史列表
        """
        # 尝试使用上下文的get_conversation_history方法
        if hasattr(self.context, "get_conversation_history"):
            return getattr(self.context, "get_conversation_history")(limit=limit)
        
        # 否则从上下文属性获取消息历史
        if hasattr(self.context, "messages"):
            messages = getattr(self.context, "messages", [])
            # 返回最近的消息
            return messages[-limit:] if limit > 0 and len(messages) > 0 else messages
        
        # 无法获取消息历史
        return []
    
    def has_permission(self, permission: str) -> bool:
        """
        检查权限
        
        Args:
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        # 尝试使用上下文的has_permission方法
        if hasattr(self.context, "has_permission"):
            return getattr(self.context, "has_permission")(permission)
        
        # 否则从上下文属性检查权限
        if hasattr(self.context, "permissions"):
            permissions = getattr(self.context, "permissions", {})
            return permissions.get(permission, False)
        
        # 无法检查权限，默认返回False
        return False
    
    def get_metadata(self, key: Optional[str] = None) -> Any:
        """
        获取元数据
        
        Args:
            key: 元数据键，为None时返回所有元数据
            
        Returns:
            元数据值或整个元数据字典
        """
        # 尝试从上下文获取元数据
        metadata = {}
        
        if hasattr(self.context, "get_metadata"):
            metadata = getattr(self.context, "get_metadata")()
        elif hasattr(self.context, "metadata"):
            metadata = getattr(self.context, "metadata", {})
        
        # 返回特定键的值或整个字典
        if key is not None:
            return metadata.get(key)
        return metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将上下文转换为字典
        
        Returns:
            表示上下文的字典
        """
        # 尝试使用上下文的to_dict方法
        if hasattr(self.context, "to_dict"):
            return getattr(self.context, "to_dict")()
        
        # 否则将上下文对象的属性转换为字典
        result = {}
        for attr in dir(self.context):
            # 跳过私有属性和方法
            if attr.startswith('_') or callable(getattr(self.context, attr)):
                continue
            result[attr] = getattr(self.context, attr)
        
        return result


def create_context_wrapper(context: Any) -> RunContextWrapper:
    """
    创建上下文包装器
    
    Args:
        context: 要包装的上下文对象
        
    Returns:
        包装后的上下文对象
    """
    # 如果已经是包装器，直接返回
    if isinstance(context, RunContextWrapper):
        return context
    
    # 创建新的包装器
    return RunContextWrapper(context)


def validate_context(context: Any) -> bool:
    """
    验证上下文对象是否有效
    
    Args:
        context: 要验证的上下文对象
        
    Returns:
        上下文是否有效
    """
    if context is None:
        return False
    
    # 检查最基本的要求：用户ID
    if hasattr(context, "user_id"):
        return True
    
    # 如果是包装器，检查内部上下文
    if hasattr(context, "context") and context.context is not None:
        return validate_context(context.context)
    
    return False


def get_user_info_from_context(context: Any) -> Dict[str, Any]:
    """
    从上下文获取用户信息
    
    Args:
        context: 上下文对象
        
    Returns:
        用户信息字典
    """
    wrapper = create_context_wrapper(context)
    return wrapper.get_user_info()


def get_conversation_history_from_context(context: Any, limit: int = 5) -> List[Dict[str, Any]]:
    """
    从上下文获取对话历史
    
    Args:
        context: 上下文对象
        limit: 返回的最大消息数
        
    Returns:
        对话历史列表
    """
    wrapper = create_context_wrapper(context)
    return wrapper.get_conversation_history(limit)


def check_permission_from_context(context: Any, permission: str) -> bool:
    """
    从上下文检查权限
    
    Args:
        context: 上下文对象
        permission: 权限名称
        
    Returns:
        是否有权限
    """
    wrapper = create_context_wrapper(context)
    return wrapper.has_permission(permission) 