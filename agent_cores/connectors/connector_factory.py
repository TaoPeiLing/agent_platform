"""
企业连接器工厂

用于创建和管理不同类型的企业连接器。
"""

import logging
from typing import Dict, Any, Optional, Type, List, Union

from .base_connector import BaseConnector
from .http_connector import HTTPConnector
from .sse_connector import SSEConnector

# 配置日志
logger = logging.getLogger(__name__)


class ConnectorFactory:
    """企业连接器工厂类"""
    
    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        self._connector_types: Dict[str, Type[BaseConnector]] = {
            "http": HTTPConnector,
            "sse": SSEConnector
        }
        
    def register_connector_type(self, name: str, connector_class: Type[BaseConnector]):
        """注册新的连接器类型"""
        self._connector_types[name] = connector_class
        logger.info(f"已注册连接器类型: {name}")
        
    def create_connector(self, connector_type: str, config: Optional[Dict[str, Any]] = None) -> BaseConnector:
        """
        创建指定类型的连接器
        
        Args:
            connector_type: 连接器类型名称
            config: 连接器配置
            
        Returns:
            创建的连接器实例
            
        Raises:
            ValueError: 如果指定的连接器类型不存在
        """
        if connector_type not in self._connector_types:
            raise ValueError(f"未知的连接器类型: {connector_type}")
            
        config = config or {}
        
        # 创建连接器实例
        connector_class = self._connector_types[connector_type]
        connector = connector_class()
        
        # 初始化连接器
        if not connector.initialize(config):
            raise RuntimeError(f"连接器初始化失败: {connector_type}")
            
        # 保存连接器实例
        self._connectors[connector_type] = connector
        
        logger.info(f"已创建连接器: {connector_type}")
        return connector
        
    def get_connector(self, connector_type: str) -> BaseConnector:
        """
        获取指定类型的连接器
        
        如果连接器不存在，则先创建
        
        Args:
            connector_type: 连接器类型名称
            
        Returns:
            连接器实例
        """
        if connector_type not in self._connectors:
            return self.create_connector(connector_type)
            
        return self._connectors[connector_type]
        
    def get_all_connectors(self) -> List[BaseConnector]:
        """
        获取所有已创建的连接器
        
        Returns:
            连接器实例列表
        """
        return list(self._connectors.values())
        
    def get_connector_types(self) -> List[str]:
        """
        获取所有已注册的连接器类型
        
        Returns:
            连接器类型名称列表
        """
        return list(self._connector_types.keys())


# 全局连接器工厂实例
connector_factory = ConnectorFactory() 