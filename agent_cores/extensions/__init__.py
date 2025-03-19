"""
扩展模块 - 为核心代理能力提供额外功能支持

该模块包含各种扩展功能，如代理间切换(Handoffs)、提示词生成工具、过滤器等，
扩展OpenAI Agent SDK的核心功能。
"""

# 导入handoffs相关组件
from agent_cores.extensions.handoffs import handoff, Handoff, HandoffInputData
from agent_cores.extensions.handoff_filters import (
    remove_all_tools,
    keep_user_messages_only,
    summarize_history,
    custom_filter
)
from agent_cores.extensions.handoff_prompt import (
    RECOMMENDED_PROMPT_PREFIX,
    prompt_with_handoff_instructions
)

# 导出所有组件
__all__ = [
    # Handoff核心功能
    'handoff',
    'Handoff',
    'HandoffInputData',
    
    # 过滤器
    'remove_all_tools',
    'keep_user_messages_only', 
    'summarize_history',
    'custom_filter',
    
    # 提示词工具
    'RECOMMENDED_PROMPT_PREFIX',
    'prompt_with_handoff_instructions'
] 