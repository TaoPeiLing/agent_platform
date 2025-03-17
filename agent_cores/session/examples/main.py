"""
会话管理示例 - 演示如何使用会话管理系统
"""

import asyncio
import logging
import os
import sys
import uuid
from typing import Dict, Any

# 首先加载环境变量，确保在导入其他模块前完成
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(".env_development"))

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from agent_cores.session import get_session_manager
from agent_cores.core.simple_context import SimpleContext

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


async def create_and_use_session():
    """创建并使用会话的示例"""
    # 获取会话管理器
    session_manager = get_session_manager()

    # 初始化会话管理器
    await session_manager.initialize()

    try:
        # 创建用户ID
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        logger.info(f"创建用户: {user_id}")

        # 创建会话
        session_metadata = {
            "tags": ["demo", "example"],
            "properties": {
                "app_name": "Session Demo",
                "version": "1.0.0"
            }
        }

        session_id = await session_manager.create_session(
            user_id=user_id,
            metadata=session_metadata,
            ttl_hours=1  # 1小时后过期
        )

        if not session_id:
            logger.error("创建会话失败")
            return

        logger.info(f"成功创建会话: {session_id}")

        # 添加系统消息
        system_message = "你是一个友好的助手，帮助用户回答问题。"
        await session_manager.add_system_message(session_id, user_id, system_message)
        logger.info("已添加系统消息")

        # 添加用户消息
        await session_manager.add_message(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content="你好，请介绍一下自己。"
        )
        logger.info("已添加用户消息")

        # 添加助手消息
        await session_manager.add_message(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content="你好！我是一个AI助手，随时准备帮助你解答问题或提供信息。有什么我可以帮到你的吗？"
        )
        logger.info("已添加助手消息")

        # 获取会话消息
        messages = await session_manager.get_session_messages(session_id, user_id)
        logger.info(f"会话消息列表:")
        for i, msg in enumerate(messages):
            logger.info(f"  [{i + 1}] {msg['role']}: {msg['content'][:50]}...")

        # 列出用户的所有会话
        sessions = await session_manager.list_user_sessions(user_id)
        logger.info(f"用户 {user_id} 的会话列表:")
        for i, session in enumerate(sessions):
            logger.info(
                f"  [{i + 1}] ID: {session['id']}, 创建时间: {session['created_at']}, 状态: {session['status']}")

        # 共享会话给另一个用户
        other_user_id = f"user_{uuid.uuid4().hex[:8]}"
        logger.info(f"创建另一个用户: {other_user_id}")

        shared = await session_manager.share_session(session_id, user_id, other_user_id)
        if shared:
            logger.info(f"已成功将会话 {session_id} 共享给用户 {other_user_id}")

            # 新用户访问会话
            shared_session = await session_manager.get_session(session_id, other_user_id)
            if shared_session:
                logger.info(f"用户 {other_user_id} 成功访问共享会话")

                # 新用户添加消息
                await session_manager.add_message(
                    session_id=session_id,
                    user_id=other_user_id,
                    role="user",
                    content="我是新用户，我也有一个问题。"
                )
                logger.info(f"新用户已添加消息到共享会话")

        # 获取更新后的会话消息
        updated_messages = await session_manager.get_session_messages(session_id, user_id)
        logger.info(f"更新后的会话消息列表:")
        for i, msg in enumerate(updated_messages):
            logger.info(f"  [{i + 1}] {msg['role']}: {msg['content'][:50]}...")

        # 暂停会话
        await session_manager.update_session(
            session_id=session_id,
            user_id=user_id,
            metadata_updates={"status": "paused"}
        )
        logger.info(f"已暂停会话 {session_id}")

        # 获取会话统计信息
        stats = await session_manager.get_statistics()
        logger.info(f"存储统计信息: {stats}")

        # 删除会话
        deleted = await session_manager.delete_session(session_id, user_id)
        if deleted:
            logger.info(f"已成功删除会话 {session_id}")
        else:
            logger.error(f"删除会话 {session_id} 失败")

    except Exception as e:
        logger.exception(f"示例运行出错: {str(e)}")
    finally:
        # 关闭会话管理器
        await session_manager.shutdown()


async def benchmark():
    """简单的性能基准测试"""
    session_manager = get_session_manager()
    await session_manager.initialize()

    try:
        user_id = f"bench_user_{uuid.uuid4().hex[:8]}"
        logger.info(f"基准测试用户: {user_id}")

        # 创建多个会话
        session_count = 10
        session_ids = []

        logger.info(f"开始创建 {session_count} 个会话...")
        start_time = asyncio.get_event_loop().time()

        for i in range(session_count):
            session_id = await session_manager.create_session(
                user_id=user_id,
                metadata={"tags": ["benchmark"], "properties": {"test_id": i}}
            )
            if session_id:
                session_ids.append(session_id)

        end_time = asyncio.get_event_loop().time()
        logger.info(f"创建 {len(session_ids)} 个会话耗时: {end_time - start_time:.4f} 秒")

        if not session_ids:
            logger.error("没有创建成功的会话，退出基准测试")
            return

        # 向每个会话添加消息
        message_count = 20
        logger.info(f"向每个会话添加 {message_count} 条消息...")
        start_time = asyncio.get_event_loop().time()

        tasks = []
        for session_id in session_ids:
            for i in range(message_count):
                task = session_manager.add_message(
                    session_id=session_id,
                    user_id=user_id,
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"这是第 {i + 1} 条测试消息，用于性能测试。" * 5
                )
                tasks.append(task)

        await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        total_messages = len(session_ids) * message_count
        logger.info(f"添加 {total_messages} 条消息耗时: {end_time - start_time:.4f} 秒")
        logger.info(f"每秒消息处理量: {total_messages / (end_time - start_time):.2f} 条/秒")

        # 获取所有会话
        logger.info("检索所有会话...")
        start_time = asyncio.get_event_loop().time()

        sessions = await session_manager.list_user_sessions(
            user_id=user_id,
            limit=100
        )

        end_time = asyncio.get_event_loop().time()
        logger.info(f"检索 {len(sessions)} 个会话耗时: {end_time - start_time:.4f} 秒")

        # 清理测试数据
        logger.info("清理测试数据...")
        delete_tasks = []
        for session_id in session_ids:
            delete_tasks.append(session_manager.delete_session(session_id, user_id))

        await asyncio.gather(*delete_tasks)
        logger.info("基准测试完成")

    except Exception as e:
        logger.exception(f"基准测试出错: {str(e)}")
    finally:
        await session_manager.shutdown()


async def main():
    """主函数"""
    logger.info("=== 会话管理系统示例 ===")

    # 运行基本示例
    logger.info("\n=== 基本使用示例 ===")
    await create_and_use_session()

    # 运行基准测试
    logger.info("\n=== 性能基准测试 ===")
    await benchmark()

    logger.info("示例程序结束")


if __name__ == "__main__":
    asyncio.run(main())