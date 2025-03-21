"""
企业连接器模块

这个模块提供了一组标准化的连接器，用于将智能体平台的能力暴露给外部系统。
支持多种连接方式，包括HTTP REST API、HTTP+SSE、WebSocket等。
"""

__version__ = "0.1.0"

from .base_connector import BaseConnector, ConnectorResponse
from .http_connector import HTTPConnector
from .sse_connector import SSEConnector
from .connector_factory import ConnectorFactory, connector_factory

__all__ = [
    "BaseConnector",
    "ConnectorResponse",
    "HTTPConnector", 
    "SSEConnector",
    "ConnectorFactory",
    "connector_factory"
] 