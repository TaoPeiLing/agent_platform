from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import json
import logging

from agent_cores.core.runtime import runtime_service
from agent_cores.models.rbac import Role

# 配置日志
logger = logging.getLogger(__name__)

app = FastAPI(title="SSS Agent Platform API")

# API密钥和授权头
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

# 默认配置为用户角色
DEFAULT_ROLE = Role.USER.value


class RunAgentRequest(BaseModel):
    template_name: Optional[str] = None
    input: str
    session_id: Optional[str] = None
    # 添加角色信息字段，可由调用方直接传递
    roles: Optional[List[str]] = None
    # 用户ID，可由调用方传递
    user_id: Optional[str] = None
    # 元数据，可包含调用方的任何附加信息
    metadata: Optional[Dict[str, Any]] = None


# 用于从授权头中提取角色信息
async def extract_roles_from_auth(
    authorization: Optional[str] = Header(None),
    x_user_roles: Optional[str] = Header(None)
) -> List[str]:
    """
    从授权信息中提取角色信息
    
    支持两种方式:
    1. Authorization头中的JWT令牌
    2. X-User-Roles自定义头
    
    如果都没有，则返回默认用户角色
    """
    # 模拟处理逻辑
    roles = []
    
    # 尝试从X-User-Roles头中获取角色
    if x_user_roles:
        # 格式: role1,role2,role3
        try:
            roles = [role.strip() for role in x_user_roles.split(',')]
            # 验证角色是否有效
            valid_roles = []
            for role in roles:
                try:
                    # 尝试转换为Role枚举验证有效性
                    Role(role)
                    valid_roles.append(role)
                except ValueError:
                    logger.warning(f"忽略无效角色: {role}")
            roles = valid_roles
        except Exception as e:
            logger.error(f"解析X-User-Roles时出错: {e}")
    
    # 如果没有从X-User-Roles获取到角色，尝试从Authorization头解析JWT
    elif authorization and authorization.startswith("Bearer "):
        # 这里应该有JWT解析和验证的逻辑
        # 为演示简化，我们仅进行模拟
        try:
            # 模拟从JWT中提取角色
            token = authorization.split(" ")[1]
            # 实际应用中应该验证令牌并从中提取声明
            # 简化模拟:
            if token == "admin-token":
                roles = [Role.ADMIN.value]
            elif token == "power-user-token":
                roles = [Role.POWER_USER.value]
            else:
                roles = [Role.USER.value]
        except Exception as e:
            logger.error(f"解析Authorization头时出错: {e}")
    
    # 如果角色列表为空，使用默认角色
    if not roles:
        roles = [DEFAULT_ROLE]
        
    return roles


@app.post("/api/v1/agents/run")
async def run_agent(
    request: RunAgentRequest,
    auth_roles: List[str] = Depends(extract_roles_from_auth)
):
    """异步运行代理 (使用Runner.run)"""
    
    # 优先使用请求体中的角色，其次使用从授权提取的角色
    roles = request.roles or auth_roles
    
    # 创建会话并设置角色
    session_id = request.session_id
    if not session_id:
        # 创建新会话
        session_id = runtime_service.create_session(
            user_id=request.user_id,
            roles=roles,
            metadata=request.metadata
        )
    else:
        # 使用现有会话，但更新角色
        session = runtime_service.get_session(session_id)
        if not session:
            # 会话不存在，创建新会话
            session_id = runtime_service.create_session(
                user_id=request.user_id,
                roles=roles,
                metadata=request.metadata
            )
        else:
            # 更新现有会话的角色
            runtime_service.update_session_roles(session_id, roles)
            # 更新会话元数据
            if request.metadata:
                runtime_service.update_session(session_id, request.metadata)
    
    # 执行代理
    result = await runtime_service.run_agent(
        session_id=session_id,
        input_text=request.input,
        template_name=request.template_name
    )
    return result


