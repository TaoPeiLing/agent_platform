[Skip to content](https://openai.github.io/openai-agents-python/ref/usage/#usage)

# `Usage`

### Usage`dataclass`

Source code in `src/agents/usage.py`

|     |     |
| --- | --- |
| ```<br> 4<br> 5<br> 6<br> 7<br> 8<br> 9<br>10<br>11<br>12<br>13<br>14<br>15<br>16<br>17<br>18<br>19<br>20<br>21<br>22<br>``` | ```md-code__content<br>@dataclass<br>class Usage:<br>    requests: int = 0<br>    """Total requests made to the LLM API."""<br>    input_tokens: int = 0<br>    """Total input tokens sent, across all requests."""<br>    output_tokens: int = 0<br>    """Total output tokens received, across all requests."""<br>    total_tokens: int = 0<br>    """Total tokens sent and received, across all requests."""<br>    def add(self, other: "Usage") -> None:<br>        self.requests += other.requests if other.requests else 0<br>        self.input_tokens += other.input_tokens if other.input_tokens else 0<br>        self.output_tokens += other.output_tokens if other.output_tokens else 0<br>        self.total_tokens += other.total_tokens if other.total_tokens else 0<br>``` |

#### requests`class-attribute``instance-attribute`

```md-code__content
requests: int = 0

```

Total requests made to the LLM API.

#### input\_tokens`class-attribute``instance-attribute`

```md-code__content
input_tokens: int = 0

```

Total input tokens sent, across all requests.

#### output\_tokens`class-attribute``instance-attribute`

```md-code__content
output_tokens: int = 0

```

Total output tokens received, across all requests.

#### total\_tokens`class-attribute``instance-attribute`

```md-code__content
total_tokens: int = 0

```

Total tokens sent and received, across all requests.