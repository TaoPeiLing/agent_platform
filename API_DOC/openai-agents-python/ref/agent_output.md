[Skip to content](https://openai.github.io/openai-agents-python/ref/agent_output/#agent-output)

# `Agent output`

### AgentOutputSchema`dataclass`

An object that captures the JSON schema of the output, as well as validating/parsing JSON
produced by the LLM into the output type.

Source code in `src/agents/agent_output.py`

|     |     |
| --- | --- |
| ```<br> 15<br> 16<br> 17<br> 18<br> 19<br> 20<br> 21<br> 22<br> 23<br> 24<br> 25<br> 26<br> 27<br> 28<br> 29<br> 30<br> 31<br> 32<br> 33<br> 34<br> 35<br> 36<br> 37<br> 38<br> 39<br> 40<br> 41<br> 42<br> 43<br> 44<br> 45<br> 46<br> 47<br> 48<br> 49<br> 50<br> 51<br> 52<br> 53<br> 54<br> 55<br> 56<br> 57<br> 58<br> 59<br> 60<br> 61<br> 62<br> 63<br> 64<br> 65<br> 66<br> 67<br> 68<br> 69<br> 70<br> 71<br> 72<br> 73<br> 74<br> 75<br> 76<br> 77<br> 78<br> 79<br> 80<br> 81<br> 82<br> 83<br> 84<br> 85<br> 86<br> 87<br> 88<br> 89<br> 90<br> 91<br> 92<br> 93<br> 94<br> 95<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>108<br>109<br>110<br>111<br>112<br>113<br>114<br>115<br>116<br>117<br>118<br>``` | ```md-code__content<br>@dataclass(init=False)<br>class AgentOutputSchema:<br>    """An object that captures the JSON schema of the output, as well as validating/parsing JSON<br>    produced by the LLM into the output type.<br>    """<br>    output_type: type[Any]<br>    """The type of the output."""<br>    _type_adapter: TypeAdapter[Any]<br>    """A type adapter that wraps the output type, so that we can validate JSON."""<br>    _is_wrapped: bool<br>    """Whether the output type is wrapped in a dictionary. This is generally done if the base<br>    output type cannot be represented as a JSON Schema object.<br>    """<br>    _output_schema: dict[str, Any]<br>    """The JSON schema of the output."""<br>    strict_json_schema: bool<br>    """Whether the JSON schema is in strict mode. We **strongly** recommend setting this to True,<br>    as it increases the likelihood of correct JSON input.<br>    """<br>    def __init__(self, output_type: type[Any], strict_json_schema: bool = True):<br>        """<br>        Args:<br>            output_type: The type of the output.<br>            strict_json_schema: Whether the JSON schema is in strict mode. We **strongly** recommend<br>                setting this to True, as it increases the likelihood of correct JSON input.<br>        """<br>        self.output_type = output_type<br>        self.strict_json_schema = strict_json_schema<br>        if output_type is None or output_type is str:<br>            self._is_wrapped = False<br>            self._type_adapter = TypeAdapter(output_type)<br>            self._output_schema = self._type_adapter.json_schema()<br>            return<br>        # We should wrap for things that are not plain text, and for things that would definitely<br>        # not be a JSON Schema object.<br>        self._is_wrapped = not _is_subclass_of_base_model_or_dict(output_type)<br>        if self._is_wrapped:<br>            OutputType = TypedDict(<br>                "OutputType",<br>                {<br>                    _WRAPPER_DICT_KEY: output_type,  # type: ignore<br>                },<br>            )<br>            self._type_adapter = TypeAdapter(OutputType)<br>            self._output_schema = self._type_adapter.json_schema()<br>        else:<br>            self._type_adapter = TypeAdapter(output_type)<br>            self._output_schema = self._type_adapter.json_schema()<br>        if self.strict_json_schema:<br>            self._output_schema = ensure_strict_json_schema(self._output_schema)<br>    def is_plain_text(self) -> bool:<br>        """Whether the output type is plain text (versus a JSON object)."""<br>        return self.output_type is None or self.output_type is str<br>    def json_schema(self) -> dict[str, Any]:<br>        """The JSON schema of the output type."""<br>        if self.is_plain_text():<br>            raise UserError("Output type is plain text, so no JSON schema is available")<br>        return self._output_schema<br>    def validate_json(self, json_str: str, partial: bool = False) -> Any:<br>        """Validate a JSON string against the output type. Returns the validated object, or raises<br>        a `ModelBehaviorError` if the JSON is invalid.<br>        """<br>        validated = _utils.validate_json(json_str, self._type_adapter, partial)<br>        if self._is_wrapped:<br>            if not isinstance(validated, dict):<br>                _utils.attach_error_to_current_span(<br>                    SpanError(<br>                        message="Invalid JSON",<br>                        data={"details": f"Expected a dict, got {type(validated)}"},<br>                    )<br>                )<br>                raise ModelBehaviorError(<br>                    f"Expected a dict, got {type(validated)} for JSON: {json_str}"<br>                )<br>            if _WRAPPER_DICT_KEY not in validated:<br>                _utils.attach_error_to_current_span(<br>                    SpanError(<br>                        message="Invalid JSON",<br>                        data={"details": f"Could not find key {_WRAPPER_DICT_KEY} in JSON"},<br>                    )<br>                )<br>                raise ModelBehaviorError(<br>                    f"Could not find key {_WRAPPER_DICT_KEY} in JSON: {json_str}"<br>                )<br>            return validated[_WRAPPER_DICT_KEY]<br>        return validated<br>    def output_type_name(self) -> str:<br>        """The name of the output type."""<br>        return _type_to_str(self.output_type)<br>``` |

#### \_type\_adapter`instance-attribute`

```md-code__content
_type_adapter: TypeAdapter[Any]

```

A type adapter that wraps the output type, so that we can validate JSON.

#### \_output\_schema`instance-attribute`

```md-code__content
_output_schema: dict[str, Any]

```

The JSON schema of the output.

#### output\_type`instance-attribute`

```md-code__content
output_type: type[Any] = output_type

```

The type of the output.

#### strict\_json\_schema`instance-attribute`

```md-code__content
strict_json_schema: bool = strict_json_schema

```

Whether the JSON schema is in strict mode. We **strongly** recommend setting this to True,
as it increases the likelihood of correct JSON input.

#### \_is\_wrapped`instance-attribute`

```md-code__content
_is_wrapped: bool = not _is_subclass_of_base_model_or_dict(
    output_type
)

```

Whether the output type is wrapped in a dictionary. This is generally done if the base
output type cannot be represented as a JSON Schema object.

#### \_\_init\_\_

```md-code__content
__init__(
    output_type: type[Any], strict_json_schema: bool = True
)

```

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `output_type` | `type[Any]` | The type of the output. | _required_ |
| `strict_json_schema` | `bool` | Whether the JSON schema is in strict mode. We **strongly** recommend<br>setting this to True, as it increases the likelihood of correct JSON input. | `True` |

Source code in `src/agents/agent_output.py`

|     |     |
| --- | --- |
| ```<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>69<br>70<br>71<br>72<br>73<br>74<br>``` | ```md-code__content<br>def __init__(self, output_type: type[Any], strict_json_schema: bool = True):<br>    """<br>    Args:<br>        output_type: The type of the output.<br>        strict_json_schema: Whether the JSON schema is in strict mode. We **strongly** recommend<br>            setting this to True, as it increases the likelihood of correct JSON input.<br>    """<br>    self.output_type = output_type<br>    self.strict_json_schema = strict_json_schema<br>    if output_type is None or output_type is str:<br>        self._is_wrapped = False<br>        self._type_adapter = TypeAdapter(output_type)<br>        self._output_schema = self._type_adapter.json_schema()<br>        return<br>    # We should wrap for things that are not plain text, and for things that would definitely<br>    # not be a JSON Schema object.<br>    self._is_wrapped = not _is_subclass_of_base_model_or_dict(output_type)<br>    if self._is_wrapped:<br>        OutputType = TypedDict(<br>            "OutputType",<br>            {<br>                _WRAPPER_DICT_KEY: output_type,  # type: ignore<br>            },<br>        )<br>        self._type_adapter = TypeAdapter(OutputType)<br>        self._output_schema = self._type_adapter.json_schema()<br>    else:<br>        self._type_adapter = TypeAdapter(output_type)<br>        self._output_schema = self._type_adapter.json_schema()<br>    if self.strict_json_schema:<br>        self._output_schema = ensure_strict_json_schema(self._output_schema)<br>``` |

#### is\_plain\_text

```md-code__content
is_plain_text() -> bool

```

Whether the output type is plain text (versus a JSON object).

Source code in `src/agents/agent_output.py`

|     |     |
| --- | --- |
| ```<br>76<br>77<br>78<br>``` | ```md-code__content<br>def is_plain_text(self) -> bool:<br>    """Whether the output type is plain text (versus a JSON object)."""<br>    return self.output_type is None or self.output_type is str<br>``` |

#### json\_schema

```md-code__content
json_schema() -> dict[str, Any]

```

The JSON schema of the output type.

Source code in `src/agents/agent_output.py`

|     |     |
| --- | --- |
| ```<br>80<br>81<br>82<br>83<br>84<br>``` | ```md-code__content<br>def json_schema(self) -> dict[str, Any]:<br>    """The JSON schema of the output type."""<br>    if self.is_plain_text():<br>        raise UserError("Output type is plain text, so no JSON schema is available")<br>    return self._output_schema<br>``` |

#### validate\_json

```md-code__content
validate_json(json_str: str, partial: bool = False) -> Any

```

Validate a JSON string against the output type. Returns the validated object, or raises
a `ModelBehaviorError` if the JSON is invalid.

Source code in `src/agents/agent_output.py`

|     |     |
| --- | --- |
| ```<br> 86<br> 87<br> 88<br> 89<br> 90<br> 91<br> 92<br> 93<br> 94<br> 95<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>108<br>109<br>110<br>111<br>112<br>113<br>114<br>``` | ```md-code__content<br>def validate_json(self, json_str: str, partial: bool = False) -> Any:<br>    """Validate a JSON string against the output type. Returns the validated object, or raises<br>    a `ModelBehaviorError` if the JSON is invalid.<br>    """<br>    validated = _utils.validate_json(json_str, self._type_adapter, partial)<br>    if self._is_wrapped:<br>        if not isinstance(validated, dict):<br>            _utils.attach_error_to_current_span(<br>                SpanError(<br>                    message="Invalid JSON",<br>                    data={"details": f"Expected a dict, got {type(validated)}"},<br>                )<br>            )<br>            raise ModelBehaviorError(<br>                f"Expected a dict, got {type(validated)} for JSON: {json_str}"<br>            )<br>        if _WRAPPER_DICT_KEY not in validated:<br>            _utils.attach_error_to_current_span(<br>                SpanError(<br>                    message="Invalid JSON",<br>                    data={"details": f"Could not find key {_WRAPPER_DICT_KEY} in JSON"},<br>                )<br>            )<br>            raise ModelBehaviorError(<br>                f"Could not find key {_WRAPPER_DICT_KEY} in JSON: {json_str}"<br>            )<br>        return validated[_WRAPPER_DICT_KEY]<br>    return validated<br>``` |

#### output\_type\_name

```md-code__content
output_type_name() -> str

```

The name of the output type.

Source code in `src/agents/agent_output.py`

|     |     |
| --- | --- |
| ```<br>116<br>117<br>118<br>``` | ```md-code__content<br>def output_type_name(self) -> str:<br>    """The name of the output type."""<br>    return _type_to_str(self.output_type)<br>``` |