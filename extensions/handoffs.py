"""
Handoffs模块 - 定义Handoff相关的基础类型和数据结构

该模块提供基于OpenAI Agent SDK的Handoffs机制的基础类型定义，
适用于代理间任务委托和切换的场景。
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Generic
from pydantic import BaseModel

# 导入OpenAI Agent SDK
from agents.items import RunItem, TResponseInputItem
# 从SDK中直接导入Handoff和handoff,用于重新导出
from agents import Handoff, handoff

# 配置日志
logger = logging.getLogger(__name__)

# 定义类型变量
TContext = TypeVar('TContext')
THandoffInput = TypeVar('THandoffInput')  # 可以接受任何类型


@dataclass(frozen=True)
class HandoffInputData:
    """
    Handoff输入数据 - 包含在执行handoff时传递给下一个代理的上下文信息
    
    可以被过滤函数修改以控制下一个代理能访问的历史记录内容
    """
    input_history: Union[str, tuple[TResponseInputItem, ...]]
    """
    执行Runner.run()前的输入历史
    """

    pre_handoff_items: tuple[RunItem, ...]
    """
    在触发handoff的代理轮次之前生成的项目
    """

    new_items: tuple[RunItem, ...]
    """
    当前代理轮次期间生成的新项目，包括触发handoff的项目
    """


# 定义HandoffInputFilter类型
HandoffInputFilter = Callable[[HandoffInputData], HandoffInputData]

# 导出类型，方便其他模块使用
__all__ = [
    'HandoffInputData', 
    'HandoffInputFilter', 
    'TContext', 
    'THandoffInput',
    'Handoff',
    'handoff'
] 