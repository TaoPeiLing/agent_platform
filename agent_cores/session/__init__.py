"""
会话管理模块 - 提供高性能可扩展的会话持久化和管理服务

该模块旨在为业务系统提供一套统一的会话管理机制，包括：
1. 会话的持久化存储和检索
2. 会话访问控制
3. 会话生命周期管理
4. 会话上下文的处理

模块的架构设计采用模块化方式，各组件之间通过接口解耦，易于扩展和维护。
"""

import logging
from typing import Optional

from .session_manager import SessionManager
from .context_bridge import SessionContextBridge, get_session_context_bridge, get_session_manager

__all__ = [
    "SessionManager",
    "get_session_manager",
    "SessionContextBridge",
    "get_session_context_bridge"
]