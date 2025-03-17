"""
会话-上下文桥接模块 - 提供会话管理服务与SimpleContext的无缝集成

该模块实现了会话管理服务与上下文管理之间的桥接，使得持久化的会话数据
可以方便地转换为SimpleContext对象，反之亦然。这样可以在保持会话持久化的
同时，充分利用SimpleContext的功能来传递给Agent SDK。
"""

import logging
from typing import Optional, Dict, Any, List, Union

# 导入SimpleContext
from agent_cores.core.simple_context import SimpleContext

# 直接从session_manager模块导入，避免循环导入
from .session_manager import SessionManager
from .models.session import Session

logger = logging.getLogger(__name__)

# 全局默认会话管理器实例
_default_manager: Optional[SessionManager] = None

def get_session_manager(storage_type: str = "redis") -> SessionManager:
    """
    获取默认会话管理器实例
    
    Args:
        storage_type: 存储类型，默认为redis
        
    Returns:
        SessionManager: 会话管理器实例
    """
    global _default_manager
    
    if _default_manager is None:
        _default_manager = SessionManager(storage_type=storage_type)
        
    return _default_manager

class SessionContextBridge:
    """
    会话上下文桥接器 - 连接会话管理服务与SimpleContext
    
    该类提供了一种简洁的方式来集成会话管理服务的持久化功能与
    SimpleContext的依赖注入功能，遵循OpenAI Agent SDK的设计理念。
    
    使用该桥接器可以:
    1. 从持久化会话加载消息到SimpleContext
    2. 将SimpleContext的消息持久化到会话
    3. 在会话管理与Agent执行之间无缝切换
    """
    
    def __init__(self, session_id: str, user_id: str, user_name: str = "用户", session_manager = None):
        """
        初始化会话上下文桥接器
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            user_name: 用户名
            session_manager: 会话管理器实例，如果为None则使用默认实例
        """
        self.session_id = session_id
        self.user_id = user_id
        self.user_name = user_name
        self.session_manager = session_manager or get_session_manager()
        self._context_cache = None  # 用于缓存上下文
        
    async def get_context(self, refresh: bool = True) -> SimpleContext:
        """
        获取SimpleContext实例，加载会话中的所有消息
        
        Args:
            refresh: 是否强制刷新缓存，默认为True
            
        Returns:
            SimpleContext: 包含会话所有消息的上下文对象
        """
        # 如果有缓存且不需要刷新，直接返回缓存
        if not refresh and self._context_cache is not None:
            return self._context_cache
            
        # 从会话中获取消息
        messages = await self.session_manager.get_session_messages(self.session_id, self.user_id)
        
        # 获取会话以提取元数据
        session = await self.session_manager.get_session(self.session_id, self.user_id)
        
        # 准备元数据
        metadata = {}
        if session and hasattr(session, "metadata") and session.metadata:
            # 尝试从session.metadata对象中提取属性
            if hasattr(session.metadata, "properties") and session.metadata.properties:
                if isinstance(session.metadata.properties, dict):
                    metadata = session.metadata.properties.copy()
                else:
                    logger.warning(f"会话元数据properties不是字典: {type(session.metadata.properties)}")
            
            # 尝试从其他属性中提取
            for attr in ["message_count", "status", "last_active"]:
                if hasattr(session.metadata, attr):
                    try:
                        metadata[attr] = getattr(session.metadata, attr)
                    except Exception as e:
                        logger.warning(f"无法提取元数据属性 {attr}: {e}")
        
        # 添加用户信息到元数据
        metadata["user_id"] = self.user_id
        metadata["user_name"] = self.user_name
        
        # 创建SimpleContext
        context = SimpleContext(
            user_id=self.user_id,
            user_name=self.user_name,
            metadata=metadata
        )
        
        # 添加系统消息，包含用户信息
        user_info_message = f"""用户信息:
- 用户ID: {self.user_id}
- 用户名称: {self.user_name}"""
        
        # 添加重要元数据到系统消息
        important_fields = ["preference", "language", "role", "permission_level"]
        for field in important_fields:
            if field in metadata:
                user_info_message += f"\n- {field}: {metadata[field]}"
        
        # 添加用户信息系统消息
        context.add_system_message(user_info_message)
        logger.debug(f"添加用户信息系统消息: {user_info_message}")
        
        # 加载消息到上下文
        for msg in messages:
            if msg["role"] == "system":
                context.add_system_message(msg["content"])
            else:
                context.add_message(msg["role"], msg["content"])
                
        # 缓存上下文
        self._context_cache = context
        
        return context
    
    async def add_message(self, role: str, content: str) -> bool:
        """
        添加消息到会话
        
        Args:
            role: 消息角色(user/assistant/system)
            content: 消息内容
            
        Returns:
            bool: 是否成功添加
        """
        # 添加到会话
        success = await self.session_manager.add_message(
            session_id=self.session_id,
            user_id=self.user_id,
            role=role,
            content=content
        )
        
        # 如果添加成功且有缓存，同步更新缓存
        if success and self._context_cache:
            if role == "system":
                self._context_cache.add_system_message(content)
            else:
                self._context_cache.add_message(role, content)
                
        return success
    
    async def add_system_message(self, content: str) -> bool:
        """
        添加系统消息到会话
        
        Args:
            content: 系统消息内容
            
        Returns:
            bool: 是否成功添加
        """
        return await self.add_message("system", content)
    
    async def update_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        更新会话元数据
        
        Args:
            metadata: 要更新的元数据
            
        Returns:
            bool: 是否成功更新
        """
        # 更新会话元数据
        success = await self.session_manager.update_session(
            session_id=self.session_id,
            user_id=self.user_id,
            metadata_updates=metadata
        )
        
        # 如果更新成功且有缓存，同步更新缓存的元数据
        if success and self._context_cache:
            for key, value in metadata.items():
                self._context_cache.metadata[key] = value
                
        return success
    
    async def get_session(self) -> Optional[Session]:
        """
        获取当前会话对象
        
        Returns:
            Optional[Session]: 会话对象
        """
        return await self.session_manager.get_session(self.session_id, self.user_id)
    
    async def get_messages(self, limit: int = 0) -> List[Dict[str, str]]:
        """
        获取会话消息
        
        Args:
            limit: 获取的消息数量限制，0表示获取所有消息
            
        Returns:
            List[Dict[str, str]]: 消息列表
        """
        return await self.session_manager.get_session_messages(
            session_id=self.session_id,
            user_id=self.user_id,
            limit=limit
        )
    
    async def sync_from_context(self, context: SimpleContext) -> bool:
        """
        从SimpleContext同步消息到会话
        
        Args:
            context: SimpleContext实例
            
        Returns:
            bool: 是否成功同步
        """
        # 清除当前会话消息
        session = await self.get_session()
        if not session:
            logger.error(f"无法获取会话 {self.session_id}")
            return False
            
        success = await self.session_manager.clear_session_messages(
            session_id=self.session_id,
            user_id=self.user_id,
            preserve_system=False
        )
        
        if not success:
            logger.error(f"清除会话 {self.session_id} 消息失败")
            return False
            
        # 添加上下文中的所有消息
        for msg in context.messages:
            role = msg.get("role")
            content = msg.get("content")
            
            if not role or not content:
                continue
                
            await self.add_message(role, content)
            
        # 更新元数据
        await self.update_metadata(context.metadata)
        
        # 更新缓存
        self._context_cache = context
        
        return True
    
    @classmethod
    async def create_session(cls, user_id: str, user_name: str = "用户", 
                          metadata: Dict[str, Any] = None, 
                          ttl_hours: int = 24,
                          system_message: str = None,
                          session_manager = None) -> Optional["SessionContextBridge"]:
        """
        创建新会话并返回桥接器
        
        Args:
            user_id: 用户ID
            user_name: 用户名称
            metadata: 会话元数据
            ttl_hours: 会话过期时间(小时)
            system_message: 可选的系统消息
            session_manager: 会话管理器实例，如果为None则使用默认实例
            
        Returns:
            Optional[SessionContextBridge]: 会话上下文桥接器实例
        """
        # 获取会话管理器
        sm = session_manager or get_session_manager()
        await sm.initialize()
        
        # 准备元数据
        meta = metadata or {}
        if "user_name" not in meta:
            meta["user_name"] = user_name
        if "user_id" not in meta:
            meta["user_id"] = user_id
            
        # 创建会话
        session_id = await sm.create_session(
            user_id=user_id,
            metadata=meta,
            ttl_hours=ttl_hours
        )
        
        if not session_id:
            logger.error(f"创建用户 {user_id} 的会话失败")
            return None
            
        # 创建桥接器
        bridge = cls(session_id, user_id, user_name, sm)
        
        # 添加系统消息(如果有)
        if system_message:
            await bridge.add_system_message(system_message)
            
        return bridge
    
    @classmethod
    async def from_context(cls, context: SimpleContext, ttl_hours: int = 24, 
                         session_manager = None) -> Optional["SessionContextBridge"]:
        """
        从SimpleContext创建新会话
        
        Args:
            context: SimpleContext实例
            ttl_hours: 会话过期时间(小时)
            session_manager: 会话管理器实例，如果为None则使用默认实例
            
        Returns:
            Optional[SessionContextBridge]: 会话上下文桥接器实例
        """
        # 获取用户信息
        user_id = context.user_id
        user_name = context.user_name
        
        # 创建会话
        bridge = await cls.create_session(
            user_id=user_id,
            user_name=user_name,
            metadata=context.metadata,
            ttl_hours=ttl_hours,
            session_manager=session_manager
        )
        
        if not bridge:
            return None
            
        # 同步消息
        await bridge.sync_from_context(context)
        
        return bridge
    
    async def close(self):
        """关闭桥接器，释放资源"""
        self._context_cache = None


def get_session_context_bridge(session_id: str, user_id: str, 
                             user_name: str = "用户", 
                             session_manager = None) -> SessionContextBridge:
    """
    获取会话上下文桥接器
    
    Args:
        session_id: 会话ID
        user_id: 用户ID
        user_name: 用户名
        session_manager: 会话管理器实例，如果为None则使用默认实例
        
    Returns:
        SessionContextBridge: 会话上下文桥接器实例
    """
    return SessionContextBridge(session_id, user_id, user_name, session_manager) 