"""
存储工厂 - 负责创建不同类型的存储提供者
"""

import logging
from typing import Optional, Dict, Type

from .base import StorageProvider
from .redis_provider import RedisStorageProvider

logger = logging.getLogger(__name__)


class StorageFactory:
    """
    存储工厂类，负责创建不同类型的存储提供者

    使用工厂模式隐藏存储实现细节，使上层代码与具体存储实现解耦。
    支持通过配置动态切换存储后端。
    """

    # 存储提供者注册表
    _providers: Dict[str, Type[StorageProvider]] = {
        "redis": RedisStorageProvider,
        # 可以在此添加更多存储提供者
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[StorageProvider]) -> None:
        """
        注册新的存储提供者

        Args:
            name: 存储提供者名称
            provider_class: 存储提供者类
        """
        cls._providers[name] = provider_class
        logger.info(f"已注册存储提供者: {name}")

    @classmethod
    def create(cls, provider_type: str, **kwargs) -> Optional[StorageProvider]:
        """
        创建存储提供者实例

        Args:
            provider_type: 存储提供者类型名称
            **kwargs: 传递给存储提供者构造函数的参数

        Returns:
            StorageProvider: 存储提供者实例

        Raises:
            ValueError: 如果指定的存储提供者类型不存在
        """
        provider_class = cls._providers.get(provider_type)
        if not provider_class:
            available = ", ".join(cls._providers.keys())
            logger.error(f"未知的存储提供者类型: {provider_type}，可用类型: {available}")
            raise ValueError(f"未知的存储提供者类型: {provider_type}，可用类型: {available}")

        try:
            provider = provider_class(**kwargs)
            logger.info(f"已创建存储提供者: {provider_type}")
            return provider
        except Exception as e:
            logger.error(f"创建存储提供者 {provider_type} 失败: {e}")
            raise