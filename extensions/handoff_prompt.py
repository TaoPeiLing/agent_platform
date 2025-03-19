"""
Handoff提示词模块 - 提供优化的代理提示词模板

该模块包含为支持Handoff机制优化的提示词模板和生成函数，
确保代理正确理解和执行Handoff过程。
"""

import logging
from typing import Dict, List, Any, Optional

# 配置日志
logger = logging.getLogger(__name__)

# 推荐的提示词前缀 - 用于增强代理对Handoff的理解
RECOMMENDED_PROMPT_PREFIX = """
你是一个支持团队协作的智能助手，能够识别并处理自己擅长和不擅长的任务。

当你收到一个超出你职责范围或专业领域的请求时，应该考虑将其转交给更合适的专业助手。不要尝试回答你不确定的问题，而是使用"转交"工具将请求传递给适当的专家。

转交规则:
1. 只有在确实需要专业知识时才转交请求
2. 明确告知用户你正在将请求转交给专家助手
3. 提供转交的简短理由
4. 转交后，将不再参与当前对话，由专家助手负责回应

记住：质量比全面性更重要，宁可转交专家，也不要提供不确定的答案。
"""


def prompt_with_handoff_instructions(
    original_prompt: str,
    custom_handoff_instructions: Optional[str] = None
) -> str:
    """
    为提示词添加Handoff指令
    
    将原始提示词与Handoff指令结合，确保代理理解如何使用Handoff工具。
    可以提供自定义的Handoff指令，否则使用推荐的默认指令。
    
    Args:
        original_prompt: 原始提示词
        custom_handoff_instructions: 自定义的Handoff指令
        
    Returns:
        增强后的提示词
    """
    # 使用自定义指令或默认指令
    handoff_instructions = custom_handoff_instructions or RECOMMENDED_PROMPT_PREFIX
    
    # 根据原始提示词是否已包含Handoff相关内容进行判断
    has_handoff_content = any(
        keyword in original_prompt.lower() 
        for keyword in ["转交", "handoff", "转给", "交给", "委托给"]
    )
    
    if has_handoff_content:
        logger.info("原始提示词已包含Handoff相关内容，不添加标准Handoff指令")
        return original_prompt
    
    # 组合指令和原始提示词
    combined_prompt = f"{handoff_instructions}\n\n{original_prompt}"
    
    # 记录日志
    logger.info("已为提示词添加Handoff指令")
    return combined_prompt


def create_handoff_system_message(target_agent_name: str, reason: Optional[str] = None) -> str:
    """
    创建Handoff系统消息
    
    为接收Handoff的代理创建合适的系统消息，说明Handoff来源和原因。
    
    Args:
        target_agent_name: 目标代理名称
        reason: Handoff的原因
        
    Returns:
        Handoff系统消息
    """
    reason_text = f"原因: {reason}\n" if reason else ""
    
    system_message = f"""你是 {target_agent_name}，正在接收一个由其他助手转交过来的请求。

{reason_text}
请专注于你的专业领域，提供准确、有帮助的回答。作为专家，你应该:
1. 详细解答用户问题，展示你的专业知识
2. 如有需要，可以请求更多信息
3. 给出明确、可操作的建议

不要提及你是由另一个助手转交的，只需自然地回答用户的问题。"""
    
    return system_message


def generate_handoff_description(expertise_areas: List[str]) -> str:
    """
    生成Handoff描述
    
    根据代理的专业领域生成Handoff描述，用于代理模板。
    
    Args:
        expertise_areas: 专业领域列表
        
    Returns:
        Handoff描述
    """
    if not expertise_areas:
        return "该代理可以处理特定领域的专业问题。"
    
    # 格式化专业领域
    areas_text = "、".join(expertise_areas)
    
    return f"该代理是{areas_text}领域的专家，可以处理相关的专业问题。" 