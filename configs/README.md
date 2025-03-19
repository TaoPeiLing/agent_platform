# 智能体配置说明

本目录包含系统中所有智能体的配置信息。

## 文件结构

- `agent_configs.json` - 主要的智能体配置文件，包含所有的智能体配置定义

## 配置类型

配置文件中包含三种主要类型的智能体配置：

1. **分诊智能体配置 (Triage)**
   - 用于创建能够将用户问题分配给专家智能体的分诊智能体
   - 关键字段：
     - `type`: "triage"
     - `description`: 智能体描述
     - `instruction_template`: 指导智能体行为的提示模板

2. **专家智能体配置 (Expert)**
   - 用于创建针对特定领域的专家智能体
   - 关键字段：
     - `type`: "expert"
     - `description`: 专家智能体描述
     - `tool_name_template`: 定义调用专家的工具名称模板
     - `description_template`: 定义专家描述的模板
     - `input_filter_type`: 输入过滤类型，可以是 "summarize"、"user_only" 或 "remove_tools"

3. **独立智能体配置 (Standalone)**
   - 用于创建不需要分诊或协作的独立智能体
   - 可以直接通过Agent构造函数创建，或通过配置文件定义
   - 适用于单一功能、专一领域或通用型助手

## 使用方法

### 1. 分诊和专家智能体

```python
from agent_cores.services.agent_cooperation_service import agent_cooperation_service
from agent_cores.core.template_manager import template_manager
from agent_cores.core.runtime import runtime_service
from agents import Agent

# 从配置文件加载配置
config_path = "path/to/configs/agent_configs.json"
agent_cooperation_service.load_agent_configs_from_json(config_path)

# 创建专家智能体模板
doctor_expert = Agent(
    name="医疗专科医生",
    model="doubao/ep-20250317114344-dlfz2",
    instructions="你是一名专业医生，请根据你的专业知识回答患者的问题。"
)
template_manager.register_template("doctor_expert", doctor_expert)

# 使用配置创建专家智能体
cardiologist = agent_cooperation_service.create_expert_from_config(
    name="cardiology",
    agent_template=doctor_expert,
    config_id="doctor_expert",
    description="心脏科专家，处理心脑血管相关问题"
)

# 创建分诊智能体模板
triage_agent = Agent(
    name="分诊智能体",
    model="doubao/ep-20250317114344-dlfz2",
    instructions="你是一名医疗分诊助手，负责将患者的问题分配给合适的专科医生。"
)
template_manager.register_template("triage_agent", triage_agent)

# 使用配置创建分诊智能体
medical_triage = agent_cooperation_service.create_agent_from_config(
    config="medical_triage",  # 配置ID，对应agent_configs.json中的键
    base_agent=triage_agent,  # 基础智能体模板
    expert_names=["cardiology", "orthopedics", "neurology"]  # 专家名称列表
)
```

### 2. 独立智能体

```python
from agents import Agent
from agent_cores.core.simple_context import SimpleContext
from agent_cores.core.runtime import runtime_service

# 方法一：直接创建独立智能体
standalone_agent = Agent(
    name="通用智能助手",
    model="doubao/ep-20250317114344-dlfz2",
    instructions="""
    你是一个通用智能助手，能够：
    1. 回答用户的各类知识问题
    2. 提供信息和建议
    3. 帮助用户解决日常问题
    4. 进行简单的对话交流
    
    请以友好、专业的方式回应用户，提供准确、有用的信息。
    """
)

# 构建会话上下文
context = SimpleContext(
    user_id="user123",
    user_name="测试用户"
)

# 运行独立智能体
async def run_standalone_agent():
    result = await runtime_service.run_agent(
        agent=standalone_agent,
        input_text="如何提高英语口语水平？",
        session_id="standalone_session",
        context=context
    )
    print(f"智能体回复: {result.get('output', 'No output')}")

# 方法二：使用模板管理器
template_manager.register_template("standalone_agent", standalone_agent)
registered_agent = template_manager.get_template("standalone_agent")
```

## 注意事项

- 所有智能体配置均集中在此目录的`agent_configs.json`文件中
- 创建新智能体类型时，应在此文件中添加相应配置
- 配置文件使用JSON格式，确保格式正确无误
- 根据需求选择适当的智能体类型：
  - 需要多智能体协作完成复杂任务时，使用分诊+专家模式
  - 单一功能场景下，使用独立智能体模式更加高效
- 独立智能体可以直接通过代码创建，不必依赖配置文件
- 所有类型的智能体均可通过`runtime_service.run_agent`执行 