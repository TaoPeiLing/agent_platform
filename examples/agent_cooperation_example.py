"""
代理协作示例 - 展示如何使用AgentCooperationService实现代理协作

本示例展示了如何使用AgentCooperationService来实现代理间的任务委托和协作，
包括注册专家代理、创建分诊代理和执行协作对话的完整流程。
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 首先加载环境变量，确保在导入其他模块前完成
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(".env_development"))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入代理协作服务
from agent_cores.services.agent_cooperation_service import agent_cooperation_service

# 导入模板管理器和上下文
from agent_cores.core.template_manager import template_manager
from agent_cores.core.simple_context import SimpleContext

# 导入过滤器
from agent_cores.extensions.handoff_filters import summarize_history

# 创建并注册专家代理模板，确保它们存在
def register_agent_templates():
    """注册基础模板，确保它们存在"""
    from agents import Agent
    
    # 检查并注册旅游专家
    if template_manager.get_template("travel_agent") is None:
        travel_agent = Agent(
            name="旅游专家",
            instructions="您是一位专业的旅游顾问，擅长提供各类旅游建议、景点推荐、行程规划等服务。\n\n"
                       "用户信息:\n- 用户ID: {user_id}\n- 用户名称: {user_name}",
        )
        template_manager.register_template("travel_agent", travel_agent)
        print("已注册旅游专家模板")
    
    # 检查并注册金融专家
    if template_manager.get_template("finance_agent") is None:
        finance_agent = Agent(
            name="金融专家",
            instructions="您是一位专业的金融顾问，擅长提供投资建议、理财规划、风险评估等金融服务。\n\n"
                       "用户信息:\n- 用户ID: {user_id}\n- 用户名称: {user_name}",
        )
        template_manager.register_template("finance_agent", finance_agent)
        print("已注册金融专家模板")
    
    # 检查并注册分诊代理
    if template_manager.get_template("triage_agent") is None:
        triage_agent = Agent(
            name="客服分诊助手",
            instructions="您是一位专业的客服分诊助手，负责将用户问题转交给相应的专家处理。\n\n"
                       "用户信息:\n- 用户ID: {user_id}\n- 用户名称: {user_name}",
        )
        template_manager.register_template("triage_agent", triage_agent)
        print("已注册分诊代理模板")

# 确保模板已注册
register_agent_templates()

# 示例1: 使用装饰器注册专家代理
@agent_cooperation_service.expert(
    name="travel", 
    description="将旅游相关问题转交给旅游专家处理",
    input_filter=summarize_history  # 使用历史摘要过滤器
)
def register_travel_expert():
    """注册旅游专家"""
    return "travel_agent"  # 返回模板名称


@agent_cooperation_service.expert(
    name="finance", 
    description="将金融、投资、理财相关问题转交给金融专家处理"
)
def register_finance_expert():
    """注册金融专家"""
    return "finance_agent"  # 返回模板名称


# 示例2: 使用工厂函数创建分诊代理
def create_triage_agent():
    """创建分诊代理"""
    # 使用工厂方法
    triage_factory = agent_cooperation_service.triage_agent_factory("triage_agent")
    
    # 调用注册函数
    register_travel_expert()
    register_finance_expert()
    
    # 创建分诊代理，使用默认指令
    return triage_factory(["travel", "finance"])


# 示例3: 手动注册和创建
async def manual_setup():
    """手动注册和创建代理"""
    # 注册专家
    agent_cooperation_service.register_expert(
        name="customer_service",
        agent_template="assistant_agent",  # 使用通用助手作为客服专家
        description="将客服相关问题转交给客服专家处理"
    )
    
    # 创建分诊代理
    triage_agent = agent_cooperation_service.create_triage_agent(
        base_agent="triage_agent",
        expert_names=["travel", "finance", "customer_service"],
        instructions="""
你是客服中心的总负责人，负责初步接待用户并将问题分配给合适的专家。

