[Skip to content](https://openai.github.io/openai-agents-python/ref/tracing/traces/#traces)

# `Traces`

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

### NoOpTrace

Bases: `Trace`

A no-op trace that will not be recorded.

Source code in `src/agents/tracing/traces.py`

|     |     |
| --- | --- |
| ```<br> 70<br> 71<br> 72<br> 73<br> 74<br> 75<br> 76<br> 77<br> 78<br> 79<br> 80<br> 81<br> 82<br> 83<br> 84<br> 85<br> 86<br> 87<br> 88<br> 89<br> 90<br> 91<br> 92<br> 93<br> 94<br> 95<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>108<br>109<br>110<br>111<br>``` | ```md-code__content<br>class NoOpTrace(Trace):<br>    """<br>    A no-op trace that will not be recorded.<br>    """<br>    def __init__(self):<br>        self._started = False<br>        self._prev_context_token: contextvars.Token[Trace | None] | None = None<br>    def __enter__(self) -> Trace:<br>        if self._started:<br>            if not self._prev_context_token:<br>                logger.error("Trace already started but no context token set")<br>            return self<br>        self._started = True<br>        self.start(mark_as_current=True)<br>        return self<br>    def __exit__(self, exc_type, exc_val, exc_tb):<br>        self.finish(reset_current=True)<br>    def start(self, mark_as_current: bool = False):<br>        if mark_as_current:<br>            self._prev_context_token = Scope.set_current_trace(self)<br>    def finish(self, reset_current: bool = False):<br>        if reset_current and self._prev_context_token is not None:<br>            Scope.reset_current_trace(self._prev_context_token)<br>            self._prev_context_token = None<br>    @property<br>    def trace_id(self) -> str:<br>        return "no-op"<br>    @property<br>    def name(self) -> str:<br>        return "no-op"<br>    def export(self) -> dict[str, Any] | None:<br>        return None<br>``` |

### TraceImpl

Bases: `Trace`

A trace that will be recorded by the tracing library.

Source code in `src/agents/tracing/traces.py`

|     |     |
| --- | --- |
| ```<br>117<br>118<br>119<br>120<br>121<br>122<br>123<br>124<br>125<br>126<br>127<br>128<br>129<br>130<br>131<br>132<br>133<br>134<br>135<br>136<br>137<br>138<br>139<br>140<br>141<br>142<br>143<br>144<br>145<br>146<br>147<br>148<br>149<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>157<br>158<br>159<br>160<br>161<br>162<br>163<br>164<br>165<br>166<br>167<br>168<br>169<br>170<br>171<br>172<br>173<br>174<br>175<br>176<br>177<br>178<br>179<br>180<br>181<br>182<br>183<br>184<br>185<br>186<br>187<br>188<br>189<br>190<br>191<br>192<br>193<br>194<br>195<br>``` | ```md-code__content<br>class TraceImpl(Trace):<br>    """<br>    A trace that will be recorded by the tracing library.<br>    """<br>    __slots__ = (<br>        "_name",<br>        "_trace_id",<br>        "group_id",<br>        "metadata",<br>        "_prev_context_token",<br>        "_processor",<br>        "_started",<br>    )<br>    def __init__(<br>        self,<br>        name: str,<br>        trace_id: str | None,<br>        group_id: str | None,<br>        metadata: dict[str, Any] | None,<br>        processor: TracingProcessor,<br>    ):<br>        self._name = name<br>        self._trace_id = trace_id or util.gen_trace_id()<br>        self.group_id = group_id<br>        self.metadata = metadata<br>        self._prev_context_token: contextvars.Token[Trace | None] | None = None<br>        self._processor = processor<br>        self._started = False<br>    @property<br>    def trace_id(self) -> str:<br>        return self._trace_id<br>    @property<br>    def name(self) -> str:<br>        return self._name<br>    def start(self, mark_as_current: bool = False):<br>        if self._started:<br>            return<br>        self._started = True<br>        self._processor.on_trace_start(self)<br>        if mark_as_current:<br>            self._prev_context_token = Scope.set_current_trace(self)<br>    def finish(self, reset_current: bool = False):<br>        if not self._started:<br>            return<br>        self._processor.on_trace_end(self)<br>        if reset_current and self._prev_context_token is not None:<br>            Scope.reset_current_trace(self._prev_context_token)<br>            self._prev_context_token = None<br>    def __enter__(self) -> Trace:<br>        if self._started:<br>            if not self._prev_context_token:<br>                logger.error("Trace already started but no context token set")<br>            return self<br>        self.start(mark_as_current=True)<br>        return self<br>    def __exit__(self, exc_type, exc_val, exc_tb):<br>        self.finish(reset_current=exc_type is not GeneratorExit)<br>    def export(self) -> dict[str, Any] | None:<br>        return {<br>            "object": "trace",<br>            "id": self.trace_id,<br>            "workflow_name": self.name,<br>            "group_id": self.group_id,<br>            "metadata": self.metadata,<br>        }<br>``` |