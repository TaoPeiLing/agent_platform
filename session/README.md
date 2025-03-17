# 会话管理服务

高性能、可扩展的会话管理服务，为业务系统提供统一的会话管理机制。

## 功能特性

- **灵活的存储策略**：支持多种存储后端（Redis、数据库等），可根据需求动态切换
- **访问控制**：完整的会话访问权限控制，支持私有、共享与公开会话
- **生命周期管理**：自动化会话创建、过期与清理过程
- **高性能**：针对高并发场景优化，支持异步操作
- **可扩展**：模块化设计，易于扩展和定制

## 架构设计

会话管理服务采用模块化架构，主要包含以下组件：

1. **核心管理器 (SessionManager)**：统一入口，协调各个子模块
2. **会话模型 (Session & SessionMetadata)**：定义会话数据结构
3. **存储管理 (Storage)**：负责会话持久化
4. **访问控制 (AccessController)**：处理权限验证
5. **生命周期管理 (LifecycleManager)**：处理会话创建与过期

## 目录结构

```
session/
├── __init__.py               # 模块入口
├── session_manager.py        # 核心管理器
├── models/                   # 数据模型
│   ├── __init__.py
│   └── session.py            # 会话模型定义
├── storage/                  # 存储管理
│   ├── __init__.py           # 存储接口
│   ├── base.py               # 基类定义
│   ├── factory.py            # 工厂模式
│   └── redis_provider.py     # Redis存储实现
├── access/                   # 访问控制
│   ├── __init__.py
│   └── access_control.py     # 访问控制器
├── lifecycle/                # 生命周期管理
│   ├── __init__.py
│   └── lifecycle_manager.py  # 生命周期管理器
└── examples/                 # 使用示例
    └── main.py               # 示例代码
```

## 快速开始

### 安装依赖

```bash
pip install aioredis==2.0.1
```

### 基本使用

```python
import asyncio
from agent_cores.session import get_session_manager

async def main():
    # 获取会话管理器
    session_manager = get_session_manager()
    
    # 初始化会话管理器
    await session_manager.initialize()
    
    try:
        # 创建会话
        session_id = await session_manager.create_session(
            user_id="user123",
            metadata={"tags": ["demo"]}
        )
        
        # 添加消息
        await session_manager.add_message(
            session_id=session_id,
            user_id="user123",
            role="user",
            content="你好，这是一条测试消息"
        )
        
        # 获取会话消息
        messages = await session_manager.get_session_messages(
            session_id=session_id, 
            user_id="user123"
        )
        
        print(f"会话消息: {messages}")
        
    finally:
        # 关闭会话管理器
        await session_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## 配置

会话管理服务支持以下配置项：

### Redis 存储设置

在环境变量或配置文件中设置：

```
REDIS_URL=redis://localhost:6379/0
SESSION_KEY_PREFIX=session:
SESSION_DEFAULT_EXPIRY=86400  # 过期时间（秒）
```

### 自定义存储提供者

```python
from agent_cores.session.storage import StorageFactory
from your_module import CustomStorageProvider

# 注册自定义存储提供者
StorageFactory.register_provider("custom", CustomStorageProvider)

# 使用自定义存储
session_manager = get_session_manager(storage_type="custom")
```

## API 参考

### SessionManager

核心管理类，提供会话管理的主要功能：

- `create_session(user_id, metadata=None, ttl_hours=24)` - 创建新会话
- `get_session(session_id, user_id)` - 获取会话
- `update_session(session_id, user_id, context_updates=None, metadata_updates=None)` - 更新会话
- `add_message(session_id, user_id, role, content)` - 添加消息
- `list_user_sessions(user_id, status=None, limit=10, offset=0)` - 列出用户会话
- `delete_session(session_id, user_id)` - 删除会话
- `share_session(session_id, owner_id, target_user_id)` - 分享会话
- `get_session_messages(session_id, user_id, limit=50)` - 获取会话消息

### 存储接口

所有存储提供者必须实现以下接口：

- `save_session(session)` - 保存会话
- `load_session(session_id)` - 加载会话
- `delete_session(session_id)` - 删除会话
- `list_sessions(owner_id=None, status=None, tags=None, limit=10, offset=0)` - 列出会话
- `update_metadata(session_id, metadata_updates)` - 更新元数据
- `clean_expired_sessions()` - 清理过期会话
- `get_statistics()` - 获取统计信息

## 性能与扩展性

会话管理服务设计支持高并发场景：

- 异步I/O操作，避免阻塞
- 连接池管理减少资源消耗
- 分页查询减轻服务器负担
- 可配置的自动清理任务，防止资源泄漏
- 模块化设计便于水平扩展

## 贡献指南

欢迎贡献代码或提交问题，请遵循以下步骤：

1. Fork项目
2. 创建分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 提交Pull Request

## 许可证

请查看LICENSE文件了解项目许可证信息。 