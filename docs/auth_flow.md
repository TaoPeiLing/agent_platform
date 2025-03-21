# 认证流程说明

## 1. 认证流程概述

SSS Agent Platform 提供了完整的认证和授权体系，支持智能体与外部系统的安全集成。认证流程主要包括以下几个方面：

- **用户身份认证**：验证调用智能体的用户身份
- **角色与权限管理**：基于角色的访问控制(RBAC)
- **外部系统认证集成**：管理与第三方系统的认证信息
- **会话管理**：维护用户会话和认证状态

本文档将详细说明如何实现和使用SSS Agent Platform的认证流程。

## 2. 认证体系架构

认证授权体系包含以下核心组件：

1. **AuthContext**：认证上下文，包含用户身份和外部系统令牌
2. **SessionExtension**：会话扩展，将认证上下文关联到会话
3. **AuthService**：认证服务，管理外部系统认证配置和流程
4. **PermissionService**：权限服务，实现基于角色的访问控制

### 体系架构图

```
┌─────────────────┐     ┌───────────────┐
│  ConnectorAPI   │────▶│ AuthContext   │
└────────┬────────┘     └───────┬───────┘
         │                      │
         ▼                      ▼
┌─────────────────┐     ┌───────────────┐
│ PermissionService│◀───▶│SessionExtension│
└────────┬────────┘     └───────┬───────┘
         │                      │
         ▼                      ▼
┌─────────────────┐     ┌───────────────┐
│ AgentRuntime    │◀───▶│ AuthService   │
└─────────────────┘     └───────────────┘
```

## 3. 用户认证与会话管理

### 3.1 创建会话

连接器API在用户首次请求时创建会话，会话中包含用户标识和角色信息。

```python
# 创建会话
session_id = runtime_service.create_session(
    user_id="user123",
    roles=["user"],
    metadata={"source": "web_app"}
)
```

### 3.2 管理认证上下文

利用`SessionExtension`将认证上下文关联到会话：

```python
# 获取会话
session = runtime_service.get_session(session_id)

# 创建会话扩展
session_extension = SessionExtension.from_session(session)

# 访问认证上下文
auth_context = session_extension.auth_context

# 更新会话中的认证信息
session_extension.update_session(session)
```

## 4. 基于角色的访问控制(RBAC)

### 4.1 角色定义

系统预定义了以下角色：

- `admin`: 管理员，具有所有权限
- `user`: 普通用户
- `guest`: 访客
- `api`: API调用角色
- `tool`: 工具角色

### 4.2 权限检查

使用`PermissionService`检查资源访问权限：

```python
# 检查智能体访问权限
has_permission = permission_service.check_agent_permission(
    roles=["user"], 
    agent_id="financial_advisor",
    operation=Permission.EXECUTE
)

# 检查工作流访问权限
has_permission = permission_service.check_workflow_permission(
    roles=["user"], 
    workflow_id="loan_approval",
    operation=Permission.EXECUTE
)

# 检查工具访问权限
has_permission = permission_service.check_tool_permission(
    roles=["user"], 
    tool_id="web_search"
)

# 检查外部系统访问权限
has_permission = permission_service.check_external_system_permission(
    roles=["user"], 
    system_id="crm_system"
)
```

### 4.3 资源访问策略

资源访问策略定义了哪些角色可以对特定资源执行哪些操作：

```python
# 添加资源访问策略
policy = ResourcePolicy(
    resource_id="financial_advisor",
    resource_type=ResourceType.AGENT,
    allowed_roles=[Role.ADMIN, Role.USER],
    allowed_operations=[Permission.READ, Permission.EXECUTE]
)
permission_service.add_resource_policy(policy)
```

## 5. 外部系统认证集成

### 5.1 外部系统配置

向认证服务注册外部系统配置：

```python
# 注册外部系统配置
config = ExternalSystemConfig(
    system_id="crm_system",
    auth_type="oauth2",
    auth_url="https://crm.example.com/oauth/authorize",
    auth_header_name="Authorization",
    additional_params={
        "service_url": "https://api.crm.example.com"
    }
)
auth_service.register_external_system(config)
```

