"""
工具管理模块 - 负责注册、发现和管理代理工具
"""
import os
import sys
import logging
import inspect
from typing import Dict, List, Any, Optional, Callable, TypeVar, Set, Union, get_type_hints
from dataclasses import dataclass, field
import functools
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logger = logging.getLogger(__name__)

# 导入OpenAI Agent SDK
from agents import function_tool, FunctionTool, ComputerTool, WebSearchTool, FileSearchTool
from agents.run_context import RunContextWrapper

# 类型定义
T = TypeVar('T')
ToolFunction = Callable[..., Any]


@dataclass
class ToolMetadata:
    """工具元数据"""
    category: str = "general"  # 工具分类
    permission_level: str = "basic"  # 权限级别: basic, advanced, admin
    rate_limit: Optional[int] = None  # 每分钟调用限制
    description: Optional[str] = None  # 额外描述
    version: str = "1.0.0"  # 工具版本
    tags: List[str] = field(default_factory=list)  # 标签列表
    custom_data: Dict[str, Any] = field(default_factory=dict)  # 自定义数据


class ToolManager:
    """
    工具管理器 - 管理所有可用的工具

    主要功能:
    1. 注册和管理工具
    2. 工具发现和过滤
    3. 工具权限检查
    """

    def __init__(self):
        self.tools: Dict[str, Any] = {}  # 工具注册表
        self.categories: Dict[str, Set[str]] = {}  # 分类到工具名称的映射
        self.permission_levels: Dict[str, Set[str]] = {}  # 权限级别到工具名称的映射

    def tool(self,
             category: str = "general",
             permission_level: str = "basic",
             **metadata) -> Callable[[ToolFunction], ToolFunction]:
        """
        工具注册装饰器

        用法:
        @tool_manager.tool(category="search", permission_level="basic")
        def search_web(query: str) -> str:
            ...

        Args:
            category: 工具分类
            permission_level: 权限级别
            **metadata: 其他元数据

        Returns:
            装饰器函数
        """

        def decorator(func: ToolFunction) -> ToolFunction:
            # 使用OpenAI SDK的function_tool装饰器
            tool_func = function_tool(func)

            # 添加元数据
            tool_metadata = ToolMetadata(
                category=category,
                permission_level=permission_level,
                **metadata
            )
            tool_func.metadata = tool_metadata

            # 注册工具
            self._register_tool(tool_func)

            return tool_func

        return decorator

    def _register_tool(self, tool: Any) -> None:
        """
        内部方法：注册工具到管理器

        Args:
            tool: 工具函数或工具对象
        """
        # 获取工具名称
        if hasattr(tool, '__tool_name__'):
            name = tool.__tool_name__
        elif isinstance(tool, FunctionTool):
            name = tool.name
        elif isinstance(tool, (WebSearchTool, ComputerTool, FileSearchTool)):
            name = tool.__class__.__name__
        else:
            name = tool.__name__

        # 注册工具
        self.tools[name] = tool

        # 获取工具元数据
        metadata = getattr(tool, 'metadata', ToolMetadata())

        # 更新分类索引
        # 处理metadata可能是字典的情况
        if isinstance(metadata, dict):
            category = metadata.get('category', 'general')
        else:
            category = metadata.category

        if category not in self.categories:
            self.categories[category] = set()
        self.categories[category].add(name)

        # 更新权限级别索引
        # 处理metadata可能是字典的情况
        if isinstance(metadata, dict):
            permission_level = metadata.get('permission_level', 'basic')
        else:
            permission_level = metadata.permission_level

        if permission_level not in self.permission_levels:
            self.permission_levels[permission_level] = set()
        self.permission_levels[permission_level].add(name)

        logger.info(f"已注册工具: {name}, 分类: {category}, 权限: {permission_level}")

    def register_tool(self, tool: Any) -> None:
        """
        注册已有工具

        Args:
            tool: 工具函数或工具对象
        """
        self._register_tool(tool)

    def get_tool(self, name: str) -> Optional[Any]:
        """
        获取指定名称的工具

        Args:
            name: 工具名称

        Returns:
            工具对象，如果不存在则返回None
        """
        return self.tools.get(name)

    def find_tools(self,
                   category: Optional[str] = None,
                   permission_level: Optional[str] = None,
                   tag: Optional[str] = None) -> List[Any]:
        """
        根据条件查找工具

        Args:
            category: 工具分类
            permission_level: 权限级别
            tag: 标签

        Returns:
            符合条件的工具列表
        """
        # 首先按分类过滤
        if category and category in self.categories:
            tool_names = self.categories[category]
        else:
            tool_names = set(self.tools.keys())

        # 按权限级别过滤
        if permission_level and permission_level in self.permission_levels:
            tool_names = tool_names.intersection(self.permission_levels[permission_level])

        # 按标签过滤
        if tag:
            filtered_names = set()
            for name in tool_names:
                tool = self.tools[name]
                metadata = getattr(tool, 'metadata', None)
                if metadata:
                    # 处理metadata可能是字典的情况
                    if isinstance(metadata, dict):
                        tags = metadata.get('tags', [])
                    else:
                        tags = metadata.tags

                    if tag in tags:
                        filtered_names.add(name)
            tool_names = filtered_names

        # 获取工具对象
        return [self.tools[name] for name in tool_names]

    def check_permission(self,
                         tool_name: str,
                         user_permission_level: str) -> bool:
        """
        检查用户是否有权限使用工具

        Args:
            tool_name: 工具名称
            user_permission_level: 用户权限级别

        Returns:
            是否有权限
        """
        if tool_name not in self.tools:
            return False

        tool = self.tools[tool_name]
        metadata = getattr(tool, 'metadata', ToolMetadata())

        # 处理metadata可能是字典的情况
        if isinstance(metadata, dict):
            tool_permission = metadata.get('permission_level', 'basic')
        else:
            tool_permission = metadata.permission_level

        # 权限级别层次
        levels = ["basic", "advanced", "admin"]

        # 检查用户权限是否足够
        user_level = levels.index(user_permission_level) if user_permission_level in levels else -1
        tool_level = levels.index(tool_permission) if tool_permission in levels else 0

        return user_level >= tool_level

    def get_original_function(self, tool_name: str):
        """
        获取工具的原始函数

        Args:
            tool_name: 工具名称

        Returns:
            原始函数，如果找不到则返回None
        """
        if tool_name not in self.tools:
            return None

        tool = self.tools[tool_name]

        # 首先检查我们添加的original_function属性
        if hasattr(tool, 'original_function'):
            return tool.original_function

        # 尝试不同的方法获取原始函数
        for attr_name in ['function', '_function', '__wrapped__', '_func']:
            if hasattr(tool, attr_name):
                return getattr(tool, attr_name)

        # 如果工具对象本身可调用，直接返回
        if callable(tool):
            return tool

        # 如果找不到原始函数，返回None
        return None

    def execute_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """
        直接执行指定的工具

        这个方法提供了一个统一的接口来执行任何工具，无论它是如何注册的。
        它会自动尝试找到正确的函数并执行它。

        Args:
            tool_name: 工具名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            工具执行结果

        Raises:
            ValueError: 如果工具不存在或无法执行
        """
        if tool_name not in self.tools:
            raise ValueError(f"工具 '{tool_name}' 不存在")

        # 获取原始函数
        func = self.get_original_function(tool_name)
        if not func:
            raise ValueError(f"无法获取工具 '{tool_name}' 的可执行函数")

        try:
            # 执行函数
            logger.info(f"执行工具函数: {tool_name}, 参数: {args}, 关键字参数: {kwargs}")
            result = func(*args, **kwargs)
            logger.info(f"工具函数 {tool_name} 执行成功")
            return result
        except Exception as e:
            logger.error(f"执行工具 '{tool_name}' 时出错: {str(e)}")
            # 返回标准化的错误响应
            return {
                "success": False,
                "error": True,
                "message": f"工具执行错误: {str(e)}",
                "error_type": type(e).__name__
            }

    def batch_execute_tools(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量执行多个工具

        Args:
            executions: 工具执行配置列表，每项包含:
                        - tool_name: 工具名称
                        - args: 位置参数 (可选)
                        - kwargs: 关键字参数 (可选)

        Returns:
            包含每个工具执行结果的字典，键为工具名称
        """
        results = {}

        for exec_config in executions:
            tool_name = exec_config.get("tool_name")
            if not tool_name:
                continue

            args = exec_config.get("args", [])
            kwargs = exec_config.get("kwargs", {})

            try:
                results[tool_name] = self.execute_tool(tool_name, *args, **kwargs)
            except Exception as e:
                results[tool_name] = {
                    "success": False,
                    "error": True,
                    "message": f"执行失败: {str(e)}"
                }

        return results

    def create_computer_tool(self,
                             allowed_executables: Optional[List[str]] = None,
                             environment: Optional[Dict[str, str]] = None) -> ComputerTool:
        """
        创建计算机工具

        Args:
            allowed_executables: 允许执行的可执行文件列表
            environment: 环境变量

        Returns:
            ComputerTool实例
        """
        tool = ComputerTool()
        # 这里可以配置ComputerTool的特定设置
        return tool

    def create_web_search_tool(self) -> WebSearchTool:
        """
        创建网络搜索工具

        Returns:
            WebSearchTool实例
        """
        return WebSearchTool()

    def create_file_search_tool(self,
                                vector_store_ids: List[str],
                                max_results: int = 5) -> FileSearchTool:
        """
        创建文件搜索工具

        Args:
            vector_store_ids: 向量存储ID列表
            max_results: 最大结果数

        Returns:
            FileSearchTool实例
        """
        return FileSearchTool(
            vector_store_ids=vector_store_ids,
            max_num_results=max_results
        )


# 创建全局工具管理器实例
tool_manager = ToolManager()

# 示例用法
if __name__ == "__main__":
    @tool_manager.tool(category="search", tags=["web"])
    def search_web(query: str) -> str:
        """
        搜索网络获取信息

        Args:
            query: 搜索查询
        """
        return f"网络搜索结果: {query}"


    @tool_manager.tool(category="compute", permission_level="advanced")
    def calculate(context: RunContextWrapper, expression: str) -> str:
        """
        执行数学计算

        Args:
            expression: 数学表达式
        """
        try:
            result = eval(expression)
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {e}"


    # 测试工具查找
    search_tools = tool_manager.find_tools(category="search")
    print(f"搜索工具: {[getattr(t, 'name', getattr(t, '__tool_name__', 'unknown')) for t in search_tools]}")

    # 测试权限检查
    has_permission = tool_manager.check_permission("calculate", "basic")
    print(f"基本用户可以使用计算工具: {has_permission}")

    has_permission = tool_manager.check_permission("calculate", "advanced")
    print(f"高级用户可以使用计算工具: {has_permission}")