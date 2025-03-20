"""
认证中间件

提供拦截和处理认证请求的中间件，支持API密钥和JWT认证。
为FastAPI和Flask等Web框架提供认证功能。
"""

import logging
import time
from datetime import datetime
from functools import wraps
from typing import Callable, Dict, List, Optional, Any, Union, Tuple

from agent_cores.security.api_key import api_key_manager
from agent_cores.security.jwt_auth import jwt_auth_service
from agent_cores.security.models import AuthResult

# 配置日志
logger = logging.getLogger(__name__)


class AuthMiddleware:
    """
    认证中间件
    
    提供API密钥和JWT认证功能的中间件。
    """
    
    def __init__(self, 
                 require_auth: bool = True,
                 auth_schemes: List[str] = None,
                 excluded_paths: List[str] = None):
        """
        初始化认证中间件
        
        Args:
            require_auth: 是否要求认证，默认为True
            auth_schemes: 支持的认证方案列表，默认为["api_key", "jwt"]
            excluded_paths: 排除的路径列表，这些路径不需要认证
        """
        self.require_auth = require_auth
        self.auth_schemes = auth_schemes or ["api_key", "jwt"]
        self.excluded_paths = excluded_paths or ["/docs", "/redoc", "/openapi.json", "/health"]
        
        logger.info(f"认证中间件已初始化，认证方案: {self.auth_schemes}")
    
    def authenticate(self, request_headers: Dict[str, str], path: str) -> AuthResult:
        """
        认证请求
        
        Args:
            request_headers: 请求头
            path: 请求路径
            
        Returns:
            认证结果
        """
        # 检查是否排除路径
        if self._is_excluded_path(path):
            logger.debug(f"路径 {path} 无需认证")
            return AuthResult(
                success=True,
                auth_type="none",
                subject_id="anonymous",
                roles=["anonymous"],
                permissions=[]
            )
            
        # 尝试从Authorization头部获取认证信息
        auth_header = request_headers.get("Authorization") or request_headers.get("authorization")
        
        # 尝试从X-API-Key头部获取API密钥
        api_key_header = request_headers.get("X-API-Key") or request_headers.get("x-api-key")
        
        # 首先尝试API密钥认证（如果支持）
        if "api_key" in self.auth_schemes and api_key_header:
            auth_result = api_key_manager.verify_api_key(api_key_header)
            if auth_result.success:
                return auth_result
                
        # 然后尝试JWT认证（如果支持）
        if "jwt" in self.auth_schemes and auth_header:
            # 提取JWT令牌
            token = jwt_auth_service.extract_token_from_header(auth_header)
            if token:
                auth_result = jwt_auth_service.verify_token(token)
                if auth_result.success:
                    return auth_result
        
        # 如果API密钥存在但认证失败，且不尝试其他认证方式，直接返回API密钥认证失败
        if "api_key" in self.auth_schemes and api_key_header:
            return AuthResult(
                success=False,
                error="无效的API密钥",
                auth_type="api_key"
            )
            
        # 如果JWT令牌存在但认证失败，且不尝试其他认证方式，直接返回JWT认证失败
        if "jwt" in self.auth_schemes and auth_header:
            return AuthResult(
                success=False,
                error="无效的JWT令牌",
                auth_type="jwt"
            )
            
        # 如果不要求认证，返回匿名用户
        if not self.require_auth:
            return AuthResult(
                success=True,
                auth_type="none",
                subject_id="anonymous",
                roles=["anonymous"],
                permissions=[]
            )
            
        # 认证失败
        return AuthResult(
            success=False,
            error="需要认证",
            auth_type="none"
        )
    
    def _is_excluded_path(self, path: str) -> bool:
        """
        检查路径是否被排除认证
        
        Args:
            path: 请求路径
            
        Returns:
            是否排除
        """
        for excluded_path in self.excluded_paths:
            if path == excluded_path or path.startswith(f"{excluded_path}/"):
                return True
                
        return False


