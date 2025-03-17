[Skip to content](https://openai.github.io/openai-agents-python/ref/tracing/setup/#setup)

# `Setup`

### SynchronousMultiTracingProcessor

Bases: `TracingProcessor`

Forwards all calls to a list of TracingProcessors, in order of registration.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>15<br>16<br>17<br>18<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>69<br>70<br>71<br>72<br>73<br>74<br>75<br>76<br>77<br>78<br>79<br>80<br>``` | ```md-code__content<br>class SynchronousMultiTracingProcessor(TracingProcessor):<br>    """<br>    Forwards all calls to a list of TracingProcessors, in order of registration.<br>    """<br>    def __init__(self):<br>        # Using a tuple to avoid race conditions when iterating over processors<br>        self._processors: tuple[TracingProcessor, ...] = ()<br>        self._lock = threading.Lock()<br>    def add_tracing_processor(self, tracing_processor: TracingProcessor):<br>        """<br>        Add a processor to the list of processors. Each processor will receive all traces/spans.<br>        """<br>        with self._lock:<br>            self._processors += (tracing_processor,)<br>    def set_processors(self, processors: list[TracingProcessor]):<br>        """<br>        Set the list of processors. This will replace the current list of processors.<br>        """<br>        with self._lock:<br>            self._processors = tuple(processors)<br>    def on_trace_start(self, trace: Trace) -> None:<br>        """<br>        Called when a trace is started.<br>        """<br>        for processor in self._processors:<br>            processor.on_trace_start(trace)<br>    def on_trace_end(self, trace: Trace) -> None:<br>        """<br>        Called when a trace is finished.<br>        """<br>        for processor in self._processors:<br>            processor.on_trace_end(trace)<br>    def on_span_start(self, span: Span[Any]) -> None:<br>        """<br>        Called when a span is started.<br>        """<br>        for processor in self._processors:<br>            processor.on_span_start(span)<br>    def on_span_end(self, span: Span[Any]) -> None:<br>        """<br>        Called when a span is finished.<br>        """<br>        for processor in self._processors:<br>            processor.on_span_end(span)<br>    def shutdown(self) -> None:<br>        """<br>        Called when the application stops.<br>        """<br>        for processor in self._processors:<br>            logger.debug(f"Shutting down trace processor {processor}")<br>            processor.shutdown()<br>    def force_flush(self):<br>        """<br>        Force the processors to flush their buffers.<br>        """<br>        for processor in self._processors:<br>            processor.force_flush()<br>``` |

#### add\_tracing\_processor

```md-code__content
add_tracing_processor(tracing_processor: TracingProcessor)

```

Add a processor to the list of processors. Each processor will receive all traces/spans.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>25<br>26<br>27<br>28<br>29<br>30<br>``` | ```md-code__content<br>def add_tracing_processor(self, tracing_processor: TracingProcessor):<br>    """<br>    Add a processor to the list of processors. Each processor will receive all traces/spans.<br>    """<br>    with self._lock:<br>        self._processors += (tracing_processor,)<br>``` |

#### set\_processors

```md-code__content
set_processors(processors: list[TracingProcessor])

```

Set the list of processors. This will replace the current list of processors.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>32<br>33<br>34<br>35<br>36<br>37<br>``` | ```md-code__content<br>def set_processors(self, processors: list[TracingProcessor]):<br>    """<br>    Set the list of processors. This will replace the current list of processors.<br>    """<br>    with self._lock:<br>        self._processors = tuple(processors)<br>``` |

#### on\_trace\_start

```md-code__content
on_trace_start(trace: Trace) -> None

```

Called when a trace is started.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>39<br>40<br>41<br>42<br>43<br>44<br>``` | ```md-code__content<br>def on_trace_start(self, trace: Trace) -> None:<br>    """<br>    Called when a trace is started.<br>    """<br>    for processor in self._processors:<br>        processor.on_trace_start(trace)<br>``` |

#### on\_trace\_end

```md-code__content
on_trace_end(trace: Trace) -> None

```

Called when a trace is finished.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>46<br>47<br>48<br>49<br>50<br>51<br>``` | ```md-code__content<br>def on_trace_end(self, trace: Trace) -> None:<br>    """<br>    Called when a trace is finished.<br>    """<br>    for processor in self._processors:<br>        processor.on_trace_end(trace)<br>``` |

#### on\_span\_start

```md-code__content
on_span_start(span: Span[Any]) -> None

```

Called when a span is started.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>53<br>54<br>55<br>56<br>57<br>58<br>``` | ```md-code__content<br>def on_span_start(self, span: Span[Any]) -> None:<br>    """<br>    Called when a span is started.<br>    """<br>    for processor in self._processors:<br>        processor.on_span_start(span)<br>``` |

#### on\_span\_end

```md-code__content
on_span_end(span: Span[Any]) -> None

```

Called when a span is finished.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>60<br>61<br>62<br>63<br>64<br>65<br>``` | ```md-code__content<br>def on_span_end(self, span: Span[Any]) -> None:<br>    """<br>    Called when a span is finished.<br>    """<br>    for processor in self._processors:<br>        processor.on_span_end(span)<br>``` |

#### shutdown

```md-code__content
shutdown() -> None

```

Called when the application stops.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>67<br>68<br>69<br>70<br>71<br>72<br>73<br>``` | ```md-code__content<br>def shutdown(self) -> None:<br>    """<br>    Called when the application stops.<br>    """<br>    for processor in self._processors:<br>        logger.debug(f"Shutting down trace processor {processor}")<br>        processor.shutdown()<br>``` |

#### force\_flush

```md-code__content
force_flush()

```

Force the processors to flush their buffers.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>75<br>76<br>77<br>78<br>79<br>80<br>``` | ```md-code__content<br>def force_flush(self):<br>    """<br>    Force the processors to flush their buffers.<br>    """<br>    for processor in self._processors:<br>        processor.force_flush()<br>``` |

### TraceProvider

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br> 83<br> 84<br> 85<br> 86<br> 87<br> 88<br> 89<br> 90<br> 91<br> 92<br> 93<br> 94<br> 95<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>108<br>109<br>110<br>111<br>112<br>113<br>114<br>115<br>116<br>117<br>118<br>119<br>120<br>121<br>122<br>123<br>124<br>125<br>126<br>127<br>128<br>129<br>130<br>131<br>132<br>133<br>134<br>135<br>136<br>137<br>138<br>139<br>140<br>141<br>142<br>143<br>144<br>145<br>146<br>147<br>148<br>149<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>157<br>158<br>159<br>160<br>161<br>162<br>163<br>164<br>165<br>166<br>167<br>168<br>169<br>170<br>171<br>172<br>173<br>174<br>175<br>176<br>177<br>178<br>179<br>180<br>181<br>182<br>183<br>184<br>185<br>186<br>187<br>188<br>189<br>190<br>191<br>192<br>193<br>194<br>195<br>196<br>197<br>198<br>199<br>200<br>201<br>202<br>203<br>204<br>205<br>206<br>207<br>208<br>``` | ```md-code__content<br>class TraceProvider:<br>    def __init__(self):<br>        self._multi_processor = SynchronousMultiTracingProcessor()<br>        self._disabled = os.environ.get("OPENAI_AGENTS_DISABLE_TRACING", "false").lower() in (<br>            "true",<br>            "1",<br>        )<br>    def register_processor(self, processor: TracingProcessor):<br>        """<br>        Add a processor to the list of processors. Each processor will receive all traces/spans.<br>        """<br>        self._multi_processor.add_tracing_processor(processor)<br>    def set_processors(self, processors: list[TracingProcessor]):<br>        """<br>        Set the list of processors. This will replace the current list of processors.<br>        """<br>        self._multi_processor.set_processors(processors)<br>    def get_current_trace(self) -> Trace | None:<br>        """<br>        Returns the currently active trace, if any.<br>        """<br>        return Scope.get_current_trace()<br>    def get_current_span(self) -> Span[Any] | None:<br>        """<br>        Returns the currently active span, if any.<br>        """<br>        return Scope.get_current_span()<br>    def set_disabled(self, disabled: bool) -> None:<br>        """<br>        Set whether tracing is disabled.<br>        """<br>        self._disabled = disabled<br>    def create_trace(<br>        self,<br>        name: str,<br>        trace_id: str | None = None,<br>        group_id: str | None = None,<br>        metadata: dict[str, Any] | None = None,<br>        disabled: bool = False,<br>    ) -> Trace:<br>        """<br>        Create a new trace.<br>        """<br>        if self._disabled or disabled:<br>            logger.debug(f"Tracing is disabled. Not creating trace {name}")<br>            return NoOpTrace()<br>        trace_id = trace_id or util.gen_trace_id()<br>        logger.debug(f"Creating trace {name} with id {trace_id}")<br>        return TraceImpl(<br>            name=name,<br>            trace_id=trace_id,<br>            group_id=group_id,<br>            metadata=metadata,<br>            processor=self._multi_processor,<br>        )<br>    def create_span(<br>        self,<br>        span_data: TSpanData,<br>        span_id: str | None = None,<br>        parent: Trace | Span[Any] | None = None,<br>        disabled: bool = False,<br>    ) -> Span[TSpanData]:<br>        """<br>        Create a new span.<br>        """<br>        if self._disabled or disabled:<br>            logger.debug(f"Tracing is disabled. Not creating span {span_data}")<br>            return NoOpSpan(span_data)<br>        if not parent:<br>            current_span = Scope.get_current_span()<br>            current_trace = Scope.get_current_trace()<br>            if current_trace is None:<br>                logger.error(<br>                    "No active trace. Make sure to start a trace with `trace()` first"<br>                    "Returning NoOpSpan."<br>                )<br>                return NoOpSpan(span_data)<br>            elif isinstance(current_trace, NoOpTrace) or isinstance(current_span, NoOpSpan):<br>                logger.debug(<br>                    f"Parent {current_span} or {current_trace} is no-op, returning NoOpSpan"<br>                )<br>                return NoOpSpan(span_data)<br>            parent_id = current_span.span_id if current_span else None<br>            trace_id = current_trace.trace_id<br>        elif isinstance(parent, Trace):<br>            if isinstance(parent, NoOpTrace):<br>                logger.debug(f"Parent {parent} is no-op, returning NoOpSpan")<br>                return NoOpSpan(span_data)<br>            trace_id = parent.trace_id<br>            parent_id = None<br>        elif isinstance(parent, Span):<br>            if isinstance(parent, NoOpSpan):<br>                logger.debug(f"Parent {parent} is no-op, returning NoOpSpan")<br>                return NoOpSpan(span_data)<br>            parent_id = parent.span_id<br>            trace_id = parent.trace_id<br>        logger.debug(f"Creating span {span_data} with id {span_id}")<br>        return SpanImpl(<br>            trace_id=trace_id,<br>            span_id=span_id,<br>            parent_id=parent_id,<br>            processor=self._multi_processor,<br>            span_data=span_data,<br>        )<br>    def shutdown(self) -> None:<br>        try:<br>            logger.debug("Shutting down trace provider")<br>            self._multi_processor.shutdown()<br>        except Exception as e:<br>            logger.error(f"Error shutting down trace provider: {e}")<br>``` |

#### register\_processor

```md-code__content
register_processor(processor: TracingProcessor)

```

Add a processor to the list of processors. Each processor will receive all traces/spans.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>91<br>92<br>93<br>94<br>95<br>``` | ```md-code__content<br>def register_processor(self, processor: TracingProcessor):<br>    """<br>    Add a processor to the list of processors. Each processor will receive all traces/spans.<br>    """<br>    self._multi_processor.add_tracing_processor(processor)<br>``` |

#### set\_processors

```md-code__content
set_processors(processors: list[TracingProcessor])

```

Set the list of processors. This will replace the current list of processors.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br> 97<br> 98<br> 99<br>100<br>101<br>``` | ```md-code__content<br>def set_processors(self, processors: list[TracingProcessor]):<br>    """<br>    Set the list of processors. This will replace the current list of processors.<br>    """<br>    self._multi_processor.set_processors(processors)<br>``` |

#### get\_current\_trace

```md-code__content
get_current_trace() -> Trace | None

```

Returns the currently active trace, if any.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>103<br>104<br>105<br>106<br>107<br>``` | ```md-code__content<br>def get_current_trace(self) -> Trace | None:<br>    """<br>    Returns the currently active trace, if any.<br>    """<br>    return Scope.get_current_trace()<br>``` |

#### get\_current\_span

```md-code__content
get_current_span() -> Span[Any] | None

```

Returns the currently active span, if any.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>109<br>110<br>111<br>112<br>113<br>``` | ```md-code__content<br>def get_current_span(self) -> Span[Any] | None:<br>    """<br>    Returns the currently active span, if any.<br>    """<br>    return Scope.get_current_span()<br>``` |

#### set\_disabled

```md-code__content
set_disabled(disabled: bool) -> None

```

Set whether tracing is disabled.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>115<br>116<br>117<br>118<br>119<br>``` | ```md-code__content<br>def set_disabled(self, disabled: bool) -> None:<br>    """<br>    Set whether tracing is disabled.<br>    """<br>    self._disabled = disabled<br>``` |

#### create\_trace

```md-code__content
create_trace(
    name: str,
    trace_id: str | None = None,
    group_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    disabled: bool = False,
) -> Trace

```

Create a new trace.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>121<br>122<br>123<br>124<br>125<br>126<br>127<br>128<br>129<br>130<br>131<br>132<br>133<br>134<br>135<br>136<br>137<br>138<br>139<br>140<br>141<br>142<br>143<br>144<br>145<br>146<br>``` | ```md-code__content<br>def create_trace(<br>    self,<br>    name: str,<br>    trace_id: str | None = None,<br>    group_id: str | None = None,<br>    metadata: dict[str, Any] | None = None,<br>    disabled: bool = False,<br>) -> Trace:<br>    """<br>    Create a new trace.<br>    """<br>    if self._disabled or disabled:<br>        logger.debug(f"Tracing is disabled. Not creating trace {name}")<br>        return NoOpTrace()<br>    trace_id = trace_id or util.gen_trace_id()<br>    logger.debug(f"Creating trace {name} with id {trace_id}")<br>    return TraceImpl(<br>        name=name,<br>        trace_id=trace_id,<br>        group_id=group_id,<br>        metadata=metadata,<br>        processor=self._multi_processor,<br>    )<br>``` |

#### create\_span

```md-code__content
create_span(
    span_data: TSpanData,
    span_id: str | None = None,
    parent: Trace | Span[Any] | None = None,
    disabled: bool = False,
) -> Span[TSpanData]

```

Create a new span.

Source code in `src/agents/tracing/setup.py`

|     |     |
| --- | --- |
| ```<br>148<br>149<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>157<br>158<br>159<br>160<br>161<br>162<br>163<br>164<br>165<br>166<br>167<br>168<br>169<br>170<br>171<br>172<br>173<br>174<br>175<br>176<br>177<br>178<br>179<br>180<br>181<br>182<br>183<br>184<br>185<br>186<br>187<br>188<br>189<br>190<br>191<br>192<br>193<br>194<br>195<br>196<br>197<br>198<br>199<br>200<br>201<br>``` | ```md-code__content<br>def create_span(<br>    self,<br>    span_data: TSpanData,<br>    span_id: str | None = None,<br>    parent: Trace | Span[Any] | None = None,<br>    disabled: bool = False,<br>) -> Span[TSpanData]:<br>    """<br>    Create a new span.<br>    """<br>    if self._disabled or disabled:<br>        logger.debug(f"Tracing is disabled. Not creating span {span_data}")<br>        return NoOpSpan(span_data)<br>    if not parent:<br>        current_span = Scope.get_current_span()<br>        current_trace = Scope.get_current_trace()<br>        if current_trace is None:<br>            logger.error(<br>                "No active trace. Make sure to start a trace with `trace()` first"<br>                "Returning NoOpSpan."<br>            )<br>            return NoOpSpan(span_data)<br>        elif isinstance(current_trace, NoOpTrace) or isinstance(current_span, NoOpSpan):<br>            logger.debug(<br>                f"Parent {current_span} or {current_trace} is no-op, returning NoOpSpan"<br>            )<br>            return NoOpSpan(span_data)<br>        parent_id = current_span.span_id if current_span else None<br>        trace_id = current_trace.trace_id<br>    elif isinstance(parent, Trace):<br>        if isinstance(parent, NoOpTrace):<br>            logger.debug(f"Parent {parent} is no-op, returning NoOpSpan")<br>            return NoOpSpan(span_data)<br>        trace_id = parent.trace_id<br>        parent_id = None<br>    elif isinstance(parent, Span):<br>        if isinstance(parent, NoOpSpan):<br>            logger.debug(f"Parent {parent} is no-op, returning NoOpSpan")<br>            return NoOpSpan(span_data)<br>        parent_id = parent.span_id<br>        trace_id = parent.trace_id<br>    logger.debug(f"Creating span {span_data} with id {span_id}")<br>    return SpanImpl(<br>        trace_id=trace_id,<br>        span_id=span_id,<br>        parent_id=parent_id,<br>        processor=self._multi_processor,<br>        span_data=span_data,<br>    )<br>``` |