"""
工具注册模块 - 负责向工具管理器注册所有可用工具
"""
import logging
from typing import Any, Dict

# 配置日志
logger = logging.getLogger(__name__)

# 导入工具管理器
from agent_cores.tools.core.tool_manager import tool_manager

# 导入工具注册装饰器和工具发现函数
from agent_cores.tools.core.tool_registry import register_tool, discover_tools, register_function_dynamically

# 导入OpenAI Agent SDK

# 导入工具
from agent_cores.tools.data.database import DatabaseManager
from agent_cores.tools.data.file import FileManager


# 导入RBAC工具 - 这些已经被@function_tool装饰，无需再注册
# 导入上下文工具


@register_tool(
    name="search",
    description="搜索互联网获取最新信息",
    category="search",
    tags=["web", "search"]
)
def search(query: str) -> Dict[str, Any]:
    """搜索互联网获取最新信息
    
    Args:
        query: 搜索查询
        
    Returns:
        Dict: 搜索结果
    """
    # 实际情况下，应当调用搜索API获取结果
    # 这里仅返回模拟数据
    logger.info(f"执行网络搜索: {query}")
    
    return {
        "query": query,
        "results": [
            {
                "title": f"关于 {query} 的搜索结果1",
                "snippet": f"这是关于 {query} 的简短描述1...",
                "url": f"https://example.com/result1-{query}"
            },
            {
                "title": f"关于 {query} 的搜索结果2",
                "snippet": f"这是关于 {query} 的简短描述2...",
                "url": f"https://example.com/result2-{query}"
            }
        ],
        "total_results": 2,
        "error": False
    }


@register_tool(
    name="calculator",
    description="执行数学计算",
    category="math",
    tags=["math", "calculation"]
)
def calculator(expression: str) -> Dict[str, Any]:
    """执行数学计算
    
    Args:
        expression: 要计算的数学表达式
        
    Returns:
        Dict: 计算结果
    """
    # 这里实际上可以直接调用我们已有的calculate函数
    # 但为了保持工具名称一致，我们单独实现
    logger.info(f"计算表达式: {expression}")
    
    try:
        # 安全计算
        result = eval(expression, {"__builtins__": {}}, {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'sum': sum, 'pow': pow, 'int': int, 'float': float
        })
        
        return {
            "expression": expression,
            "result": result,
            "error": False
        }
    except Exception as e:
        logger.error(f"计算错误: {str(e)}")
        return {
            "expression": expression,
            "error": True,
            "message": f"计算错误: {str(e)}"
        }


def register_all_tools():
    """
    注册所有可用的工具到工具管理器
    
    注册方式:
    1. 部分工具通过装饰器自动注册
    2. 部分工具在此函数中手动注册
    3. 其余工具通过自动发现机制注册
    """
    # 使用装饰器注册的工具不需要在这里再次注册
    
    # 注意：RBAC工具已经被@function_tool装饰，无需再次注册
    # 这些工具会由discover_tools()自动发现并注册
    
    # 上下文工具已通过装饰器注册，不需要在这里手动注册
    
    # 创建和注册类实例方法工具
    db_manager = DatabaseManager()
    file_manager = FileManager()
    
    # 注册数据库工具
    register_function_dynamically(db_manager.search_database, 
                                category="database", 
                                tags=["database", "search"])
    register_function_dynamically(db_manager.insert_record, 
                                category="database", 
                                tags=["database", "insert"])
    register_function_dynamically(db_manager.update_record, 
                                category="database", 
                                tags=["database", "update"])
    register_function_dynamically(db_manager.delete_record, 
                                category="database", 
                                tags=["database", "delete"])
    register_function_dynamically(db_manager.execute_query, 
                                category="database", 
                                tags=["database", "query"])
    
    # 注册文件工具
    register_function_dynamically(file_manager.read_file, 
                                category="file", 
                                tags=["file", "read"])
    register_function_dynamically(file_manager.write_file, 
                                category="file", 
                                tags=["file", "write"])
    register_function_dynamically(file_manager.list_files, 
                                category="file", 
                                tags=["file", "list"])
    
    # 自动发现并注册其他工具
    discover_tools()
    
    logger.info(f"已注册 {len(tool_manager.tools)} 个工具")


# 仅在作为主模块运行时自动执行注册
if __name__ == "__main__":
    register_all_tools() 