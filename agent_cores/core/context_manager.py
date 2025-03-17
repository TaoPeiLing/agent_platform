"""
上下文管理器 - 处理OpenAI Agent的上下文需求

该模块定义了与OpenAI Agent SDK兼容的上下文管理系统，确保：
1. 本地上下文（RunContext）正确管理依赖和状态
2. 消息历史（对话历史）正确格式化供LLM使用
"""

import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """
    代理上下文 - 符合OpenAI Agent SDK的上下文对象
    
    这个类对应OpenAI Agent SDK文档中的Context对象，
    用于依赖注入和状态管理。
    """
    # 用户信息
    user_id: str = "anonymous"
    user_name: str = "用户"
    
    # 系统指令和元数据
    system_instruction: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 消息历史 - 符合OpenAI格式的消息列表
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    # 内存管理配置
    max_messages: int = 20  # 最大消息数量限制
    max_token_estimate: int = 8000  # 估计的最大token数
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保metadata包含user_name
        if "user_name" not in self.metadata:
            self.metadata["user_name"] = self.user_name
            
    def add_message(self, role: str, content: str) -> None:
        """
        添加消息到历史记录
        
        Args:
            role: 角色(user/assistant/system)
            content: 消息内容
        """
        # 安全检查 - 确保内容不是极端大的对象
        if not isinstance(content, str):
            content = str(content)
            
        # 内容长度限制 - 如果内容超过10000字符，截断它
        if len(content) > 10000:
            content = content[:10000] + "...(内容过长，已截断)"
            
        # 添加新消息
        new_message = {
            "role": role,
            "content": content
        }
        
        # 如果是system消息，确保添加到开头
        if role == "system":
            # 首先移除任何现有的系统消息
            self.messages = [msg for msg in self.messages if msg.get("role") != "system"]
            # 然后添加新的系统消息到开头
            self.messages.insert(0, new_message)
            # 同时更新系统指令
            self.system_instruction = content
        else:
            # 对于非系统消息，添加到列表末尾，但可能需要进行清理
            self.messages.append(new_message)
            
        # 自动清理 - 如果消息太多，移除旧消息
        self._cleanup_messages()
        
    def _cleanup_messages(self) -> None:
        """
        清理消息历史，确保不超过限制
        """
        # 如果消息数量超过限制，删除旧消息(保留系统消息和最新的消息)
        if len(self.messages) > self.max_messages:
            # 保留系统消息
            system_messages = [msg for msg in self.messages if msg.get("role") == "system"]
            # 保留最新的消息
            recent_messages = self.messages[-(self.max_messages - len(system_messages)):]
            # 重建消息列表
            self.messages = system_messages + recent_messages
        
    def add_system_message(self, content: str) -> None:
        """
        添加系统消息 - 确保系统消息在首位
        
        Args:
            content: 系统消息内容
        """
        # 保存系统指令
        self.system_instruction = content
        
        # 安全检查 - 确保内容不是极端大的对象
        if not isinstance(content, str):
            content = str(content)
            
        # 内容长度限制
        if len(content) > 10000:
            content = content[:10000] + "...(内容过长，已截断)"
        
        # 检查是否已存在系统消息
        has_system = False
        for msg in self.messages:
            if msg["role"] == "system":
                msg["content"] = content
                has_system = True
                break
                
        # 如果不存在系统消息，添加到列表开头
        if not has_system:
            self.messages.insert(0, {
                "role": "system",
                "content": content
            })
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式 - 用于传递给OpenAI Agent SDK
        
        Returns:
            包含必要上下文信息的字典
        """
        # 应用清理，确保消息不会太多
        self._cleanup_messages()
        
        return {
            "messages": self.messages,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "metadata": self.metadata
        }
    
    @staticmethod
    def from_messages(messages: List[Dict[str, Any]], 
                     user_id: str = "anonymous",
                     user_name: str = "用户",
                     metadata: Optional[Dict[str, Any]] = None,
                     max_messages: int = 20) -> 'AgentContext':
        """
        从消息列表创建上下文
        
        Args:
            messages: 消息列表
            user_id: 用户ID
            user_name: 用户名
            metadata: 元数据
            max_messages: 最大消息数量限制
            
        Returns:
            AgentContext实例
        """
        context = AgentContext(
            user_id=user_id,
            user_name=user_name,
            metadata=metadata or {},
            max_messages=max_messages
        )
        
        # 安全地添加消息，避免内存问题
        system_messages = []
        other_messages = []
        
        # 分开处理系统消息和其他消息
        for msg in messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                if msg["role"] == "system":
                    system_messages.append(msg)
                else:
                    other_messages.append(msg)
        
        # 如果消息过多，进行截断
        if len(other_messages) > max_messages:
            other_messages = other_messages[-max_messages:]
        
        # 重建消息列表 - 系统消息在前面
        safe_messages = system_messages + other_messages
        
        # 提取系统指令
        for msg in safe_messages:
            if msg["role"] == "system":
                context.system_instruction = msg["content"]
                break
                
        # 设置消息列表
        context.messages = safe_messages
        
        return context


class ContextManager:
    """
    上下文管理器 - 管理代理的上下文
    
    提供创建、获取和更新上下文的功能，确保与OpenAI Agent SDK的兼容性。
    """
    
    def __init__(self):
        """初始化上下文管理器"""
        self.contexts: Dict[str, AgentContext] = {}
        self.max_messages = 20  # 默认最大消息数量
        
    def create_context(self, 
                      session_id: str,
                      user_id: str = "anonymous",
                      user_name: str = "用户",
                      system_instruction: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None,
                      max_messages: Optional[int] = None) -> AgentContext:
        """
        创建新的上下文
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            user_name: 用户名
            system_instruction: 系统指令
            metadata: 元数据
            max_messages: 最大消息数量，如果为None则使用默认值
            
        Returns:
            新创建的AgentContext实例
        """
        # 使用默认值或提供的值
        max_msg = max_messages if max_messages is not None else self.max_messages
        
        context = AgentContext(
            user_id=user_id,
            user_name=user_name,
            metadata=metadata or {},
            max_messages=max_msg
        )
        
        # 如果提供了系统指令，添加系统消息
        if system_instruction:
            context.add_system_message(system_instruction)
            
        # 保存上下文
        self.contexts[session_id] = context
        
        return context
    
    def get_context(self, session_id: str) -> Optional[AgentContext]:
        """
        获取上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            AgentContext实例，如果不存在则返回None
        """
        return self.contexts.get(session_id)
    
    def update_context(self, 
                      session_id: str,
                      role: str,
                      content: str) -> Optional[AgentContext]:
        """
        更新上下文 - 添加新消息
        
        Args:
            session_id: 会话ID
            role: 角色(user/assistant/system)
            content: 消息内容
            
        Returns:
            更新后的AgentContext实例，如果不存在则返回None
        """
        context = self.get_context(session_id)
        if not context:
            return None
        
        try:
            # 添加消息
            if role == "system":
                context.add_system_message(content)
            else:
                context.add_message(role, content)
                
            return context
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"更新上下文失败: {e}")
            return None
    
    def prepare_for_agent_sdk(self, context: AgentContext) -> Dict[str, Any]:
        """
        准备用于OpenAI Agent SDK的上下文
        
        Args:
            context: AgentContext实例
            
        Returns:
            适合传递给Runner.run的字典
        """
        try:
            # 确保在转换前应用清理
            if hasattr(context, '_cleanup_messages'):
                context._cleanup_messages()
                
            return context.to_dict()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"准备上下文失败: {e}")
            # 返回一个最小的默认上下文
            return {
                "messages": [{"role": "system", "content": "你是一个智能助手。"}],
                "user_id": "anonymous",
                "user_name": "用户",
                "metadata": {}
            }


# 创建全局上下文管理器实例
context_manager = ContextManager() 