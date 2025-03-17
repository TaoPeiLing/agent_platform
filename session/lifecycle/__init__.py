"""
会话生命周期管理模块 - 负责会话的创建、过期和清理

提供会话生命周期的管理功能，包括创建会话、检查过期、清理过期会话等。
"""

from .lifecycle_manager import LifecycleManager

__all__ = ["LifecycleManager"] 