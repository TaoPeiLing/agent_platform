"""
HTTP+SSE连接器

提供HTTP+Server-Sent Events流式响应的连接器功能。
适用于需要实时流式输出但又不需要双向通信的场景。
"""

import uuid
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
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
    auth_tokens: Optional[Dict[str, str]] = None  # 外部系统认证令牌


class WorkflowRequest(BaseModel):
    """工作流调用请求模型"""
    input: Union[str, Dict[str, Any]]
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    session_id: Optional[str] = None
    roles: Optional[List[str]] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    auth_tokens: Optional[Dict[str, str]] = None  # 外部系统认证令牌


class SSEEvent:
    """SSE事件类"""
    
    def __init__(
        self, 
        event_type: str, 
        data: Dict[str, Any],
        event_id: Optional[str] = None,
        retry: Optional[int] = None
    ):
        self.event_type = event_type
        self.data = data
        self.event_id = event_id
        self.retry = retry
        
    def to_sse(self) -> str:
        """转换为SSE格式的字符串"""
        lines = [f"event: {self.event_type}"]
        
        if self.event_id:
            lines.append(f"id: {self.event_id}")
            
        if self.retry:
            lines.append(f"retry: {self.retry}")
            
        # 序列化数据
        data_str = json.dumps(self.data)
        
        # SSE规范要求data字段可以分多行，每行以"data: "开头
        lines.append(f"data: {data_str}")
        
        # 以两个换行符结束事件
        return "\n".join(lines) + "\n\n"


