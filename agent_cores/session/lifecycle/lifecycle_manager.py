"""
生命周期管理器 - 管理会话的生命周期
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..storage.base import StorageProvider
from ..models.session import Session, SessionMetadata
from ...core.simple_context import SimpleContext

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    会话生命周期管理器

    管理会话的创建、过期检查和清理，确保资源得到及时释放。
    提供自动清理过期会话的功能，可配置清理频率和策略。
    """

    def __init__(self, storage: StorageProvider, cleanup_interval: int = 3600):
        """
        初始化生命周期管理器

        Args:
            storage: 存储提供者
            cleanup_interval: 自动清理过期会话的间隔时间(秒)
        """
        self.storage = storage
        self.cleanup_interval = cleanup_interval
        self._cleanup_task = None

    async def create_session(self, user_id: str,
                             ttl_hours: int = 24,
                             metadata: Dict[str, Any] = None) -> Optional[Session]:
        """
        创建新会话

        Args:
            user_id: 用户ID
            ttl_hours: 会话生存时间(小时)
            metadata: 会话元数据

        Returns:
            Optional[Session]: 新创建的会话对象，如果创建失败则返回None
        """
        try:
            # 创建会话元数据
            now = datetime.now()
            metadata_obj = SessionMetadata(
                created_at=now,
                last_accessed_at=now,
                expires_at=now + timedelta(hours=ttl_hours) if ttl_hours > 0 else None,
                status="active",
                owner_id=user_id,
                properties=metadata or {}
            )

            # 提取用户名
            user_name = metadata.get("user_name", "用户") if metadata else "用户"

            # 创建上下文
            context = SimpleContext(
                user_id=user_id,
                user_name=user_name,
                metadata=metadata or {}
            )

            # 创建会话
            session = Session(
                context=context,
                metadata=metadata_obj
            )

            # 保存会话
            success = await self.storage.save_session(session)
            if success:
                logger.info(f"已为用户 {user_id} 创建会话 {session.id}")
                return session

            logger.error(f"为用户 {user_id} 创建会话失败: 保存失败")
            return None

        except Exception as e:
            logger.error(f"为用户 {user_id} 创建会话失败: {e}")
            return None

    async def update_session_status(self, session_id: str, status: str) -> bool:
        """
        更新会话状态

        Args:
            session_id: 会话ID
            status: 新状态

        Returns:
            bool: 是否更新成功
        """
        try:
            return await self.storage.update_metadata(session_id, {"status": status})
        except Exception as e:
            logger.error(f"更新会话 {session_id} 状态失败: {e}")
            return False

    async def extend_session_expiry(self, session_id: str, hours: int) -> bool:
        """
        延长会话过期时间

        Args:
            session_id: 会话ID
            hours: 延长的小时数

        Returns:
            bool: 是否延长成功
        """
        try:
            # 加载会话
            session = await self.storage.load_session(session_id)
            if not session:
                logger.warning(f"要延长的会话 {session_id} 不存在")
                return False

            # 计算新的过期时间
            if session.metadata.expires_at:
                new_expiry = session.metadata.expires_at + timedelta(hours=hours)
            else:
                new_expiry = datetime.now() + timedelta(hours=hours)

            # 更新过期时间
            return await self.storage.update_metadata(
                session_id,
                {"expires_at": new_expiry.isoformat()}
            )

        except Exception as e:
            logger.error(f"延长会话 {session_id} 过期时间失败: {e}")
            return False

    async def end_session(self, session_id: str) -> bool:
        """
        结束会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否结束成功
        """
        return await self.update_session_status(session_id, "ended")

    async def pause_session(self, session_id: str) -> bool:
        """
        暂停会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否暂停成功
        """
        return await self.update_session_status(session_id, "paused")

    async def resume_session(self, session_id: str) -> bool:
        """
        恢复会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否恢复成功
        """
        return await self.update_session_status(session_id, "active")

    async def check_expired_sessions(self) -> List[Session]:
        """
        检查已过期的会话

        Returns:
            List[Session]: 已过期的会话列表
        """
        try:
            # 获取所有会话
            sessions = await self.storage.list_sessions(limit=1000)

            # 检查哪些会话已过期
            now = datetime.now()
            expired_sessions = [
                session for session in sessions
                if session.metadata.expires_at and session.metadata.expires_at < now
            ]

            return expired_sessions

        except Exception as e:
            logger.error(f"检查过期会话失败: {e}")
            return []

    async def clean_expired_sessions(self) -> int:
        """
        清理过期会话

        Returns:
            int: 清理的会话数量
        """
        try:
            return await self.storage.clean_expired_sessions()
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0

    async def start_cleanup_task(self) -> None:
        """启动自动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("已启动会话自动清理任务")

    async def stop_cleanup_task(self) -> None:
        """停止自动清理任务"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("已停止会话自动清理任务")

    async def _cleanup_loop(self) -> None:
        """自动清理循环"""
        try:
            while True:
                # 执行清理
                count = await self.clean_expired_sessions()
                if count > 0:
                    logger.info(f"自动清理: 已清理 {count} 个过期会话")

                # 等待下次清理
                await asyncio.sleep(self.cleanup_interval)
        except asyncio.CancelledError:
            logger.info("会话自动清理任务已取消")
            raise 