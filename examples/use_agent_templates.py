"""
代理模板使用示例 - 展示如何使用注册好的代理模板
# 运行所有示例
python agent_cores/examples/use_agent_templates.py

# 或者运行特定示例（1-5）
python agent_cores/examples/use_agent_templates.py 1  # 运行示例1
python agent_cores/examples/use_agent_templates.py 2  # 运行示例2

# 以此类推
该脚本展示了几种使用注册好的代理模板的方法：
1. 简单交互：创建代理并发送单个请求
2. 多轮对话：使用会话进行多轮对话
3. 不同权限级别：展示不同角色如何访问不同工具
"""
import os
# 首先加载环境变量，确保在导入其他模块前完成
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(".env_development"))

# 验证环境变量是否加载
zhipu_api_key = os.getenv("DOUBAO_API_KEY", "")
if zhipu_api_key:
    print(f"ZHIPU_API_KEY已加载：{'*' * (len(zhipu_api_key) - 4)}{zhipu_api_key[-4:]}")
else:
    print("警告: ZHIPU_API_KEY未设置")

import sys
import logging
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入运行时服务
from agent_cores.core.runtime import runtime_service

# 导入模板管理器
from agent_cores.core.template_manager import template_manager

# 导入OpenAI Agent SDK

# 导入RBAC权限相关

# 导入系统诊断工具
from agent_cores.tools.example.diagnostics import diagnostics

# 尝试导入Redis上下文管理器
try:
    from agent_cores.core.redis_context_manager import redis_context_manager

    HAS_REDIS = True
    logger.info("Redis上下文管理器可用，将使用Redis进行上下文存储")
except ImportError:
    HAS_REDIS = False
    logger.info("Redis上下文管理器不可用，将使用内存存储上下文")


# 定义对话历史上下文类
@dataclass
class ConversationContext:
    """对话历史上下文"""
    history: List[Dict[str, Any]] = field(default_factory=list)
    user_id: str = "anonymous"
    user_name: str = "用户"

    def add_message(self, role: str, content: str):
        """添加消息到历史记录"""
        self.history.append({"role": role, "content": content})

    def get_formatted_history(self) -> str:
        """获取格式化的历史记录用于Agent指令"""
        # 如果没有历史记录，则返回空字符串
        if not self.history:
            return ""

        # 有历史记录时，返回格式化的历史（包括所有历史消息）
        formatted = "以下是之前的对话历史：\n\n"
        for msg in self.history:
            name = self.user_name if msg["role"] == "user" else "AI"
            formatted += f"{name}: {msg['content']}\n\n"
        return formatted


# 定义用户上下文类 - 特别为OpenAI Agent SDK设计
@dataclass
class UserContext:
    """用户上下文 - 为OpenAI Agent SDK设计"""
    user_id: str
    user_name: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        # 确保metadata包含user_name
        if "user_name" not in self.metadata:
            self.metadata["user_name"] = self.user_name


# 导入简化上下文
from agent_cores.core.simple_context import SimpleContext


async def example_1_simple_interaction():
    """示例1：简单交互 - 创建代理并发送单个请求"""
    logger.info("示例1：简单交互 - 开始")

    # 获取所有可用模板
    available_templates = template_manager.list_templates()
    logger.info(f"可用的代理模板: {', '.join(available_templates)}")

    # 选择默认模板（优先assistant_agent）
    template_name = "assistant_agent" if "assistant_agent" in available_templates else available_templates[0]
    logger.info(f"使用模板: {template_name}")

    # 发送请求
    question = "你好，请简单介绍一下你自己"
    logger.info(f"发送问题: {question}")

    # 使用runtime_service运行代理
    result = await runtime_service.run_agent(
        template_name=template_name,
        input_text=question,
        session_id="test-async-session"
    )

    # 打印结果 (添加错误处理)
    logger.info("代理回答:")
    if 'error' in result:
        logger.error(f"发生错误: {result['error']}")
        print(f"\n错误: {result['error']}\n")
    else:
        print(f"\n{result['output']}\n")

    logger.info("示例1：简单交互 - 结束")
    print("-" * 80)


