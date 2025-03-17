"""
上下文使用示例 - 演示Context的正确使用方法

此示例演示:
1. 如何创建和使用AgentContext
2. 如何在AgentContext中存储用户信息
3. 如何让工具函数访问AgentContext中的信息
4. 如何正确管理消息历史
"""

import os
import sys

# ⚠️ 最重要的设置：在导入任何其他模块前，强制禁用Redis
os.environ["USE_REDIS"] = "false"

import logging
import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 首先加载环境变量，但不让它覆盖已设置的USE_REDIS
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(".env_development"), override=False)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 打印关键环境变量
logger.info(f"USE_REDIS环境变量设置为: {os.getenv('USE_REDIS')}")

# 导入工具装饰器
from agents import function_tool, RunContextWrapper

# 导入所需模块
from agent_cores.core.runtime import runtime_service
from agent_cores.core.template_manager import template_manager
from agent_cores.core.agent_context import AgentContext
from agent_cores.core.factory import agent_factory

# 导入OpenAI Agent SDK
from agents import Agent, Runner


# 示例工具函数 - 将在代理执行时访问上下文
@function_tool
async def get_user_profile(wrapper: RunContextWrapper[AgentContext], input_data=None):
    """获取用户资料，从上下文中提取用户信息"""
    logger.info(f"调用get_user_profile工具，上下文类型: {type(wrapper)}")
    
    if not wrapper or not hasattr(wrapper, "context"):
        logger.error("上下文对象无效或不包含context属性")
        return "无法获取用户信息，上下文参数无效"
    
    context = wrapper.context
    logger.info(f"上下文对象类型: {type(context)}")
    
    try:
        if hasattr(context, "get_user_info"):
            user_info = context.get_user_info()
            logger.info(f"获取到用户信息: {user_info}")
            return f"您的用户名是{user_info.get('user_name')}，用户ID是{user_info.get('user_id')}。"
        elif hasattr(context, "user_id") and hasattr(context, "user_name"):
            logger.info(f"从属性获取用户信息: {context.user_id}, {context.user_name}")
            return f"您的用户名是{context.user_name}，用户ID是{context.user_id}。"
        else:
            logger.warning("上下文中没有找到用户信息")
            return "抱歉，无法获取您的个人资料信息。"
    except Exception as e:
        logger.error(f"获取用户信息时出错: {e}")
        return f"获取用户信息时出错: {e}"


# 示例工具函数 - 获取对话历史
@function_tool
async def get_chat_history(wrapper: RunContextWrapper[AgentContext], input_data=None):
    """获取聊天历史，从上下文中提取历史消息"""
    logger.info(f"调用get_chat_history工具，上下文类型: {type(wrapper)}")
    
    if not wrapper or not hasattr(wrapper, "context"):
        logger.error("上下文对象无效或不包含context属性")
        return "无法获取聊天历史，上下文参数无效"
    
    context = wrapper.context
    logger.info(f"上下文对象类型: {type(context)}")
    
    try:
        # 检查消息列表是否存在且非空
        if not hasattr(context, "messages") or not context.messages:
            logger.warning(f"上下文中没有消息历史或messages属性不存在: {dir(context)}")
            return "抱歉，我无法找到我们之前的对话记录。"
        
        # 获取所有消息并输出到日志进行调试
        all_messages = context.messages
        logger.info(f"上下文中的所有消息({len(all_messages)}条): {all_messages}")
        
        # 获取最近5条消息
        messages = all_messages[-5:] if len(all_messages) > 5 else all_messages
        logger.info(f"将处理{len(messages)}条最近消息")
        
        # 简化处理逻辑，减少出错可能
        history_text = []
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            logger.info(f"处理消息: {role} - {content[:30]}...")
            
            # 跳过系统消息
            if role == "system":
                logger.info("跳过系统消息")
                continue
                
            # 格式化角色名称
            display_role = role
            if role == "user":
                display_role = "您"
            elif role == "assistant":
                display_role = "我"
            
            history_text.append(f"{display_role}: {content}")
        
        # 检查结果并返回
        if history_text:
            logger.info(f"找到{len(history_text)}条有效消息历史")
            return "以下是我们之前的对话记录：\n" + "\n".join(history_text)
        else:
            logger.warning("过滤后没有有效的消息历史")
            return "我们之前没有有效的对话记录。"
            
    except Exception as e:
        logger.error(f"获取聊天历史时出错: {e}", exc_info=True)
        return f"获取聊天历史时出错: {e}"


