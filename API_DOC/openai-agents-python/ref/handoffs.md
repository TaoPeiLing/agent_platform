[Skip to content](https://openai.github.io/openai-agents-python/ref/handoffs/#handoffs)

# `Handoffs`

### HandoffInputFilter`module-attribute`

```md-code__content
HandoffInputFilter: TypeAlias = Callable[\
    [HandoffInputData], HandoffInputData\
]

```

A function that filters the input data passed to the next agent.

### HandoffInputData`dataclass`

Source code in `src/agents/handoffs.py`

|     |     |
| --- | --- |
| ```<br>29<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>``` | ```md-code__content<br>@dataclass(frozen=True)<br>class HandoffInputData:<br>    input_history: str | tuple[TResponseInputItem, ...]<br>    """<br>    The input history before `Runner.run()` was called.<br>    """<br>    pre_handoff_items: tuple[RunItem, ...]<br>    """<br>    The items generated before the agent turn where the handoff was invoked.<br>    """<br>    new_items: tuple[RunItem, ...]<br>    """<br>    The new items generated during the current agent turn, including the item that triggered the<br>    handoff and the tool output message representing the response from the handoff output.<br>    """<br>``` |

#### input\_history`instance-attribute`

```md-code__content
input_history: str | tuple[TResponseInputItem, ...]

```

The input history before `Runner.run()` was called.

#### pre\_handoff\_items`instance-attribute`

```md-code__content
pre_handoff_items: tuple[RunItem, ...]

```

The items generated before the agent turn where the handoff was invoked.

#### new\_items`instance-attribute`

```md-code__content
new_items: tuple[RunItem, ...]

```

The new items generated during the current agent turn, including the item that triggered the
handoff and the tool output message representing the response from the handoff output.

### Handoff`dataclass`

Bases: `Generic[TContext]`

A handoff is when an agent delegates a task to another agent.
For example, in a customer support scenario you might have a "triage agent" that determines
which agent should handle the user's request, and sub-agents that specialize in different
areas like billing, account management, etc.

Source code in `src/agents/handoffs.py`

|     |     |
| --- | --- |
| ```<br> 52<br> 53<br> 54<br> 55<br> 56<br> 57<br> 58<br> 59<br> 60<br> 61<br> 62<br> 63<br> 64<br> 65<br> 66<br> 67<br> 68<br> 69<br> 70<br> 71<br> 72<br> 73<br> 74<br> 75<br> 76<br> 77<br> 78<br> 79<br> 80<br> 81<br> 82<br> 83<br> 84<br> 85<br> 86<br> 87<br> 88<br> 89<br> 90<br> 91<br> 92<br> 93<br> 94<br> 95<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>108<br>109<br>110<br>111<br>112<br>113<br>114<br>``` | ```md-code__content<br>@dataclass<br>class Handoff(Generic[TContext]):<br>    """A handoff is when an agent delegates a task to another agent.<br>    For example, in a customer support scenario you might have a "triage agent" that determines<br>    which agent should handle the user's request, and sub-agents that specialize in different<br>    areas like billing, account management, etc.<br>    """<br>    tool_name: str<br>    """The name of the tool that represents the handoff."""<br>    tool_description: str<br>    """The description of the tool that represents the handoff."""<br>    input_json_schema: dict[str, Any]<br>    """The JSON schema for the handoff input. Can be empty if the handoff does not take an input.<br>    """<br>    on_invoke_handoff: Callable[[RunContextWrapper[Any], str], Awaitable[Agent[TContext]]]<br>    """The function that invokes the handoff. The parameters passed are:<br>    1. The handoff run context<br>    2. The arguments from the LLM, as a JSON string. Empty string if input_json_schema is empty.<br>    Must return an agent.<br>    """<br>    agent_name: str<br>    """The name of the agent that is being handed off to."""<br>    input_filter: HandoffInputFilter | None = None<br>    """A function that filters the inputs that are passed to the next agent. By default, the new<br>    agent sees the entire conversation history. In some cases, you may want to filter inputs e.g.<br>    to remove older inputs, or remove tools from existing inputs.<br>    The function will receive the entire conversation history so far, including the input item<br>    that triggered the handoff and a tool call output item representing the handoff tool's output.<br>    You are free to modify the input history or new items as you see fit. The next agent that<br>    runs will receive `handoff_input_data.all_items`.<br>    IMPORTANT: in streaming mode, we will not stream anything as a result of this function. The<br>    items generated before will already have been streamed.<br>    """<br>    strict_json_schema: bool = True<br>    """Whether the input JSON schema is in strict mode. We **strongly** recommend setting this to<br>    True, as it increases the likelihood of correct JSON input.<br>    """<br>    def get_transfer_message(self, agent: Agent[Any]) -> str:<br>        base = f"{{'assistant': '{agent.name}'}}"<br>        return base<br>    @classmethod<br>    def default_tool_name(cls, agent: Agent[Any]) -> str:<br>        return _utils.transform_string_function_style(f"transfer_to_{agent.name}")<br>    @classmethod<br>    def default_tool_description(cls, agent: Agent[Any]) -> str:<br>        return (<br>            f"Handoff to the {agent.name} agent to handle the request. "<br>            f"{agent.handoff_description or ''}"<br>        )<br>``` |

#### tool\_name`instance-attribute`

```md-code__content
tool_name: str

```

The name of the tool that represents the handoff.

#### tool\_description`instance-attribute`

```md-code__content
tool_description: str

```

The description of the tool that represents the handoff.

#### input\_json\_schema`instance-attribute`

```md-code__content
input_json_schema: dict[str, Any]

```

The JSON schema for the handoff input. Can be empty if the handoff does not take an input.

#### on\_invoke\_handoff`instance-attribute`

```md-code__content
on_invoke_handoff: Callable[\
    [RunContextWrapper[Any], str],\
    Awaitable[Agent[TContext]],\
]

```

The function that invokes the handoff. The parameters passed are:
1\. The handoff run context
2\. The arguments from the LLM, as a JSON string. Empty string if input\_json\_schema is empty.

Must return an agent.

#### agent\_name`instance-attribute`

```md-code__content
agent_name: str

```

The name of the agent that is being handed off to.

#### input\_filter`class-attribute``instance-attribute`

```md-code__content
input_filter: HandoffInputFilter | None = None

```

A function that filters the inputs that are passed to the next agent. By default, the new
agent sees the entire conversation history. In some cases, you may want to filter inputs e.g.
to remove older inputs, or remove tools from existing inputs.

The function will receive the entire conversation history so far, including the input item
that triggered the handoff and a tool call output item representing the handoff tool's output.

You are free to modify the input history or new items as you see fit. The next agent that
runs will receive `handoff_input_data.all_items`.

IMPORTANT: in streaming mode, we will not stream anything as a result of this function. The
items generated before will already have been streamed.

#### strict\_json\_schema`class-attribute``instance-attribute`

```md-code__content
strict_json_schema: bool = True

```

Whether the input JSON schema is in strict mode. We **strongly** recommend setting this to
True, as it increases the likelihood of correct JSON input.

### handoff

```md-code__content
handoff(
    agent: Agent[TContext],
    *,
    tool_name_override: str | None = None,
    tool_description_override: str | None = None,
    input_filter: Callable[\
        [HandoffInputData], HandoffInputData\
    ]
    | None = None,
) -> Handoff[TContext]

```

```md-code__content
handoff(
    agent: Agent[TContext],
    *,
    on_handoff: OnHandoffWithInput[THandoffInput],
    input_type: type[THandoffInput],
    tool_description_override: str | None = None,
    tool_name_override: str | None = None,
    input_filter: Callable[\
        [HandoffInputData], HandoffInputData\
    ]
    | None = None,
) -> Handoff[TContext]

```

```md-code__content
handoff(
    agent: Agent[TContext],
    *,
    on_handoff: OnHandoffWithoutInput,
    tool_description_override: str | None = None,
    tool_name_override: str | None = None,
    input_filter: Callable[\
        [HandoffInputData], HandoffInputData\
    ]
    | None = None,
) -> Handoff[TContext]

```

```md-code__content
handoff(
    agent: Agent[TContext],
    tool_name_override: str | None = None,
    tool_description_override: str | None = None,
    on_handoff: OnHandoffWithInput[THandoffInput]
    | OnHandoffWithoutInput
    | None = None,
    input_type: type[THandoffInput] | None = None,
    input_filter: Callable[\
        [HandoffInputData], HandoffInputData\
    ]
    | None = None,
) -> Handoff[TContext]

```

Create a handoff from an agent.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `agent` | `Agent[TContext]` | The agent to handoff to, or a function that returns an agent. | _required_ |
| `tool_name_override` | `str | None` | Optional override for the name of the tool that represents the handoff. | `None` |
| `tool_description_override` | `str | None` | Optional override for the description of the tool that<br>represents the handoff. | `None` |
| `on_handoff` | `OnHandoffWithInput[THandoffInput] | OnHandoffWithoutInput | None` | A function that runs when the handoff is invoked. | `None` |
| `input_type` | `type[THandoffInput] | None` | the type of the input to the handoff. If provided, the input will be validated<br>against this type. Only relevant if you pass a function that takes an input. | `None` |
| `input_filter` | `Callable[[HandoffInputData], HandoffInputData] | None` | a function that filters the inputs that are passed to the next agent. | `None` |

Source code in `src/agents/handoffs.py`

|     |     |
| --- | --- |
| ```<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>157<br>158<br>159<br>160<br>161<br>162<br>163<br>164<br>165<br>166<br>167<br>168<br>169<br>170<br>171<br>172<br>173<br>174<br>175<br>176<br>177<br>178<br>179<br>180<br>181<br>182<br>183<br>184<br>185<br>186<br>187<br>188<br>189<br>190<br>191<br>192<br>193<br>194<br>195<br>196<br>197<br>198<br>199<br>200<br>201<br>202<br>203<br>204<br>205<br>206<br>207<br>208<br>209<br>210<br>211<br>212<br>213<br>214<br>215<br>216<br>217<br>218<br>219<br>220<br>221<br>222<br>223<br>224<br>225<br>226<br>227<br>228<br>229<br>230<br>231<br>232<br>233<br>234<br>235<br>236<br>``` | ```md-code__content<br>def handoff(<br>    agent: Agent[TContext],<br>    tool_name_override: str | None = None,<br>    tool_description_override: str | None = None,<br>    on_handoff: OnHandoffWithInput[THandoffInput] | OnHandoffWithoutInput | None = None,<br>    input_type: type[THandoffInput] | None = None,<br>    input_filter: Callable[[HandoffInputData], HandoffInputData] | None = None,<br>) -> Handoff[TContext]:<br>    """Create a handoff from an agent.<br>    Args:<br>        agent: The agent to handoff to, or a function that returns an agent.<br>        tool_name_override: Optional override for the name of the tool that represents the handoff.<br>        tool_description_override: Optional override for the description of the tool that<br>            represents the handoff.<br>        on_handoff: A function that runs when the handoff is invoked.<br>        input_type: the type of the input to the handoff. If provided, the input will be validated<br>            against this type. Only relevant if you pass a function that takes an input.<br>        input_filter: a function that filters the inputs that are passed to the next agent.<br>    """<br>    assert (on_handoff and input_type) or not (on_handoff and input_type), (<br>        "You must provide either both on_input and input_type, or neither"<br>    )<br>    type_adapter: TypeAdapter[Any] | None<br>    if input_type is not None:<br>        assert callable(on_handoff), "on_handoff must be callable"<br>        sig = inspect.signature(on_handoff)<br>        if len(sig.parameters) != 2:<br>            raise UserError("on_handoff must take two arguments: context and input")<br>        type_adapter = TypeAdapter(input_type)<br>        input_json_schema = type_adapter.json_schema()<br>    else:<br>        type_adapter = None<br>        input_json_schema = {}<br>        if on_handoff is not None:<br>            sig = inspect.signature(on_handoff)<br>            if len(sig.parameters) != 1:<br>                raise UserError("on_handoff must take one argument: context")<br>    async def _invoke_handoff(<br>        ctx: RunContextWrapper[Any], input_json: str | None = None<br>    ) -> Agent[Any]:<br>        if input_type is not None and type_adapter is not None:<br>            if input_json is None:<br>                _utils.attach_error_to_current_span(<br>                    SpanError(<br>                        message="Handoff function expected non-null input, but got None",<br>                        data={"details": "input_json is None"},<br>                    )<br>                )<br>                raise ModelBehaviorError("Handoff function expected non-null input, but got None")<br>            validated_input = _utils.validate_json(<br>                json_str=input_json,<br>                type_adapter=type_adapter,<br>                partial=False,<br>            )<br>            input_func = cast(OnHandoffWithInput[THandoffInput], on_handoff)<br>            if inspect.iscoroutinefunction(input_func):<br>                await input_func(ctx, validated_input)<br>            else:<br>                input_func(ctx, validated_input)<br>        elif on_handoff is not None:<br>            no_input_func = cast(OnHandoffWithoutInput, on_handoff)<br>            if inspect.iscoroutinefunction(no_input_func):<br>                await no_input_func(ctx)<br>            else:<br>                no_input_func(ctx)<br>        return agent<br>    tool_name = tool_name_override or Handoff.default_tool_name(agent)<br>    tool_description = tool_description_override or Handoff.default_tool_description(agent)<br>    # Always ensure the input JSON schema is in strict mode<br>    # If there is a need, we can make this configurable in the future<br>    input_json_schema = ensure_strict_json_schema(input_json_schema)<br>    return Handoff(<br>        tool_name=tool_name,<br>        tool_description=tool_description,<br>        input_json_schema=input_json_schema,<br>        on_invoke_handoff=_invoke_handoff,<br>        input_filter=input_filter,<br>        agent_name=agent.name,<br>    )<br>``` |