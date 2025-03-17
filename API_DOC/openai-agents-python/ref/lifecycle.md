[Skip to content](https://openai.github.io/openai-agents-python/ref/lifecycle/#lifecycle)

# `Lifecycle`

### RunHooks

Bases: `Generic[TContext]`

A class that receives callbacks on various lifecycle events in an agent run. Subclass and
override the methods you need.

#### on\_agent\_start`async`

```md-code__content
on_agent_start(
    context: RunContextWrapper[TContext],
    agent: Agent[TContext],
) -> None

```

Called before the agent is invoked. Called each time the current agent changes.

#### on\_agent\_end`async`

```md-code__content
on_agent_end(
    context: RunContextWrapper[TContext],
    agent: Agent[TContext],
    output: Any,
) -> None

```

Called when the agent produces a final output.

#### on\_handoff`async`

```md-code__content
on_handoff(
    context: RunContextWrapper[TContext],
    from_agent: Agent[TContext],
    to_agent: Agent[TContext],
) -> None

```

Called when a handoff occurs.

#### on\_tool\_start`async`

```md-code__content
on_tool_start(
    context: RunContextWrapper[TContext],
    agent: Agent[TContext],
    tool: Tool,
) -> None

```

Called before a tool is invoked.

#### on\_tool\_end`async`

```md-code__content
on_tool_end(
    context: RunContextWrapper[TContext],
    agent: Agent[TContext],
    tool: Tool,
    result: str,
) -> None

```

Called after a tool is invoked.

### AgentHooks

Bases: `Generic[TContext]`

A class that receives callbacks on various lifecycle events for a specific agent. You can
set this on `agent.hooks` to receive events for that specific agent.

Subclass and override the methods you need.

#### on\_start`async`

```md-code__content
on_start(
    context: RunContextWrapper[TContext],
    agent: Agent[TContext],
) -> None

```

Called before the agent is invoked. Called each time the running agent is changed to this
agent.

#### on\_end`async`

```md-code__content
on_end(
    context: RunContextWrapper[TContext],
    agent: Agent[TContext],
    output: Any,
) -> None

```

Called when the agent produces a final output.

#### on\_handoff`async`

```md-code__content
on_handoff(
    context: RunContextWrapper[TContext],
    agent: Agent[TContext],
    source: Agent[TContext],
) -> None

```

Called when the agent is being handed off to. The `source` is the agent that is handing
off to this agent.

#### on\_tool\_start`async`

```md-code__content
on_tool_start(
    context: RunContextWrapper[TContext],
    agent: Agent[TContext],
    tool: Tool,
) -> None

```

Called before a tool is invoked.

#### on\_tool\_end`async`

```md-code__content
on_tool_end(
    context: RunContextWrapper[TContext],
    agent: Agent[TContext],
    tool: Tool,
    result: str,
) -> None

```

Called after a tool is invoked.