"""
用户权限委派模块 - 允许第三方平台为自己的用户创建差异化权限
"""
import time
import logging
import json
import os
import uuid
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class DelegationRule:
    """权限委派规则"""
    rule_id: str
    platform_id: str  # 第三方平台ID
    name: str = ""
    description: str = ""
    delegated_permissions: List[str] = field(default_factory=list)  # 可以委派的权限
    max_delegation_depth: int = 1  # 最大委派深度
    require_approval: bool = False  # 是否需要管理员批准
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    created_by: Optional[str] = None

@dataclass
class PermissionGrant:
    """权限授予记录"""
    grant_id: str
    platform_id: str  # 第三方平台ID
    user_id: str  # 用户ID
    granted_permissions: List[str] = field(default_factory=list)  # 授予的权限
    rule_id: Optional[str] = None  # 委派规则ID
    is_active: bool = True
    expires_at: Optional[float] = None  # 过期时间，如果为None则永不过期
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    created_by: Optional[str] = None  # 创建者ID
    approved_by: Optional[str] = None  # 批准者ID

class PermissionDelegator:
    """权限委派器 - 管理用户权限委派"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化权限委派器
        
        Args:
            storage_dir: 存储目录路径，如果为None则使用默认路径
        """
        # 线程锁，确保线程安全
        self.lock = Lock()
        
        # 存储委派规则
        self.rules: Dict[str, DelegationRule] = {}
        
        # 存储权限授予记录
        self.grants: Dict[str, PermissionGrant] = {}
        
        # 确定存储目录
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            # 默认存储在项目根目录下的data/security/delegation目录
            project_root = Path(__file__).parent.parent.parent.parent
            self.storage_dir = project_root / "data" / "security" / "delegation"
        
        # 确保目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 存储文件路径
        self.rules_file = self.storage_dir / "delegation_rules.json"
        self.grants_file = self.storage_dir / "permission_grants.json"
        
        # 加载数据
        self._load_data()
        
        # 初始化默认规则
        if not self.rules:
            self._initialize_default_rules()
        
        logger.info(f"权限委派器初始化，已加载 {len(self.rules)} 条委派规则和 {len(self.grants)} 条权限授予记录")
    
    def _initialize_default_rules(self):
        """初始化默认委派规则"""
        default_rules = [
            # 平台管理员委派规则
            DelegationRule(
                rule_id="platform_admin_delegate",
                platform_id="*",
                name="平台管理员委派",
                description="允许平台管理员委派任意权限",
                delegated_permissions=["*"],
                max_delegation_depth=3,
                require_approval=False
            ),
            
            # 内容创建者委派规则
            DelegationRule(
                rule_id="content_creator_delegate",
                platform_id="*",
                name="内容创建者委派",
                description="允许内容创建者委派内容相关权限",
                delegated_permissions=[
                    "content.read",
                    "content.write",
                    "content.publish"
                ],
                max_delegation_depth=1,
                require_approval=False
            ),
            
            # 团队管理者委派规则
            DelegationRule(
                rule_id="team_manager_delegate",
                platform_id="*",
                name="团队管理者委派",
                description="允许团队管理者委派团队相关权限",
                delegated_permissions=[
                    "team.view",
                    "team.edit",
                    "team.invite"
                ],
                max_delegation_depth=2,
                require_approval=True
            )
        ]
        
        # 添加默认规则
        for rule in default_rules:
            self.rules[rule.rule_id] = rule
        
        # 保存规则
        self._save_rules()
    
    def _load_data(self):
        """从文件加载数据"""
        # 加载委派规则
        if self.rules_file.exists():
            try:
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                    for rule_data in rules_data:
                        rule = DelegationRule(
                            rule_id=rule_data["rule_id"],
                            platform_id=rule_data["platform_id"],
                            name=rule_data.get("name", ""),
                            description=rule_data.get("description", ""),
                            delegated_permissions=rule_data.get("delegated_permissions", []),
                            max_delegation_depth=rule_data.get("max_delegation_depth", 1),
                            require_approval=rule_data.get("require_approval", False),
                            is_active=rule_data.get("is_active", True),
                            created_at=rule_data.get("created_at", time.time()),
                            updated_at=rule_data.get("updated_at", time.time()),
                            created_by=rule_data.get("created_by")
                        )
                        self.rules[rule.rule_id] = rule
                logger.info(f"从 {self.rules_file} 加载了 {len(self.rules)} 条委派规则")
            except Exception as e:
                logger.error(f"加载委派规则失败: {e}")
        
        # 加载权限授予记录
        if self.grants_file.exists():
            try:
                with open(self.grants_file, 'r', encoding='utf-8') as f:
                    grants_data = json.load(f)
                    for grant_data in grants_data:
                        grant = PermissionGrant(
                            grant_id=grant_data["grant_id"],
                            platform_id=grant_data["platform_id"],
                            user_id=grant_data["user_id"],
                            granted_permissions=grant_data.get("granted_permissions", []),
                            rule_id=grant_data.get("rule_id"),
                            is_active=grant_data.get("is_active", True),
                            expires_at=grant_data.get("expires_at"),
                            created_at=grant_data.get("created_at", time.time()),
                            updated_at=grant_data.get("updated_at", time.time()),
                            created_by=grant_data.get("created_by"),
                            approved_by=grant_data.get("approved_by")
                        )
                        self.grants[grant.grant_id] = grant
                logger.info(f"从 {self.grants_file} 加载了 {len(self.grants)} 条权限授予记录")
            except Exception as e:
                logger.error(f"加载权限授予记录失败: {e}")
    
    def _save_rules(self):
        """保存委派规则到文件"""
        try:
            with self.lock:
                rules_data = []
                for rule in self.rules.values():
                    rules_data.append({
                        "rule_id": rule.rule_id,
                        "platform_id": rule.platform_id,
                        "name": rule.name,
                        "description": rule.description,
                        "delegated_permissions": rule.delegated_permissions,
                        "max_delegation_depth": rule.max_delegation_depth,
                        "require_approval": rule.require_approval,
                        "is_active": rule.is_active,
                        "created_at": rule.created_at,
                        "updated_at": rule.updated_at,
                        "created_by": rule.created_by
                    })
                
                with open(self.rules_file, 'w', encoding='utf-8') as f:
                    json.dump(rules_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已保存 {len(self.rules)} 条委派规则到 {self.rules_file}")
        except Exception as e:
            logger.error(f"保存委派规则失败: {e}")
    
    def _save_grants(self):
        """保存权限授予记录到文件"""
        try:
            with self.lock:
                grants_data = []
                for grant in self.grants.values():
                    grants_data.append({
                        "grant_id": grant.grant_id,
                        "platform_id": grant.platform_id,
                        "user_id": grant.user_id,
                        "granted_permissions": grant.granted_permissions,
                        "rule_id": grant.rule_id,
                        "is_active": grant.is_active,
                        "expires_at": grant.expires_at,
                        "created_at": grant.created_at,
                        "updated_at": grant.updated_at,
                        "created_by": grant.created_by,
                        "approved_by": grant.approved_by
                    })
                
                with open(self.grants_file, 'w', encoding='utf-8') as f:
                    json.dump(grants_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"已保存 {len(self.grants)} 条权限授予记录到 {self.grants_file}")
        except Exception as e:
            logger.error(f"保存权限授予记录失败: {e}")
    
    def create_rule(self, 
                   platform_id: str,
                   name: str,
                   delegated_permissions: List[str],
                   description: str = "",
                   max_delegation_depth: int = 1,
                   require_approval: bool = False,
                   created_by: Optional[str] = None) -> Optional[str]:
        """
        创建委派规则
        
        Args:
            platform_id: 第三方平台ID
            name: 规则名称
            delegated_permissions: 可委派的权限列表
            description: 规则描述
            max_delegation_depth: 最大委派深度
            require_approval: 是否需要管理员批准
            created_by: 创建者ID
            
        Returns:
            规则ID，如果创建失败则返回None
        """
        with self.lock:
            rule_id = f"rule_{uuid.uuid4().hex[:8]}"
            
            rule = DelegationRule(
                rule_id=rule_id,
                platform_id=platform_id,
                name=name,
                description=description,
                delegated_permissions=delegated_permissions,
                max_delegation_depth=max_delegation_depth,
                require_approval=require_approval,
                created_by=created_by
            )
            
            self.rules[rule_id] = rule
            self._save_rules()
            
            logger.info(f"创建委派规则: {rule_id}, 平台: {platform_id}")
            return rule_id
    
    def update_rule(self, 
                   rule_id: str,
                   platform_id: Optional[str] = None,
                   name: Optional[str] = None,
                   description: Optional[str] = None,
                   delegated_permissions: Optional[List[str]] = None,
                   max_delegation_depth: Optional[int] = None,
                   require_approval: Optional[bool] = None,
                   is_active: Optional[bool] = None) -> bool:
        """
        更新委派规则
        
        Args:
            rule_id: 规则ID
            platform_id: 第三方平台ID
            name: 规则名称
            description: 规则描述
            delegated_permissions: 可委派的权限列表
            max_delegation_depth: 最大委派深度
            require_approval: 是否需要管理员批准
            is_active: 是否激活
            
        Returns:
            是否成功更新
        """
        with self.lock:
            if rule_id not in self.rules:
                logger.warning(f"委派规则不存在: {rule_id}")
                return False
            
            rule = self.rules[rule_id]
            
            if platform_id is not None:
                rule.platform_id = platform_id
            if name is not None:
                rule.name = name
            if description is not None:
                rule.description = description
            if delegated_permissions is not None:
                rule.delegated_permissions = delegated_permissions
            if max_delegation_depth is not None:
                rule.max_delegation_depth = max_delegation_depth
            if require_approval is not None:
                rule.require_approval = require_approval
            if is_active is not None:
                rule.is_active = is_active
            
            rule.updated_at = time.time()
            
            self._save_rules()
            
            logger.info(f"更新委派规则: {rule_id}")
            return True
    
    def delete_rule(self, rule_id: str) -> bool:
        """
        删除委派规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否成功删除
        """
        with self.lock:
            if rule_id not in self.rules:
                logger.warning(f"委派规则不存在: {rule_id}")
                return False
            
            # 从内存中删除
            del self.rules[rule_id]
            
            # 删除依赖此规则的权限授予记录
            for grant_id, grant in list(self.grants.items()):
                if grant.rule_id == rule_id:
                    del self.grants[grant_id]
            
            # 保存
            self._save_rules()
            self._save_grants()
            
            logger.info(f"删除委派规则: {rule_id}")
            return True
    
    def list_rules(self, 
                  platform_id: Optional[str] = None,
                  active_only: bool = True) -> List[DelegationRule]:
        """
        列出委派规则
        
        Args:
            platform_id: 第三方平台ID过滤
            active_only: 是否只返回激活的规则
            
        Returns:
            委派规则列表
        """
        with self.lock:
            result = []
            
            for rule in self.rules.values():
                # 活动状态过滤
                if active_only and not rule.is_active:
                    continue
                
                # 平台ID过滤
                if platform_id and rule.platform_id != "*" and rule.platform_id != platform_id:
                    continue
                
                result.append(rule)
            
            return result
    
    def get_rule(self, rule_id: str) -> Optional[DelegationRule]:
        """
        获取委派规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            委派规则，如果不存在则返回None
        """
        return self.rules.get(rule_id)
    
    def delegate_permissions(self,
                            platform_id: str,
                            user_id: str,
                            permissions: List[str],
                            rule_id: Optional[str] = None,
                            expires_in_days: Optional[int] = None,
                            delegated_by: Optional[str] = None) -> Optional[str]:
        """
        委派权限给用户
        
        Args:
            platform_id: 第三方平台ID
            user_id: 用户ID
            permissions: 要委派的权限列表
            rule_id: 委派规则ID
            expires_in_days: 过期天数，如果为None则永不过期
            delegated_by: 委派者ID
            
        Returns:
            授权ID，如果委派失败则返回None
        """
        with self.lock:
            # 验证委派规则
            if rule_id:
                rule = self.rules.get(rule_id)
                if not rule:
                    logger.warning(f"委派规则不存在: {rule_id}")
                    return None
                
                # 检查规则是否适用于该平台
                if rule.platform_id != "*" and rule.platform_id != platform_id:
                    logger.warning(f"委派规则 {rule_id} 不适用于平台 {platform_id}")
                    return None
                
                # 检查规则是否激活
                if not rule.is_active:
                    logger.warning(f"委派规则 {rule_id} 未激活")
                    return None
                
                # 验证权限是否在规则允许的范围内
                if "*" not in rule.delegated_permissions:
                    for permission in permissions:
                        allowed = False
                        for allowed_perm in rule.delegated_permissions:
                            # 完全匹配
                            if permission == allowed_perm:
                                allowed = True
                                break
                            # 通配符匹配
                            if allowed_perm.endswith(".*") and permission.startswith(allowed_perm[:-1]):
                                allowed = True
                                break
                        
                        if not allowed:
                            logger.warning(f"权限 {permission} 不在规则 {rule_id} 允许的范围内")
                            return None
            
            # 创建授权记录
            grant_id = f"grant_{uuid.uuid4().hex[:8]}"
            
            # 计算过期时间
            expires_at = None
            if expires_in_days is not None:
                expires_at = time.time() + expires_in_days * 86400
            
            grant = PermissionGrant(
                grant_id=grant_id,
                platform_id=platform_id,
                user_id=user_id,
                granted_permissions=permissions,
                rule_id=rule_id,
                expires_at=expires_at,
                created_by=delegated_by
            )
            
            # 如果规则需要批准，标记为非活动状态
            if rule_id and self.rules[rule_id].require_approval:
                grant.is_active = False
            
            self.grants[grant_id] = grant
            self._save_grants()
            
            logger.info(f"委派权限: {grant_id}, 平台: {platform_id}, 用户: {user_id}, 权限: {permissions}")
            return grant_id
    
    def approve_grant(self, grant_id: str, approved_by: str) -> bool:
        """
        批准权限授予
        
        Args:
            grant_id: 授权ID
            approved_by: 批准者ID
            
        Returns:
            是否成功批准
        """
        with self.lock:
            if grant_id not in self.grants:
                logger.warning(f"权限授予记录不存在: {grant_id}")
                return False
            
            grant = self.grants[grant_id]
            
            # 检查是否需要批准
            if grant.rule_id and self.rules.get(grant.rule_id) and not self.rules[grant.rule_id].require_approval:
                logger.warning(f"权限授予 {grant_id} 不需要批准")
                return False
            
            # 激活授权
            grant.is_active = True
            grant.approved_by = approved_by
            grant.updated_at = time.time()
            
            self._save_grants()
            
            logger.info(f"批准权限授予: {grant_id}, 批准者: {approved_by}")
            return True
    
    def revoke_grant(self, grant_id: str) -> bool:
        """
        撤销权限授予
        
        Args:
            grant_id: 授权ID
            
        Returns:
            是否成功撤销
        """
        with self.lock:
            if grant_id not in self.grants:
                logger.warning(f"权限授予记录不存在: {grant_id}")
                return False
            
            # 从内存中删除
            del self.grants[grant_id]
            
            # 保存
            self._save_grants()
            
            logger.info(f"撤销权限授予: {grant_id}")
            return True
    
    def list_grants(self,
                   platform_id: Optional[str] = None,
                   user_id: Optional[str] = None,
                   rule_id: Optional[str] = None,
                   active_only: bool = True) -> List[PermissionGrant]:
        """
        列出权限授予记录
        
        Args:
            platform_id: 第三方平台ID过滤
            user_id: 用户ID过滤
            rule_id: 规则ID过滤
            active_only: 是否只返回激活的记录
            
        Returns:
            权限授予记录列表
        """
        with self.lock:
            result = []
            
            for grant in self.grants.values():
                # 活动状态过滤
                if active_only and not grant.is_active:
                    continue
                
                # 平台ID过滤
                if platform_id and grant.platform_id != platform_id:
                    continue
                
                # 用户ID过滤
                if user_id and grant.user_id != user_id:
                    continue
                
                # 规则ID过滤
                if rule_id and grant.rule_id != rule_id:
                    continue
                
                result.append(grant)
            
            return result
    
    def get_grant(self, grant_id: str) -> Optional[PermissionGrant]:
        """
        获取权限授予记录
        
        Args:
            grant_id: 授权ID
            
        Returns:
            权限授予记录，如果不存在则返回None
        """
        return self.grants.get(grant_id)
    
    def get_user_permissions(self, platform_id: str, user_id: str) -> List[str]:
        """
        获取用户的所有委派权限
        
        Args:
            platform_id: 第三方平台ID
            user_id: 用户ID
            
        Returns:
            权限列表
        """
        with self.lock:
            permissions = set()
            
            now = time.time()
            
            for grant in self.grants.values():
                if grant.platform_id != platform_id or grant.user_id != user_id:
                    continue
                
                if not grant.is_active:
                    continue
                
                if grant.expires_at and grant.expires_at < now:
                    continue
                
                permissions.update(grant.granted_permissions)
            
            return sorted(list(permissions))
    
    def check_permission(self, platform_id: str, user_id: str, permission: str) -> bool:
        """
        检查用户是否具有特定权限
        
        Args:
            platform_id: 第三方平台ID
            user_id: 用户ID
            permission: 权限名称
            
        Returns:
            是否具有权限
        """
        user_permissions = self.get_user_permissions(platform_id, user_id)
        
        # 检查完全匹配
        if permission in user_permissions:
            return True
        
        # 检查通配符匹配
        for perm in user_permissions:
            if perm == "*":
                return True
            
            if perm.endswith(".*") and permission.startswith(perm[:-1]):
                return True
        
        return False
    
    def clean_expired_grants(self) -> int:
        """
        清理过期的权限授予记录
        
        Returns:
            清理的记录数量
        """
        with self.lock:
            count = 0
            now = time.time()
            
            to_delete = []
            
            for grant_id, grant in self.grants.items():
                if grant.expires_at and grant.expires_at < now:
                    to_delete.append(grant_id)
                    count += 1
            
            for grant_id in to_delete:
                del self.grants[grant_id]
            
            if count > 0:
                self._save_grants()
                logger.info(f"清理 {count} 条过期的权限授予记录")
            
            return count

# 创建全局权限委派器实例
permission_delegator = PermissionDelegator() 