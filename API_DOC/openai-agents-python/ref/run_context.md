[Skip to content](https://openai.github.io/openai-agents-python/ref/run_context/#run-context)

# `Run context`

### RunContextWrapper`dataclass`

Bases: `Generic[TContext]`

This wraps the context object that you passed to `Runner.run()`. It also contains
information about the usage of the agent run so far.

NOTE: Contexts are not passed to the LLM. They're a way to pass dependencies and data to code
you implement, like tool functions, callbacks, hooks, etc.

Source code in `src/agents/run_context.py`

|     |     |
| --- | --- |
| ```<br>11<br>12<br>13<br>14<br>15<br>16<br>17<br>18<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>``` | ```md-code__content<br>@dataclass<br>class RunContextWrapper(Generic[TContext]):<br>    """This wraps the context object that you passed to `Runner.run()`. It also contains<br>    information about the usage of the agent run so far.<br>    NOTE: Contexts are not passed to the LLM. They're a way to pass dependencies and data to code<br>    you implement, like tool functions, callbacks, hooks, etc.<br>    """<br>    context: TContext<br>    """The context object (or None), passed by you to `Runner.run()`"""<br>    usage: Usage = field(default_factory=Usage)<br>    """The usage of the agent run so far. For streamed responses, the usage will be stale until the<br>    last chunk of the stream is processed.<br>    """<br>``` |

#### context`instance-attribute`

```md-code__content
context: TContext

```

The context object (or None), passed by you to `Runner.run()`

#### usage`class-attribute``instance-attribute`

```md-code__content
usage: Usage = field(default_factory=Usage)

```

The usage of the agent run so far. For streamed responses, the usage will be stale until the
last chunk of the stream is processed.