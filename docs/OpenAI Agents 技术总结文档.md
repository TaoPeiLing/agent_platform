# OpenAI Agents 技术总结文档

## 核心概念与架构

OpenAI Agents SDK是一个轻量级但功能强大的Python库，用于构建基于大型语言模型(LLM)的智能代理应用。它提供了一套简洁的原语，让开发者能够快速构建复杂的AI应用程序。

## 基础组件

### 1.Agent（代理）

    - Agent（代理）
    - 核心类，代表一个由LLM驱动的AI助手
    - 可配置instructions（系统提示）、工具、交接和围栏
    - 支持泛型上下文管理，便于状态传递
    - 可定义输出类型，支持结构化输出

### Tools（工具）

    - 允许Agent与外部系统和资源交互
    - 主要类型：
     -FunctionTool: 包装Python函数
     -FileSearchTool: 向量存储搜索（检索增强）
     -WebSearchTool: 网络搜索
     -ComputerTool: 控制计算机自动化

### Guardrails（围栏）

    - 安全防护机制，并行于Agent执行
    - 两种类型：
     -InputGuardrail: 检查用户输入
     -OutputGuardrail: 检查Agent输出
     -可触发tripwire中断执行流程

### Handoffs（交接）

    - 允许Agent将任务委派给其他Agent
    - 表现为LLM可调用的工具
    -支持自定义输入过滤和回调处理

### Runner（运行器）

    - 执行Agent工作流程的核心类
    - 支持同步和异步执行模式
    - 管理代理循环、工具调用和交接处理

### Context（上下文）

    - 通过RunContextWrapper实现上下文管理
    - 支持任意Python对象作为上下文载体
    - 便于依赖注入和状态共享

## 关键特性

### 函数工具定义

from agents import function_tool

@function_tool
async def fetch_weather(location: str) -> str:
    """获取指定位置的天气
    
    Args:
        location: 需要查询天气的位置
    """
    # 实际实现...
    return "晴天"

特点：
自动提取函数签名生成JSON Schema
自动解析文档字符串获取描述信息
支持同步和异步函数
支持复杂类型（Pydantic模型、TypedDict等）

### Agent定义与配置

from agents import Agent, ModelSettings

agent = Agent(
    name="客服助手",
    instructions="你是一个专业的客服助手，帮助用户解决问题。",
    model="o3-mini",  # 指定使用的模型
    model_settings=ModelSettings(temperature=0.7),  # 模型参数配置
    tools=[fetch_weather],  # 工具列表
    handoffs=[billing_agent, refund_agent],  # 交接列表
    input_guardrails=[offensive_content_check],  # 输入围栏
    output_guardrails=[compliance_check],  # 输出围栏
    output_type=ResponseSchema,  # 输出类型（可选）
)

### 围栏实现

```python
from agents import GuardrailFunctionOutput, input_guardrail

@input_guardrail
async def offensive_content_check(ctx, agent, input_data):
    # 检查输入内容是否包含不适当内容
    contains_offensive = await check_content(input_data)
    
    return GuardrailFunctionOutput(
        output_info={"detected": contains_offensive},
        tripwire_triggered=contains_offensive  # 如果为True，会中断执行
    )
```

### 交接实现

```python
from agents import handoff
from pydantic import BaseModel

class EscalationData(BaseModel):
    reason: str
    urgency: int

async def on_escalation(ctx, input_data: EscalationData):
    # 当交接发生时执行
    await log_escalation(input_data.reason, input_data.urgency)

escalation_agent = Agent(name="升级处理专员", instructions="...")

handoff_obj = handoff(
    agent=escalation_agent,
    on_handoff=on_escalation,
    input_type=EscalationData,
    tool_name_override="escalate_issue"
)

support_agent = Agent(
    name="前线客服",
    instructions="处理常规问题，需要时升级给专员",
    handoffs=[handoff_obj]
)
```

### 执行代理

```python
from agents import Runner

# 异步执行
result = await Runner.run(
    starting_agent=agent,
    input="我想了解今天北京的天气",
    context=user_context  # 可选上下文对象
)

# 同步执行
result = Runner.run_sync(agent, "我想了解今天北京的天气")

# 流式输出
async for event in Runner.stream(agent, "给我写一首诗"):
    if isinstance(event, RunItemStreamEvent):
        print(event.item.item_type, event.item.content)
```

### 上下文管理

```python
from dataclasses import dataclass
from agents import Agent, Runner, RunContextWrapper, function_tool

@dataclass
class UserContext:
    user_id: str
    preferences: dict
    
    async def fetch_history(self):
        # 获取用户历史记录
        return [...]

@function_tool
async def get_user_preferences(ctx: RunContextWrapper[UserContext]) -> str:
    # 通过上下文访问用户信息
    prefs = ctx.context.preferences
    return f"用户偏好: {prefs}"

agent = Agent[UserContext](
    name="个性化助手",
    tools=[get_user_preferences]
)

user_ctx = UserContext(user_id="123", preferences={"theme": "dark"})
result = await Runner.run(agent, "显示我的偏好设置", context=user_ctx)
```

## 高级功能

### 动态指令

```python
def dynamic_instructions(ctx: RunContextWrapper[UserContext], agent: Agent) -> str:
    return f"用户名: {ctx.context.name}。请帮助他们解决问题。"

agent = Agent[UserContext](
    name="动态指令助手",
    instructions=dynamic_instructions
)
```

### 模型配置

```python
from agents import ModelSettings, set_default_openai_key

# 全局设置API密钥
set_default_openai_key("sk-...")

# 模型参数配置
settings = ModelSettings(
    temperature=0.7,
    top_p=0.9,
    max_tokens=1024
)

agent = Agent(
    name="精确助手",
    model="gpt-4o",
    model_settings=settings
)
```

### Agent作为工具

```python
translator_agent = Agent(
    name="翻译助手",
    instructions="你的任务是将文本翻译成指定的语言"
)

main_agent = Agent(
    name="主助手",
    instructions="你是一个多功能助手，可以使用各种工具完成任务",
    tools=[
        translator_agent.as_tool(
            tool_name="translate_text",
            tool_description="将文本翻译成其他语言"
        )
    ]
)
```

## 最佳实践

1. **Agent设计**
   - 每个Agent专注于单一职责
   - 编写清晰具体的指令
   - 合理组织多Agent协作结构

2. **工具开发**
   - 编写详细的文档字符串
   - 使用类型注解以提高工具使用准确性
   - 实现适当的错误处理

3. **围栏配置**
   - 输入围栏用于早期拦截不适当请求
   - 输出围栏用于确保输出符合规范要求
   - 使用快速、轻量级模型执行围栏检查

4. **上下文管理**
   - 使用强类型上下文对象
   - 区分本地上下文和LLM上下文
   - 通过工具暴露按需上下文

5. **错误处理**
   - 捕获并妥善处理各类异常
   - 为用户提供友好的错误信息
   - 使用跟踪功能进行调试

6. **跟踪与监控**
   - 启用跟踪以可视化代理工作流
   - 使用OpenAI跟踪查看器分析执行过程
   - 结合自定义日志增强可观测性

通过以上技术细节和最佳实践，开发者可以使用OpenAI Agents SDK构建高效、可靠的AI代理应用程序，实现各种复杂的自动化和交互场景。

