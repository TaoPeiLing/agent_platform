"""
运行时服务模块 - 负责代理执行和会话管理
"""
import os
import sys
import logging
import uuid
import time
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logger = logging.getLogger(__name__)

# 导入OpenAI Agent SDK
from agents import Runner, Agent, RunConfig

# 导入事件类型 (从agents.events或agents中导入)
try:
    # 尝试从新版SDK导入
    from agents.events import RunItemStreamEvent
except ImportError:
    try:
        # 尝试从旧版SDK导入
        from agents import RunItemStreamEvent
    except ImportError:
        logger.warning("无法导入RunItemStreamEvent，流式输出可能无法正确处理事件类型")

# 导入代理工厂
from agent_cores.core.factory import AgentFactory

# 导入模板管理器
from agent_cores.core.template_manager import template_manager

# 导入上下文管理器 - 同时支持内存版本和Redis版本
from agent_cores.core.context_manager import context_manager, AgentContext

# 检查环境变量中的Redis设置（优先级高于自动检测）
USE_REDIS_ENV = os.getenv("USE_REDIS", "").lower()
if USE_REDIS_ENV in ["false", "0", "no", "off"]:
    # 环境变量明确禁用Redis
    USE_REDIS = False
    logger.info("根据环境变量设置，已禁用Redis上下文管理器")
elif USE_REDIS_ENV in ["true", "1", "yes", "on"]:
    # 环境变量明确启用Redis
    USE_REDIS = True
    logger.info("根据环境变量设置，尝试启用Redis上下文管理器")
else:
    # 环境变量未明确指定，尝试自动检测
    try:
        from agent_cores.core.redis_context_manager import redis_context_manager
        USE_REDIS = True
        logger.info("Redis上下文管理器已加载(自动检测)")
    except ImportError:
        USE_REDIS = False
        logger.warning("Redis上下文管理器未加载(自动检测)，将使用内存管理器")

# 如果启用了Redis，但尚未导入，尝试导入
if USE_REDIS and 'redis_context_manager' not in locals():
    try:
        from agent_cores.core.redis_context_manager import redis_context_manager
        logger.info("Redis上下文管理器已成功导入")
    except ImportError:
        USE_REDIS = False
        logger.warning("Redis上下文管理器导入失败，切换到内存管理器")

# 导入RBAC相关
from agent_cores.models.rbac import Role

# 导入简化上下文

# 导入新的Agent上下文
from agent_cores.core.agent_context import AgentContext

# 添加导入
from agent_cores.extensions.agent_adapter import OpenAIAgentAdapter

# 导入安全服务
try:
    from agent_cores.security import security_service
    HAS_SECURITY_SERVICE = True
except ImportError:
    HAS_SECURITY_SERVICE = False
    logger.warning("无法导入安全服务，安全特性将被禁用")


@dataclass
class SessionContext:
    """会话上下文数据"""
    session_id: str
    user_id: Optional[str] = None
    roles: List[str] = field(default_factory=lambda: [Role.USER.value])  # 默认为普通用户角色
    permissions: List[str] = field(default_factory=list)  # 用户权限列表
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    history: List[Dict[str, Any]] = field(default_factory=list)
    security_context: Dict[str, Any] = field(default_factory=dict)  # 安全上下文信息


