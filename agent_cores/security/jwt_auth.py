"""
JWT认证模块

提供JWT令牌的生成、验证和刷新功能。
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

import jwt
from jwt.exceptions import PyJWTError

from agent_cores.security.models import JWTTokenData, AuthResult

# 配置日志
logger = logging.getLogger(__name__)

# JWT配置常量
DEFAULT_TOKEN_EXPIRE_MINUTES = 30  # 访问令牌默认过期时间（分钟）
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7  # 刷新令牌默认过期时间（天）
DEFAULT_ALGORITHM = "HS256"  # 默认签名算法
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


class JWTAuthService:
    """
    JWT认证服务
    
    提供JWT令牌的生成、验证和刷新功能。
    """
    
    def __init__(self, 
                 secret_key: Optional[str] = None,
                 algorithm: str = DEFAULT_ALGORITHM,
                 access_token_expire_minutes: int = DEFAULT_TOKEN_EXPIRE_MINUTES,
                 refresh_token_expire_days: int = DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS):
        """
        初始化JWT认证服务
        
        Args:
            secret_key: JWT签名密钥，默认从环境变量或配置文件获取
            algorithm: JWT签名算法
            access_token_expire_minutes: 访问令牌过期时间（分钟）
            refresh_token_expire_days: 刷新令牌过期时间（天）
        """
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        # 设置签名密钥
        if secret_key:
            self.secret_key = secret_key
        else:
            # 尝试从环境变量获取
            self.secret_key = os.getenv("JWT_SECRET_KEY")
            
            # 如果环境变量不存在，尝试从配置文件获取
            if not self.secret_key:
                try:
                    # 尝试从项目根目录的配置文件加载
                    project_root = Path(__file__).parent.parent.parent.parent
                    config_path = os.path.join(project_root, ".env")
                    
                    if os.path.exists(config_path):
                        with open(config_path, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.strip().startswith("JWT_SECRET_KEY="):
                                    self.secret_key = line.strip().split("=", 1)[1].strip()
                                    # 移除引号
                                    if self.secret_key.startswith('"') and self.secret_key.endswith('"'):
                                        self.secret_key = self.secret_key[1:-1]
                                    break
                except Exception as e:
                    logger.warning(f"从配置文件加载JWT密钥时出错: {str(e)}")
            
            # 如果仍然没有密钥，生成一个警告并使用临时密钥
            if not self.secret_key:
                import secrets
                self.secret_key = secrets.token_hex(32)
                logger.warning("未设置JWT_SECRET_KEY，使用临时生成的密钥。请在生产环境中设置固定密钥！")
        
        logger.info(f"JWT认证服务已初始化，使用算法: {self.algorithm}")
    
    def _create_token(self, 
                     data: Dict[str, Any], 
                     expires_delta: Optional[timedelta] = None,
                     token_type: str = TOKEN_TYPE_ACCESS) -> str:
        """
        创建JWT令牌
        
        Args:
            data: 令牌数据
            expires_delta: 过期时间增量，None表示使用默认值
            token_type: 令牌类型，"access"或"refresh"
            
        Returns:
            JWT令牌字符串
        """
        if expires_delta is None:
            if token_type == TOKEN_TYPE_ACCESS:
                expires_delta = timedelta(minutes=self.access_token_expire_minutes)
            else:
                expires_delta = timedelta(days=self.refresh_token_expire_days)
                
        # 复制数据，避免修改原始数据
        payload = data.copy()
        
        # 设置过期时间
        expire = datetime.utcnow() + expires_delta
        payload.update({"exp": expire, "type": token_type})
        
        # 生成令牌
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_access_token(self, 
                           subject: str, 
                           roles: List[str] = None,
                           permissions: List[str] = None,
                           metadata: Dict[str, Any] = None,
                           expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        
        Args:
            subject: 主题（通常是用户ID或服务账户ID）
            roles: 角色列表
            permissions: 权限列表
            metadata: 元数据
            expires_delta: 过期时间增量，None表示使用默认值
            
        Returns:
            JWT访问令牌
        """
        data = {
            "sub": subject,
            "iss": "sss_agent_platform",
            "iat": datetime.utcnow(),
        }
        
        if roles:
            data["roles"] = roles
            
        if permissions:
            data["permissions"] = permissions
            
        if metadata:
            data["metadata"] = metadata
            
        return self._create_token(data, expires_delta, TOKEN_TYPE_ACCESS)
    
    def create_refresh_token(self, 
                            subject: str,
                            metadata: Dict[str, Any] = None,
                            expires_delta: Optional[timedelta] = None) -> str:
        """
        创建刷新令牌
        
        Args:
            subject: 主题（通常是用户ID或服务账户ID）
            metadata: 元数据
            expires_delta: 过期时间增量，None表示使用默认值
            
        Returns:
            JWT刷新令牌
        """
        data = {
            "sub": subject,
            "iss": "sss_agent_platform",
            "iat": datetime.utcnow(),
        }
        
        if metadata:
            data["metadata"] = metadata
            
        return self._create_token(data, expires_delta, TOKEN_TYPE_REFRESH)
    
    def create_token_pair(self,
                         subject: str,
                         roles: List[str] = None,
                         permissions: List[str] = None,
                         metadata: Dict[str, Any] = None) -> Dict[str, str]:
        """
        创建令牌对（访问令牌和刷新令牌）
        
        Args:
            subject: 主题（通常是用户ID或服务账户ID）
            roles: 角色列表
            permissions: 权限列表
            metadata: 元数据
            
        Returns:
            包含访问令牌和刷新令牌的字典
        """
        access_token = self.create_access_token(
            subject=subject,
            roles=roles,
            permissions=permissions,
            metadata=metadata
        )
        
        refresh_token = self.create_refresh_token(
            subject=subject,
            metadata=metadata
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        解码JWT令牌
        
        Args:
            token: JWT令牌字符串
            
        Returns:
            解码后的令牌数据，如果解码失败则返回None
        """
        try:
            # 解码令牌
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except PyJWTError as e:
            logger.warning(f"JWT令牌解码失败: {str(e)}")
            return None
    
    def verify_token(self, token: str, token_type: str = TOKEN_TYPE_ACCESS) -> AuthResult:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌字符串
            token_type: 令牌类型，"access"或"refresh"
            
        Returns:
            认证结果
        """
        try:
            # 解码令牌
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get("type") != token_type:
                logger.warning(f"JWT令牌类型不匹配，期望: {token_type}，实际: {payload.get('type')}")
                return AuthResult(
                    success=False,
                    error=f"无效的令牌类型，期望: {token_type}",
                    auth_type="jwt"
                )
            
            # 检查令牌是否包含必要字段
            if "sub" not in payload:
                logger.warning("JWT令牌缺少必要字段 'sub'")
                return AuthResult(
                    success=False,
                    error="无效的令牌结构",
                    auth_type="jwt"
                )
                
            # 验证成功
            subject_id = payload["sub"]
            logger.info(f"JWT令牌验证成功, 主题: {subject_id}")
            
            # 提取角色和权限
            roles = payload.get("roles", [])
            permissions = payload.get("permissions", [])
            metadata = payload.get("metadata", {})
            
            # 填充认证结果
            result = AuthResult(
                success=True,
                subject_id=subject_id,
                auth_type="jwt",
                roles=roles,
                permissions=permissions,
                metadata={
                    "jwt": {
                        "iss": payload.get("iss"),
                        "iat": payload.get("iat"),
                        "exp": payload.get("exp"),
                        "type": payload.get("type")
                    },
                    **metadata
                }
            )
            
            return result
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return AuthResult(
                success=False,
                error="令牌已过期",
                auth_type="jwt"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效的JWT令牌: {str(e)}")
            return AuthResult(
                success=False,
                error="无效的令牌",
                auth_type="jwt"
            )
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        使用刷新令牌创建新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            包含新访问令牌的字典，如果刷新失败则返回None
        """
        # 验证刷新令牌
        auth_result = self.verify_token(refresh_token, TOKEN_TYPE_REFRESH)
        if not auth_result.success:
            logger.warning(f"刷新令牌验证失败: {auth_result.error}")
            return None
        
        # 提取刷新令牌中的数据
        token_data = self.decode_token(refresh_token)
        if not token_data:
            logger.warning("解码刷新令牌失败")
            return None
            
        # 创建新的访问令牌
        subject = token_data["sub"]
        roles = token_data.get("roles", [])
        permissions = token_data.get("permissions", [])
        metadata = token_data.get("metadata", {})
        
        # 如果刷新令牌不包含角色和权限，可能需要从用户或服务账户获取
        # 这里为了简化，直接使用刷新令牌中的数据
        
        new_access_token = self.create_access_token(
            subject=subject,
            roles=roles,
            permissions=permissions,
            metadata=metadata
        )
        
        logger.info(f"已为主题 {subject} 刷新访问令牌")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    
    def extract_token_from_header(self, authorization_header: Optional[str]) -> Optional[str]:
        """
        从Authorization头部提取令牌
        
        Args:
            authorization_header: Authorization头部字符串
            
        Returns:
            JWT令牌字符串，如果提取失败则返回None
        """
        if not authorization_header:
            return None
            
        # 检查Bearer前缀
        parts = authorization_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
            
        return parts[1]
    
    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """
        获取令牌的过期时间
        
        Args:
            token: JWT令牌字符串
            
        Returns:
            过期时间，如果获取失败则返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_signature": True})
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp)
            return None
        except PyJWTError:
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """
        检查令牌是否已过期
        
        Args:
            token: JWT令牌字符串
            
        Returns:
            是否已过期
        """
        try:
            jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return False
        except jwt.ExpiredSignatureError:
            return True
        except PyJWTError:
            # 令牌无效，视为已过期
            return True


# 创建全局JWT认证服务实例
jwt_auth_service = JWTAuthService() 