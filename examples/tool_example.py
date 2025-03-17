"""
工具测试模块 - 展示如何在Agent系统中使用工具

该模块演示了如何:
1. 注册和管理工具
2. 从工具对象获取原始函数
3. 通过工具管理器执行工具
4. 模拟Agent系统如何使用工具
"""
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入工具和上下文类
from agent_cores.core.agent_context import AgentContext
from agent_cores.core.context_utils import create_context_wrapper
from agent_cores.tools.tool_manager import tool_manager
from agent_cores.tools.register_tools import register_all_tools
# 确保导入上下文工具，虽然我们不会直接使用它们，但这保证了它们被Python解释器加载


def create_test_context() -> AgentContext:
    """
    创建测试上下文
    
    Returns:
        测试上下文对象
    """
    # 创建测试消息历史
    messages = [
        {"role": "system", "content": "你是一个有用的助手。"},
        {"role": "user", "content": "你好，我需要一些帮助。"},
        {"role": "assistant", "content": "你好！我很乐意帮助你。请告诉我你需要什么帮助？"},
        {"role": "user", "content": "我想了解如何使用这个平台的工具。"}
    ]
    
    # 创建上下文对象
    context = AgentContext(
        user_id="user123",
        user_name="测试用户",
        messages=messages,
        metadata={
            "session_id": "test_session_001",
            "client_info": {
                "device": "Web Browser",
                "os": "Windows 11"
            }
        },
        permissions={
            "use_calculator": True,
            "access_user_info": True,
            "read_files": False
        }
    )
    
    return context


def test_tools():
    """测试工具功能"""
    # 确保工具已注册
    if len(tool_manager.tools) == 0:
        register_all_tools()
        
    # 列出所有可用工具
    logger.info(f"可用工具数量: {len(tool_manager.tools)}")
    logger.info(f"可用工具列表: {', '.join(tool_manager.tools.keys())}")
    
    # 创建测试上下文
    context = create_test_context()
    wrapped_context = create_context_wrapper(context)
    
    logger.info("=" * 50)
    logger.info("测试工具函数")
    logger.info("=" * 50)
    
    # 测试获取用户信息
    logger.info("\n\n1. 获取用户信息")
    try:
        user_info_result = tool_manager.execute_tool("get_user_info_tool", wrapped_context)
        print_tool_result("获取用户信息", user_info_result)
    except Exception as e:
        logger.error(f"执行用户信息工具出错: {str(e)}")
    
    # 测试获取对话历史
    logger.info("\n\n2. 获取对话历史")
    try:
        history_result = tool_manager.execute_tool(
            "get_conversation_history_tool", 
            limit=3, 
            ctx=wrapped_context
        )
        print_tool_result("获取对话历史", history_result)
    except Exception as e:
        logger.error(f"执行对话历史工具出错: {str(e)}")
    
    # 测试权限检查
    logger.info("\n\n3. 检查权限")
    try:
        permission_result1 = tool_manager.execute_tool(
            "check_permission_tool",
            permission="use_calculator", 
            ctx=wrapped_context
        )
        print_tool_result("检查计算器权限", permission_result1)
        
        permission_result2 = tool_manager.execute_tool(
            "check_permission_tool",
            permission="read_files", 
            ctx=wrapped_context
        )
        print_tool_result("检查文件读取权限", permission_result2)
    except Exception as e:
        logger.error(f"执行权限检查工具出错: {str(e)}")
    
    # 测试计算器
    logger.info("\n\n4. 使用计算器")
    try:
        calc_result1 = tool_manager.execute_tool("calculator_tool", "2 + 2 * 3")
        print_tool_result("计算 2 + 2 * 3", calc_result1)
        
        calc_result2 = tool_manager.execute_tool("calculator_tool", "(10 + 5) / 3 + sqrt(16)")
        print_tool_result("计算 (10 + 5) / 3 + sqrt(16)", calc_result2)
    except Exception as e:
        logger.error(f"执行计算器工具出错: {str(e)}")
    
    # 测试单位转换
    logger.info("\n\n5. 单位转换")
    try:
        conv_result1 = tool_manager.execute_tool(
            "converter_tool", 
            value=100, 
            from_unit="cm", 
            to_unit="m"
        )
        print_tool_result("转换 100 厘米到米", conv_result1)
        
        conv_result2 = tool_manager.execute_tool(
            "converter_tool", 
            value=25, 
            from_unit="c", 
            to_unit="f"
        )
        print_tool_result("转换 25 摄氏度到华氏度", conv_result2)
    except Exception as e:
        logger.error(f"执行单位转换工具出错: {str(e)}")
    
    logger.info("=" * 50)
    logger.info("工具测试完成")
    logger.info("=" * 50)


def test_agent_tools_integration():
    """
    测试工具在Agent系统中的集成
    
    这个函数模拟了Agent系统如何使用工具的典型场景
    """
    # 1. 注册所有工具
    register_all_tools()
    
    # 2. 获取工具列表 - 在实际应用中，这些工具会被传递给Agent
    available_tools = list(tool_manager.tools.values())
    logger.info(f"为Agent配置了 {len(available_tools)} 个工具")
    
    # 3. 创建测试上下文
    context = create_test_context()
    wrapped_context = create_context_wrapper(context)
    
    logger.info("=" * 50)
    logger.info("模拟Agent使用工具")
    logger.info("=" * 50)
    
    # 4. 模拟Agent接收用户输入并选择工具
    user_input = "帮我计算 (10 + 5) * 2 是多少"
    logger.info(f"用户输入: {user_input}")
    
    logger.info("Agent决定使用计算器工具...")
    
    # 5. 模拟Agent执行工具
    try:
        expression = "(10 + 5) * 2"  # 通常由Agent从用户输入中提取
        result = tool_manager.execute_tool("calculator_tool", expression)
        
        # 6. 模拟Agent根据工具结果生成回复
        if result.get("success", False):
            agent_response = f"根据计算，(10 + 5) * 2 = {result.get('result', 'unknown')}"
        else:
            agent_response = f"很抱歉，我在计算时遇到了问题: {result.get('message', '未知错误')}"
            
        logger.info(f"Agent回复: {agent_response}")
        
    except Exception as e:
        logger.error(f"Agent使用工具时出错: {str(e)}")
    
    logger.info("=" * 50)
    logger.info("Agent工具集成测试完成")
    logger.info("=" * 50)


def print_tool_result(title: str, result: Dict[str, Any]):
    """
    打印工具结果
    
    Args:
        title: 标题
        result: 工具结果
    """
    print(f"\n--- {title} ---")
    
    if result.get("success", False):
        print("✅ 成功")
    else:
        print("❌ 失败")
    
    for key, value in result.items():
        if key != "success":
            print(f"  {key}: {value}")


if __name__ == "__main__":
    # 测试工具功能
    test_tools()
    
    # 测试工具在Agent中的集成
    test_agent_tools_integration() 