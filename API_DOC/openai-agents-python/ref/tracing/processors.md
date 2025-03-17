[Skip to content](https://openai.github.io/openai-agents-python/ref/tracing/processors/#processors)

# `Processors`

### ConsoleSpanExporter

Bases: `TracingExporter`

Prints the traces and spans to the console.

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br>18<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>``` | ```md-code__content<br>class ConsoleSpanExporter(TracingExporter):<br>    """Prints the traces and spans to the console."""<br>    def export(self, items: list[Trace | Span[Any]]) -> None:<br>        for item in items:<br>            if isinstance(item, Trace):<br>                print(f"[Exporter] Export trace_id={item.trace_id}, name={item.name}, ")<br>            else:<br>                print(f"[Exporter] Export span: {item.export()}")<br>``` |

### BackendSpanExporter

Bases: `TracingExporter`

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br> 29<br> 30<br> 31<br> 32<br> 33<br> 34<br> 35<br> 36<br> 37<br> 38<br> 39<br> 40<br> 41<br> 42<br> 43<br> 44<br> 45<br> 46<br> 47<br> 48<br> 49<br> 50<br> 51<br> 52<br> 53<br> 54<br> 55<br> 56<br> 57<br> 58<br> 59<br> 60<br> 61<br> 62<br> 63<br> 64<br> 65<br> 66<br> 67<br> 68<br> 69<br> 70<br> 71<br> 72<br> 73<br> 74<br> 75<br> 76<br> 77<br> 78<br> 79<br> 80<br> 81<br> 82<br> 83<br> 84<br> 85<br> 86<br> 87<br> 88<br> 89<br> 90<br> 91<br> 92<br> 93<br> 94<br> 95<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>108<br>109<br>110<br>111<br>112<br>113<br>114<br>115<br>116<br>117<br>118<br>119<br>120<br>121<br>122<br>123<br>124<br>125<br>126<br>``` | ```md-code__content<br>class BackendSpanExporter(TracingExporter):<br>    def __init__(<br>        self,<br>        api_key: str | None = None,<br>        organization: str | None = None,<br>        project: str | None = None,<br>        endpoint: str = "https://api.openai.com/v1/traces/ingest",<br>        max_retries: int = 3,<br>        base_delay: float = 1.0,<br>        max_delay: float = 30.0,<br>    ):<br>        """<br>        Args:<br>            api_key: The API key for the "Authorization" header. Defaults to<br>                `os.environ["OPENAI_TRACE_API_KEY"]` if not provided.<br>            organization: The OpenAI organization to use. Defaults to<br>                `os.environ["OPENAI_ORG_ID"]` if not provided.<br>            project: The OpenAI project to use. Defaults to<br>                `os.environ["OPENAI_PROJECT_ID"]` if not provided.<br>            endpoint: The HTTP endpoint to which traces/spans are posted.<br>            max_retries: Maximum number of retries upon failures.<br>            base_delay: Base delay (in seconds) for the first backoff.<br>            max_delay: Maximum delay (in seconds) for backoff growth.<br>        """<br>        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")<br>        self.organization = organization or os.environ.get("OPENAI_ORG_ID")<br>        self.project = project or os.environ.get("OPENAI_PROJECT_ID")<br>        self.endpoint = endpoint<br>        self.max_retries = max_retries<br>        self.base_delay = base_delay<br>        self.max_delay = max_delay<br>        # Keep a client open for connection pooling across multiple export calls<br>        self._client = httpx.Client(timeout=httpx.Timeout(timeout=60, connect=5.0))<br>    def set_api_key(self, api_key: str):<br>        """Set the OpenAI API key for the exporter.<br>        Args:<br>            api_key: The OpenAI API key to use. This is the same key used by the OpenAI Python<br>                client.<br>        """<br>        self.api_key = api_key<br>    def export(self, items: list[Trace | Span[Any]]) -> None:<br>        if not items:<br>            return<br>        if not self.api_key:<br>            logger.warning("OPENAI_API_KEY is not set, skipping trace export")<br>            return<br>        data = [item.export() for item in items if item.export()]<br>        payload = {"data": data}<br>        headers = {<br>            "Authorization": f"Bearer {self.api_key}",<br>            "Content-Type": "application/json",<br>            "OpenAI-Beta": "traces=v1",<br>        }<br>        # Exponential backoff loop<br>        attempt = 0<br>        delay = self.base_delay<br>        while True:<br>            attempt += 1<br>            try:<br>                response = self._client.post(url=self.endpoint, headers=headers, json=payload)<br>                # If the response is successful, break out of the loop<br>                if response.status_code < 300:<br>                    logger.debug(f"Exported {len(items)} items")<br>                    return<br>                # If the response is a client error (4xx), we wont retry<br>                if 400 <= response.status_code < 500:<br>                    logger.error(f"Tracing client error {response.status_code}: {response.text}")<br>                    return<br>                # For 5xx or other unexpected codes, treat it as transient and retry<br>                logger.warning(f"Server error {response.status_code}, retrying.")<br>            except httpx.RequestError as exc:<br>                # Network or other I/O error, we'll retry<br>                logger.warning(f"Request failed: {exc}")<br>            # If we reach here, we need to retry or give up<br>            if attempt >= self.max_retries:<br>                logger.error("Max retries reached, giving up on this batch.")<br>                return<br>            # Exponential backoff + jitter<br>            sleep_time = delay + random.uniform(0, 0.1 * delay)  # 10% jitter<br>            time.sleep(sleep_time)<br>            delay = min(delay * 2, self.max_delay)<br>    def close(self):<br>        """Close the underlying HTTP client."""<br>        self._client.close()<br>``` |

#### \_\_init\_\_

```md-code__content
__init__(
    api_key: str | None = None,
    organization: str | None = None,
    project: str | None = None,
    endpoint: str = "https://api.openai.com/v1/traces/ingest",
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
)

```

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `api_key` | `str | None` | The API key for the "Authorization" header. Defaults to<br>`os.environ["OPENAI_TRACE_API_KEY"]` if not provided. | `None` |
| `organization` | `str | None` | The OpenAI organization to use. Defaults to<br>`os.environ["OPENAI_ORG_ID"]` if not provided. | `None` |
| `project` | `str | None` | The OpenAI project to use. Defaults to<br>`os.environ["OPENAI_PROJECT_ID"]` if not provided. | `None` |
| `endpoint` | `str` | The HTTP endpoint to which traces/spans are posted. | `'https://api.openai.com/v1/traces/ingest'` |
| `max_retries` | `int` | Maximum number of retries upon failures. | `3` |
| `base_delay` | `float` | Base delay (in seconds) for the first backoff. | `1.0` |
| `max_delay` | `float` | Maximum delay (in seconds) for backoff growth. | `30.0` |

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>``` | ```md-code__content<br>def __init__(<br>    self,<br>    api_key: str | None = None,<br>    organization: str | None = None,<br>    project: str | None = None,<br>    endpoint: str = "https://api.openai.com/v1/traces/ingest",<br>    max_retries: int = 3,<br>    base_delay: float = 1.0,<br>    max_delay: float = 30.0,<br>):<br>    """<br>    Args:<br>        api_key: The API key for the "Authorization" header. Defaults to<br>            `os.environ["OPENAI_TRACE_API_KEY"]` if not provided.<br>        organization: The OpenAI organization to use. Defaults to<br>            `os.environ["OPENAI_ORG_ID"]` if not provided.<br>        project: The OpenAI project to use. Defaults to<br>            `os.environ["OPENAI_PROJECT_ID"]` if not provided.<br>        endpoint: The HTTP endpoint to which traces/spans are posted.<br>        max_retries: Maximum number of retries upon failures.<br>        base_delay: Base delay (in seconds) for the first backoff.<br>        max_delay: Maximum delay (in seconds) for backoff growth.<br>    """<br>    self.api_key = api_key or os.environ.get("OPENAI_API_KEY")<br>    self.organization = organization or os.environ.get("OPENAI_ORG_ID")<br>    self.project = project or os.environ.get("OPENAI_PROJECT_ID")<br>    self.endpoint = endpoint<br>    self.max_retries = max_retries<br>    self.base_delay = base_delay<br>    self.max_delay = max_delay<br>    # Keep a client open for connection pooling across multiple export calls<br>    self._client = httpx.Client(timeout=httpx.Timeout(timeout=60, connect=5.0))<br>``` |

#### set\_api\_key

```md-code__content
set_api_key(api_key: str)

```

Set the OpenAI API key for the exporter.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `api_key` | `str` | The OpenAI API key to use. This is the same key used by the OpenAI Python<br>client. | _required_ |

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br>64<br>65<br>66<br>67<br>68<br>69<br>70<br>71<br>``` | ```md-code__content<br>def set_api_key(self, api_key: str):<br>    """Set the OpenAI API key for the exporter.<br>    Args:<br>        api_key: The OpenAI API key to use. This is the same key used by the OpenAI Python<br>            client.<br>    """<br>    self.api_key = api_key<br>``` |

#### close

```md-code__content
close()

```

Close the underlying HTTP client.

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br>124<br>125<br>126<br>``` | ```md-code__content<br>def close(self):<br>    """Close the underlying HTTP client."""<br>    self._client.close()<br>``` |

### BatchTraceProcessor

Bases: `TracingProcessor`

Some implementation notes:
1\. Using Queue, which is thread-safe.
2\. Using a background thread to export spans, to minimize any performance issues.
3\. Spans are stored in memory until they are exported.

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br>129<br>130<br>131<br>132<br>133<br>134<br>135<br>136<br>137<br>138<br>139<br>140<br>141<br>142<br>143<br>144<br>145<br>146<br>147<br>148<br>149<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>157<br>158<br>159<br>160<br>161<br>162<br>163<br>164<br>165<br>166<br>167<br>168<br>169<br>170<br>171<br>172<br>173<br>174<br>175<br>176<br>177<br>178<br>179<br>180<br>181<br>182<br>183<br>184<br>185<br>186<br>187<br>188<br>189<br>190<br>191<br>192<br>193<br>194<br>195<br>196<br>197<br>198<br>199<br>200<br>201<br>202<br>203<br>204<br>205<br>206<br>207<br>208<br>209<br>210<br>211<br>212<br>213<br>214<br>215<br>216<br>217<br>218<br>219<br>220<br>221<br>222<br>223<br>224<br>225<br>226<br>227<br>228<br>229<br>230<br>231<br>232<br>233<br>234<br>235<br>236<br>237<br>238<br>239<br>240<br>241<br>242<br>243<br>``` | ```md-code__content<br>class BatchTraceProcessor(TracingProcessor):<br>    """Some implementation notes:<br>    1. Using Queue, which is thread-safe.<br>    2. Using a background thread to export spans, to minimize any performance issues.<br>    3. Spans are stored in memory until they are exported.<br>    """<br>    def __init__(<br>        self,<br>        exporter: TracingExporter,<br>        max_queue_size: int = 8192,<br>        max_batch_size: int = 128,<br>        schedule_delay: float = 5.0,<br>        export_trigger_ratio: float = 0.7,<br>    ):<br>        """<br>        Args:<br>            exporter: The exporter to use.<br>            max_queue_size: The maximum number of spans to store in the queue. After this, we will<br>                start dropping spans.<br>            max_batch_size: The maximum number of spans to export in a single batch.<br>            schedule_delay: The delay between checks for new spans to export.<br>            export_trigger_ratio: The ratio of the queue size at which we will trigger an export.<br>        """<br>        self._exporter = exporter<br>        self._queue: queue.Queue[Trace | Span[Any]] = queue.Queue(maxsize=max_queue_size)<br>        self._max_queue_size = max_queue_size<br>        self._max_batch_size = max_batch_size<br>        self._schedule_delay = schedule_delay<br>        self._shutdown_event = threading.Event()<br>        # The queue size threshold at which we export immediately.<br>        self._export_trigger_size = int(max_queue_size * export_trigger_ratio)<br>        # Track when we next *must* perform a scheduled export<br>        self._next_export_time = time.time() + self._schedule_delay<br>        self._shutdown_event = threading.Event()<br>        self._worker_thread = threading.Thread(target=self._run, daemon=True)<br>        self._worker_thread.start()<br>    def on_trace_start(self, trace: Trace) -> None:<br>        try:<br>            self._queue.put_nowait(trace)<br>        except queue.Full:<br>            logger.warning("Queue is full, dropping trace.")<br>    def on_trace_end(self, trace: Trace) -> None:<br>        # We send traces via on_trace_start, so we don't need to do anything here.<br>        pass<br>    def on_span_start(self, span: Span[Any]) -> None:<br>        # We send spans via on_span_end, so we don't need to do anything here.<br>        pass<br>    def on_span_end(self, span: Span[Any]) -> None:<br>        try:<br>            self._queue.put_nowait(span)<br>        except queue.Full:<br>            logger.warning("Queue is full, dropping span.")<br>    def shutdown(self, timeout: float | None = None):<br>        """<br>        Called when the application stops. We signal our thread to stop, then join it.<br>        """<br>        self._shutdown_event.set()<br>        self._worker_thread.join(timeout=timeout)<br>    def force_flush(self):<br>        """<br>        Forces an immediate flush of all queued spans.<br>        """<br>        self._export_batches(force=True)<br>    def _run(self):<br>        while not self._shutdown_event.is_set():<br>            current_time = time.time()<br>            queue_size = self._queue.qsize()<br>            # If it's time for a scheduled flush or queue is above the trigger threshold<br>            if current_time >= self._next_export_time or queue_size >= self._export_trigger_size:<br>                self._export_batches(force=False)<br>                # Reset the next scheduled flush time<br>                self._next_export_time = time.time() + self._schedule_delay<br>            else:<br>                # Sleep a short interval so we don't busy-wait.<br>                time.sleep(0.2)<br>        # Final drain after shutdown<br>        self._export_batches(force=True)<br>    def _export_batches(self, force: bool = False):<br>        """Drains the queue and exports in batches. If force=True, export everything.<br>        Otherwise, export up to `max_batch_size` repeatedly until the queue is empty or below a<br>        certain threshold.<br>        """<br>        while True:<br>            items_to_export: list[Span[Any] | Trace] = []<br>            # Gather a batch of spans up to max_batch_size<br>            while not self._queue.empty() and (<br>                force or len(items_to_export) < self._max_batch_size<br>            ):<br>                try:<br>                    items_to_export.append(self._queue.get_nowait())<br>                except queue.Empty:<br>                    # Another thread might have emptied the queue between checks<br>                    break<br>            # If we collected nothing, we're done<br>            if not items_to_export:<br>                break<br>            # Export the batch<br>            self._exporter.export(items_to_export)<br>``` |

#### \_\_init\_\_

```md-code__content
__init__(
    exporter: TracingExporter,
    max_queue_size: int = 8192,
    max_batch_size: int = 128,
    schedule_delay: float = 5.0,
    export_trigger_ratio: float = 0.7,
)

```

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `exporter` | `TracingExporter` | The exporter to use. | _required_ |
| `max_queue_size` | `int` | The maximum number of spans to store in the queue. After this, we will<br>start dropping spans. | `8192` |
| `max_batch_size` | `int` | The maximum number of spans to export in a single batch. | `128` |
| `schedule_delay` | `float` | The delay between checks for new spans to export. | `5.0` |
| `export_trigger_ratio` | `float` | The ratio of the queue size at which we will trigger an export. | `0.7` |

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br>136<br>137<br>138<br>139<br>140<br>141<br>142<br>143<br>144<br>145<br>146<br>147<br>148<br>149<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>157<br>158<br>159<br>160<br>161<br>162<br>163<br>164<br>165<br>166<br>167<br>168<br>``` | ```md-code__content<br>def __init__(<br>    self,<br>    exporter: TracingExporter,<br>    max_queue_size: int = 8192,<br>    max_batch_size: int = 128,<br>    schedule_delay: float = 5.0,<br>    export_trigger_ratio: float = 0.7,<br>):<br>    """<br>    Args:<br>        exporter: The exporter to use.<br>        max_queue_size: The maximum number of spans to store in the queue. After this, we will<br>            start dropping spans.<br>        max_batch_size: The maximum number of spans to export in a single batch.<br>        schedule_delay: The delay between checks for new spans to export.<br>        export_trigger_ratio: The ratio of the queue size at which we will trigger an export.<br>    """<br>    self._exporter = exporter<br>    self._queue: queue.Queue[Trace | Span[Any]] = queue.Queue(maxsize=max_queue_size)<br>    self._max_queue_size = max_queue_size<br>    self._max_batch_size = max_batch_size<br>    self._schedule_delay = schedule_delay<br>    self._shutdown_event = threading.Event()<br>    # The queue size threshold at which we export immediately.<br>    self._export_trigger_size = int(max_queue_size * export_trigger_ratio)<br>    # Track when we next *must* perform a scheduled export<br>    self._next_export_time = time.time() + self._schedule_delay<br>    self._shutdown_event = threading.Event()<br>    self._worker_thread = threading.Thread(target=self._run, daemon=True)<br>    self._worker_thread.start()<br>``` |

#### shutdown

```md-code__content
shutdown(timeout: float | None = None)

```

Called when the application stops. We signal our thread to stop, then join it.

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br>190<br>191<br>192<br>193<br>194<br>195<br>``` | ```md-code__content<br>def shutdown(self, timeout: float | None = None):<br>    """<br>    Called when the application stops. We signal our thread to stop, then join it.<br>    """<br>    self._shutdown_event.set()<br>    self._worker_thread.join(timeout=timeout)<br>``` |

#### force\_flush

```md-code__content
force_flush()

```

Forces an immediate flush of all queued spans.

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br>197<br>198<br>199<br>200<br>201<br>``` | ```md-code__content<br>def force_flush(self):<br>    """<br>    Forces an immediate flush of all queued spans.<br>    """<br>    self._export_batches(force=True)<br>``` |

#### \_export\_batches

```md-code__content
_export_batches(force: bool = False)

```

Drains the queue and exports in batches. If force=True, export everything.
Otherwise, export up to `max_batch_size` repeatedly until the queue is empty or below a
certain threshold.

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br>220<br>221<br>222<br>223<br>224<br>225<br>226<br>227<br>228<br>229<br>230<br>231<br>232<br>233<br>234<br>235<br>236<br>237<br>238<br>239<br>240<br>241<br>242<br>243<br>``` | ```md-code__content<br>def _export_batches(self, force: bool = False):<br>    """Drains the queue and exports in batches. If force=True, export everything.<br>    Otherwise, export up to `max_batch_size` repeatedly until the queue is empty or below a<br>    certain threshold.<br>    """<br>    while True:<br>        items_to_export: list[Span[Any] | Trace] = []<br>        # Gather a batch of spans up to max_batch_size<br>        while not self._queue.empty() and (<br>            force or len(items_to_export) < self._max_batch_size<br>        ):<br>            try:<br>                items_to_export.append(self._queue.get_nowait())<br>            except queue.Empty:<br>                # Another thread might have emptied the queue between checks<br>                break<br>        # If we collected nothing, we're done<br>        if not items_to_export:<br>            break<br>        # Export the batch<br>        self._exporter.export(items_to_export)<br>``` |

### default\_exporter

```md-code__content
default_exporter() -> BackendSpanExporter

```

The default exporter, which exports traces and spans to the backend in batches.

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br>251<br>252<br>253<br>``` | ```md-code__content<br>def default_exporter() -> BackendSpanExporter:<br>    """The default exporter, which exports traces and spans to the backend in batches."""<br>    return _global_exporter<br>``` |

### default\_processor

```md-code__content
default_processor() -> BatchTraceProcessor

```

The default processor, which exports traces and spans to the backend in batches.

Source code in `src/agents/tracing/processors.py`

|     |     |
| --- | --- |
| ```<br>256<br>257<br>258<br>``` | ```md-code__content<br>def default_processor() -> BatchTraceProcessor:<br>    """The default processor, which exports traces and spans to the backend in batches."""<br>    return _global_processor<br>``` |