"""
存储提供者抽象基类 - 定义存储接口
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from ..models.session import Session


class StorageProvider(ABC):
    """
    存储提供者抽象基类，定义所有存储实现必须支持的接口

    所有具体存储实现(如Redis存储、数据库存储等)必须继承此类并实现其方法。
    """

    @abstractmethod
    async def save_session(self, session: Session) -> bool:
        """
        保存会话到存储

        Args:
            session: 要保存的会话对象

        Returns:
            bool: 是否保存成功
        """
        pass

    @abstractmethod
    async def load_session(self, session_id: str) -> Optional[Session]:
        """
        从存储加载会话

        Args:
            session_id: 会话ID

        Returns:
            Optional[Session]: 会话对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """
        从存储删除会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否删除成功
        """
        pass

    @abstractmethod
    async def list_sessions(self,
                            owner_id: Optional[str] = None,
                            status: Optional[str] = None,
                            tags: Optional[List[str]] = None,
                            limit: int = 100,
                            offset: int = 0) -> List[Session]:
        """
        列出符合条件的会话

        Args:
            owner_id: 所有者ID，如果指定则只返回此所有者的会话
            status: 会话状态，如果指定则只返回此状态的会话
            tags: 标签列表，如果指定则只返回包含这些标签的会话
            limit: 返回结果数量限制
            offset: 结果偏移量，用于分页

        Returns:
            List[Session]: 会话列表
        """
        pass

    @abstractmethod
    async def update_metadata(self, session_id: str, metadata_updates: Dict[str, Any]) -> bool:
        """
        更新会话元数据

        Args:
            session_id: 会话ID
            metadata_updates: 要更新的元数据字段和值

        Returns:
            bool: 是否更新成功
        """
        pass

    @abstractmethod
    async def clean_expired_sessions(self) -> int:
        """
        清理过期会话，返回清理的会话数量

        Returns:
            int: 清理的会话数量
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取存储统计信息

        Returns:
            Dict[str, Any]: 包含统计信息的字典
        """
        pass 