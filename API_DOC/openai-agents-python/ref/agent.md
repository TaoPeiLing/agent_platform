[Skip to content](https://openai.github.io/openai-agents-python/ref/agent/#agents)

# `Agents`

### Agent`dataclass`

Bases: `Generic[TContext]`

An agent is an AI model configured with instructions, tools, guardrails, handoffs and more.

We strongly recommend passing `instructions`, which is the "system prompt" for the agent. In
addition, you can pass `description`, which is a human-readable description of the agent, used
when the agent is used inside tools/handoffs.

Agents are generic on the context type. The context is a (mutable) object you create. It is
passed to tool functions, handoffs, guardrails, etc.

Source code in `src/agents/agent.py`

|     |     |
| --- | --- |
| ```<br> 25<br> 26<br> 27<br> 28<br> 29<br> 30<br> 31<br> 32<br> 33<br> 34<br> 35<br> 36<br> 37<br> 38<br> 39<br> 40<br> 41<br> 42<br> 43<br> 44<br> 45<br> 46<br> 47<br> 48<br> 49<br> 50<br> 51<br> 52<br> 53<br> 54<br> 55<br> 56<br> 57<br> 58<br> 59<br> 60<br> 61<br> 62<br> 63<br> 64<br> 65<br> 66<br> 67<br> 68<br> 69<br> 70<br> 71<br> 72<br> 73<br> 74<br> 75<br> 76<br> 77<br> 78<br> 79<br> 80<br> 81<br> 82<br> 83<br> 84<br> 85<br> 86<br> 87<br> 88<br> 89<br> 90<br> 91<br> 92<br> 93<br> 94<br> 95<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>108<br>109<br>110<br>111<br>112<br>113<br>114<br>115<br>116<br>117<br>118<br>119<br>120<br>121<br>122<br>123<br>124<br>125<br>126<br>127<br>128<br>129<br>130<br>131<br>132<br>133<br>134<br>135<br>136<br>137<br>138<br>139<br>140<br>141<br>142<br>143<br>144<br>145<br>146<br>147<br>148<br>149<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>157<br>158<br>159<br>``` | ````md-code__content<br>@dataclass<br>class Agent(Generic[TContext]):<br>    """An agent is an AI model configured with instructions, tools, guardrails, handoffs and more.<br>    We strongly recommend passing `instructions`, which is the "system prompt" for the agent. In<br>    addition, you can pass `description`, which is a human-readable description of the agent, used<br>    when the agent is used inside tools/handoffs.<br>    Agents are generic on the context type. The context is a (mutable) object you create. It is<br>    passed to tool functions, handoffs, guardrails, etc.<br>    """<br>    name: str<br>    """The name of the agent."""<br>    instructions: (<br>        str<br>        | Callable[<br>            [RunContextWrapper[TContext], Agent[TContext]],<br>            MaybeAwaitable[str],<br>        ]<br>        | None<br>    ) = None<br>    """The instructions for the agent. Will be used as the "system prompt" when this agent is<br>    invoked. Describes what the agent should do, and how it responds.<br>    Can either be a string, or a function that dynamically generates instructions for the agent. If<br>    you provide a function, it will be called with the context and the agent instance. It must<br>    return a string.<br>    """<br>    handoff_description: str | None = None<br>    """A description of the agent. This is used when the agent is used as a handoff, so that an<br>    LLM knows what it does and when to invoke it.<br>    """<br>    handoffs: list[Agent[Any] | Handoff[TContext]] = field(default_factory=list)<br>    """Handoffs are sub-agents that the agent can delegate to. You can provide a list of handoffs,<br>    and the agent can choose to delegate to them if relevant. Allows for separation of concerns and<br>    modularity.<br>    """<br>    model: str | Model | None = None<br>    """The model implementation to use when invoking the LLM.<br>    By default, if not set, the agent will use the default model configured in<br>    `model_settings.DEFAULT_MODEL`.<br>    """<br>    model_settings: ModelSettings = field(default_factory=ModelSettings)<br>    """Configures model-specific tuning parameters (e.g. temperature, top_p).<br>    """<br>    tools: list[Tool] = field(default_factory=list)<br>    """A list of tools that the agent can use."""<br>    input_guardrails: list[InputGuardrail[TContext]] = field(default_factory=list)<br>    """A list of checks that run in parallel to the agent's execution, before generating a<br>    response. Runs only if the agent is the first agent in the chain.<br>    """<br>    output_guardrails: list[OutputGuardrail[TContext]] = field(default_factory=list)<br>    """A list of checks that run on the final output of the agent, after generating a response.<br>    Runs only if the agent produces a final output.<br>    """<br>    output_type: type[Any] | None = None<br>    """The type of the output object. If not provided, the output will be `str`."""<br>    hooks: AgentHooks[TContext] | None = None<br>    """A class that receives callbacks on various lifecycle events for this agent.<br>    """<br>    def clone(self, **kwargs: Any) -> Agent[TContext]:<br>        """Make a copy of the agent, with the given arguments changed. For example, you could do:<br>        ```<br>        new_agent = agent.clone(instructions="New instructions")<br>        ```<br>        """<br>        return dataclasses.replace(self, **kwargs)<br>    def as_tool(<br>        self,<br>        tool_name: str | None,<br>        tool_description: str | None,<br>        custom_output_extractor: Callable[[RunResult], Awaitable[str]] | None = None,<br>    ) -> Tool:<br>        """Transform this agent into a tool, callable by other agents.<br>        This is different from handoffs in two ways:<br>        1. In handoffs, the new agent receives the conversation history. In this tool, the new agent<br>           receives generated input.<br>        2. In handoffs, the new agent takes over the conversation. In this tool, the new agent is<br>           called as a tool, and the conversation is continued by the original agent.<br>        Args:<br>            tool_name: The name of the tool. If not provided, the agent's name will be used.<br>            tool_description: The description of the tool, which should indicate what it does and<br>                when to use it.<br>            custom_output_extractor: A function that extracts the output from the agent. If not<br>                provided, the last message from the agent will be used.<br>        """<br>        @function_tool(<br>            name_override=tool_name or _utils.transform_string_function_style(self.name),<br>            description_override=tool_description or "",<br>        )<br>        async def run_agent(context: RunContextWrapper, input: str) -> str:<br>            from .run import Runner<br>            output = await Runner.run(<br>                starting_agent=self,<br>                input=input,<br>                context=context.context,<br>            )<br>            if custom_output_extractor:<br>                return await custom_output_extractor(output)<br>            return ItemHelpers.text_message_outputs(output.new_items)<br>        return run_agent<br>    async def get_system_prompt(self, run_context: RunContextWrapper[TContext]) -> str | None:<br>        """Get the system prompt for the agent."""<br>        if isinstance(self.instructions, str):<br>            return self.instructions<br>        elif callable(self.instructions):<br>            if inspect.iscoroutinefunction(self.instructions):<br>                return await cast(Awaitable[str], self.instructions(run_context, self))<br>            else:<br>                return cast(str, self.instructions(run_context, self))<br>        elif self.instructions is not None:<br>            logger.error(f"Instructions must be a string or a function, got {self.instructions}")<br>        return None<br>```` |

#### name`instance-attribute`

```md-code__content
name: str

```

The name of the agent.

#### instructions`class-attribute``instance-attribute`

```md-code__content
instructions: (
    str
    | Callable[\
        [RunContextWrapper[TContext], Agent[TContext]],\
        MaybeAwaitable[str],\
    ]
    | None
) = None

```

The instructions for the agent. Will be used as the "system prompt" when this agent is
invoked. Describes what the agent should do, and how it responds.

Can either be a string, or a function that dynamically generates instructions for the agent. If
you provide a function, it will be called with the context and the agent instance. It must
return a string.

#### handoff\_description`class-attribute``instance-attribute`

```md-code__content
handoff_description: str | None = None

```

A description of the agent. This is used when the agent is used as a handoff, so that an
LLM knows what it does and when to invoke it.

#### handoffs`class-attribute``instance-attribute`

```md-code__content
handoffs: list[Agent[Any] | Handoff[TContext]] = field(
    default_factory=list
)

```

Handoffs are sub-agents that the agent can delegate to. You can provide a list of handoffs,
and the agent can choose to delegate to them if relevant. Allows for separation of concerns and
modularity.

#### model`class-attribute``instance-attribute`

```md-code__content
model: str | Model | None = None

```

The model implementation to use when invoking the LLM.

By default, if not set, the agent will use the default model configured in
`model_settings.DEFAULT_MODEL`.

#### model\_settings`class-attribute``instance-attribute`

```md-code__content
model_settings: ModelSettings = field(
    default_factory=ModelSettings
)

```

Configures model-specific tuning parameters (e.g. temperature, top\_p).

#### tools`class-attribute``instance-attribute`

```md-code__content
tools: list[Tool] = field(default_factory=list)

```

A list of tools that the agent can use.

#### input\_guardrails`class-attribute``instance-attribute`

```md-code__content
input_guardrails: list[InputGuardrail[TContext]] = field(
    default_factory=list
)

```

A list of checks that run in parallel to the agent's execution, before generating a
response. Runs only if the agent is the first agent in the chain.

#### output\_guardrails`class-attribute``instance-attribute`

```md-code__content
output_guardrails: list[OutputGuardrail[TContext]] = field(
    default_factory=list
)

```

A list of checks that run on the final output of the agent, after generating a response.
Runs only if the agent produces a final output.

#### output\_type`class-attribute``instance-attribute`

```md-code__content
output_type: type[Any] | None = None

```

The type of the output object. If not provided, the output will be `str`.

#### hooks`class-attribute``instance-attribute`

```md-code__content
hooks: AgentHooks[TContext] | None = None

```

A class that receives callbacks on various lifecycle events for this agent.

#### clone

```md-code__content
clone(**kwargs: Any) -> Agent[TContext]

```

Make a copy of the agent, with the given arguments changed. For example, you could do:

```md-code__content
new_agent = agent.clone(instructions="New instructions")

```

Source code in `src/agents/agent.py`

|     |     |
| --- | --- |
| ```<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>``` | ````md-code__content<br>def clone(self, **kwargs: Any) -> Agent[TContext]:<br>    """Make a copy of the agent, with the given arguments changed. For example, you could do:<br>    ```<br>    new_agent = agent.clone(instructions="New instructions")<br>    ```<br>    """<br>    return dataclasses.replace(self, **kwargs)<br>```` |

#### as\_tool

```md-code__content
as_tool(
    tool_name: str | None,
    tool_description: str | None,
    custom_output_extractor: Callable[\
        [RunResult], Awaitable[str]\
    ]
    | None = None,
) -> Tool

```

Transform this agent into a tool, callable by other agents.

This is different from handoffs in two ways:
1\. In handoffs, the new agent receives the conversation history. In this tool, the new agent
receives generated input.
2\. In handoffs, the new agent takes over the conversation. In this tool, the new agent is
called as a tool, and the conversation is continued by the original agent.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `tool_name` | `str | None` | The name of the tool. If not provided, the agent's name will be used. | _required_ |
| `tool_description` | `str | None` | The description of the tool, which should indicate what it does and<br>when to use it. | _required_ |
| `custom_output_extractor` | `Callable[[RunResult], Awaitable[str]] | None` | A function that extracts the output from the agent. If not<br>provided, the last message from the agent will be used. | `None` |

Source code in `src/agents/agent.py`

|     |     |
| --- | --- |
| ```<br>106<br>107<br>108<br>109<br>110<br>111<br>112<br>113<br>114<br>115<br>116<br>117<br>118<br>119<br>120<br>121<br>122<br>123<br>124<br>125<br>126<br>127<br>128<br>129<br>130<br>131<br>132<br>133<br>134<br>135<br>136<br>137<br>138<br>139<br>140<br>141<br>142<br>143<br>144<br>145<br>``` | ```md-code__content<br>def as_tool(<br>    self,<br>    tool_name: str | None,<br>    tool_description: str | None,<br>    custom_output_extractor: Callable[[RunResult], Awaitable[str]] | None = None,<br>) -> Tool:<br>    """Transform this agent into a tool, callable by other agents.<br>    This is different from handoffs in two ways:<br>    1. In handoffs, the new agent receives the conversation history. In this tool, the new agent<br>       receives generated input.<br>    2. In handoffs, the new agent takes over the conversation. In this tool, the new agent is<br>       called as a tool, and the conversation is continued by the original agent.<br>    Args:<br>        tool_name: The name of the tool. If not provided, the agent's name will be used.<br>        tool_description: The description of the tool, which should indicate what it does and<br>            when to use it.<br>        custom_output_extractor: A function that extracts the output from the agent. If not<br>            provided, the last message from the agent will be used.<br>    """<br>    @function_tool(<br>        name_override=tool_name or _utils.transform_string_function_style(self.name),<br>        description_override=tool_description or "",<br>    )<br>    async def run_agent(context: RunContextWrapper, input: str) -> str:<br>        from .run import Runner<br>        output = await Runner.run(<br>            starting_agent=self,<br>            input=input,<br>            context=context.context,<br>        )<br>        if custom_output_extractor:<br>            return await custom_output_extractor(output)<br>        return ItemHelpers.text_message_outputs(output.new_items)<br>    return run_agent<br>``` |

#### get\_system\_prompt`async`

```md-code__content
get_system_prompt(
    run_context: RunContextWrapper[TContext],
) -> str | None

```

Get the system prompt for the agent.

Source code in `src/agents/agent.py`

|     |     |
| --- | --- |
| ```<br>147<br>148<br>149<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>157<br>158<br>159<br>``` | ```md-code__content<br>async def get_system_prompt(self, run_context: RunContextWrapper[TContext]) -> str | None:<br>    """Get the system prompt for the agent."""<br>    if isinstance(self.instructions, str):<br>        return self.instructions<br>    elif callable(self.instructions):<br>        if inspect.iscoroutinefunction(self.instructions):<br>            return await cast(Awaitable[str], self.instructions(run_context, self))<br>        else:<br>            return cast(str, self.instructions(run_context, self))<br>    elif self.instructions is not None:<br>        logger.error(f"Instructions must be a string or a function, got {self.instructions}")<br>    return None<br>``` |