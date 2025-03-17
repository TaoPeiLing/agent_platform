"""
Redis存储提供者 - 使用Redis实现会话存储
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import redis.asyncio as aioredis
except ImportError:
    # 如果未安装redis.asyncio，后续将在初始化时报错
    aioredis = None

from .base import StorageProvider
from ..models.session import Session, SessionMetadata
from ...core.simple_context import SimpleContext

logger = logging.getLogger(__name__)


class RedisStorageProvider(StorageProvider):
    """
    Redis会话存储实现

    使用Redis作为存储后端，支持会话的创建、读取、更新和删除操作。
    使用Redis的集合和排序集合实现索引和查询功能。
    """

    def __init__(self, url=None, prefix=None, expiry=None):
        """
        初始化Redis存储提供者

        Args:
            url: Redis连接URL
            prefix: Redis键前缀
            expiry: 会话过期时间(秒)
        """
        if aioredis is None:
            logger.error("未安装Redis异步客户端库，请使用pip install redis[hiredis] 安装")
            raise ImportError("未安装Redis异步客户端库，请使用pip install redis[hiredis] 安装")

        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.prefix = prefix or os.getenv("REDIS_PREFIX", "agent:session:")
        self.expiry = int(expiry or os.getenv("REDIS_EXPIRY", "86400"))
        self.redis = None

    async def connect(self):
        """连接Redis"""
        if not self.redis:
            self.redis = await aioredis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info(f"已连接到Redis: {self.url}")
        return self.redis

    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("已关闭Redis连接")

    def _get_session_key(self, session_id):
        """获取会话Redis键"""
        return f"{self.prefix}{session_id}"

    def _get_metadata_key(self, session_id):
        """获取元数据Redis键"""
        return f"{self.prefix}{session_id}:metadata"

    def _get_owner_index_key(self, owner_id):
        """获取所有者索引键"""
        return f"{self.prefix}owner:{owner_id}"

    def _get_tag_index_key(self, tag):
        """获取标签索引键"""
        return f"{self.prefix}tag:{tag}"

    def _get_status_index_key(self, status):
        """获取状态索引键"""
        return f"{self.prefix}status:{status}"

    async def save_session(self, session: Session) -> bool:
        """
        保存会话到Redis

        Args:
            session: 要保存的会话对象

        Returns:
            bool: 是否保存成功
        """
        await self.connect()

        # 更新访问时间
        session.metadata.update_last_accessed()

        # 序列化上下文
        if session.context:
            context_data = session.context.serialize()
        else:
            context_data = ""

        # 序列化元数据
        metadata_dict = {
            "created_at": session.metadata.created_at.isoformat(),
            "last_accessed_at": session.metadata.last_accessed_at.isoformat(),
            "expires_at": session.metadata.expires_at.isoformat() if session.metadata.expires_at else None,
            "status": session.metadata.status,
            "tags": session.metadata.tags,
            "properties": session.metadata.properties,
            "message_count": session.metadata.message_count,
            "token_count": session.metadata.token_count,
            "turn_count": session.metadata.turn_count,
            "owner_id": session.metadata.owner_id,
            "shared_with": session.metadata.shared_with,
            "is_public": session.metadata.is_public,
        }

        # 保存会话数据
        session_key = self._get_session_key(session.id)
        metadata_key = self._get_metadata_key(session.id)

        try:
            # 开始Redis事务
            async with self.redis.pipeline(transaction=True) as pipe:
                # 保存会话上下文和元数据
                await pipe.set(session_key, context_data)
                await pipe.set(metadata_key, json.dumps(metadata_dict))

                # 设置过期时间
                if self.expiry > 0:
                    await pipe.expire(session_key, self.expiry)
                    await pipe.expire(metadata_key, self.expiry)

                # 更新索引
                owner_key = self._get_owner_index_key(session.metadata.owner_id)
                await pipe.sadd(owner_key, session.id)

                # 更新标签索引
                for tag in session.metadata.tags:
                    tag_key = self._get_tag_index_key(tag)
                    await pipe.sadd(tag_key, session.id)

                # 更新状态索引
                status_key = self._get_status_index_key(session.metadata.status)
                await pipe.sadd(status_key, session.id)

                # 执行事务
                await pipe.execute()

            logger.debug(f"已保存会话 {session.id} 到Redis")
            return True
        except Exception as e:
            logger.error(f"保存会话 {session.id} 到Redis失败: {e}")
            return False

    async def load_session(self, session_id: str) -> Optional[Session]:
        """
        从Redis加载会话

        Args:
            session_id: 会话ID

        Returns:
            Optional[Session]: 会话对象，如果不存在则返回None
        """
        await self.connect()

        session_key = self._get_session_key(session_id)
        metadata_key = self._get_metadata_key(session_id)

        try:
            # 并行获取会话数据和元数据
            context_data, metadata_data = await self.redis.mget(session_key, metadata_key)

            if not context_data or not metadata_data:
                logger.warning(f"会话 {session_id} 不存在或数据不完整")
                return None

            # 解析元数据
            metadata_dict = json.loads(metadata_data)

            # 创建元数据对象
            metadata = SessionMetadata(
                created_at=datetime.fromisoformat(metadata_dict["created_at"]),
                last_accessed_at=datetime.fromisoformat(metadata_dict["last_accessed_at"]),
                expires_at=datetime.fromisoformat(metadata_dict["expires_at"]) if metadata_dict["expires_at"] else None,
                status=metadata_dict["status"],
                tags=metadata_dict["tags"],
                properties=metadata_dict["properties"],
                message_count=metadata_dict["message_count"],
                token_count=metadata_dict["token_count"],
                turn_count=metadata_dict["turn_count"],
                owner_id=metadata_dict["owner_id"],
                shared_with=metadata_dict["shared_with"],
                is_public=metadata_dict["is_public"],
            )

            # 反序列化上下文
            context = SimpleContext.deserialize(context_data)

            # 创建会话对象
            session = Session(
                id=session_id,
                context=context,
                metadata=metadata
            )

            # 更新最后访问时间
            session.metadata.update_last_accessed()
            await self.update_metadata(session_id, {
                "last_accessed_at": session.metadata.last_accessed_at.isoformat()
            })

            return session

        except Exception as e:
            logger.error(f"加载会话 {session_id} 失败: {e}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """
        从Redis删除会话

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否删除成功
        """
        await self.connect()

        try:
            # 首先获取会话信息，以便从索引中删除
            session = await self.load_session(session_id)
            if not session:
                logger.warning(f"要删除的会话 {session_id} 不存在")
                return False

            # 准备要删除的键
            session_key = self._get_session_key(session_id)
            metadata_key = self._get_metadata_key(session_id)

            # 开始事务
            async with self.redis.pipeline(transaction=True) as pipe:
                # 从所有者索引中删除
                owner_key = self._get_owner_index_key(session.metadata.owner_id)
                await pipe.srem(owner_key, session_id)

                # 从标签索引中删除
                for tag in session.metadata.tags:
                    tag_key = self._get_tag_index_key(tag)
                    await pipe.srem(tag_key, session_id)

                # 从状态索引中删除
                status_key = self._get_status_index_key(session.metadata.status)
                await pipe.srem(status_key, session_id)

                # 删除会话数据
                await pipe.delete(session_key, metadata_key)

                # 执行事务
                await pipe.execute()

            logger.info(f"已删除会话 {session_id}")
            return True
        except Exception as e:
            logger.error(f"删除会话 {session_id} 失败: {e}")
            return False

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
        await self.connect()

        try:
            # 收集所有条件匹配的会话ID集合
            session_sets = []

            # 如果指定了所有者ID，获取该所有者的所有会话
            if owner_id:
                owner_key = self._get_owner_index_key(owner_id)
                owner_sessions = await self.redis.smembers(owner_key)
                if owner_sessions:
                    session_sets.append(set(owner_sessions))
                else:
                    # 如果所有者没有会话，直接返回空列表
                    return []

            # 如果指定了状态，获取该状态的所有会话
            if status:
                status_key = self._get_status_index_key(status)
                status_sessions = await self.redis.smembers(status_key)
                if status_sessions:
                    session_sets.append(set(status_sessions))
                else:
                    # 如果没有指定状态的会话，直接返回空列表
                    return []

            # 如果指定了标签，获取包含这些标签的所有会话
            if tags:
                for tag in tags:
                    tag_key = self._get_tag_index_key(tag)
                    tag_sessions = await self.redis.smembers(tag_key)
                    if tag_sessions:
                        session_sets.append(set(tag_sessions))
                    else:
                        # 如果没有指定标签的会话，直接返回空列表
                        return []

            # 如果没有指定任何条件，获取所有会话
            # 这里可以通过扫描会话键模式来实现，但效率不高，可以考虑维护一个全局会话ID集合
            if not session_sets:
                # 使用扫描获取所有会话键
                all_sessions = set()
                cursor = 0
                pattern = f"{self.prefix}*:metadata"
                while True:
                    cursor, keys = await self.redis.scan(cursor, match=pattern, count=1000)
                    if keys:
                        # 从元数据键中提取会话ID
                        session_ids = [key.replace(f"{self.prefix}", "").replace(":metadata", "") for key in keys]
                        all_sessions.update(session_ids)
                    if cursor == 0:
                        break

                if all_sessions:
                    session_sets.append(all_sessions)
                else:
                    # 如果没有任何会话，直接返回空列表
                    return []

            # 计算所有条件的交集
            if len(session_sets) > 1:
                matched_ids = set.intersection(*session_sets)
            elif len(session_sets) == 1:
                matched_ids = session_sets[0]
            else:
                matched_ids = set()

            # 应用分页
            matched_ids = list(matched_ids)
            matched_ids.sort()  # 排序以确保结果一致性
            paged_ids = matched_ids[offset:offset + limit]

            # 加载会话对象
            sessions = []
            for session_id in paged_ids:
                session = await self.load_session(session_id)
                if session:
                    sessions.append(session)

            return sessions
        except Exception as e:
            logger.error(f"列出会话失败: {e}")
            return []

    async def update_metadata(self, session_id: str, metadata_updates: Dict[str, Any]) -> bool:
        """
        更新会话元数据

        Args:
            session_id: 会话ID
            metadata_updates: 要更新的元数据字段和值

        Returns:
            bool: 是否更新成功
        """
        await self.connect()

        try:
            # 加载当前元数据
            metadata_key = self._get_metadata_key(session_id)
            metadata_data = await self.redis.get(metadata_key)

            if not metadata_data:
                logger.warning(f"要更新的会话 {session_id} 不存在")
                return False

            # 解析元数据
            metadata_dict = json.loads(metadata_data)

            # 更新元数据字段
            for key, value in metadata_updates.items():
                metadata_dict[key] = value

            # 保存更新后的元数据
            await self.redis.set(metadata_key, json.dumps(metadata_dict))

            # 如果有过期时间，重新设置
            if self.expiry > 0:
                await self.redis.expire(metadata_key, self.expiry)

                # 也更新会话键的过期时间
                session_key = self._get_session_key(session_id)
                await self.redis.expire(session_key, self.expiry)

            logger.debug(f"已更新会话 {session_id} 的元数据")
            return True
        except Exception as e:
            logger.error(f"更新会话 {session_id} 的元数据失败: {e}")
            return False

    async def clean_expired_sessions(self) -> int:
        """
        清理过期会话，返回清理的会话数量

        Returns:
            int: 清理的会话数量
        """
        await self.connect()

        try:
            # 获取所有会话
            sessions = await self.list_sessions(limit=1000)

            # 检查哪些会话已过期
            now = datetime.now()
            expired_sessions = [
                session for session in sessions
                if session.metadata.expires_at and session.metadata.expires_at < now
            ]

            # 删除过期会话
            for session in expired_sessions:
                await self.delete_session(session.id)

            count = len(expired_sessions)
            if count > 0:
                logger.info(f"已清理 {count} 个过期会话")

            return count
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0

    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取存储统计信息

        Returns:
            Dict[str, Any]: 包含统计信息的字典
        """
        await self.connect()

        try:
            # 获取所有会话数量
            total_sessions = 0
            cursor = 0
            pattern = f"{self.prefix}*:metadata"
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=1000)
                total_sessions += len(keys)
                if cursor == 0:
                    break

            # 获取不同状态的会话数量
            status_counts = {}
            for status in ["active", "paused", "ended"]:
                status_key = self._get_status_index_key(status)
                count = await self.redis.scard(status_key)
                status_counts[status] = count

            # 返回统计信息
            return {
                "total_sessions": total_sessions,
                "status_counts": status_counts,
                "provider": "redis",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取存储统计信息失败: {e}")
            return {
                "error": str(e),
                "provider": "redis",
                "timestamp": datetime.now().isoformat()
            }