[Skip to content](https://openai.github.io/openai-agents-python/ref/tracing/processor_interface/#processor-interface)

# `Processor interface`

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

### TracingExporter

Bases: `ABC`

Exports traces and spans. For example, could log them or send them to a backend.

Source code in `src/agents/tracing/processor_interface.py`

|     |     |
| --- | --- |
| ```<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>69<br>``` | ```md-code__content<br>class TracingExporter(abc.ABC):<br>    """Exports traces and spans. For example, could log them or send them to a backend."""<br>    @abc.abstractmethod<br>    def export(self, items: list["Trace | Span[Any]"]) -> None:<br>        """Exports a list of traces and spans.<br>        Args:<br>            items: The items to export.<br>        """<br>        pass<br>``` |

#### export`abstractmethod`

```md-code__content
export(items: list[Trace | Span[Any]]) -> None

```

Exports a list of traces and spans.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `items` | `list[Trace | Span[Any]]` | The items to export. | _required_ |

Source code in `src/agents/tracing/processor_interface.py`

|     |     |
| --- | --- |
| ```<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>69<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def export(self, items: list["Trace | Span[Any]"]) -> None:<br>    """Exports a list of traces and spans.<br>    Args:<br>        items: The items to export.<br>    """<br>    pass<br>``` |