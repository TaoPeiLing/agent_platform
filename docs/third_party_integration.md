# 第三方系统权限集成指南

本文档详细说明如何将第三方系统的用户权限与SSS Agent Platform的RBAC系统集成。

## 概述

SSS Agent Platform提供了灵活的权限传递机制，允许第三方系统在调用API时传递用户角色和权限信息。集成方式主要有三种：

1. **通过请求头传递** - 使用Authorization或自定义头部
2. **通过请求体传递** - 直接在JSON请求中包含角色信息
3. **通过WebSocket连接传递** - 在WebSocket消息中包含角色信息

## 权限传递机制

### 系统架构

权限传递的关键组件：

```
第三方系统 → API接口 → 会话管理 → 权限上下文 → 代理执行
```

1. **API接口层**：接收第三方系统传递的权限信息
2. **会话管理**：存储和管理用户的角色和权限
3. **权限上下文**：在代理运行时提供权限控制
4. **代理执行**：根据权限限制工具访问

### 支持的角色

系统默认支持以下角色，按权限从低到高排序：

- `guest`：访客，最小权限
- `user`：普通用户，基本操作权限
- `power_user`：高级用户，扩展操作权限
- `admin`：管理员，大部分系统权限
- `system`：系统级，完全访问权限

## 集成方法

### 1. 通过请求头传递权限

#### Authorization头（JWT集成）

如果第三方系统使用JWT授权，可以通过Authorization头传递角色信息：

```http
POST /api/v1/agents/run HTTP/1.1
Host: api.sss-agent.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "input": "查询天气",
  "template_name": "weather_assistant"
}
```

系统会从JWT令牌中提取角色信息。

#### 自定义角色头

也可以使用自定义头直接传递角色信息：

```http
POST /api/v1/agents/run HTTP/1.1
Host: api.sss-agent.com
X-User-Roles: admin,power_user
Content-Type: application/json

{
  "input": "查询数据库",
  "template_name": "database_assistant"
}
```

### 2. 通过请求体传递权限

直接在请求体中包含角色信息：

```http
POST /api/v1/agents/run HTTP/1.1
Host: api.sss-agent.com
Content-Type: application/json

{
  "input": "查询天气",
  "template_name": "weather_assistant",
  "roles": ["user", "power_user"],
  "user_id": "user123",
  "metadata": {
    "source": "third_party_system"
  }
}
```

### 3. 通过WebSocket传递权限

在WebSocket连接中的初始化消息中包含角色信息：

```javascript
// WebSocket连接示例
const socket = new WebSocket('ws://api.sss-agent.com/api/v1/agents/stream');

// 发送带有角色信息的消息
socket.send(JSON.stringify({
  "input": "查询天气",
  "template_name": "weather_assistant",
  "roles": ["user"],
  "user_id": "user123",
  "metadata": {
    "source": "third_party_system"
  }
}));
```

## 会话管理

系统支持通过会话ID保持权限状态：

1. 首次调用时不提供会话ID，系统会创建新会话并返回会话ID
2. 后续调用可使用返回的会话ID，保持用户上下文
3. 可以在请求中更新角色信息，会话会保存最新角色

```http
POST /api/v1/agents/run HTTP/1.1
Host: api.sss-agent.com
Content-Type: application/json

{
  "input": "查询天气",
  "template_name": "weather_assistant",
  "session_id": "f7a9b3c2-1234-5678-90ab-cdef01234567",
  "roles": ["admin"]  // 更新角色
}
```

## 权限优先级

当多种方式同时传递角色信息时，系统按以下优先级处理：

1. 请求体中的`roles`字段（最高优先级）
2. 自定义头`X-User-Roles`中的角色
3. Authorization头中的JWT角色信息
4. 现有会话中的角色信息
5. 默认角色`guest`（最低优先级）

## 代码示例

### Python示例

```python
import requests
import json

# API基础URL
API_BASE_URL = "http://api.sss-agent.com"

# 通过请求头调用
def call_with_auth_header():
    response = requests.post(
        f"{API_BASE_URL}/api/v1/agents/run",
        json={
            "input": "查询天气",
            "template_name": "weather_assistant"
        },
        headers={
            "X-User-Roles": "user,power_user"
        }
    )
    return response.json()

# 通过请求体调用
def call_with_roles_in_body():
    response = requests.post(
        f"{API_BASE_URL}/api/v1/agents/run",
        json={
            "input": "查询天气",
            "template_name": "weather_assistant",
            "roles": ["user"],
            "user_id": "user123"
        }
    )
    return response.json()
```

### JavaScript示例

```javascript
// 通过请求头调用
async function callWithAuthHeader() {
  const response = await fetch('http://api.sss-agent.com/api/v1/agents/run', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Roles': 'user,power_user'
    },
    body: JSON.stringify({
      input: '查询天气',
      template_name: 'weather_assistant'
    })
  });
  
  return await response.json();
}

// 通过WebSocket调用
function callViaWebSocket() {
  const socket = new WebSocket('ws://api.sss-agent.com/api/v1/agents/stream');
  
  socket.onopen = () => {
    socket.send(JSON.stringify({
      input: '查询天气',
      template_name: 'weather_assistant',
      roles: ['user']
    }));
  };
  
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
  };
}
```

## 错误处理

当权限验证失败时，系统会返回以下错误：

- **401 Unauthorized**: 授权失败，无效的凭证
- **403 Forbidden**: 权限不足，无法执行请求的操作

错误响应示例：

```json
{
  "error": "permission_denied",
  "message": "当前角色无法访问请求的工具",
  "details": {
    "requested_tool": "search_database",
    "required_role": "admin"
  }
}
```

## 最佳实践

1. **使用最小权限原则**：只请求完成任务所需的最小权限
2. **维护会话**：尽可能使用会话ID保持上下文，避免频繁创建新会话
3. **处理错误**：应当优雅处理权限错误，向用户提供明确的反馈
4. **日志和审计**：记录权限变更和访问模式，帮助排查问题

## 完整示例

查看我们的示例代码以获取完整的集成演示：

- [第三方API调用示例](../agent_cores/examples/third_party_api_call.py) 