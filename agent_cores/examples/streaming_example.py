"""
流式执行示例 - 演示如何使用三种方式执行代理
"""
import os
import sys
import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置环境
from dotenv import load_dotenv,find_dotenv

load_dotenv(find_dotenv(".env_development"))

# 导入OpenAI Agent SDK相关组件
from agents import Agent, function_tool, RunConfig
from agents.model_settings import ModelSettings  # 导入ModelSettings用于配置模型参数

# 导入运行时服务及代理工厂
from agent_cores.core.runtime import runtime_service
from agent_cores.core.factory import agent_factory

# 创建代理工厂实例，用于获取默认模型
try:
    # 尝试设置智谱模型提供者
    zhipu_api_key = os.getenv("ZHIPU_API_KEY")
    if zhipu_api_key:
        agent_factory.set_model_provider("zhipu", zhipu_api_key)
        print(f"成功设置智谱AI为默认提供者，默认模型: {agent_factory.default_model}")
    else:
        print("未找到ZHIPU_API_KEY环境变量，将使用默认模型提供者")
        
        # 尝试使用默认提供者
        default_provider = agent_factory.get_default_model_provider()
        if default_provider:
            print(f"使用默认提供者: {default_provider.get_model_info().get('provider')}")
        else:
            print("警告: 未能设置任何模型提供者，可能导致运行失败")
except Exception as e:
    print(f"设置模型提供者时出错: {e}")
    print("将尝试使用系统默认模型配置继续")

"""
配置说明:

RunConfig是OpenAI Agents SDK中重要的配置类，用于控制代理执行时的各种行为。

主要配置选项包括:
1. model_settings: ModelSettings实例，控制使用的模型和生成参数
   - model: 使用的模型名称，如"gpt-4o"、"gpt-3.5-turbo"等
   - temperature: 控制输出随机性，范围0-1，越低越确定性
   - top_p: 控制token选择概率阈值
   - max_tokens: 限制生成的最大token数
   - system_prompt: 可选自定义系统提示

2. timeout_seconds: 执行超时时间（秒），超过则中断执行
3. stream_mode: 流式输出模式
   - "auto": 根据情况自动选择最佳流式模式
   - "tokens": 逐token输出
   - "messages": 逐消息输出
   - "final": 仅输出最终结果（不流式）
4. debug: 是否启用调试模式
5. run_id: 自定义运行ID，用于跟踪特定执行
6. run_context_wrapper: 可选自定义上下文包装器

在runtime_service的方法中，config参数就是RunConfig实例:
- run_agent()
- run_agent_sync()
- run_agent_streamed()
- stream_agent()

使用适当的RunConfig可以优化代理执行的效率、响应性和资源使用。
"""

# 定义示例工具
@function_tool
def get_weather(location: str) -> str:
    """
    获取指定地点的天气信息
    
    Args:
        location: 地点名称
        
    Returns:
        天气信息描述
    """
    # 示例实现，实际应该调用天气API
    weather_data = {
        "北京": "晴天，温度25°C，微风",
        "上海": "多云，温度28°C，湿度较高",
        "广州": "小雨，温度30°C，局部有雷阵雨",
        "深圳": "阴天，温度29°C，有转晴趋势"
    }

    return weather_data.get(location, f"无法获取{location}的天气信息")


