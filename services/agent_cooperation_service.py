"""
代理协作服务 - 提供简化的代理间协作API

该服务封装了基于Handoff机制的代理协作功能，为整个平台提供统一的代理协作接口，
使得在项目任何位置都可以方便地实现代理间任务委托和专业分工。
"""

import logging
import asyncio
import inspect
import functools
import json
import os
from typing import Any, Dict, List, Optional, Callable, Union, Type, TypeVar

# 导入OpenAI Agent SDK
from agents import Agent, Handoff, handoff as sdk_handoff

# 导入本地模块
from agent_cores.core.runtime import runtime_service
from agent_cores.core.template_manager import template_manager
from agent_cores.extensions.handoff_manager import HandoffManager, HandoffConfig
from agent_cores.extensions.agent_adapter import OpenAIAgentAdapter
from agent_cores.extensions.handoffs import HandoffInputData, HandoffInputFilter
from agent_cores.extensions.handoff_filters import remove_all_tools, summarize_history, keep_user_messages_only, custom_filter
from agent_cores.extensions.handoff_prompt import create_handoff_system_message

# 配置日志
logger = logging.getLogger(__name__)

# 定义类型变量
TContext = TypeVar('TContext')
TInput = TypeVar('TInput', bound=Any)


class AgentCooperationService:
    """
    代理协作服务 - 提供简化的代理间协作API
    
    这个服务封装了所有与代理协作相关的功能，包括：
    1. 注册专家代理
    2. 创建分诊代理
    3. 执行代理协作对话
    4. 处理协作结果
    """
    
    def __init__(self):
        """初始化代理协作服务"""
        self.handoff_manager = HandoffManager()
        self._expert_templates = {}
        self._input_type_cache = {}
        self._agent_configs = {}  # 存储智能体配置
        
        # 注册默认智能体配置
        self._register_default_agent_configs()
        
    def _register_default_agent_configs(self):
        """
        注册默认的智能体配置模板
        """
        # 注册默认的分诊智能体配置
        self.register_agent_config(
            "default_triage", 
            {
                "type": "triage",
                "description": "默认分诊智能体",
                "instruction_template": """
你是客服中心的分诊助手，负责初步接待用户并将专业问题转交给相应领域的专家代理。

你的主要职责是:
1. 识别用户请求的类型和主题
2. 解答简单的一般性问题
3. 将专业性问题转交给相应的专家代理

重要规则:
1. 你不能自己回答专业问题，必须转交给对应专家
2. 对于问候或简单问题可以简短回答
3. 发现专业问题后立即使用转交工具
4. 当用户提出专业问题时，直接判断并转交，不要询问是否需要转交

可用专家:
{experts_text}

在转交前，向用户说明你将把问题转交给专家，并简要说明原因。
"""
            }
        )
        
        # 注册默认的专家智能体配置
        self.register_agent_config(
            "default_expert",
            {
                "type": "expert",
                "description": "默认专家智能体",
                "tool_name_template": "transfer_to_{name}_expert",
                "description_template": "将相关问题转交给{agent_name}处理"
            }
        )
    
    def register_agent_config(self, config_id: str, config: Dict[str, Any]):
        """
        注册智能体配置
        
        Args:
            config_id: 配置ID
            config: 配置内容
        """
        self._agent_configs[config_id] = config
        logger.info(f"注册智能体配置: {config_id}")
    
    def get_agent_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """
        获取智能体配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            配置内容，不存在则返回None
        """
        return self._agent_configs.get(config_id)
    
    def create_agent_from_config(self, config: Dict[str, Any], **kwargs) -> Agent:
        """
        从配置创建智能体
        
        Args:
            config: 智能体配置，可以是配置ID或配置字典
            **kwargs: 替换配置中的参数
            
        Returns:
            创建的智能体
        """
        # 如果是配置ID，获取配置内容
        if isinstance(config, str):
            config_id = config
            config = self.get_agent_config(config_id)
            if not config:
                raise ValueError(f"找不到智能体配置: {config_id}")
        
        # 复制配置，避免修改原始配置
        config = config.copy()
        
        # 替换配置中的参数
        for key, value in kwargs.items():
            config[key] = value
        
        # 根据类型创建智能体
        agent_type = config.get("type")
        if not agent_type:
            raise ValueError("配置中缺少'type'字段")
        
        # 调用相应的创建方法
        if agent_type == "triage":
            return self._create_triage_agent_from_config(config)
        elif agent_type == "expert":
            return self._create_expert_agent_from_config(config)
        else:
            raise ValueError(f"不支持的智能体类型: {agent_type}")
    
    def _create_triage_agent_from_config(self, config: Dict[str, Any]) -> Agent:
        """
        从配置创建分诊智能体
        
        Args:
            config: 分诊智能体配置
            
        Returns:
            创建的分诊智能体
        """
        # 获取必要参数
        base_agent = config.get("base_agent")
        if not base_agent:
            raise ValueError("配置中缺少'base_agent'字段")
        
        expert_names = config.get("expert_names", [])
        instruction_template = config.get("instruction_template")
        
        # 获取基础代理
        triage_agent = None
        if isinstance(base_agent, str):
            triage_agent = template_manager.get_template(base_agent)
            if not triage_agent:
                raise ValueError(f"找不到代理模板: {base_agent}")
        else:
            triage_agent = base_agent
        
        # 应用handoffs
        enhanced_agent = self.handoff_manager.apply_handoffs_to_agent(
            triage_agent, 
            expert_names
        )
        
        # 如果提供了指令模板，应用它
        if instruction_template:
            # 创建专家文本
            experts_text = self._create_experts_text(expert_names)
            
            # 渲染指令
            instructions = instruction_template.format(
                experts_text=experts_text,
                **config.get("template_vars", {})
            )
            
            enhanced_agent = enhanced_agent.clone(instructions=instructions)
        
        return enhanced_agent
    
    def _create_input_filter_from_config(self, config: Dict[str, Any]) -> Optional[HandoffInputFilter]:
        """
        从配置创建输入过滤器
        
        Args:
            config: 过滤器配置
            
        Returns:
            创建的输入过滤器，如果配置无效则返回None
        """
        from agent_cores.extensions.handoff_filters import (
            remove_all_tools, 
            summarize_history, 
            keep_user_messages_only,
            custom_filter
        )
        
        # 检查过滤器类型
        filter_type = config.get("input_filter_type")
        if not filter_type:
            return None
            
        # 根据类型创建过滤器
        if filter_type == "remove_tools":
            return remove_all_tools
            
        elif filter_type == "user_only":
            return keep_user_messages_only
            
        elif filter_type == "summarize":
            # 获取自定义参数
            prefix = config.get("summarize_prefix", "历史对话总结")
            max_messages = config.get("keep_recent_messages", 3)
            return summarize_history(prefix, max_messages)
            
        elif filter_type == "custom" and "filter_function" in config:
            # 警告：这里应该谨慎处理，确保不会执行恶意代码
            try:
                # 这里假设filter_function是一个安全的函数定义字符串
                # 实际应用中应该有更严格的安全措施
                filter_code = config["filter_function"]
                filter_globals = {
                    "HandoffInputData": HandoffInputData,
                    "logger": logger
                }
                exec(filter_code, filter_globals)
                filter_func = filter_globals.get("filter_func")
                if callable(filter_func):
                    return custom_filter(filter_func)
                else:
                    logger.error("自定义过滤器代码未定义filter_func函数")
            except Exception as e:
                logger.error(f"创建自定义过滤器时出错: {str(e)}")
                
        return None
    
    def _create_expert_agent_from_config(self, config: Dict[str, Any]) -> HandoffConfig:
        """
        从配置创建专家智能体
        
        Args:
            config: 专家智能体配置
            
        Returns:
            创建的专家智能体配置对象
        """
        # 获取必要参数
        name = config.get("name")
        if not name:
            raise ValueError("配置中缺少'name'字段")
        
        agent_template = config.get("agent_template")
        if not agent_template:
            raise ValueError("配置中缺少'agent_template'字段")
        
        # 可选参数
        description = config.get("description")
        tool_name = config.get("tool_name")
        input_type = config.get("input_type")
        
        # 处理输入过滤器
        input_filter = config.get("input_filter")
        if not input_filter and "input_filter_type" in config:
            # 从配置创建输入过滤器
            input_filter = self._create_input_filter_from_config(config)
        
        # 如果描述使用模板，渲染它
        if "description_template" in config and not description:
            description_template = config.get("description_template")
            agent_name = self._get_safe_agent_name(agent_template)
            description = description_template.format(agent_name=agent_name)
        
        # 如果工具名称使用模板，渲染它
        if "tool_name_template" in config and not tool_name:
            tool_name_template = config.get("tool_name_template")
            tool_name = tool_name_template.format(name=name)
        
        # 注册专家代理
        return self.register_expert(
            name=name,
            agent_template=agent_template,
            description=description,
            tool_name=tool_name,
            input_type=input_type,
            input_filter=input_filter
        )

    def _create_experts_text(self, expert_names: List[str]) -> str:
        """
        创建专家文本描述
        
        Args:
            expert_names: 专家名称列表
            
        Returns:
            专家文本描述
        """
        experts_text = ""
        for name in expert_names:
            if name in self._expert_templates:
                agent = self._expert_templates[name]
                # 安全获取代理名称
                agent_name = self._get_safe_agent_name(agent, name)
                tool_name = f"transfer_to_{name}_expert"
                experts_text += f"- {name}专家 ({agent_name}): 使用 {tool_name} 工具\n"
        return experts_text

    def register_expert(
        self, 
        name: str, 
        agent_template: Union[str, Agent], 
        description: Optional[str] = None,
        tool_name: Optional[str] = None,
        input_type: Optional[Type] = None,
        input_filter: Optional[HandoffInputFilter] = None
    ) -> HandoffConfig:
        """
        注册专家代理
        
        Args:
            name: 专家名称，例如 'travel', 'finance'
            agent_template: 代理模板名称或Agent实例
            description: 专家描述，用于生成工具说明
            tool_name: 工具名称，默认为 'transfer_to_{name}'
            input_type: 输入类型，默认为自动创建
            input_filter: 输入过滤器，默认为 remove_all_tools
            
        Returns:
            HandoffConfig: 注册成功的配置对象
        """
        # 获取代理实例
        agent = None
        if isinstance(agent_template, str):
            agent = template_manager.get_template(agent_template)
            if not agent:
                raise ValueError(f"找不到代理模板: {agent_template}")
        else:
            agent = agent_template
            
        # 缓存模板
        self._expert_templates[name] = agent
        
        # 默认值
        if not description:
            description = f"将相关问题转交给{agent.name}处理"
            
        if not tool_name:
            tool_name = f"transfer_to_{name}_expert"
        
        if not input_type:
            # 创建简单的输入类型
            input_type = self._get_or_create_input_type(name)
        
        # 处理输入过滤器 - 特别检查summarize_history
        if not input_filter:
            # 默认移除所有工具并保留主要对话
            input_filter = remove_all_tools
        elif input_filter == summarize_history:
            # 如果是未初始化的summarize_history，需要正确调用它
            logger.info(f"专家[{name}]检测到未初始化的summarize_history，初始化为默认配置")
            input_filter = summarize_history(f"为{agent.name}提供的历史对话总结", 2)
        
        # 确保input_filter是安全的
        input_filter = self._ensure_safe_input_filter(input_filter, agent.name)
            
        # 创建异步回调
        async def expert_callback(ctx, input_data):
            """专家回调函数"""
            reason = getattr(input_data, 'reason', '未提供原因')
            details = getattr(input_data, 'details', '无详细信息')
            logger.info(f"正在转交给{agent.name}处理: {reason}")
            if details:
                logger.info(f"详细信息: {details}")
            return {"success": True}
            
        # 注册到管理器
        return self.handoff_manager.register_handoff(
            name=name,
            agent=agent,
            callback=expert_callback,
            input_type=input_type,
            tool_name=tool_name,
            tool_description=description,
            input_filter=input_filter
        )

    def _ensure_safe_input_filter(self, input_filter, agent_name="未知代理"):
        """
        确保输入过滤器是安全的函数，能正确处理和返回HandoffInputData对象
        
        Args:
            input_filter: 原始输入过滤器
            agent_name: 代理名称，用于日志
            
        Returns:
            包装后的安全输入过滤器
        """
        from agent_cores.extensions.handoffs import HandoffInputData as LocalHandoffInputData
        from agents.handoffs import HandoffInputData as SDKHandoffInputData
        import functools
        import inspect
        
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
            
        # 创建安全包装函数
        @functools.wraps(input_filter)
        def safe_filter(data):
            try:
                # 检查输入类型
                is_sdk_type = isinstance(data, SDKHandoffInputData)
                is_local_type = isinstance(data, LocalHandoffInputData)
                
                # 记录输入类型
                logger.info(f"{agent_name}: input_filter接收到数据类型: {type(data)}, SDK类型: {is_sdk_type}, 本地类型: {is_local_type}")
                
                # 如果是SDK类型，转换为本地类型
                if is_sdk_type and not is_local_type:
                    logger.info(f"{agent_name}: 将SDK HandoffInputData转换为本地HandoffInputData")
                    local_data = LocalHandoffInputData(
                        input_history=data.input_history,
                        pre_handoff_items=getattr(data, 'pre_handoff_items', ()),
                        new_items=getattr(data, 'new_items', ())
                    )
                    # 执行过滤器，传入本地类型
                    result = input_filter(local_data)
                    
                    # 检查结果类型
                    if isinstance(result, LocalHandoffInputData):
                        # 从本地类型转回SDK类型
                        logger.info(f"{agent_name}: 将本地HandoffInputData转换回SDK HandoffInputData")
                        return SDKHandoffInputData(
                            input_history=result.input_history,
                            pre_handoff_items=result.pre_handoff_items,
                            new_items=result.new_items
                        )
                    else:
                        logger.warning(f"{agent_name}: input_filter返回非预期类型: {type(result)}")
                        # 返回原始SDK类型数据
                        return data
                        
                # 如果不是SDK类型也不是本地类型，创建本地类型
                elif not is_local_type and not is_sdk_type:
                    logger.warning(f"{agent_name}: input_filter接收到未知类型: {type(data)}")
                    if hasattr(data, 'input_history') and hasattr(data, 'new_items'):
                        # 尝试转换为本地类型
                        local_data = LocalHandoffInputData(
                            input_history=data.input_history,
                            pre_handoff_items=getattr(data, 'pre_handoff_items', ()),
                            new_items=getattr(data, 'new_items', ())
                        )
                        # 执行过滤器
                        result = input_filter(local_data)
                        
                        # 检查并转换返回类型
                        if isinstance(result, LocalHandoffInputData):
                            if is_sdk_type:  # 如果原来是SDK类型
                                return SDKHandoffInputData(
                                    input_history=result.input_history,
                                    pre_handoff_items=result.pre_handoff_items,
                                    new_items=result.new_items
                                )
                            else:
                                return result
                        else:
                            logger.warning(f"{agent_name}: input_filter返回非预期类型: {type(result)}")
                            return data
                    else:
                        logger.error(f"{agent_name}: 无法将输入转换为HandoffInputData")
                        return data
                
                # 如果是本地类型，直接处理
                else:
                    # 执行过滤器
                    result = input_filter(data)
                    
                    # 检查结果类型
                    if isinstance(result, LocalHandoffInputData):
                        if is_sdk_type:  # 如果原来是SDK类型
                            return SDKHandoffInputData(
                                input_history=result.input_history,
                                pre_handoff_items=result.pre_handoff_items,
                                new_items=result.new_items
                            )
                        else:
                            return result
                    else:
                        logger.warning(f"{agent_name}: input_filter返回非预期类型: {type(result)}")
                        return data
                
            except Exception as e:
                logger.error(f"{agent_name}: 执行input_filter出错: {str(e)}")
                return data
        
        # 标记为安全函数
        safe_filter._is_safe_input_filter = True
        return safe_filter

    def expert(
        self, 
        name: str, 
        description: Optional[str] = None,
        tool_name: Optional[str] = None,
        input_filter: Optional[HandoffInputFilter] = None,
        config_id: str = "default_expert"
    ) -> Callable[[Union[str, Agent]], HandoffConfig]:
        """
        专家代理装饰器 - 方便快速注册专家代理
        
        用法:
        @agent_cooperation_service.expert("travel", "将旅游问题转交给旅游专家")
        def get_travel_expert():
            return "travel_agent"  # 返回模板名称或Agent实例
        
        Args:
            name: 专家名称
            description: 专家描述
            tool_name: 工具名称
            input_filter: 输入过滤器
            config_id: 配置ID，默认使用"default_expert"
            
        Returns:
            装饰器函数
        """
        kwargs = {}
        if description:
            kwargs["description"] = description
        if tool_name:
            kwargs["tool_name"] = tool_name
        if input_filter:
            kwargs["input_filter"] = input_filter
            
        return self.register_expert_with_decorator(
            name=name,
            config_id=config_id,
            **kwargs
        )
        
    def _get_or_create_input_type(self, name: str) -> Type:
        """
        获取或创建输入类型
        
        Args:
            name: 专家名称
            
        Returns:
            输入类型类
        """
        if name in self._input_type_cache:
            return self._input_type_cache[name]
            
        # 使用动态创建的类型
        from pydantic import BaseModel, Field, create_model
        from typing import Optional as OptionalType
        
        class_name = f"{name.capitalize()}HandoffInput"
        
        # 使用create_model创建模型，确保类型注解正确
        HandoffInput = create_model(
            class_name,
            reason=(str, Field(..., description="转交原因")),
            details=(OptionalType[str], Field(None, description="详细信息"))
        )
        
        # 缓存
        self._input_type_cache[name] = HandoffInput
        return HandoffInput
        
    def create_triage_agent(
        self, 
        base_agent: Union[str, Agent],
        expert_names: List[str],
        instructions: Optional[str] = None
    ) -> Agent:
        """
        创建分诊代理
        
        Args:
            base_agent: 基础代理模板名称或Agent实例
            expert_names: 专家名称列表
            instructions: 代理指令，如果为None则使用默认指令
            
        Returns:
            Agent: 配置好的分诊代理
        """
        # 使用配置系统创建分诊代理
        config = {
            "type": "triage",
            "base_agent": base_agent,
            "expert_names": expert_names
        }
        
        if instructions:
            config["instruction_template"] = instructions
        else:
            # 使用默认指令模板
            default_config = self.get_agent_config("default_triage")
            if default_config:
                config["instruction_template"] = default_config.get("instruction_template")
        
        return self._create_triage_agent_from_config(config)

    def triage_agent_factory(
        self, 
        base_agent: Union[str, Agent],
        config_id: str = "default_triage"
    ) -> Callable[[List[str], Optional[str]], Agent]:
        """
        分诊代理工厂 - 返回一个函数，用于创建分诊代理
        
        用法:
        create_support_triage = agent_cooperation_service.triage_agent_factory("support_agent")
        triage_agent = create_support_triage(["travel", "finance"])
        
        Args:
            base_agent: 基础代理模板名称或Agent实例
            config_id: 分诊智能体配置ID，默认使用"default_triage"
            
        Returns:
            创建分诊代理的函数
        """
        def factory(expert_names: List[str], instructions: Optional[str] = None) -> Agent:
            # 创建配置
            config = {
                "type": "triage",
                "base_agent": base_agent,
                "expert_names": expert_names
            }
            
            # 如果有自定义指令，添加到配置
            if instructions:
                config["instruction_template"] = instructions
            else:
                # 使用指定的配置模板
                template_config = self.get_agent_config(config_id)
                if template_config and "instruction_template" in template_config:
                    config["instruction_template"] = template_config["instruction_template"]
            
            # 创建智能体
            return self._create_triage_agent_from_config(config)
        
        return factory

    def create_expert_from_config(
        self,
        name: str,
        agent_template: Union[str, Agent],
        config_id: str = "default_expert",
        **kwargs
    ) -> HandoffConfig:
        """
        基于配置创建专家智能体
        
        Args:
            name: 专家名称
            agent_template: 代理模板名称或Agent实例
            config_id: 配置ID，默认使用"default_expert"
            **kwargs: 额外参数，会覆盖配置中的值
            
        Returns:
            HandoffConfig: 注册成功的配置对象
        """
        # 获取配置
        config = self.get_agent_config(config_id)
        if not config:
            raise ValueError(f"找不到智能体配置: {config_id}")
        
        # 复制配置
        config = config.copy()
        
        # 添加必要参数
        config["name"] = name
        config["agent_template"] = agent_template
        
        # 添加额外参数
        for key, value in kwargs.items():
            config[key] = value
        
        # 创建专家代理
        return self._create_expert_agent_from_config(config)
        
    def expert_factory(
        self,
        config_id: str = "default_expert",
        **fixed_kwargs
    ) -> Callable[[str, Union[str, Agent], Optional[Dict[str, Any]]], HandoffConfig]:
        """
        专家智能体工厂 - 返回一个函数，用于创建专家智能体
        
        用法:
        create_travel_expert = agent_cooperation_service.expert_factory(
            description="处理旅游相关问题"
        )
        travel_expert = create_travel_expert("travel", "travel_agent")
        
        Args:
            config_id: 配置ID，默认使用"default_expert"
            **fixed_kwargs: 固定参数，会应用到所有创建的专家智能体
            
        Returns:
            创建专家智能体的函数
        """
        def factory(
            name: str,
            agent_template: Union[str, Agent],
            kwargs: Optional[Dict[str, Any]] = None
        ) -> HandoffConfig:
            # 合并固定参数和动态参数
            all_kwargs = fixed_kwargs.copy()
            if kwargs:
                all_kwargs.update(kwargs)
            
            # 创建专家
            return self.create_expert_from_config(
                name=name,
                agent_template=agent_template,
                config_id=config_id,
                **all_kwargs
            )
        
        return factory
    
    def register_expert_with_decorator(
        self, 
        name: str, 
        config_id: str = "default_expert",
        **kwargs
    ) -> Callable[[Callable], HandoffConfig]:
        """
        使用装饰器注册专家智能体 - 改进版本，支持配置
        
        用法:
        @agent_cooperation_service.register_expert_with_decorator(
            name="travel",
            description="处理旅游相关的咨询"
        )
        def get_travel_expert():
            return "travel_agent"  # 返回模板名称或Agent实例
        
        Args:
            name: 专家名称
            config_id: 配置ID，默认使用"default_expert"
            **kwargs: 额外参数，会覆盖配置中的值
            
        Returns:
            装饰器函数
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **func_kwargs):
                agent_or_name = func(*args, **func_kwargs)
                return self.create_expert_from_config(
                    name=name,
                    agent_template=agent_or_name,
                    config_id=config_id,
                    **kwargs
                )
            return wrapper
        return decorator

    def _get_safe_agent_name(self, agent, default_name="unknown_expert") -> str:
        """
        安全获取代理名称
        
        Args:
            agent: 代理对象，可能是Agent实例、字典或其他类型
            default_name: 获取失败时的默认名称
            
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
            # 默认返回传入的名称
            return default_name
        except Exception:
            return default_name
    
    async def execute_with_cooperation(
        self,
        agent: Agent,
        input_text: str,
        session_id: Optional[str] = None,
        context: Any = None
    ) -> Dict[str, Any]:
        """
        执行代理，支持协作处理
        
        Args:
            agent: 代理实例
            input_text: 输入文本
            session_id: 会话ID，如果为None则创建新会话
            context: 上下文对象
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 执行代理
        result = await runtime_service.run_agent(
            agent=agent,
            input_text=input_text,
            session_id=session_id,
            context=context
        )
        
        # 处理handoff结果
        if 'items' in result and result['items']:
            # 检查是否有handoff结果
            for item in result['items']:
                if item.get('type') == 'handoff_result':
                    # 处理handoff结果
                    logger.info("检测到handoff结果，进行处理")
                    result = await self.handoff_manager.process_handoff_result(
                        result,
                        context,
                        session_id
                    )
                    break
                    
        return result

    def with_cooperation(self, func: Callable) -> Callable:
        """
        协作执行装饰器 - 用于为现有函数添加协作处理功能
        
        用法:
        @agent_cooperation_service.with_cooperation
        async def run_agent(agent, message, session_id=None):
            return await runtime_service.run_agent(agent, message, session_id)
        
        Args:
            func: 要装饰的函数
            
        Returns:
            装饰后的函数
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 调用原始函数
            result = await func(*args, **kwargs)
            
            # 提取参数
            session_id = kwargs.get('session_id', None)
            context = kwargs.get('context', None)
            
            # 处理handoff结果
            if isinstance(result, dict) and 'items' in result and result['items']:
                # 检查是否有handoff结果
                for item in result['items']:
                    if item.get('type') == 'handoff_result':
                        # 处理handoff结果
                        logger.info("检测到handoff结果，进行处理")
                        result = await self.handoff_manager.process_handoff_result(
                            result,
                            context,
                            session_id
                        )
                        break
                        
            return result
        return wrapper
        
    async def direct_handoff_to_expert(
        self,
        expert_name: str,
        user_message: str,
        reason: str,
        session_id: Optional[str] = None,
        context: Any = None
    ) -> Dict[str, Any]:
        """
        直接转交给专家处理
        
        Args:
            expert_name: 专家名称
            user_message: 用户消息
            reason: 转交原因
            session_id: 会话ID，如果为None则创建新会话
            context: 上下文对象
            
        Returns:
            Dict[str, Any]: 专家回复
        """
        if expert_name not in self._expert_templates:
            raise ValueError(f"找不到专家: {expert_name}")
            
        # 获取专家代理
        expert_agent = self._expert_templates[expert_name]
        
        # 安全获取代理名称
        agent_name = self._get_safe_agent_name(expert_agent, expert_name)
        
        # 创建系统消息
        system_message = create_handoff_system_message(
            target_agent_name=agent_name,
            reason=reason
        )
        
        # 安全克隆代理
        enhanced_expert = self._safely_clone_agent(expert_agent, system_message)
        if not enhanced_expert:
            logger.error(f"无法克隆专家代理: {expert_name}")
            raise ValueError(f"无法创建专家代理: {expert_name}")
        
        # 执行专家代理
        return await runtime_service.run_agent(
            agent=enhanced_expert,
            input_text=user_message,
            session_id=session_id,
            context=context
        )
        
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

    def load_agent_configs_from_json(self, json_file: str):
        """
        从JSON文件加载智能体配置
        
        Args:
            json_file: JSON文件路径
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
                
            # 注册配置
            for config_id, config in configs.items():
                self.register_agent_config(config_id, config)
                
            logger.info(f"从{json_file}加载了{len(configs)}个智能体配置")
        except Exception as e:
            logger.error(f"加载智能体配置出错: {str(e)}")
            
    def load_agent_configs_from_directory(self, directory: str, pattern: str = "*.json"):
        """
        从目录加载所有JSON配置文件
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
        """
        import glob
        try:
            # 查找所有匹配的文件
            pattern_path = os.path.join(directory, pattern)
            files = glob.glob(pattern_path)
            
            # 加载每个文件
            total_configs = 0
            for file in files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        configs = json.load(f)
                    
                    # 以文件名为前缀注册配置
                    base_name = os.path.splitext(os.path.basename(file))[0]
                    for config_id, config in configs.items():
                        # 组合ID: 文件名_配置ID
                        combined_id = f"{base_name}_{config_id}"
                        self.register_agent_config(combined_id, config)
                        total_configs += 1
                        
                except Exception as e:
                    logger.error(f"加载配置文件{file}出错: {str(e)}")
                    
            logger.info(f"从{directory}目录加载了{total_configs}个智能体配置")
        except Exception as e:
            logger.error(f"加载目录配置出错: {str(e)}")


# 创建全局服务实例
agent_cooperation_service = AgentCooperationService() 