[Skip to content](https://openai.github.io/openai-agents-python/ref/tracing/spans/#spans)

# `Spans`

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

### NoOpSpan

Bases: `Span[TSpanData]`

Source code in `src/agents/tracing/spans.py`

|     |     |
| --- | --- |
| ```<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>108<br>109<br>110<br>111<br>112<br>113<br>114<br>115<br>116<br>117<br>118<br>119<br>120<br>121<br>122<br>123<br>124<br>125<br>126<br>127<br>128<br>129<br>130<br>131<br>132<br>133<br>134<br>135<br>136<br>137<br>138<br>139<br>140<br>141<br>142<br>143<br>144<br>145<br>146<br>147<br>148<br>149<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>``` | ```md-code__content<br>class NoOpSpan(Span[TSpanData]):<br>    __slots__ = ("_span_data", "_prev_span_token")<br>    def __init__(self, span_data: TSpanData):<br>        self._span_data = span_data<br>        self._prev_span_token: contextvars.Token[Span[TSpanData] | None] | None = None<br>    @property<br>    def trace_id(self) -> str:<br>        return "no-op"<br>    @property<br>    def span_id(self) -> str:<br>        return "no-op"<br>    @property<br>    def span_data(self) -> TSpanData:<br>        return self._span_data<br>    @property<br>    def parent_id(self) -> str | None:<br>        return None<br>    def start(self, mark_as_current: bool = False):<br>        if mark_as_current:<br>            self._prev_span_token = Scope.set_current_span(self)<br>    def finish(self, reset_current: bool = False) -> None:<br>        if reset_current and self._prev_span_token is not None:<br>            Scope.reset_current_span(self._prev_span_token)<br>            self._prev_span_token = None<br>    def __enter__(self) -> Span[TSpanData]:<br>        self.start(mark_as_current=True)<br>        return self<br>    def __exit__(self, exc_type, exc_val, exc_tb):<br>        reset_current = True<br>        if exc_type is GeneratorExit:<br>            logger.debug("GeneratorExit, skipping span reset")<br>            reset_current = False<br>        self.finish(reset_current=reset_current)<br>    def set_error(self, error: SpanError) -> None:<br>        pass<br>    @property<br>    def error(self) -> SpanError | None:<br>        return None<br>    def export(self) -> dict[str, Any] | None:<br>        return None<br>    @property<br>    def started_at(self) -> str | None:<br>        return None<br>    @property<br>    def ended_at(self) -> str | None:<br>        return None<br>``` |

### SpanImpl

Bases: `Span[TSpanData]`

Source code in `src/agents/tracing/spans.py`

|     |     |
| --- | --- |
| ```<br>159<br>160<br>161<br>162<br>163<br>164<br>165<br>166<br>167<br>168<br>169<br>170<br>171<br>172<br>173<br>174<br>175<br>176<br>177<br>178<br>179<br>180<br>181<br>182<br>183<br>184<br>185<br>186<br>187<br>188<br>189<br>190<br>191<br>192<br>193<br>194<br>195<br>196<br>197<br>198<br>199<br>200<br>201<br>202<br>203<br>204<br>205<br>206<br>207<br>208<br>209<br>210<br>211<br>212<br>213<br>214<br>215<br>216<br>217<br>218<br>219<br>220<br>221<br>222<br>223<br>224<br>225<br>226<br>227<br>228<br>229<br>230<br>231<br>232<br>233<br>234<br>235<br>236<br>237<br>238<br>239<br>240<br>241<br>242<br>243<br>244<br>245<br>246<br>247<br>248<br>249<br>250<br>251<br>252<br>253<br>254<br>255<br>256<br>257<br>258<br>259<br>260<br>261<br>262<br>263<br>264<br>``` | ```md-code__content<br>class SpanImpl(Span[TSpanData]):<br>    __slots__ = (<br>        "_trace_id",<br>        "_span_id",<br>        "_parent_id",<br>        "_started_at",<br>        "_ended_at",<br>        "_error",<br>        "_prev_span_token",<br>        "_processor",<br>        "_span_data",<br>    )<br>    def __init__(<br>        self,<br>        trace_id: str,<br>        span_id: str | None,<br>        parent_id: str | None,<br>        processor: TracingProcessor,<br>        span_data: TSpanData,<br>    ):<br>        self._trace_id = trace_id<br>        self._span_id = span_id or util.gen_span_id()<br>        self._parent_id = parent_id<br>        self._started_at: str | None = None<br>        self._ended_at: str | None = None<br>        self._processor = processor<br>        self._error: SpanError | None = None<br>        self._prev_span_token: contextvars.Token[Span[TSpanData] | None] | None = None<br>        self._span_data = span_data<br>    @property<br>    def trace_id(self) -> str:<br>        return self._trace_id<br>    @property<br>    def span_id(self) -> str:<br>        return self._span_id<br>    @property<br>    def span_data(self) -> TSpanData:<br>        return self._span_data<br>    @property<br>    def parent_id(self) -> str | None:<br>        return self._parent_id<br>    def start(self, mark_as_current: bool = False):<br>        if self.started_at is not None:<br>            logger.warning("Span already started")<br>            return<br>        self._started_at = util.time_iso()<br>        self._processor.on_span_start(self)<br>        if mark_as_current:<br>            self._prev_span_token = Scope.set_current_span(self)<br>    def finish(self, reset_current: bool = False) -> None:<br>        if self.ended_at is not None:<br>            logger.warning("Span already finished")<br>            return<br>        self._ended_at = util.time_iso()<br>        self._processor.on_span_end(self)<br>        if reset_current and self._prev_span_token is not None:<br>            Scope.reset_current_span(self._prev_span_token)<br>            self._prev_span_token = None<br>    def __enter__(self) -> Span[TSpanData]:<br>        self.start(mark_as_current=True)<br>        return self<br>    def __exit__(self, exc_type, exc_val, exc_tb):<br>        reset_current = True<br>        if exc_type is GeneratorExit:<br>            logger.debug("GeneratorExit, skipping span reset")<br>            reset_current = False<br>        self.finish(reset_current=reset_current)<br>    def set_error(self, error: SpanError) -> None:<br>        self._error = error<br>    @property<br>    def error(self) -> SpanError | None:<br>        return self._error<br>    @property<br>    def started_at(self) -> str | None:<br>        return self._started_at<br>    @property<br>    def ended_at(self) -> str | None:<br>        return self._ended_at<br>    def export(self) -> dict[str, Any] | None:<br>        return {<br>            "object": "trace.span",<br>            "id": self.span_id,<br>            "trace_id": self.trace_id,<br>            "parent_id": self._parent_id,<br>            "started_at": self._started_at,<br>            "ended_at": self._ended_at,<br>            "span_data": self.span_data.export(),<br>            "error": self._error,<br>        }<br>``` |