class SSEConnector(BaseConnector):
    """HTTP+SSE连接器实现"""
    
    def __init__(self):
        self.app = FastAPI(title="SSS Agent Platform SSE Connector API")
        self.config = {}
        self.execution_store = {}  # 简单的执行状态存储
        self._setup_routes()
        
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化连接器"""
        self.config = config
        logger.info("SSE连接器已初始化")
        return True
        
    def _setup_routes(self):
        """设置API路由"""
        
        @self.app.post("/v1/agents/{agent_id}/stream")
        async def stream_agent(
            agent_id: str, 
            request: AgentRequest, 
            authorization: Optional[str] = Header(None)
        ):
            """流式调用单个智能体，返回SSE响应"""
            roles = request.roles or [Role.USER.value]
            
            # 创建认证上下文
            auth_context = self._create_auth_context(
                user_id=request.user_id or "",
                roles=roles,
                auth_tokens=request.auth_tokens or {}
            )
            
            # 检查权限
            if not permission_service.check_agent_permission(roles, agent_id, Permission.EXECUTE):
                # 返回权限错误的SSE流
                return StreamingResponse(
                    self._generate_error_stream("permission_denied", "权限不足，无法调用此智能体"),
                    media_type="text/event-stream"
                )
            
            input_data = request.input
            options = request.options or {}
            
            # 准备会话
            session_id = await self._prepare_session(
                request.session_id,
                roles,
                request.user_id,
                request.metadata,
                auth_context
            )
            
            # 创建执行ID
            execution_id = str(uuid.uuid4())
            
            # 返回流式响应
            return StreamingResponse(
                self._generate_agent_stream(
                    execution_id,
                    agent_id,
                    input_data,
                    {
                        **options,
                        "session_id": session_id,
                        "roles": roles,
                        "user_id": request.user_id,
                        "metadata": request.metadata
                    },
                    auth_context.to_dict()
                ),
                media_type="text/event-stream"
            )
            
        @self.app.post("/v1/workflows/{workflow_id}/stream")
        async def stream_workflow(
            workflow_id: str, 
            request: WorkflowRequest, 
            authorization: Optional[str] = Header(None)
        ):
            """流式调用多智能体工作流，返回SSE响应"""
            roles = request.roles or [Role.USER.value]
            
            # 创建认证上下文
            auth_context = self._create_auth_context(
                user_id=request.user_id or "",
                roles=roles,
                auth_tokens=request.auth_tokens or {}
            )
            
            # 检查权限
            if not permission_service.check_workflow_permission(roles, workflow_id):
                # 返回权限错误的SSE流
                return StreamingResponse(
                    self._generate_error_stream("permission_denied", "权限不足，无法调用此工作流"),
                    media_type="text/event-stream"
                )
            
            input_data = request.input
            options = request.options or {}
            
            # 准备会话
            session_id = await self._prepare_session(
                request.session_id,
                roles,
                request.user_id,
                request.metadata,
                auth_context
            )
            
            # 创建执行ID
            execution_id = str(uuid.uuid4())
            
            # 返回流式响应
            return StreamingResponse(
                self._generate_workflow_stream(
                    execution_id,
                    workflow_id,
                    input_data,
                    {
                        **options,
                        "session_id": session_id,
                        "roles": roles,
                        "user_id": request.user_id,
                        "metadata": request.metadata
                    },
                    auth_context.to_dict()
                ),
                media_type="text/event-stream"
            )
            
        @self.app.get("/v1/auth/sse_status")
        async def auth_status(
            system_id: str,
            session_id: str
        ):
            """获取认证状态的SSE流"""
            try:
                # 获取会话
                session = runtime_service.get_session(session_id)
                if not session:
                    return StreamingResponse(
                        self._generate_error_stream("session_not_found", "会话不存在"),
                        media_type="text/event-stream"
                    )
                
                # 创建会话扩展
                session_extension = SessionExtension.from_session(session)
                
                # 检查令牌状态
                return StreamingResponse(
                    self._generate_auth_status_stream(system_id, session_extension),
                    media_type="text/event-stream"
                )
                
            except Exception as e:
                logger.error(f"获取认证状态时出错: {e}")
                return StreamingResponse(
                    self._generate_error_stream("internal_error", str(e)),
                    media_type="text/event-stream"
                )
    
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
    
    async def _generate_error_stream(self, error_type: str, error_message: str) -> AsyncGenerator[str, None]:
        """生成错误事件流"""
        # 发送错误事件
        yield SSEEvent(
            event_type="error",
            data={
                "type": error_type,
                "message": error_message
            },
            event_id=f"error-{uuid.uuid4()}"
        ).to_sse()
        
        # 发送完成事件
        yield SSEEvent(
            event_type="done",
            data={"success": False},
            event_id=f"done-{uuid.uuid4()}"
        ).to_sse()
    
    async def _generate_auth_status_stream(self, system_id: str, session_extension: SessionExtension) -> AsyncGenerator[str, None]:
        """生成认证状态事件流"""
        auth_context = session_extension.auth_context
        
        # 检查令牌状态
        is_valid = auth_context.is_token_valid(system_id)
        
        # 发送状态事件
        yield SSEEvent(
            event_type="auth_status",
            data={
                "system_id": system_id,
                "is_valid": is_valid,
                "expiry": auth_context.auth_expiry.get(system_id, 0) if is_valid else 0
            },
            event_id=f"status-{uuid.uuid4()}"
        ).to_sse()
        
        # 如果令牌无效，获取认证URL
        if not is_valid:
            # 这里应该提供一个默认的重定向URL
            redirect_uri = "http://localhost:3000/auth/callback"
            
            # 获取认证URL
            auth_url = auth_service.get_auth_url(
                system_id=system_id,
                redirect_url=redirect_uri
            )
            
            if auth_url:
                yield SSEEvent(
                    event_type="auth_url",
                    data={
                        "system_id": system_id,
                        "auth_url": auth_url
                    },
                    event_id=f"auth-url-{uuid.uuid4()}"
                ).to_sse()
        
        # 发送完成事件
        yield SSEEvent(
            event_type="done",
            data={"success": True},
            event_id=f"done-{uuid.uuid4()}"
        ).to_sse()
    
    async def _prepare_session(
        self,
        session_id: Optional[str], 
        roles: List[str],
        user_id: Optional[str],
        metadata: Optional[Dict[str, Any]],
        auth_context: AuthContext
    ) -> str:
        """准备会话"""
        if not session_id:
            # 创建新会话
            session_id = runtime_service.create_session(
                user_id=user_id,
                roles=roles,
                metadata=metadata
            )
        else:
            # 确保会话存在
            session = runtime_service.get_session(session_id)
            if not session:
                # 会话不存在，创建新会话
                session_id = runtime_service.create_session(
                    user_id=user_id,
                    roles=roles,
                    metadata=metadata
                )
            else:
                # 更新现有会话
                runtime_service.update_session_roles(session_id, roles)
                if metadata:
                    runtime_service.update_session(session_id, metadata)
        
        # 更新会话的认证信息
        try:
            session = runtime_service.get_session(session_id)
            
            # 创建会话扩展
            session_extension = SessionExtension(session_id, auth_context)
            
            # 更新会话
            session_extension.update_session(session)
        except Exception as e:
            logger.error(f"更新会话认证信息时出错: {e}")
                    
        return session_id
        
    async def _generate_agent_stream(
        self,
        execution_id: str,
        agent_id: str,
        input_data: Union[str, Dict[str, Any]],
        options: Dict[str, Any],
        auth_context_dict: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """生成智能体流式响应"""
        try:
            # 发送开始事件
            yield SSEEvent(
                event_type="start",
                data={
                    "execution_id": execution_id,
                    "agent_id": agent_id,
                    "timestamp": _get_current_time_str()
                },
                event_id=f"event-{uuid.uuid4()}"
            ).to_sse()
            
            # 处理输入数据
            if isinstance(input_data, dict):
                input_text = json.dumps(input_data)
            else:
                input_text = str(input_data)
                
            session_id = options.get("session_id")
            
            # 获取会话和认证上下文
            session = runtime_service.get_session(session_id)
            
            # 检查外部系统认证
            auth_context = AuthContext.from_dict(auth_context_dict)
            auth_required_systems = set()
            
            # 这里应该检查智能体可能需要的外部系统认证
            # 这部分需要与实际的Agent实现集成
            # 以下是示例逻辑
            required_systems = []  # 此处应从agent_id获取可能需要的系统列表
            
            for system_id in required_systems:
                if not auth_context.is_token_valid(system_id):
                    auth_required_systems.add(system_id)
            
            # 如果需要认证，发送认证所需事件
            if auth_required_systems:
                for system_id in auth_required_systems:
                    # 获取认证URL，这里使用一个默认重定向URI
                    redirect_uri = "http://localhost:3000/auth/callback"
                    auth_url = auth_service.get_auth_url(
                        system_id=system_id,
                        redirect_url=redirect_uri
                    )
                    
                    if auth_url:
                        yield SSEEvent(
                            event_type="auth_required",
                            data={
                                "system_id": system_id,
                                "auth_url": auth_url,
                                "message": f"需要认证才能访问系统: {system_id}"
                            },
                            event_id=f"auth-required-{uuid.uuid4()}"
                        ).to_sse()
                
                # 发送认证等待事件
                yield SSEEvent(
                    event_type="auth_waiting",
                    data={
                        "systems": list(auth_required_systems),
                        "message": "请完成认证后继续"
                    },
                    event_id=f"auth-waiting-{uuid.uuid4()}"
                ).to_sse()
                
                # 发送完成事件
                yield SSEEvent(
                    event_type="done",
                    data={
                        "success": False,
                        "reason": "auth_required"
                    },
                    event_id=f"done-{uuid.uuid4()}"
                ).to_sse()
                
                return
            
            # 实际运行智能体并流式输出
            chunk_id = 0
            start_time = _get_current_time()
            
            async for chunk in runtime_service.run_agent_streamed(
                session_id=session_id,
                input_text=input_text,
                template_name=agent_id
            ):
                chunk_id += 1
                
                # 为不同类型的块生成不同的事件
                if "thinking" in chunk:
                    yield SSEEvent(
                        event_type="thinking",
                        data={"content": chunk["thinking"]},
                        event_id=f"chunk-{chunk_id}"
                    ).to_sse()
                elif "content" in chunk:
                    yield SSEEvent(
                        event_type="chunk",
                        data={
                            "content": chunk["content"],
                            "finish_reason": chunk.get("finish_reason")
                        },
                        event_id=f"chunk-{chunk_id}"
                    ).to_sse()
                elif "tool_call" in chunk:
                    yield SSEEvent(
                        event_type="tool_call",
                        data=chunk["tool_call"],
                        event_id=f"chunk-{chunk_id}"
                    ).to_sse()
                elif "tool_result" in chunk:
                    yield SSEEvent(
                        event_type="tool_result",
                        data=chunk["tool_result"],
                        event_id=f"chunk-{chunk_id}"
                    ).to_sse()
                
            # 计算耗时
            end_time = _get_current_time()
            duration_ms = int((end_time - start_time) * 1000)
            
            # 发送元数据事件
            yield SSEEvent(
                event_type="metadata",
                data={
                    "duration_ms": duration_ms,
                    "chunks": chunk_id
                },
                event_id=f"metadata-{uuid.uuid4()}"
            ).to_sse()
            
            # 发送完成事件
            yield SSEEvent(
                event_type="done",
                data={"success": True},
                event_id=f"done-{uuid.uuid4()}"
            ).to_sse()
            
        except Exception as e:
            logger.error(f"生成智能体流式输出时出错: {e}")
            
            # 发送错误事件
            yield SSEEvent(
                event_type="error",
                data={"message": str(e)},
                event_id=f"error-{uuid.uuid4()}"
            ).to_sse()
            
    async def _generate_workflow_stream(
        self,
        execution_id: str,
        workflow_id: str,
        input_data: Union[str, Dict[str, Any]],
        options: Dict[str, Any],
        auth_context_dict: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """生成工作流流式响应"""
        try:
            # 发送开始事件
            yield SSEEvent(
                event_type="workflow_start",
                data={
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                    "timestamp": _get_current_time_str()
                },
                event_id=f"event-{uuid.uuid4()}"
            ).to_sse()
            
            # 获取会话和认证上下文
            session_id = options.get("session_id")
            session = runtime_service.get_session(session_id)
            
            # 检查外部系统认证
            auth_context = AuthContext.from_dict(auth_context_dict)
            auth_required_systems = set()
            
            # 这里应该检查工作流可能需要的外部系统认证
            # 这部分需要与实际的工作流实现集成
            # 以下是示例逻辑
            required_systems = []  # 此处应从workflow_id获取可能需要的系统列表
            
            for system_id in required_systems:
                if not auth_context.is_token_valid(system_id):
                    auth_required_systems.add(system_id)
            
            # 如果需要认证，发送认证所需事件
            if auth_required_systems:
                for system_id in auth_required_systems:
                    # 获取认证URL，这里使用一个默认重定向URI
                    redirect_uri = "http://localhost:3000/auth/callback"
                    auth_url = auth_service.get_auth_url(
                        system_id=system_id,
                        redirect_url=redirect_uri
                    )
                    
                    if auth_url:
                        yield SSEEvent(
                            event_type="auth_required",
                            data={
                                "system_id": system_id,
                                "auth_url": auth_url,
                                "message": f"需要认证才能访问系统: {system_id}"
                            },
                            event_id=f"auth-required-{uuid.uuid4()}"
                        ).to_sse()
                
                # 发送完成事件
                yield SSEEvent(
                    event_type="done",
                    data={
                        "success": False,
                        "reason": "auth_required"
                    },
                    event_id=f"done-{uuid.uuid4()}"
                ).to_sse()
                
                return
            
            # 注意：工作流功能需要在runtime_service中实现
            # 这里是模拟实现
            
            # 模拟工作流中的第一个智能体
            yield SSEEvent(
                event_type="agent_start",
                data={
                    "agent_id": "data_analyzer",
                    "step": 1,
                    "timestamp": _get_current_time_str()
                },
                event_id=f"agent-1-start"
            ).to_sse()
            
            # 模拟思考
            yield SSEEvent(
                event_type="thinking",
                data={"content": "分析数据中...", "agent_id": "data_analyzer"},
                event_id=f"chunk-thinking-1"
            ).to_sse()
            
            # 模拟输出
            yield SSEEvent(
                event_type="chunk",
                data={
                    "content": "初步分析结果表明...", 
                    "agent_id": "data_analyzer",
                    "finish_reason": None
                },
                event_id=f"chunk-1"
            ).to_sse()
            
            # 模拟第一个智能体完成
            yield SSEEvent(
                event_type="agent_complete",
                data={
                    "agent_id": "data_analyzer",
                    "status": "success",
                    "timestamp": _get_current_time_str()
                },
                event_id=f"agent-1-complete"
            ).to_sse()
            
            # 模拟第二个智能体开始
            yield SSEEvent(
                event_type="agent_start",
                data={
                    "agent_id": "financial_advisor",
                    "step": 2,
                    "timestamp": _get_current_time_str()
                },
                event_id=f"agent-2-start"
            ).to_sse()
            
            # 模拟思考
            yield SSEEvent(
                event_type="thinking",
                data={"content": "制定建议中...", "agent_id": "financial_advisor"},
                event_id=f"chunk-thinking-2"
            ).to_sse()
            
            # 模拟输出
            yield SSEEvent(
                event_type="chunk",
                data={
                    "content": "基于分析，我建议...", 
                    "agent_id": "financial_advisor",
                    "finish_reason": "stop"
                },
                event_id=f"chunk-2"
            ).to_sse()
            
            # 模拟第二个智能体完成
            yield SSEEvent(
                event_type="agent_complete",
                data={
                    "agent_id": "financial_advisor",
                    "status": "success",
                    "timestamp": _get_current_time_str()
                },
                event_id=f"agent-2-complete"
            ).to_sse()
            
            # 发送工作流完成事件
            yield SSEEvent(
                event_type="workflow_complete",
                data={
                    "workflow_id": workflow_id,
                    "status": "success",
                    "timestamp": _get_current_time_str()
                },
                event_id=f"workflow-complete"
            ).to_sse()
            
            # 发送元数据事件
            yield SSEEvent(
                event_type="metadata",
                data={
                    "duration_ms": 2000,
                    "agents_completed": 2
                },
                event_id=f"metadata-{uuid.uuid4()}"
            ).to_sse()
            
            # 发送完成事件
            yield SSEEvent(
                event_type="done",
                data={"success": True},
                event_id=f"done-{uuid.uuid4()}"
            ).to_sse()
            
        except Exception as e:
            logger.error(f"生成工作流流式输出时出错: {e}")
            
            # 发送错误事件
            yield SSEEvent(
                event_type="error",
                data={"message": str(e)},
                event_id=f"error-{uuid.uuid4()}"
            ).to_sse()
    
    def invoke_agent(
        self, 
        agent_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """同步调用单个智能体（不支持，重定向到HTTP连接器）"""
        raise NotImplementedError("SSE连接器不支持同步调用，请使用HTTPConnector")
    
    async def ainvoke_agent(
        self, 
        agent_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """异步调用单个智能体（不支持，重定向到HTTP连接器）"""
        raise NotImplementedError("SSE连接器不支持异步调用，请使用HTTPConnector")
    
    async def stream_agent(
        self, 
        agent_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用单个智能体"""
        options = options or {}
        auth_context_dict = auth_context or {}
        
        # 提取和准备会话
        session_id = options.get("session_id")
        roles = options.get("roles", [Role.USER.value])
        user_id = options.get("user_id")
        metadata = options.get("metadata", {})
        
        # 检查权限
        if not permission_service.check_agent_permission(roles, agent_id, Permission.EXECUTE):
            logger.warning(f"用户无权限执行智能体: {agent_id}")
            
            # 记录权限拒绝事件
            async for chunk in self._generate_error_stream("permission_denied", "权限不足，无法调用此智能体"):
                yield json.loads(chunk.split("data: ")[1])
                
            return
        
        # 创建认证上下文
        if not auth_context_dict:
            auth_ctx = self._create_auth_context(user_id or "", roles)
        else:
            auth_ctx = AuthContext.from_dict(auth_context_dict)
        
        # 处理会话
        if not session_id:
            session_id = runtime_service.create_session(
                user_id=user_id,
                roles=roles,
                metadata=metadata
            )
            
            # 更新会话认证信息
            session = runtime_service.get_session(session_id)
            session_extension = SessionExtension(session_id, auth_ctx)
            session_extension.update_session(session)
        else:
            # 确保会话存在
            session = runtime_service.get_session(session_id)
            if not session:
                session_id = runtime_service.create_session(
                    user_id=user_id,
                    roles=roles,
                    metadata=metadata
                )
                
                # 更新会话认证信息
                session = runtime_service.get_session(session_id)
                session_extension = SessionExtension(session_id, auth_ctx)
                session_extension.update_session(session)
            else:
                # 更新会话
                runtime_service.update_session_roles(session_id, roles)
                if metadata:
                    runtime_service.update_session(session_id, metadata)
                
                # 更新会话认证信息
                session_extension = SessionExtension(session_id, auth_ctx)
                session_extension.update_session(session)
        
        # 处理输入数据
        if isinstance(input_data, dict):
            input_text = json.dumps(input_data)
        else:
            input_text = str(input_data)
        
        # 流式输出
        try:
            # 检查是否需要认证
            # 这部分需要跟实际的Agent实现集成
            required_systems = []  # 此处应从agent_id获取可能需要的系统列表
            
            for system_id in required_systems:
                if not auth_ctx.is_token_valid(system_id):
                    yield {
                        "event": "auth_required",
                        "system_id": system_id,
                        "message": f"需要认证才能访问系统: {system_id}"
                    }
                    return
            
            async for chunk in runtime_service.run_agent_streamed(
                session_id=session_id,
                input_text=input_text,
                template_name=agent_id
            ):
                yield chunk
        except Exception as e:
            logger.error(f"流式调用智能体时出错: {e}")
            yield {"error": str(e)}
        
    def invoke_workflow(
        self, 
        workflow_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """同步调用多智能体协作工作流（不支持，重定向到HTTP连接器）"""
        raise NotImplementedError("SSE连接器不支持同步调用，请使用HTTPConnector")
    
    async def ainvoke_workflow(
        self, 
        workflow_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """异步调用多智能体协作工作流（不支持，重定向到HTTP连接器）"""
        raise NotImplementedError("SSE连接器不支持异步调用，请使用HTTPConnector")
        
    async def stream_workflow(
        self, 
        workflow_id: str, 
        input_data: Union[str, Dict[str, Any]], 
        options: Optional[Dict[str, Any]] = None,
        auth_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用多智能体协作工作流"""
        options = options or {}
        auth_context_dict = auth_context or {}
        
        # 提取和准备会话
        session_id = options.get("session_id")
        roles = options.get("roles", [Role.USER.value])
        user_id = options.get("user_id")
        
        # 检查权限
        if not permission_service.check_workflow_permission(roles, workflow_id):
            logger.warning(f"用户 {user_id} 没有权限调用工作流 {workflow_id}")
            yield {"error": "权限不足，无法调用此工作流"}
            return
        
        # 注意：工作流功能需要在runtime_service中实现
        # 这里是模拟实现
        
        # 模拟工作流中的第一个智能体
        yield {"event": "agent_start", "agent_id": "data_analyzer", "step": 1}
        yield {"thinking": "分析数据中...", "agent_id": "data_analyzer"}
        yield {"content": "初步分析结果表明...", "agent_id": "data_analyzer"}
        yield {"event": "agent_complete", "agent_id": "data_analyzer", "status": "success"}
        
        # 模拟第二个智能体
        yield {"event": "agent_start", "agent_id": "financial_advisor", "step": 2}
        yield {"thinking": "制定建议中...", "agent_id": "financial_advisor"}
        yield {"content": "基于分析，我建议...", "agent_id": "financial_advisor"}
        yield {"event": "agent_complete", "agent_id": "financial_advisor", "status": "success"}
        
        # 完成
        yield {"event": "workflow_complete", "status": "success"}
    
    def get_status(self, execution_id: str) -> Dict[str, Any]:
        """获取特定执行的状态"""
        return {"execution_id": execution_id, "status": "completed", "message": "SSE连接器不维护执行状态"}
    
    def register_callback(self, execution_id: str, callback_url: str) -> bool:
        """注册回调（不支持，SSE是推送模式）"""
        logger.warning("SSE连接器不支持回调注册，使用事件流代替")
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