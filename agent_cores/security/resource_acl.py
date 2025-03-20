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
            
    def create_acl_entry(self,
                        resource_type: Union[ResourceType, str],
                        resource_id: str,
                        owner_id: str,
                        access_level_default: Union[AccessLevel, int] = AccessLevel.NONE,
                        is_public: bool = False,
                        public_access_level: Union[AccessLevel, int] = AccessLevel.READ,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        创建资源ACL条目
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            owner_id: 资源所有者ID
            access_level_default: 默认访问级别
            is_public: 是否公开访问
            public_access_level: 公开访问级别
            metadata: 额外元数据
            
        Returns:
            ACL条目ID
        """
        with self.lock:
            # 处理枚举类型
            if isinstance(resource_type, str):
                resource_type = ResourceType(resource_type)
            
            if isinstance(access_level_default, int):
                access_level_default = AccessLevel(access_level_default)
            
            if isinstance(public_access_level, int):
                public_access_level = AccessLevel(public_access_level)
            
            # 检查是否已存在
            existing_entry_id = self.resource_map[resource_type].get(resource_id)
            if existing_entry_id:
                logger.warning(f"资源ACL条目已存在: {resource_type.value}/{resource_id}")
                return existing_entry_id
            
            # 生成条目ID
            import uuid
            entry_id = f"acl_{uuid.uuid4().hex[:8]}"
            
            # 创建ACL条目
            entry = ResourceACLEntry(
                entry_id=entry_id,
                resource_type=resource_type,
                resource_id=resource_id,
                owner_id=owner_id,
                access_level_default=access_level_default,
                is_public=is_public,
                public_access_level=public_access_level,
                metadata=metadata or {}
            )
            
            # 添加用户所有者的访问权限
            entry.access_level_users[owner_id] = AccessLevel.OWNER
            
            # 存储ACL条目
            self.acl_entries[entry_id] = entry
            
            # 更新资源映射
            self.resource_map[resource_type][resource_id] = entry_id
            
            # 保存数据
            self._save_data()
            
            logger.info(f"创建资源ACL条目: {entry_id}, 资源: {resource_type.value}/{resource_id}")
            return entry_id
    
    def update_acl_entry(self,
                        entry_id: str,
                        access_level_default: Optional[Union[AccessLevel, int]] = None,
                        is_public: Optional[bool] = None,
                        public_access_level: Optional[Union[AccessLevel, int]] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新资源ACL条目
        
        Args:
            entry_id: ACL条目ID
            access_level_default: 默认访问级别
            is_public: 是否公开访问
            public_access_level: 公开访问级别
            metadata: 额外元数据
            
        Returns:
            是否成功更新
        """
        with self.lock:
            # 检查条目是否存在
            if entry_id not in self.acl_entries:
                logger.warning(f"ACL条目不存在: {entry_id}")
                return False
            
            entry = self.acl_entries[entry_id]
            
            # 更新默认访问级别
            if access_level_default is not None:
                if isinstance(access_level_default, int):
                    access_level_default = AccessLevel(access_level_default)
                entry.access_level_default = access_level_default
            
            # 更新公开访问设置
            if is_public is not None:
                entry.is_public = is_public
            
            # 更新公开访问级别
            if public_access_level is not None:
                if isinstance(public_access_level, int):
                    public_access_level = AccessLevel(public_access_level)
                entry.public_access_level = public_access_level
            
            # 更新元数据
            if metadata is not None:
                entry.metadata.update(metadata)
            
            # 更新时间戳
            entry.updated_at = time.time()
            
            # 保存数据
            self._save_data()
            
            logger.info(f"更新资源ACL条目: {entry_id}")
            return True
    
    def delete_acl_entry(self, entry_id: str) -> bool:
        """
        删除资源ACL条目
        
        Args:
            entry_id: ACL条目ID
            
        Returns:
            是否成功删除
        """
        with self.lock:
            # 检查条目是否存在
            if entry_id not in self.acl_entries:
                logger.warning(f"ACL条目不存在: {entry_id}")
                return False
            
            entry = self.acl_entries[entry_id]
            
            # 从资源映射中删除
            self.resource_map[entry.resource_type].pop(entry.resource_id, None)
            
            # 删除ACL条目
            del self.acl_entries[entry_id]
            
            # 保存数据
            self._save_data()
            
            logger.info(f"删除资源ACL条目: {entry_id}")
            return True
    
    def get_acl_entry(self, entry_id: str) -> Optional[ResourceACLEntry]:
        """
        获取资源ACL条目
        
        Args:
            entry_id: ACL条目ID
            
        Returns:
            ACL条目，如果不存在则返回None
        """
        return self.acl_entries.get(entry_id)
    
    def get_acl_entry_by_resource(self,
                                  resource_type: Union[ResourceType, str],
                                  resource_id: str) -> Optional[ResourceACLEntry]:
        """
        根据资源获取ACL条目
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            
        Returns:
            ACL条目，如果不存在则返回None
        """
        # 处理枚举类型
        if isinstance(resource_type, str):
            resource_type = ResourceType(resource_type)
        
        # 查找条目ID
        entry_id = self.resource_map[resource_type].get(resource_id)
        if not entry_id:
            return None
        
        return self.acl_entries.get(entry_id)
        
    def set_user_access(self,
                       resource_type: Union[ResourceType, str],
                       resource_id: str,
                       user_id: str,
                       access_level: Union[AccessLevel, int]) -> bool:
        """
        设置用户对资源的访问级别
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            user_id: 用户ID
            access_level: 访问级别
            
        Returns:
            是否成功设置
        """
        with self.lock:
            # 处理枚举类型
            if isinstance(resource_type, str):
                resource_type = ResourceType(resource_type)
            
            if isinstance(access_level, int):
                access_level = AccessLevel(access_level)
            
            # 获取ACL条目
            entry = self.get_acl_entry_by_resource(resource_type, resource_id)
            if not entry:
                logger.warning(f"资源ACL条目不存在: {resource_type.value}/{resource_id}")
                return False
            
            # 设置用户访问级别
            entry.access_level_users[user_id] = access_level
            entry.updated_at = time.time()
            
            # 保存数据
            self._save_data()
            
            logger.info(f"设置用户访问级别: {user_id} -> {access_level.name} for {resource_type.value}/{resource_id}")
            return True
    
    def remove_user_access(self,
                         resource_type: Union[ResourceType, str],
                         resource_id: str,
                         user_id: str) -> bool:
        """
        移除用户对资源的访问权限
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            user_id: 用户ID
            
        Returns:
            是否成功移除
        """
        with self.lock:
            # 处理枚举类型
            if isinstance(resource_type, str):
                resource_type = ResourceType(resource_type)
            
            # 获取ACL条目
            entry = self.get_acl_entry_by_resource(resource_type, resource_id)
            if not entry:
                logger.warning(f"资源ACL条目不存在: {resource_type.value}/{resource_id}")
                return False
            
            # 检查是否为所有者
            if entry.owner_id == user_id:
                logger.warning(f"无法移除所有者的访问权限: {user_id} for {resource_type.value}/{resource_id}")
                return False
            
            # 移除用户访问级别
            if user_id in entry.access_level_users:
                del entry.access_level_users[user_id]
                entry.updated_at = time.time()
                
                # 保存数据
                self._save_data()
                
                logger.info(f"移除用户访问权限: {user_id} for {resource_type.value}/{resource_id}")
                return True
            
            return False
    
    def set_team_access(self,
                      resource_type: Union[ResourceType, str],
                      resource_id: str,
                      team_id: str,
                      access_level: Union[AccessLevel, int]) -> bool:
        """
        设置团队对资源的访问级别
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            team_id: 团队ID
            access_level: 访问级别
            
        Returns:
            是否成功设置
        """
        with self.lock:
            # 处理枚举类型
            if isinstance(resource_type, str):
                resource_type = ResourceType(resource_type)
            
            if isinstance(access_level, int):
                access_level = AccessLevel(access_level)
            
            # 获取ACL条目
            entry = self.get_acl_entry_by_resource(resource_type, resource_id)
            if not entry:
                logger.warning(f"资源ACL条目不存在: {resource_type.value}/{resource_id}")
                return False
            
            # 设置团队访问级别
            entry.access_level_teams[team_id] = access_level
            entry.updated_at = time.time()
            
            # 保存数据
            self._save_data()
            
            logger.info(f"设置团队访问级别: {team_id} -> {access_level.name} for {resource_type.value}/{resource_id}")
            return True
    
    def remove_team_access(self,
                         resource_type: Union[ResourceType, str],
                         resource_id: str,
                         team_id: str) -> bool:
        """
        移除团队对资源的访问权限
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            team_id: 团队ID
            
        Returns:
            是否成功移除
        """
        with self.lock:
            # 处理枚举类型
            if isinstance(resource_type, str):
                resource_type = ResourceType(resource_type)
            
            # 获取ACL条目
            entry = self.get_acl_entry_by_resource(resource_type, resource_id)
            if not entry:
                logger.warning(f"资源ACL条目不存在: {resource_type.value}/{resource_id}")
                return False
            
            # 移除团队访问级别
            if team_id in entry.access_level_teams:
                del entry.access_level_teams[team_id]
                entry.updated_at = time.time()
                
                # 保存数据
                self._save_data()
                
                logger.info(f"移除团队访问权限: {team_id} for {resource_type.value}/{resource_id}")
                return True
            
            return False
    
    def get_user_access_level(self,
                             user_id: str,
                             resource_type: Union[ResourceType, str],
                             resource_id: str,
                             team_ids: Optional[List[str]] = None) -> AccessLevel:
        """
        获取用户对资源的访问级别
        
        Args:
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            team_ids: 用户所在的团队ID列表
            
        Returns:
            访问级别
        """
        # 处理枚举类型
        if isinstance(resource_type, str):
            resource_type = ResourceType(resource_type)
        
        # 获取ACL条目
        entry = self.get_acl_entry_by_resource(resource_type, resource_id)
        if not entry:
            return AccessLevel.NONE
        
        # 检查用户是否为所有者
        if entry.owner_id == user_id:
            return AccessLevel.OWNER
        
        # 检查用户直接访问级别
        if user_id in entry.access_level_users:
            return entry.access_level_users[user_id]
        
        # 检查团队访问级别
        if team_ids:
            max_team_level = AccessLevel.NONE
            for team_id in team_ids:
                if team_id in entry.access_level_teams:
                    team_level = entry.access_level_teams[team_id]
                    if team_level.value > max_team_level.value:
                        max_team_level = team_level
            
            if max_team_level != AccessLevel.NONE:
                return max_team_level
        
        # 检查公开访问
        if entry.is_public:
            return entry.public_access_level
        
        # 返回默认访问级别
        return entry.access_level_default
    
    def check_access(self,
                     user_id: str,
                     resource_type: Union[ResourceType, str],
                     resource_id: str,
                     required_level: Union[AccessLevel, int],
                     team_ids: Optional[List[str]] = None) -> bool:
        """
        检查用户是否有足够的访问权限
        
        Args:
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            required_level: 所需的访问级别
            team_ids: 用户所在的团队ID列表
            
        Returns:
            是否有足够的访问权限
        """
        # 处理枚举类型
        if isinstance(required_level, int):
            required_level = AccessLevel(required_level)
        
        # 获取用户访问级别
        user_level = self.get_user_access_level(user_id, resource_type, resource_id, team_ids)
        
        # 检查是否有足够的访问权限
        return user_level.value >= required_level.value
    
    def list_accessible_resources(self,
                                user_id: str,
                                resource_type: Union[ResourceType, str],
                                min_level: Union[AccessLevel, int] = AccessLevel.READ,
                                team_ids: Optional[List[str]] = None) -> List[Tuple[str, AccessLevel]]:
        """
        列出用户可访问的资源
        
        Args:
            user_id: 用户ID
            resource_type: 资源类型
            min_level: 最小访问级别
            team_ids: 用户所在的团队ID列表
            
        Returns:
            可访问的资源ID和访问级别列表
        """
        # 处理枚举类型
        if isinstance(resource_type, str):
            resource_type = ResourceType(resource_type)
        
        if isinstance(min_level, int):
            min_level = AccessLevel(min_level)
        
        result = []
        
        # 遍历资源
        for resource_id in self.resource_map[resource_type]:
            # 获取用户访问级别
            access_level = self.get_user_access_level(user_id, resource_type, resource_id, team_ids)
            
            # 检查是否满足最小访问级别
            if access_level.value >= min_level.value:
                result.append((resource_id, access_level))
        
        return result
    
    def list_resource_users(self,
                          resource_type: Union[ResourceType, str],
                          resource_id: str,
                          min_level: Union[AccessLevel, int] = AccessLevel.READ) -> List[Tuple[str, AccessLevel]]:
        """
        列出可访问资源的用户
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            min_level: 最小访问级别
            
        Returns:
            可访问资源的用户ID和访问级别列表
        """
        # 处理枚举类型
        if isinstance(resource_type, str):
            resource_type = ResourceType(resource_type)
        
        if isinstance(min_level, int):
            min_level = AccessLevel(min_level)
        
        # 获取ACL条目
        entry = self.get_acl_entry_by_resource(resource_type, resource_id)
        if not entry:
            return []
        
        result = []
        
        # 添加所有者
        result.append((entry.owner_id, AccessLevel.OWNER))
        
        # 添加直接访问用户
        for user_id, level in entry.access_level_users.items():
            if user_id != entry.owner_id and level.value >= min_level.value:
                result.append((user_id, level))
        
        return result
    
    def change_owner(self,
                    resource_type: Union[ResourceType, str],
                    resource_id: str,
                    new_owner_id: str) -> bool:
        """
        更改资源所有者
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            new_owner_id: 新所有者ID
            
        Returns:
            是否成功更改
        """
        with self.lock:
            # 处理枚举类型
            if isinstance(resource_type, str):
                resource_type = ResourceType(resource_type)
            
            # 获取ACL条目
            entry = self.get_acl_entry_by_resource(resource_type, resource_id)
            if not entry:
                logger.warning(f"资源ACL条目不存在: {resource_type.value}/{resource_id}")
                return False
            
            # 更改所有者
            old_owner_id = entry.owner_id
            entry.owner_id = new_owner_id
            
            # 更新访问级别
            if old_owner_id in entry.access_level_users:
                # 保持旧所有者的高级访问权限
                entry.access_level_users[old_owner_id] = AccessLevel.ADMIN
            
            # 确保新所有者有所有者权限
            entry.access_level_users[new_owner_id] = AccessLevel.OWNER
            
            entry.updated_at = time.time()
            
            # 保存数据
            self._save_data()
            
            logger.info(f"更改资源所有者: {old_owner_id} -> {new_owner_id} for {resource_type.value}/{resource_id}")
            return True
    
    def copy_acl(self,
               source_type: Union[ResourceType, str],
               source_id: str,
               target_type: Union[ResourceType, str],
               target_id: str,
               new_owner_id: Optional[str] = None) -> bool:
        """
        复制ACL设置
        
        Args:
            source_type: 源资源类型
            source_id: 源资源ID
            target_type: 目标资源类型
            target_id: 目标资源ID
            new_owner_id: 新所有者ID，如果为None则使用源资源的所有者
            
        Returns:
            是否成功复制
        """
        with self.lock:
            # 处理枚举类型
            if isinstance(source_type, str):
                source_type = ResourceType(source_type)
            
            if isinstance(target_type, str):
                target_type = ResourceType(target_type)
            
            # 获取源ACL条目
            source_entry = self.get_acl_entry_by_resource(source_type, source_id)
            if not source_entry:
                logger.warning(f"源资源ACL条目不存在: {source_type.value}/{source_id}")
                return False
            
            # 检查目标ACL条目是否已存在
            target_entry = self.get_acl_entry_by_resource(target_type, target_id)
            if target_entry:
                logger.warning(f"目标资源ACL条目已存在: {target_type.value}/{target_id}")
                return False
            
            # 确定所有者
            owner_id = new_owner_id or source_entry.owner_id
            
            # 创建目标ACL条目
            import uuid
            entry_id = f"acl_{uuid.uuid4().hex[:8]}"
            
            # 复制ACL设置
            target_entry = ResourceACLEntry(
                entry_id=entry_id,
                resource_type=target_type,
                resource_id=target_id,
                owner_id=owner_id,
                access_level_default=source_entry.access_level_default,
                is_public=source_entry.is_public,
                public_access_level=source_entry.public_access_level,
                metadata=source_entry.metadata.copy()
            )
            
            # 复制用户访问级别
            for user_id, level in source_entry.access_level_users.items():
                if user_id != source_entry.owner_id:
                    target_entry.access_level_users[user_id] = level
            
            # 确保新所有者有所有者权限
            target_entry.access_level_users[owner_id] = AccessLevel.OWNER
            
            # 复制团队访问级别
            for team_id, level in source_entry.access_level_teams.items():
                target_entry.access_level_teams[team_id] = level
            
            # 存储ACL条目
            self.acl_entries[entry_id] = target_entry
            
            # 更新资源映射
            self.resource_map[target_type][target_id] = entry_id
            
            # 保存数据
            self._save_data()
            
            logger.info(f"复制ACL设置: {source_type.value}/{source_id} -> {target_type.value}/{target_id}")
            return True

# 创建全局资源ACL管理器实例
acl_manager = ResourceACLManager() 