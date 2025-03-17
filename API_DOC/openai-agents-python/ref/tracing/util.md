[Skip to content](https://openai.github.io/openai-agents-python/ref/tracing/util/#util)

# `Util`

### time\_iso

```md-code__content
time_iso() -> str

```

Returns the current time in ISO 8601 format.

Source code in `src/agents/tracing/util.py`

|     |     |
| --- | --- |
| ```<br>5<br>6<br>7<br>``` | ```md-code__content<br>def time_iso() -> str:<br>    """Returns the current time in ISO 8601 format."""<br>    return datetime.now(timezone.utc).isoformat()<br>``` |

### gen\_trace\_id

```md-code__content
gen_trace_id() -> str

```

Generates a new trace ID.

Source code in `src/agents/tracing/util.py`

|     |     |
| --- | --- |
| ```<br>10<br>11<br>12<br>``` | ```md-code__content<br>def gen_trace_id() -> str:<br>    """Generates a new trace ID."""<br>    return f"trace_{uuid.uuid4().hex}"<br>``` |

### gen\_span\_id

```md-code__content
gen_span_id() -> str

```

Generates a new span ID.

Source code in `src/agents/tracing/util.py`

|     |     |
| --- | --- |
| ```<br>15<br>16<br>17<br>``` | ```md-code__content<br>def gen_span_id() -> str:<br>    """Generates a new span ID."""<br>    return f"span_{uuid.uuid4().hex[:24]}"<br>``` |