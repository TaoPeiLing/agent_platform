"""
Redis上下文管理器 - 使用Redis存储代理上下文

该模块通过Redis管理与OpenAI Agent SDK兼容的上下文系统，提供：
1. 持久化存储 - 服务重启后会话数据不丢失
2. 分布式支持 - 多个应用实例可以共享会话数据  
3. 内存外部管理 - 避免应用内存溢出问题
4. 自动过期管理 - 自动清理不活跃的会话
"""

import os
import json
import logging
import time
import redis
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict

# 配置日志
logger = logging.getLogger(__name__)

# 从环境变量获取默认配置
DEFAULT_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_KEY_PREFIX = os.getenv("REDIS_PREFIX", "agent:context:")
DEFAULT_EXPIRY = int(os.getenv("REDIS_EXPIRY", 86400))  # 24小时
DEFAULT_MAX_MESSAGES = int(os.getenv("CONTEXT_MAX_MESSAGES", 20))
DEFAULT_MAX_CONTENT_LENGTH = int(os.getenv("CONTEXT_MAX_CONTENT_LENGTH", 10000))
DEFAULT_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", 10))
DEFAULT_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", 5))


@dataclass
class AgentContext:
    """
    代理上下文 - 符合OpenAI Agent SDK的上下文对象
    
    这个类对应OpenAI Agent SDK文档中的Context对象，
    用于依赖注入和状态管理。支持序列化和反序列化，
    便于Redis存储。
    """
    # 用户信息
    user_id: str = "anonymous"
    user_name: str = "用户"
    
    # 系统指令和元数据
    system_instruction: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 消息历史 - 符合OpenAI格式的消息列表
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    # 会话管理
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # 限制配置 - 从环境变量获取默认值
    max_messages: int = DEFAULT_MAX_MESSAGES
    max_content_length: int = DEFAULT_MAX_CONTENT_LENGTH
    
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
        # 更新时间戳
        self.updated_at = time.time()
        
        # 安全检查 - 确保内容是字符串
        if not isinstance(content, str):
            content = str(content)
            
        # 内容长度限制
        if len(content) > self.max_content_length:
            content = content[:self.max_content_length] + "...(内容过长，已截断)"
            
        # 添加新消息
        new_message = {
            "role": role,
            "content": content,
            "timestamp": self.updated_at
        }
        
        # 如果是system消息，确保在首位
        if role == "system":
            # 移除现有系统消息
            self.messages = [msg for msg in self.messages if msg.get("role") != "system"]
            # 添加新的系统消息到开头
            self.messages.insert(0, new_message)
            # 更新系统指令
            self.system_instruction = content
        else:
            # 添加到列表末尾
            self.messages.append(new_message)
            
        # 清理过多消息
        self._cleanup_messages()
        
    def _cleanup_messages(self) -> None:
        """清理过多消息，保留系统消息和最新的消息"""
        if len(self.messages) > self.max_messages:
            # 保留系统消息
            system_messages = [msg for msg in self.messages if msg.get("role") == "system"]
            # 保留最新消息
            recent_messages = self.messages[-(self.max_messages - len(system_messages)):]
            # 重建消息列表
            self.messages = system_messages + recent_messages
        
    def add_system_message(self, content: str) -> None:
        """
        添加系统消息 - 确保系统消息在首位
        
        Args:
            content: 系统消息内容
        """
        # 更新时间戳
        self.updated_at = time.time()
        
        # 保存系统指令
        self.system_instruction = content
        
        # 安全检查
        if not isinstance(content, str):
            content = str(content)
            
        # 内容长度限制
        if len(content) > self.max_content_length:
            content = content[:self.max_content_length] + "...(内容过长，已截断)"
        
        # 检查是否有系统消息
        has_system = False
        for msg in self.messages:
            if msg["role"] == "system":
                msg["content"] = content
                msg["timestamp"] = self.updated_at
                has_system = True
                break
                
        # 如果没有，添加到开头
        if not has_system:
            self.messages.insert(0, {
                "role": "system",
                "content": content,
                "timestamp": self.updated_at
            })
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式 - 用于传递给OpenAI Agent SDK
        
        Returns:
            包含必要上下文信息的字典
        """
        # 确保消息不会过多
        self._cleanup_messages()
        
        # 准备最终的上下文字典，去掉不需要的内部字段
        return {
            "messages": [
                {
                    "role": msg["role"],
                    "content": msg["content"]
                } 
                for msg in self.messages
            ],
            "user_id": self.user_id,
            "user_name": self.user_name,
            "metadata": self.metadata
        }
    
    def to_redis_dict(self) -> Dict[str, Any]:
        """
        转换为适合Redis存储的字典，包含完整信息
        
        Returns:
            包含完整上下文信息的字典
        """
        # 直接使用dataclass的asdict方法
        return asdict(self)
    
    @classmethod
    def from_redis_dict(cls, data: Dict[str, Any]) -> 'AgentContext':
        """
        从Redis字典创建上下文
        
        Args:
            data: 从Redis读取的字典数据
            
        Returns:
            AgentContext实例
        """
        return cls(**data)


class RedisContextManager:
    """
    Redis上下文管理器 - 使用Redis存储会话上下文
    
    使用Redis作为存储后端，支持会话持久化、自动过期和分布式部署。
    """
    
    def __init__(self, 
                redis_url: str = DEFAULT_REDIS_URL,
                key_prefix: str = DEFAULT_KEY_PREFIX,
                default_expiry: int = DEFAULT_EXPIRY,
                max_messages: int = DEFAULT_MAX_MESSAGES,
                connection_pool_kwargs: Optional[Dict[str, Any]] = None):
        """
        初始化Redis上下文管理器
        
        Args:
            redis_url: Redis连接URL
            key_prefix: Redis键前缀
            default_expiry: 默认过期时间(秒)
            max_messages: 每个上下文的最大消息数
            connection_pool_kwargs: Redis连接池参数
        """
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_expiry = default_expiry
        self.max_messages = max_messages
        
        # 创建连接池配置
        self.pool_kwargs = connection_pool_kwargs or {
            "max_connections": DEFAULT_MAX_CONNECTIONS,
            "socket_timeout": DEFAULT_SOCKET_TIMEOUT,
            "socket_keepalive": True,
            "health_check_interval": 30
        }
        
        # 懒加载Redis客户端
        self._redis_client = None
        
        # 记录初始化信息
        logger.info(f"初始化Redis上下文管理器: URL={redis_url}, 前缀={key_prefix}, "
                  f"过期时间={default_expiry}秒, 最大消息数={max_messages}")
        
    @property
    def redis(self) -> redis.Redis:
        """获取Redis客户端，如果未初始化则创建"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(self.redis_url, **self.pool_kwargs)
                logger.info(f"已连接到Redis: {self.redis_url}")
            except Exception as e:
                logger.error(f"Redis连接失败: {e}")
                # 创建一个内存模拟Redis，仅用于开发/测试
                # from fakeredis import FakeRedis
                # logger.warning("使用FakeRedis作为后备方案")
                # self._redis_client = FakeRedis()
        return self._redis_client
    
    def _get_key(self, session_id: str) -> str:
        """获取会话的Redis键"""
        return f"{self.key_prefix}{session_id}"
    
    def create_context(self,
                      session_id: str,
                      user_id: str = "anonymous",
                      user_name: str = "用户",
                      system_instruction: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None,
                      expiry: Optional[int] = None,
                      max_messages: Optional[int] = None) -> AgentContext:
        """
        创建新上下文并存储到Redis
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            user_name: 用户名
            system_instruction: 系统指令
            metadata: 元数据
            expiry: 过期时间(秒)，默认使用实例默认值
            max_messages: 最大消息数量
            
        Returns:
            新创建的AgentContext实例
        """
        # 使用提供的值或默认值
        max_msg = max_messages if max_messages is not None else self.max_messages
        
        # 创建上下文
        context = AgentContext(
            user_id=user_id,
            user_name=user_name,
            metadata=metadata or {},
            max_messages=max_msg,
            created_at=time.time(),
            updated_at=time.time()
        )
        
        # 添加系统指令
        if system_instruction:
            context.add_system_message(system_instruction)
            
        # 保存到Redis
        self._save_context(session_id, context, expiry)
        
        return context
    
    def _save_context(self, 
                     session_id: str, 
                     context: AgentContext,
                     expiry: Optional[int] = None) -> bool:
        """
        保存上下文到Redis
        
        Args:
            session_id: 会话ID
            context: AgentContext实例
            expiry: 过期时间(秒)
            
        Returns:
            是否成功保存
        """
        try:
            # 获取Redis键
            key = self._get_key(session_id)
            
            # 序列化上下文
            context_dict = context.to_redis_dict()
            json_data = json.dumps(context_dict)
            
            # 设置过期时间
            exp = expiry if expiry is not None else self.default_expiry
            
            # 保存到Redis
            self.redis.set(key, json_data, ex=exp)
            
            return True
        except Exception as e:
            logger.error(f"保存上下文到Redis失败: {e}")
            return False
    
    def get_context(self, session_id: str) -> Optional[AgentContext]:
        """
        从Redis获取上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            AgentContext实例，如果不存在则返回None
        """
        try:
            # 获取Redis键
            key = self._get_key(session_id)
            
            # 从Redis获取数据
            json_data = self.redis.get(key)
            
            if not json_data:
                return None
                
            # 反序列化
            context_dict = json.loads(json_data)
            
            # 创建上下文对象
            return AgentContext.from_redis_dict(context_dict)
        except Exception as e:
            logger.error(f"从Redis获取上下文失败: {e}")
            return None
    
    def update_context(self,
                      session_id: str,
                      role: str,
                      content: str,
                      expiry: Optional[int] = None) -> Optional[AgentContext]:
        """
        更新上下文 - 添加新消息
        
        Args:
            session_id: 会话ID
            role: 角色(user/assistant/system)
            content: 消息内容
            expiry: 过期时间(秒)
            
        Returns:
            更新后的AgentContext实例，如果失败则返回None
        """
        try:
            # 获取现有上下文
            context = self.get_context(session_id)
            
            if not context:
                return None
                
            # 添加消息
            if role == "system":
                context.add_system_message(content)
            else:
                context.add_message(role, content)
                
            # 保存回Redis
            self._save_context(session_id, context, expiry)
            
            return context
        except Exception as e:
            logger.error(f"更新上下文失败: {e}")
            return None
    
    def delete_context(self, session_id: str) -> bool:
        """
        删除上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功删除
        """
        try:
            # 获取Redis键
            key = self._get_key(session_id)
            
            # 删除键
            self.redis.delete(key)
            
            return True
        except Exception as e:
            logger.error(f"删除上下文失败: {e}")
            return False
    
    def list_sessions(self, pattern: str = "*") -> List[str]:
        """
        列出所有会话ID
        
        Args:
            pattern: 匹配模式
            
        Returns:
            会话ID列表
        """
        try:
            # 构建完整模式
            full_pattern = f"{self.key_prefix}{pattern}"
            
            # 使用scan迭代器，避免阻塞Redis
            keys = []
            for key in self.redis.scan_iter(match=full_pattern):
                # 移除前缀，提取会话ID
                session_id = key.decode('utf-8').replace(self.key_prefix, "")
                keys.append(session_id)
                
            return keys
        except Exception as e:
            logger.error(f"列出会话失败: {e}")
            return []
    
    def clear_all(self, confirm: bool = False) -> bool:
        """
        清除所有会话数据(危险操作)
        
        Args:
            confirm: 确认操作
            
        Returns:
            是否成功清除
        """
        if not confirm:
            logger.warning("清除所有会话需要确认参数confirm=True")
            return False
            
        try:
            # 获取所有会话键
            keys = self.redis.keys(f"{self.key_prefix}*")
            
            if not keys:
                return True
                
            # 删除所有键
            self.redis.delete(*keys)
            
            return True
        except Exception as e:
            logger.error(f"清除所有会话失败: {e}")
            return False
    
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
            logger.error(f"准备上下文失败: {e}")
            # 返回最小默认上下文
            return {
                "messages": [{"role": "system", "content": "你是一个智能助手。"}],
                "user_id": "anonymous",
                "user_name": "用户",
                "metadata": {}
            }
    
    def touch(self, session_id: str, expiry: Optional[int] = None) -> bool:
        """
        刷新会话过期时间
        
        Args:
            session_id: 会话ID
            expiry: 新的过期时间(秒)
            
        Returns:
            是否成功
        """
        try:
            # 获取Redis键
            key = self._get_key(session_id)
            
            # 检查键是否存在
            if not self.redis.exists(key):
                return False
                
            # 设置新的过期时间
            exp = expiry if expiry is not None else self.default_expiry
            self.redis.expire(key, exp)
            
            return True
        except Exception as e:
            logger.error(f"刷新会话过期时间失败: {e}")
            return False


# 创建全局Redis上下文管理器实例
# 注意：实际应用中从环境变量获取Redis配置
redis_context_manager = RedisContextManager(
    redis_url=DEFAULT_REDIS_URL,
    key_prefix=DEFAULT_KEY_PREFIX,
    default_expiry=DEFAULT_EXPIRY,
    max_messages=DEFAULT_MAX_MESSAGES
)