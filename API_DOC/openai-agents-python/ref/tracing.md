[Skip to content](https://openai.github.io/openai-agents-python/ref/tracing/#tracing-module)

# Tracing module

### TracingProcessor

Bases: `ABC`

Interface for processing spans.

Source code in `src/agents/tracing/processor_interface.py`

|     |     |
| --- | --- |
| ```<br> 9<br>10<br>11<br>12<br>13<br>14<br>15<br>16<br>17<br>18<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>``` | ```md-code__content<br>class TracingProcessor(abc.ABC):<br>    """Interface for processing spans."""<br>    @abc.abstractmethod<br>    def on_trace_start(self, trace: "Trace") -> None:<br>        """Called when a trace is started.<br>        Args:<br>            trace: The trace that started.<br>        """<br>        pass<br>    @abc.abstractmethod<br>    def on_trace_end(self, trace: "Trace") -> None:<br>        """Called when a trace is finished.<br>        Args:<br>            trace: The trace that started.<br>        """<br>        pass<br>    @abc.abstractmethod<br>    def on_span_start(self, span: "Span[Any]") -> None:<br>        """Called when a span is started.<br>        Args:<br>            span: The span that started.<br>        """<br>        pass<br>    @abc.abstractmethod<br>    def on_span_end(self, span: "Span[Any]") -> None:<br>        """Called when a span is finished. Should not block or raise exceptions.<br>        Args:<br>            span: The span that finished.<br>        """<br>        pass<br>    @abc.abstractmethod<br>    def shutdown(self) -> None:<br>        """Called when the application stops."""<br>        pass<br>    @abc.abstractmethod<br>    def force_flush(self) -> None:<br>        """Forces an immediate flush of all queued spans/traces."""<br>        pass<br>``` |

#### on\_trace\_start`abstractmethod`

```md-code__content
on_trace_start(trace: Trace) -> None

```

Called when a trace is started.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `trace` | `Trace` | The trace that started. | _required_ |

Source code in `src/agents/tracing/processor_interface.py`

|     |     |
| --- | --- |
| ```<br>12<br>13<br>14<br>15<br>16<br>17<br>18<br>19<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def on_trace_start(self, trace: "Trace") -> None:<br>    """Called when a trace is started.<br>    Args:<br>        trace: The trace that started.<br>    """<br>    pass<br>``` |

#### on\_trace\_end`abstractmethod`

```md-code__content
on_trace_end(trace: Trace) -> None

```

Called when a trace is finished.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `trace` | `Trace` | The trace that started. | _required_ |

Source code in `src/agents/tracing/processor_interface.py`

|     |     |
| --- | --- |
| ```<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def on_trace_end(self, trace: "Trace") -> None:<br>    """Called when a trace is finished.<br>    Args:<br>        trace: The trace that started.<br>    """<br>    pass<br>``` |

#### on\_span\_start`abstractmethod`

```md-code__content
on_span_start(span: Span[Any]) -> None

```

Called when a span is started.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `span` | `Span[Any]` | The span that started. | _required_ |

Source code in `src/agents/tracing/processor_interface.py`

|     |     |
| --- | --- |
| ```<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def on_span_start(self, span: "Span[Any]") -> None:<br>    """Called when a span is started.<br>    Args:<br>        span: The span that started.<br>    """<br>    pass<br>``` |

#### on\_span\_end`abstractmethod`

```md-code__content
on_span_end(span: Span[Any]) -> None

```

Called when a span is finished. Should not block or raise exceptions.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `span` | `Span[Any]` | The span that finished. | _required_ |

Source code in `src/agents/tracing/processor_interface.py`

|     |     |
| --- | --- |
| ```<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def on_span_end(self, span: "Span[Any]") -> None:<br>    """Called when a span is finished. Should not block or raise exceptions.<br>    Args:<br>        span: The span that finished.<br>    """<br>    pass<br>``` |

#### shutdown`abstractmethod`

```md-code__content
shutdown() -> None

```

Called when the application stops.

Source code in `src/agents/tracing/processor_interface.py`

|     |     |
| --- | --- |
| ```<br>48<br>49<br>50<br>51<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def shutdown(self) -> None:<br>    """Called when the application stops."""<br>    pass<br>``` |

#### force\_flush`abstractmethod`

```md-code__content
force_flush() -> None

```

Forces an immediate flush of all queued spans/traces.

Source code in `src/agents/tracing/processor_interface.py`

|     |     |
| --- | --- |
| ```<br>53<br>54<br>55<br>56<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def force_flush(self) -> None:<br>    """Forces an immediate flush of all queued spans/traces."""<br>    pass<br>``` |

### Span

Bases: `ABC`, `Generic[TSpanData]`

Source code in `src/agents/tracing/spans.py`

|     |     |
| --- | --- |
| ```<br>23<br>24<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>69<br>70<br>71<br>72<br>73<br>74<br>75<br>76<br>77<br>78<br>79<br>80<br>81<br>82<br>83<br>84<br>85<br>86<br>87<br>88<br>89<br>90<br>91<br>92<br>93<br>``` | ```md-code__content<br>class Span(abc.ABC, Generic[TSpanData]):<br>    @property<br>    @abc.abstractmethod<br>    def trace_id(self) -> str:<br>        pass<br>    @property<br>    @abc.abstractmethod<br>    def span_id(self) -> str:<br>        pass<br>    @property<br>    @abc.abstractmethod<br>    def span_data(self) -> TSpanData:<br>        pass<br>    @abc.abstractmethod<br>    def start(self, mark_as_current: bool = False):<br>        """<br>        Start the span.<br>        Args:<br>            mark_as_current: If true, the span will be marked as the current span.<br>        """<br>        pass<br>    @abc.abstractmethod<br>    def finish(self, reset_current: bool = False) -> None:<br>        """<br>        Finish the span.<br>        Args:<br>            reset_current: If true, the span will be reset as the current span.<br>        """<br>        pass<br>    @abc.abstractmethod<br>    def __enter__(self) -> Span[TSpanData]:<br>        pass<br>    @abc.abstractmethod<br>    def __exit__(self, exc_type, exc_val, exc_tb):<br>        pass<br>    @property<br>    @abc.abstractmethod<br>    def parent_id(self) -> str | None:<br>        pass<br>    @abc.abstractmethod<br>    def set_error(self, error: SpanError) -> None:<br>        pass<br>    @property<br>    @abc.abstractmethod<br>    def error(self) -> SpanError | None:<br>        pass<br>    @abc.abstractmethod<br>    def export(self) -> dict[str, Any] | None:<br>        pass<br>    @property<br>    @abc.abstractmethod<br>    def started_at(self) -> str | None:<br>        pass<br>    @property<br>    @abc.abstractmethod<br>    def ended_at(self) -> str | None:<br>        pass<br>``` |

#### start`abstractmethod`

```md-code__content
start(mark_as_current: bool = False)

```

Start the span.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `mark_as_current` | `bool` | If true, the span will be marked as the current span. | `False` |

Source code in `src/agents/tracing/spans.py`

|     |     |
| --- | --- |
| ```<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def start(self, mark_as_current: bool = False):<br>    """<br>    Start the span.<br>    Args:<br>        mark_as_current: If true, the span will be marked as the current span.<br>    """<br>    pass<br>``` |

#### finish`abstractmethod`

```md-code__content
finish(reset_current: bool = False) -> None

```

Finish the span.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `reset_current` | `bool` | If true, the span will be reset as the current span. | `False` |

Source code in `src/agents/tracing/spans.py`

|     |     |
| --- | --- |
| ```<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def finish(self, reset_current: bool = False) -> None:<br>    """<br>    Finish the span.<br>    Args:<br>        reset_current: If true, the span will be reset as the current span.<br>    """<br>    pass<br>``` |

### Trace

A trace is the root level object that tracing creates. It represents a logical "workflow".

Source code in `src/agents/tracing/traces.py`

|     |     |
| --- | --- |
| ```<br>13<br>14<br>15<br>16<br>17<br>18<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>``` | ```md-code__content<br>class Trace:<br>    """<br>    A trace is the root level object that tracing creates. It represents a logical "workflow".<br>    """<br>    @abc.abstractmethod<br>    def __enter__(self) -> Trace:<br>        pass<br>    @abc.abstractmethod<br>    def __exit__(self, exc_type, exc_val, exc_tb):<br>        pass<br>    @abc.abstractmethod<br>    def start(self, mark_as_current: bool = False):<br>        """<br>        Start the trace.<br>        Args:<br>            mark_as_current: If true, the trace will be marked as the current trace.<br>        """<br>        pass<br>    @abc.abstractmethod<br>    def finish(self, reset_current: bool = False):<br>        """<br>        Finish the trace.<br>        Args:<br>            reset_current: If true, the trace will be reset as the current trace.<br>        """<br>        pass<br>    @property<br>    @abc.abstractmethod<br>    def trace_id(self) -> str:<br>        """<br>        The trace ID.<br>        """<br>        pass<br>    @property<br>    @abc.abstractmethod<br>    def name(self) -> str:<br>        """<br>        The name of the workflow being traced.<br>        """<br>        pass<br>    @abc.abstractmethod<br>    def export(self) -> dict[str, Any] | None:<br>        """<br>        Export the trace as a dictionary.<br>        """<br>        pass<br>``` |

#### trace\_id`abstractmethod``property`

```md-code__content
trace_id: str

```

The trace ID.

#### name`abstractmethod``property`

```md-code__content
name: str

```

The name of the workflow being traced.

#### start`abstractmethod`

```md-code__content
start(mark_as_current: bool = False)

```

Start the trace.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `mark_as_current` | `bool` | If true, the trace will be marked as the current trace. | `False` |

Source code in `src/agents/tracing/traces.py`

|     |     |
| --- | --- |
| ```<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>33<br>34<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def start(self, mark_as_current: bool = False):<br>    """<br>    Start the trace.<br>    Args:<br>        mark_as_current: If true, the trace will be marked as the current trace.<br>    """<br>    pass<br>``` |

#### finish`abstractmethod`

```md-code__content
finish(reset_current: bool = False)

```

Finish the trace.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `reset_current` | `bool` | If true, the trace will be reset as the current trace. | `False` |

Source code in `src/agents/tracing/traces.py`

|     |     |
| --- | --- |
| ```<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def finish(self, reset_current: bool = False):<br>    """<br>    Finish the trace.<br>    Args:<br>        reset_current: If true, the trace will be reset as the current trace.<br>    """<br>    pass<br>``` |

#### export`abstractmethod`

```md-code__content
export() -> dict[str, Any] | None

```

Export the trace as a dictionary.

Source code in `src/agents/tracing/traces.py`

|     |     |
| --- | --- |
| ```<br>62<br>63<br>64<br>65<br>66<br>67<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def export(self) -> dict[str, Any] | None:<br>    """<br>    Export the trace as a dictionary.<br>    """<br>    pass<br>``` |

### agent\_span

```md-code__content
agent_span(
    name: str,
    handoffs: list[str] | None = None,
    tools: list[str] | None = None,
    output_type: str | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[AgentSpanData]

```

Create a new agent span. The span will not be started automatically, you should either do
`with agent_span() ...` or call `span.start()` \+ `span.finish()` manually.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `name` | `str` | The name of the agent. | _required_ |
| `handoffs` | `list[str] | None` | Optional list of agent names to which this agent could hand off control. | `None` |
| `tools` | `list[str] | None` | Optional list of tool names available to this agent. | `None` |
| `output_type` | `str | None` | Optional name of the output type produced by the agent. | `None` |
| `span_id` | `str | None` | The ID of the span. Optional. If not provided, we will generate an ID. We<br>recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>correctly formatted. | `None` |
| `parent` | `Trace | Span[Any] | None` | The parent span or trace. If not provided, we will automatically use the current<br>trace/span as the parent. | `None` |
| `disabled` | `bool` | If True, we will return a Span but the Span will not be recorded. | `False` |

Returns:

| Type | Description |
| --- | --- |
| `Span[AgentSpanData]` | The newly created agent span. |

Source code in `src/agents/tracing/create.py`

|     |     |
| --- | --- |
| ```<br> 80<br> 81<br> 82<br> 83<br> 84<br> 85<br> 86<br> 87<br> 88<br> 89<br> 90<br> 91<br> 92<br> 93<br> 94<br> 95<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>108<br>109<br>110<br>111<br>112<br>``` | ```md-code__content<br>def agent_span(<br>    name: str,<br>    handoffs: list[str] | None = None,<br>    tools: list[str] | None = None,<br>    output_type: str | None = None,<br>    span_id: str | None = None,<br>    parent: Trace | Span[Any] | None = None,<br>    disabled: bool = False,<br>) -> Span[AgentSpanData]:<br>    """Create a new agent span. The span will not be started automatically, you should either do<br>    `with agent_span() ...` or call `span.start()` + `span.finish()` manually.<br>    Args:<br>        name: The name of the agent.<br>        handoffs: Optional list of agent names to which this agent could hand off control.<br>        tools: Optional list of tool names available to this agent.<br>        output_type: Optional name of the output type produced by the agent.<br>        span_id: The ID of the span. Optional. If not provided, we will generate an ID. We<br>            recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>            correctly formatted.<br>        parent: The parent span or trace. If not provided, we will automatically use the current<br>            trace/span as the parent.<br>        disabled: If True, we will return a Span but the Span will not be recorded.<br>    Returns:<br>        The newly created agent span.<br>    """<br>    return GLOBAL_TRACE_PROVIDER.create_span(<br>        span_data=AgentSpanData(name=name, handoffs=handoffs, tools=tools, output_type=output_type),<br>        span_id=span_id,<br>        parent=parent,<br>        disabled=disabled,<br>    )<br>``` |

### custom\_span

```md-code__content
custom_span(
    name: str,
    data: dict[str, Any] | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[CustomSpanData]

```

Create a new custom span, to which you can add your own metadata. The span will not be
started automatically, you should either do `with custom_span() ...` or call
`span.start()` \+ `span.finish()` manually.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `name` | `str` | The name of the custom span. | _required_ |
| `data` | `dict[str, Any] | None` | Arbitrary structured data to associate with the span. | `None` |
| `span_id` | `str | None` | The ID of the span. Optional. If not provided, we will generate an ID. We<br>recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>correctly formatted. | `None` |
| `parent` | `Trace | Span[Any] | None` | The parent span or trace. If not provided, we will automatically use the current<br>trace/span as the parent. | `None` |
| `disabled` | `bool` | If True, we will return a Span but the Span will not be recorded. | `False` |

Returns:

| Type | Description |
| --- | --- |
| `Span[CustomSpanData]` | The newly created custom span. |

Source code in `src/agents/tracing/create.py`

|     |     |
| --- | --- |
| ```<br>249<br>250<br>251<br>252<br>253<br>254<br>255<br>256<br>257<br>258<br>259<br>260<br>261<br>262<br>263<br>264<br>265<br>266<br>267<br>268<br>269<br>270<br>271<br>272<br>273<br>274<br>275<br>276<br>277<br>278<br>``` | ```md-code__content<br>def custom_span(<br>    name: str,<br>    data: dict[str, Any] | None = None,<br>    span_id: str | None = None,<br>    parent: Trace | Span[Any] | None = None,<br>    disabled: bool = False,<br>) -> Span[CustomSpanData]:<br>    """Create a new custom span, to which you can add your own metadata. The span will not be<br>    started automatically, you should either do `with custom_span() ...` or call<br>    `span.start()` + `span.finish()` manually.<br>    Args:<br>        name: The name of the custom span.<br>        data: Arbitrary structured data to associate with the span.<br>        span_id: The ID of the span. Optional. If not provided, we will generate an ID. We<br>            recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>            correctly formatted.<br>        parent: The parent span or trace. If not provided, we will automatically use the current<br>            trace/span as the parent.<br>        disabled: If True, we will return a Span but the Span will not be recorded.<br>    Returns:<br>        The newly created custom span.<br>    """<br>    return GLOBAL_TRACE_PROVIDER.create_span(<br>        span_data=CustomSpanData(name=name, data=data or {}),<br>        span_id=span_id,<br>        parent=parent,<br>        disabled=disabled,<br>    )<br>``` |

### function\_span

```md-code__content
function_span(
    name: str,
    input: str | None = None,
    output: str | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[FunctionSpanData]

```

Create a new function span. The span will not be started automatically, you should either do
`with function_span() ...` or call `span.start()` \+ `span.finish()` manually.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `name` | `str` | The name of the function. | _required_ |
| `input` | `str | None` | The input to the function. | `None` |
| `output` | `str | None` | The output of the function. | `None` |
| `span_id` | `str | None` | The ID of the span. Optional. If not provided, we will generate an ID. We<br>recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>correctly formatted. | `None` |
| `parent` | `Trace | Span[Any] | None` | The parent span or trace. If not provided, we will automatically use the current<br>trace/span as the parent. | `None` |
| `disabled` | `bool` | If True, we will return a Span but the Span will not be recorded. | `False` |

Returns:

| Type | Description |
| --- | --- |
| `Span[FunctionSpanData]` | The newly created function span. |

Source code in `src/agents/tracing/create.py`

|     |     |
| --- | --- |
| ```<br>115<br>116<br>117<br>118<br>119<br>120<br>121<br>122<br>123<br>124<br>125<br>126<br>127<br>128<br>129<br>130<br>131<br>132<br>133<br>134<br>135<br>136<br>137<br>138<br>139<br>140<br>141<br>142<br>143<br>144<br>145<br>``` | ```md-code__content<br>def function_span(<br>    name: str,<br>    input: str | None = None,<br>    output: str | None = None,<br>    span_id: str | None = None,<br>    parent: Trace | Span[Any] | None = None,<br>    disabled: bool = False,<br>) -> Span[FunctionSpanData]:<br>    """Create a new function span. The span will not be started automatically, you should either do<br>    `with function_span() ...` or call `span.start()` + `span.finish()` manually.<br>    Args:<br>        name: The name of the function.<br>        input: The input to the function.<br>        output: The output of the function.<br>        span_id: The ID of the span. Optional. If not provided, we will generate an ID. We<br>            recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>            correctly formatted.<br>        parent: The parent span or trace. If not provided, we will automatically use the current<br>            trace/span as the parent.<br>        disabled: If True, we will return a Span but the Span will not be recorded.<br>    Returns:<br>        The newly created function span.<br>    """<br>    return GLOBAL_TRACE_PROVIDER.create_span(<br>        span_data=FunctionSpanData(name=name, input=input, output=output),<br>        span_id=span_id,<br>        parent=parent,<br>        disabled=disabled,<br>    )<br>``` |

### generation\_span

```md-code__content
generation_span(
    input: Sequence[Mapping[str, Any]] | None = None,
    output: Sequence[Mapping[str, Any]] | None = None,
    model: str | None = None,
    model_config: Mapping[str, Any] | None = None,
    usage: dict[str, Any] | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[GenerationSpanData]

```

Create a new generation span. The span will not be started automatically, you should either
do `with generation_span() ...` or call `span.start()` \+ `span.finish()` manually.

This span captures the details of a model generation, including the
input message sequence, any generated outputs, the model name and
configuration, and usage data. If you only need to capture a model
response identifier, use `response_span()` instead.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `input` | `Sequence[Mapping[str, Any]] | None` | The sequence of input messages sent to the model. | `None` |
| `output` | `Sequence[Mapping[str, Any]] | None` | The sequence of output messages received from the model. | `None` |
| `model` | `str | None` | The model identifier used for the generation. | `None` |
| `model_config` | `Mapping[str, Any] | None` | The model configuration (hyperparameters) used. | `None` |
| `usage` | `dict[str, Any] | None` | A dictionary of usage information (input tokens, output tokens, etc.). | `None` |
| `span_id` | `str | None` | The ID of the span. Optional. If not provided, we will generate an ID. We<br>recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>correctly formatted. | `None` |
| `parent` | `Trace | Span[Any] | None` | The parent span or trace. If not provided, we will automatically use the current<br>trace/span as the parent. | `None` |
| `disabled` | `bool` | If True, we will return a Span but the Span will not be recorded. | `False` |

Returns:

| Type | Description |
| --- | --- |
| `Span[GenerationSpanData]` | The newly created generation span. |

Source code in `src/agents/tracing/create.py`

|     |     |
| --- | --- |
| ```<br>148<br>149<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>157<br>158<br>159<br>160<br>161<br>162<br>163<br>164<br>165<br>166<br>167<br>168<br>169<br>170<br>171<br>172<br>173<br>174<br>175<br>176<br>177<br>178<br>179<br>180<br>181<br>182<br>183<br>184<br>185<br>186<br>187<br>188<br>189<br>``` | ```md-code__content<br>def generation_span(<br>    input: Sequence[Mapping[str, Any]] | None = None,<br>    output: Sequence[Mapping[str, Any]] | None = None,<br>    model: str | None = None,<br>    model_config: Mapping[str, Any] | None = None,<br>    usage: dict[str, Any] | None = None,<br>    span_id: str | None = None,<br>    parent: Trace | Span[Any] | None = None,<br>    disabled: bool = False,<br>) -> Span[GenerationSpanData]:<br>    """Create a new generation span. The span will not be started automatically, you should either<br>    do `with generation_span() ...` or call `span.start()` + `span.finish()` manually.<br>    This span captures the details of a model generation, including the<br>    input message sequence, any generated outputs, the model name and<br>    configuration, and usage data. If you only need to capture a model<br>    response identifier, use `response_span()` instead.<br>    Args:<br>        input: The sequence of input messages sent to the model.<br>        output: The sequence of output messages received from the model.<br>        model: The model identifier used for the generation.<br>        model_config: The model configuration (hyperparameters) used.<br>        usage: A dictionary of usage information (input tokens, output tokens, etc.).<br>        span_id: The ID of the span. Optional. If not provided, we will generate an ID. We<br>            recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>            correctly formatted.<br>        parent: The parent span or trace. If not provided, we will automatically use the current<br>            trace/span as the parent.<br>        disabled: If True, we will return a Span but the Span will not be recorded.<br>    Returns:<br>        The newly created generation span.<br>    """<br>    return GLOBAL_TRACE_PROVIDER.create_span(<br>        span_data=GenerationSpanData(<br>            input=input, output=output, model=model, model_config=model_config, usage=usage<br>        ),<br>        span_id=span_id,<br>        parent=parent,<br>        disabled=disabled,<br>    )<br>``` |

### get\_current\_span

```md-code__content
get_current_span() -> Span[Any] | None

```

Returns the currently active span, if present.

Source code in `src/agents/tracing/create.py`

|     |     |
| --- | --- |
| ```<br>75<br>76<br>77<br>``` | ```md-code__content<br>def get_current_span() -> Span[Any] | None:<br>    """Returns the currently active span, if present."""<br>    return GLOBAL_TRACE_PROVIDER.get_current_span()<br>``` |

### get\_current\_trace

```md-code__content
get_current_trace() -> Trace | None

```

Returns the currently active trace, if present.

Source code in `src/agents/tracing/create.py`

|     |     |
| --- | --- |
| ```<br>70<br>71<br>72<br>``` | ```md-code__content<br>def get_current_trace() -> Trace | None:<br>    """Returns the currently active trace, if present."""<br>    return GLOBAL_TRACE_PROVIDER.get_current_trace()<br>``` |

### guardrail\_span

```md-code__content
guardrail_span(
    name: str,
    triggered: bool = False,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[GuardrailSpanData]

```

Create a new guardrail span. The span will not be started automatically, you should either
do `with guardrail_span() ...` or call `span.start()` \+ `span.finish()` manually.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `name` | `str` | The name of the guardrail. | _required_ |
| `triggered` | `bool` | Whether the guardrail was triggered. | `False` |
| `span_id` | `str | None` | The ID of the span. Optional. If not provided, we will generate an ID. We<br>recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>correctly formatted. | `None` |
| `parent` | `Trace | Span[Any] | None` | The parent span or trace. If not provided, we will automatically use the current<br>trace/span as the parent. | `None` |
| `disabled` | `bool` | If True, we will return a Span but the Span will not be recorded. | `False` |

Source code in `src/agents/tracing/create.py`

|     |     |
| --- | --- |
| ```<br>281<br>282<br>283<br>284<br>285<br>286<br>287<br>288<br>289<br>290<br>291<br>292<br>293<br>294<br>295<br>296<br>297<br>298<br>299<br>300<br>301<br>302<br>303<br>304<br>305<br>306<br>``` | ```md-code__content<br>def guardrail_span(<br>    name: str,<br>    triggered: bool = False,<br>    span_id: str | None = None,<br>    parent: Trace | Span[Any] | None = None,<br>    disabled: bool = False,<br>) -> Span[GuardrailSpanData]:<br>    """Create a new guardrail span. The span will not be started automatically, you should either<br>    do `with guardrail_span() ...` or call `span.start()` + `span.finish()` manually.<br>    Args:<br>        name: The name of the guardrail.<br>        triggered: Whether the guardrail was triggered.<br>        span_id: The ID of the span. Optional. If not provided, we will generate an ID. We<br>            recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>            correctly formatted.<br>        parent: The parent span or trace. If not provided, we will automatically use the current<br>            trace/span as the parent.<br>        disabled: If True, we will return a Span but the Span will not be recorded.<br>    """<br>    return GLOBAL_TRACE_PROVIDER.create_span(<br>        span_data=GuardrailSpanData(name=name, triggered=triggered),<br>        span_id=span_id,<br>        parent=parent,<br>        disabled=disabled,<br>    )<br>``` |

### handoff\_span

```md-code__content
handoff_span(
    from_agent: str | None = None,
    to_agent: str | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[HandoffSpanData]

```

Create a new handoff span. The span will not be started automatically, you should either do
`with handoff_span() ...` or call `span.start()` \+ `span.finish()` manually.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `from_agent` | `str | None` | The name of the agent that is handing off. | `None` |
| `to_agent` | `str | None` | The name of the agent that is receiving the handoff. | `None` |
| `span_id` | `str | None` | The ID of the span. Optional. If not provided, we will generate an ID. We<br>recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>correctly formatted. | `None` |
| `parent` | `Trace | Span[Any] | None` | The parent span or trace. If not provided, we will automatically use the current<br>trace/span as the parent. | `None` |
| `disabled` | `bool` | If True, we will return a Span but the Span will not be recorded. | `False` |

Returns:

| Type | Description |
| --- | --- |
| `Span[HandoffSpanData]` | The newly created handoff span. |

Source code in `src/agents/tracing/create.py`

|     |     |
| --- | --- |
| ```<br>218<br>219<br>220<br>221<br>222<br>223<br>224<br>225<br>226<br>227<br>228<br>229<br>230<br>231<br>232<br>233<br>234<br>235<br>236<br>237<br>238<br>239<br>240<br>241<br>242<br>243<br>244<br>245<br>246<br>``` | ```md-code__content<br>def handoff_span(<br>    from_agent: str | None = None,<br>    to_agent: str | None = None,<br>    span_id: str | None = None,<br>    parent: Trace | Span[Any] | None = None,<br>    disabled: bool = False,<br>) -> Span[HandoffSpanData]:<br>    """Create a new handoff span. The span will not be started automatically, you should either do<br>    `with handoff_span() ...` or call `span.start()` + `span.finish()` manually.<br>    Args:<br>        from_agent: The name of the agent that is handing off.<br>        to_agent: The name of the agent that is receiving the handoff.<br>        span_id: The ID of the span. Optional. If not provided, we will generate an ID. We<br>            recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>            correctly formatted.<br>        parent: The parent span or trace. If not provided, we will automatically use the current<br>            trace/span as the parent.<br>        disabled: If True, we will return a Span but the Span will not be recorded.<br>    Returns:<br>        The newly created handoff span.<br>    """<br>    return GLOBAL_TRACE_PROVIDER.create_span(<br>        span_data=HandoffSpanData(from_agent=from_agent, to_agent=to_agent),<br>        span_id=span_id,<br>        parent=parent,<br>        disabled=disabled,<br>    )<br>``` |

### response\_span

```md-code__content
response_span(
    response: Response | None = None,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[ResponseSpanData]

```

Create a new response span. The span will not be started automatically, you should either do
`with response_span() ...` or call `span.start()` \+ `span.finish()` manually.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `response` | `Response | None` | The OpenAI Response object. | `None` |
| `span_id` | `str | None` | The ID of the span. Optional. If not provided, we will generate an ID. We<br>recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>correctly formatted. | `None` |
| `parent` | `Trace | Span[Any] | None` | The parent span or trace. If not provided, we will automatically use the current<br>trace/span as the parent. | `None` |
| `disabled` | `bool` | If True, we will return a Span but the Span will not be recorded. | `False` |

Source code in `src/agents/tracing/create.py`

|     |     |
| --- | --- |
| ```<br>192<br>193<br>194<br>195<br>196<br>197<br>198<br>199<br>200<br>201<br>202<br>203<br>204<br>205<br>206<br>207<br>208<br>209<br>210<br>211<br>212<br>213<br>214<br>215<br>``` | ```md-code__content<br>def response_span(<br>    response: Response | None = None,<br>    span_id: str | None = None,<br>    parent: Trace | Span[Any] | None = None,<br>    disabled: bool = False,<br>) -> Span[ResponseSpanData]:<br>    """Create a new response span. The span will not be started automatically, you should either do<br>    `with response_span() ...` or call `span.start()` + `span.finish()` manually.<br>    Args:<br>        response: The OpenAI Response object.<br>        span_id: The ID of the span. Optional. If not provided, we will generate an ID. We<br>            recommend using `util.gen_span_id()` to generate a span ID, to guarantee that IDs are<br>            correctly formatted.<br>        parent: The parent span or trace. If not provided, we will automatically use the current<br>            trace/span as the parent.<br>        disabled: If True, we will return a Span but the Span will not be recorded.<br>    """<br>    return GLOBAL_TRACE_PROVIDER.create_span(<br>        span_data=ResponseSpanData(response=response),<br>        span_id=span_id,<br>        parent=parent,<br>        disabled=disabled,<br>    )<br>``` |

### trace

```md-code__content
trace(
    workflow_name: str,
    trace_id: str | None = None,
    group_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    disabled: bool = False,
) -> Trace

```

Create a new trace. The trace will not be started automatically; you should either use
it as a context manager ( `with trace(...):`) or call `trace.start()` \+ `trace.finish()`
manually.

In addition to the workflow name and optional grouping identifier, you can provide
an arbitrary metadata dictionary to attach additional user-defined information to
the trace.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `workflow_name` | `str` | The name of the logical app or workflow. For example, you might provide<br>"code\_bot" for a coding agent, or "customer\_support\_agent" for a customer support agent. | _required_ |
| `trace_id` | `str | None` | The ID of the trace. Optional. If not provided, we will generate an ID. We<br>recommend using `util.gen_trace_id()` to generate a trace ID, to guarantee that IDs are<br>correctly formatted. | `None` |
| `group_id` | `str | None` | Optional grouping identifier to link multiple traces from the same conversation<br>or process. For instance, you might use a chat thread ID. | `None` |
| `metadata` | `dict[str, Any] | None` | Optional dictionary of additional metadata to attach to the trace. | `None` |
| `disabled` | `bool` | If True, we will return a Trace but the Trace will not be recorded. This will<br>not be checked if there's an existing trace and `even_if_trace_running` is True. | `False` |

Returns:

| Type | Description |
| --- | --- |
| `Trace` | The newly created trace object. |

Source code in `src/agents/tracing/create.py`

|     |     |
| --- | --- |
| ```<br>24<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>``` | ```md-code__content<br>def trace(<br>    workflow_name: str,<br>    trace_id: str | None = None,<br>    group_id: str | None = None,<br>    metadata: dict[str, Any] | None = None,<br>    disabled: bool = False,<br>) -> Trace:<br>    """<br>    Create a new trace. The trace will not be started automatically; you should either use<br>    it as a context manager (`with trace(...):`) or call `trace.start()` + `trace.finish()`<br>    manually.<br>    In addition to the workflow name and optional grouping identifier, you can provide<br>    an arbitrary metadata dictionary to attach additional user-defined information to<br>    the trace.<br>    Args:<br>        workflow_name: The name of the logical app or workflow. For example, you might provide<br>            "code_bot" for a coding agent, or "customer_support_agent" for a customer support agent.<br>        trace_id: The ID of the trace. Optional. If not provided, we will generate an ID. We<br>            recommend using `util.gen_trace_id()` to generate a trace ID, to guarantee that IDs are<br>            correctly formatted.<br>        group_id: Optional grouping identifier to link multiple traces from the same conversation<br>            or process. For instance, you might use a chat thread ID.<br>        metadata: Optional dictionary of additional metadata to attach to the trace.<br>        disabled: If True, we will return a Trace but the Trace will not be recorded. This will<br>            not be checked if there's an existing trace and `even_if_trace_running` is True.<br>    Returns:<br>        The newly created trace object.<br>    """<br>    current_trace = GLOBAL_TRACE_PROVIDER.get_current_trace()<br>    if current_trace:<br>        logger.warning(<br>            "Trace already exists. Creating a new trace, but this is probably a mistake."<br>        )<br>    return GLOBAL_TRACE_PROVIDER.create_trace(<br>        name=workflow_name,<br>        trace_id=trace_id,<br>        group_id=group_id,<br>        metadata=metadata,<br>        disabled=disabled,<br>    )<br>``` |

### gen\_span\_id

```md-code__content
gen_span_id() -> str

```

Generates a new span ID.

Source code in `src/agents/tracing/util.py`

|     |     |
| --- | --- |
| ```<br>15<br>16<br>17<br>``` | ```md-code__content<br>def gen_span_id() -> str:<br>    """Generates a new span ID."""<br>    return f"span_{uuid.uuid4().hex[:24]}"<br>``` |

### gen\_trace\_id

```md-code__content
gen_trace_id() -> str

```

Generates a new trace ID.

Source code in `src/agents/tracing/util.py`

|     |     |
| --- | --- |
| ```<br>10<br>11<br>12<br>``` | ```md-code__content<br>def gen_trace_id() -> str:<br>    """Generates a new trace ID."""<br>    return f"trace_{uuid.uuid4().hex}"<br>``` |

### add\_trace\_processor

```md-code__content
add_trace_processor(
    span_processor: TracingProcessor,
) -> None

```

Adds a new trace processor. This processor will receive all traces/spans.

Source code in `src/agents/tracing/__init__.py`

|     |     |
| --- | --- |
| ```<br>63<br>64<br>65<br>66<br>67<br>``` | ```md-code__content<br>def add_trace_processor(span_processor: TracingProcessor) -> None:<br>    """<br>    Adds a new trace processor. This processor will receive all traces/spans.<br>    """<br>    GLOBAL_TRACE_PROVIDER.register_processor(span_processor)<br>``` |

### set\_trace\_processors

```md-code__content
set_trace_processors(
    processors: list[TracingProcessor],
) -> None

```

Set the list of trace processors. This will replace the current list of processors.

Source code in `src/agents/tracing/__init__.py`

|     |     |
| --- | --- |
| ```<br>70<br>71<br>72<br>73<br>74<br>``` | ```md-code__content<br>def set_trace_processors(processors: list[TracingProcessor]) -> None:<br>    """<br>    Set the list of trace processors. This will replace the current list of processors.<br>    """<br>    GLOBAL_TRACE_PROVIDER.set_processors(processors)<br>``` |

### set\_tracing\_disabled

```md-code__content
set_tracing_disabled(disabled: bool) -> None

```

Set whether tracing is globally disabled.

Source code in `src/agents/tracing/__init__.py`

|     |     |
| --- | --- |
| ```<br>77<br>78<br>79<br>80<br>81<br>``` | ```md-code__content<br>def set_tracing_disabled(disabled: bool) -> None:<br>    """<br>    Set whether tracing is globally disabled.<br>    """<br>    GLOBAL_TRACE_PROVIDER.set_disabled(disabled)<br>``` |

### set\_tracing\_export\_api\_key

```md-code__content
set_tracing_export_api_key(api_key: str) -> None

```

Set the OpenAI API key for the backend exporter.

Source code in `src/agents/tracing/__init__.py`

|     |     |
| --- | --- |
| ```<br>84<br>85<br>86<br>87<br>88<br>``` | ```md-code__content<br>def set_tracing_export_api_key(api_key: str) -> None:<br>    """<br>    Set the OpenAI API key for the backend exporter.<br>    """<br>    default_exporter().set_api_key(api_key)<br>``` |