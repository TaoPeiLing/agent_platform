"""
OpenAI Agent适配器 - 提供与OpenAI Agent SDK的无缝集成

该模块实现了适配器模式，确保我们的代码能与OpenAI Agent SDK无缝集成，
特别是在处理Handoffs等复杂功能时保持类型一致性。
"""

import logging
import inspect
from typing import Any, Dict, List, Optional, TypeVar, Callable, Union, cast
import functools

# 导入OpenAI Agent SDK
from agents import Agent, Runner, Handoff, handoff as sdk_handoff
from agents.run_context import RunContextWrapper

# 导入本地模块
from agent_cores.extensions.handoffs import HandoffInputData

# 配置日志
logger = logging.getLogger(__name__)

# 定义类型变量
TContext = TypeVar('TContext')


class OpenAIAgentAdapter:
    """
    OpenAI Agent SDK适配器 - 确保我们的实现与SDK无缝集成
    """
    @staticmethod
    def create_agent_with_handoffs(base_agent: Agent, handoffs: List[Any], **kwargs) -> Agent:
        """
        创建带有Handoffs功能的agent
        
        Args:
            base_agent: 基础代理
            handoffs: handoff对象列表
            **kwargs: 附加参数
            
        Returns:
            配置好的代理
        """
        # 先创建工具定义
        tools = list(base_agent.tools) if hasattr(base_agent, 'tools') else []
        
        # 收集base_agent的所有必要属性
        agent_kwargs = {
            "name": base_agent.name,
            "instructions": base_agent.instructions,
            "tools": tools,
            "handoffs": handoffs,  # 保持原始对象
        }
        
        # 添加可选属性
        for attr in ["handoff_description", "model", "model_settings", "output_type", "hooks"]:
            if hasattr(base_agent, attr):
                agent_kwargs[attr] = getattr(base_agent, attr)
                
        # 合并外部传入的kwargs
        agent_kwargs.update(kwargs)
        
        # 创建新agent
        new_agent = Agent(**agent_kwargs)
        return new_agent
    
    @staticmethod
    def log_agent_handoffs(agent: Agent, prefix: str = "") -> None:
        """
        记录agent的handoffs信息
        
        Args:
            agent: 要记录的代理
            prefix: 日志前缀
        """
        agent_name = OpenAIAgentAdapter.safely_get_property(agent, 'name', 'unknown')
        logger.info(f"{prefix} Agent: {agent_name}, handoffs类型: {type(getattr(agent, 'handoffs', None))}")
        
        if hasattr(agent, 'handoffs'):
            for i, h in enumerate(agent.handoffs):
                # 记录handoff属性
                if isinstance(h, Handoff):
                    logger.info(f"{prefix} handoff[{i}]类型: {type(h)}")
                    logger.info(f"{prefix} handoff[{i}]名称: {getattr(h, 'agent_name', 'unknown')}")
                    logger.info(f"{prefix} handoff[{i}]工具名: {getattr(h, 'tool_name', 'unknown')}")
                elif isinstance(h, dict):
                    logger.info(f"{prefix} handoff[{i}]类型: 字典")
                    logger.info(f"{prefix} handoff[{i}]名称: {h.get('agent_name', h.get('name', 'unknown'))}")
                else:
                    logger.info(f"{prefix} handoff[{i}]类型: {type(h)}")
        
    @staticmethod
    def safely_get_property(obj, property_name, default_value=None):
        """
        安全获取对象属性，适用于任何类型的对象
        
        Args:
            obj: 目标对象，可以是任何类型
            property_name: 属性名
            default_value: 默认值
            
        Returns:
            属性值或默认值
        """
        try:
            # 对象属性访问
            if hasattr(obj, property_name):
                return getattr(obj, property_name)
            # 字典键访问
            elif isinstance(obj, dict) and property_name in obj:
                return obj[property_name]
            # 默认返回值
            return default_value
        except Exception as e:
            logger.debug(f"安全获取属性 {property_name} 失败: {str(e)}")
            return default_value
    
    @staticmethod
    def _create_safe_input_filter(original_filter):
        """
        创建一个安全的input_filter包装函数
        
        处理高阶过滤器函数(如summarize_history)，自动初始化它们，
        并确保返回的过滤器函数总是返回HandoffInputData对象。
        
        Args:
            original_filter: 原始过滤器函数
            
        Returns:
            安全的过滤器函数
        """
        # 如果没有原始filter，返回None
        if original_filter is None:
            return None
        
        from agents.handoffs import HandoffInputData
        
        # 检查是否是高阶函数(如summarize_history)需要先调用
        import inspect
        from agent_cores.extensions.handoff_filters import summarize_history
        
        # 检查是否为特定的高阶过滤器函数
        is_higher_order = False
        if original_filter == summarize_history:
            logger.info("检测到未初始化的summarize_history过滤器，正在初始化...")
            # 使用默认参数调用summarize_history
            try:
                original_filter = summarize_history("历史对话已被总结", 2)
                is_higher_order = True
                logger.info("成功初始化summarize_history过滤器")
            except Exception as e:
                logger.error(f"初始化summarize_history过滤器失败: {e}")
        
        # 如果函数名包含filter或summary，检查其签名是否返回函数
        elif hasattr(original_filter, "__name__") and ("filter" in original_filter.__name__ or "summary" in original_filter.__name__):
            try:
                sig = inspect.signature(original_filter)
                # 如果函数的返回类型注解是Callable，说明它是一个高阶函数
                if (hasattr(sig, "return_annotation") and 
                    "Callable" in str(sig.return_annotation)):
                    
                    logger.info(f"检测到未初始化的高阶过滤器: {original_filter.__name__}，尝试初始化...")
                    # 尝试不带参数调用函数，获取实际的过滤器
                    if len(sig.parameters) == 0:
                        # 无参数高阶函数
                        original_filter = original_filter()
                    else:
                        # 带默认参数的高阶函数，使用默认值调用
                        default_args = {}
                        for name, param in sig.parameters.items():
                            if param.default != inspect.Parameter.empty:
                                default_args[name] = param.default
                            else:
                                # 对于没有默认值的参数，提供一些常规值
                                if "summary" in name or "message" in name:
                                    default_args[name] = "历史对话已被总结"
                                elif "count" in name or "limit" in name or "max" in name or "num" in name:
                                    default_args[name] = 2
                                else:
                                    default_args[name] = None
                        
                        # 使用构建的默认参数调用高阶函数
                        original_filter = original_filter(**default_args)
                        
                    is_higher_order = True
                    logger.info(f"成功初始化高阶过滤器: {original_filter.__name__ if hasattr(original_filter, '__name__') else '匿名函数'}")
            except Exception as e:
                logger.error(f"检查/初始化高阶过滤器失败: {e}")
        
        # 创建安全包装函数
        def safe_filter(input_data: HandoffInputData) -> HandoffInputData:
            """安全包装input_filter函数，确保总是返回HandoffInputData对象"""
            try:
                # 调用原始filter函数
                result = original_filter(input_data)
                
                # 检查结果是否为函数类型(可能是高阶函数的返回)
                if callable(result) and not isinstance(result, HandoffInputData):
                    logger.warning(f"原始filter函数返回了函数类型而不是HandoffInputData: {result.__name__ if hasattr(result, '__name__') else '匿名函数'}，尝试调用它")
                    try:
                        # 尝试以input_data为参数调用返回的函数
                        result = result(input_data)
                    except Exception as e:
                        logger.error(f"调用filter返回的函数失败: {e}，使用原始输入")
                        return input_data
                
                # 检查结果是否为HandoffInputData类型
                if not isinstance(result, HandoffInputData):
                    logger.warning(f"原始filter函数返回了非HandoffInputData类型: {type(result)}，使用原始输入")
                    return input_data
                
                return result
            except Exception as e:
                logger.error(f"执行input_filter函数时出错: {e}，使用原始输入")
                return input_data
            
        return safe_filter

    @staticmethod
    def pre_run_hook(agent: Agent, context: Any, **kwargs) -> Agent:
        """
        运行前钩子，确保agent配置正确
        
        Args:
            agent: 要执行的代理
            context: 运行上下文
            **kwargs: 附加参数
            
        Returns:
            处理后的代理
        """
        logger.info("=========== 应用预处理钩子，确保代理对象类型安全 ===========")
        
        # 记录agent状态
        agent_name = OpenAIAgentAdapter.safely_get_property(agent, 'name', 'unknown')
        logger.info(f"处理代理: {agent_name}")
        
        # 创建安全的input_filter包装函数 - 使用公共方法
        def create_safe_input_filter(original_filter):
            """创建一个安全的input_filter包装函数"""
            return OpenAIAgentAdapter._create_safe_input_filter(original_filter)
        
        # 检查是否有handoffs需要处理
        if hasattr(agent, 'handoffs') and agent.handoffs:
            # 记录原始状态
            OpenAIAgentAdapter.log_agent_handoffs(agent, "执行前")
            
            # 导入必要的类和模块
            from agent_cores.core.template_manager import template_manager
            # 导入SDK的handoff函数，用于创建标准Handoff对象
            from agents import handoff as sdk_handoff
            
            # 处理handoffs
            fixed_handoffs = []
            needs_fix = False
            
            for h in agent.handoffs:
                # 如果已经是Handoff类型且input_filter可能有问题，创建安全版本
                if isinstance(h, Handoff):
                    original_filter = getattr(h, 'input_filter', None)
                    if original_filter is not None:
                        # 创建一个新的Handoff对象，使用安全的input_filter
                        safe_filter = create_safe_input_filter(original_filter)
                        logger.info(f"为Handoff[{getattr(h, 'agent_name', 'unknown')}]创建安全input_filter包装")
                        
                        try:
                            # 获取正确的目标代理
                            target_agent = None
                            if hasattr(h, 'agent'):
                                target_agent = getattr(h, 'agent')
                            elif hasattr(h, 'agent_name'):
                                agent_name = getattr(h, 'agent_name')
                                try:
                                    target_agent = template_manager.get_template(agent_name)
                                except Exception as exc:
                                    logger.warning(f"通过agent_name获取目标代理失败: {exc}")

                            if target_agent:
                                # 克隆handoff对象，替换input_filter
                                safe_h = sdk_handoff(
                                    agent=target_agent,
                                    tool_name_override=getattr(h, 'tool_name', None),
                                    tool_description_override=getattr(h, 'tool_description', None),
                                    on_handoff=getattr(h, 'on_invoke_handoff', None),
                                    input_filter=safe_filter
                                )
                                fixed_handoffs.append(safe_h)
                                needs_fix = True
                            else:
                                logger.warning(f"无法获取Handoff目标代理，保留原始对象")
                                fixed_handoffs.append(h)
                        except Exception as e:
                            logger.warning(f"创建安全Handoff对象失败: {e}，保留原始对象")
                            fixed_handoffs.append(h)
                    else:
                        fixed_handoffs.append(h)
                    continue
                    
                # 需要修复
                needs_fix = True
                
                # 字典类型 -> 使用 SDK 的 handoff() 函数创建 Handoff 对象
                if isinstance(h, dict):
                    # 获取必要参数
                    agent_name = h.get('agent_name') or h.get('name', 'unknown_expert')
                    tool_name = h.get('tool_name', f"handoff_to_{agent_name}")
                    tool_description = h.get('tool_description', f"将问题交给{agent_name}专家处理")
                    
                    # 获取并包装input_filter
                    original_filter = h.get('input_filter')
                    safe_filter = create_safe_input_filter(original_filter)
                    
                    # 尝试获取目标代理
                    target_agent = None
                    try:
                        if agent_name != 'unknown_expert':
                            target_agent = template_manager.get_template(agent_name)
                    except Exception as e:
                        logger.warning(f"获取目标代理模板失败: {e}")
                    
                    if target_agent:
                        # 使用SDK的handoff函数创建标准Handoff对象
                        try:
                            # 提取回调函数，如果有的话
                            on_handoff = h.get('on_invoke_handoff')
                            
                            # 创建标准Handoff对象的参数
                            handoff_kwargs = {
                                'tool_name_override': tool_name,
                                'tool_description_override': tool_description,
                                'input_filter': safe_filter
                            }
                            
                            # 如果有回调函数和输入类型，则添加
                            if on_handoff and h.get('input_type'):
                                handoff_kwargs['on_handoff'] = on_handoff
                                handoff_kwargs['input_type'] = h.get('input_type')
                            elif on_handoff:
                                handoff_kwargs['on_handoff'] = on_handoff
                            
                            # 使用SDK原生函数创建Handoff对象
                            handoff_obj = sdk_handoff(target_agent, **handoff_kwargs)
                            
                            logger.info(f"成功创建原生Handoff对象: {agent_name}")
                            fixed_handoffs.append(handoff_obj)
                        except Exception as e:
                            logger.error(f"创建原生Handoff对象失败: {e}，使用回退方法")
                            # 回退方法：尝试直接追加目标代理
                            fixed_handoffs.append(target_agent)
                    else:
                        logger.warning(f"找不到{agent_name}专家代理，跳过此handoff")
                else:
                    # 对于其他非字典非Handoff对象，尝试获取其agent_name或name
                    agent_name = OpenAIAgentAdapter.safely_get_property(h, 'agent_name', 
                                OpenAIAgentAdapter.safely_get_property(h, 'name', 'unknown'))
                    logger.warning(f"不支持的handoff类型 {type(h)}, agent_name={agent_name}, 跳过此handoff")
            
            # 如果需要修复，替换handoffs
            if needs_fix:
                fixed_agent = agent.clone(handoffs=fixed_handoffs)
                OpenAIAgentAdapter.log_agent_handoffs(fixed_agent, "修复后")
                logger.info(f"已替换 {len(agent.handoffs)} 个handoffs为 {len(fixed_handoffs)} 个标准化的Handoff对象")
            else:
                fixed_agent = agent
                logger.info("所有handoffs已是标准Handoff对象，无需修复")
        else:
            fixed_agent = agent
            logger.info("代理没有handoffs，无需修复")
        
        # 将上下文中的handoff对象转换为标准格式
        if context and hasattr(context, "handoffs") and context.handoffs:
            context = OpenAIAgentAdapter.convert_handoff_objects(fixed_agent, context)
        
        logger.info("=========== 预处理钩子执行完成 ===========")
        return fixed_agent
        
    @staticmethod
    def convert_handoff_objects(agent: Agent, context: Any) -> Any:
        """
        将上下文中的handoff对象转换为原生SDK Handoff实例
        
        Args:
            agent: 当前代理
            context: 上下文对象，可能包含handoffs属性
        
        Returns:
            处理后的上下文对象
        """
        if not context or not hasattr(context, "handoffs") or not context.handoffs:
            return context
        
        try:
            logger.info("转换上下文中的handoff对象...")
            from agent_cores.core.template_manager import template_manager
            # 导入SDK的handoff函数，用于创建标准Handoff对象
            from agents import handoff as sdk_handoff
            
            # 使用共享的安全过滤器创建函数
            def create_safe_input_filter(original_filter):
                """创建一个安全的input_filter包装函数"""
                return OpenAIAgentAdapter._create_safe_input_filter(original_filter)
            
            # 转换上下文中的handoffs
            converted_handoffs = []
            for h in context.handoffs:
                # 如果已经是Handoff类型，检查是否需要包装input_filter
                if isinstance(h, Handoff):
                    original_filter = getattr(h, 'input_filter', None)
                    if original_filter is not None:
                        # 创建安全的input_filter
                        safe_filter = create_safe_input_filter(original_filter)
                        logger.info(f"为上下文Handoff[{getattr(h, 'agent_name', 'unknown')}]创建安全input_filter包装")
                        
                        try:
                            # 获取正确的目标代理
                            target_agent = None
                            if hasattr(h, 'agent'):
                                target_agent = getattr(h, 'agent')
                            elif hasattr(h, 'agent_name'):
                                agent_name = getattr(h, 'agent_name')
                                try:
                                    target_agent = template_manager.get_template(agent_name)
                                except Exception as exc:
                                    logger.warning(f"通过agent_name获取目标代理失败: {exc}")
                            
                            if target_agent:
                                # 创建新的安全Handoff对象
                                safe_h = sdk_handoff(
                                    agent=target_agent,
                                    tool_name_override=getattr(h, 'tool_name', None),
                                    tool_description_override=getattr(h, 'tool_description', None),
                                    on_handoff=getattr(h, 'on_invoke_handoff', None),
                                    input_filter=safe_filter
                                )
                                logger.info(f"成功创建带安全filter的Handoff: {getattr(h, 'agent_name', 'unknown')}")
                                converted_handoffs.append(safe_h)
                            else:
                                logger.warning(f"无法获取Handoff目标代理，保留原始对象")
                                converted_handoffs.append(h)
                        except Exception as e:
                            logger.warning(f"创建安全Handoff对象失败: {e}，保留原始对象")
                            converted_handoffs.append(h)
                    else:
                        logger.info(f"保留原生Handoff对象: {getattr(h, 'agent_name', 'unknown')}")
                        converted_handoffs.append(h)
                    continue
                
                # 字典类型 -> 尝试创建Handoff对象
                if isinstance(h, dict):
                    agent_name = h.get('agent_name') or h.get('name', 'unknown_expert')
                    tool_name = h.get('tool_name', f"handoff_to_{agent_name}")
                    tool_description = h.get('tool_description', f"将问题交给{agent_name}专家处理")
                    
                    # 获取并包装input_filter
                    original_filter = h.get('input_filter')
                    safe_filter = create_safe_input_filter(original_filter)
                    
                    # 尝试获取目标代理
                    target_agent = None
                    try:
                        if agent_name != 'unknown_expert':
                            target_agent = template_manager.get_template(agent_name)
                    except Exception as e:
                        logger.warning(f"获取目标代理模板失败: {e}")
                    
                    if target_agent:
                        # 使用SDK的handoff函数创建标准Handoff对象
                        try:
                            # 提取回调函数，如果有的话
                            on_handoff = h.get('on_invoke_handoff')
                            
                            # 创建标准Handoff对象的参数
                            handoff_kwargs = {
                                'tool_name_override': tool_name,
                                'tool_description_override': tool_description,
                                'input_filter': safe_filter
                            }
                            
                            # 如果有回调函数和输入类型，则添加
                            if on_handoff and h.get('input_type'):
                                handoff_kwargs['on_handoff'] = on_handoff
                                handoff_kwargs['input_type'] = h.get('input_type')
                            elif on_handoff:
                                handoff_kwargs['on_handoff'] = on_handoff
                            
                            # 使用SDK原生函数创建Handoff对象
                            handoff_obj = sdk_handoff(target_agent, **handoff_kwargs)
                            
                            logger.info(f"成功创建上下文原生Handoff对象: {agent_name}")
                            converted_handoffs.append(handoff_obj)
                        except Exception as e:
                            logger.error(f"创建上下文原生Handoff对象失败: {e}，使用目标代理")
                            # 回退方法：直接使用目标代理
                            converted_handoffs.append(target_agent)
                    else:
                        logger.warning(f"找不到{agent_name}专家代理，跳过此handoff")
                else:
                    # 对于其他非字典非Handoff对象，跳过
                    agent_name = OpenAIAgentAdapter.safely_get_property(h, 'agent_name', 
                                OpenAIAgentAdapter.safely_get_property(h, 'name', 'unknown'))
                    logger.warning(f"上下文中不支持的handoff类型 {type(h)}, agent_name={agent_name}, 跳过")
            
            # 更新上下文中的handoffs
            context.handoffs = converted_handoffs
            logger.info(f"上下文handoff对象转换完成，共{len(converted_handoffs)}个对象")
            
        except Exception as e:
            logger.error(f"处理上下文handoffs时出错: {str(e)}")
        
        return context 

    def convert_handoff_objects(self, context):
        """将上下文中的handoff对象转换为SDK标准对象"""
        from agents import Handoff, handoff

        # 检查上下文是否有效
        if not context or not hasattr(context, 'handoffs') or not context.handoffs:
            logger.debug("上下文不包含handoffs，跳过转换")
            return
            
        logger.info(f"开始转换handoff对象，共 {len(context.handoffs)} 个")
        for i, handoff_obj in enumerate(context.handoffs):
            # 检查是否已经是SDK原生的Handoff对象
            if isinstance(handoff_obj, Handoff):
                logger.debug(f"[{i}] 检测到SDK原生Handoff对象: {self.safely_get_property(handoff_obj, 'agent_name', '未知')}")
                
                # 检查和修复input_filter
                handoff_obj = self.ensure_safe_input_filter(handoff_obj)
                context.handoffs[i] = handoff_obj
                continue
                
            try:
                # 安全获取属性
                agent = self.safely_get_property(handoff_obj, 'agent')
                tool_name = self.safely_get_property(handoff_obj, 'tool_name')
                tool_description = self.safely_get_property(handoff_obj, 'tool_description')
                input_json_schema = self.safely_get_property(handoff_obj, 'input_json_schema')
                input_type = self.safely_get_property(handoff_obj, 'input_type')
                on_invoke_handoff = self.safely_get_property(handoff_obj, 'on_invoke_handoff')
                agent_name = self.safely_get_property(handoff_obj, 'agent_name')
                input_filter = self.safely_get_property(handoff_obj, 'input_filter')
                
                # 检查必要属性
                if not agent or not on_invoke_handoff:
                    logger.warning(f"[{i}] Handoff对象缺少必要属性，保留原始对象")
                    continue
                    
                # 创建标准Handoff对象
                logger.debug(f"[{i}] 转换Handoff对象: {agent_name or '未知代理'}")
                native_handoff = handoff(
                    agent=agent,
                    tool_name_override=tool_name,
                    tool_description_override=tool_description,
                    on_handoff=on_invoke_handoff,
                    input_type=input_type,
                    input_filter=self.ensure_safe_input_filter_func(input_filter)
                )
                
                # 替换原始对象
                context.handoffs[i] = native_handoff
                logger.debug(f"[{i}] Handoff对象转换成功")
            except Exception as e:
                logger.error(f"[{i}] 转换Handoff对象失败: {str(e)}")

    def ensure_safe_input_filter(self, handoff_obj):
        """确保handoff对象中的input_filter是安全的可执行函数"""
        from agents import handoff

        # 安全获取属性
        agent = self.safely_get_property(handoff_obj, 'agent')
        tool_name = self.safely_get_property(handoff_obj, 'tool_name')
        tool_description = self.safely_get_property(handoff_obj, 'tool_description')
        input_json_schema = self.safely_get_property(handoff_obj, 'input_json_schema')
        input_type = self.safely_get_property(handoff_obj, 'input_type')
        on_invoke_handoff = self.safely_get_property(handoff_obj, 'on_invoke_handoff')
        agent_name = self.safely_get_property(handoff_obj, 'agent_name')
        input_filter = self.safely_get_property(handoff_obj, 'input_filter')
        
        # 检测特殊的input_filter情况
        input_filter = self.ensure_safe_input_filter_func(input_filter)
        
        # 如果有变更，创建新的Handoff对象
        if input_filter != self.safely_get_property(handoff_obj, 'input_filter'):
            logger.info(f"修复Handoff对象中的input_filter: {agent_name or '未知代理'}")
            return handoff(
                agent=agent,
                tool_name_override=tool_name,
                tool_description_override=tool_description,
                on_handoff=on_invoke_handoff,
                input_type=input_type,
                input_filter=input_filter
            )
        
        return handoff_obj
        
    def ensure_safe_input_filter_func(self, input_filter):
        """确保input_filter是安全的可执行函数或None"""
        import inspect
        from agent_cores.extensions.handoff_filters import summarize_history
        
        # 如果是None，直接返回
        if input_filter is None:
            return None
            
        # 检查是否是summarize_history函数本身(未调用)
        if input_filter is summarize_history or (hasattr(input_filter, '__name__') and input_filter.__name__ == 'summarize_history'):
            logger.info("检测到未初始化的summarize_history，初始化为默认配置")
            return summarize_history("提供的历史对话总结", 2)
            
        # 检查是否是filter_func(内部函数)
        if hasattr(input_filter, '__name__') and input_filter.__name__ == 'filter_func':
            # 这是已经初始化的summarize_history返回的函数
            return input_filter
            
        # 检查是否已经被safe_input_filter装饰
        if hasattr(input_filter, '_is_safe_input_filter') and input_filter._is_safe_input_filter:
            return input_filter
            
        # 如果是可调用的函数，检查其签名
        if callable(input_filter):
            try:
                sig = inspect.signature(input_filter)
                # 确保至少有一个参数(HandoffInputData)
                if len(sig.parameters) >= 1:
                    # 包装函数以确保返回类型正确
                    from agent_cores.extensions.handoffs import HandoffInputData
                    
                    @functools.wraps(input_filter)
                    def safe_filter(data):
                        try:
                            result = input_filter(data)
                            return self.ensure_handoff_input_data(result, data)
                        except Exception as e:
                            logger.error(f"执行input_filter出错: {str(e)}")
                            return data
                            
                    safe_filter._is_safe_input_filter = True
                    return safe_filter
            except Exception as e:
                logger.error(f"检查input_filter签名出错: {str(e)}")
                
        # 如果无法确定，返回None
        logger.warning(f"无法处理的input_filter类型: {type(input_filter)}")
        return None
        
    def ensure_handoff_input_data(self, data, fallback_data=None):
        """确保返回的是HandoffInputData对象"""
        from agent_cores.extensions.handoffs import HandoffInputData
        
        # 如果已经是正确类型，直接返回
        if isinstance(data, HandoffInputData):
            return data
            
        # 如果是元组形式的返回值，尝试构造HandoffInputData
        if isinstance(data, tuple) and len(data) == 3:
            try:
                return HandoffInputData(
                    input_history=data[0],
                    pre_handoff_items=data[1],
                    new_items=data[2]
                )
            except Exception as e:
                logger.error(f"从元组转换为HandoffInputData失败: {str(e)}")
                
        # 如果是字典形式，尝试构造HandoffInputData
        if isinstance(data, dict):
            try:
                return HandoffInputData(
                    input_history=data.get('input_history', ()),
                    pre_handoff_items=data.get('pre_handoff_items', ()),
                    new_items=data.get('new_items', ())
                )
            except Exception as e:
                logger.error(f"从字典转换为HandoffInputData失败: {str(e)}")
                
        # 如果无法转换，返回备用数据或创建空对象
        if fallback_data and isinstance(fallback_data, HandoffInputData):
            logger.warning("返回备用HandoffInputData对象")
            return fallback_data
        else:
            logger.warning("创建空HandoffInputData对象")
            return HandoffInputData(input_history=(), pre_handoff_items=(), new_items=())

    def pre_run_hook(self, context):
        """运行前的处理钩子"""
        # 记录代理列表
        if hasattr(context, 'agents') and context.agents:
            agent_names = []
            for agent in context.agents:
                name = self.safely_get_property(agent, 'name', 'unknown')
                agent_names.append(name)
            logger.info(f"上下文中的代理列表: {', '.join(agent_names)}")
                
        # 记录handoff对象
        if hasattr(context, 'handoffs') and context.handoffs:
            handoff_count = len(context.handoffs)
            logger.info(f"上下文中的handoff数量: {handoff_count}")
            
            # 记录和修复handoff对象
            for i, handoff_obj in enumerate(context.handoffs):
                agent_name = self.safely_get_property(handoff_obj, 'agent_name', 'unknown')
                logger.info(f"处理handoff[{i}]: {agent_name}")
                
                # 检查和修复input_filter
                fixed_handoff = self.ensure_safe_input_filter(handoff_obj)
                if fixed_handoff is not handoff_obj:
                    context.handoffs[i] = fixed_handoff
                    logger.info(f"修复了handoff[{i}]的input_filter")
        
        # 将Dict形式的handoff对象转换为SDK标准对象
        self.convert_handoff_objects(context)
            
        return context 