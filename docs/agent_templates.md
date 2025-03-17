# 代理模板系统

本文档详细说明SSS Agent Platform中的代理模板系统实现，该系统基于OpenAI Agent SDK的Agent.clone()功能构建。

## 概述

代理模板系统允许您定义标准化的代理配置，并基于这些模板快速创建新的代理实例。这种方式有以下优势：

1. **配置复用** - 避免为每个代理重复定义相同的基础配置
2. **统一标准** - 确保所有代理遵循一致的设计模式
3. **灵活定制** - 在创建实例时可以覆盖特定属性
4. **减少代码重复** - 将通用配置集中管理

## 实现机制

### 1. 配置文件

代理模板使用JSON配置文件定义，存储在`agent_configs/agents/`目录中。每个JSON文件对应一个模板，文件名即为模板名称。

配置文件示例：
```json
{
    "name": "管理员助手",
    "description": "一个具有管理员权限的助手代理",
    "instructions": "你是一个有管理员权限的智能助手...",
    "model": {
        "provider": "openai",
        "name": "gpt-3.5-turbo-0125",
        "temperature": 0.3
    },
    "tools": [
        {"name": "search_weather", "...": "..."},
        {"name": "calculate", "...": "..."}
    ]
}
```

### 2. 模板加载

系统启动时，`agent_templates.py`模块会自动加载所有配置文件并注册模板：

```python
def register_all_templates():
    """注册所有代理模板"""
    # 查找所有JSON文件
    config_dir = os.path.join(project_root, "agent_configs", "agents")
    json_files = glob.glob(os.path.join(config_dir, "*.json"))
    
    # 注册所有模板
    for json_file in json_files:
        register_template_from_json(json_file)
```

### 3. Agent.clone() 机制

代理模板系统的核心是利用OpenAI Agent SDK的`Agent.clone()`方法，该方法允许从现有代理创建新实例，并可以选择性地覆盖某些属性。

这种实现机制在`AgentFactory.create_from_template()`方法中：

```python
def create_from_template(self, template_name: str, **overrides) -> Agent:
    """基于现有模板创建代理实例"""
    if template_name not in self.templates:
        raise ValueError(f"未知代理模板: {template_name}")

    # 使用Agent.clone()方法创建新实例
    template = self.templates[template_name]
    return template.clone(**overrides)
```

## 使用方法

### 1. 从已有模板创建代理

通过运行时服务使用模板运行代理：

```python
result = await runtime_service.run_agent(
    session_id=session_id,
    input_text="你好",
    template_name="admin_agent"  # 使用模板名称
)
```

### 2. 创建定制版本

直接使用代理工厂创建定制的代理实例：

```python
# 导入代理工厂
from agent_cores.core.factory import agent_factory

# 使用模板创建代理，覆盖部分属性
customized_agent = agent_factory.create_from_template(
    "user_agent",
    instructions="这是自定义指令，将覆盖原模板中的指令。",
    model="gpt-4o",  # 使用不同的模型
    tools=[]  # 去掉所有工具
)

# 然后可以直接使用这个代理
result = await runtime_service.run_agent(
    session_id=session_id,
    input_text="你好",
    agent=customized_agent  # 直接提供代理实例
)
```

### 3. 创建新模板

两种方式创建新模板：

#### 方式一：创建JSON配置文件

在`agent_configs/agents/`目录下创建新的JSON文件，例如`my_template.json`：

```json
{
    "name": "我的助手",
    "instructions": "你是一个专门帮助...",
    "model": {
        "name": "gpt-3.5-turbo-0125",
        "temperature": 0.5
    }
}
```

然后重启服务或手动注册：

```python
from agent_cores.examples.agent_templates import register_template_from_json
register_template_from_json("/path/to/my_template.json")
```

#### 方式二：代码中注册

```python
from agent_cores.core.factory import agent_factory

# 注册新模板
agent_factory.register_template_from_config(
    name="my_template",
    instructions="你是一个专门...",
    model_name="gpt-3.5-turbo-0125",
    model_settings={"temperature": 0.5},
    tools=[]
)
```

## 动态覆盖

在创建代理实例时，可以覆盖模板中的任何属性：

```python
# 以下都是可选的覆盖项
agent = agent_factory.create_from_template(
    "assistant_agent",
    name="定制助手",
    instructions="定制指令...",
    model="gpt-4o",
    model_settings={"temperature": 0.9},
    tools=[...],
    handoffs=[...],
    input_guardrails=[...],
    output_guardrails=[...]
)
```

## 最佳实践

1. **保持模板简洁** - 模板应包含必要的配置，但避免过度定制
2. **合理命名** - 使用描述性名称，反映模板的用途
3. **模板分层** - 创建基本、中级和高级模板，允许继承
4. **版本控制** - 在模板元数据中包含版本信息
5. **权限控制** - 在模板中定义所需的角色和权限

## 示例

查看示例脚本以了解完整用法：

```
agent_cores/examples/template_demo.py
```

该脚本演示了如何加载模板、创建代理实例和运行代理。

## 常见问题

1. **如何处理工具加载失败？**
   - 系统会跳过无法加载的工具，并继续处理其他工具

2. **能否在运行时更新模板？**
   - 可以，但不会影响已创建的代理实例

3. **如何共享模板？**
   - 只需共享JSON配置文件即可 