@function_tool
def get_current_time() -> str:
    """
    获取当前时间
    
    Returns:
        当前时间的格式化字符串
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


# 创建示例代理
def create_example_agent() -> Agent:
    """创建一个具有天气和时间工具的示例代理"""
    print("==========准备创建Agent===================")
    instructions = """
    你是一个智能助手，可以帮助用户回答问题，特别是关于天气和时间的查询。
    
    当用户询问天气信息时，请使用get_weather工具获取特定城市的天气数据。
    当用户询问当前时间时，请使用get_current_time工具获取准确的系统时间。
    
    请用友好的语气回应用户，提供详细且有用的信息。
    """
    
    # 获取当前提供者和默认模型信息
    model = None
    
    # 正确获取模型信息
    if agent_factory.current_provider:
        # 优先使用模型对象（如果提供者支持）
        if hasattr(agent_factory.current_provider, 'get_model_object') and callable(getattr(agent_factory.current_provider, 'get_model_object')):
            model = agent_factory.current_provider.get_model_object()
            print(f"使用模型对象：{type(model).__name__}")
        else:
            # 否则使用模型名称字符串
            model = agent_factory.default_model
            print(f"使用模型名称：{model}")
    else:
        # 如果没有设置提供者，使用默认模型名称
        model = agent_factory.default_model
        print(f"使用默认模型名称：{model}")
    
    # 创建代理
    agent = Agent(
        name="天气助手",
        instructions=instructions,
        model=model,  # 使用正确获取的模型对象或名称
        tools=[get_weather, get_current_time]
    )

    # 显示模型提供者信息
    if agent_factory.current_provider:
        provider_info = agent_factory.current_provider.get_model_info()
        print(f"模型提供者: {provider_info.get('provider')}")
        print(f"模型名称: {provider_info.get('model')}")
    
    return agent


# 异步执行示例
async def test_async_execution():
    """
    测试异步执行方法 (Runner.run)
    """
    print("\n=== 测试异步执行 (run_agent) ===")

    agent = create_example_agent()
    start_time = time.time()

    # 执行查询
    result = await runtime_service.run_agent(
        agent=agent,
        input_text="北京今天天气怎么样？",
        session_id="test-async-session"
    )

    # 显示结果
    print(f"输入: 北京今天天气怎么样？")
    print(f"输出: {result['output']}")
    print(f"耗时: {time.time() - start_time:.2f}秒")

    # 第二次查询使用相同会话
    result = await runtime_service.run_agent(
        agent=agent,
        input_text="我之前问你什么了？然后现在几点了？",
        session_id="test-async-session"
    )

    # 显示结果
    print(f"\n输入: 现在几点了？")
    print(f"输出: {result['output']}")


# 同步执行示例
def test_sync_execution():
    """
    测试同步执行方法 (Runner.run_sync)
    """
    print("\n=== 测试同步执行 (run_agent_sync) ===")

    agent = create_example_agent()
    start_time = time.time()

    # 执行查询
    result = runtime_service.run_agent_sync(
        agent=agent,
        input_text="上海的天气如何？",
        session_id="test-sync-session"
    )

    # 显示结果
    print(f"输入: 上海的天气如何？")
    print(f"输出: {result['output']}")
    print(f"耗时: {time.time() - start_time:.2f}秒")


# 流式执行示例
async def test_streamed_execution():
    """
    测试流式执行方法 (Runner.run_streamed)
    """
    print("\n=== 测试流式执行 (run_agent_streamed) ===")

    agent = create_example_agent()
    start_time = time.time()

    print(f"输入: 广州今天天气怎么样？请详细解释一下。")
    print("输出: ", end="", flush=True)

    # 流式执行  run_agent_streamed
    async for chunk in runtime_service.run_agent_streamed(
            agent=agent,
            input_text="广州今天天气怎么样？请详细解释一下。",
            session_id="test-streamed-session"
    ):
        # 只处理内容块
        if chunk.get("type") == "content" and chunk.get("content"):
            print(chunk["content"], end="", flush=True)

        # 处理完成事件    
        if chunk.get("done"):
            print("\n")
            break

    print(f"耗时: {time.time() - start_time:.2f}秒")


# 配置选项示例
async def test_config_options():
    """
    测试RunConfig配置选项
    演示如何配置RunConfig和ModelSettings来调整代理运行时的行为
    """
    print("\n=== 测试配置选项 (RunConfig) ===")

    agent = create_example_agent()
    start_time = time.time()

    # 创建ModelSettings配置模型参数
    model_settings = ModelSettings(
        temperature=0.2,  # 控制输出的随机性（0-1之间，越低越确定性）
        top_p=0.9,        # 控制token选择的概率阈值
        max_tokens=500,   # 限制响应生成的最大token数
    )
    
    # 创建RunConfig实例
    run_config = RunConfig(
        model_settings=model_settings,  # 模型设置
        tracing_disabled=True
        # run_context_wrapper=None      # 可选：自定义上下文包装器
    )

    print(f"输入: 请分析北京的天气情况并提供穿衣建议。")
    print("使用配置: 模型=gpt-4o, 温度=0.2, 最大token=500, 超时=30秒")
    
    # 异步执行，使用自定义配置
    result = await runtime_service.run_agent(
        agent=agent,
        input_text="请分析北京的天气情况并提供穿衣建议。",
        session_id="test-config-session",
        config=run_config  # 传递配置参数！
    )

    # 显示结果
    print(f"输出: {result['output']}")
    print(f"耗时: {time.time() - start_time:.2f}秒")
    
    # 简化的流式配置示例
    print("\n测试简化配置的流式执行...")
    
    # 创建简化的配置
    simple_config = RunConfig(
        # 只设置基本属性
        tracing_disabled=True
    )
    
    print(f"输入: 深圳今天天气怎么样？请给出详细信息。")
    print("使用配置: 默认模型, stream_mode=tokens, 超时=20秒")
    print("输出: ", end="", flush=True)
    
    # 流式执行，使用简化配置
    async for chunk in runtime_service.run_agent_streamed(
            agent=agent,
            input_text="深圳今天天气怎么样？请给出详细信息。",
            session_id="test-config-stream-session",
            config=simple_config  # 传递配置参数
    ):
        if chunk.get("type") == "content" and chunk.get("content"):
            print(chunk["content"], end="", flush=True)
            
        if chunk.get("done"):
            print("\n")
            break
            
    print(f"耗时: {time.time() - start_time:.2f}秒")
    
    # 配置解释
    print("\nRunConfig主要配置选项说明:")
    print("- model_settings: 控制模型名称、温度、top_p等生成参数")
    print("- timeout_seconds: 执行超时时间，超过则中断")
    print("- stream_mode: 流式输出模式 (auto/tokens/messages/final)")
    print("- debug: 是否启用调试模式，输出更多日志")
    print("- run_id: 可指定唯一运行ID，用于跟踪和调试")

async def main():
    """
    主函数 - 运行所有示例
    """
    print("===== OpenAI Agent SDK执行方法示例 =====")

    # 确认运行环境
    if not agent_factory.current_provider and not os.environ.get("OPENAI_API_KEY"):
        print("警告: 未设置模型提供者且未找到OPENAI_API_KEY环境变量")
        print("这可能导致代理执行失败，请确保设置了正确的API密钥")
        user_continue = input("是否继续执行示例? (y/n): ")
        if user_continue.lower() != 'y':
            print("退出示例")
            return

    # 运行示例
    try:
        # await test_async_execution()  # 异步执行
        
        # 注意：同步方法不应在异步上下文中调用，这里仅作为演示
        # 在实际应用中，应该在异步和同步调用之间做出明确选择
        # 或者使用不同的进程/脚本分别运行
        # test_sync_execution()  # 同步执行 - 在异步上下文中可能导致死锁
        
        await test_streamed_execution()  # 流式执行

        # await test_config_options()  # 配置选项示例
        print("\n所有示例执行完成!")
        
        print("\n为了避免在异步上下文中调用同步方法的问题，")
        print("请在主程序结束后再单独测试同步方法")
    except Exception as e:
        print(f"示例执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
    
    # 主程序结束后，事件循环已关闭，现在可以安全地调用同步方法
    # print("\n\n=== 主程序结束，现在测试同步方法 ===")
    # try:
    #     test_sync_execution()  # 同步执行
    # except Exception as e:
    #     print(f"同步执行测试发生错误: {e}")
    #     import traceback
    #     traceback.print_exc()
