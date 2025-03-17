"""
会话模型定义 - 定义会话的数据结构和相关操作
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


@dataclass
class SessionMetadata:
    """
    会话元数据模型，用于存储会话相关的元信息

    包含会话的创建时间、最后访问时间、过期时间、状态、标签等信息，
    以及访问控制相关的所有者和共享用户信息。
    """
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: str = "active"  # active, paused, ended
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

    # 会话使用统计
    message_count: int = 0
    token_count: int = 0
    turn_count: int = 0

    # 访问控制
    owner_id: str = ""
    shared_with: List[str] = field(default_factory=list)
    is_public: bool = False

    def update_last_accessed(self):
        """更新最后访问时间"""
        self.last_accessed_at = datetime.now()

    def increment_counters(self, messages=0, tokens=0, turns=0):
        """增加计数器值"""
        self.message_count += messages
        self.token_count += tokens
        self.turn_count += turns


@dataclass
class Session:
    """
    会话模型，包含会话的完整信息

    一个会话包含一个SimpleContext实例和会话元数据。
    每个会话有一个唯一的ID，用于标识和检索。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: Any = None  # SimpleContext实例
    metadata: SessionMetadata = field(default_factory=SessionMetadata)

    def is_expired(self) -> bool:
        """检查会话是否已过期"""
        if not self.metadata.expires_at:
            return False
        return datetime.now() > self.metadata.expires_at

    def can_access(self, user_id: str) -> bool:
        """检查用户是否可以访问此会话"""
        if self.metadata.is_public:
            return True
        if self.metadata.owner_id == user_id:
            return True
        return user_id in self.metadata.shared_with