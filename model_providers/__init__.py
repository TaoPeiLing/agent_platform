"""
模型提供者模块 - 支持多种LLM集成
"""
from typing import Dict, Any, Optional, Type

from .base_provider import ModelProvider
from .zhipu_provider import ZhipuModelProvider
from .doubao_provider import DouBaoModelProvider

# 提供者注册表
_PROVIDERS: Dict[str, Type[ModelProvider]] = {
    "zhipu": ZhipuModelProvider,
    "doubao": DouBaoModelProvider,
}


def register_provider(name: str, provider_class: Type[ModelProvider]) -> None:
    """
    注册模型提供者

    Args:
        name: 提供者名称
        provider_class: 提供者类
    """
    _PROVIDERS[name] = provider_class


def get_provider(name: str, **kwargs) -> ModelProvider:
    """
    获取模型提供者实例

    Args:
        name: 提供者名称
        **kwargs: 传递给提供者构造函数的参数

    Returns:
        ModelProvider: 模型提供者实例

    Raises:
        ValueError: 如果提供者不存在
    """
    if name not in _PROVIDERS:
        raise ValueError(f"未知的模型提供者: {name}")

    return _PROVIDERS[name](**kwargs)


def list_providers() -> Dict[str, str]:
    """
    列出所有可用的模型提供者

    Returns:
        Dict[str, str]: 提供者名称到类名的映射
    """
    return {name: provider.__name__ for name, provider in _PROVIDERS.items()}


# 动态导入其他提供者
try:
    from .zhipu_provider import ZhipuModelProvider

    register_provider("zhipu", ZhipuModelProvider)

except ImportError:
    pass

try:
    from .doubao_provider import DouBaoModelProvider

    register_provider("doubao", DouBaoModelProvider)

except ImportError:
    pass

try:
    from .baidu_provider import BaiduModelProvider

    register_provider("baidu", BaiduModelProvider)

except ImportError:
    pass
