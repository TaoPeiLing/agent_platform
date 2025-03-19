"""
核心模块 - 提供代理运行时、模板管理和上下文处理等核心功能

包含以下主要组件:
- 运行时服务: 负责代理执行和会话管理
- 模板管理器: 负责加载和管理代理模板
- 上下文管理: 提供多种上下文处理方式
- 工厂函数: 用于创建代理和工具
"""

import logging
import sys

# 配置日志
logger = logging.getLogger(__name__)

# 导入核心组件
from agent_cores.core.factory import AgentFactory, agent_factory
from agent_cores.core.template_manager import TemplateManager, template_manager
from agent_cores.core.runtime import RuntimeService, runtime_service, SessionContext
from agent_cores.core.context_manager import ContextManager, context_manager
from agent_cores.core.simple_context import SimpleContext
from agent_cores.core.agent_context import AgentContext

# 导入Redis上下文管理器（如可用）
try:
    from agent_cores.core.redis_context_manager import redis_context_manager
    logger.info("已加载Redis上下文管理器")
except ImportError:
    logger.warning("Redis上下文管理器不可用，已跳过导入")
    redis_context_manager = None

# 定义扩展组件变量占位符
handoff = None
Handoff = None
HandoffInputData = None
remove_all_tools = None
keep_user_messages_only = None
summarize_history = None
custom_filter = None
RECOMMENDED_PROMPT_PREFIX = None
prompt_with_handoff_instructions = None

# 添加对扩展模块的导入，包括Handoffs支持
try:
    # 使用绝对导入从extensions模块导入组件
    from agent_cores.extensions import (
        handoff, Handoff, HandoffInputData,
        remove_all_tools, keep_user_messages_only, summarize_history, custom_filter,
        RECOMMENDED_PROMPT_PREFIX, prompt_with_handoff_instructions
    )
    logger.info("已成功加载Handoffs扩展模块")
except ImportError as e:
    logger.warning(f"Handoffs扩展模块导入失败: {str(e)}")

# 定义导出的组件列表
__all__ = [
    # 工厂相关
    'AgentFactory',
    'agent_factory',
    
    # 上下文相关
    'SimpleContext',
    'AgentContext',
    'ContextManager',
    'context_manager',
    
    # 模板相关 
    'TemplateManager',
    'template_manager',
    
    # 代理执行
    'RuntimeService',
    'runtime_service',
    'SessionContext',
]

# 添加Redis上下文管理器（如可用）
if redis_context_manager is not None:
    __all__.append('redis_context_manager')

# 添加扩展模块组件（如可用）
handoff_components = {
    'handoff': handoff,
    'Handoff': Handoff,
    'HandoffInputData': HandoffInputData,
    'remove_all_tools': remove_all_tools,
    'keep_user_messages_only': keep_user_messages_only,
    'summarize_history': summarize_history,
    'custom_filter': custom_filter,
    'RECOMMENDED_PROMPT_PREFIX': RECOMMENDED_PROMPT_PREFIX,
    'prompt_with_handoff_instructions': prompt_with_handoff_instructions
}

# 将可用的扩展组件添加到__all__
for name, component in handoff_components.items():
    if component is not None:
        __all__.append(name)