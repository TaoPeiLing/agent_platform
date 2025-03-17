"""
代理核心层 - 包含代理工厂、仓库、配置加载和生命周期管理等核心组件
"""

from .factory import (
    AgentFactory,
    agent_factory
)

from .template_manager import template_manager

from .runtime import (
    SessionContext,
    RuntimeService,
    runtime_service
)

__all__ = [
    # 工厂相关
    'AgentFactory',
    'agent_factory',
    'template_manager',
    # 会话管理
    'SessionContext',
    # 代理执行
    'RuntimeService',
    'runtime_service'
]