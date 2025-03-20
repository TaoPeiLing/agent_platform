"""
安全服务模块

集成API密钥管理和JWT认证，提供统一的安全服务接口。
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple

from agent_cores.security.api_key import api_key_manager, APIKeyManager
from agent_cores.security.jwt_auth import jwt_auth_service, JWTAuthService
from agent_cores.security.models import AuthResult, ServiceAccount, APIKeyResponse, APIKeyInfo
from agent_cores.models.rbac import Role

# 配置日志
logger = logging.getLogger(__name__)


class SecurityService:
    """
    安全服务
    
    集成API密钥管理和JWT认证，提供统一的安全服务接口。
    """
    
    def __init__(self, 
                 api_key_manager: APIKeyManager = None,
                 jwt_auth_service: JWTAuthService = None):
        """
        初始化安全服务
        
        Args:
            api_key_manager: API密钥管理器
            jwt_auth_service: JWT认证服务
        """
        self.api_key_manager = api_key_manager or globals()["api_key_manager"]
        self.jwt_auth_service = jwt_auth_service or globals()["jwt_auth_service"]
        
        logger.info("安全服务已初始化")
    
    def authenticate(self, 
                    api_key: Optional[str] = None, 
                    jwt_token: Optional[str] = None) -> AuthResult:
        """
        认证请求
        
        支持API密钥和JWT令牌认证，按优先级尝试认证。
        
        Args:
            api_key: API密钥
            jwt_token: JWT令牌
            
        Returns:
            认证结果
        """
        # 首先尝试API密钥认证
        if api_key:
            auth_result = self.api_key_manager.verify_api_key(api_key)
            if auth_result.success:
                return auth_result
                
        # 然后尝试JWT认证
        if jwt_token:
            auth_result = self.jwt_auth_service.verify_token(jwt_token)
            if auth_result.success:
                return auth_result
                
        # 如果都失败，返回认证失败
        return AuthResult(
            success=False,
            error="认证失败",
            auth_type="none"
        )
    
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
        return self.api_key_manager.create_service_account(
            name=name,
            description=description,
            owner_id=owner_id,
            roles=roles,
            permissions=permissions,
            metadata=metadata
        )
    
    def create_api_key(self,
                      service_account_id: str,
                      description: str,
                      expires_in_days: Optional[int] = 90,
                      permissions: Optional[List[str]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Optional[APIKeyResponse]:
        """
        创建API密钥
        
        Args:
            service_account_id: 服务账户ID
            description: 密钥用途描述
            expires_in_days: 有效期天数，None表示永不过期
            permissions: 权限列表，None表示继承服务账户权限
            metadata: 元数据
            
        Returns:
            API密钥响应，包含完整密钥（仅返回一次）
            如果服务账户不存在，则返回None
        """
        return self.api_key_manager.create_api_key(
            service_account_id=service_account_id,
            description=description,
            expires_in_days=expires_in_days,
            permissions=permissions,
            metadata=metadata
        )
    
    def create_jwt_token_pair(self,
                             subject: str,
                             roles: List[str] = None,
                             permissions: List[str] = None,
                             metadata: Dict[str, Any] = None) -> Dict[str, str]:
        """
        创建JWT令牌对
        
        Args:
            subject: 主题（通常是用户ID或服务账户ID）
            roles: 角色列表
            permissions: 权限列表
            metadata: 元数据
            
        Returns:
            包含访问令牌和刷新令牌的字典
        """
        return self.jwt_auth_service.create_token_pair(
            subject=subject,
            roles=roles,
            permissions=permissions,
            metadata=metadata
        )
    
    def refresh_jwt_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        刷新JWT令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            包含新访问令牌的字典，如果刷新失败则返回None
        """
        return self.jwt_auth_service.refresh_access_token(refresh_token)
    
    def revoke_api_key(self, key_prefix: str) -> bool:
        """
        撤销API密钥
        
        Args:
            key_prefix: 密钥前缀
            
        Returns:
            是否成功撤销
        """
        return self.api_key_manager.revoke_api_key(key_prefix)
    
    def rotate_api_key(self,
                      old_key_prefix: str,
                      new_description: Optional[str] = None,
                      expires_in_days: Optional[int] = 90,
                      permissions: Optional[List[str]] = None) -> Optional[APIKeyResponse]:
        """
        轮换API密钥
        
        创建新密钥并撤销旧密钥。
        
        Args:
            old_key_prefix: 旧密钥前缀
            new_description: 新密钥描述，默认使用旧密钥的描述
            expires_in_days: 新密钥有效期天数
            permissions: 新密钥权限列表，默认继承旧密钥的权限
            
        Returns:
            新API密钥响应，如果旧密钥不存在则返回None
        """
        return self.api_key_manager.rotate_api_key(
            old_key_prefix=old_key_prefix,
            new_description=new_description,
            expires_in_days=expires_in_days,
            permissions=permissions
        )
    
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
        return self.api_key_manager.list_service_accounts(
            owner_id=owner_id,
            include_inactive=include_inactive
        )
    
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
        return self.api_key_manager.list_api_keys(
            service_account_id=service_account_id,
            include_revoked=include_revoked,
            include_expired=include_expired
        )
    
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
        return self.api_key_manager.get_usage_report(
            days=days,
            service_account_id=service_account_id
        )
    
    def clear_expired_keys(self) -> int:
        """
        清理已过期的密钥
        
        将所有过期的密钥标记为已过期状态。
        
        Returns:
            已清理的密钥数量
        """
        return self.api_key_manager.clear_expired_keys()
    
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
        return self.api_key_manager.update_service_account(
            account_id=account_id,
            name=name,
            description=description,
            roles=roles,
            permissions=permissions,
            metadata=metadata,
            is_active=is_active
        )
    
    def delete_service_account(self, account_id: str) -> bool:
        """
        删除服务账户
        
        Args:
            account_id: 服务账户ID
            
        Returns:
            是否成功删除
        """
        return self.api_key_manager.delete_service_account(account_id)
    
    def migrate_legacy_api_keys(self, legacy_keys: Dict[str, Dict[str, Any]]) -> int:
        """
        迁移旧版API密钥
        
        将旧系统的API密钥迁移到新系统。
        
        Args:
            legacy_keys: 旧版API密钥数据
            
        Returns:
            成功迁移的密钥数量
        """
        migrated_count = 0
        
        # 为旧密钥创建一个服务账户
        legacy_account = self.api_key_manager.create_service_account(
            name="Legacy API Keys",
            description="从旧系统迁移的API密钥",
            roles=[Role.USER.value],
            permissions=["legacy_api"],
            metadata={"source": "legacy_migration"}
        )
        
        # 迁移每个密钥
        for key_id, key_data in legacy_keys.items():
            try:
                # 创建新的API密钥记录
                api_key = APIKeyResponse(
                    id=key_id,
                    prefix=key_data.get("prefix", key_id[:8]),
                    full_key=key_data.get("api_key", ""),  # 旧密钥，仅用于日志记录
                    service_account_id=legacy_account.id,
                    description=key_data.get("description", "迁移的旧密钥"),
                    permissions=key_data.get("permissions", ["legacy_api"]),
                    created_at=datetime.fromisoformat(key_data.get("created_at", datetime.now().isoformat())),
                    expires_at=datetime.fromisoformat(key_data.get("expires_at")) if key_data.get("expires_at") else None
                )
                
                # 记录迁移
                logger.info(f"已迁移旧版API密钥: {key_id}")
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"迁移旧版API密钥失败: {key_id}, 错误: {str(e)}")
                
        return migrated_count


# 创建全局安全服务实例
security_service = SecurityService() 