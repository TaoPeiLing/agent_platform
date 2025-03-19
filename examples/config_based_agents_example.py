#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基于配置的智能体创建示例

该示例展示如何使用基于配置的方式创建各种类型的智能体，
无需硬编码智能体的创建逻辑。
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 首先加载环境变量，确保在导入其他模块前完成
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(".env_development"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入服务
from agent_cores.services.agent_cooperation_service import agent_cooperation_service
from agent_cores.core.template_manager import template_manager
from agent_cores.core.runtime import runtime_service

# 导入OpenAI Agent SDK
from agents import Agent


async def run_example():
    """运行示例"""
    logger.info("启动基于配置的智能体创建示例")
    
    # 加载智能体配置
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs", "agent_configs.json")
    agent_cooperation_service.load_agent_configs_from_json(config_path)
    
    # 确保模板已加载
    template_manager.ensure_loaded()
    
    # 从agent_configs/agents目录加载现有的模板
    doctor_expert = template_manager.get_template("doctor_expert")
    triage_agent = template_manager.get_template("triage_agent")
    tech_triage = template_manager.get_template("tech_triage")
    software_expert = template_manager.get_template("software_expert")
    hardware_expert = template_manager.get_template("hardware_expert")
    network_expert = template_manager.get_template("network_expert")
    
    # 如果模板不存在，创建基础模板
    if not doctor_expert:
        # 创建基础医生模板
        doctor_expert = Agent(
            name="医疗专科医生",
            model="doubao/ep-20250317114344-dlfz2",
            instructions="你是一名专业医生，请根据你的专业知识回答患者的问题。"
        )
        template_manager.register_template("doctor_expert", doctor_expert)
    
    # 使用配置创建专科医生
    cardiologist = agent_cooperation_service.create_expert_from_config(
        name="cardiology",
        agent_template=doctor_expert,
        config_id="doctor_expert",
        description="心脏科专家，处理心脑血管相关问题"
    )
    
    # 使用工厂方法创建多个专家
    create_doctor = agent_cooperation_service.expert_factory(
        config_id="doctor_expert",
        description_template="专业{agent_name}，解答相关医疗问题"
    )
    
    orthopedist = create_doctor(
        "orthopedics", 
        doctor_expert,
        {"description": "骨科专家，处理骨骼、关节问题"}
    )
    
    neurologist = create_doctor(
        "neurology",
        doctor_expert,
        {"description": "神经科专家，处理神经系统问题"}
    )
    
    # 创建分诊智能体的基础模板
    if not triage_agent:
        # 创建基础助手模板
        triage_agent = Agent(
            name="分诊智能体",
            model="doubao/ep-20250317114344-dlfz2",
            instructions="你是一名医疗分诊助手，负责将患者的问题分配给合适的专科医生。"
        )
        template_manager.register_template("triage_agent", triage_agent)
    
    # 创建技术专家智能体基础模板
    if not software_expert:
        # 创建软件专家模板
        software_expert = Agent(
            name="软件技术专家",
            model="doubao/ep-20250317114344-dlfz2",
            instructions="你是一名软件技术专家，请根据你的专业知识解决用户的软件技术问题。"
        )
        template_manager.register_template("software_expert", software_expert)
    
    if not hardware_expert:
        # 创建硬件专家模板
        hardware_expert = Agent(
            name="硬件技术专家",
            model="doubao/ep-20250317114344-dlfz2",
            instructions="你是一名硬件技术专家，请根据你的专业知识解决用户的硬件问题。"
        )
        template_manager.register_template("hardware_expert", hardware_expert)
    
    if not network_expert:
        # 创建网络专家模板
        network_expert = Agent(
            name="网络技术专家",
            model="doubao/ep-20250317114344-dlfz2",
            instructions="你是一名网络技术专家，请根据你的专业知识解决用户的网络连接问题。"
        )
        template_manager.register_template("network_expert", network_expert)
    
    # 使用配置创建医疗分诊智能体
    medical_triage = agent_cooperation_service.create_agent_from_config(
        config="medical_triage",
        base_agent=triage_agent,
        expert_names=["cardiology", "orthopedics", "neurology"]
    )
    
    # 创建技术分诊智能体
    if not tech_triage:
        tech_triage = Agent(
            name="技术问题分诊助手",
            model="doubao/ep-20250317114344-dlfz2",
            instructions="你是技术支持中心的分诊助手，负责将用户的技术问题分配给合适的专业技术支持人员。"
        )
        template_manager.register_template("tech_triage", tech_triage)
    
    # 从配置创建技术分诊智能体
    tech_triage_agent = agent_cooperation_service.create_agent_from_config(
        config="tech_triage",
        base_agent=tech_triage,
        expert_names=["software", "hardware", "network"]
    )
    
    # 使用装饰器创建和注册专家
    @agent_cooperation_service.register_expert_with_decorator(
        name="pediatrics",
        config_id="doctor_expert",
        description="儿科专家，专注0-14岁儿童健康问题"
    )
    def get_pediatrician():
        return doctor_expert
    
    # 测试智能体
    logger.info(f"创建的智能体: 心脏科专家, 骨科专家, 神经科专家, 儿科专家")
    logger.info(f"创建的技术专家: 软件专家, 硬件专家, 网络专家")
    logger.info(f"创建的分诊智能体: 医疗分诊, 技术分诊")
    
    # 构建会话上下文
    from agent_cores.core.simple_context import SimpleContext
    context = SimpleContext(
        user_id="user123",
        user_name="测试用户"
    )
    
    # 测试运行医疗分诊智能体
    try:
        result = await runtime_service.run_agent(
            agent=medical_triage,
            input_text="我最近总是感到胸闷气短，这是怎么回事？",
            session_id="test_session_1",
            context=context
        )
        
        logger.info(f"医疗分诊回复: {result.get('output', 'No output')}")
        
        # 检查是否包含handoff结果
        has_handoff = False
        if 'items' in result:
            for item in result['items']:
                if item.get('type') == 'tool_call' and 'consult_cardiology_doctor' in item.get('name', ''):
                    has_handoff = True
                    logger.info(f"检测到向心脏科医生的转诊")
                    
        if not has_handoff:
            logger.warning("未检测到转诊操作")
    except Exception as e:
        logger.error(f"运行医疗分诊智能体时出错: {str(e)}")
    
    # 测试运行技术分诊智能体
    try:
        tech_result = await runtime_service.run_agent(
            agent=tech_triage_agent,
            input_text="我的电脑无法连接到WiFi网络，该怎么解决？",
            session_id="test_session_2",
            context=context
        )
        
        logger.info(f"技术分诊回复: {tech_result.get('output', 'No output')}")
        
        # 检查是否包含handoff结果
        tech_has_handoff = False
        if 'items' in tech_result:
            for item in tech_result['items']:
                if item.get('type') == 'tool_call' and 'consult_network_expert' in item.get('name', ''):
                    tech_has_handoff = True
                    logger.info(f"检测到向网络专家的转诊")
                    
        if not tech_has_handoff:
            logger.warning("未检测到技术问题转诊操作")
    except Exception as e:
        logger.error(f"运行技术分诊智能体时出错: {str(e)}")
    
    logger.info("基于配置的智能体创建示例完成")


if __name__ == "__main__":
    try:
        asyncio.run(run_example())
    except Exception as e:
        logger.error(f"运行示例时出错: {str(e)}")
        import traceback
        traceback.print_exc()