async def example_2_calculator_tool():
    """示例2：使用工具 - 测试计算器工具"""
    logger.info("示例2：使用工具 - 开始")

    # 获取所有可用模板
    available_templates = template_manager.list_templates()
    logger.info(f"可用的代理模板: {', '.join(available_templates)}")

    # 选择默认模板（admin_agent）
    # template_name = "admin_agent" if "admin_agent" in available_templates else available_templates[0]
    template_name = "admin_agent" # if "assistant_agent.json" in available_templates else available_templates[0]
    logger.info(f"使用模板: {template_name}")

    # 发送需要使用计算器的请求
    question = "请计算 (15 * 7)的结果"
    logger.info(f"发送问题: {question}")

    # 运行代理
    result = await runtime_service.run_agent(
        template_name=template_name,  # 传递代理模板
        input_text=question,
        session_id="test-calculator-session"
    )

    # 打印结果 (添加错误处理)
    logger.info("代理回答:")
    if 'error' in result:
        logger.error(f"发生错误: {result['error']}")
        print(f"\n错误: {result['error']}\n")
    else:
        print(f"\n{result['output']}\n")

    logger.info("示例2：使用工具 - 结束")
    print("-" * 80)


async def example_3_multi_turn_conversation():
    """示例3：多轮对话 - 使用SimpleContext进行标准化上下文管理
    
    这个示例展示如何使用SimpleContext类进行多轮对话上下文管理，
    包括系统消息设置、添加用户和助手消息、以及使用同一上下文进行多轮交互。
    """
    logger.info("示例3：多轮对话 - 开始")

    # 用户信息
    user_id = "user_456"
    user_name = "张三"
    
    # 创建SimpleContext实例 - 标准化的上下文管理方式
    context = SimpleContext(
        user_id=user_id,
        user_name=user_name,
        metadata={
            "user_name": user_name,
            "preference": "简短回答",
            "language": "zh-CN"
        }
    )
    
    # 创建会话 - 确保与上下文用户ID一致
    session_id = runtime_service.create_session(
        user_id=user_id,
        metadata=context.metadata
    )
    logger.info(f"创建新会话: {session_id}")

    # 添加系统消息到上下文 - 使用SimpleContext的专用方法
    system_message = f"""你是一个智能助手。
当前用户的名字是{user_name}。
请记住这个名字，当用户询问自己的名字时，你应该回答他的名字是{user_name}。
请提供简短、有帮助的回答。"""

    context.add_system_message(system_message)
    logger.info("已添加系统消息到上下文")

    # 获取代理实例
    template_name = "assistant_agent"
    agent = template_manager.get_template(template_name)
    if not agent:
        logger.error(f"无法获取代理模板: {template_name}")
        return

    logger.info(f"成功获取代理模板: {agent.name}")

    # 多轮对话内容
    conversations = [
        "你好，请问你是谁?",
        "苹果英文单词是什么？",
        "我的名字是什么?",
        "我向你提出了几个问题，分别是什么?"
    ]

    # 多轮对话 - 使用同一个SimpleContext对象
    for i, message in enumerate(conversations):
        logger.info(f"第{i + 1}轮对话，问题: {message}")
        print(f"\n用户: {message}")

        # 添加用户消息到上下文 - 使用SimpleContext的add_message方法
        context.add_message("user", message)
        
        # 运行代理 - 传递标准化的SimpleContext对象
        result = await runtime_service.run_agent(
            agent=agent,
            input_text=message,
            session_id=session_id,
            context=context  # 传递完整的SimpleContext对象
        )

        # 处理回复
        if 'error' in result:
            logger.error(f"第{i + 1}轮对话发生错误: {result['error']}")
            print(f"\n错误: {result['error']}\n")
        else:
            output = result['output']
            print(f"\nAI: {output}\n")

            # 将助手回复添加到上下文
            context.add_message("assistant", output)
            
        # 可选：展示当前上下文中的消息数量
        logger.info(f"上下文中已累积 {len(context.messages)} 条消息")

    # 对话结束后显示完整历史
    logger.info("完整对话历史：")
    for i, msg in enumerate(context.messages):
        role = msg.get("role", "unknown")
        content_preview = msg.get("content", "")[:50] + ("..." if len(msg.get("content", "")) > 50 else "")
        print(f"[{i+1}] {role}: {content_preview}")
    
    # 展示如何使用get_last_n_messages方法
    recent_messages = context.get_last_n_messages(2)
    logger.info(f"最近2条消息 (不包括系统消息): {len(recent_messages) - 1} 条")

    logger.info("示例3：多轮对话 - 结束")
    print("-" * 80)


