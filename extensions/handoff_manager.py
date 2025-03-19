"""
Handoff管理器 - 集中管理所有Handoff相关操作

该模块提供了一个中心化的管理器，负责管理所有Handoff配置、创建和执行操作，
确保Handoff功能的一致性和可靠性。
"""

import logging
import inspect
from typing import Any, Dict, List, Optional, Callable, Type, Union, TypeVar, cast
from dataclasses import dataclass

# 导入OpenAI Agent SDK
from agents import Agent, Handoff, handoff as sdk_handoff
from agents.run_context import RunContextWrapper

# 导入本地模块
from agent_cores.core.runtime import runtime_service
from agent_cores.extensions.handoffs import HandoffInputData
from agent_cores.extensions.agent_adapter import OpenAIAgentAdapter

# 配置日志
logger = logging.getLogger(__name__)

# 定义类型变量
TContext = TypeVar('TContext')
THandoffInput = TypeVar('THandoffInput')

# 定义回调函数类型
HandoffCallback = Callable[[RunContextWrapper[Any], Any], Any]


@dataclass
class HandoffConfig:
    """
    Handoff配置类 - 存储Handoff设置
    """
    name: str
    """Handoff名称"""
    
    target_agent: Agent
    """目标代理"""
    
    callback: Optional[HandoffCallback] = None
    """回调函数"""
    
    input_type: Optional[Type] = None
    """输入类型"""
    
    tool_name: Optional[str] = None
    """工具名称"""
    
    tool_description: Optional[str] = None
    """工具描述"""
    
    input_filter: Optional[Callable[[HandoffInputData], HandoffInputData]] = None
    """输入过滤器"""