### 5.2 OAuth2认证流程

实现OAuth2认证流程：

1. 获取认证URL
2. 重定向用户到认证页面
3. 处理认证回调
4. 存储认证令牌

示例代码：

```python
# 获取认证URL
auth_url = auth_service.get_auth_url(
    system_id="crm_system",
    callback_url="https://myapp.com/auth/callback"
)

# 处理认证回调
token, expiry = auth_service.authenticate(
    system_id="crm_system",
    user_id="user123",
    auth_params={
        "code": "auth_code_from_callback",
        "redirect_uri": "https://myapp.com/auth/callback"
    }
)

# 存储认证令牌
session = runtime_service.get_session(session_id)
session_extension = SessionExtension.from_session(session)
session_extension.auth_context.set_token(
    system_id="crm_system",
    token=token,
    expiry=expiry
)
session_extension.update_session(session)
```

### 5.3 API密钥认证

对于使用API密钥的系统：

```python
# 注册API密钥系统
config = ExternalSystemConfig(
    system_id="weather_api",
    auth_type="api_key",
    auth_header_name="X-API-Key"
)
auth_service.register_external_system(config)

# 设置API密钥
session_extension.auth_context.set_token(
    system_id="weather_api",
    token="api_key_value"
)
```

## 6. 在连接器中使用认证

### 6.1 HTTP连接器

HTTP连接器支持通过HTTP头和请求参数传递认证信息：

```python
# HTTP请求示例
response = requests.post(
    "http://localhost:8000/v1/agents/financial_advisor/invoke",
    json={
        "input": "我需要投资建议",
        "user_id": "user123",
        "roles": ["user"],
        "auth_tokens": {
            "crm_system": "your_auth_token"
        }
    },
    headers={
        "Authorization": "Bearer user_token"
    }
)
```

### 6.2 SSE连接器

SSE连接器支持认证状态查询和认证事件：

```javascript
// JavaScript示例：SSE流中处理认证事件
const eventSource = new EventSource(
    '/v1/agents/financial_advisor/stream'
);

eventSource.addEventListener('auth_required', function(event) {
    const data = JSON.parse(event.data);
    // 重定向到认证页面
    window.location.href = data.auth_url;
});

eventSource.addEventListener('auth_status', function(event) {
    const data = JSON.parse(event.data);
    console.log('认证状态:', data.is_valid);
});
```

## 7. 认证流程示例

### 7.1 物业维修资金查询示例

以下是一个完整的智能体认证流程示例，演示用户查询物业维修资金时的认证过程：

1. 用户请求智能体查询物业维修资金
2. 系统检查是否有物业系统的认证令牌
3. 如果没有，返回认证URL
4. 用户完成认证后，系统存储令牌
5. 智能体使用令牌查询物业维修资金信息
6. 返回查询结果给用户

具体实现参见示例代码：`sss_agent_platform/agent_cores/examples/auth_tool_example.py`。

### 7.2 运行示例

运行示例代码：

```bash
python -m sss_agent_platform.agent_cores.examples.auth_tool_example
```

## 8. 安全最佳实践

1. **令牌管理**：定期清理过期令牌
2. **最小权限原则**：为每个角色分配最小所需权限
3. **HTTPS**：在生产环境中使用HTTPS保护API通信
4. **OAuth2安全配置**：正确配置OAuth2参数，如scope和state
5. **日志记录**：记录认证相关的关键事件
6. **令牌存储**：安全存储认证令牌，避免明文存储

## 9. 故障排查

常见问题：

1. **认证失败**：检查系统配置和认证参数
2. **权限被拒绝**：检查用户角色和资源策略
3. **令牌过期**：实现令牌续期机制
4. **跨域问题**：配置CORS以允许跨域认证回调
5. **会话过期**：处理会话超时情况

---

有关详细API参考，请查看代码文档或API文档。 