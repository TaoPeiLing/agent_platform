"""
Handoff过滤器模块 - 提供处理Handoff输入数据的常用过滤器

该模块包含各种预定义的过滤器函数，用于在代理间Handoff时
对历史数据进行过滤、修剪或转换，确保下一个代理获得最佳上下文信息。
"""

import logging
import functools
from typing import Any, Dict, List, Optional, Callable, Union, TypeVar, cast
from agent_cores.extensions.handoffs import HandoffInputData

# 配置日志
logger = logging.getLogger(__name__)


def safe_input_filter(filter_func: Callable) -> Callable:
    """
    装饰器：确保输入过滤器函数安全执行并返回正确类型
    
    装饰后的函数将会:
    1. 捕获所有异常
    2. 确保返回类型为HandoffInputData
    3. 如果失败则返回原始输入数据
    
    Args:
        filter_func: 原始过滤器函数
        
    Returns:
        安全包装后的过滤器函数
    """
    @functools.wraps(filter_func)
    def wrapper(data: Any) -> Any:
        try:
            # 导入类型
            from agents.handoffs import HandoffInputData as SDKHandoffInputData
            from agent_cores.extensions.handoffs import HandoffInputData as LocalHandoffInputData
            
            # 检查数据类型
            input_is_sdk = isinstance(data, SDKHandoffInputData)
            input_is_local = isinstance(data, LocalHandoffInputData)
            
            logger.debug(f"执行输入过滤器函数: {filter_func.__name__}, 输入类型: {type(data)}, SDK类型: {input_is_sdk}, 本地类型: {input_is_local}")
            
            # 执行过滤器函数
            result = filter_func(data)
            
            # 检查结果类型
            result_is_sdk = isinstance(result, SDKHandoffInputData)
            result_is_local = isinstance(result, LocalHandoffInputData)
            
            # 确保类型一致性
            if input_is_sdk and result_is_local:
                # 如果输入是SDK类型但返回是本地类型，转换回SDK类型
                logger.debug(f"将本地HandoffInputData结果转换回SDK类型")
                return SDKHandoffInputData(
                    input_history=result.input_history,
                    pre_handoff_items=result.pre_handoff_items,
                    new_items=result.new_items
                )
            elif input_is_local and result_is_sdk:
                # 如果输入是本地类型但返回是SDK类型，转换回本地类型
                logger.debug(f"将SDK HandoffInputData结果转换回本地类型")
                return LocalHandoffInputData(
                    input_history=result.input_history,
                    pre_handoff_items=result.pre_handoff_items,
                    new_items=result.new_items
                )
            elif not result_is_sdk and not result_is_local:
                # 如果返回类型既不是SDK也不是本地类型
                logger.warning(f"过滤器函数 {filter_func.__name__} 返回了错误类型: {type(result)}")
                # 尝试转换为适当的类型
                if hasattr(result, 'input_history'):
                    try:
                        if input_is_sdk:
                            return SDKHandoffInputData(
                                input_history=result.input_history,
                                pre_handoff_items=getattr(result, 'pre_handoff_items', ()),
                                new_items=getattr(result, 'new_items', ())
                            )
                        else:
                            return LocalHandoffInputData(
                                input_history=result.input_history,
                                pre_handoff_items=getattr(result, 'pre_handoff_items', ()),
                                new_items=getattr(result, 'new_items', ())
                            )
                    except Exception as e:
                        logger.error(f"转换结果类型失败: {str(e)}")
                # 返回原始数据
                return data
            
            # 返回结果
            return result
            
        except Exception as e:
            logger.error(f"执行过滤器函数 {filter_func.__name__} 时出错: {str(e)}")
            return data
    
    # 特殊标记，供检测使用
    wrapper._is_safe_input_filter = True
    return wrapper


def remove_all_tools(data: HandoffInputData) -> HandoffInputData:
    """
    移除所有工具调用结果
    
    此函数处理输入历史，确保不向下一个代理传递工具调用结果。
    它保留所有的用户消息和代理的文本响应。
    
    Args:
        data: 原始输入数据
        
    Returns:
        过滤后的输入数据
    """
    try:
        filtered_history = []
        
        # 处理输入历史
        if data.input_history:
            for item in data.input_history:
                # 保留用户消息
                if item.get('role') == 'user':
                    filtered_history.append(item)
                # 过滤助手消息，只保留文本内容
                elif item.get('role') == 'assistant':
                    # 创建新的消息，只保留content字段
                    filtered_item = {'role': 'assistant', 'content': item.get('content', '')}
                    filtered_history.append(filtered_item)
                # 保留系统消息
                elif item.get('role') == 'system':
                    filtered_history.append(item)
                    
        # 创建新的HandoffInputData
        return HandoffInputData(
            input_history=tuple(filtered_history),
            pre_handoff_items=data.pre_handoff_items,
            new_items=data.new_items
        )
    except Exception as e:
        logger.error(f"执行remove_all_tools过滤器出错: {str(e)}")
        return data


