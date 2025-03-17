[Skip to content](https://openai.github.io/openai-agents-python/ref/models/interface/#model-interface)

# `Model interface`

### ModelTracing

Bases: `Enum`

Source code in `src/agents/models/interface.py`

|     |     |
| --- | --- |
| ```<br>17<br>18<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>``` | ```md-code__content<br>class ModelTracing(enum.Enum):<br>    DISABLED = 0<br>    """Tracing is disabled entirely."""<br>    ENABLED = 1<br>    """Tracing is enabled, and all data is included."""<br>    ENABLED_WITHOUT_DATA = 2<br>    """Tracing is enabled, but inputs/outputs are not included."""<br>    def is_disabled(self) -> bool:<br>        return self == ModelTracing.DISABLED<br>    def include_data(self) -> bool:<br>        return self == ModelTracing.ENABLED<br>``` |

#### DISABLED`class-attribute``instance-attribute`

```md-code__content
DISABLED = 0

```

Tracing is disabled entirely.

#### ENABLED`class-attribute``instance-attribute`

```md-code__content
ENABLED = 1

```

Tracing is enabled, and all data is included.

#### ENABLED\_WITHOUT\_DATA`class-attribute``instance-attribute`

```md-code__content
ENABLED_WITHOUT_DATA = 2

```

Tracing is enabled, but inputs/outputs are not included.

### Model

Bases: `ABC`

The base interface for calling an LLM.

Source code in `src/agents/models/interface.py`

|     |     |
| --- | --- |
| ```<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>69<br>70<br>71<br>72<br>73<br>74<br>75<br>76<br>77<br>78<br>79<br>80<br>81<br>82<br>83<br>84<br>85<br>86<br>87<br>88<br>89<br>``` | ```md-code__content<br>class Model(abc.ABC):<br>    """The base interface for calling an LLM."""<br>    @abc.abstractmethod<br>    async def get_response(<br>        self,<br>        system_instructions: str | None,<br>        input: str | list[TResponseInputItem],<br>        model_settings: ModelSettings,<br>        tools: list[Tool],<br>        output_schema: AgentOutputSchema | None,<br>        handoffs: list[Handoff],<br>        tracing: ModelTracing,<br>    ) -> ModelResponse:<br>        """Get a response from the model.<br>        Args:<br>            system_instructions: The system instructions to use.<br>            input: The input items to the model, in OpenAI Responses format.<br>            model_settings: The model settings to use.<br>            tools: The tools available to the model.<br>            output_schema: The output schema to use.<br>            handoffs: The handoffs available to the model.<br>            tracing: Tracing configuration.<br>        Returns:<br>            The full model response.<br>        """<br>        pass<br>    @abc.abstractmethod<br>    def stream_response(<br>        self,<br>        system_instructions: str | None,<br>        input: str | list[TResponseInputItem],<br>        model_settings: ModelSettings,<br>        tools: list[Tool],<br>        output_schema: AgentOutputSchema | None,<br>        handoffs: list[Handoff],<br>        tracing: ModelTracing,<br>    ) -> AsyncIterator[TResponseStreamEvent]:<br>        """Stream a response from the model.<br>        Args:<br>            system_instructions: The system instructions to use.<br>            input: The input items to the model, in OpenAI Responses format.<br>            model_settings: The model settings to use.<br>            tools: The tools available to the model.<br>            output_schema: The output schema to use.<br>            handoffs: The handoffs available to the model.<br>            tracing: Tracing configuration.<br>        Returns:<br>            An iterator of response stream events, in OpenAI Responses format.<br>        """<br>        pass<br>``` |

#### get\_response`abstractmethod``async`

```md-code__content
get_response(
    system_instructions: str | None,
    input: str | list[TResponseInputItem],
    model_settings: ModelSettings,
    tools: list[Tool],
    output_schema: AgentOutputSchema | None,
    handoffs: list[Handoff],
    tracing: ModelTracing,
) -> ModelResponse

```

Get a response from the model.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `system_instructions` | `str | None` | The system instructions to use. | _required_ |
| `input` | `str | list[TResponseInputItem]` | The input items to the model, in OpenAI Responses format. | _required_ |
| `model_settings` | `ModelSettings` | The model settings to use. | _required_ |
| `tools` | `list[Tool]` | The tools available to the model. | _required_ |
| `output_schema` | `AgentOutputSchema | None` | The output schema to use. | _required_ |
| `handoffs` | `list[Handoff]` | The handoffs available to the model. | _required_ |
| `tracing` | `ModelTracing` | Tracing configuration. | _required_ |

Returns:

| Type | Description |
| --- | --- |
| `ModelResponse` | The full model response. |

Source code in `src/agents/models/interface.py`

|     |     |
| --- | --- |
| ```<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>``` | ```md-code__content<br>@abc.abstractmethod<br>async def get_response(<br>    self,<br>    system_instructions: str | None,<br>    input: str | list[TResponseInputItem],<br>    model_settings: ModelSettings,<br>    tools: list[Tool],<br>    output_schema: AgentOutputSchema | None,<br>    handoffs: list[Handoff],<br>    tracing: ModelTracing,<br>) -> ModelResponse:<br>    """Get a response from the model.<br>    Args:<br>        system_instructions: The system instructions to use.<br>        input: The input items to the model, in OpenAI Responses format.<br>        model_settings: The model settings to use.<br>        tools: The tools available to the model.<br>        output_schema: The output schema to use.<br>        handoffs: The handoffs available to the model.<br>        tracing: Tracing configuration.<br>    Returns:<br>        The full model response.<br>    """<br>    pass<br>``` |

#### stream\_response`abstractmethod`

```md-code__content
stream_response(
    system_instructions: str | None,
    input: str | list[TResponseInputItem],
    model_settings: ModelSettings,
    tools: list[Tool],
    output_schema: AgentOutputSchema | None,
    handoffs: list[Handoff],
    tracing: ModelTracing,
) -> AsyncIterator[TResponseStreamEvent]

```

Stream a response from the model.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `system_instructions` | `str | None` | The system instructions to use. | _required_ |
| `input` | `str | list[TResponseInputItem]` | The input items to the model, in OpenAI Responses format. | _required_ |
| `model_settings` | `ModelSettings` | The model settings to use. | _required_ |
| `tools` | `list[Tool]` | The tools available to the model. | _required_ |
| `output_schema` | `AgentOutputSchema | None` | The output schema to use. | _required_ |
| `handoffs` | `list[Handoff]` | The handoffs available to the model. | _required_ |
| `tracing` | `ModelTracing` | Tracing configuration. | _required_ |

Returns:

| Type | Description |
| --- | --- |
| `AsyncIterator[TResponseStreamEvent]` | An iterator of response stream events, in OpenAI Responses format. |

Source code in `src/agents/models/interface.py`

|     |     |
| --- | --- |
| ```<br>64<br>65<br>66<br>67<br>68<br>69<br>70<br>71<br>72<br>73<br>74<br>75<br>76<br>77<br>78<br>79<br>80<br>81<br>82<br>83<br>84<br>85<br>86<br>87<br>88<br>89<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def stream_response(<br>    self,<br>    system_instructions: str | None,<br>    input: str | list[TResponseInputItem],<br>    model_settings: ModelSettings,<br>    tools: list[Tool],<br>    output_schema: AgentOutputSchema | None,<br>    handoffs: list[Handoff],<br>    tracing: ModelTracing,<br>) -> AsyncIterator[TResponseStreamEvent]:<br>    """Stream a response from the model.<br>    Args:<br>        system_instructions: The system instructions to use.<br>        input: The input items to the model, in OpenAI Responses format.<br>        model_settings: The model settings to use.<br>        tools: The tools available to the model.<br>        output_schema: The output schema to use.<br>        handoffs: The handoffs available to the model.<br>        tracing: Tracing configuration.<br>    Returns:<br>        An iterator of response stream events, in OpenAI Responses format.<br>    """<br>    pass<br>``` |

### ModelProvider

Bases: `ABC`

The base interface for a model provider.

Model provider is responsible for looking up Models by name.

Source code in `src/agents/models/interface.py`

|     |     |
| --- | --- |
| ```<br> 92<br> 93<br> 94<br> 95<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>``` | ```md-code__content<br>class ModelProvider(abc.ABC):<br>    """The base interface for a model provider.<br>    Model provider is responsible for looking up Models by name.<br>    """<br>    @abc.abstractmethod<br>    def get_model(self, model_name: str | None) -> Model:<br>        """Get a model by name.<br>        Args:<br>            model_name: The name of the model to get.<br>        Returns:<br>            The model.<br>        """<br>``` |

#### get\_model`abstractmethod`

```md-code__content
get_model(model_name: str | None) -> Model

```

Get a model by name.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `model_name` | `str | None` | The name of the model to get. | _required_ |

Returns:

| Type | Description |
| --- | --- |
| `Model` | The model. |

Source code in `src/agents/models/interface.py`

|     |     |
| --- | --- |
| ```<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>``` | ```md-code__content<br>@abc.abstractmethod<br>def get_model(self, model_name: str | None) -> Model:<br>    """Get a model by name.<br>    Args:<br>        model_name: The name of the model to get.<br>    Returns:<br>        The model.<br>    """<br>``` |