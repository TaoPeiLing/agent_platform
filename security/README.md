# 安全认证与授权体系

## 🔑 简介

本模块提供了完整的安全认证与授权体系，保护您的AI代理平台免受未授权访问和滥用。即使您不懂技术细节，也能通过本文档了解如何安全地设置和使用这个系统。

## 🏗️ 整体架构

安全系统由以下几个核心部分组成：

1. **身份认证** - 确认"你是谁"
2. **权限控制** - 决定"你能做什么"
3. **资源访问控制** - 管理"你能访问哪些资源"
4. **使用限制** - 控制"你能使用多少资源"
5. **内容安全** - 确保"内容符合规定"

## 📝 核心组件详解

### 1. 身份认证 (Authentication)

身份认证回答的是"你是谁"的问题，我们提供两种主要的认证方式：

#### API密钥认证 (api_key.py)

- **什么是API密钥？** 类似于一把钥匙，持有它就能获得相应的访问权限
- **如何使用：** 在请求中附带API密钥，系统会自动验证
- **适用场景：** 适合服务器间通信、程序化调用

```python
# 示例：使用API密钥访问
result = runtime_service.run_agent(
    input_text="你好", 
    api_key="sk-xxxxxxxxxxxx"
)
```

#### JWT令牌认证 (jwt_auth.py)

- **什么是JWT？** JSON Web Token，一种携带用户身份和权限的加密令牌
- **特点：** 支持过期时间、包含用户信息、支持刷新机制
- **适用场景：** 适合Web应用、移动应用的用户登录

```python
# 示例：使用JWT访问
result = runtime_service.run_agent(
    input_text="你好", 
    jwt_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
)
```

### 2. 权限控制 (Authorization)

权限控制解决的是"你能做什么"的问题：

#### 角色与权限系统

- **角色（Roles）：** 用户的身份类型，如管理员、开发者、普通用户
- **权限（Permissions）：** 具体的操作权限，如读取、写入、执行等
- **权限委托（Delegation）：** 允许临时授权他人执行特定操作

#### 权限管理 (permission_delegator.py)

权限委托器允许在不更改用户基本权限的情况下，临时授权特定操作：

```python
# 示例：检查用户是否有特定权限
if security_service.has_permission(user_id, "agent.execute"):
    # 允许执行代理
```

### 3. 资源访问控制 (resource_acl.py)

资源访问控制列表(ACL)管理"你能访问哪些资源"：

#### 核心概念

- **资源类型：** 如代理(agent)、模型(model)、工具(tool)、数据集(dataset)等
- **访问级别：** 无权限、只读、读写、所有者、管理员
- **继承机制：** 资源访问权限可以从团队或父资源继承

#### 主要功能

- 精确到单个资源的访问控制
- 支持团队共享资源
- 支持资源公开/私有设置
- 支持所有权转移

```python
# 示例：检查用户是否可以访问资源
if acl_manager.check_access(
    user_id="user123",
    resource_type="agent",
    resource_id="agent001",
    required_level=AccessLevel.WRITE
):
    # 允许写入操作
```

### 4. 使用限制

控制API调用频率和资源使用配额：

#### 速率限制 (rate_limiter.py)

- 限制单位时间内的请求次数
- 支持不同级别的限制策略
- 防止API滥用和DoS攻击

```python
# 速率限制示例
if not security_service.check_rate_limit(user_id, "model"):
    return {"error": "请求频率超限，请稍后再试"}
```

#### 资源配额 (quota_manager.py)

- 管理用户可使用的资源总量(如API调用次数、生成的token数等)
- 支持按时间段重置配额
- 支持不同服务级别的配额设置

```python
# 配额检查示例
if not security_service.check_resource_quota(user_id, "model_tokens", tokens_estimate):
    return {"error": "资源配额不足"}
```

#### 服务计划 (service_plans.py)

- 定义不同级别的服务计划(免费版、基础版、高级版等)
- 每个计划包含不同的资源配额和功能权限
- 支持计划升级、降级和定制

### 5. 内容安全 (guardrails.py)

