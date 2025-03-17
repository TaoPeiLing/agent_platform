"""
访问控制器 - 检查用户对会话的访问权限
"""

import logging
from typing import Dict, Any, Optional

from ..models.session import Session

logger = logging.getLogger(__name__)


class AccessController:
    """
    会话访问控制器

    负责检查用户是否有权限访问、修改或删除会话。
    支持多种访问控制策略，如所有者控制、共享访问和公共会话。
    """

    def can_access(self, session: Session, user_id: str) -> bool:
        """
        检查用户是否可以访问会话

        Args:
            session: 会话对象
            user_id: 用户ID

        Returns:
            bool: 是否有访问权限
        """
        # 公共会话可以被任何人访问
        if session.metadata.is_public:
            return True

        # 会话所有者可以访问自己的会话
        if session.metadata.owner_id == user_id:
            return True

        # 共享会话可以被共享用户访问
        if user_id in session.metadata.shared_with:
            return True

        # 记录访问尝试失败
        logger.warning(f"用户 {user_id} 尝试访问无权限的会话 {session.id}")
        return False

    def can_write(self, session: Session, user_id: str) -> bool:
        """
        检查用户是否可以修改会话

        Args:
            session: 会话对象
            user_id: 用户ID

        Returns:
            bool: 是否有写入权限
        """
        # 会话所有者可以修改自己的会话
        if session.metadata.owner_id == user_id:
            return True

        # 共享用户默认也可以修改，但可以根据需要调整这一策略
        if user_id in session.metadata.shared_with:
            # 可以在这里添加更细粒度的权限控制逻辑
            return True

        # 记录写入尝试失败
        logger.warning(f"用户 {user_id} 尝试修改无权限的会话 {session.id}")
        return False

    def can_delete(self, session: Session, user_id: str) -> bool:
        """
        检查用户是否可以删除会话

        Args:
            session: 会话对象
            user_id: 用户ID

        Returns:
            bool: 是否有删除权限
        """
        # 默认只有会话所有者可以删除会话
        if session.metadata.owner_id == user_id:
            return True

        # 记录删除尝试失败
        logger.warning(f"用户 {user_id} 尝试删除无权限的会话 {session.id}")
        return False

    def can_share(self, session: Session, user_id: str, target_user_id: str) -> bool:
        """
        检查用户是否可以分享会话给其他用户

        Args:
            session: 会话对象
            user_id: 分享操作发起用户ID
            target_user_id: 目标用户ID

        Returns:
            bool: 是否有分享权限
        """
        # 只有会话所有者可以分享会话
        if session.metadata.owner_id != user_id:
            logger.warning(f"用户 {user_id} 尝试分享不属于自己的会话 {session.id}")
            return False

        # 检查目标用户是否已在共享列表中
        if target_user_id in session.metadata.shared_with:
            logger.info(f"会话 {session.id} 已经与用户 {target_user_id} 共享")
            return True

        return True 