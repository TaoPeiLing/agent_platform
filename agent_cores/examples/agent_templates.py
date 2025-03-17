"""
代理模板注册模块 - 负责从配置文件加载并注册代理模板

该模块实现了使用Agent.clone()功能创建代理模板的机制，
通过从JSON配置文件自动加载代理定义并注册到代理工厂。
"""
import os
import sys
import json
import logging
import glob
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logger = logging.getLogger(__name__)

# 导入代理工厂
from agent_cores.core.factory import agent_factory

# 导入RBAC相关

# 导入工具管理器
from agent_cores.tools import tool_manager


def load_tools_from_config(tool_configs: List[Dict[str, Any]]) -> List[Any]:
    """
    从工具配置加载工具列表
    
    Args:
        tool_configs: 工具配置列表
        
    Returns:
        工具对象列表
    """
    tools = []
    if not tool_configs:
        return tools
        
    for tool_config in tool_configs:
        try:
            tool_name = tool_config.get("name")
            if not tool_name:
                logger.warning(f"工具配置缺少名称字段，跳过")
                continue
                
            # 从工具管理器获取工具
            tool = tool_manager.get_tool(tool_name)
            if tool:
                tools.append(tool)
            else:
                logger.warning(f"未找到工具: {tool_name}")
        except Exception as e:
            logger.error(f"加载工具时出错 {tool_config.get('name', 'unknown')}: {e}")
            
    return tools


def register_template_from_json(file_path: str) -> str:
    """
    从JSON文件加载并注册代理模板
    
    Args:
        file_path: JSON配置文件路径
        
    Returns:
        注册的模板名称，失败则返回None
    """
    try:
        # 加载JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 提取基本信息
        name = config.get("name", "未命名代理")
        template_name = Path(file_path).stem  # 使用文件名作为模板名称
        instructions = config.get("instructions", "")
        
        # 解析模型配置
        model_config = config.get("model", {})
        model_name = model_config.get("name", "gpt-3.5-turbo-0125")
        
        # 构建模型设置
        model_settings = None
        if "settings" in model_config:
            model_settings = model_config["settings"]
        elif any(k in model_config for k in ["temperature", "top_p", "presence_penalty", "frequency_penalty"]):
            model_settings = {k: v for k, v in model_config.items()
                             if k in ["temperature", "top_p", "presence_penalty", "frequency_penalty"]}
        
        # 加载工具
        tools = load_tools_from_config(config.get("tools", []))
        
        # 注册模板
        agent_factory.register_template_from_config(
            name=template_name,
            instructions=instructions,
            model_name=model_name,
            model_settings=model_settings,
            tools=tools
        )
        
        logger.info(f"已注册代理模板: {template_name} ({name})")
        return template_name
    except Exception as e:
        logger.error(f"从JSON注册模板失败 {file_path}: {e}")
        return None


def register_all_templates() -> List[str]:
    """
    注册所有代理模板
    
    从agent_configs/agents目录加载所有JSON配置文件
    并将它们注册为代理模板
    
    Returns:
        注册成功的模板名称列表
    """
    # 查找配置文件目录
    config_dir = os.path.join(project_root, "agent_configs", "agents")
    if not os.path.exists(config_dir):
        logger.warning(f"代理配置目录不存在: {config_dir}")
        return []
        
    # 查找所有JSON文件
    json_pattern = os.path.join(config_dir, "*.json")
    json_files = glob.glob(json_pattern)
    
    if not json_files:
        logger.warning(f"未找到代理配置文件: {json_pattern}")
        return []
    
    # 注册所有模板
    registered_templates = []
    for json_file in json_files:
        if "__" in json_file or json_file.endswith("_example.json"):
            # 跳过特殊文件
            continue
            
        template_name = register_template_from_json(json_file)
        if template_name:
            registered_templates.append(template_name)
    
    # 记录注册结果
    logger.info(f"共注册 {len(registered_templates)} 个代理模板: {', '.join(registered_templates)}")
    return registered_templates


def create_default_templates():
    """
    创建默认的代理模板
    
    在没有找到任何模板配置文件时使用
    """
    # 创建默认助手代理
    agent_factory.register_template_from_config(
        name="assistant_agent",
        instructions="你是一个友好、乐于助人的AI助手。认真回答问题，提供有用的信息。",
        model_name="gpt-3.5-turbo-0125",
        model_settings={"temperature": 0.7},
        tools=[]
    )
    
    # 创建中文翻译代理
    agent_factory.register_template_from_config(
        name="chinese_translator_agent",
        instructions="你是一个专业的中文翻译助手。你的任务是将用户输入的内容翻译成流畅、准确的中文。无论输入是什么语言，都将其翻译为中文。保持原文的意思、风格和语气。",
        model_name="gpt-3.5-turbo-0125",
        model_settings={"temperature": 0.3},
        tools=[]
    )
    
    logger.info("已创建默认代理模板")


# 自动执行函数
if __name__ == "__main__":
    # 配置基本日志
    logging.basicConfig(level=logging.INFO)
    
    # 注册所有模板
    templates = register_all_templates()
    
    # 如果没有注册任何模板，创建默认模板
    if not templates:
        create_default_templates() 