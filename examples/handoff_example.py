"""
Handoffs示例 - 演示如何实现代理间的任务委托

本示例展示如何使用OpenAI Agent SDK的Handoffs机制实现代理间的任务委托，
适用于多代理协作系统，如客服分诊、专家咨询等场景。
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 首先加载环境变量，确保在导入其他模块前完成
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(".env_development"))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入运行时服务和模板管理器
from agent_cores.core.runtime import runtime_service
from agent_cores.core.template_manager import template_manager

# 导入OpenAI Agent SDK相关组件
from agents import Agent, handoff

# 导入上下文管理
from agent_cores.core.simple_context import SimpleContext

# 导入过滤器
from agent_cores.extensions.handoff_filters import summarize_history

# 定义转交原因数据模型 - 使用最简单的定义
class HandoffReason(BaseModel):
    """转交原因数据模型"""
    reason: str
    details: Optional[str] = None


async def setup_triage_agent() -> Agent:
    """
    设置简单的分诊代理
    
    使用标准SDK方式配置Handoff，不添加复杂的过滤器或处理
    """
    # 确保模板已注册
    register_agent_templates()
    
    # 获取基本分诊代理
    triage_agent = template_manager.get_template("triage_agent")
    travel_agent = template_manager.get_template("travel_agent")
    finance_agent = template_manager.get_template("finance_agent")
    
    if not triage_agent or not travel_agent or not finance_agent:
        logger.error("无法加载代理模板")
        raise ValueError("代理模板不存在")
        
    logger.info("成功加载所有代理模板")
    
    # 创建必需的回调函数
    async def on_travel_handoff(ctx, input_data):
        """旅游专家handoff回调函数"""
        logger.info(f"正在转交给旅游专家处理: {getattr(input_data, 'reason', '未提供原因')}")
        return {"success": True}
    
    async def on_finance_handoff(ctx, input_data):
        """金融专家handoff回调函数"""
        # 增加详细日志
        logger.info(f"正在转交给金融专家处理: {getattr(input_data, 'reason', '未提供原因')}")
        logger.info(f"金融专家Handoff输入数据类型: {type(input_data)}")
        logger.info(f"金融专家Handoff输入数据内容: {input_data}")
        return {"success": True}
    
    # 原生SDK方式创建handoff
    travel_handoff = handoff(
        agent=travel_agent,
        input_type=HandoffReason,
        on_handoff=on_travel_handoff,  # 添加必需的回调函数
        tool_name_override="transfer_to_travel_expert",
        tool_description_override="将旅游相关问题转交给旅游专家处理"
    )
    
    finance_handoff = handoff(
        agent=finance_agent,
        input_type=HandoffReason,
        on_handoff=on_finance_handoff,  # 添加必需的回调函数
        tool_name_override="transfer_to_finance_expert",
        tool_description_override="将金融、投资、理财相关问题转交给金融专家处理"
    )
    
    # 记录handoff类型信息
    logger.info(f"旅游Handoff类型: {type(travel_handoff)}")
    logger.info(f"金融Handoff类型: {type(finance_handoff)}")
    
    # 克隆代理，添加非常明确的指令，强化金融问题识别
    final_agent = triage_agent.clone(
        handoffs=[travel_handoff, finance_handoff],
        instructions="""
你是客服中心的分诊助手，你的唯一任务是识别用户问题类型并将专业问题转交给对应专家。

重要规则:
1. 你不能自己回答专业问题，必须转交给对应专家
2. 对于问候或简单问题可以简短回答
3. 发现专业问题后立即使用转交工具
4. 不要询问用户是否需要转交，直接判断并转交

旅游问题判断标准:
- 提到旅游目的地、景点、酒店、行程
- 例如: 三亚旅游、北京景点、酒店推荐等
- 使用: transfer_to_travel_expert工具

金融问题判断标准(立即识别并转交):
- 提到投资、理财、资金、资本、金额、股票、基金等
- 提到具体金额如"10万元"、"5000元"等
- 提到投资渠道如基金、股票、理财产品等
- 例如: "10万元投资"、"理财建议"、"资金分配"等
- 只要涉及金钱投资相关问题，立即使用: transfer_to_finance_expert工具