专业问题分配规则:
- 旅游问题 → 旅游专家
- 金融问题 → 金融专家
- 一般客服问题 → 客服专家
        """
    )
    
    return triage_agent


# 示例4: 执行协作对话
async def run_cooperation_conversation():
    """执行协作对话"""
    try:
        # 获取分诊代理
        triage_agent = create_triage_agent()
        
        # 创建上下文
        context = SimpleContext(
            user_id="user456",
            user_name="李女士"
        )
        
        # 对话内容
        conversation = [
            "你好，我是李女士，请问有什么可以帮助我的？",
            "我计划去北京旅游，有什么好的景点推荐吗？",
            "我还有20万元想做一些投资，有什么建议？"
        ]
        
        # 创建会话
        session_id = f"cooperation_demo_{context.user_id}"
        
        # 进行对话
        for message in conversation:
            print(f"\n用户: {message}")
            
            # 使用协作服务执行代理
            result = await agent_cooperation_service.execute_with_cooperation(
                agent=triage_agent,
                input_text=message,
                session_id=session_id,
                context=context
            )
            
            # 打印输出
            output = result.get('output', '')
            print(f"\n回复: {output}")
            
    except Exception as e:
        logger.exception(f"执行协作对话时出错: {str(e)}")
        print(f"\n系统错误: {str(e)}")


# 示例5: 直接转交给专家
async def direct_to_expert():
    """直接转交给专家示例"""
    try:
        # 确保专家已注册
        register_finance_expert()
        
        # 创建上下文
        context = SimpleContext(
            user_id="user789",
            user_name="王先生"
        )
        
        # 创建会话
        session_id = f"direct_expert_demo_{context.user_id}"
        
        # 直接转交给金融专家
        print("\n=== 直接转交给金融专家 ===")
        print("\n用户: 我有50万元想做一些投资，请给我一些建议。")
        
        result = await agent_cooperation_service.direct_handoff_to_expert(
            expert_name="finance",
            user_message="我有50万元想做一些投资，请给我一些建议。",
            reason="用户咨询投资理财问题",
            session_id=session_id,
            context=context
        )
        
        # 打印输出
        output = result.get('output', '')
        print(f"\n金融专家回复: {output}")
        
    except Exception as e:
        logger.exception(f"直接转交给专家时出错: {str(e)}")
        print(f"\n系统错误: {str(e)}")


# 示例6: 使用装饰器为现有函数添加协作处理
@agent_cooperation_service.with_cooperation
async def run_custom_agent(agent, message, session_id=None, context=None):
    """自定义代理执行函数，添加了协作处理功能"""
    from agent_cores.core.runtime import runtime_service
    return await runtime_service.run_agent(
        agent=agent,
        input_text=message,
        session_id=session_id,
        context=context
    )


async def custom_agent_example():
    """自定义代理执行示例"""
    try:
        # 创建分诊代理
        triage_agent = create_triage_agent()
        
        # 创建上下文
        context = SimpleContext(
            user_id="user999",
            user_name="赵先生"
        )
        
        # 创建会话
        session_id = f"custom_demo_{context.user_id}"
        
        # 使用自定义函数
        print("\n=== 使用自定义函数 ===")
        print("\n用户: 我想了解一下北京的旅游景点。")
        
        result = await run_custom_agent(
            agent=triage_agent,
            message="我想了解一下北京的旅游景点。",
            session_id=session_id,
            context=context
        )
        
        # 打印输出
        output = result.get('output', '')
        print(f"\n回复: {output}")
        
    except Exception as e:
        logger.exception(f"使用自定义函数时出错: {str(e)}")
        print(f"\n系统错误: {str(e)}")


async def main():
    """主函数"""
    # 确保模板已加载
    template_manager.ensure_loaded()
    
    print("\n=== 代理协作服务示例 ===")
    
    # 示例4: 执行协作对话
    # await run_cooperation_conversation()
    
    # 示例5: 直接转交给专家
    # await direct_to_expert()
    
    # 示例6: 使用装饰器为现有函数添加协作处理
    # await custom_agent_example()


if __name__ == "__main__":
    asyncio.run(main()) 