async def example_4_different_agent_templates():
    """示例4：不同代理模板 - 比较不同代理模板的回答"""
    logger.info("示例4：不同代理模板 - 开始")

    # 获取可用的模板名称
    available_templates = template_manager.list_templates()
    logger.info(f"可用的代理模板: {', '.join(available_templates)}")

    if not available_templates:
        logger.error("没有可用的代理模板，示例无法继续")
        return

    # 测试问题
    question = "请把这段话翻译成英文：人工智能正在改变我们的生活方式"
    logger.info(f"测试问题: {question}")

    # 为每个模板创建代理并运行
    for template_name in available_templates:
        agent = template_manager.get_template(template_name)
        if not agent:
            logger.error(f"无法获取模板: {template_name}")
            continue

        logger.info(f"使用模板 {template_name} ({agent.name}) 回答问题:")

        # 运行代理
        result = await runtime_service.run_agent(
            agent=agent,
            input_text=question,
            session_id=f"template-compare-{template_name}"
        )

        # 打印结果 (添加错误处理)
        if 'error' in result:
            logger.error(f"使用模板 {template_name} 时发生错误: {result['error']}")
            print(f"\n错误: {result['error']}\n")
        else:
            print(f"\n{result['output']}\n")

    logger.info("示例4：不同代理模板 - 结束")
    print("-" * 80)


async def example_5_weather_tool():
    """示例5：天气工具 - 使用天气查询工具"""
    logger.info("示例5：天气工具 - 开始")

    # 获取可用的模板名称
    available_templates = template_manager.list_templates()

    # 选择user_agent或另一个可用模板
    template_name = "user_agent" if "user_agent" in available_templates else available_templates[0]
    logger.info(f"使用模板: {template_name}")

    # 获取代理实例
    agent = template_manager.get_template(template_name)
    if not agent:
        logger.error(f"无法获取模板: {template_name}")
        return

    logger.info(f"成功获取代理: {agent.name}")

    # 发送需要使用天气工具的请求
    question = "请查询北京今天的天气"
    logger.info(f"发送问题: {question}")

    # 运行代理
    result = await runtime_service.run_agent(
        agent=agent,
        input_text=question,
        session_id="weather-tool-test"
    )

    # 打印结果 (添加错误处理)
    logger.info("代理回答:")
    if 'error' in result:
        logger.error(f"发生错误: {result['error']}")
        print(f"\n错误: {result['error']}\n")
    else:
        print(f"\n{result['output']}\n")

    logger.info("示例5：天气工具 - 结束")
    print("-" * 80)


