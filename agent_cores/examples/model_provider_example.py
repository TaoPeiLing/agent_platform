"""
模型提供者示例 - 展示如何使用不同的模型提供者
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import argparse

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入项目组件
from agent_cores.model_providers import list_providers, get_provider
from agent_cores.core.factory import agent_factory
from agents import Agent, function_tool, Runner

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 示例工具
@function_tool
def get_weather(location: str) -> str:
    """
    获取指定位置的天气信息（模拟）

    Args:
        location: 地点名称
    """
    # 这只是一个模拟工具
    locations = {
        "北京": "晴天，25°C",
        "上海": "多云，28°C",
        "广州": "小雨，30°C",
        "深圳": "阵雨，29°C",
        "杭州": "晴天，26°C"
    }

    return f"{location}的天气：{locations.get(location, '数据不可用')}"


@function_tool
def get_time() -> str:
    """获取当前时间"""
    from datetime import datetime
    now = datetime.now()
    return f"当前时间是：{now.strftime('%Y-%m-%d %H:%M:%S')}"


# 代理指令
INSTRUCTIONS = """
你是一个有用的智能助手。你可以：
1. 提供天气信息
2. 回答用户问题
3. 提供当前时间

尽量使用中文回答用户提问。
保持回答简洁、准确、友好。
"""


async def test_provider(provider_name: str, api_key: Optional[str] = None, **kwargs):
    """
    测试指定的模型提供者

    Args:
        provider_name: 提供者名称
        api_key: API密钥
        **kwargs: 其他提供者特定参数
    """
    logger.info(f"正在测试模型提供者: {provider_name}")

    try:
        # 1. 初始化提供者
        provider = get_provider(provider_name, **kwargs)

        # 2. 设置客户端
        if api_key is None:
            # 尝试从环境变量获取
            api_key_var = f"{provider_name.upper()}_API_KEY"
            api_key = os.environ.get(api_key_var)
            if not api_key:
                raise ValueError(f"未提供API密钥，请设置{api_key_var}环境变量或提供api_key参数")

        # 设置客户端 - 针对特定提供者的额外参数
        if provider_name == "baidu":
            secret_key = kwargs.get("secret_key") or os.environ.get("BAIDU_SECRET_KEY")
            if not secret_key:
                raise ValueError(f"百度文心一言需要Secret Key，请设置BAIDU_SECRET_KEY环境变量或提供secret_key参数")
            provider.setup_client(api_key=api_key, secret_key=secret_key)
        else:
            agent_factory.set_model_provider(provider_name, api_key=api_key)
            # provider.setup_client(api_key=api_key)

        # 3. 创建代理
        model_info = agent_factory.get_default_model_provider()
        logger.info(f"使用模型: {model_info['model']} (提供者: {model_info['provider']})")

        agent = Agent(
            name="助手",
            instructions=INSTRUCTIONS,
            model=agent_factory.default_model,
            tools=[get_weather, get_time]
        )

        # 4. 测试查询
        queries = [
            "你好，请告诉我北京的天气怎么样？",
            "现在几点了？",
            "你能做什么？"
        ]

        for query in queries:
            logger.info(f"\n用户: {query}")

            # 执行查询
            result = await Runner.run(agent, query)
            logger.info(f"助手: {result.final_output}")

        logger.info(f"\n{provider_name} 测试完成\n{'=' * 50}")
        return True

    except Exception as e:
        logger.error(f"测试 {provider_name} 失败: {e}")
        return False


async def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="测试不同的模型提供者")
    parser.add_argument("--provider", type=str, default="all", help="要测试的提供者名称 (openai, zhipu, baidu, 或 all)")
    args = parser.parse_args()
    # 运行命令
    # python model_provider_example.py --provider zhipu
    # 获取可用提供者
    available_providers = list_providers()
    logger.info(f"可用的模型提供者: {', '.join(available_providers.keys())}")

    # 决定要测试的提供者
    if args.provider.lower() == "all":
        providers_to_test = list(available_providers.keys())
    else:
        if args.provider not in available_providers:
            logger.error(f"未知的提供者: {args.provider}")
            return
        providers_to_test = [args.provider]

    # 测试每个提供者
    results = {}
    for provider in providers_to_test:
        success = await test_provider(provider)
        results[provider] = "成功" if success else "失败"

    # 打印测试结果摘要
    logger.info("\n测试结果摘要:")
    for provider, result in results.items():
        logger.info(f"{provider}: {result}")


if __name__ == "__main__":
    # 加载环境变量
    from dotenv import load_dotenv,find_dotenv

    load_dotenv(find_dotenv(".env_development"))

    # 运行测试
    asyncio.run(main())