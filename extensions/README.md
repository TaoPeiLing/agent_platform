# Agent扩展 - Handoffs实现方案

## 概述

Handoffs功能允许一个代理将任务委托给另一个代理，适用于多代理协作系统，如客服分诊、专家咨询等场景。本实现基于OpenAI Agent SDK的核心设计理念，提供了更加稳定和可扩展的架构。

## 架构设计

Handoffs实现采用了三层架构设计：

1. **基础类型层**：定义基本数据结构（`handoffs.py`）
2. **适配器层**：确保与SDK的类型兼容性（`agent_adapter.py`）
3. **管理器层**：集中管理Handoff配置和执行（`handoff_manager.py`）

### 核心组件

#### 1. 基础类型（`handoffs.py`）

提供基础数据类型定义，包括：
- `HandoffInputData`：Handoff输入数据结构
- `HandoffInputFilter`：输入过滤器类型

这些类型直接使用OpenAI Agent SDK的设计，确保兼容性。

#### 2. OpenAI Agent适配器（`agent_adapter.py`）

确保与SDK的无缝集成，主要功能：
- 创建带有Handoffs功能的代理
- 日志记录和调试支持
- 修复序列化问题

```python
# 创建带有Handoffs的代理
agent = OpenAIAgentAdapter.create_agent_with_handoffs(base_agent, handoffs)

# 诊断Handoffs设置
OpenAIAgentAdapter.log_agent_handoffs(agent, "前缀")

# 修复可能的序列化问题
fixed_agent = OpenAIAgentAdapter.fix_handoff_objects(agent)
```

#### 3. Handoff管理器（`handoff_manager.py`）

集中管理所有Handoff配置和执行，提供：
- 注册和管理Handoff配置
- 应用Handoff到代理
- 处理Handoff执行结果

```python
# 注册Handoff配置
handoff_manager.register_handoff(
    name="travel",
    agent=travel_agent,
    callback=on_travel_handoff,
    input_type=HandoffReason
)

# 应用Handoff到代理
enhanced_agent = handoff_manager.apply_handoffs_to_agent(
    agent, ["travel", "finance"]
)

# 处理执行结果
result = await handoff_manager.process_handoff_result(
    result=result,
    context=context,
    session_id=session_id
)
```

### 集成到运行时

在`runtime_service.run_agent`方法中，我们添加了对Handoff对象的预处理：

```python
# 使用OpenAIAgentAdapter预处理agent
agent = OpenAIAgentAdapter.pre_run_hook(agent, prepared_context)
```

这确保了在执行过程中Handoff对象的类型一致性。

## 使用指南

### 1. 定义转交原因模型

```python
class HandoffReason(BaseModel):
    """转交原因数据模型"""
    reason: str
    details: Optional[str] = None
```

### 2. 注册Handoff配置

```python
handoff_manager.register_handoff(
    name="finance",
    agent=finance_agent,
    callback=on_finance_handoff,
    input_type=HandoffReason,
    tool_name="transfer_to_finance_expert",
    tool_description="将金融、投资、理财相关问题转交给金融专家处理",
    input_filter=remove_all_tools
)
```

### 3. 应用Handoff到代理

```python
enhanced_agent = handoff_manager.apply_handoffs_to_agent(
    triage_agent, ["finance", "travel"]
)
```

### 4. 使用增强提示词

```python
enhanced_instructions = prompt_with_handoff_instructions(
    agent.instructions,
    custom_handoff_instructions="..."
)

final_agent = enhanced_agent.clone(
    instructions=enhanced_instructions
)
```

### 5. 执行代理并处理结果

```python
result = await runtime_service.run_agent(
    agent=enhanced_agent,
    input_text=user_message,
    session_id=session_id,
    context=context
)

# 处理可能的Handoff结果
expert_result = await handoff_manager.process_handoff_result(
    result=result,
    context=context,
    session_id=session_id
)
```

## 优势

1. **类型安全**：确保Handoff对象在整个生命周期中保持类型一致性
2. **集中管理**：通过HandoffManager集中管理所有Handoff配置和执行
3. **运行时修复**：自动检测并修复序列化问题
4. **可扩展性**：易于添加新的Handoff类型和处理逻辑
5. **与SDK兼容**：完全兼容OpenAI Agent SDK的设计理念

## 示例

完整示例请参考 `agent_cores/examples/handoff_example.py`。 