当看到任何与金钱金额和投资理财相关的问题，你必须立即转交给金融专家，不要尝试自己回答。
"""
    )
    
    # 记录最终代理信息
    logger.info(f"分诊代理设置完成: {final_agent.name}")
    
    return final_agent


async def run_handoff_conversation():
    """
    运行对话示例 - 简化版本
    """
    try:
        # 创建分诊代理
        triage_agent = await setup_triage_agent()
        
        # 创建上下文
        context = SimpleContext(
            user_id="user123",
            user_name="张先生"
        )
        
        # 创建会话
        session_id = runtime_service.create_session(user_id=context.user_id)
        
        # 对话内容
        conversation = [
            "你好，我是张先生，我想了解一些信息",
            "今年暑假带家人去三亚旅游，有什么好的景点和酒店推荐？",
            "另外，我有10万元想做一些投资理财，有什么建议？"
        ]
        
        # 进行对话
        for message in conversation:
            print(f"\n用户: {message}")
            
            # 运行代理 - 使用最简单的方式
            result = await runtime_service.run_agent(
                agent=triage_agent,
                input_text=message,
                session_id=session_id
            )
            
            # 添加更多日志分析结果
            logger.info(f"代理返回结果类型: {type(result)}")
            logger.info(f"代理返回结果键: {result.keys() if isinstance(result, dict) else 'N/A'}")
            
            # 处理结果
            if 'error' in result and result['error']:
                print(f"\n系统错误: {result['error']}")
                continue
                
            # 检查是否有handoff items
            if 'items' in result and result['items']:
                logger.info(f"发现items项: {result['items']}")
                for item in result['items']:
                    if item.get('type') == 'handoff_result':
                        logger.info(f"处理handoff结果: {item}")
            
            # 打印输出
            output = result.get('output', '')
            print(f"\n回复: {output}")
            
    except Exception as e:
        logger.exception(f"运行对话示例时出错: {str(e)}")
        print(f"\n系统错误: {str(e)}")


# 创建并注册专家代理模板，确保它们存在
def register_agent_templates():
    """注册基础模板，确保它们存在"""
    # 检查并注册旅游专家
    travel_template = template_manager.get_template("travel_agent")
    if travel_template is None:
        travel_agent = Agent(
            name="旅游专家",
            instructions="您是一位专业的旅游顾问，擅长提供各类旅游建议、景点推荐、行程规划等服务。\n\n"
                       "用户信息:\n- 用户ID: {user_id}\n- 用户名称: {user_name}",
        )
        template_manager.register_template("travel_agent", travel_agent)
        logger.info("已注册旅游专家模板")
    
    # 检查并注册金融专家
    finance_template = template_manager.get_template("finance_agent")
    if finance_template is None:
        finance_agent = Agent(
            name="金融专家",
            instructions="您是一位专业的金融顾问，擅长提供投资建议、理财规划、风险评估等金融服务。\n\n"
                       "用户信息:\n- 用户ID: {user_id}\n- 用户名称: {user_name}",
        )
        template_manager.register_template("finance_agent", finance_agent)
        logger.info("已注册金融专家模板")
    
    # 检查并注册分诊代理
    triage_template = template_manager.get_template("triage_agent")
    if triage_template is None:
        triage_agent = Agent(
            name="客服分诊助手",
            instructions="您是一位专业的客服分诊助手，负责将用户问题转交给相应的专家处理。\n\n"
                       "用户信息:\n- 用户ID: {user_id}\n- 用户名称: {user_name}",
        )
        template_manager.register_template("triage_agent", triage_agent)
        logger.info("已注册分诊代理模板")


async def main():
    """主函数"""
    # 确保模板已加载
    template_manager.ensure_loaded()
    
    # 注册必要的代理模板
    register_agent_templates()
    
    # 运行对话示例
    await run_handoff_conversation()


if __name__ == "__main__":
    asyncio.run(main()) 