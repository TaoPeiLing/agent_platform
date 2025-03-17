"""
模型提供者基类 - 定义LLM接入的标准接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class ModelProvider(ABC):
    """
    模型提供者基类

    定义所有模型提供者必须实现的标准接口
    """

    @abstractmethod
    def setup_client(self, api_key: str, **kwargs) -> Any:
        """
        设置API客户端

        Args:
            api_key: API密钥
            **kwargs: 其他配置参数

        Returns:
            Any: 客户端实例
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 包含模型信息的字典
        """
        pass

    def register_as_openai_client(self, client: Any) -> None:
        """
        将客户端注册为OpenAI默认客户端

        Args:
            client: 客户端实例
        """
        try:
            from agents import set_default_openai_client
            set_default_openai_client(client)
        except (ImportError, AttributeError) as e:
            raise ImportError(f"无法注册默认OpenAI客户端: {e}")

    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表

        Returns:
            List[str]: 可用模型列表
        """
        info = self.get_model_info()
        models = info.get("available_models", [])
        if not models and "model" in info:
            # 如果未提供可用模型列表但有默认模型，则返回默认模型
            models = [info["model"]]
        return models 