内容安全保障进出系统的内容符合规范：

- **输入过滤：** 检查用户输入是否包含不允许的内容
- **输出过滤：** 确保AI生成的内容符合安全标准
- **敏感信息处理：** 屏蔽或模糊处理敏感数据

```python
# 内容安全检查示例
content_check = security_service.check_content(input_text)
if content_check and not content_check.safe_to_use:
    return {"error": "输入内容包含不允许的敏感信息"}
```

## 🚀 快速开始

### 基本设置

1. **启用安全服务**

```python
from agent_cores.security import security_service

# 在应用启动时初始化
security_service.initialize()
```

2. **创建API密钥**

```python
# 创建一个新的API密钥
api_key = security_service.create_api_key(
    name="测试密钥",
    user_id="user123",
    permissions=["agent.execute", "model.invoke"]
)
```

3. **创建资源ACL**

```python
from agent_cores.security.resource_acl import acl_manager, AccessLevel, ResourceType

# 创建资源ACL并设置访问控制
acl_id = acl_manager.create_acl_entry(
    resource_type=ResourceType.AGENT,
    resource_id="my_agent_001",
    owner_id="user123"
)

# 授予另一个用户访问权限
acl_manager.set_user_access(
    resource_type=ResourceType.AGENT,
    resource_id="my_agent_001",
    user_id="another_user",
    access_level=AccessLevel.READ
)
```

## 📊 典型使用场景

### 场景一：多用户AI平台

适合构建多用户的AI助手平台，每个用户只能访问自己的代理和数据。

### 场景二：企业内部AI平台

适合企业内部使用，通过团队权限管理，让不同部门能够协作使用AI资源。

### 场景三：公开API服务

适合提供API服务给外部开发者，通过API密钥和配额管理控制使用量。

## 🔧 常见问题排查

**问题1：认证失败**
- 检查API密钥或JWT令牌是否有效
- 检查令牌是否过期
- 查看日志中的具体错误信息

**问题2：权限不足**
- 检查用户是否有所需的权限
- 确认资源ACL设置是否正确
- 考虑使用权限委托临时授权

**问题3：配额耗尽**
- 检查用户的服务计划
- 查看用户的资源使用情况
- 考虑升级服务计划或调整配额限制

## 📚 核心类及函数参考

### SecurityService

中心服务，整合所有安全功能：

```python
# 认证
auth_result = security_service.authenticate(api_key="sk-xxxx")

# 权限检查
has_permission = security_service.has_permission(user_id, "agent.execute")

# 速率检查
within_limit = security_service.check_rate_limit(user_id, "api_calls")

# 配额检查
has_quota = security_service.check_resource_quota(user_id, "tokens", 1000)

# 内容安全
content_result = security_service.check_content("用户输入内容")
```

### ACLManager

资源访问控制管理：

```python
# 创建ACL
acl_id = acl_manager.create_acl_entry(resource_type, resource_id, owner_id)

# 设置访问权限
acl_manager.set_user_access(resource_type, resource_id, user_id, access_level)

# 检查访问权限
can_access = acl_manager.check_access(user_id, resource_type, resource_id, required_level)

# 列出用户可访问的资源
resources = acl_manager.list_accessible_resources(user_id, resource_type)
```

## 🔒 安全最佳实践

1. **最小权限原则**：只授予用户完成任务所需的最小权限集
2. **定期轮换密钥**：定期更换API密钥和证书
3. **监控异常行为**：设置监控和告警，及时发现异常访问
4. **数据加密**：敏感数据存储和传输时进行加密
5. **安全审计**：定期审计权限设置和访问日志

## 📝 总结

本安全认证与授权体系提供了全面的保护机制，确保您的AI代理平台安全可靠：

- **身份认证**：确认用户身份
- **权限控制**：管理用户权限
- **资源访问**：控制资源访问级别
- **使用限制**：管理资源使用量
- **内容安全**：保障内容合规

从小型项目到企业级应用，这套系统都能满足不同级别的安全需求，帮助您构建安全可靠的AI代理平台。 