def keep_user_messages_only(handoff_data: HandoffInputData) -> HandoffInputData:
    """
    仅保留用户消息
    
    此过滤器只保留用户消息，删除所有助手回复和工具调用，
    适用于需要重新处理用户请求的场景。
    
    Args:
        handoff_data: Handoff输入数据
        
    Returns:
        修改后的Handoff输入数据
    """
    try:
        # 处理字符串历史
        if isinstance(handoff_data.input_history, str):
            # 对于字符串类型的历史，我们无法精确过滤，返回原始数据
            logger.warning("字符串类型的历史无法过滤非用户消息，返回原始数据")
            return handoff_data
            
        # 处理结构化历史
        filtered_history = []
        for item in handoff_data.input_history:
            # 仅保留用户消息
            if "role" in item and item["role"] == "user":
                filtered_history.append(item)
                    
        # 返回新的HandoffInputData
        return HandoffInputData(
            input_history=tuple(filtered_history),
            pre_handoff_items=handoff_data.pre_handoff_items,
            new_items=handoff_data.new_items
        )
    except Exception as e:
        logger.error(f"仅保留用户消息过滤器错误: {str(e)}")
        return handoff_data


def summarize_history(summary_prefix: str = "历史对话总结", max_messages: int = 3) -> Callable[[HandoffInputData], HandoffInputData]:
    """
    创建一个过滤器，将历史对话总结为一条系统消息
    
    此函数生成一个新的过滤器函数，它将:
    1. 保留最近的N条消息
    2. 将早于N条的消息总结为一条系统消息
    3. 设置总结消息的前缀
    
    Args:
        summary_prefix: 总结消息的前缀
        max_messages: 保留的最近消息数量
        
    Returns:
        过滤器函数
    """
    @safe_input_filter
    def filter_func(data: HandoffInputData) -> HandoffInputData:
        try:
            from agents.handoffs import HandoffInputData as SDKHandoffInputData
            from agent_cores.extensions.handoffs import HandoffInputData as LocalHandoffInputData
            
            # 检查数据类型
            input_is_sdk = isinstance(data, SDKHandoffInputData)
            input_is_local = isinstance(data, LocalHandoffInputData)
            
            logger.debug(f"summarize_history接收到数据类型: {type(data)}, SDK类型: {input_is_sdk}, 本地类型: {input_is_local}")
            
            # 如果历史消息数量不足，直接返回
            if not data.input_history or len(data.input_history) <= max_messages * 2:
                logger.info(f"历史消息数量不足 {max_messages*2}，不进行总结")
                return data
                
            # 分离最近的消息和历史消息
            recent_messages = list(data.input_history[-max_messages*2:])
            old_messages = list(data.input_history[:-max_messages*2])
            
            if not old_messages:
                logger.info("没有旧消息需要总结")
                return data
                
            # 创建总结消息
            summary = []
            for msg in old_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                if content:
                    summary.append(f"{role}: {content[:100]}...")
                    
            # 创建系统消息
            summary_msg = {
                'role': 'system',
                'content': f"{summary_prefix}:\n" + "\n".join(summary)
            }
            
            # 合并消息
            new_history = [summary_msg] + recent_messages
            
            logger.info(f"已总结 {len(old_messages)} 条历史消息, 保留 {len(recent_messages)} 条最近消息")
            
            # 根据输入类型返回相应类型的结果
            if input_is_sdk:
                return SDKHandoffInputData(
                    input_history=tuple(new_history),
                    pre_handoff_items=data.pre_handoff_items,
                    new_items=data.new_items
                )
            else:
                return LocalHandoffInputData(
                    input_history=tuple(new_history),
                    pre_handoff_items=data.pre_handoff_items,
                    new_items=data.new_items
                )
        except Exception as e:
            logger.error(f"执行summarize_history过滤器出错: {str(e)}")
            # 出错时返回原始数据
            return data
            
    # 添加额外的标识，便于调试和检测
    filter_func._filter_name = "summarize_history"
    filter_func._summary_prefix = summary_prefix
    filter_func._max_messages = max_messages
    
    return filter_func


def custom_filter(
    filter_func: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]
) -> Callable[[HandoffInputData], HandoffInputData]:
    """
    创建自定义过滤器
    
    允许用户提供自己的过滤函数来处理历史记录，
    提供最大的灵活性。
    
    Args:
        filter_func: 自定义过滤函数，接收消息列表并返回过滤后的消息列表
        
    Returns:
        处理HandoffInputData的过滤器函数
    """
    def wrapper(handoff_data: HandoffInputData) -> HandoffInputData:
        try:
            # 处理字符串历史
            if isinstance(handoff_data.input_history, str):
                # 对于字符串类型的历史，我们无法应用自定义过滤器，返回原始数据
                logger.warning("字符串类型的历史无法应用自定义过滤器，返回原始数据")
                return handoff_data
                
            # 处理结构化历史
            history_items = list(handoff_data.input_history)
            
            # 应用自定义过滤函数
            filtered_history = filter_func(history_items)
                    
            # 返回新的HandoffInputData
            return HandoffInputData(
                input_history=tuple(filtered_history),
                pre_handoff_items=handoff_data.pre_handoff_items,
                new_items=handoff_data.new_items
            )
        except Exception as e:
            logger.error(f"自定义过滤器错误: {str(e)}")
            return handoff_data
            
    return wrapper 