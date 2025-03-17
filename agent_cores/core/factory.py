"""
代理工厂模块 - 负责创建和配置不同类型的智能代理
"""
import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Type, Union, Callable
from pathlib import Path
import inspect

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logger = logging.getLogger(__name__)

# 导入OpenAI Agent SDK
from agents import Agent, ModelSettings, function_tool, handoff
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from agents.models.openai_responses import OpenAIResponsesModel
from dataclasses import dataclass


class AgentFactory:
    """
    代理工厂类 - 使用OpenAI Agent SDK创建和管理代理实例

    主要功能：
    1. 注册和管理代理模板
    2. 基于模板创建新代理实例
    3. 动态配置代理属性
    """

    def __init__(self):
        self.templates: Dict[str, Agent] = {}
        self.default_model = "gpt-3.5-turbo-0125"  # 默认模型
        self.current_provider = None  # 当前模型提供者

    def set_model_provider(self, provider_name: str, api_key: str, **kwargs) -> None:
        """
        设置模型提供者

        Args:
            provider_name: 提供者名称 (openai, zhipu, baidu等)
            api_key: API密钥
            **kwargs: 其他配置参数
        """
        try:
            from agent_cores.model_providers import get_provider

            # 获取模型提供者实例
            provider = get_provider(provider_name, **kwargs)

            print("开始设置模型客户端")
            # 设置客户端
            provider.setup_client(api_key, **kwargs)

            # 记录当前提供者
            self.current_provider = provider

            # 更新默认模型
            provider_info = provider.get_model_info()
            self.default_model = provider_info.get("model", self.default_model)

            logger.info(f"已设置模型提供者: {provider_name}, 默认模型: {self.default_model}")
        except (ImportError, ValueError) as e:
            logger.error(f"设置模型提供者失败: {e}")
            raise

    def get_available_providers(self) -> List[str]:
        """
        获取可用的模型提供者列表

        Returns:
            List[str]: 可用提供者列表
        """
        try:
            from agent_cores.model_providers import list_providers
            return list(list_providers().keys())
        except ImportError:
            return ["openai"]  # 默认至少支持OpenAI

    def register_template(self, name: str, agent: Agent) -> None:
        """
        注册代理模板

        Args:
            name: 模板名称
            agent: 代理实例，用作模板
        """
        self.templates[name] = agent
        logger.info(f"已注册代理模板: {name}")

    def register_template_from_config(self,
                                      name: str,
                                      instructions: str,
                                      model_name: Optional[str] = None,
                                      model_settings: Optional[Dict[str, Any]] = None,
                                      tools: Optional[List[Any]] = None,
                                      handoffs: Optional[List[Any]] = None) -> Agent:
        """
        从配置创建并注册代理模板

        Args:
            name: 代理名称
            instructions: 代理指令
            model_name: 模型名称
            model_settings: 模型设置
            tools: 工具列表
            handoffs: 交接列表

        Returns:
            创建的代理实例
        """
        settings = None
        if model_settings:
            settings = ModelSettings(**model_settings)

        agent = Agent(
            name=name,
            instructions=instructions,
            model=model_name or self.default_model,
            model_settings=settings,
            tools=tools or [],
            handoffs=handoffs or []
        )

        self.register_template(name, agent)
        return agent

    def create_from_template(self, template_name: str, **overrides) -> Agent:
        """
        基于现有模板创建代理实例

        Args:
            template_name: 模板名称
            **overrides: 要覆盖的属性

        Returns:
            代理实例

        Raises:
            ValueError: 如果模板不存在
        """
        if template_name not in self.templates:
            raise ValueError(f"未知代理模板: {template_name}")

        # 使用Agent.clone()方法创建新实例
        template = self.templates[template_name]
        return template.clone(**overrides)

    def create_from_json(self, json_config: Dict[str, Any]) -> Agent:
        """
        从JSON配置创建代理实例

        Args:
            json_config: 代理配置

        Returns:
            代理实例
        """
        name = json_config.get("name", "Unnamed Agent")
        instructions = json_config.get("instructions", "")

        # 解析模型配置
        model_config = json_config.get("model", {})

        # 获取模型提供者
        provider_name = model_config.get("provider", "openai")
        model_name = model_config.get("name", self.default_model)
        print(f"创建代理实例: {name}，模型提供者: {provider_name}，模型名称: {model_name}")
        # 如果指定了提供者但不是当前提供者，则尝试切换
        if self.current_provider and provider_name != self.current_provider.get_model_info().get("provider"):
            logger.warning(f"配置指定的提供者 {provider_name} 与当前提供者不同，模型行为可能不一致")

        settings = None
        if "settings" in model_config:
            settings = ModelSettings(**model_config["settings"])
        elif any(k in model_config for k in ["temperature", "top_p", "presence_penalty", "frequency_penalty"]):
            # 从配置构建ModelSettings
            settings_dict = {k: v for k, v in model_config.items()
                             if k in ["temperature", "top_p", "presence_penalty", "frequency_penalty"]}
            settings = ModelSettings(**settings_dict)

        # 创建代理实例
        agent = Agent(
            name=name,
            instructions=instructions,
            model=model_name,
            model_settings=settings
        )

        # 解析工具 (示例，实际实现应该使用ToolManager集成)
        if "tools" in json_config:
            # 这里应该调用工具管理器加载工具
            pass

        # 解析交接代理 (示例，实际实现应该使用代理管理器)
        if "handoffs" in json_config:
            # 这里应该加载交接代理
            pass

        return agent

    def create_from_json_file(self, file_path: str) -> Agent:
        """
        从JSON文件创建代理实例

        Args:
            file_path: JSON文件路径

        Returns:
            代理实例

        Raises:
            FileNotFoundError: 如果文件不存在
            JSONDecodeError: 如果JSON格式无效
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return self.create_from_json(config)

    def create_dynamic_agent(self,
                             name: str,
                             instructions_func: Callable[..., str],
                             **kwargs) -> Agent:
        """
        创建具有动态指令的代理

        Args:
            name: 代理名称
            instructions_func: 动态生成指令的函数
            **kwargs: 其他代理参数

        Returns:
            代理实例
        """
        return Agent(
            name=name,
            instructions=instructions_func,
            **kwargs
        )

    @staticmethod
    def get_default_model_provider():
        """
        获取默认模型提供者

        Returns:
            ModelProvider: 默认模型提供者实例
        """
        try:
            # 确定默认提供者名称
            default_provider = os.getenv("DEFAULT_MODEL_PROVIDER", "openai")
            api_key_var = f"{default_provider.upper()}_API_KEY"
            api_key = os.getenv(api_key_var)

            if api_key:
                # 导入提供者管理模块
                from agent_cores.model_providers import get_provider

                # 获取提供者实例
                provider = get_provider(default_provider)
                
                # 设置客户端
                provider.setup_client(api_key)
                
                # 返回提供者实例
                return provider
            else:
                # 如果没有找到API密钥，使用默认OpenAI提供者
                logger.warning(f"未找到 {api_key_var} 环境变量，无法初始化默认提供者")
                return None
        except Exception as e:
            logger.warning(f"加载默认模型提供者失败: {e}")
            return None


# 创建全局代理工厂实例
agent_factory = AgentFactory()

# 尝试自动加载默认提供者
try:
    # 从环境变量中获取默认提供者
    default_provider = os.environ.get("DEFAULT_MODEL_PROVIDER", "openai")
    print("==========进入代理工厂=====================")
    print(f"默认提供者: {default_provider}")
    if default_provider != "openai":
        # 如果默认提供者不是OpenAI，则尝试加载
        api_key_var = f"{default_provider.upper()}_API_KEY"
        api_key = os.environ.get(api_key_var)
        if api_key:
            # 尝试设置模型提供者
            agent_factory.set_model_provider(default_provider, api_key)
        else:
            logger.warning(f"未找到 {api_key_var} 环境变量，将使用OpenAI作为默认提供者")
except Exception as e:
    logger.warning(f"加载默认模型提供者失败: {e}")