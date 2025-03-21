# 企业连接器使用指南

本文档介绍了SSS Agent Platform的企业连接器，它提供了标准化的接口，使第三方系统能够轻松地集成和使用智能体平台的能力。

## 1. 概述

企业连接器是一组标准化的接口和实现，用于将SSS Agent Platform的智能体能力暴露给外部系统。它支持多种连接方式，包括：

- **HTTP REST API**：提供标准的RESTful API接口，支持同步和异步调用模式
- **HTTP+SSE**：提供基于Server-Sent Events的流式响应接口，适用于需要实时输出的场景

## 2. 连接器类型

### 2.1 HTTP REST连接器

HTTP REST连接器提供了一组RESTful API，支持同步和异步调用模式。

#### 主要端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/agents/{agent_id}/invoke` | POST | 同步调用单个智能体 |
| `/v1/agents/{agent_id}/ainvoke` | POST | 异步调用单个智能体 |
| `/v1/workflows/{workflow_id}/invoke` | POST | 同步调用多智能体工作流 |
| `/v1/workflows/{workflow_id}/ainvoke` | POST | 异步调用多智能体工作流 |
| `/v1/executions/{execution_id}` | GET | 获取执行状态 |

#### 请求示例

同步调用智能体：

```bash
curl -X POST http://localhost:8000/v1/agents/general_assistant/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": "你能介绍一下自己吗？",
    "options": {
      "temperature": 0.7
    }
  }'
```

异步调用智能体：

```bash
curl -X POST http://localhost:8000/v1/agents/general_assistant/ainvoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": "你能介绍一下自己吗？",
    "options": {
      "temperature": 0.7
    },
    "callback_url": "http://your-server.com/callback"
  }'
```

### 2.2 HTTP+SSE连接器

HTTP+SSE连接器提供了基于Server-Sent Events的流式响应接口，适用于需要实时输出的场景。

#### 主要端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/agents/{agent_id}/stream` | POST | 流式调用单个智能体 |
| `/v1/workflows/{workflow_id}/stream` | POST | 流式调用多智能体工作流 |

#### 事件类型

| 事件类型 | 说明 |
|---------|------|
| `start` | 开始事件 |
| `thinking` | 智能体思考过程 |
| `chunk` | 内容片段 |
| `tool_call` | 工具调用 |
| `tool_result` | 工具调用结果 |
| `metadata` | 元数据信息 |
| `error` | 错误信息 |
| `done` | 完成标记 |

#### 请求示例

```bash
curl -X POST http://localhost:8001/v1/agents/general_assistant/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "input": "你能解释一下大语言模型是如何工作的？",
    "options": {
      "temperature": 0.7
    }
  }'
```

#### JavaScript客户端示例

```javascript
const eventSource = new EventSource('http://localhost:8001/v1/agents/general_assistant/stream');

eventSource.addEventListener('thinking', (event) => {
  const data = JSON.parse(event.data);
  console.log('智能体思考:', data.content);
});

eventSource.addEventListener('chunk', (event) => {
  const data = JSON.parse(event.data);
  console.log('内容片段:', data.content);
});

eventSource.addEventListener('error', (event) => {
  const data = JSON.parse(event.data);
  console.error('错误:', data.message);
  eventSource.close();
});

eventSource.addEventListener('done', () => {
  console.log('完成');
  eventSource.close();
});
```

## 3. Python代码集成示例

### 3.1 使用HTTP连接器

```python
from agent_cores.connectors import connector_factory

# 获取HTTP连接器
http_connector = connector_factory.get_connector("http")

# 同步调用智能体
response = http_connector.invoke_agent(
    agent_id="general_assistant",
    input_data="你能介绍一下自己吗？",
    options={
        "temperature": 0.7,
        "metadata": {"source": "my_application"}
    }
)

print(f"执行ID: {response.execution_id}")
print(f"状态: {response.status}")
print(f"结果: {response.result}")
```

### 3.2 使用SSE连接器

```python
import asyncio
from agent_cores.connectors import connector_factory

async def stream_example():
    # 获取SSE连接器
    sse_connector = connector_factory.get_connector("sse")
    
    # 流式调用智能体
    async for chunk in sse_connector.stream_agent(
        agent_id="general_assistant",
        input_data="请解释一下大语言模型是如何工作的？",
        options={
            "temperature": 0.7
        }
    ):
        if "thinking" in chunk:
            print(f"思考: {chunk['thinking']}")
        elif "content" in chunk:
            print(f"内容: {chunk['content']}")

# 运行异步函数
asyncio.run(stream_example())
```

## 4. 启动连接器服务器

SSS Agent Platform提供了一个示例脚本，可以启动连接器服务器：

```bash
# 启动HTTP REST API服务器
python -m agent_cores.examples.connector_usage --mode server --connector http

# 启动SSE API服务器
python -m agent_cores.examples.connector_usage --mode server --connector sse

# 同时启动两种服务器
python -m agent_cores.examples.connector_usage --mode server --connector all
```

## 5. 多智能体工作流

企业连接器也支持多智能体工作流的调用，允许多个智能体协作完成复杂任务。

### 5.1 同步工作流调用

```bash
curl -X POST http://localhost:8000/v1/workflows/data_analysis_workflow/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": "分析这份销售数据并给出建议",
    "options": {
      "data_source": "sales_q2_2023.csv"
    }
  }'
```

### 5.2 流式工作流调用

```bash
curl -X POST http://localhost:8001/v1/workflows/data_analysis_workflow/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "input": "分析这份销售数据并给出建议",
    "options": {
      "data_source": "sales_q2_2023.csv"
    }
  }'
```

## 6. 安全与授权

企业连接器支持多种认证方式，包括API密钥和JWT令牌。

### 6.1 使用API密钥

```bash
curl -X POST http://localhost:8000/v1/agents/general_assistant/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "input": "你能介绍一下自己吗？"
  }'
```

### 6.2 使用JWT令牌

```bash
curl -X POST http://localhost:8000/v1/agents/general_assistant/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "input": "你能介绍一下自己吗？"
  }'
```

## 7. 错误处理

企业连接器使用标准的HTTP状态码和结构化的错误响应：

```json
{
  "error": {
    "message": "智能体调用失败",
    "code": "agent_execution_error",
    "details": "模型服务暂时不可用"
  }
}
```

常见错误码：

| 状态码 | 错误码 | 说明 |
|-------|-------|------|
| 400 | invalid_request | 请求参数错误 |
| 401 | unauthorized | 未授权 |
| 403 | forbidden | 权限不足 |
| 404 | not_found | 资源不存在 |
| 429 | rate_limit_exceeded | 超出速率限制 |
| 500 | internal_error | 内部服务器错误 |

## 8. 性能考虑

- 对于短小的请求，推荐使用同步调用模式
- 对于可能需要较长时间处理的请求，推荐使用异步调用模式
- 对于需要实时反馈的场景，推荐使用流式调用模式
- 考虑使用连接池和保持连接以提高性能 