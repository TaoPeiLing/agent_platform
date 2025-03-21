"""
HTTP REST连接器

提供标准的HTTP REST API形式的连接器功能。
"""

import uuid
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union, AsyncGenerator, Tuple
import httpx
from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .base_connector import BaseConnector, ConnectorResponse
from agent_cores.core.runtime import runtime_service
from agent_cores.models.rbac import Role
from agent_cores.auth import AuthContext, SessionExtension, auth_service, permission_service, Permission

# 配置日志
logger = logging.getLogger(__name__)


class AgentRequest(BaseModel):
    """智能体调用请求模型"""
    input: Union[str, Dict[str, Any]]
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    session_id: Optional[str] = None
    roles: Optional[List[str]] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    callback_url: Optional[str] = None
    auth_tokens: Optional[Dict[str, str]] = None  # 外部系统认证令牌


class WorkflowRequest(BaseModel):
    """工作流调用请求模型"""
    input: Union[str, Dict[str, Any]]
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    session_id: Optional[str] = None
    roles: Optional[List[str]] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    callback_url: Optional[str] = None
    auth_tokens: Optional[Dict[str, str]] = None  # 外部系统认证令牌


class AuthRequest(BaseModel):
    """认证请求模型"""
    system_id: str
    auth_code: str
    session_id: str
    redirect_uri: str
    state: Optional[str] = None


class StatusResponse(BaseModel):
    """状态响应模型"""
    execution_id: str
    status: str
    progress: Optional[float] = None
    current_step: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error: Optional[str] = None


