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


@dataclass
class SessionContext:
    """会话上下文数据"""
    session_id: str
    user_id: Optional[str] = None
    roles: List[str] = field(default_factory=lambda: [Role.USER.value])  # 默认为普通用户角色
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    history: List[Dict[str, Any]] = field(default_factory=list)


class RuntimeService:
    """
    运行时服务 - 管理代理执行和会话状态

    主要功能:
    1. 执行代理（同步/异步/流式）
    2. 会话状态管理
    3. 执行历史记录
    """

    def __init__(self, use_redis: Optional[bool] = None):
        """
        初始化运行时服务
        
        Args:
            use_redis: 是否使用Redis存储上下文，如果为None则使用环境变量或自动检测
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
                        system_message: Optional[str] = None) -> Dict[str, Any]:
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
        
        # 准备输入消息 - 使用AgentContext的to_api_messages方法
        input_messages = []
        
        # 如果上下文是AgentContext实例，使用其to_api_messages方法
        if isinstance(prepared_context, AgentContext):
            input_messages = prepared_context.to_api_messages(include_system=False)
            
            # 确保当前输入被添加到消息列表的最后
            if input_text:
                # 首先添加到上下文中
                prepared_context.add_message("user", input_text)
                # 重新获取API格式的消息
                input_messages = prepared_context.to_api_messages(include_system=False)
        else:
            # 兼容旧的SimpleContext和其他上下文类型
            if hasattr(prepared_context, "messages") and prepared_context.messages:
                for msg in prepared_context.messages:
                    if msg.get("role") != "system":  # 忽略系统消息，现在通过agent.instructions传递
                        input_messages.append(msg)
            
            # 如果没有从上下文中找到消息，尝试从会话历史获取
            if not input_messages:
                history = self.get_history(session_id)
                for item in history:
                    if item.get("role") != "system":  # 忽略系统消息
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
            
        logger.info(f"输入消息数量: {len(input_messages)}")
        
        try:
            # 执行代理
            logger.info("=============开始运行代理==============")
            # 添加详细的agent调试信息
            logger.info(f"代理类型: {type(agent)}")
            # 使用安全访问方法
            agent_name = self._safely_get_agent_property(agent, "name", "未知代理")
            logger.info(f"代理名称: {agent_name}")
            
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
            logger.error(f"执行代理出错: {str(e)}")
            return {
                "session_id": session_id,
                "input": input_text,
                "output": None,
                "success": False,
                "error": str(e)
            }

    def run_agent_sync(self,
                       session_id: Optional[str] = None,
                       input_text: str = "",
                       template_name: Optional[str] = None,
                       agent: Optional[Agent] = None,
                       context: Any = None,
                       config: Optional[RunConfig] = None,
                       system_message: Optional[str] = None) -> Dict[str, Any]:
        """
        同步执行代理 (对应Runner.run_sync) 适合脚本和简单应用
        
        注意: 此方法不应在异步上下文(如事件循环内)调用，
        在异步环境中请使用 run_agent 异步方法

        Args:
            session_id: 会话ID，如果为None则创建新会话
            input_text: 输入文本
            template_name: 代理模板名称（如果agent为None，则使用此模板创建代理）
            agent: 代理实例，如果提供则直接使用
            context: 上下文对象，仅提供给工具函数使用，不传递给LLM
            config: 运行配置
            system_message: 可选的系统消息，如果提供则直接设置为代理指令

        Returns:
            执行结果
        """
        # 检查是否在事件循环中运行
        try:
            loop = asyncio.get_running_loop()
            logger.warning("在异步上下文中调用同步方法run_agent_sync，这可能导致死锁")
            # 在异步上下文中不应使用同步方法，返回错误提示
            return {
                "session_id": session_id or self.create_session(),
                "input": input_text,
                "output": None,
                "success": False,
                "error": "在异步上下文(事件循环)中检测到同步调用。请改用run_agent异步方法，或在非异步环境中调用此方法。"
            }
        except RuntimeError:
            # 不在事件循环中，可以安全地使用同步方法
            pass
            
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
        # 如果已提供agent但同时也提供了system_message，使用系统消息覆盖指令
        elif agent and system_message:
            agent = agent.clone(instructions=system_message)
            logger.info(f"使用提供的系统消息覆盖代理指令: {system_message[:50]}...")

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
        
        # 准备上下文
        conversation_context = self._prepare_context(context, session_id)
        
        # 使用OpenAIAgentAdapter预处理上下文，确保handoff对象的类型安全
        adapter = OpenAIAgentAdapter()
        conversation_context = adapter.pre_run_hook(conversation_context)
        logger.info("已应用代理预处理钩子，确保handoff对象类型安全")
        
        # 执行代理
        logger.info("=============开始运行代理(同步)==============")
        # 添加详细的agent调试信息
        logger.info(f"代理类型: {type(agent)}")
        # 使用安全访问方法
        agent_name = self._safely_get_agent_property(agent, "name", "未知代理")
        logger.info(f"代理名称: {agent_name}")
        
        # 准备输入消息 - 从上下文或历史中获取
        input_messages = []
        
        # 从SimpleContext中提取非系统消息
        if hasattr(conversation_context, "messages") and conversation_context.messages:
            for msg in conversation_context.messages:
                if msg.get("role") != "system":  # 忽略系统消息，现在通过agent.instructions传递
                    input_messages.append(msg)
        
        # 如果没有从SimpleContext中找到消息，尝试从会话历史获取
        if not input_messages:
            history = self.get_history(session_id)
            for item in history:
                if item.get("role") != "system":  # 忽略系统消息
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
            
        logger.info(f"同步执行 - 输入消息数量: {len(input_messages)}")
        
        # 记录传递给代理的上下文，用于调试
        debug_context = {
            "has_messages": hasattr(conversation_context, "messages"),
            "message_count": len(getattr(conversation_context, "messages", [])),
            "user_info": {"user_id": getattr(conversation_context, "user_id", None), 
                         "user_name": getattr(conversation_context, "user_name", None)}
        }
        logger.debug(f"同步代理上下文: {debug_context}")

        try:
            # 使用OpenAIAgentAdapter预处理上下文，确保handoff对象的类型安全
            adapter = OpenAIAgentAdapter()
            conversation_context = adapter.pre_run_hook(conversation_context)
            logger.info("已应用代理预处理钩子，确保handoff对象类型安全")
            
            # 创建新的事件循环并在其中运行异步代码 - 简化版本
            import concurrent.futures
            
            def run_in_new_thread():
                # 创建新的事件循环
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                
                try:
                    # 使用OpenAIAgentAdapter预处理上下文，确保handoff对象的类型安全
                    # 注意：这里不需要重复处理上下文，直接使用外部已处理的conversation_context
                    # adapter = OpenAIAgentAdapter()
                    # conversation_context = adapter.pre_run_hook(conversation_context)
                    logger.info("在新线程中使用已预处理的上下文，确保handoff对象类型安全")
                    
                    # 在新的事件循环中运行异步代码
                    return new_loop.run_until_complete(
                        Runner.run(
                            starting_agent=agent,
                            input=input_messages if input_messages else input_text,  # 使用消息历史或文本 
                            context=conversation_context,
                            run_config=run_config
                        )
                    )
                finally:
                    # 确保关闭事件循环
                    new_loop.close()
            
            # 使用线程池运行
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_thread)
                result = future.result()  # 阻塞等待结果

            # 记录代理输出
            final_output = result.final_output
            self.add_history_item(session_id, "assistant", final_output)

            # 转换结果为可序列化格式
            result_dict = {
                "session_id": session_id,
                "input": input_text,
                "output": str(result.final_output) if result.final_output else None,
                "success": True,
                "items": [self._serializable_item(item) for item in result.new_items] if hasattr(self, "_serializable_item") else []
            }

            return result_dict

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

            # 构建错误返回
            return {
                "session_id": session_id,
                "input": input_text,
                "output": None,
                "success": False,
                "error": error_message
            }

    async def run_agent_streamed(self,
                                 session_id: Optional[str] = None,
                                 input_text: str = "",
                                 template_name: Optional[str] = None,
                                 agent: Optional[Agent] = None,
                                 context: Any = None,
                                 config: Optional[RunConfig] = None,
                                 system_message: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式执行代理（对应Runner.run_streamed方法）

        使用OpenAI Agent SDK的流式功能直接获取并传递响应内容。
        
        Args:
            session_id: 会话ID，如果为None则创建新会话
            input_text: 输入文本
            template_name: 代理模板名称（如果agent为None，则使用此模板创建代理）
            agent: 代理实例，如果提供则直接使用
            context: 上下文对象，仅提供给工具函数使用
            config: 运行配置
            system_message: 可选的系统消息，如果提供则直接设置为代理指令
            
        Yields:
            流式执行结果，包含文本块
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
                        "session_id": session_id,
                        "type": "error",
                        "error": f"代理模板不存在: {template_name}",
                        "done": True
                    }
                    return
            except Exception as e:
                logger.error(f"创建代理失败: {e}")
                yield {
                    "session_id": session_id,
                    "type": "error",
                    "error": f"代理模板不存在: {template_name}",
                    "done": True
                }
                return
        # 如果已提供agent但同时也提供了system_message，使用系统消息覆盖指令
        elif agent and system_message:
            agent = agent.clone(instructions=system_message)
            logger.info(f"使用提供的系统消息覆盖代理指令: {system_message[:50]}...")

        if agent is None:
            logger.error("未提供代理实例或有效的模板名称")
            yield {
                "session_id": session_id,
                "type": "error",
                "error": "未指定代理",
                "done": True
            }
            return

        # 准备运行配置
        run_config = config or self.default_config

        # 准备上下文
        conversation_context = self._prepare_context(context, session_id)
        
        # 准备输入消息 - 从上下文或历史中获取
        input_messages = []
        
        # 从SimpleContext中提取非系统消息
        if hasattr(conversation_context, "messages") and conversation_context.messages:
            for msg in conversation_context.messages:
                if msg.get("role") != "system":  # 忽略系统消息，现在通过agent.instructions传递
                    input_messages.append(msg)
        
        # 如果没有从SimpleContext中找到消息，尝试从会话历史获取
        if not input_messages:
            history = self.get_history(session_id)
            for item in history:
                if item.get("role") != "system":  # 忽略系统消息
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
        logger.debug(f"流式代理上下文: {debug_context}")

        try:
            logger.info("准备运行代理,run_streamed获取流式结果对象...")
            
            # 使用OpenAIAgentAdapter预处理上下文，确保handoff对象的类型安全
            adapter = OpenAIAgentAdapter()
            conversation_context = adapter.pre_run_hook(conversation_context)
            logger.info("已应用代理预处理钩子，确保handoff对象类型安全")
            
            # 使用Runner.run_streamed获取流式结果对象
            streamed_result = Runner.run_streamed(
                starting_agent=agent,
                input=input_messages if input_messages else input_text,  # 使用消息历史或文本
                context=conversation_context,  # 上下文仅提供给工具函数
                run_config=run_config
            )
            
            # 收集完整输出用于历史记录
            full_content = ""
            has_yielded_content = False
            
            # 流式事件处理
            async for event in streamed_result.stream_events():
                # 尝试提取并处理事件内容
                try:
                    # 如果事件有类型属性
                    if hasattr(event, "type"):
                        # 1. 处理raw_response_event类型 - 这是主要文本内容来源
                        if event.type == "raw_response_event":
                            if hasattr(event, "data") and hasattr(event.data, "delta"):
                                if event.data.type == "response.function_call_arguments.delta":
                                    pass
                                else:
                                    delta = event.data.delta
                                    full_content += delta
                                    has_yielded_content = True
                                    # 发送文本块
                                    yield {
                                        "session_id": session_id,
                                        "type": "content",
                                        "content": delta,
                                        "done": False
                                    }

                        # 2. 处理content_block_delta类型 - 备用文本内容来源
                        elif event.type == "content_block_delta":
                            if hasattr(event, "delta") and hasattr(event.delta, "text"):
                                chunk = event.delta.text
                                full_content += chunk
                                has_yielded_content = True

                                # 发送文本块
                                yield {
                                    "session_id": session_id,
                                    "type": "content",
                                    "content": chunk,
                                    "done": False
                                }

                        # 3. 处理tool_call类型事件 - 可能包含非文本结果
                        elif event.type == "tool_call":
                            # 工具调用可能不直接生成文本内容，但我们记录这个事件发生了
                            pass

                    # 如果事件可以序列化为字典，直接尝试获取内容
                    elif hasattr(event, "__dict__"):
                        event_dict = event.__dict__
                        logger.debug(f"事件字典: {event_dict}")
                        # 尝试从其他类型的事件中提取内容
                        if "content" in event_dict and event_dict["content"]:
                            chunk = str(event_dict["content"])
                            full_content += chunk
                            has_yielded_content = True

                            # 发送文本块
                            yield {
                                "session_id": session_id,
                                "type": "content",
                                "content": chunk,
                                "done": False
                            }

                    # 如果事件是字符串，直接使用
                    elif isinstance(event, str) and event:
                        full_content += event
                        has_yielded_content = True

                        # 发送文本块
                        yield {
                            "session_id": session_id,
                            "type": "content",
                            "content": event,
                            "done": False
                        }

                    # 通用处理 - 尝试将任何事件转换为字符串并获取
                    elif str(event) and str(event) != "None":
                        chunk = str(event)
                        full_content += chunk
                        has_yielded_content = True

                        # 发送文本块
                        yield {
                            "session_id": session_id,
                            "type": "content",
                            "content": chunk,
                            "done": False
                        }

                except Exception as e:
                    # 忽略单个事件处理失败，继续处理下一个事件
                    logger.warning(f"处理流式事件失败: {e}")
                    pass

            # 流式处理结束后，如果没有获取到任何内容，使用final_output
            if not has_yielded_content:
                # 等待任务完成以获取final_output
                if hasattr(streamed_result, "_run_impl_task"):
                    await streamed_result._run_impl_task

                # 检查是否有最终输出
                if hasattr(streamed_result, "final_output") and streamed_result.final_output:
                    final_output = str(streamed_result.final_output)
                    full_content = final_output

                    # 发送最终输出
                    yield {
                        "session_id": session_id,
                        "type": "content",
                        "content": final_output,
                        "done": False
                    }

            # 记录完整内容到历史
            if full_content:
                self.add_history_item(session_id, "assistant", full_content)

            # 发送完成事件
            yield {
                "session_id": session_id,
                "type": "done",
                "content": "",
                "done": True
            }

        except Exception as e:
            logger.error(f"代理流式执行错误: {e}")
            yield {
                "session_id": session_id,
                "type": "error",
                "content": str(e),
                "done": True
            }

    async def stream_agent(self,
                        session_id: Optional[str] = None,
                        input_text: str = "",
                        template_name: Optional[str] = None,
                        agent: Optional[Agent] = None,
                        context: Any = None,
                        config: Optional[RunConfig] = None,
                        system_message: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
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
                    input_messages.append(msg)
        
        # 如果没有从SimpleContext中找到消息，尝试从会话历史获取
        if not input_messages:
            history = self.get_history(session_id)
            for item in history:
                if item.get("role") != "system":  # 忽略系统消息
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
            logger.info("准备运行代理,run_streamed获取流式结果对象...")
            # 使用Runner.run_streamed获取流式结果对象
            streamed_result = Runner.run_streamed(
                starting_agent=agent,
                input=input_messages if input_messages else input_text,  # 使用消息历史或文本
                context=conversation_context,  # 上下文仅提供给工具函数
                run_config=run_config
            )
            
            # 收集完整输出用于历史记录
            full_content = ""
            
            # 处理流式结果
            async for event in streamed_result.stream_events():
                # 尝试提取并处理事件内容
                try:
                    # 如果事件有类型属性
                    if hasattr(event, "type"):
                        # 1. 处理raw_response_event类型 - 这是主要文本内容来源
                        if event.type == "raw_response_event":
                            if hasattr(event, "data") and hasattr(event.data, "delta"):
                                if event.data.type == "response.function_call_arguments.delta":
                                    pass
                                else:
                                    delta = event.data.delta
                                    full_content += delta
                                    # 发送文本块
                                    yield {
                                        "session_id": session_id,
                                        "event_type": "content",
                                        "content": delta,
                                        "done": False
                                    }

                        # 2. 处理content_block_delta类型 - 备用文本内容来源
                        elif event.type == "content_block_delta":
                            if hasattr(event, "delta") and hasattr(event.delta, "text"):
                                chunk = event.delta.text
                                full_content += chunk
                                # 发送文本块
                                yield {
                                    "session_id": session_id,
                                    "event_type": "content",
                                    "content": chunk,
                                    "done": False
                                }

                        # 3. 处理tool_call类型事件 - 可能包含非文本结果
                        elif event.type == "tool_call":
                            # 工具调用可能不直接生成文本内容，但我们记录这个事件发生了
                            pass

                    # 如果事件可以序列化为字典，直接尝试获取内容
                    elif hasattr(event, "__dict__"):
                        event_dict = event.__dict__
                        logger.debug(f"事件字典(stream_agent): {event_dict}")
                        # 尝试从其他类型的事件中提取内容
                        if "content" in event_dict and event_dict["content"]:
                            chunk = str(event_dict["content"])
                            full_content += chunk
                            # 发送文本块
                            yield {
                                "session_id": session_id,
                                "event_type": "content",
                                "content": chunk,
                                "done": False
                            }

                    # 如果事件是字符串，直接使用
                    elif isinstance(event, str) and event:
                        full_content += event
                        # 发送文本块
                        yield {
                            "session_id": session_id,
                            "event_type": "content",
                            "content": event,
                            "done": False
                        }

                    # 通用处理 - 尝试将任何事件转换为字符串并获取
                    elif str(event) and str(event) != "None":
                        chunk = str(event)
                        full_content += chunk
                        # 发送文本块
                        yield {
                            "session_id": session_id,
                            "event_type": "content",
                            "content": chunk,
                            "done": False
                        }

                except Exception as e:
                    # 忽略单个事件处理失败，继续处理下一个事件
                    logger.warning(f"处理流式事件失败(stream_agent): {e}")
                    pass

            # 记录完整输出到历史
            if full_content:
                self.add_history_item(session_id, "assistant", full_content)

            # 发送完成事件
            yield {
                "session_id": session_id,
                "event_type": "CompletionEvent",
                "content": None,
                "done": True,
                "full_content": full_content
            }

        except Exception as e:
            logger.error(f"代理流式执行错误: {e}")
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
