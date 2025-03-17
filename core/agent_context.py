"""
Agent上下文管理模块 - 基于OpenAI Agent SDK设计理念

Context是一个依赖注入工具：它是一个你创建并传递给Runner.run()的对象，
该对象被传递给每个代理、工具、交接等，并作为代理运行依赖和状态的容器。
"""

import time
import logging
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class AgentContext:
    """
    代理上下文类 - 用于在代理执行过程中传递数据和状态
    
    这个类遵循OpenAI Agent SDK的设计理念，作为依赖注入容器，
    存储代理运行所需的状态和数据，如用户信息、系统设置、工具权限等。
    
    注意：这个对象不会直接传递给LLM，而是传递给工具函数、回调、钩子等代码。
    """
    
    # 用户信息
    user_id: str = "anonymous"
    user_name: str = "用户"
    
    # 消息历史 - 可用于工具函数查询历史交互，但不会直接传给LLM
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    # 元数据 - 可存储任意键值对数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 工具权限控制
    permissions: Dict[str, bool] = field(default_factory=dict)
    
    # 会话状态信息
    session_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    
    # 系统设置
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        # 设置默认权限
        if not self.permissions:
            self.permissions = {
                "calculator": True,       # 计算器
                "web_search": False,      # 网络搜索
                "file_access": False,     # 文件访问
                "system_access": False,   # 系统访问
                "weather": True,          # 天气查询
            }
        
        # 设置默认系统设置
        if not self.settings:
            self.settings = {
                "max_tokens": int(os.getenv("MAX_TOKENS", "4000")),
                "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
                "stream_enabled": True,
                "safety_filters": os.getenv("SAFETY_FILTERS", "standard"),
            }
        
        # 将用户名同步到元数据中
        if "user_name" not in self.metadata:
            self.metadata["user_name"] = self.user_name
    
    def add_message(self, role: str, content: str, **extra_data):
        """
        添加消息到历史记录
        
        Args:
            role: 角色（user/assistant/system/tool）
            content: 消息内容
            **extra_data: 额外数据
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            **extra_data
        }
        self.messages.append(message)
        self.last_active = time.time()
        
        # 如果消息过多，可以裁剪
        max_messages = int(os.getenv("CONTEXT_MAX_MESSAGES", "50"))
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息
        
        Returns:
            包含用户ID、名称和元数据的字典
        """
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "metadata": self.metadata
        }
    
    def get_conversation_history(self, roles: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            roles: 要筛选的角色列表，如["user", "assistant"]，None表示所有角色
            limit: 最大返回消息数
            
        Returns:
            消息列表
        """
        if not roles:
            history = self.messages
        else:
            history = [msg for msg in self.messages if msg.get("role") in roles]
        
        return history[-limit:] if limit > 0 else history
    
    def has_permission(self, permission_name: str) -> bool:
        """
        检查是否有指定权限
        
        Args:
            permission_name: 权限名称
            
        Returns:
            是否有权限
        """
        return self.permissions.get(permission_name, False)
    
    def set_permission(self, permission_name: str, allowed: bool):
        """
        设置权限
        
        Args:
            permission_name: 权限名称
            allowed: 是否允许
        """
        self.permissions[permission_name] = allowed
    
    def update_metadata(self, new_metadata: Dict[str, Any]):
        """
        更新元数据
        
        Args:
            new_metadata: 新的元数据
        """
        self.metadata.update(new_metadata)
        
        # 如果更新了user_name，同步到实例属性
        if "user_name" in new_metadata:
            self.user_name = new_metadata["user_name"]
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """
        更新系统设置
        
        Args:
            new_settings: 新的设置
        """
        self.settings.update(new_settings)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        获取系统设置
        
        Args:
            key: 设置键名
            default: 默认值
            
        Returns:
            设置值或默认值
        """
        return self.settings.get(key, default)
    
    def to_api_messages(self, include_system: bool = False) -> List[Dict[str, str]]:
        """
        转换为API可用的消息格式，用于传递给LLM
        
        Args:
            include_system: 是否包含系统消息
            
        Returns:
            API格式的消息列表
        """
        api_messages = []
        
        for msg in self.messages:
            if not include_system and msg.get("role") == "system":
                continue
                
            if msg.get("role") in ["user", "assistant", "system", "tool"]:
                api_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content", "")
                })
        
        return api_messages
    
    def clear_history(self, keep_system: bool = True):
        """
        清除历史记录
        
        Args:
            keep_system: 是否保留系统消息
        """
        if keep_system:
            self.messages = [msg for msg in self.messages if msg.get("role") == "system"]
        else:
            self.messages = [] 