async def example_6_system_diagnostics():
    """示例6: 使用系统诊断工具和SimpleContext
    
    展示如何使用系统诊断工具检查系统状态和解决问题，
    同时演示如何在诊断场景中使用SimpleContext。
    """
    logger.info("运行示例6: 使用系统诊断工具")

    # 创建标准化的上下文对象
    admin_context = SimpleContext(
        user_id="admin",
        user_name="系统管理员",
        metadata={
            "role": "admin",
            "purpose": "system_diagnostics"
        }
    )
    
    # 创建诊断会话
    session_id = runtime_service.create_session(
        user_id="admin",
        metadata=admin_context.metadata
    )

    # 运行系统诊断
    try:
        logger.info("开始执行系统诊断...")
        diagnosis_report = diagnostics.diagnose_system()

        # 输出诊断结果
        logger.info("系统诊断完成")
        logger.info(f"系统状态: {diagnosis_report['system_status']}")
        logger.info(f"发现并修复的问题数量: {diagnosis_report['total_problems_fixed']}")
        logger.info(f"可用模板数量: {diagnosis_report['templates_available']}")
        logger.info(f"注册工具数量: {diagnosis_report['tools_registered']}")

        # 检查模板诊断
        template_diag = diagnosis_report['template_diagnostics']
        logger.info(
            f"模板诊断: 找到 {template_diag['templates_found']} 个模板，加载 {template_diag['templates_loaded']} 个，"
            f"失败 {template_diag['templates_failed']} 个")

        # 如果有失败的模板，打印详情
        if template_diag['templates_failed'] > 0:
            logger.warning(f"以下模板加载失败: {template_diag['failed_templates']}")

        # 如果诊断工具创建了新模板，打印信息
        if template_diag['fixed_problems'] > 0:
            logger.info("诊断工具已自动修复一些问题，如创建缺失的默认模板")

        # 输出SSL诊断结果
        ssl_diag = diagnosis_report['ssl_diagnostics']
        if ssl_diag['ssl_available'] and ssl_diag['default_context_works']:
            logger.info("SSL配置正常")
        else:
            logger.warning("SSL配置存在问题，可能会影响API连接")

        # 输出API连接诊断结果
        api_diag = diagnosis_report['api_diagnostics']
        if api_diag['connection_works']:
            logger.info("API连接测试成功")
        else:
            logger.warning(f"API连接测试失败: {api_diag['error_message']}")

        # 使用诊断信息创建代理
        if diagnosis_report['templates_available'] > 0:
            # 从文件创建代理
            agent_config = template_manager.create_agent_from_config_file("assistant_agent.json")
            if agent_config:
                # 准备请求
                user_query = "请告诉我系统状态，包括模板和工具数量"
                
                # 将诊断信息添加到上下文
                admin_context.add_system_message(
                    f"""你是系统诊断助手。
当前系统状态: {diagnosis_report['system_status']}
可用模板数量: {diagnosis_report['templates_available']}
注册工具数量: {diagnosis_report['tools_registered']}

请基于上述信息回答用户的问题。"""
                )
                
                # 添加用户问题到上下文
                admin_context.add_message("user", user_query)

                # 运行代理
                result = await runtime_service.run_agent(
                    agent=agent_config,
                    input_text=user_query,
                    session_id=session_id,
                    context=admin_context
                )

                # 输出结果
                logger.info(f"用户: {user_query}")
                if 'error' in result:
                    logger.error(f"发生错误: {result['error']}")
                    print(f"\n错误: {result['error']}\n")
                else:
                    output = result['output']
                    print(f"\n助手: {output}\n")
                    # 添加助手回复到上下文
                    admin_context.add_message("assistant", output)
        else:
            logger.error("没有可用模板，无法创建代理")

    except Exception as e:
        logger.error(f"执行系统诊断失败: {e}")


