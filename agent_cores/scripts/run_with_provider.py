"""
运行脚本 - 使用指定的模型提供者运行代理
"""
import os
import sys
import asyncio
from pathlib import Path
import argparse
import logging
from dotenv import load_dotenv, find_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入项目组件
from agent_cores.core.factory import agent_factory
from agent_cores.model_providers import list_providers, get_provider
from agent_cores.utils.logging_config import setup_logging, get_logger
from agents import Agent, Runner, ModelSettings
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

# 配置日志
setup_logging(app_name="run_with_provider")
logger = get_logger(__name__)

async def run_with_provider(
        provider_name: str,
        input_text: str,
        agent_template: str = None,
        instructions: str = None,
        model_name: str = None,
        verbose: bool = False
):
    """
    使用指定的模型提供者运行代理

    Args:
        provider_name: 提供者名称
        input_text: 输入文本
        agent_template: 代理模板名称
        instructions: 代理指令
        model_name: 模型名称
        verbose: 是否显示详细日志
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # 1. 设置模型提供者
        api_key_var = f"{provider_name.upper()}_API_KEY"
        api_key = os.getenv(api_key_var)

        if not api_key:
            logger.error(f"未找到API密钥环境变量: {api_key_var}")
            return

        # 针对不同提供者的特殊处理
        if provider_name == "baidu":
            secret_key = os.environ.get("BAIDU_SECRET_KEY")
            if not secret_key:
                logger.error("未找到百度Secret Key环境变量: BAIDU_SECRET_KEY")
                return
            agent_factory.set_model_provider(provider_name, api_key, secret_key=secret_key)
        else:
            agent_factory.set_model_provider(provider_name, api_key)

        # 2. 获取或创建代理
        agent = None

        if agent_template:
            # 从模板创建代理
            if agent_template in agent_factory.templates:
                agent = agent_factory.create_from_template(agent_template)
                logger.info(f"使用模板创建代理: {agent_template}")
            else:
                logger.warning(f"未找到模板: {agent_template}")

        if agent is None:
            # 创建新代理
            provider_model = model_name
            if provider_model is None:
                # 使用提供者默认模型
                if agent_factory.current_provider:
                    # 获取模型对象
                    provider_model = agent_factory.current_provider.get_model_info()["model"]
                else:
                    provider_model = agent_factory.default_model

            agent_instructions = instructions or "你是一个有帮助的智能助手。尽量提供简洁、准确的回答。"
            
            # 获取模型对象（如果提供者支持）
            model_obj = None
            if hasattr(agent_factory.current_provider, 'get_model_object'):
                model_obj = agent_factory.current_provider.get_model_object()
            
            # 创建代理
            if model_obj:
                # 使用模型对象创建代理
                agent = Agent(
                    name="助手",
                    instructions=agent_instructions,
                    model=model_obj,
                    model_settings=ModelSettings(temperature=0.7)
                )
                logger.info(f"使用模型对象创建代理: {provider_model}")
            else:
                # 使用模型名称创建代理
                agent = Agent(
                    name="助手",
                    instructions=agent_instructions,
                    model=provider_model,
                    model_settings=ModelSettings(temperature=0.7)
                )
                logger.info(f"使用模型名称创建代理: {provider_model}")

        # 3. 运行代理
        logger.info(f"输入: {input_text}")
        result = await Runner.run(agent, input_text)

        # 4. 输出结果
        print("\n" + "=" * 50)
        print(f"提供者: {provider_name}")
        print(f"模型: {agent.model}")
        print("=" * 50)
        print(f"输入: {input_text}")
        print("-" * 50)
        print(f"输出: {result.final_output}")
        print("=" * 50)

        return result

    except Exception as e:
        logger.error(f"运行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="使用指定的模型提供者运行代理")
    parser.add_argument("--provider", type=str, required=True, help="提供者名称 (openai, zhipu, baidu)")
    parser.add_argument("--input", type=str, required=True, help="输入文本")
    parser.add_argument("--template", type=str, help="代理模板名称")
    parser.add_argument("--instructions", type=str, help="代理指令")
    parser.add_argument("--model", type=str, help="模型名称")
    parser.add_argument("--verbose", action="store_true", help="显示详细日志")
    args = parser.parse_args()

    # 加载环境变量
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(".env_development"))

    # 获取可用提供者
    available_providers = list(list_providers().keys())
    if args.provider not in available_providers:
        logger.error(f"未知的提供者: {args.provider}")
        logger.info(f"可用的提供者: {', '.join(available_providers)}")
        return

    # 运行代理
    asyncio.run(run_with_provider(
        provider_name=args.provider,
        input_text=args.input,
        agent_template=args.template,
        instructions=args.instructions,
        model_name=args.model,
        verbose=args.verbose
    ))
# 运行： python run_with_provider.py --provider zhipu --input "讲个笑话" --instructions "你是一个幽默的助手，善
# 于讲笑话"


if __name__ == "__main__":
    main()