# FastAPI认证依赖
try:
    from fastapi import Depends, HTTPException, Request, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    
    # FastAPI安全方案
    api_key_scheme = HTTPBearer(scheme_name="API Key", auto_error=False)
    jwt_scheme = HTTPBearer(scheme_name="JWT", auto_error=False)
    
    # 创建认证中间件实例
    auth_middleware = AuthMiddleware()
    
    # FastAPI认证依赖函数
    async def authenticate_request(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(jwt_scheme)
    ) -> AuthResult:
        """
        FastAPI认证依赖函数
        
        Args:
            request: FastAPI请求对象
            credentials: 认证凭据
            
        Returns:
            认证结果
            
        Raises:
            HTTPException: 如果认证失败
        """
        # 创建请求头字典
        headers = dict(request.headers)
        
        # 如果有认证凭据，添加到请求头
        if credentials:
            headers["Authorization"] = f"Bearer {credentials.credentials}"
            
        # 调用认证中间件
        auth_result = auth_middleware.authenticate(headers, request.url.path)
        
        # 如果认证失败且要求认证，抛出HTTP异常
        if not auth_result.success and auth_middleware.require_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth_result.error or "需要认证",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        return auth_result
    
    # 检查权限的依赖函数
    def require_permission(permission: str):
        """
        要求特定权限的依赖函数工厂
        
        Args:
            permission: 所需权限
            
        Returns:
            依赖函数
        """
        async def check_permission(auth_result: AuthResult = Depends(authenticate_request)) -> AuthResult:
            if not auth_result.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少所需权限: {permission}"
                )
            return auth_result
        return check_permission
    
    # 检查角色的依赖函数
    def require_role(role: str):
        """
        要求特定角色的依赖函数工厂
        
        Args:
            role: 所需角色
            
        Returns:
            依赖函数
        """
        async def check_role(auth_result: AuthResult = Depends(authenticate_request)) -> AuthResult:
            if not auth_result.has_role(role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少所需角色: {role}"
                )
            return auth_result
        return check_role
    
except ImportError:
    # FastAPI没有安装，跳过
    logger.info("FastAPI未安装，跳过FastAPI认证依赖")


# Flask认证中间件
try:
    from flask import Flask, request, jsonify, g
    
    class FlaskAuthMiddleware:
        """
        Flask认证中间件
        
        将认证中间件集成到Flask应用中。
        """
        
        def __init__(self, app: Flask = None, **kwargs):
            """
            初始化Flask认证中间件
            
            Args:
                app: Flask应用
                **kwargs: 传递给AuthMiddleware的参数
            """
            self.auth_middleware = AuthMiddleware(**kwargs)
            
            if app:
                self.init_app(app)
                
        def init_app(self, app: Flask):
            """
            初始化Flask应用
            
            Args:
                app: Flask应用
            """
            @app.before_request
            def authenticate():
                # 跳过OPTIONS请求
                if request.method == "OPTIONS":
                    return None
                    
                # 获取认证结果
                auth_result = self.auth_middleware.authenticate(
                    request_headers=dict(request.headers),
                    path=request.path
                )
                
                # 将认证结果存储在g对象中
                g.auth_result = auth_result
                
                # 如果认证失败且要求认证，返回401响应
                if not auth_result.success and self.auth_middleware.require_auth:
                    return jsonify({
                        "error": auth_result.error or "需要认证",
                        "status": "error",
                        "code": 401
                    }), 401
                    
                return None
                
        def require_permission(self, permission: str):
            """
            要求特定权限的装饰器
            
            Args:
                permission: 所需权限
                
            Returns:
                装饰器
            """
            def decorator(f):
                @wraps(f)
                def decorated(*args, **kwargs):
                    auth_result = g.auth_result
                    
                    if not auth_result.has_permission(permission):
                        return jsonify({
                            "error": f"缺少所需权限: {permission}",
                            "status": "error",
                            "code": 403
                        }), 403
                        
                    return f(*args, **kwargs)
                return decorated
            return decorator
            
        def require_role(self, role: str):
            """
            要求特定角色的装饰器
            
            Args:
                role: 所需角色
                
            Returns:
                装饰器
            """
            def decorator(f):
                @wraps(f)
                def decorated(*args, **kwargs):
                    auth_result = g.auth_result
                    
                    if not auth_result.has_role(role):
                        return jsonify({
                            "error": f"缺少所需角色: {role}",
                            "status": "error",
                            "code": 403
                        }), 403
                        
                    return f(*args, **kwargs)
                return decorated
            return decorator
            
except ImportError:
    # Flask没有安装，跳过
    logger.info("Flask未安装，跳过Flask认证中间件") 