async def example_7_detailed_diagnostics():
    """示例7: 详细诊断与上下文持久化
    
    展示如何使用诊断类的各个独立方法进行针对性诊断，
    并演示如何在多个诊断步骤之间保持上下文的连续性。
    """
    logger.info("运行示例7: 详细诊断")

    # 创建持久化的诊断上下文
    diag_context = SimpleContext(
        user_id="diagnostics",
        user_name="诊断系统",
        metadata={"purpose": "detailed_diagnostics"}
    )
    
    # 创建或恢复诊断会话
    session_id = runtime_service.create_session(
        user_id="diagnostics",
        metadata=diag_context.metadata
    )
    
    # 添加系统消息，指导代理理解诊断上下文
    diag_context.add_system_message(
        """你是一个系统诊断助手，负责分析和解释诊断结果。
请保持简洁明了的回复风格，突出关键的诊断信息和建议。
如果发现问题，请提供解决方案建议。"""
    )

    try:
        # 记录诊断开始到上下文
        diag_context.add_message("user", "开始执行详细系统诊断")
        
        # 诊断模板配置
        logger.info("诊断模板配置...")
        template_report = diagnostics.diagnose_templates()
        
        # 记录模板诊断结果到上下文
        template_diag_msg = (
            f"模板诊断结果:\n"
            f"- 找到 {template_report['templates_found']} 个模板配置文件\n"
            f"- 成功加载 {template_report['templates_loaded']} 个模板\n"
            f"- 失败 {template_report['templates_failed']} 个模板\n"
        )
        diag_context.add_message("assistant", template_diag_msg)

        # 输出模板诊断结果
        logger.info(f"找到 {template_report['templates_found']} 个模板配置文件")
        logger.info(f"成功加载 {template_report['templates_loaded']} 个模板")

        if template_report['config_files']:
            logger.info("模板配置文件:")
            for config_file in template_report['config_files']:
                logger.info(f"  - {config_file}")

        # 诊断SSL配置并记录到上下文
        logger.info("诊断SSL配置...")
        ssl_report = diagnostics.diagnose_ssl()
        
        ssl_diag_msg = "SSL诊断结果:\n"
        if ssl_report['cert_file_exists']:
            ssl_diag_msg += f"- 找到SSL证书文件: {ssl_report['cert_path']}\n"
            ssl_diag_msg += "- SSL配置正常\n"
        else:
            ssl_diag_msg += "- 未找到SSL证书文件\n"
            ssl_diag_msg += "- 警告: SSL配置可能有问题，可能会影响API连接\n"
        
        diag_context.add_message("user", "请分析SSL配置状态")
        diag_context.add_message("assistant", ssl_diag_msg)

        # 诊断API连接并记录到上下文
        logger.info("诊断API连接...")
        api_report = diagnostics.diagnose_api_connection()
        
        api_diag_msg = "API连接诊断结果:\n"
        if api_report['openai_api_key']:
            api_diag_msg += "- 找到API密钥\n"
        else:
            api_diag_msg += "- 警告: 未找到API密钥\n"
            
        if api_report['connection_works']:
            api_diag_msg += "- API连接测试成功\n"
        else:
            api_diag_msg += f"- 错误: API连接测试失败: {api_report['error_message']}\n"
        
        diag_context.add_message("user", "请分析API连接状态")
        diag_context.add_message("assistant", api_diag_msg)
        
        # 获取模板处理诊断总结
        template_name = "assistant_agent"
        agent = template_manager.get_template(template_name)
        if agent:
            # 请求诊断总结
            diag_summary_prompt = "请根据之前的诊断结果，给出系统状态总结和建议"
            diag_context.add_message("user", diag_summary_prompt)
            
            # 运行代理获取诊断总结
            result = await runtime_service.run_agent(
                agent=agent,
                input_text=diag_summary_prompt,
                session_id=session_id,
                context=diag_context
            )
            
            # 处理并显示结果
            if 'error' in result:
                logger.error(f"获取诊断总结时发生错误: {result['error']}")
            else:
                diag_summary = result['output']
                print("\n===== 诊断总结 =====")
                print(diag_summary)
                print("=====================\n")
                # 将总结添加到上下文
                diag_context.add_message("assistant", diag_summary)
                
            # 显示上下文历史的大小
            logger.info(f"诊断会话上下文包含 {len(diag_context.messages)} 条消息")
        else:
            logger.error(f"无法获取代理模板: {template_name}")

    except Exception as e:
        logger.error(f"执行详细诊断失败: {e}")
        diag_context.add_message("system", f"诊断过程中出现错误: {str(e)}")


async def run_all_examples():
    """运行所有示例"""
    # 确保模板已加载
    # template_manager.ensure_loaded()

    # 简单交互示例
    await example_1_simple_interaction()

    # 使用计算器工具示例
    await example_2_calculator_tool()

    # 多轮对话示例
    await example_3_multi_turn_conversation()

    # 不同代理模板示例
    await example_4_different_agent_templates()

    # 天气工具示例
    await example_5_weather_tool()

    # 系统诊断示例
    await example_6_system_diagnostics()

    # 详细诊断示例
    await example_7_detailed_diagnostics()


if __name__ == "__main__":
    # 解析命令行参数
    import argparse

    parser = argparse.ArgumentParser(description="代理模板使用示例")
    parser.add_argument("example", nargs="?", type=int, choices=range(1, 8),
                        help="要运行的示例编号 (1-7)，不提供则运行所有示例")
    args = parser.parse_args()

    # 确保模板已加载
    template_manager.ensure_loaded()

    # 如果提供了示例编号，则只运行该示例
    if args.example:
        examples = {
            1: example_1_simple_interaction,
            2: example_2_calculator_tool,
            3: example_3_multi_turn_conversation,
            4: example_4_different_agent_templates,
            5: example_5_weather_tool,
            6: example_6_system_diagnostics,
            7: example_7_detailed_diagnostics
        }
        asyncio.run(examples[args.example]())
    else:
        # 否则运行所有示例
        asyncio.run(run_all_examples())
