"""
会话管理器 - 会话管理服务的核心入口
"""

import os
import logging
import asyncio
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime, timedelta

from .models.session import Session, SessionMetadata
from .storage import StorageFactory
from .access.access_control import AccessController
from .lifecycle.lifecycle_manager import LifecycleManager
from ..core.simple_context import SimpleContext

logger = logging.getLogger(__name__)


class SessionManager:
    """
    会话管理核心服务

    作为会话管理的统一入口，集成存储、访问控制和生命周期管理功能。
    提供会话的创建、检索、更新、删除等功能，同时处理权限检查和生命周期管理。
    """

    def __init__(self, storage_type="redis"):
        """
        初始化会话管理器

        Args:
            storage_type: 存储类型，默认为redis
        """
        self.storage = StorageFactory.create(storage_type)
        self.access_controller = AccessController()
        self.lifecycle_manager = LifecycleManager(self.storage)
        self._cleaner_task = None
        self._initialized = False

    async def initialize(self):
        """
        初始化会话管理器

        连接存储并启动清理任务。
        """
        if self._initialized:
            return

        # 连接存储
        if hasattr(self.storage, 'connect'):
            await self.storage.connect()

        # 启动过期会话清理任务
        await self.lifecycle_manager.start_cleanup_task()

        self._initialized = True
        logger.info("会话管理器初始化完成")

    async def shutdown(self):
        """
        关闭会话管理器

        停止清理任务并关闭存储连接。
        """
        if not self._initialized:
            return

        # 停止清理任务
        await self.lifecycle_manager.stop_cleanup_task()

        # 关闭存储连接
        if hasattr(self.storage, 'close'):
            await self.storage.close()

        self._initialized = False
        logger.info("会话管理器已关闭")

    async def create_session(self, user_id: str,
                             metadata: Dict[str, Any] = None,
                             ttl_hours: int = 24) -> Optional[str]:
        """
        创建新会话

        Args:
            user_id: 用户ID
            metadata: 会话元数据
            ttl_hours: 会话生存时间(小时)

        Returns:
            Optional[str]: 会话ID，如果创建失败则返回None
        """
        if not self._initialized:
            await self.initialize()

        session = await self.lifecycle_manager.create_session(
            user_id=user_id,
            ttl_hours=ttl_hours,
            metadata=metadata
        )

        if session:
            return session.id

        return None

    async def get_session(self, session_id: str, user_id: str) -> Optional[Session]:
        """
        获取会话

        Args:
            session_id: 会话ID
            user_id: 用户ID，用于权限检查

        Returns:
            Optional[Session]: 会话对象，如果会话不存在或用户无权访问则返回None
        """
        if not self._initialized:
            await self.initialize()

        # 加载会话
        session = await self.storage.load_session(session_id)
        if not session:
            logger.warning(f"会话 {session_id} 不存在")
            return None

        # 检查会话是否过期
        if session.is_expired():
            logger.warning(f"会话 {session_id} 已过期")
            return None

        # 检查访问权限
        if not self.access_controller.can_access(session, user_id):
            logger.warning(f"用户 {user_id} 无权访问会话 {session_id}")
            return None

        return session

    async def update_session(self, session_id: str, user_id: str,
                             context_updates: Dict[str, Any] = None,
                             metadata_updates: Dict[str, Any] = None) -> bool:
        """
        更新会话

        Args:
            session_id: 会话ID
            user_id: 用户ID，用于权限检查
            context_updates: 上下文更新
            metadata_updates: 元数据更新

        Returns:
            bool: 是否更新成功
        """
        if not self._initialized:
            await self.initialize()

        # 获取会话
        session = await self.get_session(session_id, user_id)
        if not session:
            return False

        # 检查写入权限
        if not self.access_controller.can_write(session, user_id):
            logger.warning(f"用户 {user_id} 无权修改会话 {session_id}")
            return False

        # 更新上下文
        if context_updates:
            # 更新元数据
            if "metadata" in context_updates:
                session.context.update_metadata(context_updates["metadata"])

            # 添加消息
            if "messages" in context_updates:
                for msg in context_updates["messages"]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role and content:
                        session.context.add_message(role, content)

                        # 更新消息计数
                        session.metadata.increment_counters(
                            messages=1,
                            tokens=len(content) // 4,  # 简单估算token数
                            turns=0.5 if role in ["user", "assistant"] else 0
                        )

        # 更新元数据
        if metadata_updates:
            for key, value in metadata_updates.items():
                if hasattr(session.metadata, key):
                    setattr(session.metadata, key, value)
                else:
                    session.metadata.properties[key] = value

        # 保存更新
        success = await self.storage.save_session(session)
        if success:
            logger.info(f"已更新会话 {session_id}")
        else:
            logger.error(f"更新会话 {session_id} 失败")

        return success

    async def add_message(self, session_id: str, user_id: str,
                          role: str, content: str) -> bool:
        """
        添加消息到会话

        Args:
            session_id: 会话ID
            user_id: 用户ID，用于权限检查
            role: 消息角色(user/assistant/system)
            content: 消息内容

        Returns:
            bool: 是否添加成功
        """
        return await self.update_session(
            session_id=session_id,
            user_id=user_id,
            context_updates={
                "messages": [{"role": role, "content": content}]
            }
        )

    async def add_system_message(self, session_id: str, user_id: str, content: str) -> bool:
        """
        添加系统消息到会话，这会覆盖之前的系统消息

        Args:
            session_id: 会话ID
            user_id: 用户ID，用于权限检查
            content: 系统消息内容

        Returns:
            bool: 是否添加成功
        """
        # 获取会话
        session = await self.get_session(session_id, user_id)
        if not session:
            return False

        # 检查写入权限
        if not self.access_controller.can_write(session, user_id):
            logger.warning(f"用户 {user_id} 无权修改会话 {session_id}")
            return False

        # 添加系统消息
        session.context.add_system_message(content)

        # 保存更新
        success = await self.storage.save_session(session)
        if success:
            logger.info(f"已更新会话 {session_id} 的系统消息")
        else:
            logger.error(f"更新会话 {session_id} 的系统消息失败")

        return success

    async def list_user_sessions(self, user_id: str,
                                 status: str = None,
                                 limit: int = 10,
                                 offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出用户的会话

        Args:
            user_id: 用户ID
            status: 会话状态过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[Dict[str, Any]]: 会话摘要列表
        """
        if not self._initialized:
            await self.initialize()

        sessions = await self.storage.list_sessions(
            owner_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )

        # 转换为摘要格式
        return [
            {
                "id": session.id,
                "created_at": session.metadata.created_at.isoformat(),
                "last_accessed_at": session.metadata.last_accessed_at.isoformat(),
                "status": session.metadata.status,
                "tags": session.metadata.tags,
                "message_count": session.metadata.message_count,
                "turn_count": session.metadata.turn_count,
                "properties": session.metadata.properties
            }
            for session in sessions
        ]

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID
            user_id: 用户ID，用于权限检查

        Returns:
            bool: 是否删除成功
        """
        if not self._initialized:
            await self.initialize()

        # 获取会话
        session = await self.get_session(session_id, user_id)
        if not session:
            return False

        # 检查删除权限
        if not self.access_controller.can_delete(session, user_id):
            logger.warning(f"用户 {user_id} 无权删除会话 {session_id}")
            return False

        # 删除会话
        success = await self.storage.delete_session(session_id)
        if success:
            logger.info(f"已删除会话 {session_id}")
        else:
            logger.error(f"删除会话 {session_id} 失败")

        return success

    async def share_session(self, session_id: str, owner_id: str,
                            target_user_id: str) -> bool:
        """
        分享会话给其他用户

        Args:
            session_id: 会话ID
            owner_id: 所有者ID，用于权限检查
            target_user_id: 目标用户ID

        Returns:
            bool: 是否分享成功
        """
        if not self._initialized:
            await self.initialize()

        # 获取会话
        session = await self.get_session(session_id, owner_id)
        if not session:
            return False

        # 检查分享权限
        if not self.access_controller.can_share(session, owner_id, target_user_id):
            return False

        # 添加到共享列表
        if target_user_id not in session.metadata.shared_with:
            session.metadata.shared_with.append(target_user_id)

            # 保存更新
            success = await self.storage.save_session(session)
            if success:
                logger.info(f"已将会话 {session_id} 分享给用户 {target_user_id}")
                return True
            else:
                logger.error(f"分享会话 {session_id} 失败")
                return False

        # 已经在共享列表中
        return True

    async def end_session(self, session_id: str, user_id: str) -> bool:
        """
        结束会话

        Args:
            session_id: 会话ID
            user_id: 用户ID，用于权限检查

        Returns:
            bool: 是否结束成功
        """
        if not self._initialized:
            await self.initialize()

        # 获取会话
        session = await self.get_session(session_id, user_id)
        if not session:
            return False

        # 检查写入权限
        if not self.access_controller.can_write(session, user_id):
            logger.warning(f"用户 {user_id} 无权修改会话 {session_id}")
            return False

        # 结束会话
        return await self.lifecycle_manager.end_session(session_id)

    async def get_session_messages(self, session_id: str, user_id: str,
                                   limit: int = 50) -> Optional[List[Dict[str, str]]]:
        """
        获取会话消息

        Args:
            session_id: 会话ID
            user_id: 用户ID，用于权限检查
            limit: 返回最近的消息数量

        Returns:
            Optional[List[Dict[str, str]]]: 消息列表，如果会话不存在或用户无权访问则返回None
        """
        if not self._initialized:
            await self.initialize()

        # 获取会话
        session = await self.get_session(session_id, user_id)
        if not session:
            return None

        # 获取最近的消息
        if limit > 0:
            return session.context.get_last_n_messages(limit)
        else:
            return session.context.messages

    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取会话统计信息

        Returns:
            Dict[str, Any]: 包含统计信息的字典
        """
        if not self._initialized:
            await self.initialize()

        return await self.storage.get_statistics()

    async def clear_session_messages(self, session_id: str, user_id: str,
                                     preserve_system: bool = True) -> bool:
        """
        清除会话消息

        Args:
            session_id: 会话ID
            user_id: 用户ID，用于权限检查
            preserve_system: 是否保留系统消息

        Returns:
            bool: 是否清除成功
        """
        if not self._initialized:
            await self.initialize()

        # 获取会话
        session = await self.get_session(session_id, user_id)
        if not session:
            return False

        # 检查写入权限
        if not self.access_controller.can_write(session, user_id):
            logger.warning(f"用户 {user_id} 无权修改会话 {session_id}")
            return False

        # 清除消息
        session.context.clear_messages(preserve_system=preserve_system)

        # 重置计数器
        session.metadata.message_count = 0
        session.metadata.token_count = 0
        session.metadata.turn_count = 0

        # 保存更新
        success = await self.storage.save_session(session)
        if success:
            logger.info(f"已清除会话 {session_id} 的消息")
        else:
            logger.error(f"清除会话 {session_id} 的消息失败")

        return success