class HandoffManager:
    """
    Handoff管理器 - 集中管理所有Handoff相关操作
    """
    def __init__(self):
        self._registered_handoffs: Dict[str, HandoffConfig] = {}
        self._handoff_objects: Dict[str, Handoff] = {}
        
    def register_handoff(
        self, 
        name: str, 
        agent: Agent, 
        callback: Optional[HandoffCallback] = None, 
        input_type: Optional[Type] = None, 
        tool_name: Optional[str] = None, 
        tool_description: Optional[str] = None,
        input_filter: Optional[Callable[[HandoffInputData], HandoffInputData]] = None
    ) -> HandoffConfig:
        """
        注册一个Handoff配置
        
        Args:
            name: Handoff名称
            agent: 目标代理
            callback: 回调函数
            input_type: 输入类型
            tool_name: 工具名称
            tool_description: 工具描述
            input_filter: 输入过滤器
            
        Returns:
            Handoff配置对象
        """
        config = HandoffConfig(
            name=name,
            target_agent=agent,
            callback=callback,
            input_type=input_type,
            tool_name=tool_name if tool_name else f"transfer_to_{name}",
            tool_description=tool_description,
            input_filter=input_filter
        )
        
        self._registered_handoffs[name] = config
        logger.info(f"注册Handoff配置: {name} -> {agent.name}")
        return config
    
    def get_handoff_object(self, name: str) -> Optional[Handoff]:
        """
        获取Handoff对象
        
        Args:
            name: Handoff名称
            
        Returns:
            Handoff对象，如果不存在则返回None
        """
        # 检查是否已创建
        if name in self._handoff_objects:
            return self._handoff_objects[name]
            
        # 检查配置是否存在
        if name not in self._registered_handoffs:
            logger.warning(f"Handoff配置不存在: {name}")
            return None
            
        # 创建新的Handoff对象
        config = self._registered_handoffs[name]
        
        try:
            # 安全包装input_filter
            safe_input_filter = self._ensure_safe_input_filter(config.input_filter, config.target_agent.name if hasattr(config.target_agent, 'name') else name)
            
            handoff_obj = sdk_handoff(
                agent=config.target_agent,
                on_handoff=config.callback,
                input_type=config.input_type,
                tool_name_override=config.tool_name,
                tool_description_override=config.tool_description,
                input_filter=safe_input_filter
            )
            
            # 存储并返回
            self._handoff_objects[name] = handoff_obj
            return handoff_obj
        except Exception as e:
            logger.error(f"创建Handoff对象失败: {name}, 错误: {str(e)}")
            return None
    
    def apply_handoffs_to_agent(self, agent: Agent, handoff_names: List[str]) -> Agent:
        """
        将指定的handoffs应用到代理
        
        Args:
            agent: 基础代理
            handoff_names: 要应用的Handoff名称列表
            
        Returns:
            配置好的代理
        """
        # 获取所有Handoff对象
        handoffs = []
        for name in handoff_names:
            handoff_obj = self.get_handoff_object(name)
            if handoff_obj:
                handoffs.append(handoff_obj)
            else:
                logger.warning(f"无法获取Handoff对象: {name}")
                
        if not handoffs:
            logger.warning(f"没有有效的Handoff对象应用到代理: {agent.name}")
            return agent
            
        # 使用适配器创建新的代理
        return OpenAIAgentAdapter.create_agent_with_handoffs(agent, handoffs)
    
    async def process_handoff_result(self, result: Dict[str, Any], context: Any, session_id: str) -> Dict[str, Any]:
        """
        处理Handoff执行结果
        
        Args:
            result: 执行结果
            context: 上下文
            session_id: 会话ID
            
        Returns:
            处理后的结果
        """
        # 检查是否有Handoff
        handoff_item = None
        for item in result.get('items', []):
            if item.get('type') == 'tool_call' and 'transfer_to_' in item.get('name', ''):
                handoff_item = item
                break
                
        # 如果没有Handoff，直接返回原结果
        if not handoff_item:
            return result
            
        logger.info(f"检测到Handoff: {handoff_item.get('name')}")
        
        # 确定专家类型
        item_name = handoff_item.get('name', '')
        
        # 查找匹配的Handoff配置
        target_agent = None
        matching_config = None
        
        # 首先根据tool_name匹配
        for name, config in self._registered_handoffs.items():
            if config.tool_name == item_name:
                matching_config = config
                target_agent = config.target_agent
                # 安全获取代理名称
                agent_name = self._get_safe_agent_name(target_agent)
                logger.info(f"找到匹配的Handoff配置: {name} -> {agent_name}")
                break
                
        # 如果找不到匹配的配置，尝试从名称推断
        if not target_agent:
            expert_type = None
            # 从名称推断专家类型
            if "travel" in item_name.lower():
                expert_type = "travel_agent"
            elif "finance" in item_name.lower():
                expert_type = "finance_agent"
            elif "customer" in item_name.lower():
                expert_type = "customer_service_agent"
                
            if expert_type:
                logger.info(f"通过名称推断专家类型: {expert_type}")
                # 尝试从模板获取
                from agent_cores.core.template_manager import template_manager
                target_agent = template_manager.get_template(expert_type)
                
        if not target_agent:
            logger.error(f"无法确定Handoff目标代理: {item_name}")
            return result
            
        # 安全获取代理名称
        agent_name = self._get_safe_agent_name(target_agent)
        logger.info(f"执行Handoff到: {agent_name}")
        
        # 构建专家系统消息
        try:
            from agent_cores.extensions.handoff_prompt import create_handoff_system_message
            system_message = create_handoff_system_message(
                target_agent_name=agent_name,
                reason=f"用户咨询{agent_name}相关问题"
            )
            
            # 安全克隆代理
            enhanced_expert = self._safely_clone_agent(target_agent, system_message)
            if not enhanced_expert:
                logger.error(f"无法克隆代理: {agent_name}")
                return result
            
            # 获取用户输入
            user_input = self._get_user_input(result, context)
            if not user_input:
                logger.warning("无法获取用户输入，使用默认消息")
                user_input = "请帮助我解决问题"
                
            # 执行专家代理
            expert_result = await runtime_service.run_agent(
                agent=enhanced_expert,
                input_text=user_input,
                session_id=session_id,
                context=context
            )
            
            # 将结果合并到原结果中
            result['handoff_result'] = {
                'expert': agent_name,
                'output': expert_result.get('output'),
                'success': expert_result.get('success', False)
            }
            
            # 更新输出
            if expert_result.get('success', False) and expert_result.get('output'):
                result['output'] = expert_result.get('output')
                
            return result
            
        except Exception as e:
            logger.error(f"处理Handoff结果时出错: {str(e)}")
            return result
            
    def _get_safe_agent_name(self, agent) -> str:
        """
        安全获取代理名称
        
        Args:
            agent: 代理对象，可能是Agent实例、字典或其他类型
            
        Returns:
            代理名称
        """
        try:
            # 如果是Agent对象
            if hasattr(agent, 'name'):
                return agent.name
            # 如果是字典
            elif isinstance(agent, dict) and 'name' in agent:
                return agent['name']
            # 如果是字典但使用agent_name
            elif isinstance(agent, dict) and 'agent_name' in agent:
                return agent['agent_name']
            # 如果有__str__方法
            elif hasattr(agent, '__str__'):
                return str(agent)
            # 默认返回
            return "unknown_expert"
        except Exception:
            return "unknown_expert"
            
    def _safely_clone_agent(self, agent, system_message):
        """
        安全克隆代理
        
        Args:
            agent: 要克隆的代理
            system_message: 系统消息
            
        Returns:
            克隆后的代理，失败则返回None
        """
        try:
            # 如果是Agent对象
            if hasattr(agent, 'clone'):
                return agent.clone(instructions=system_message)
                
            # 如果是字典或需要从模板获取
            agent_name = self._get_safe_agent_name(agent)
            from agent_cores.core.template_manager import template_manager
            base_agent = template_manager.get_template(agent_name)
            if base_agent:
                return base_agent.clone(instructions=system_message)
                
            return None
        except Exception as e:
            logger.error(f"克隆代理时出错: {str(e)}")
            return None
            
    def _get_user_input(self, result, context):
        """
        获取用户输入
        
        Args:
            result: 代理执行结果
            context: 上下文
            
        Returns:
            用户输入文本
        """
        try:
            # 首先尝试从结果中获取
            if 'input' in result and result['input']:
                return result['input']
                
            # 尝试从上下文获取
            if hasattr(context, 'get_last_user_message'):
                message = context.get_last_user_message()
                if message:
                    return message
                    
            # 尝试从上下文的messages属性获取
            if hasattr(context, 'messages') and context.messages:
                for msg in reversed(context.messages):
                    if msg.get('role') == 'user':
                        return msg.get('content', '')
                        
            return None
        except Exception:
            return None

    def _ensure_safe_input_filter(self, input_filter, agent_name="未知代理"):
        """
        确保输入过滤器是安全的函数，能正确处理和返回HandoffInputData对象
        
        Args:
            input_filter: 原始输入过滤器
            agent_name: 代理名称，用于日志
            
        Returns:
            包装后的安全输入过滤器
        """
        from agent_cores.extensions.handoffs import HandoffInputData
        import functools
        
        # 如果已为None，直接返回
        if input_filter is None:
            return None
            
        # 检查是否已经被safe_input_filter装饰
        if hasattr(input_filter, '_is_safe_input_filter') and input_filter._is_safe_input_filter:
            return input_filter
        
        # 检查是否为可调用函数
        if not callable(input_filter):
            logger.warning(f"{agent_name}: input_filter不是可调用函数，将被忽略")
            return None
            
        # 检查是否是summarize_history函数本身(未调用)
        from agent_cores.extensions.handoff_filters import summarize_history
        if input_filter is summarize_history or (hasattr(input_filter, '__name__') and input_filter.__name__ == 'summarize_history'):
            logger.info(f"{agent_name}: 检测到未初始化的summarize_history，初始化为默认配置")
            input_filter = summarize_history(f"为{agent_name}提供的历史对话总结", 2)
            
        # 检查是否是filter_func(已经初始化的内部函数)
        if hasattr(input_filter, '__name__') and input_filter.__name__ == 'filter_func':
            # 继续安全包装
            pass
        
        # 创建安全包装函数
        @functools.wraps(input_filter)
        def safe_filter(data):
            try:
                # 检查输入
                if not isinstance(data, HandoffInputData):
                    logger.warning(f"{agent_name}: input_filter接收到非HandoffInputData输入: {type(data)}")
                    # 尝试转换为HandoffInputData
                    if hasattr(data, 'input_history') and hasattr(data, 'new_items'):
                        data = HandoffInputData(
                            input_history=data.input_history,
                            pre_handoff_items=getattr(data, 'pre_handoff_items', ()),
                            new_items=getattr(data, 'new_items', ())
                        )
                    else:
                        # 无法转换，创建空数据
                        logger.error(f"{agent_name}: 无法将输入转换为HandoffInputData，创建空数据")
                        data = HandoffInputData(input_history=(), pre_handoff_items=(), new_items=())
                
                # 执行原始过滤器
                logger.info(f"{agent_name}: 执行input_filter")
                result = input_filter(data)
                
                # 检查结果
                if not isinstance(result, HandoffInputData):
                    logger.warning(f"{agent_name}: input_filter返回非HandoffInputData结果: {type(result)}")
                    
                    # 尝试转换为HandoffInputData
                    if hasattr(result, 'input_history'):
                        logger.info(f"{agent_name}: 尝试从结果创建HandoffInputData")
                        try:
                            return HandoffInputData(
                                input_history=result.input_history,
                                pre_handoff_items=getattr(result, 'pre_handoff_items', ()),
                                new_items=getattr(result, 'new_items', ())
                            )
                        except Exception as e:
                            logger.error(f"{agent_name}: 尝试转换结果为HandoffInputData失败: {str(e)}")
                    
                    # 返回原始数据
                    logger.warning(f"{agent_name}: 返回原始HandoffInputData")
                    return data
                
                return result
            except Exception as e:
                logger.error(f"{agent_name}: 执行input_filter出错: {str(e)}")
                return data
        
        # 标记为安全函数
        safe_filter._is_safe_input_filter = True
        
        # 保留原始函数的名称和其他特殊属性
        for attr in dir(input_filter):
            if attr.startswith('_') and not attr.startswith('__'):
                try:
                    setattr(safe_filter, attr, getattr(input_filter, attr))
                except:
                    pass
        
        return safe_filter


# 创建全局Handoff管理器实例
handoff_manager = HandoffManager() 