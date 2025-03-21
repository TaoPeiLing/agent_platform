#!/usr/bin/env python
"""
企业连接器使用示例

这个脚本展示了如何使用各种企业连接器与智能体平台进行交互。
包括HTTP REST连接器和HTTP+SSE连接器的示例。
"""

import asyncio
import json
import os
from typing import Dict, Any
import uvicorn
import argparse
import logging

from agent_cores.connectors import connector_factory, HTTPConnector, SSEConnector

# 设置环境变量禁用Redis，避免连接错误
os.environ["USE_REDIS"] = "False"

# 首先加载环境变量，但不让它覆盖已设置的USE_REDIS
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(".env_development"), override=False)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_http_connector_example():
    """HTTP连接器使用示例"""
    logger.info("运行HTTP连接器示例...")
    
    # 获取HTTP连接器
    http_connector = connector_factory.get_connector("http")
    
    # 同步调用智能体
    try:
        response = http_connector.invoke_agent(
            agent_id="general_assistant",  # 替换为实际的智能体模板名称
            input_data="你能介绍一下自己吗？",
            options={
                "metadata": {"source": "connector_example"}
            },
            auth_context={
                "user_id": "example_user",
                "roles": ["user", "admin"]  # 确保有权限调用智能体
            }
        )
        
        logger.info(f"同步调用结果: {json.dumps(response.to_dict(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        logger.error(f"同步调用出错: {e}")
    
    # 异步调用智能体
    try:
        response = await http_connector.ainvoke_agent(
            agent_id="general_assistant",  # 替换为实际的智能体模板名称
            input_data="有哪些常见的AI应用场景？",
            options={
                "metadata": {"source": "connector_example", "async": True}
            },
            auth_context={
                "user_id": "example_user",
                "roles": ["user", "admin"]  # 确保有权限调用智能体
            }
        )
        
        logger.info(f"异步调用结果: {json.dumps(response.to_dict(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        logger.error(f"异步调用出错: {e}")


async def run_sse_connector_example():
    """SSE连接器使用示例"""
    logger.info("运行SSE连接器示例...")
    
    # 获取SSE连接器
    sse_connector = connector_factory.get_connector("sse")
    
    # 流式调用智能体
    try:
        logger.info("开始流式调用...")
        
        async for chunk in sse_connector.stream_agent(
            agent_id="general_assistant",  # 替换为实际的智能体模板名称
            input_data="请解释一下大语言模型是如何工作的？",
            options={
                "metadata": {"source": "connector_example", "streaming": True}
            },
            auth_context={
                "user_id": "example_user",
                "roles": ["user", "admin"]  # 确保有权限调用智能体
            }
        ):
            # 在实际应用中，这些块会通过SSE发送给客户端
            if "thinking" in chunk:
                logger.info(f"思考: {chunk['thinking']}")
            elif "content" in chunk:
                logger.info(f"内容: {chunk['content']}")
            elif "tool_call" in chunk:
                logger.info(f"工具调用: {json.dumps(chunk['tool_call'], ensure_ascii=False)}")
            elif "tool_result" in chunk:
                logger.info(f"工具结果: {json.dumps(chunk['tool_result'], ensure_ascii=False)}")
            elif "error" in chunk:
                logger.error(f"错误: {chunk['error']}")
                
        logger.info("流式调用完成")
    except Exception as e:
        logger.error(f"流式调用出错: {e}")


async def run_http_server(host: str = "0.0.0.0", port: int = 8000):
    """运行HTTP服务器"""
    # 获取HTTP连接器
    http_connector = connector_factory.get_connector("http")
    
    # 启动HTTP服务器
    config = uvicorn.Config(
        http_connector.app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    logger.info(f"HTTP REST API服务器运行在 http://{host}:{port}")
    await server.serve()


async def run_sse_server(host: str = "0.0.0.0", port: int = 8001):
    """运行SSE服务器"""
    # 获取SSE连接器
    sse_connector = connector_factory.get_connector("sse")
    
    # 启动SSE服务器
    config = uvicorn.Config(
        sse_connector.app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    logger.info(f"SSE API服务器运行在 http://{host}:{port}")
    await server.serve()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="企业连接器示例")
    parser.add_argument("--mode", choices=["example", "server"], default="example",
                       help="运行模式：example（运行示例）或server（启动服务器）")
    parser.add_argument("--connector", choices=["http", "sse", "all"], default="all",
                       help="要使用的连接器类型")
    parser.add_argument("--http-port", type=int, default=8000,
                       help="HTTP服务器端口")
    parser.add_argument("--sse-port", type=int, default=8001,
                       help="SSE服务器端口")
    parser.add_argument("--redis", action="store_true", default=False,
                       help="使用Redis存储会话信息（默认不使用）")
    
    args = parser.parse_args()
    
    # 如果不使用Redis，确保USE_REDIS环境变量设置为False
    if not args.redis:
        os.environ["USE_REDIS"] = "False"
        logger.info("运行示例时不使用Redis存储会话")
    
    if args.mode == "example":
        if args.connector in ["http", "all"]:
            await run_http_connector_example()
            
        if args.connector in ["sse", "all"]:
            await run_sse_connector_example()
    else:  # server模式
        if args.connector == "http":
            await run_http_server(port=args.http_port)
        elif args.connector == "sse":
            await run_sse_server(port=args.sse_port)
        else:  # all
            # 使用asyncio.gather同时运行两个服务器
            await asyncio.gather(
                run_http_server(port=args.http_port),
                run_sse_server(port=args.sse_port)
            )


if __name__ == "__main__":
    asyncio.run(main()) 