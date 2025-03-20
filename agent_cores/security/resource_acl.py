"""
资源访问控制列表（ACL）管理模块 - 实现对特定资源的细粒度访问控制
"""
import time
import logging
import json
import os
from typing import Dict, List, Optional, Set, Any, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from enum import Enum

# 配置日志
logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """资源类型枚举"""
    AGENT = "agent"
    MODEL = "model"
    TOOL = "tool"
    DATASET = "dataset"
    FILE = "file"
    WORKSPACE = "workspace"
    PROJECT = "project"
    TEAM = "team"
    CUSTOM = "custom"

class AccessLevel(Enum):
    """访问级别枚举"""
    NONE = 0  # 无访问权限
    READ = 1  # 只读权限
    WRITE = 2  # 读写权限
    OWNER = 3  # 所有者权限
    ADMIN = 4  # 管理员权限

@dataclass
class ResourceACLEntry:
    """资源ACL条目"""
    # 基本信息
    entry_id: str  # 条目ID
    resource_type: ResourceType  # 资源类型
    resource_id: str  # 资源ID
    
    # 权限控制
    owner_id: str  # 资源所有者ID
    access_level_default: AccessLevel = AccessLevel.NONE  # 默认访问级别
    access_level_users: Dict[str, AccessLevel] = field(default_factory=dict)  # 用户访问级别
    access_level_teams: Dict[str, AccessLevel] = field(default_factory=dict)  # 团队访问级别
    
    # 公共访问控制
    is_public: bool = False  # 是否公开访问
    public_access_level: AccessLevel = AccessLevel.READ  # 公开访问级别
    
    # 其他元数据
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据

class ResourceACLManager:
    """资源ACL管理器"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化资源ACL管理器
        
        Args:
            storage_dir: 存储目录路径，如果为None则使用默认路径
        """
        # 线程锁，确保线程安全
        self.lock = Lock()
        
        # 存储ACL条目
        self.acl_entries: Dict[str, ResourceACLEntry] = {}
        
        # 资源映射，用于快速查找资源的ACL条目
        # {resource_type -> {resource_id -> entry_id}}
        self.resource_map: Dict[ResourceType, Dict[str, str]] = {
            resource_type: {} for resource_type in ResourceType
        }
        
        # 确定存储目录
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            # 默认存储在项目根目录下的data/security/acl目录
            project_root = Path(__file__).parent.parent.parent.parent
            self.storage_dir = project_root / "data" / "security" / "acl"
        
        # 确保目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 存储文件路径
        self.acl_file = self.storage_dir / "resource_acl.json"
        
        # 加载数据
        self._load_data()
        
        logger.info(f"资源ACL管理器初始化，已加载 {len(self.acl_entries)} 个ACL条目")
    
    def _load_data(self):
        """从文件加载数据"""
        if not self.acl_file.exists():
            return
        
        try:
            with open(self.acl_file, 'r', encoding='utf-8') as f:
                acl_data = json.load(f)
                for entry_data in acl_data:
                    # 处理枚举类型
                    resource_type = ResourceType(entry_data["resource_type"])
                    access_level_default = AccessLevel(entry_data["access_level_default"])
                    
                    # 处理用户访问级别字典
                    access_level_users = {}
                    for user_id, level in entry_data.get("access_level_users", {}).items():
                        access_level_users[user_id] = AccessLevel(level)
                    
                    # 处理团队访问级别字典
                    access_level_teams = {}
                    for team_id, level in entry_data.get("access_level_teams", {}).items():
                        access_level_teams[team_id] = AccessLevel(level)
                    
                    public_access_level = AccessLevel(entry_data.get("public_access_level", AccessLevel.READ.value))
                    
                    entry = ResourceACLEntry(
                        entry_id=entry_data["entry_id"],
                        resource_type=resource_type,
                        resource_id=entry_data["resource_id"],
                        owner_id=entry_data["owner_id"],
                        access_level_default=access_level_default,
                        access_level_users=access_level_users,
                        access_level_teams=access_level_teams,
                        is_public=entry_data.get("is_public", False),
                        public_access_level=public_access_level,
                        created_at=entry_data.get("created_at", time.time()),
                        updated_at=entry_data.get("updated_at", time.time()),
                        metadata=entry_data.get("metadata", {})
                    )
                    
                    # 存储ACL条目
                    self.acl_entries[entry.entry_id] = entry
                    
                    # 更新资源映射
                    self.resource_map[entry.resource_type][entry.resource_id] = entry.entry_id
                
            logger.info(f"从 {self.acl_file} 加载了 {len(self.acl_entries)} 个ACL条目")
        except Exception as e:
            logger.error(f"加载ACL数据失败: {e}")
    
    def _save_data(self):
        """保存数据到文件"""
        try:
            with self.lock:
                acl_data = []
                for entry in self.acl_entries.values():
                    # 处理枚举类型
                    access_level_users = {user_id: level.value for user_id, level in entry.access_level_users.items()}
                    access_level_teams = {team_id: level.value for team_id, level in entry.access_level_teams.items()}
                    
                    entry_data = {
                        "entry_id": entry.entry_id,
                        "resource_type": entry.resource_type.value,
                        "resource_id": entry.resource_id,
                        "owner_id": entry.owner_id,
                        "access_level_default": entry.access_level_default.value,
                        "access_level_users": access_level_users,
                        "access_level_teams": access_level_teams,
                        "is_public": entry.is_public,
                        "public_access_level": entry.public_access_level.value,
                        "created_at": entry.created_at,
                        "updated_at": entry.updated_at,
                        "metadata": entry.metadata
                    }
                    acl_data.append(entry_data)
                
                with open(self.acl_file, 'w', encoding='utf-8') as f:
                    json.dump(acl_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已保存 {len(self.acl_entries)} 个ACL条目到 {self.acl_file}")
        except Exception as e:
            logger.error(f"保存ACL数据失败: {e}")

# 创建全局资源ACL管理器实例
acl_manager = ResourceACLManager() 