[Skip to content](https://openai.github.io/openai-agents-python/ref/stream_events/#streaming-events)

# `Streaming events`

### StreamEvent`module-attribute`

```md-code__content
StreamEvent: TypeAlias = Union[\
    RawResponsesStreamEvent,\
    RunItemStreamEvent,\
    AgentUpdatedStreamEvent,\
]

```

A streaming event from an agent.

### RawResponsesStreamEvent`dataclass`

Streaming event from the LLM. These are 'raw' events, i.e. they are directly passed through
from the LLM.

Source code in `src/agents/stream_events.py`

|     |     |
| --- | --- |
| ```<br>12<br>13<br>14<br>15<br>16<br>17<br>18<br>19<br>20<br>21<br>22<br>``` | ```md-code__content<br>@dataclass<br>class RawResponsesStreamEvent:<br>    """Streaming event from the LLM. These are 'raw' events, i.e. they are directly passed through<br>    from the LLM.<br>    """<br>    data: TResponseStreamEvent<br>    """The raw responses streaming event from the LLM."""<br>    type: Literal["raw_response_event"] = "raw_response_event"<br>    """The type of the event."""<br>``` |

#### data`instance-attribute`

```md-code__content
data: TResponseStreamEvent

```

The raw responses streaming event from the LLM.

#### type`class-attribute``instance-attribute`

```md-code__content
type: Literal['raw_response_event'] = 'raw_response_event'

```

The type of the event.

### RunItemStreamEvent`dataclass`

Streaming events that wrap a `RunItem`. As the agent processes the LLM response, it will
generate these events for new messages, tool calls, tool outputs, handoffs, etc.

Source code in `src/agents/stream_events.py`

|     |     |
| --- | --- |
| ```<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>``` | ```md-code__content<br>@dataclass<br>class RunItemStreamEvent:<br>    """Streaming events that wrap a `RunItem`. As the agent processes the LLM response, it will<br>    generate these events for new messages, tool calls, tool outputs, handoffs, etc.<br>    """<br>    name: Literal[<br>        "message_output_created",<br>        "handoff_requested",<br>        "handoff_occured",<br>        "tool_called",<br>        "tool_output",<br>        "reasoning_item_created",<br>    ]<br>    """The name of the event."""<br>    item: RunItem<br>    """The item that was created."""<br>    type: Literal["run_item_stream_event"] = "run_item_stream_event"<br>``` |

#### name`instance-attribute`

```md-code__content
name: Literal[\
    "message_output_created",\
    "handoff_requested",\
    "handoff_occured",\
    "tool_called",\
    "tool_output",\
    "reasoning_item_created",\
]

```

The name of the event.

#### item`instance-attribute`

```md-code__content
item: RunItem

```

The item that was created.

### AgentUpdatedStreamEvent`dataclass`

Event that notifies that there is a new agent running.

Source code in `src/agents/stream_events.py`

|     |     |
| --- | --- |
| ```<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>``` | ```md-code__content<br>@dataclass<br>class AgentUpdatedStreamEvent:<br>    """Event that notifies that there is a new agent running."""<br>    new_agent: Agent[Any]<br>    """The new agent."""<br>    type: Literal["agent_updated_stream_event"] = "agent_updated_stream_event"<br>``` |

#### new\_agent`instance-attribute`

```md-code__content
new_agent: Agent[Any]

```

The new agent.