"""
服务模块 - 提供各种功能服务

该模块提供了系统各种功能性服务，包括代理协作服务、会话管理服务等。
"""

# 导入并导出代理协作服务
from agent_cores.services.agent_cooperation_service import (
    agent_cooperation_service,
    AgentCooperationService
)

# 导出所有组件
__all__ = [
    # 代理协作服务
    'agent_cooperation_service',
    'AgentCooperationService'
] 