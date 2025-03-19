"""
Handoffs集成测试 - 验证Handoffs机制是否正常工作

本测试验证以下几点：
1. 扩展模块能否正确导入
2. 所有组件能否正常工作
3. 基本的Handoff功能是否可用
"""

import os
import sys
import logging
import asyncio
import importlib
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 首先加载环境变量
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(".env_development"))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_import_extensions():
    """测试导入扩展模块"""
    logger.info("测试1: 导入扩展模块")
    try:
        # 尝试直接导入扩展模块
        import agent_cores.extensions
        logger.info("✓ 成功导入agent_cores.extensions模块")
        
        # 尝试导入具体组件
        from agent_cores.extensions import (
            handoff, Handoff, HandoffInputData,
            remove_all_tools, keep_user_messages_only,
            summarize_history, custom_filter,
            RECOMMENDED_PROMPT_PREFIX, prompt_with_handoff_instructions
        )
        
        # 验证所有组件都已成功导入
        all_components = [
            handoff, Handoff, HandoffInputData,
            remove_all_tools, keep_user_messages_only,
            summarize_history, custom_filter,
            RECOMMENDED_PROMPT_PREFIX, prompt_with_handoff_instructions
        ]
        
        all_imported = all(component is not None for component in all_components)
        if all_imported:
            logger.info("✓ 所有扩展组件导入成功")
        else:
            missing = [comp for comp, val in zip(
                ["handoff", "Handoff", "HandoffInputData", 
                 "remove_all_tools", "keep_user_messages_only",
                 "summarize_history", "custom_filter",
                 "RECOMMENDED_PROMPT_PREFIX", "prompt_with_handoff_instructions"],
                all_components) if val is None]
            logger.error(f"✗ 部分组件导入失败: {', '.join(missing)}")
            
        return all_imported
            
    except ImportError as e:
        logger.error(f"✗ 导入extensions模块失败: {str(e)}")
        return False


async def test_import_from_core():
    """测试从核心模块导入扩展组件"""
    logger.info("测试2: 从核心模块导入扩展组件")
    try:
        # 尝试从核心模块导入扩展组件
        from agent_cores.core import (
            handoff, Handoff, HandoffInputData,
            remove_all_tools, keep_user_messages_only,
            summarize_history, custom_filter,
            RECOMMENDED_PROMPT_PREFIX, prompt_with_handoff_instructions
        )
        
        # 验证所有组件都已成功导入
        all_components = [
            handoff, Handoff, HandoffInputData,
            remove_all_tools, keep_user_messages_only,
            summarize_history, custom_filter,
            RECOMMENDED_PROMPT_PREFIX, prompt_with_handoff_instructions
        ]
        
        all_imported = all(component is not None for component in all_components)
        if all_imported:
            logger.info("✓ 从核心模块导入扩展组件成功")
        else:
            missing = [comp for comp, val in zip(
                ["handoff", "Handoff", "HandoffInputData", 
                 "remove_all_tools", "keep_user_messages_only",
                 "summarize_history", "custom_filter",
                 "RECOMMENDED_PROMPT_PREFIX", "prompt_with_handoff_instructions"],
                all_components) if val is None]
            logger.error(f"✗ 部分组件从核心模块导入失败: {', '.join(missing)}")
            
        return all_imported
            
    except ImportError as e:
        logger.error(f"✗ 从核心模块导入扩展组件失败: {str(e)}")
        return False


async def test_create_handoff():
    """测试创建Handoff对象"""
    logger.info("测试3: 创建Handoff对象")
    try:
        # 导入所需组件
        from agents import Agent
        from agent_cores.extensions import handoff, Handoff
        
        # 创建一个基本的代理对象
        test_agent = Agent(name="测试代理")
        
        # 使用handoff函数创建Handoff对象
        test_handoff = handoff(
            agent=test_agent,
            tool_name_override="test_handoff",
            tool_description_override="测试用Handoff工具"
        )
        
        # 验证Handoff对象属性
        if isinstance(test_handoff, Handoff):
            logger.info(f"✓ 成功创建Handoff对象")
            logger.info(f"  - 工具名称: {test_handoff.tool_name}")
            logger.info(f"  - 工具描述: {test_handoff.tool_description}")
            return True
        else:
            logger.error(f"✗ 创建的对象不是Handoff类型")
            return False
            
    except Exception as e:
        logger.error(f"✗ 创建Handoff对象失败: {str(e)}")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("开始运行Handoffs集成测试...")
    
    # 测试1: 导入扩展模块
    test1_result = await test_import_extensions()
    
    # 测试2: 从核心模块导入扩展组件
    test2_result = await test_import_from_core()
    
    # 测试3: 创建Handoff对象
    test3_result = await test_create_handoff()
    
    # 报告测试结果
    logger.info("\n测试结果汇总:")
    logger.info(f"测试1 (导入扩展模块): {'通过' if test1_result else '失败'}")
    logger.info(f"测试2 (从核心模块导入): {'通过' if test2_result else '失败'}")
    logger.info(f"测试3 (创建Handoff对象): {'通过' if test3_result else '失败'}")
    
    # 总体结果
    if all([test1_result, test2_result, test3_result]):
        logger.info("\n✅ 所有测试通过! Handoffs机制集成成功!")
    else:
        logger.error("\n❌ 测试失败! 请检查错误信息并修复问题。")


if __name__ == "__main__":
    asyncio.run(run_all_tests()) 