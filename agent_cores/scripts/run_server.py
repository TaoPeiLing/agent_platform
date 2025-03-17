#!/usr/bin/env python
"""
运行API服务器的脚本
"""
import os
import sys
import argparse
import logging
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置环境
from dotenv import load_dotenv
load_dotenv()

# 配置日志
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def main():
    """
    运行API服务器主函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="运行SSS Agent Platform API服务器")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="主机地址")
    parser.add_argument("--port", type=int, default=8000, help="端口号")
    parser.add_argument("--reload", action="store_true", help="启用自动重载")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # 检查环境变量
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("⚠️ OPENAI_API_KEY环境变量未设置，将使用.env文件中的值")
    
    # 注册模型提供者
    try:
        from agent_cores.core.factory import AgentFactory
        from agent_cores.model_providers import get_provider
        
        factory = AgentFactory()
        
        # 设置默认提供者（如果有API密钥）
        provider_name = os.environ.get("DEFAULT_MODEL_PROVIDER", "openai")
        api_key = os.environ.get(f"{provider_name.upper()}_API_KEY")
        
        if api_key:
            logger.info(f"🔌 正在初始化默认模型提供者: {provider_name}")
            factory.set_model_provider(provider_name, api_key)
        else:
            logger.warning(f"⚠️ 未找到{provider_name.upper()}_API_KEY，将使用临时客户端")
        
        # 显示可用的提供者
        available_providers = factory.get_available_providers()
        logger.info(f"✅ 可用的模型提供者: {', '.join(available_providers)}")
        
    except Exception as e:
        logger.error(f"❌ 初始化模型提供者失败: {e}")
    
    # 注册代理模板
    try:
        # 使用新创建的agent_templates模块
        from agent_cores.examples.agent_templates import register_all_templates
        
        # 注册所有模板
        registered_templates = register_all_templates()
        
        if registered_templates:
            logger.info(f"✅ 已成功注册 {len(registered_templates)} 个代理模板: {', '.join(registered_templates)}")
        else:
            # 如果没有找到模板配置，创建默认模板
            from agent_cores.examples.agent_templates import create_default_templates
            create_default_templates()
            logger.info("✅ 已注册默认代理模板")
    except Exception as e:
        logger.error(f"❌ 注册代理模板失败: {e}")
        logger.exception(e)
    
    # 显示服务器信息
    logger.info(f"🚀 启动SSS Agent Platform API服务器")
    logger.info(f"📡 服务地址: http://{args.host}:{args.port}")
    logger.info(f"🔄 自动重载: {'启用' if args.reload else '禁用'}")
    logger.info(f"🐞 调试模式: {'启用' if args.debug else '禁用'}")
    
    # 启动服务器
    uvicorn.run(
        "agent_cores.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 服务器已停止")
    except Exception as e:
        logger.critical(f"💥 服务器启动失败: {e}")
        sys.exit(1) 