class RuntimeService:
    """
    运行时服务 - 管理代理执行和会话状态

    主要功能:
    1. 执行代理（同步/异步/流式）
    2. 会话状态管理
    3. 执行历史记录
    """

    def __init__(self, use_redis: Optional[bool] = None, security_service=None):
        """
        初始化运行时服务
        
        Args:
            use_redis: 是否使用Redis存储上下文，如果为None则使用环境变量或自动检测
            security_service: 安全服务实例，如果为None则使用全局实例
        """
        self.sessions: Dict[str, SessionContext] = {}
        self.default_config = RunConfig()
        self.agent_factory = AgentFactory()
        
        # 确定是否使用Redis
        # 参数 > 环境变量 > 全局检测
        if use_redis is not None:
            # 传入参数明确指定，优先级最高
            self.use_redis = use_redis
            logger.info(f"运行时服务使用Redis: {self.use_redis} (由参数指定)")
        else:
            # 使用全局检测结果
            self.use_redis = USE_REDIS
            source = "环境变量" if USE_REDIS_ENV else "自动检测"
            logger.info(f"运行时服务使用Redis: {self.use_redis} (由{source}指定)")
        
        # 设置安全服务
        self.security_service = security_service
        if self.security_service is None and HAS_SECURITY_SERVICE:
            self.security_service = globals().get('security_service')
            logger.info("运行时服务已集成安全服务")
        elif self.security_service is None:
            logger.warning("安全服务未配置，安全特性将被禁用")
        
        # 日志记录初始化设置
        redis_status = "使用" if self.use_redis else "不使用"
        logger.info(f"运行时服务初始化，{redis_status}Redis存储上下文")

    def _safely_get_agent_property(self, agent, property_name, default_value=None):
        """
        安全获取代理对象的属性值，避免出现'dict' object has no attribute的错误
        
        Args:
            agent: 代理对象，可能是Agent实例、字典或其他类型
            property_name: 要获取的属性名
            default_value: 属性不存在时的默认值
            
        Returns:
            属性值或默认值
        """
        try:
            # 如果agent是对象并且有该属性
            if hasattr(agent, property_name):
                return getattr(agent, property_name)
            # 如果agent是字典
            elif isinstance(agent, dict) and property_name in agent:
                return agent[property_name]
            # 默认返回
            return default_value
        except:
            logger.warning(f"无法安全获取属性: {property_name}")
            return default_value

    def create_session(self,
                       user_id: Optional[str] = None,
                       roles: Optional[List[str]] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        创建新会话

        Args:
            user_id: 用户ID
            roles: 角色列表，默认为[user]
            metadata: 会话元数据

        Returns:
            会话ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = SessionContext(
            session_id=session_id,
            user_id=user_id,
            roles=roles or [Role.USER.value],
            metadata=metadata or {}
        )
        
        # 用户名信息
        user_name = metadata.get("user_name", "用户") if metadata else "用户"
        
        # 同时创建代理上下文 - 使用合适的上下文管理器
        if self.use_redis:
            redis_context_manager.create_context(
                session_id=session_id,
                user_id=user_id or "anonymous",
                user_name=user_name,
                metadata=metadata or {}
            )
        else:
            context_manager.create_context(
                session_id=session_id,
                user_id=user_id or "anonymous",
                user_name=user_name,
                metadata=metadata or {}
            )
        
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """
        获取会话

        Args:
            session_id: 会话ID

        Returns:
            会话上下文，如果不存在则返回None
        """
        return self.sessions.get(session_id)

    def update_session(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """
        更新会话元数据

        Args:
            session_id: 会话ID
            metadata: 要更新的元数据

        Returns:
            是否成功更新
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session.metadata.update(metadata)
        session.last_active = time.time()
        return True
        
    def update_session_roles(self, session_id: str, roles: List[str]) -> bool:
        """
        更新会话角色

        Args:
            session_id: 会话ID
            roles: 角色列表

        Returns:
            是否成功更新
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # 验证角色是否有效
        try:
            valid_roles = []
            for role in roles:
                # 尝试转换为Role枚举，验证有效性
                Role(role)
                valid_roles.append(role)
                
            session.roles = valid_roles
            session.last_active = time.time()
            return True
        except ValueError as e:
            logger.warning(f"更新角色失败: {e}")
            return False

    def add_history_item(self,
                         session_id: str,
                         role: str,
                         content: str,
                         **extra) -> bool:
        """
        添加历史记录

        Args:
            session_id: 会话ID
            role: 角色（user/assistant/system）
            content: 内容
            **extra: 额外信息

        Returns:
            是否成功添加
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # 添加到会话历史
        history_item = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            **extra
        }
        session.history.append(history_item)
        session.last_active = time.time()
        
        return True

    def get_history(self,
                    session_id: str,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取历史记录

        Args:
            session_id: 会话ID
            limit: 限制返回的记录数

        Returns:
            历史记录列表
        """
        session = self.get_session(session_id)
        if not session:
            return []

        history = session.history
        if limit and limit > 0:
            history = history[-limit:]

        return history

    def _serializable_item(self, item):
        """
        将RunItem转换为可序列化格式
        
        Args:
            item: RunItem实例
            
        Returns:
            可序列化的字典
        """
        try:
            # 基本属性
            result = {
                "id": getattr(item, "id", None),
                "type": getattr(item, "type", None),
                "timestamp": getattr(item, "timestamp", None),
            }
            
            # 处理特定类型的项
            if hasattr(item, "message") and getattr(item, "message", None):
                result["message"] = {
                    "role": getattr(item.message, "role", None),
                    "content": getattr(item.message, "content", None)
                }
                
            if hasattr(item, "tool_calls") and getattr(item, "tool_calls", None):
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "name": tc.name,
                        "args": tc.args,
                        "result": tc.result
                    } 
                    for tc in item.tool_calls if hasattr(tc, "id")
                ]
                
            return result
        except Exception as e:
            logger.warning(f"序列化RunItem失败: {e}")
            return {"error": str(e)}

    def _prepare_context(self, context: Any, session_id: str) -> Any:
        """
        准备上下文对象，遵循OpenAI Agent SDK设计理念
        
        Args:
            context: 原始上下文对象，如果为None则创建新的上下文
            session_id: 会话ID，用于获取历史记录
            
        Returns:
            上下文对象，作为依赖注入容器传递给工具函数和回调
        """
        # 如果已提供上下文，直接使用
        if context is not None:
            # 确保session_id同步
            if hasattr(context, "session_id") and not context.session_id:
                context.session_id = session_id
            
            # 记录上下文类型和内容摘要，用于调试
            context_summary = {
                "type": type(context).__name__,
                "has_user_info": hasattr(context, "user_id") and hasattr(context, "user_name"),
                "has_metadata": hasattr(context, "metadata") and bool(getattr(context, "metadata", None)),
                "session_id": session_id
            }
            logger.debug(f"使用提供的上下文: {context_summary}")
            
            return context
        
        # 创建新的上下文对象
        session = self.get_session(session_id)
        if not session:
            # 如果会话不存在，创建一个基本的上下文
            logger.warning(f"会话不存在: {session_id}，创建基本上下文")
            return AgentContext(session_id=session_id)
        
        # 使用会话信息创建上下文
        # 提取更多元数据
        metadata = {}
        if hasattr(session, "metadata") and session.metadata:
            if isinstance(session.metadata, dict):
                metadata = session.metadata.copy()
            else:
                # 尝试从session.metadata对象中提取属性
                for attr in dir(session.metadata):
                    if not attr.startswith('_') and not callable(getattr(session.metadata, attr)):
                        try:
                            metadata[attr] = getattr(session.metadata, attr)
                        except Exception as e:
                            logger.warning(f"无法提取元数据属性 {attr}: {e}")
        
        # 提取用户名
        user_name = metadata.get("user_name", "用户") if metadata else "用户"
        
        # 创建包含用户信息和会话历史的上下文对象
        agent_context = AgentContext(
            user_id=session.user_id or "anonymous",
            user_name=user_name,
            session_id=session_id,
            metadata=metadata,
            created_at=session.created_at if hasattr(session, "created_at") else time.time(),
            last_active=session.last_active if hasattr(session, "last_active") else time.time()
        )
        
        # 从会话历史填充消息
        if hasattr(session, "history") and session.history:
            for item in session.history:
                if isinstance(item, dict) and item.get("role") in ["user", "assistant", "system", "tool"]:
                    agent_context.add_message(
                        item.get("role"),
                        item.get("content", ""),
                        **{k: v for k, v in item.items() if k not in ["role", "content"]}
                    )
        
        # 设置RBAC相关权限
        if hasattr(session, "roles") and session.roles:
            # 基于角色设置权限
            is_admin = Role.ADMIN.value in session.roles
            is_developer = Role.DEVELOPER.value in session.roles
            
            agent_context.set_permission("web_search", True)  # 所有用户都可以使用网络搜索
            agent_context.set_permission("file_access", is_developer or is_admin)  # 开发者和管理员可以访问文件
            agent_context.set_permission("system_access", is_admin)  # 只有管理员可以访问系统
        
        # 记录创建的上下文摘要
        logger.debug(f"创建新上下文: user_id={agent_context.user_id}, user_name={agent_context.user_name}, metadata_keys={list(agent_context.metadata.keys() if agent_context.metadata else [])}")
        
        return agent_context

    async def run_agent(self,
                        session_id: Optional[str] = None,
                        input_text: str = "",
                        template_name: Optional[str] = None,
                        agent: Optional[Agent] = None,
                        context: Any = None,
                        config: Optional[RunConfig] = None,
                        system_message: Optional[str] = None,
                        api_key: Optional[str] = None,
                        jwt_token: Optional[str] = None) -> Dict[str, Any]:
        """
        异步执行代理 (对应Runner.run)
        
        Args:
            session_id: 会话ID，如果为None则创建新会话
            input_text: 输入文本
            template_name: 代理模板名称（如果agent为None，则使用此模板创建代理）
            agent: 代理实例，如果提供则直接使用
            context: 上下文对象，仅提供给工具函数使用，不传递给LLM
            config: 运行配置
            system_message: 可选的系统消息，如果提供则直接设置为代理指令
            api_key: API密钥，用于认证
            jwt_token: JWT令牌，用于认证

        Returns:
            执行结果
        """
        if not session_id:
            session_id = self.create_session()
        # 获取或创建会话
        else:
            session = self.get_session(session_id)
            if not session:
                session_id = self.create_session()

        # 记录用户输入
        self.add_history_item(session_id, "user", input_text)

        # 准备上下文
        prepared_context = self._prepare_context(context, session_id)
        
        # 安全检查
        if self.security_service is not None:
            try:
                # 提取用户身份和权限信息
                user_id = None
                if hasattr(prepared_context, "user_id"):
                    user_id = prepared_context.user_id
                elif isinstance(prepared_context, dict) and "user_id" in prepared_context:
                    user_id = prepared_context["user_id"]
                
                # 认证检查
                auth_result = None
                if api_key or jwt_token:
                    auth_result = self.security_service.authenticate(api_key=api_key, jwt_token=jwt_token)
                    if not auth_result.success:
                        return {"error": f"认证失败: {auth_result.error}", "status": "failed", "success": False}
                    
                    # 更新上下文中的用户信息
                    user_id = auth_result.subject_id
                    if isinstance(prepared_context, dict):
                        prepared_context["user_id"] = user_id
                        prepared_context["roles"] = auth_result.roles
                        prepared_context["permissions"] = auth_result.permissions
                    else:
                        prepared_context.user_id = user_id
                        prepared_context.roles = auth_result.roles
                        prepared_context.permissions = auth_result.permissions
                    
                    # 更新会话上下文
                    session = self.get_session(session_id)
                    if session:
                        session.user_id = user_id
                        session.roles = auth_result.roles
                        session.permissions = auth_result.permissions
                        
                # 代理权限检查
                if auth_result and agent:
                    required_permission = self._safely_get_agent_property(agent, "required_permission", "agent.execute")
                    if not auth_result.has_permission(required_permission):
                        return {"error": f"权限不足: 需要 {required_permission} 权限", "status": "permission_denied", "success": False}
                
                # 内容安全检查
                if input_text:
                    content_check = self.security_service.check_content(input_text)
                    if content_check and hasattr(content_check, "safe_to_use") and not content_check.safe_to_use:
                        if hasattr(content_check, "filtered_content") and content_check.filtered_content:
                            input_text = content_check.filtered_content
                            logger.warning(f"输入内容已过滤，包含敏感内容")
                        else:
                            return {"error": "输入内容包含不允许的敏感信息", "status": "content_blocked", "success": False}
                
                # 频率限制检查
                if user_id and not self.security_service.check_rate_limit(user_id, "model"):
                    return {"error": "请求频率超限，请稍后再试", "status": "rate_limited", "success": False}
                
                # 资源配额检查 (简单估计token数量)
                if user_id:
                    tokens_estimate = len(input_text.split()) * 1.5
                    if not self.security_service.check_resource_quota(user_id, "model_tokens", int(tokens_estimate)):
                        return {"error": "资源配额不足", "status": "quota_exceeded", "success": False}
            except Exception as e:
                logger.error(f"安全检查失败: {str(e)}")
                # 安全检查失败时，根据配置决定是否继续执行
                if getattr(config, "strict_security", False):
                    return {"error": f"安全检查失败: {str(e)}", "status": "security_error", "success": False}
        
        # 从上下文中提取用户信息，用于增强系统消息
        user_info = {}
        if hasattr(prepared_context, "user_id"):
            user_info["user_id"] = prepared_context.user_id
        if hasattr(prepared_context, "user_name"):
            user_info["user_name"] = prepared_context.user_name
        if hasattr(prepared_context, "metadata") and prepared_context.metadata:
            user_info["metadata"] = prepared_context.metadata
        
        # 增强系统消息，添加用户信息
        enhanced_system_message = system_message
        if user_info:
            # 如果已有系统消息，在其基础上添加用户信息
            if enhanced_system_message:
                enhanced_system_message = f"{enhanced_system_message}\n\n用户信息:\n"
            else:
                enhanced_system_message = "用户信息:\n"
            
            # 添加用户ID和名称
            if "user_id" in user_info:
                enhanced_system_message += f"- 用户ID: {user_info['user_id']}\n"
            if "user_name" in user_info:
                enhanced_system_message += f"- 用户名称: {user_info['user_name']}\n"
            
            # 添加重要元数据
            if "metadata" in user_info and isinstance(user_info["metadata"], dict):
                important_fields = ["preference", "language", "role", "permission_level"]
                for field in important_fields:
                    if field in user_info["metadata"]:
                        enhanced_system_message += f"- {field}: {user_info['metadata'][field]}\n"
            
            logger.info(f"增强的系统消息: {enhanced_system_message[:100]}...")

        # 准备代理实例
        if agent is None and template_name:
            try:
                # 从模板管理器获取模板，传递增强的系统消息
                agent = template_manager.get_template(
                    template_name,
                    system_message=enhanced_system_message  # 使用增强的系统消息
                )
                if not agent:
                    logger.error(f"模板不存在: {template_name}")
                    return {
                        "session_id": session_id,
                        "input": input_text,
                        "output": None,
                        "success": False,
                        "error": f"代理模板不存在: {template_name}"
                    }
            except Exception as e:
                logger.error(f"创建代理失败: {e}")
                return {
                    "session_id": session_id,
                    "input": input_text,
                    "output": None,
                    "success": False,
                    "error": f"代理模板不存在: {template_name}"
                }
        # 如果已提供agent但同时也提供了系统消息，使用增强的系统消息覆盖指令
        elif agent and enhanced_system_message:
            agent = agent.clone(instructions=enhanced_system_message)
            logger.info(f"使用增强的系统消息覆盖代理指令: {enhanced_system_message[:50]}...")

        if agent is None:
            logger.error("未提供代理实例或有效的模板名称")
            return {
                "session_id": session_id,
                "input": input_text,
                "output": None,
                "success": False,
                "error": "未指定代理"
            }

        # 准备运行配置
        run_config = config or self.default_config
        
        # 准备输入消息 - 从上下文或历史中获取
        input_messages = []
        
        # 从SimpleContext中提取非系统消息
        if hasattr(prepared_context, "messages") and prepared_context.messages:
            for msg in prepared_context.messages:
                if msg.get("role") != "system":  # 忽略系统消息，现在通过agent.instructions传递
                    # 只保留role和content字段，防止未处理的字段类型错误
                    input_messages.append({
                        "role": msg.get("role"),
                        "content": msg.get("content", "")
                    })
        
        # 如果没有从SimpleContext中找到消息，尝试从会话历史获取
        if not input_messages:
            history = self.get_history(session_id)
            for item in history:
                if item.get("role") != "system":  # 忽略系统消息
                    # 只保留role和content字段，防止未处理的字段类型错误
                    input_messages.append({
                        "role": item.get("role"),
                        "content": item.get("content", "")
                    })
        
        # 确保当前输入被添加到消息列表的最后
        if input_text and (not input_messages or input_messages[-1].get("content") != input_text):
            input_messages.append({
                "role": "user",
                "content": input_text
            })
        
        # 记录传递给代理的上下文，用于调试
        debug_context = {
            "has_messages": hasattr(prepared_context, "messages"),
            "message_count": len(getattr(prepared_context, "messages", [])),
            "user_info": {"user_id": getattr(prepared_context, "user_id", None), 
                        "user_name": getattr(prepared_context, "user_name", None)}
        }
        logger.debug(f"代理上下文: {debug_context}")

        try:
            logger.info("准备运行代理,直接使用Runner.run...")
            
            # 使用OpenAIAgentAdapter预处理上下文，确保handoff对象的类型安全
            adapter = OpenAIAgentAdapter()
            prepared_context = adapter.pre_run_hook(prepared_context)
            logger.info("已应用代理预处理钩子，确保handoff对象类型安全")
            
            # 直接使用Runner.run，移除复杂的预处理
            result = await Runner.run(
                starting_agent=agent,
                input=input_messages if input_messages else input_text,
                context=prepared_context,
                run_config=run_config
            )
            
            # 记录代理输出
            self.add_history_item(session_id, "assistant", result.final_output)
            
            # 转换结果为可序列化格式
            result_dict = {
                "session_id": session_id,
                "input": input_text,
                "output": str(result.final_output) if result.final_output else None,
                "success": True,
                "items": []  # 保持简单的输出结构
            }
            
            # 添加handoff_result项
            if hasattr(result, "new_items") and result.new_items:
                # 提取items，简化版本
                for item in result.new_items:
                    if hasattr(item, "type"):
                        if item.type == "handoff_result":
                            # 处理handoff结果
                            if hasattr(item, "content") and item.content:
                                # 添加handoff结果到输出
                                result_dict["items"].append({
                                    "type": "handoff_result",
                                    "content": {
                                        "body": item.content.body if hasattr(item.content, "body") else "", 
                                        "agent_name": item.content.agent_name if hasattr(item.content, "agent_name") else ""
                                    }
                                })
            
            return result_dict

        except Exception as e:
            logger.error(f"代理执行错误: {e}")
            return {
                "session_id": session_id,
                "input": input_text,
                "output": None,
                "success": False,
                "error": str(e)
            }

    async def stream_agent(self,
                        session_id: Optional[str] = None,
                        input_text: str = "",
                        template_name: Optional[str] = None,
                        agent: Optional[Agent] = None,
                        context: Any = None,
                        config: Optional[RunConfig] = None,
                        system_message: Optional[str] = None,
                        api_key: Optional[str] = None,
                        jwt_token: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式执行代理
        
        Args:
            session_id: 会话ID，如果为None则创建新会话
            input_text: 输入文本
            template_name: 代理模板名称（如果agent为None，则使用此模板创建代理）
            agent: 代理实例，如果提供则直接使用
            context: 上下文对象，仅提供给工具函数使用
            config: 运行配置
            system_message: 可选的系统消息，如果提供则直接设置为代理指令
            api_key: API密钥，用于认证
            jwt_token: JWT令牌，用于认证
            
        Yields:
            流式执行结果，包含事件类型和数据
        """
        # 获取或创建会话
        if session_id:
            session = self.get_session(session_id)
            if not session:
                session_id = self.create_session()
        else:
            session_id = self.create_session()

        # 记录用户输入
        self.add_history_item(session_id, "user", input_text)

        # 准备代理实例
        if agent is None and template_name:
            try:
                # 从模板管理器获取模板，传递系统消息
                agent = template_manager.get_template(
                    template_name,
                    system_message=system_message  # 如果提供了系统消息，传递给模板管理器
                )
                if not agent:
                    logger.error(f"模板不存在: {template_name}")
                    yield {
                        "event_type": "error",
                        "data": {"error": f"代理模板不存在: {template_name}"}
                    }
                    return
            except Exception as e:
                logger.error(f"创建代理失败: {e}")
                yield {
                    "event_type": "error",
                    "data": {"error": f"创建代理失败: {str(e)}"}
                }
                return
        # 如果已提供agent但同时也提供了system_message，使用系统消息覆盖指令
        elif agent and system_message:
            agent = agent.clone(instructions=system_message)
            logger.info(f"使用提供的系统消息覆盖代理指令: {system_message[:50]}...")

        if agent is None:
            logger.error("未提供代理实例或有效的模板名称")
            yield {
                "event_type": "error",
                "data": {"error": "未指定代理"}
            }
            return

        # 准备运行配置
        run_config = config or self.default_config

        # 准备上下文
        conversation_context = self._prepare_context(context, session_id)
        
        # 安全检查
        if self.security_service is not None:
            try:
                # 提取用户身份和权限信息
                user_id = None
                if hasattr(conversation_context, "user_id"):
                    user_id = conversation_context.user_id
                elif isinstance(conversation_context, dict) and "user_id" in conversation_context:
                    user_id = conversation_context["user_id"]
                
                # 认证检查
                auth_result = None
                if api_key or jwt_token:
                    auth_result = self.security_service.authenticate(api_key=api_key, jwt_token=jwt_token)
                    if not auth_result.success:
                        yield {"error": f"认证失败: {auth_result.error}", "status": "failed", "success": False}
                        return
                    
                    # 更新上下文中的用户信息
                    user_id = auth_result.subject_id
                    if isinstance(conversation_context, dict):
                        conversation_context["user_id"] = user_id
                        conversation_context["roles"] = auth_result.roles
                        conversation_context["permissions"] = auth_result.permissions
                    else:
                        conversation_context.user_id = user_id
                        conversation_context.roles = auth_result.roles
                        conversation_context.permissions = auth_result.permissions
                    
                    # 更新会话上下文
                    session = self.get_session(session_id)
                    if session:
                        session.user_id = user_id
                        session.roles = auth_result.roles
                        session.permissions = auth_result.permissions
                        
                # 代理权限检查
                if auth_result and agent:
                    required_permission = self._safely_get_agent_property(agent, "required_permission", "agent.execute")
                    if not auth_result.has_permission(required_permission):
                        yield {"error": f"权限不足: 需要 {required_permission} 权限", "status": "permission_denied", "success": False}
                        return
                
                # 内容安全检查
                if input_text:
                    content_check = self.security_service.check_content(input_text)
                    if content_check and hasattr(content_check, "safe_to_use") and not content_check.safe_to_use:
                        if hasattr(content_check, "filtered_content") and content_check.filtered_content:
                            input_text = content_check.filtered_content
                            logger.warning(f"输入内容已过滤，包含敏感内容")
                        else:
                            yield {"error": "输入内容包含不允许的敏感信息", "status": "content_blocked", "success": False}
                            return
                
                # 频率限制检查
                if user_id and not self.security_service.check_rate_limit(user_id, "model"):
                    yield {"error": "请求频率超限，请稍后再试", "status": "rate_limited", "success": False}
                    return
                
                # 资源配额检查 (简单估计token数量)
                if user_id:
                    tokens_estimate = len(input_text.split()) * 1.5
                    if not self.security_service.check_resource_quota(user_id, "model_tokens", int(tokens_estimate)):
                        yield {"error": "资源配额不足", "status": "quota_exceeded", "success": False}
                        return
            except Exception as e:
                logger.error(f"安全检查失败: {str(e)}")
                # 安全检查失败时，根据配置决定是否继续执行
                if getattr(run_config, "strict_security", False):
                    yield {"error": f"安全检查失败: {str(e)}", "status": "security_error", "success": False}
                    return
        
        # 使用OpenAIAgentAdapter预处理上下文，确保handoff对象的类型安全
        adapter = OpenAIAgentAdapter()
        conversation_context = adapter.pre_run_hook(conversation_context)
        logger.info("已应用代理预处理钩子，确保handoff对象类型安全")
        
        # 准备输入消息 - 从上下文或历史中获取
        input_messages = []
        
        # 从SimpleContext中提取非系统消息
        if hasattr(conversation_context, "messages") and conversation_context.messages:
            for msg in conversation_context.messages:
                if msg.get("role") != "system":  # 忽略系统消息，现在通过agent.instructions传递
                    # 只保留role和content字段，防止未处理的字段类型错误
                    input_messages.append({
                        "role": msg.get("role"),
                        "content": msg.get("content", "")
                    })
        
        # 如果没有从SimpleContext中找到消息，尝试从会话历史获取
        if not input_messages:
            history = self.get_history(session_id)
            for item in history:
                if item.get("role") != "system":  # 忽略系统消息
                    # 只保留role和content字段，防止未处理的字段类型错误
                    input_messages.append({
                        "role": item.get("role"),
                        "content": item.get("content", "")
                    })
        
        # 确保当前输入被添加到消息列表的最后
        if input_text and (not input_messages or input_messages[-1].get("content") != input_text):
            input_messages.append({
                "role": "user",
                "content": input_text
            })
        
        # 记录传递给代理的上下文，用于调试
        debug_context = {
            "has_messages": hasattr(conversation_context, "messages"),
            "message_count": len(getattr(conversation_context, "messages", [])),
            "user_info": {"user_id": getattr(conversation_context, "user_id", None), 
                          "user_name": getattr(conversation_context, "user_name", None)}
        }
        logger.debug(f"流式代理上下文(stream_agent): {debug_context}")

        try:
            logger.info("准备运行代理,直接使用Runner.run...")
            # 直接使用Runner.run，移除复杂的预处理
            result = await Runner.run(
                starting_agent=agent,
                input=input_messages if input_messages else input_text,
                context=conversation_context,
                run_config=run_config
            )
            
            # 记录代理输出
            self.add_history_item(session_id, "assistant", result.final_output)
            
            # 转换结果为可序列化格式
            result_dict = {
                "session_id": session_id,
                "input": input_text,
                "output": str(result.final_output) if result.final_output else None,
                "success": True,
                "items": []  # 保持简单的输出结构
            }
            
            # 添加handoff_result项
            if hasattr(result, "new_items") and result.new_items:
                # 提取items，简化版本
                for item in result.new_items:
                    if hasattr(item, "type"):
                        if item.type == "handoff_result":
                            # 处理handoff结果
                            if hasattr(item, "content") and item.content:
                                # 添加handoff结果到输出
                                result_dict["items"].append({
                                    "type": "handoff_result",
                                    "content": {
                                        "body": item.content.body if hasattr(item.content, "body") else "", 
                                        "agent_name": item.content.agent_name if hasattr(item.content, "agent_name") else ""
                                    }
                                })
            
            # 将结果作为最后一个事件产生，而不是直接返回
            yield {
                "session_id": session_id,
                "event_type": "CompletionEvent",
                "data": result_dict,
                "done": True,
                "full_content": str(result.final_output) if result.final_output else ""
            }

        except Exception as e:
            logger.error(f"代理执行错误: {e}")
            error_message = str(e)

            # 记录错误
            self.add_history_item(
                session_id,
                "system",
                f"错误: {error_message}",
                error=True
            )

            # 发送错误事件
            yield {
                "session_id": session_id,
                "event_type": "ErrorEvent",
                "content": error_message,
                "done": True,
                "error": True
            }


# 创建全局运行时服务实例
runtime_service = RuntimeService()