class HTTPConnector(BaseConnector):
    """HTTP REST API连接器实现"""
    
    def __init__(self):
        self.app = FastAPI(title="SSS Agent Platform Enterprise Connector API")
        self.config = {}
        self.execution_store = {}  # 简单的执行状态存储
        self._setup_routes()
        self._http_client = httpx.AsyncClient()
        
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化连接器"""
        self.config = config
        logger.info("HTTP连接器已初始化")
        return True
        
    def _setup_routes(self):
        """设置API路由"""
        
        @self.app.post("/v1/agents/{agent_id}/invoke", response_model=Dict[str, Any])
        async def invoke_agent(
            agent_id: str, 
            request: AgentRequest, 
            authorization: Optional[str] = Header(None)
        ):
            """同步调用单个智能体"""
            # 处理角色信息
            roles = request.roles or [Role.USER.value]
            
            # 创建认证上下文
            auth_context = self._create_auth_context(
                user_id=request.user_id or "",
                roles=roles,
                auth_tokens=request.auth_tokens or {}
            )
            
            # 检查权限
            if not permission_service.check_agent_permission(roles, agent_id, Permission.EXECUTE):
                raise HTTPException(status_code=403, detail="权限不足，无法调用此智能体")
            
            # 准备输入
            input_data = request.input
            options = request.options or {}
            
            # 调用智能体
            try:
                response = self.invoke_agent(
                    agent_id=agent_id,
                    input_data=input_data,
                    options={
                        **options,
                        "session_id": request.session_id,
                        "roles": roles,
                        "user_id": request.user_id,
                        "metadata": request.metadata
                    },
                    auth_context=auth_context.to_dict()
                )
                
                # 如果提供了回调URL，则注册
                if request.callback_url:
                    self.register_callback(response.execution_id, request.callback_url)
                    
                return response.to_dict()
            except Exception as e:
                logger.error(f"调用智能体时出错: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/v1/agents/{agent_id}/ainvoke", response_model=Dict[str, Any])
        async def ainvoke_agent(
            agent_id: str, 
            request: AgentRequest,
            background_tasks: BackgroundTasks,
            authorization: Optional[str] = Header(None)
        ):
            """异步调用单个智能体"""
            roles = request.roles or [Role.USER.value]
            
            # 创建认证上下文
            auth_context = self._create_auth_context(
                user_id=request.user_id or "",
                roles=roles,
                auth_tokens=request.auth_tokens or {}
            )
            
            # 检查权限
            if not permission_service.check_agent_permission(roles, agent_id, Permission.EXECUTE):
                # 使用后台任务处理异步任务
                execution_id = str(uuid.uuid4())
                
                # 准备错误响应
                error_response = {
                    "execution_id": execution_id,
                    "status": "failed",
                    "error": "权限不足，无法调用此智能体"
                }
                return error_response
            
            input_data = request.input
            options = request.options or {}
            execution_id = str(uuid.uuid4())
            
            # 保存初始状态
            self.execution_store[execution_id] = {
                "status": "running",
                "agent_id": agent_id,
                "created_at": _get_current_time_str(),
                "updated_at": _get_current_time_str()
            }
            
            # 后台运行智能体
            background_tasks.add_task(
                self._run_agent_in_background,
                execution_id,
                agent_id,
                input_data,
                {
                    **options,
                    "session_id": request.session_id,
                    "roles": roles,
                    "user_id": request.user_id,
                    "metadata": request.metadata
                },
                request.callback_url,
                auth_context.to_dict()
            )
            
            return {
                "execution_id": execution_id,
                "status": "running",
                "message": "智能体调用已启动，结果将通过回调URL返回或可通过状态API查询"
            }
            
        @self.app.get("/v1/executions/{execution_id}", response_model=StatusResponse)
        async def get_execution_status(execution_id: str):
            """获取执行状态"""
            status = self.get_status(execution_id)
            if not status:
                raise HTTPException(status_code=404, detail="执行不存在")
            return status
        
        # 工作流相关的API路由
        @self.app.post("/v1/workflows/{workflow_id}/invoke", response_model=Dict[str, Any])
        async def invoke_workflow(
            workflow_id: str, 
            request: WorkflowRequest, 
            authorization: Optional[str] = Header(None)
        ):
            """同步调用多智能体工作流"""
            roles = request.roles or [Role.USER.value]
            
            # 创建认证上下文
            auth_context = self._create_auth_context(
                user_id=request.user_id or "",
                roles=roles,
                auth_tokens=request.auth_tokens or {}
            )
            
            # 检查权限
            if not permission_service.check_workflow_permission(roles, workflow_id):
                raise HTTPException(status_code=403, detail="权限不足，无法调用此工作流")
            
            input_data = request.input
            options = request.options or {}
            
            try:
                response = self.invoke_workflow(
                    workflow_id=workflow_id,
                    input_data=input_data,
                    options={
                        **options,
                        "session_id": request.session_id,
                        "roles": roles,
                        "user_id": request.user_id,
                        "metadata": request.metadata
                    },
                    auth_context=auth_context.to_dict()
                )
                
                if request.callback_url:
                    self.register_callback(response.execution_id, request.callback_url)
                    
                return response.to_dict()
            except Exception as e:
                logger.error(f"调用工作流时出错: {e}")
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/v1/workflows/{workflow_id}/ainvoke", response_model=Dict[str, Any])
        async def ainvoke_workflow(
            workflow_id: str, 
            request: WorkflowRequest,
            background_tasks: BackgroundTasks,
            authorization: Optional[str] = Header(None)
        ):
            """异步调用多智能体工作流"""
            roles = request.roles or [Role.USER.value]
            
            # 创建认证上下文
            auth_context = self._create_auth_context(
                user_id=request.user_id or "",
                roles=roles,
                auth_tokens=request.auth_tokens or {}
            )
            
            # 检查权限
            if not permission_service.check_workflow_permission(roles, workflow_id):
                raise HTTPException(status_code=403, detail="权限不足，无法调用此工作流")
            
            input_data = request.input
            options = request.options or {}
            execution_id = str(uuid.uuid4())
            
            # 保存初始状态
            self.execution_store[execution_id] = {
                "status": "running",
                "workflow_id": workflow_id,
                "created_at": _get_current_time_str(),
                "updated_at": _get_current_time_str()
            }
            
            # 后台运行工作流
            background_tasks.add_task(
                self._run_workflow_in_background,
                execution_id,
                workflow_id,
                input_data,
                {
                    **options,
                    "session_id": request.session_id,
                    "roles": roles,
                    "user_id": request.user_id,
                    "metadata": request.metadata
                },
                request.callback_url,
                auth_context.to_dict()
            )
            
            return {
                "execution_id": execution_id,
                "status": "running",
                "message": "工作流调用已启动，结果将通过回调URL返回或可通过状态API查询"
            }
            
        # 认证相关API路由
        @self.app.post("/v1/auth/callback", response_model=Dict[str, Any])
        async def auth_callback(request: AuthRequest):
            """处理认证回调"""
            try:
                # 获取会话
                session_id = request.session_id
                session = runtime_service.get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="会话不存在")
                
                # 处理认证回调
                token, expiry = await auth_service.process_auth_callback(
                    system_id=request.system_id,
                    auth_code=request.auth_code,
                    redirect_uri=request.redirect_uri,
                    state=request.state
                )
                
                if not token:
                    raise HTTPException(status_code=400, detail="获取访问令牌失败")
                
                # 创建会话扩展
                session_extension = SessionExtension.from_session(session)
                
                # 保存令牌
                session_extension.auth_context.set_token(
                    system_id=request.system_id,
                    token=token,
                    expiry=expiry
                )
                
                # 更新会话
                session_extension.update_session(session)
                
                return {
                    "success": True,
                    "system_id": request.system_id,
                    "message": "认证成功",
                    "expiry": expiry
                }
                
            except Exception as e:
                logger.error(f"处理认证回调时出错: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/v1/auth/url", response_model=Dict[str, Any])
        async def get_auth_url(
            system_id: str,
            session_id: str,
            redirect_uri: str,
            state: Optional[str] = None
        ):
            """获取认证URL"""
            try:
                # 获取会话
                session = runtime_service.get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="会话不存在")
                
                # 获取认证URL
                auth_url = auth_service.get_auth_url(
                    system_id=system_id,
                    redirect_url=redirect_uri,
                    state=state
                )
                
                if not auth_url:
                    raise HTTPException(status_code=400, detail="获取认证URL失败")
                
                return {
                    "auth_url": auth_url,
                    "system_id": system_id
                }
                
            except Exception as e:
                logger.error(f"获取认证URL时出错: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
    def _create_auth_context(self, user_id: str, roles: List[str], auth_tokens: Dict[str, str] = None) -> AuthContext:
        """创建认证上下文"""
        auth_context = AuthContext(
            user_id=user_id,
            roles=roles,
            tokens=auth_tokens or {}
        )
        
        # 如果提供了令牌，设置过期时间（这里假设令牌有效期为1小时）
        if auth_tokens:
            import time
            expiry = int(time.time()) + 3600  # 1小时后过期
            for system_id in auth_tokens:
                auth_context.auth_expiry[system_id] = expiry
                
        return auth_context
        
    async def _run_agent_in_background(
        self, 
        execution_id: str, 
        agent_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Dict[str, Any],
        callback_url: Optional[str] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ):
        """在后台运行智能体"""
        try:
            # 执行智能体调用
            response = await self.ainvoke_agent(
                agent_id, 
                input_data, 
                options, 
                auth_context
            )
            
            # 更新状态
            self.execution_store[execution_id] = {
                "status": response.status,
                "result": response.result,
                "error": response.error,
                "metrics": response.metrics,
                "auth_status": response.auth_status,
                "updated_at": _get_current_time_str()
            }
            
            # 如果有回调URL，发送结果
            if callback_url:
                await self._send_callback(callback_url, response.to_dict())
                
        except Exception as e:
            logger.error(f"后台运行智能体时出错: {e}")
            self.execution_store[execution_id] = {
                "status": "failed",
                "error": str(e),
                "updated_at": _get_current_time_str()
            }
            
            if callback_url:
                await self._send_callback(callback_url, {
                    "execution_id": execution_id,
                    "status": "failed",
                    "error": str(e)
                })
    
    async def _run_workflow_in_background(
        self, 
        execution_id: str, 
        workflow_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Dict[str, Any],
        callback_url: Optional[str] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ):
        """在后台运行工作流"""
        try:
            # 执行工作流调用
            response = await self.ainvoke_workflow(
                workflow_id, 
                input_data, 
                options, 
                auth_context
            )
            
            # 更新状态
            self.execution_store[execution_id] = {
                "status": response.status,
                "result": response.result,
                "error": response.error,
                "metrics": response.metrics,
                "auth_status": response.auth_status,
                "updated_at": _get_current_time_str()
            }
            
            # 如果有回调URL，发送结果
            if callback_url:
                await self._send_callback(callback_url, response.to_dict())
                
        except Exception as e:
            logger.error(f"后台运行工作流时出错: {e}")
            self.execution_store[execution_id] = {
                "status": "failed",
                "error": str(e),
                "updated_at": _get_current_time_str()
            }
            
            if callback_url:
                await self._send_callback(callback_url, {
                    "execution_id": execution_id,
                    "status": "failed",
                    "error": str(e)
                })
    
    async def _send_callback(self, callback_url: str, data: Dict[str, Any]):
        """发送回调请求"""
        try:
            await self._http_client.post(
                callback_url,
                json=data,
                timeout=10.0
            )
        except Exception as e:
            logger.error(f"发送回调时出错: {e}")
    
    def invoke_agent(
        self, 
        agent_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """同步调用单个智能体"""
        options = options or {}
        
        # 提取会话相关参数
        session_id = options.get("session_id")
        roles = options.get("roles", [Role.USER.value])
        user_id = options.get("user_id")
        metadata = options.get("metadata", {})
        
        # 处理会话
        if not session_id:
            session_id = runtime_service.create_session(
                user_id=user_id,
                roles=roles,
                metadata=metadata
            )
        else:
            # 确保会话存在
            session = runtime_service.get_session(session_id)
            if not session:
                session_id = runtime_service.create_session(
                    user_id=user_id,
                    roles=roles,
                    metadata=metadata
                )
            else:
                # 更新会话
                runtime_service.update_session_roles(session_id, roles)
                if metadata:
                    runtime_service.update_session(session_id, metadata)
        
        # 检查权限
        if not permission_service.check_agent_permission(roles, agent_id, Permission.EXECUTE):
            logger.warning(f"用户无权限执行智能体: {agent_id}")
            execution_id = str(uuid.uuid4())
            return ConnectorResponse(
                execution_id=execution_id,
                status="failed",
                error="权限不足，无法调用此智能体"
            )
        
        # 如果提供了认证上下文，更新会话
        if auth_context:
            try:
                # 获取会话
                session = runtime_service.get_session(session_id)
                
                # 创建认证上下文对象
                auth_ctx = AuthContext.from_dict(auth_context)
                
                # 创建会话扩展
                session_extension = SessionExtension(session_id, auth_ctx)
                
                # 更新会话
                session_extension.update_session(session)
            except Exception as e:
                logger.error(f"更新会话认证信息时出错: {e}")
        
        # 处理输入数据
        if isinstance(input_data, dict):
            input_text = json.dumps(input_data)
        else:
            input_text = str(input_data)
        
        # 调用智能体
        execution_id = str(uuid.uuid4())
        try:
            start_time = _get_current_time()
            
            # 检查是否需要认证
            session = runtime_service.get_session(session_id)
            if session and hasattr(session, 'external_systems'):
                # 这部分需要跟真实的运行时集成
                # 这里是示例逻辑
                pass
            
            result = runtime_service.run_agent_sync(
                session_id=session_id,
                input_text=input_text,
                template_name=agent_id
            )
            
            end_time = _get_current_time()
            duration_ms = int((end_time - start_time) * 1000)
            
            return ConnectorResponse(
                execution_id=execution_id,
                status="completed",
                result=result,
                metrics={"duration_ms": duration_ms}
            )
        except Exception as e:
            logger.error(f"调用智能体时出错: {e}")
            return ConnectorResponse(
                execution_id=execution_id,
                status="failed",
                error=str(e)
            )
    
    async def ainvoke_agent(
        self, 
        agent_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """异步调用单个智能体"""
        # 使用同步版本并在事件循环中运行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.invoke_agent(agent_id, input_data, options, auth_context)
        )
    
    async def stream_agent(
        self, 
        agent_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用单个智能体"""
        # 这个方法将由SSEConnector实现
        # 这里提供一个空实现
        raise NotImplementedError("HTTP连接器不支持流式调用，请使用SSEConnector")
        yield {}  # 防止Python语法错误
        
    def invoke_workflow(
        self, 
        workflow_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """同步调用多智能体协作工作流"""
        # 注意：工作流功能需要在runtime_service中实现
        # 当前实现可能需要调整以适应实际的工作流API
        
        options = options or {}
        execution_id = str(uuid.uuid4())
        
        # 提取会话相关参数
        session_id = options.get("session_id")
        roles = options.get("roles", [Role.USER.value])
        
        # 检查权限
        if not permission_service.check_workflow_permission(roles, workflow_id):
            logger.warning(f"没有权限调用工作流 {workflow_id}")
            return ConnectorResponse(
                execution_id=execution_id,
                status="failed",
                error="权限不足，无法调用此工作流"
            )
        
        try:
            # 这里应该有实际的工作流调用实现
            # 以下是模拟实现
            return ConnectorResponse(
                execution_id=execution_id,
                status="completed",
                result={"message": f"工作流 {workflow_id} 调用成功（模拟）"},
                metrics={"duration_ms": 1000}
            )
        except Exception as e:
            logger.error(f"调用工作流时出错: {e}")
            return ConnectorResponse(
                execution_id=execution_id,
                status="failed",
                error=str(e)
            )
    
    async def ainvoke_workflow(
        self, 
        workflow_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """异步调用多智能体协作工作流"""
        # 使用同步版本并在事件循环中运行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.invoke_workflow(workflow_id, input_data, options, auth_context)
        )
        
    async def stream_workflow(
        self, 
        workflow_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用多智能体协作工作流"""
        # 这个方法将由SSEConnector实现
        # 这里提供一个空实现
        raise NotImplementedError("HTTP连接器不支持流式调用，请使用SSEConnector")
        yield {}  # 防止Python语法错误
    
    def get_status(self, execution_id: str) -> Dict[str, Any]:
        """获取特定执行的状态"""
        if execution_id in self.execution_store:
            return self.execution_store[execution_id]
        return {"execution_id": execution_id, "status": "unknown"}
    
    def register_callback(self, execution_id: str, callback_url: str) -> bool:
        """注册回调，用于异步通知结果"""
        # 简单实现：保存回调URL
        if execution_id in self.execution_store:
            self.execution_store[execution_id]["callback_url"] = callback_url
            return True
        return False


# 辅助函数
def _get_current_time():
    """获取当前时间戳"""
    import time
    return time.time()

def _get_current_time_str():
    """获取当前时间字符串"""
    from datetime import datetime
    return datetime.now().isoformat() 