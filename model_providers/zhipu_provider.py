"""
智谱AI模型提供者 - 实现智谱AI GLM接入
"""
import os
import logging
from typing import Dict, Any, Optional, List, Union

from .base_provider import ModelProvider

# 配置日志
logger = logging.getLogger(__name__)


class ZhipuModelProvider(ModelProvider):
    """
    智谱AI模型提供者

    使用OpenAI兼容接口访问智谱AI的GLM模型
    """

    def __init__(self, model_name: str = "glm-4", **kwargs):
        """
        初始化智谱AI模型提供者

        Args:
            model_name: 默认模型名称
            **kwargs: 其他配置参数
        """
        self.model_name = model_name
        self.client = None
        self.model_obj = None
        
        # 支持的模型列表，用于验证
        self.supported_models = [
            "glm-3-turbo",
            "glm-4",
            "glm-4v"
        ]
        
        # 保存其他参数
        self.kwargs = kwargs

    def setup_client(self, api_key: Optional[str] = None,
                     base_url: Optional[str] = None,
                     **kwargs) -> Any:
        """
        设置智谱AI客户端

        Args:
            api_key: 智谱AI API密钥，如果为None则尝试从环境变量获取
            base_url: 自定义API基础URL
            **kwargs: 其他客户端配置

        Returns:
            客户端实例
        """
        try:
            from agents import Agent, Runner, AsyncOpenAI, OpenAIResponsesModel, OpenAIChatCompletionsModel, \
                ModelSettings,function_tool
            from agents.models import _openai_shared

            # 合并构造函数和方法调用的kwargs
            all_kwargs = {**self.kwargs, **kwargs}

            # 使用提供的API密钥或从环境变量获取
            api_key = api_key or os.getenv("ZHIPU_API_KEY")
            if not api_key:
                raise ValueError("未提供智谱AI API密钥，请设置ZHIPU_API_KEY环境变量或提供api_key参数")

            # 模型名称的处理优先级:
            # 1. 构造函数传入的模型名称
            # 2. 环境变量中的模型名称
            # 3. 默认模型名称
            
            # 检查模型名称是否为有效的模型名称
            is_valid_model = self.model_name in self.supported_models
            
            # 如果是有效模型名称，直接使用
            if is_valid_model:
                logger.info(f"使用智谱AI标准模型: {self.model_name}")
            else:
                # 尝试从环境变量获取
                env_model = os.getenv("ZHIPU_MODEL")
                if env_model:
                    logger.info(f"当前模型名称'{self.model_name}'不是受支持的模型，从环境变量加载模型名称: {env_model}")
                    self.model_name = env_model
                else:
                    # 可能是自定义模型标识符，发出警告但继续使用
                    logger.warning(f"使用未知的智谱模型标识符: {self.model_name}，可能导致API调用失败")
            
            # 设置正确的base_url
            default_base_url = "https://open.bigmodel.cn/api/paas/v4"
            base_url = base_url or os.getenv("ZHIPU_BASE_URL") or default_base_url
            
            # 创建异步客户端
            external_client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                **all_kwargs
            )
            
            # 设置默认客户端
            _openai_shared.set_default_openai_client(external_client)

            # 创建模型对象
            self.model_obj = OpenAIChatCompletionsModel(model=self.model_name,openai_client=external_client)
            
            # 保存客户端引用
            self.client = external_client

            logger.info(f"智谱AI客户端初始化成功，使用模型: {self.model_name}")
            return self.client

        except ImportError as e:
            logger.error(f"初始化智谱AI客户端失败: {e}")
            raise ImportError(f"无法导入OpenAI库，请确保已安装: pip install openai>=1.0.0")

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 包含模型信息的字典
        """
        return {
            "provider": "zhipu",
            "model": self.model_name,
            "api_type": "chat_completions",  # 智谱AI仅支持chat completions
            "available_models": self.supported_models,
            "capabilities": ["chat", "function_calling", "vision"]
        }
        
    def get_model_object(self):
        """
        获取模型对象
        
        Returns:
            模型对象，可直接用于Agent初始化
        """
        if not self.model_obj:
            logger.warning("模型对象未初始化，请先调用setup_client()")
        return self.model_obj