async def example_1_context_basic_usage():
    """示例1：基本的Context使用 - 创建和传递上下文"""
    logger.info("示例1：基本的Context使用 - 开始")
    
    # 创建会话
    user_name = "王小明"
    user_id = "user_" + str(uuid.uuid4())[:8]
    
    # 创建一个AgentContext实例
    agent_context = AgentContext(
        user_id=user_id,
        user_name=user_name,
        metadata={
            "user_name": user_name,
            "age": 30,
            "interests": ["编程", "人工智能", "旅行"]
        }
    )
    logger.info(f"创建AgentContext，用户信息: {agent_context.get_user_info()}")
    
    # 设置模型提供者
    # agent_factory.set_model_provider("zhipu", os.getenv("ZHIPU_API_KEY"))
    agent_factory.set_model_provider("doubao", os.getenv("DAOBAO_API_KEY"))
    # 创建自定义代理
    agent = Agent(
        name="上下文测试代理",
        instructions=f"""你是一个测试代理，用于演示上下文的使用。
        
请记住以下重要指示：
1. 你只需要回答与上下文相关的问题，不需要回答其他问题
2. 当用户询问他们的信息时，使用get_user_profile工具获取信息
3. 当用户询问聊天历史时，使用get_chat_history工具获取历史
4. 当使用工具函数时，必须等待工具函数返回结果，然后向用户展示这些结果
5. 非常重要：当工具函数返回历史消息或用户信息时，你应该直接把这些信息作为回答的一部分呈现给用户
6. 不要简单重复用户的问题，而是回答用户的问题

例如，如果用户问"我们之前聊了什么"，你应该:
- 调用get_chat_history工具获取历史
- 把工具返回的历史信息作为你回答的主体内容
- 回复类似"这是我们之前的对话内容：[这里是工具返回的历史]"
""",
        model=agent_factory.current_provider.get_model_object(),
        tools=[get_user_profile, get_chat_history]
    )
    
    # 添加一些历史消息到上下文
    agent_context.add_message("system", "这是一个系统消息，用于初始化对话")
    agent_context.add_message("user", "你好，我是王小明")
    agent_context.add_message("assistant", "你好，王小明！很高兴认识你。我能帮你什么忙吗？")
    
    # 确认历史消息是否添加成功
    logger.info(f"初始阶段 - 上下文中的消息历史({len(agent_context.messages)}条): {agent_context.messages}")
    
    # 发送测试消息
    test_message = "请告诉我我的个人资料"
    # cagent_context.add_message("user", test_message)
    
    logger.info(f"发送测试消息: {test_message}")
    logger.info(f"第一次查询前 - 上下文中的消息历史({len(agent_context.messages)}条): {agent_context.messages}")
    
    # 运行代理
    result = await runtime_service.run_agent(
        agent=agent,
        input_text=test_message,
        context=agent_context
    )
    
    # 处理结果
    if 'error' in result:
        logger.error(f"发生错误: {result['error']}")
        print(f"\n错误: {result['error']}\n")
    else:
        output = result['output']
        logger.info(f"代理回答: {output}")
        print(f"\n用户: {test_message}")
        print(f"\nAI: {output}\n")
        
        # 添加回复到上下文
        agent_context.add_message("assistant", output)
        logger.info(f"添加代理回复后 - 上下文中的消息历史({len(agent_context.messages)}条): {agent_context.messages}")
    
    # 发送第二个测试消息
    test_message_2 = "我们之前聊了什么？"
    # agent_context.add_message("user", test_message_2)
    
    logger.info(f"发送第二个测试消息: {test_message_2}")
    logger.info(f"第二次查询前 - 上下文中的消息历史({len(agent_context.messages)}条): {agent_context.messages}")
    
    # 再次运行代理
    result_2 = await runtime_service.run_agent(
        agent=agent,
        input_text=test_message_2,
        context=agent_context
    )
    
    # 处理结果
    if 'error' in result_2:
        logger.error(f"发生错误: {result_2['error']}")
        print(f"\n错误: {result_2['error']}\n")
    else:
        output_2 = result_2['output']
        logger.info(f"代理回答: {output_2}")
        print(f"\n用户: {test_message_2}")
        print(f"\nAI: {output_2}\n")
    
    logger.info("示例1：基本的Context使用 - 结束")
    print("-" * 80)


