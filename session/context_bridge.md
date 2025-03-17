# 会话-上下文桥接模块使用指南

本文档介绍如何使用`SessionContextBridge`模块在项目任何位置无缝集成会话管理服务与SimpleContext。

## 概述

`SessionContextBridge`是一个连接会话管理服务与SimpleContext的桥接器，它遵循OpenAI Agent SDK的依赖注入设计理念，提供简洁的API，使得开发者可以：

1. 在持久化存储与内存上下文间轻松切换
2. 按照SDK设计理念，将Context作为依赖注入对象传递给代理
3. 避免重复系统指令，不干扰模板中的指令设置

## 导入模块

```python
from agent_cores.session import SessionContextBridge, get_session_context_bridge
```

## 创建会话并获取Context

### 方法1：使用工厂方法创建新会话

```python
# 创建一个新会话并获取桥接器
context_bridge = await SessionContextBridge.create_session(
    user_id="user123",
    user_name="张三",
    metadata={"preference": "简短回答", "language": "zh-CN"},
    ttl_hours=24,  # 24小时过期
    system_message="你是一个智能助手，负责回答用户问题。当前用户是张三。"
)

# 从会话加载上下文对象
context = await context_bridge.get_context()
```

### 方法2：连接到现有会话

```python
# 连接到现有会话
context_bridge = get_session_context_bridge(
    session_id="existing_session_id",
    user_id="user123",
    user_name="张三"
)

# 从会话加载上下文对象
context = await context_bridge.get_context()
```

### 方法3：从SimpleContext创建新会话

```python
# 如果你已经有了一个SimpleContext对象
from agent_cores.core.simple_context import SimpleContext

existing_context = SimpleContext(
    user_id="user123",
    user_name="张三",
    metadata={"preference": "简短回答"}
)
existing_context.add_system_message("你是一个智能助手。")

# 从现有上下文创建持久化会话
context_bridge = await SessionContextBridge.from_context(
    context=existing_context,
    ttl_hours=24
)
```

## 在代理执行中使用

```python
# 获取代理实例
agent = template_manager.get_template("assistant_agent")

# 添加用户消息
await context_bridge.add_message("user", "你好，请问你是谁?")

# 获取当前上下文对象
context = await context_bridge.get_context()

# 运行代理 - 传递上下文作为依赖注入对象
result = await runtime_service.run_agent(
    agent=agent,
    input_text="你好，请问你是谁?",
    session_id=context_bridge.session_id,
    context=context  # SimpleContext对象
)

# 添加助手回复到会话
await context_bridge.add_message("assistant", result["output"])
```

## 上下文管理

### 添加消息

```python
# 添加用户消息
await context_bridge.add_message("user", "用户消息内容")

# 添加助手消息
await context_bridge.add_message("assistant", "助手回复内容")

# 添加系统消息
await context_bridge.add_system_message("系统消息内容")
```

### 获取消息

```python
# 获取所有消息
all_messages = await context_bridge.get_messages()

# 获取最近的N条消息
recent_messages = await context_bridge.get_messages(limit=5)
```

### 更新元数据

```python
# 更新会话元数据
await context_bridge.update_metadata({
    "preference": "详细回答",
    "custom_field": "custom_value"
})
```

## 会话管理

```python
# 获取会话对象
session = await context_bridge.get_session()

# 获取会话ID
session_id = context_bridge.session_id

# 释放资源
await context_bridge.close()
```

## 在异步API中使用

```python
from fastapi import FastAPI, Depends
from agent_cores.session import SessionContextBridge

app = FastAPI()

async def get_context_bridge(user_id: str, session_id: str = None):
    """FastAPI的依赖注入函数，获取或创建上下文桥接器"""
    if session_id:
        # 连接到现有会话
        bridge = get_session_context_bridge(session_id, user_id)
    else:
        # 创建新会话
        bridge = await SessionContextBridge.create_session(user_id=user_id)
    
    try:
        yield bridge
    finally:
        await bridge.close()

@app.post("/chat")
async def chat(
    message: str,
    user_id: str,
    session_id: str = None,
    context_bridge: SessionContextBridge = Depends(get_context_bridge)
):
    # 添加用户消息
    await context_bridge.add_message("user", message)
    
    # 获取上下文
    context = await context_bridge.get_context()
    
    # 运行代理
    agent = template_manager.get_template("assistant_agent")
    result = await runtime_service.run_agent(
        agent=agent,
        input_text=message,
        session_id=context_bridge.session_id,
        context=context
    )
    
    # 添加助手回复
    await context_bridge.add_message("assistant", result["output"])
    
    return {
        "session_id": context_bridge.session_id,
        "response": result["output"]
    }
```

## 最佳实践

1. **尽早创建、晚些释放**：在请求开始时创建桥接器，在请求结束时释放
2. **缓存上下文**：使用`refresh=False`参数可以利用缓存减少数据库查询
3. **保持状态同步**：优先使用桥接器的方法添加消息，确保会话和缓存保持同步
4. **依赖注入模式**：遵循OpenAI Agent SDK的设计理念，将Context作为依赖注入对象传递

## 注意事项

1. `SessionContextBridge`是异步API，所有操作都应该使用`await`调用
2. 当不再需要桥接器时，应调用`close()`方法释放资源
3. 系统消息会自动保存在会话中，不会被覆盖或删除 