@app.post("/api/v1/agents/run_sync")
def run_agent_sync(
    request: RunAgentRequest,
    auth_roles: List[str] = Depends(extract_roles_from_auth)
):
    """同步运行代理 (使用Runner.run_sync)"""
    
    # 优先使用请求体中的角色，其次使用从授权提取的角色
    roles = request.roles or auth_roles
    
    # 创建会话并设置角色
    session_id = request.session_id
    if not session_id:
        # 创建新会话
        session_id = runtime_service.create_session(
            user_id=request.user_id,
            roles=roles,
            metadata=request.metadata
        )
    else:
        # 使用现有会话，但更新角色
        session = runtime_service.get_session(session_id)
        if not session:
            # 会话不存在，创建新会话
            session_id = runtime_service.create_session(
                user_id=request.user_id,
                roles=roles,
                metadata=request.metadata
            )
        else:
            # 更新现有会话的角色
            runtime_service.update_session_roles(session_id, roles)
            # 更新会话元数据
            if request.metadata:
                runtime_service.update_session(session_id, request.metadata)
    
    # 执行代理
    result = runtime_service.run_agent_sync(
        session_id=session_id,
        input_text=request.input,
        template_name=request.template_name
    )
    return result


@app.post("/api/v1/agents/run_streamed")
async def run_agent_streamed(
    request: RunAgentRequest,
    auth_roles: List[str] = Depends(extract_roles_from_auth)
):
    """流式运行代理 (使用Runner.run_streamed)，返回SSE响应"""
    
    # 优先使用请求体中的角色，其次使用从授权提取的角色
    roles = request.roles or auth_roles
    
    # 创建会话并设置角色
    session_id = request.session_id
    if not session_id:
        # 创建新会话
        session_id = runtime_service.create_session(
            user_id=request.user_id,
            roles=roles,
            metadata=request.metadata
        )
    else:
        # 使用现有会话，但更新角色
        session = runtime_service.get_session(session_id)
        if not session:
            # 会话不存在，创建新会话
            session_id = runtime_service.create_session(
                user_id=request.user_id,
                roles=roles,
                metadata=request.metadata
            )
        else:
            # 更新现有会话的角色
            runtime_service.update_session_roles(session_id, roles)
            # 更新会话元数据
            if request.metadata:
                runtime_service.update_session(session_id, request.metadata)

    async def event_generator():
        async for chunk in runtime_service.run_agent_streamed(
                session_id=session_id,
                input_text=request.input,
                template_name=request.template_name
        ):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@app.websocket("/api/v1/agents/stream")
async def stream_agent(websocket: WebSocket):
    """WebSocket流式API"""
    await websocket.accept()

    try:
        # 接收请求
        data = await websocket.receive_json()
        input_text = data.get("input")
        template_name = data.get("template_name")
        session_id = data.get("session_id")
        
        # 获取角色信息
        roles = data.get("roles")
        user_id = data.get("user_id")
        metadata = data.get("metadata")
        
        # 检查必须字段
        if not input_text:
            await websocket.send_json({"error": "必须提供输入文本", "done": True})
            return
        
        # 创建或获取会话
        if not session_id:
            # 创建新会话
            session_id = runtime_service.create_session(
                user_id=user_id,
                roles=roles,
                metadata=metadata
            )
        else:
            # 使用现有会话，但更新角色(如果提供)
            session = runtime_service.get_session(session_id)
            if not session:
                # 会话不存在，创建新会话
                session_id = runtime_service.create_session(
                    user_id=user_id,
                    roles=roles,
                    metadata=metadata
                )
            elif roles:
                # 更新现有会话的角色
                runtime_service.update_session_roles(session_id, roles)
                # 更新会话元数据
                if metadata:
                    runtime_service.update_session(session_id, metadata)

        # 流式执行
        async for chunk in runtime_service.run_agent_streamed(
                session_id=session_id,
                input_text=input_text,
                template_name=template_name
        ):
            await websocket.send_json(chunk)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        try:
            await websocket.send_json({"error": str(e), "done": True})
        except:
            pass