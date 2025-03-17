"""
会话访问控制模块 - 负责会话的访问权限管理

提供会话访问权限检查和控制功能，确保用户只能访问自己有权限的会话。
"""

from .access_control import AccessController

__all__ = ["AccessController"] 