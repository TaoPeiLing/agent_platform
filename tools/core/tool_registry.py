"""
工具注册模块 - 提供高级的工具注册和发现功能

该模块提供了工具注册的功能，包括：
1. 装饰器注册工具函数
2. 自动发现和注册工具
3. 工具元数据管理
"""
import os
import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Set, Union, TypeVar, get_type_hints
from functools import wraps

# 配置日志
logger = logging.getLogger(__name__)

# 导入OpenAI Agent SDK相关组件
from agents import function_tool, FunctionTool


# 导入工具管理器
from agent_cores.tools.core.tool_manager import tool_manager
from agent_cores.tools.tool_utils import tool_wrapper

# 类型定义
T = TypeVar('T')
ToolFunction = Callable[..., Dict[str, Any]]


def register_tool(
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general",
        permission_level: str = "basic",
        tags: Optional[List[str]] = None,
        **metadata
) -> Callable[[ToolFunction], ToolFunction]:
    """
    工具注册装饰器 - 装饰和注册工具函数

    使用方法:
    @register_tool(
        name="search_web",
        description="搜索网页",
        category="search",
        permission_level="basic",
        tags=["web", "search"]
    )
    def search_web(query: str) -> Dict[str, Any]:
        ...

    Args:
        name: 工具名称，默认为函数名
        description: 工具描述，默认为函数文档字符串
        category: 工具分类
        permission_level: 权限级别
        tags: 标签列表
        **metadata: 其他元数据

    Returns:
        装饰器函数
    """

    def decorator(func: ToolFunction) -> ToolFunction:
        # 应用工具包装器
        wrapped_func = tool_wrapper(func)

        # 确定工具名称
        tool_name = name or func.__name__

        # 应用OpenAI Agent SDK的function_tool装饰器
        tool_func = function_tool(
            wrapped_func,
            name_override=tool_name,
            description_override=description or func.__doc__
        )

        # 保存原始函数的引用，方便后续直接调用
        # 注意：这是我们自己添加的属性，不是OpenAI Agent SDK的标准属性
        setattr(tool_func, 'original_function', wrapped_func)

        # 添加元数据
        tool_func.metadata = {
            "name": tool_name,
            "description": description or func.__doc__,
            "category": category,
            "permission_level": permission_level,
            "tags": tags or [],
            **metadata
        }

        # 注册工具到工具管理器
        tool_manager.register_tool(tool_func)

        logger.info(f"已注册工具: {tool_name}, 分类: {category}, 权限级别: {permission_level}")

        return tool_func

    return decorator


def discover_tools(tools_dir: Optional[str] = None) -> List[str]:
    """
    自动发现工具模块 - 扫描工具目录并导入所有工具模块

    Args:
        tools_dir: 工具目录路径，默认为当前模块所在目录

    Returns:
        已加载的模块名称列表
    """
    if tools_dir is None:
        tools_dir = os.path.dirname(__file__)

    tools_path = Path(tools_dir)
    loaded_modules = []

    # 扫描目录中的Python文件
    for py_file in tools_path.glob("*.py"):
        if py_file.name.startswith("__") or py_file.name == "tool_registry.py":
            continue

        module_name = py_file.stem
        full_module_name = f"agent_cores.tools.{module_name}"

        try:
            # 动态导入模块
            importlib.import_module(full_module_name)
            loaded_modules.append(module_name)
            logger.info(f"已加载工具模块: {module_name}")
        except Exception as e:
            logger.error(f"导入工具模块 {module_name} 失败: {str(e)}")

    return loaded_modules


def register_function_dynamically(func: Callable, **kwargs) -> Optional[FunctionTool]:
    """
    动态注册函数为工具 - 在运行时注册任意函数为工具

    Args:
        func: 要注册的函数
        **kwargs: 工具元数据

    Returns:
        注册的工具或None（如果注册失败）
    """
    try:
        # 应用工具包装器
        wrapped_func = tool_wrapper(func)

        # 获取函数元数据
        name = kwargs.get("name", func.__name__)
        description = kwargs.get("description", func.__doc__ or f"{name}工具")

        # 应用OpenAI Agent SDK的function_tool装饰器
        tool_func = function_tool(
            wrapped_func,
            name_override=name,
            description_override=description
        )

        # 保存原始函数的引用，方便后续直接调用
        setattr(tool_func, 'original_function', wrapped_func)

        # 添加元数据
        tool_func.metadata = {
            "name": name,
            "description": description,
            "category": kwargs.get("category", "general"),
            "permission_level": kwargs.get("permission_level", "basic"),
            "tags": kwargs.get("tags", []),
            **{k: v for k, v in kwargs.items() if
               k not in ["name", "description", "category", "permission_level", "tags"]}
        }

        # 注册工具到工具管理器
        tool_manager.register_tool(tool_func)

        logger.info(f"已动态注册工具: {name}")
        return tool_func

    except Exception as e:
        logger.error(f"动态注册工具失败: {str(e)}")
        return None


def register_all_tools():
    """注册所有工具 - 自动发现并注册所有工具"""
    discover_tools()
    logger.info(f"已注册 {len(tool_manager.tools)} 个工具")


# 自动执行注册
if __name__ == "__main__":
    register_all_tools()