async def example_2_using_context_in_runtime():
    """示例2：在runtime中使用Context - 演示在运行时服务中使用上下文"""
    logger.info("示例2：在runtime中使用Context - 开始")

    # 确保模板已加载
    template_manager.ensure_loaded()

    # 创建一个用户会话
    user_name = "李小红"
    session_id = runtime_service.create_session(
        user_id="user_" + str(uuid.uuid4())[:8],
        metadata={"user_name": user_name, "vip_level": 2}
    )
    logger.info(f"创建会话: {session_id}")

    # 选择模板
    available_templates = template_manager.list_templates()
    template_name = "assistant_agent" if "assistant_agent" in available_templates else available_templates[0]
    logger.info(f"使用模板: {template_name}")

    # 发送第一个测试消息
    test_message = "你好，请告诉我我是谁？"
    logger.info(f"发送测试消息: {test_message}")

    # 运行代理 - runtime_service会自动创建上下文
    result = await runtime_service.run_agent(
        session_id=session_id,
        template_name=template_name,
        input_text=test_message
    )

    # 处理结果
    if 'error' in result:
        logger.error(f"发生错误: {result['error']}")
        print(f"\n错误: {result['error']}\n")
    else:
        output = result['output']
        logger.info(f"代理回答: {output}")
        print(f"\n用户: {test_message}")
        print(f"\nAI: {output}\n")

    # 发送第二个测试消息
    test_message_2 = "我们之前聊了什么？"
    logger.info(f"发送第二个测试消息: {test_message_2}")

    # 再次运行代理
    result_2 = await runtime_service.run_agent(
        session_id=session_id,
        template_name=template_name,
        input_text=test_message_2
    )

    # 处理结果
    if 'error' in result_2:
        logger.error(f"发生错误: {result_2['error']}")
        print(f"\n错误: {result_2['error']}\n")
    else:
        output_2 = result_2['output']
        logger.info(f"代理回答: {output_2}")
        print(f"\n用户: {test_message_2}")
        print(f"\nAI: {output_2}\n")

    logger.info("示例2：在runtime中使用Context - 结束")
    print("-" * 80)


async def main():
    """主函数"""
    # 检查环境设置
    logger.info("=== 环境配置检查 ===")
    logger.info(f"USE_REDIS环境变量: {os.getenv('USE_REDIS', 'not set')}")
    logger.info(f"ZHIPU_API_KEY环境变量: {'已设置' if os.getenv('ZHIPU_API_KEY') else '未设置'}")
    
    # 检查runtime_service状态
    logger.info(f"runtime_service使用Redis: {runtime_service.use_redis}")
    logger.info(f"runtime_service类: {type(runtime_service)}")
    
    # 获取Redis上下文管理器的导入路径
    try:
        from agent_cores.core.redis_context_manager import redis_context_manager
        logger.info(f"Redis上下文管理器: {redis_context_manager}")
        logger.info(f"Redis连接URL: {getattr(redis_context_manager, 'redis_url', '未知')}")
    except ImportError:
        logger.info("Redis上下文管理器未导入")
    
    # 直接运行示例
    logger.info("=== 开始运行Agent示例 ===")
    await example_1_context_basic_usage()
    
    # 不运行示例2
    # await example_2_using_context_in_runtime()


if __name__ == "__main__":
    asyncio.run(main())
