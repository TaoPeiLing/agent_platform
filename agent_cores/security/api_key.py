"""
API密钥管理模块

提供API密钥的全生命周期管理，包括创建、验证、撤销和轮换。
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

from agent_cores.security.models import APIKey, APIKeyResponse, APIKeyInfo, KeyStatus, AuthResult, ServiceAccount
from agent_cores.security.utils import (
    generate_api_key, format_api_key, split_api_key, 
    hash_secret, verify_secret, calculate_expiry, is_key_expired, generate_random_string
)

# 配置日志
logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    API密钥管理器
    
    提供API密钥的创建、验证、撤销和轮换等功能。
    """
    
    def __init__(self, 
                 storage_dir: Optional[str] = None,
                 default_expiry_days: int = 90,
                 key_prefix_length: int = 8,
                 key_secret_length: int = 32):
        """
        初始化API密钥管理器
        
        Args:
            storage_dir: 密钥存储目录，默认为项目根目录下的data/security/keys
            default_expiry_days: 默认的密钥有效期（天数）
            key_prefix_length: 密钥前缀长度
            key_secret_length: 密钥主体长度
        """
        if storage_dir is None:
            # 默认存储在项目根目录下的data/security/keys
            project_root = Path(__file__).parent.parent.parent.parent
            storage_dir = os.path.join(project_root, "data", "security", "keys")
            
        self.storage_dir = storage_dir
        self.default_expiry_days = default_expiry_days
        self.key_prefix_length = key_prefix_length
        self.key_secret_length = key_secret_length
        self.api_keys: Dict[str, APIKey] = {}  # 前缀到密钥的映射
        self.service_accounts: Dict[str, ServiceAccount] = {}  # 服务账户ID到服务账户的映射
        
        # 确保存储目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 加载已存在的密钥和服务账户
        self._load_data()
        
        logger.info(f"API密钥管理器已初始化，存储目录: {self.storage_dir}")
    
    def _get_keys_file_path(self) -> str:
        """获取API密钥存储文件路径"""
        return os.path.join(self.storage_dir, "api_keys.json")
    
    def _get_service_accounts_file_path(self) -> str:
        """获取服务账户存储文件路径"""
        return os.path.join(self.storage_dir, "service_accounts.json")
    
    def _load_data(self) -> None:
        """加载存储的密钥和服务账户数据"""
        # 加载API密钥
        keys_file = self._get_keys_file_path()
        if os.path.exists(keys_file):
            try:
                with open(keys_file, "r", encoding="utf-8") as f:
                    keys_data = json.load(f)
                    
                for key_data in keys_data:
                    key = APIKey(
                        id=key_data["id"],
                        prefix=key_data["prefix"],
                        secret_hash=key_data["secret_hash"],
                        service_account_id=key_data["service_account_id"],
                        description=key_data["description"],
                        permissions=key_data.get("permissions", []),
                        created_at=datetime.fromisoformat(key_data["created_at"]),
                        expires_at=datetime.fromisoformat(key_data["expires_at"]) if key_data.get("expires_at") else None,
                        last_used_at=datetime.fromisoformat(key_data["last_used_at"]) if key_data.get("last_used_at") else None,
                        status=KeyStatus(key_data["status"]),
                        metadata=key_data.get("metadata", {})
                    )
                    self.api_keys[key.prefix] = key
                    
                logger.info(f"已加载 {len(self.api_keys)} 个API密钥")
            except Exception as e:
                logger.error(f"加载API密钥数据失败: {str(e)}")
        
        # 加载服务账户
        service_accounts_file = self._get_service_accounts_file_path()
        if os.path.exists(service_accounts_file):
            try:
                with open(service_accounts_file, "r", encoding="utf-8") as f:
                    service_accounts_data = json.load(f)
                    
                for account_data in service_accounts_data:
                    account = ServiceAccount(
                        id=account_data["id"],
                        name=account_data["name"],
                        description=account_data["description"],
                        owner_id=account_data.get("owner_id"),
                        roles=account_data.get("roles", []),
                        permissions=account_data.get("permissions", []),
                        created_at=datetime.fromisoformat(account_data["created_at"]),
                        metadata=account_data.get("metadata", {}),
                        is_active=account_data.get("is_active", True)
                    )
                    self.service_accounts[account.id] = account
                    
                logger.info(f"已加载 {len(self.service_accounts)} 个服务账户")
            except Exception as e:
                logger.error(f"加载服务账户数据失败: {str(e)}")
    
    def _save_data(self) -> None:
        """保存密钥和服务账户数据到文件"""
        # 保存API密钥
        keys_file = self._get_keys_file_path()
        try:
            keys_data = []
            for key in self.api_keys.values():
                key_data = {
                    "id": key.id,
                    "prefix": key.prefix,
                    "secret_hash": key.secret_hash,
                    "service_account_id": key.service_account_id,
                    "description": key.description,
                    "permissions": key.permissions,
                    "created_at": key.created_at.isoformat(),
                    "status": key.status.value
                }
                
                if key.expires_at:
                    key_data["expires_at"] = key.expires_at.isoformat()
                    
                if key.last_used_at:
                    key_data["last_used_at"] = key.last_used_at.isoformat()
                    
                if key.metadata:
                    key_data["metadata"] = key.metadata
                    
                keys_data.append(key_data)
                
            with open(keys_file, "w", encoding="utf-8") as f:
                json.dump(keys_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"已保存 {len(keys_data)} 个API密钥到 {keys_file}")
        except Exception as e:
            logger.error(f"保存API密钥数据失败: {str(e)}")
        
        # 保存服务账户
        service_accounts_file = self._get_service_accounts_file_path()
        try:
            accounts_data = []
            for account in self.service_accounts.values():
                account_data = {
                    "id": account.id,
                    "name": account.name,
                    "description": account.description,
                    "roles": account.roles,
                    "permissions": account.permissions,
                    "created_at": account.created_at.isoformat(),
                    "is_active": account.is_active
                }
                
                if account.owner_id:
                    account_data["owner_id"] = account.owner_id
                    
                if account.metadata:
                    account_data["metadata"] = account.metadata
                    
                accounts_data.append(account_data)
                
            with open(service_accounts_file, "w", encoding="utf-8") as f:
                json.dump(accounts_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"已保存 {len(accounts_data)} 个服务账户到 {service_accounts_file}")
        except Exception as e:
            logger.error(f"保存服务账户数据失败: {str(e)}")
    
    def create_service_account(self, 
                               name: str, 
                               description: str, 
                               owner_id: Optional[str] = None,
                               roles: Optional[List[str]] = None,
                               permissions: Optional[List[str]] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> ServiceAccount:
        """
        创建服务账户
        
        Args:
            name: 服务账户名称
            description: 描述
            owner_id: 所有者ID
            roles: 角色列表
            permissions: 权限列表
            metadata: 元数据
            
        Returns:
            创建的服务账户
        """
        account = ServiceAccount(
            name=name,
            description=description,
            owner_id=owner_id,
            roles=roles or [],
            permissions=permissions or [],
            metadata=metadata or {}
        )
        
        self.service_accounts[account.id] = account
        self._save_data()
        
        logger.info(f"已创建服务账户: {account.name} (ID: {account.id})")
        return account
    
    def get_service_account(self, account_id: str) -> Optional[ServiceAccount]:
        """
        获取服务账户
        
        Args:
            account_id: 服务账户ID
            
        Returns:
            服务账户，如果不存在则返回None
        """
        return self.service_accounts.get(account_id)
    
    def list_service_accounts(self, 
                              owner_id: Optional[str] = None,
                              include_inactive: bool = False) -> List[ServiceAccount]:
        """
        列出服务账户
        
        Args:
            owner_id: 如果提供，仅返回该所有者的服务账户
            include_inactive: 是否包含非活跃账户
            
        Returns:
            服务账户列表
        """
        accounts = []
        for account in self.service_accounts.values():
            if not include_inactive and not account.is_active:
                continue
                
            if owner_id and account.owner_id != owner_id:
                continue
                
            accounts.append(account)
            
        return accounts
    
    def update_service_account(self,
                               account_id: str,
                               name: Optional[str] = None,
                               description: Optional[str] = None,
                               roles: Optional[List[str]] = None,
                               permissions: Optional[List[str]] = None,
                               metadata: Optional[Dict[str, Any]] = None,
                               is_active: Optional[bool] = None) -> Optional[ServiceAccount]:
        """
        更新服务账户
        
        Args:
            account_id: 服务账户ID
            name: 新名称
            description: 新描述
            roles: 新角色列表
            permissions: 新权限列表
            metadata: 新元数据
            is_active: 是否活跃
            
        Returns:
            更新后的服务账户，如果不存在则返回None
        """
        account = self.get_service_account(account_id)
        if not account:
            return None
            
        if name is not None:
            account.name = name
            
        if description is not None:
            account.description = description
            
        if roles is not None:
            account.roles = roles
            
        if permissions is not None:
            account.permissions = permissions
            
        if metadata is not None:
            account.metadata = metadata
            
        if is_active is not None:
            account.is_active = is_active
            
        self._save_data()
        
        logger.info(f"已更新服务账户: {account.name} (ID: {account.id})")
        return account
    
    def delete_service_account(self, account_id: str) -> bool:
        """
        删除服务账户
        
        Args:
            account_id: 服务账户ID
            
        Returns:
            是否成功删除
        """
        if account_id not in self.service_accounts:
            return False
            
        # 删除该账户的所有API密钥
        keys_to_remove = []
        for key in self.api_keys.values():
            if key.service_account_id == account_id:
                keys_to_remove.append(key.prefix)
                
        for prefix in keys_to_remove:
            self.api_keys.pop(prefix, None)
            
        # 删除服务账户
        account = self.service_accounts.pop(account_id)
        self._save_data()
        
        logger.info(f"已删除服务账户: {account.name} (ID: {account.id})，同时删除了 {len(keys_to_remove)} 个关联的API密钥")
        return True
    
    def create_api_key(self,
                       service_account_id: str,
                       description: str,
                       expires_in_days: Optional[int] = None,
                       permissions: Optional[List[str]] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Optional[APIKeyResponse]:
        """
        创建API密钥
        
        Args:
            service_account_id: 服务账户ID
            description: 密钥用途描述
            expires_in_days: 有效期天数，None表示使用默认值(self.default_expiry_days)
            permissions: 权限列表，None表示继承服务账户权限
            metadata: 元数据
            
        Returns:
            API密钥响应，包含完整密钥（仅返回一次）
            如果服务账户不存在，则返回None
        """
        # 验证服务账户
        service_account = self.get_service_account(service_account_id)
        if not service_account:
            logger.error(f"创建API密钥失败: 服务账户不存在 (ID: {service_account_id})")
            return None
            
        if not service_account.is_active:
            logger.error(f"创建API密钥失败: 服务账户已禁用 (ID: {service_account_id})")
            return None
            
        # 生成密钥
        prefix = generate_random_string(self.key_prefix_length)
        secret = generate_random_string(self.key_secret_length)
        full_key = format_api_key(prefix, secret)
        
        # 计算过期时间
        expires_at = calculate_expiry(expires_in_days or self.default_expiry_days)
        
        # 使用继承的权限或指定的权限
        key_permissions = permissions if permissions is not None else service_account.permissions.copy()
        
        # 创建API密钥
        api_key = APIKey(
            prefix=prefix,
            secret_hash=hash_secret(secret),
            service_account_id=service_account_id,
            description=description,
            permissions=key_permissions,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        # 存储密钥
        self.api_keys[prefix] = api_key
        self._save_data()
        
        logger.info(f"已创建API密钥: {prefix}*** (服务账户: {service_account.name}, ID: {service_account_id})")
        
        # 创建响应
        response = APIKeyResponse(
            id=api_key.id,
            prefix=prefix,
            full_key=full_key,
            service_account_id=service_account_id,
            description=description,
            permissions=key_permissions,
            created_at=api_key.created_at,
            expires_at=expires_at
        )
        
        return response
    
    def verify_api_key(self, api_key_str: str) -> AuthResult:
        """
        验证API密钥
        
        Args:
            api_key_str: API密钥字符串
            
        Returns:
            认证结果
        """
        try:
            # 分割密钥
            prefix, secret = split_api_key(api_key_str)
            
            # 查找密钥
            api_key = self.api_keys.get(prefix)
            if not api_key:
                logger.warning(f"API密钥验证失败: 密钥不存在 (前缀: {prefix})")
                return AuthResult(
                    success=False,
                    error="无效的API密钥",
                    auth_type="api_key"
                )
                
            # 检查密钥状态
            if api_key.status != KeyStatus.ACTIVE:
                logger.warning(f"API密钥验证失败: 密钥已{api_key.status.value} (前缀: {prefix})")
                return AuthResult(
                    success=False,
                    error=f"API密钥已{api_key.status.value}",
                    auth_type="api_key"
                )
                
            # 检查过期时间
            if api_key.expires_at and api_key.expires_at < datetime.now():
                # 自动将状态更新为过期
                api_key.status = KeyStatus.EXPIRED
                self._save_data()
                
                logger.warning(f"API密钥验证失败: 密钥已过期 (前缀: {prefix})")
                return AuthResult(
                    success=False,
                    error="API密钥已过期",
                    auth_type="api_key"
                )
                
            # 验证密钥
            if not verify_secret(secret, api_key.secret_hash):
                logger.warning(f"API密钥验证失败: 密钥不匹配 (前缀: {prefix})")
                return AuthResult(
                    success=False,
                    error="无效的API密钥",
                    auth_type="api_key"
                )
                
            # 更新最后使用时间
            api_key.last_used_at = datetime.now()
            self._save_data()
            
            # 获取服务账户以及关联的角色
            service_account = self.get_service_account(api_key.service_account_id)
            if not service_account:
                logger.error(f"API密钥验证成功，但服务账户不存在 (ID: {api_key.service_account_id})")
                return AuthResult(
                    success=False,
                    error="服务账户不存在",
                    auth_type="api_key"
                )
                
            if not service_account.is_active:
                logger.warning(f"API密钥验证失败: 服务账户已禁用 (ID: {api_key.service_account_id})")
                return AuthResult(
                    success=False,
                    error="服务账户已禁用",
                    auth_type="api_key"
                )
                
            # 验证成功
            logger.info(f"API密钥验证成功: {prefix}*** (服务账户: {service_account.name})")
            
            # 填充认证结果
            result = AuthResult(
                success=True,
                subject_id=service_account.id,
                auth_type="api_key",
                roles=service_account.roles,
                permissions=api_key.permissions,  # 使用密钥上的权限
                metadata={
                    "service_account": {
                        "id": service_account.id,
                        "name": service_account.name
                    },
                    "api_key": {
                        "id": api_key.id,
                        "prefix": api_key.prefix,
                        "description": api_key.description
                    }
                }
            )
            
            return result
            
        except ValueError as e:
            # 密钥格式无效
            logger.warning(f"API密钥验证失败: {str(e)}")
            return AuthResult(
                success=False,
                error=str(e),
                auth_type="api_key"
            )
        except Exception as e:
            # 其他错误
            logger.error(f"API密钥验证发生错误: {str(e)}")
            return AuthResult(
                success=False,
                error="验证过程发生错误",
                auth_type="api_key"
            )
    
    def revoke_api_key(self, key_prefix: str) -> bool:
        """
        撤销API密钥
        
        Args:
            key_prefix: 密钥前缀
            
        Returns:
            是否成功撤销
        """
        api_key = self.api_keys.get(key_prefix)
        if not api_key:
            logger.warning(f"撤销API密钥失败: 密钥不存在 (前缀: {key_prefix})")
            return False
            
        # 设置状态为已撤销
        api_key.status = KeyStatus.REVOKED
        self._save_data()
        
        logger.info(f"已撤销API密钥: {key_prefix}*** (描述: {api_key.description})")
        return True
    
    def rotate_api_key(self,
                       old_key_prefix: str,
                       new_description: Optional[str] = None,
                       expires_in_days: Optional[int] = None,
                       permissions: Optional[List[str]] = None) -> Optional[APIKeyResponse]:
        """
        轮换API密钥
        
        创建新密钥并撤销旧密钥。
        
        Args:
            old_key_prefix: 旧密钥前缀
            new_description: 新密钥描述，默认使用旧密钥的描述
            expires_in_days: 新密钥有效期天数，None表示使用默认值(self.default_expiry_days)
            permissions: 新密钥权限列表，默认继承旧密钥的权限
            
        Returns:
            新API密钥响应，如果旧密钥不存在则返回None
        """
        # 获取旧密钥
        old_key = self.api_keys.get(old_key_prefix)
        if not old_key:
            logger.warning(f"轮换API密钥失败: 旧密钥不存在 (前缀: {old_key_prefix})")
            return None
            
        # 使用旧密钥的描述或提供的新描述
        description = new_description or old_key.description
        
        # 使用旧密钥的权限或提供的新权限
        key_permissions = permissions if permissions is not None else old_key.permissions.copy()
        
        # 创建新密钥
        new_key_response = self.create_api_key(
            service_account_id=old_key.service_account_id,
            description=f"{description} (轮换于 {datetime.now().strftime('%Y-%m-%d')})",
            expires_in_days=expires_in_days,
            permissions=key_permissions,
            metadata=old_key.metadata.copy()
        )
        
        if not new_key_response:
            logger.error(f"轮换API密钥失败: 创建新密钥时出错 (旧密钥前缀: {old_key_prefix})")
            return None
            
        # 撤销旧密钥
        self.revoke_api_key(old_key_prefix)
        
        logger.info(f"已轮换API密钥: 旧前缀 {old_key_prefix}*** -> 新前缀 {new_key_response.prefix}***")
        return new_key_response
    
    def list_api_keys(self,
                      service_account_id: Optional[str] = None,
                      include_revoked: bool = False,
                      include_expired: bool = False) -> List[APIKeyInfo]:
        """
        列出API密钥
        
        Args:
            service_account_id: 如果提供，仅返回该服务账户的密钥
            include_revoked: 是否包含已撤销的密钥
            include_expired: 是否包含已过期的密钥
            
        Returns:
            API密钥信息列表（不含密钥机密部分）
        """
        key_infos = []
        
        for key in self.api_keys.values():
            # 过滤服务账户
            if service_account_id and key.service_account_id != service_account_id:
                continue
                
            # 过滤已撤销的密钥
            if not include_revoked and key.status == KeyStatus.REVOKED:
                continue
                
            # 过滤已过期的密钥
            if not include_expired and key.status == KeyStatus.EXPIRED:
                continue
                
            # 检查是否过期但尚未标记为过期
            if key.status == KeyStatus.ACTIVE and key.expires_at and key.expires_at < datetime.now():
                key.status = KeyStatus.EXPIRED
                self._save_data()
                
                if not include_expired:
                    continue
            
            # 创建密钥信息
            key_info = APIKeyInfo(
                id=key.id,
                prefix=key.prefix,
                service_account_id=key.service_account_id,
                description=key.description,
                permissions=key.permissions,
                created_at=key.created_at,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                status=key.status,
                metadata=key.metadata
            )
            
            key_infos.append(key_info)
            
        return key_infos
    
    def get_key_by_prefix(self, prefix: str) -> Optional[APIKeyInfo]:
        """
        根据前缀获取密钥信息
        
        Args:
            prefix: 密钥前缀
            
        Returns:
            API密钥信息，如果不存在则返回None
        """
        key = self.api_keys.get(prefix)
        if not key:
            return None
            
        # 检查是否过期但尚未标记为过期
        if key.status == KeyStatus.ACTIVE and key.expires_at and key.expires_at < datetime.now():
            key.status = KeyStatus.EXPIRED
            self._save_data()
            
        # 创建密钥信息
        key_info = APIKeyInfo(
            id=key.id,
            prefix=key.prefix,
            service_account_id=key.service_account_id,
            description=key.description,
            permissions=key.permissions,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            status=key.status,
            metadata=key.metadata
        )
        
        return key_info
    
    def clear_expired_keys(self) -> int:
        """
        清理已过期的密钥
        
        将所有过期的密钥标记为已过期状态。
        
        Returns:
            已清理的密钥数量
        """
        count = 0
        now = datetime.now()
        
        for key in self.api_keys.values():
            if key.status == KeyStatus.ACTIVE and key.expires_at and key.expires_at < now:
                key.status = KeyStatus.EXPIRED
                count += 1
                
        if count > 0:
            self._save_data()
            logger.info(f"已清理 {count} 个过期的API密钥")
            
        return count
    
    def get_usage_report(self, 
                         days: int = 30,
                         service_account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取密钥使用报告
        
        Args:
            days: 报告天数
            service_account_id: 如果提供，仅报告该服务账户的密钥
            
        Returns:
            使用报告
        """
        report_start = datetime.now() - timedelta(days=days)
        
        # 统计信息
        total_keys = 0
        active_keys = 0
        expired_keys = 0
        revoked_keys = 0
        unused_keys = 0
        recently_used_keys = 0
        expiring_soon_keys = 0
        
        # 各服务账户的密钥统计
        account_stats = {}
        
        for key in self.api_keys.values():
            # 过滤服务账户
            if service_account_id and key.service_account_id != service_account_id:
                continue
                
            total_keys += 1
            
            # 按状态统计
            if key.status == KeyStatus.ACTIVE:
                active_keys += 1
            elif key.status == KeyStatus.EXPIRED:
                expired_keys += 1
            elif key.status == KeyStatus.REVOKED:
                revoked_keys += 1
                
            # 未使用的密钥
            if not key.last_used_at:
                unused_keys += 1
            # 最近使用的密钥
            elif key.last_used_at and key.last_used_at >= report_start:
                recently_used_keys += 1
                
            # 即将过期的密钥（7天内）
            if key.status == KeyStatus.ACTIVE and key.expires_at and key.expires_at < (datetime.now() + timedelta(days=7)):
                expiring_soon_keys += 1
                
            # 按服务账户统计
            account_id = key.service_account_id
            if account_id not in account_stats:
                account = self.get_service_account(account_id)
                account_name = account.name if account else "未知服务账户"
                
                account_stats[account_id] = {
                    "id": account_id,
                    "name": account_name,
                    "total_keys": 0,
                    "active_keys": 0,
                    "expired_keys": 0,
                    "revoked_keys": 0,
                    "unused_keys": 0
                }
                
            account_stats[account_id]["total_keys"] += 1
            
            if key.status == KeyStatus.ACTIVE:
                account_stats[account_id]["active_keys"] += 1
            elif key.status == KeyStatus.EXPIRED:
                account_stats[account_id]["expired_keys"] += 1
            elif key.status == KeyStatus.REVOKED:
                account_stats[account_id]["revoked_keys"] += 1
                
            if not key.last_used_at:
                account_stats[account_id]["unused_keys"] += 1
        
        # 组装报告
        report = {
            "report_date": datetime.now().isoformat(),
            "report_period_days": days,
            "total_keys": total_keys,
            "active_keys": active_keys,
            "expired_keys": expired_keys,
            "revoked_keys": revoked_keys,
            "unused_keys": unused_keys,
            "recently_used_keys": recently_used_keys,
            "expiring_soon_keys": expiring_soon_keys,
            "service_accounts": list(account_stats.values())
        }
        
        return report


# 创建全局API密钥管理器实例
api_key_manager = APIKeyManager() 