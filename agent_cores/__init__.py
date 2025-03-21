"""
Agent核心模块 - 提供代理管理、执行和扩展功能的核心组件

该模块包含以下主要组件:
- 核心运行时: 执行代理、管理会话和上下文
- 模板管理: 加载和管理代理模板
- 工具集: 提供各种工具供代理使用
- 扩展功能: 如Handoffs (代理间任务委托) 等高级特性
"""

# 版本信息
__version__ = "1.0.0"

# 从核心模块导入主要组件
from agent_cores.core import (
    runtime_service,
    template_manager,
    context_manager,
    SimpleContext,
    AgentContext
)

# 导入扩展模块
try:
    from agent_cores.extensions import (
        handoff, Handoff, HandoffInputData,
        remove_all_tools, keep_user_messages_only, summarize_history, custom_filter,
        RECOMMENDED_PROMPT_PREFIX, prompt_with_handoff_instructions
    )
except ImportError:
    # 扩展模块可能不可用
    pass

from . import connectors