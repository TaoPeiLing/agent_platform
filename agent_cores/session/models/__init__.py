"""
会话模型模块 - 定义会话数据结构和相关模型

此模块提供用于表示会话数据的类，包括会话元数据和会话本身。
"""

from .session import Session, SessionMetadata

__all__ = ["Session", "SessionMetadata"]