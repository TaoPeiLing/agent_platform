"""
会话存储模块 - 提供会话持久化的存储后端

此模块定义了存储接口和不同的存储实现，如Redis和数据库存储。
使用工厂模式创建存储实例，隐藏实现细节。
"""

from .base import StorageProvider
from .redis_provider import RedisStorageProvider
from .factory import StorageFactory

__all__ = ["StorageProvider", "RedisStorageProvider", "StorageFactory"]