# 安全与授权模块

本模块为SSS Agent Platform提供全面的安全性和授权功能，包括API密钥管理、JWT认证、基于角色的访问控制(RBAC)以及内容安全保障(Guardrails)。

## 主要功能

- **API密钥管理**: 生成、验证、撤销和轮换API密钥
- **JWT认证**: 生成和验证JWT令牌，支持访问令牌和刷新令牌
- **基于角色的访问控制**: 角色和权限管理，权限检查
- **内容安全保障**: 检测敏感内容，限制请求频率，管理资源配额
- **认证中间件**: 集成到Web框架(FastAPI, Flask)的认证中间件

## 模块结构

```
security/
├── __init__.py         # 模块初始化和服务实例化
├── api_key.py          # API密钥管理
├── jwt_auth.py         # JWT认证
├── models.py           # 数据模型
├── middleware.py       # 认证中间件
├── guardrails.py       # 内容安全保障
├── security_service.py # 综合安全服务
└── utils.py            # 工具函数
```

## 快速入门

### API密钥管理

```python
from agent_cores.security import api_key_manager, security_service

# 创建服务账户
service_account = api_key_manager.create_service_account(
    name="测试账户",
    description="用于测试的服务账户",
    roles=["user"],
    permissions=["api.read", "api.write"]
)

# 创建API密钥
api_key_response = api_key_manager.create_api_key(
    service_account_id=service_account.id,
    description="测试密钥",
    expires_in_days=90
)

# 显示API密钥 (仅在创建时可见)
print(f"API密钥: {api_key_response.full_key}")

# 验证API密钥
auth_result = api_key_manager.verify_api_key(api_key_response.full_key)
if auth_result.success:
    print(f"验证成功: {auth_result.subject_id}")
```

### JWT认证

```python
from agent_cores.security import jwt_auth_service

# 创建JWT令牌对
token_pair = jwt_auth_service.create_token_pair(
    subject="user123",
    roles=["user"],
    permissions=["api.read", "api.write"],
    metadata={"username": "测试用户"}
)

access_token = token_pair["access_token"]
refresh_token = token_pair["refresh_token"]

# 验证令牌
auth_result = jwt_auth_service.verify_token(access_token)
if auth_result.success:
    print(f"验证成功: {auth_result.subject_id}")

# 刷新访问令牌
new_token_dict = jwt_auth_service.refresh_access_token(refresh_token)
new_access_token = new_token_dict["access_token"]
```

### 使用综合安全服务

```python
from agent_cores.security import security_service

# 认证请求 (支持API密钥或JWT令牌)
auth_result = security_service.authenticate(
    api_key="your-api-key",  # 或者使用 jwt_token="your-jwt-token"
)

if auth_result.success:
    print(f"认证成功: {auth_result.subject_id}")
    print(f"角色: {auth_result.roles}")
    print(f"权限: {auth_result.permissions}")
else:
    print(f"认证失败: {auth_result.error}")
```

### 内容安全检查

```python
from agent_cores.security import guardrails_service

# 检查内容是否包含敏感信息
result = guardrails_service.check_content(
    "我的密码是 123456，邮箱是 test@example.com",
    context={"allow_flagged": False}
)

if result.is_flagged:
    print(f"发现敏感内容: {len(result.flags)} 处")
    print(f"过滤后的内容: {result.filtered_content}")
```

### 使用认证中间件 (FastAPI)

```python
from fastapi import FastAPI, Depends
from agent_cores.security.middleware import authenticate_request
from agent_cores.security import security_service

app = FastAPI()

@app.get("/protected-resource")
def protected_resource(auth_result = Depends(authenticate_request)):
    return {"message": f"Hello, {auth_result.subject_id}!"}
```

## 配置

安全模块的配置位于 `configs/security_config.json`，包含以下主要部分：

- `api_key_settings`: API密钥相关设置
- `jwt_settings`: JWT相关设置
- `guardrails`: 内容安全保障相关设置
- `auth_settings`: 认证中间件相关设置
- `rbac_settings`: 角色和权限相关设置

## 注意事项

1. 在生产环境中，务必设置自定义的JWT密钥，可通过环境变量 `JWT_SECRET_KEY` 设置
2. API密钥会存储在 `data/security/keys` 目录下，确保此目录安全
3. 默认情况下，敏感内容会被检测并替换为 `[REDACTED]`

## 高级功能

### 自定义内容检查

```python
from agent_cores.security import guardrails_service
from agent_cores.security.guardrails import ContentCheckResult, ContentFlagResult, ContentFlag

def my_content_checker(content: str) -> ContentCheckResult:
    # 自定义内容检查逻辑
    is_flagged = "敏感词" in content
    flags = []
    
    if is_flagged:
        flags.append(ContentFlagResult(
            flag_type=ContentFlag.UNSAFE,
            confidence=0.9
        ))
    
    return ContentCheckResult(
        is_flagged=is_flagged,
        flags=flags,
        safe_to_use=not is_flagged,
        filtered_content=content.replace("敏感词", "[已过滤]") if is_flagged else content,
        original_content=content
    )

# 注册自定义检查器
guardrails_service.register_content_check_callback("my_checker", my_content_checker)

# 使用自定义检查器
result = guardrails_service.check_content(
    "这里有一些敏感词，需要过滤。",
    context={"check_type": "my_checker"}
)
```

### 频率限制和资源配额

```python
from agent_cores.security import guardrails_service

# 检查频率限制
user_id = "user123"
if guardrails_service.check_rate_limit(user_id, "api"):
    print("请求未超过频率限制")
else:
    print("请求超过频率限制")

# 检查资源配额
if guardrails_service.check_resource_quota(user_id, "model_tokens", 1000):
    # 使用资源配额
    guardrails_service.use_resource_quota(user_id, "model_tokens", 1000)
    print("资源配额充足")
else:
    print("资源配额不足")

# 获取资源使用情况
usage = guardrails_service.get_resource_usage(user_id)
print(f"资源使用情况: {usage}")
``` 