[Skip to content](https://openai.github.io/openai-agents-python/ref/tool/#tools)

# `Tools`

### Tool`module-attribute`

```md-code__content
Tool = Union[\
    FunctionTool,\
    FileSearchTool,\
    WebSearchTool,\
    ComputerTool,\
]

```

A tool that can be used in an agent.

### FunctionTool`dataclass`

A tool that wraps a function. In most cases, you should use the `function_tool` helpers to
create a FunctionTool, as they let you easily wrap a Python function.

Source code in `src/agents/tool.py`

|     |     |
| --- | --- |
| ```<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>``` | ```md-code__content<br>@dataclass<br>class FunctionTool:<br>    """A tool that wraps a function. In most cases, you should use  the `function_tool` helpers to<br>    create a FunctionTool, as they let you easily wrap a Python function.<br>    """<br>    name: str<br>    """The name of the tool, as shown to the LLM. Generally the name of the function."""<br>    description: str<br>    """A description of the tool, as shown to the LLM."""<br>    params_json_schema: dict[str, Any]<br>    """The JSON schema for the tool's parameters."""<br>    on_invoke_tool: Callable[[RunContextWrapper[Any], str], Awaitable[str]]<br>    """A function that invokes the tool with the given context and parameters. The params passed<br>    are:<br>    1. The tool run context.<br>    2. The arguments from the LLM, as a JSON string.<br>    You must return a string representation of the tool output. In case of errors, you can either<br>    raise an Exception (which will cause the run to fail) or return a string error message (which<br>    will be sent back to the LLM).<br>    """<br>    strict_json_schema: bool = True<br>    """Whether the JSON schema is in strict mode. We **strongly** recommend setting this to True,<br>    as it increases the likelihood of correct JSON input."""<br>``` |

#### name`instance-attribute`

```md-code__content
name: str

```

The name of the tool, as shown to the LLM. Generally the name of the function.

#### description`instance-attribute`

```md-code__content
description: str

```

A description of the tool, as shown to the LLM.

#### params\_json\_schema`instance-attribute`

```md-code__content
params_json_schema: dict[str, Any]

```

The JSON schema for the tool's parameters.

#### on\_invoke\_tool`instance-attribute`

```md-code__content
on_invoke_tool: Callable[\
    [RunContextWrapper[Any], str], Awaitable[str]\
]

```

A function that invokes the tool with the given context and parameters. The params passed
are:
1\. The tool run context.
2\. The arguments from the LLM, as a JSON string.

You must return a string representation of the tool output. In case of errors, you can either
raise an Exception (which will cause the run to fail) or return a string error message (which
will be sent back to the LLM).

#### strict\_json\_schema`class-attribute``instance-attribute`

```md-code__content
strict_json_schema: bool = True

```

Whether the JSON schema is in strict mode. We **strongly** recommend setting this to True,
as it increases the likelihood of correct JSON input.

### FileSearchTool`dataclass`

A hosted tool that lets the LLM search through a vector store. Currently only supported with
OpenAI models, using the Responses API.

Source code in `src/agents/tool.py`

|     |     |
| --- | --- |
| ```<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>69<br>70<br>71<br>72<br>73<br>74<br>75<br>76<br>77<br>78<br>79<br>80<br>81<br>82<br>83<br>84<br>85<br>``` | ```md-code__content<br>@dataclass<br>class FileSearchTool:<br>    """A hosted tool that lets the LLM search through a vector store. Currently only supported with<br>    OpenAI models, using the Responses API.<br>    """<br>    vector_store_ids: list[str]<br>    """The IDs of the vector stores to search."""<br>    max_num_results: int | None = None<br>    """The maximum number of results to return."""<br>    include_search_results: bool = False<br>    """Whether to include the search results in the output produced by the LLM."""<br>    ranking_options: RankingOptions | None = None<br>    """Ranking options for search."""<br>    filters: Filters | None = None<br>    """A filter to apply based on file attributes."""<br>    @property<br>    def name(self):<br>        return "file_search"<br>``` |

#### vector\_store\_ids`instance-attribute`

```md-code__content
vector_store_ids: list[str]

```

The IDs of the vector stores to search.

#### max\_num\_results`class-attribute``instance-attribute`

```md-code__content
max_num_results: int | None = None

```

The maximum number of results to return.

#### include\_search\_results`class-attribute``instance-attribute`

```md-code__content
include_search_results: bool = False

```

Whether to include the search results in the output produced by the LLM.

#### ranking\_options`class-attribute``instance-attribute`

```md-code__content
ranking_options: RankingOptions | None = None

```

Ranking options for search.

#### filters`class-attribute``instance-attribute`

```md-code__content
filters: Filters | None = None

```

A filter to apply based on file attributes.

### WebSearchTool`dataclass`

A hosted tool that lets the LLM search the web. Currently only supported with OpenAI models,
using the Responses API.

Source code in `src/agents/tool.py`

|     |     |
| --- | --- |
| ```<br> 88<br> 89<br> 90<br> 91<br> 92<br> 93<br> 94<br> 95<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>``` | ```md-code__content<br>@dataclass<br>class WebSearchTool:<br>    """A hosted tool that lets the LLM search the web. Currently only supported with OpenAI models,<br>    using the Responses API.<br>    """<br>    user_location: UserLocation | None = None<br>    """Optional location for the search. Lets you customize results to be relevant to a location."""<br>    search_context_size: Literal["low", "medium", "high"] = "medium"<br>    """The amount of context to use for the search."""<br>    @property<br>    def name(self):<br>        return "web_search_preview"<br>``` |

#### user\_location`class-attribute``instance-attribute`

```md-code__content
user_location: UserLocation | None = None

```

Optional location for the search. Lets you customize results to be relevant to a location.

#### search\_context\_size`class-attribute``instance-attribute`

```md-code__content
search_context_size: Literal["low", "medium", "high"] = (
    "medium"
)

```

The amount of context to use for the search.

### ComputerTool`dataclass`

A hosted tool that lets the LLM control a computer.

Source code in `src/agents/tool.py`

|     |     |
| --- | --- |
| ```<br>105<br>106<br>107<br>108<br>109<br>110<br>111<br>112<br>113<br>114<br>115<br>116<br>``` | ```md-code__content<br>@dataclass<br>class ComputerTool:<br>    """A hosted tool that lets the LLM control a computer."""<br>    computer: Computer | AsyncComputer<br>    """The computer implementation, which describes the environment and dimensions of the computer,<br>    as well as implements the computer actions like click, screenshot, etc.<br>    """<br>    @property<br>    def name(self):<br>        return "computer_use_preview"<br>``` |

#### computer`instance-attribute`

```md-code__content
computer: Computer | AsyncComputer

```

The computer implementation, which describes the environment and dimensions of the computer,
as well as implements the computer actions like click, screenshot, etc.

### default\_tool\_error\_function

```md-code__content
default_tool_error_function(
    ctx: RunContextWrapper[Any], error: Exception
) -> str

```

The default tool error function, which just returns a generic error message.

Source code in `src/agents/tool.py`

|     |     |
| --- | --- |
| ```<br>123<br>124<br>125<br>``` | ```md-code__content<br>def default_tool_error_function(ctx: RunContextWrapper[Any], error: Exception) -> str:<br>    """The default tool error function, which just returns a generic error message."""<br>    return f"An error occurred while running the tool. Please try again. Error: {str(error)}"<br>``` |

### function\_tool

```md-code__content
function_tool(
    func: ToolFunction[...],
    *,
    name_override: str | None = None,
    description_override: str | None = None,
    docstring_style: DocstringStyle | None = None,
    use_docstring_info: bool = True,
    failure_error_function: ToolErrorFunction | None = None,
) -> FunctionTool

```

```md-code__content
function_tool(
    *,
    name_override: str | None = None,
    description_override: str | None = None,
    docstring_style: DocstringStyle | None = None,
    use_docstring_info: bool = True,
    failure_error_function: ToolErrorFunction | None = None,
) -> Callable[[ToolFunction[...]], FunctionTool]

```

```md-code__content
function_tool(
    func: ToolFunction[...] | None = None,
    *,
    name_override: str | None = None,
    description_override: str | None = None,
    docstring_style: DocstringStyle | None = None,
    use_docstring_info: bool = True,
    failure_error_function: ToolErrorFunction
    | None = default_tool_error_function,
) -> (
    FunctionTool
    | Callable[[ToolFunction[...]], FunctionTool]
)

```

Decorator to create a FunctionTool from a function. By default, we will:
1\. Parse the function signature to create a JSON schema for the tool's parameters.
2\. Use the function's docstring to populate the tool's description.
3\. Use the function's docstring to populate argument descriptions.
The docstring style is detected automatically, but you can override it.

If the function takes a `RunContextWrapper` as the first argument, it _must_ match the
context type of the agent that uses the tool.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `func` | `ToolFunction[...] | None` | The function to wrap. | `None` |
| `name_override` | `str | None` | If provided, use this name for the tool instead of the function's name. | `None` |
| `description_override` | `str | None` | If provided, use this description for the tool instead of the<br>function's docstring. | `None` |
| `docstring_style` | `DocstringStyle | None` | If provided, use this style for the tool's docstring. If not provided,<br>we will attempt to auto-detect the style. | `None` |
| `use_docstring_info` | `bool` | If True, use the function's docstring to populate the tool's<br>description and argument descriptions. | `True` |
| `failure_error_function` | `ToolErrorFunction | None` | If provided, use this function to generate an error message when<br>the tool call fails. The error message is sent to the LLM. If you pass None, then no<br>error message will be sent and instead an Exception will be raised. | `default_tool_error_function` |

Source code in `src/agents/tool.py`

|     |     |
| --- | --- |
| ```<br>158<br>159<br>160<br>161<br>162<br>163<br>164<br>165<br>166<br>167<br>168<br>169<br>170<br>171<br>172<br>173<br>174<br>175<br>176<br>177<br>178<br>179<br>180<br>181<br>182<br>183<br>184<br>185<br>186<br>187<br>188<br>189<br>190<br>191<br>192<br>193<br>194<br>195<br>196<br>197<br>198<br>199<br>200<br>201<br>202<br>203<br>204<br>205<br>206<br>207<br>208<br>209<br>210<br>211<br>212<br>213<br>214<br>215<br>216<br>217<br>218<br>219<br>220<br>221<br>222<br>223<br>224<br>225<br>226<br>227<br>228<br>229<br>230<br>231<br>232<br>233<br>234<br>235<br>236<br>237<br>238<br>239<br>240<br>241<br>242<br>243<br>244<br>245<br>246<br>247<br>248<br>249<br>250<br>251<br>252<br>253<br>254<br>255<br>256<br>257<br>258<br>259<br>260<br>261<br>262<br>263<br>264<br>265<br>266<br>267<br>268<br>269<br>270<br>271<br>272<br>273<br>274<br>275<br>276<br>277<br>278<br>279<br>280<br>281<br>282<br>283<br>284<br>285<br>286<br>``` | ```md-code__content<br>def function_tool(<br>    func: ToolFunction[...] | None = None,<br>    *,<br>    name_override: str | None = None,<br>    description_override: str | None = None,<br>    docstring_style: DocstringStyle | None = None,<br>    use_docstring_info: bool = True,<br>    failure_error_function: ToolErrorFunction | None = default_tool_error_function,<br>) -> FunctionTool | Callable[[ToolFunction[...]], FunctionTool]:<br>    """<br>    Decorator to create a FunctionTool from a function. By default, we will:<br>    1. Parse the function signature to create a JSON schema for the tool's parameters.<br>    2. Use the function's docstring to populate the tool's description.<br>    3. Use the function's docstring to populate argument descriptions.<br>    The docstring style is detected automatically, but you can override it.<br>    If the function takes a `RunContextWrapper` as the first argument, it *must* match the<br>    context type of the agent that uses the tool.<br>    Args:<br>        func: The function to wrap.<br>        name_override: If provided, use this name for the tool instead of the function's name.<br>        description_override: If provided, use this description for the tool instead of the<br>            function's docstring.<br>        docstring_style: If provided, use this style for the tool's docstring. If not provided,<br>            we will attempt to auto-detect the style.<br>        use_docstring_info: If True, use the function's docstring to populate the tool's<br>            description and argument descriptions.<br>        failure_error_function: If provided, use this function to generate an error message when<br>            the tool call fails. The error message is sent to the LLM. If you pass None, then no<br>            error message will be sent and instead an Exception will be raised.<br>    """<br>    def _create_function_tool(the_func: ToolFunction[...]) -> FunctionTool:<br>        schema = function_schema(<br>            func=the_func,<br>            name_override=name_override,<br>            description_override=description_override,<br>            docstring_style=docstring_style,<br>            use_docstring_info=use_docstring_info,<br>        )<br>        async def _on_invoke_tool_impl(ctx: RunContextWrapper[Any], input: str) -> str:<br>            try:<br>                json_data: dict[str, Any] = json.loads(input) if input else {}<br>            except Exception as e:<br>                if _debug.DONT_LOG_TOOL_DATA:<br>                    logger.debug(f"Invalid JSON input for tool {schema.name}")<br>                else:<br>                    logger.debug(f"Invalid JSON input for tool {schema.name}: {input}")<br>                raise ModelBehaviorError(<br>                    f"Invalid JSON input for tool {schema.name}: {input}"<br>                ) from e<br>            if _debug.DONT_LOG_TOOL_DATA:<br>                logger.debug(f"Invoking tool {schema.name}")<br>            else:<br>                logger.debug(f"Invoking tool {schema.name} with input {input}")<br>            try:<br>                parsed = (<br>                    schema.params_pydantic_model(**json_data)<br>                    if json_data<br>                    else schema.params_pydantic_model()<br>                )<br>            except ValidationError as e:<br>                raise ModelBehaviorError(f"Invalid JSON input for tool {schema.name}: {e}") from e<br>            args, kwargs_dict = schema.to_call_args(parsed)<br>            if not _debug.DONT_LOG_TOOL_DATA:<br>                logger.debug(f"Tool call args: {args}, kwargs: {kwargs_dict}")<br>            if inspect.iscoroutinefunction(the_func):<br>                if schema.takes_context:<br>                    result = await the_func(ctx, *args, **kwargs_dict)<br>                else:<br>                    result = await the_func(*args, **kwargs_dict)<br>            else:<br>                if schema.takes_context:<br>                    result = the_func(ctx, *args, **kwargs_dict)<br>                else:<br>                    result = the_func(*args, **kwargs_dict)<br>            if _debug.DONT_LOG_TOOL_DATA:<br>                logger.debug(f"Tool {schema.name} completed.")<br>            else:<br>                logger.debug(f"Tool {schema.name} returned {result}")<br>            return str(result)<br>        async def _on_invoke_tool(ctx: RunContextWrapper[Any], input: str) -> str:<br>            try:<br>                return await _on_invoke_tool_impl(ctx, input)<br>            except Exception as e:<br>                if failure_error_function is None:<br>                    raise<br>                result = failure_error_function(ctx, e)<br>                if inspect.isawaitable(result):<br>                    return await result<br>                _utils.attach_error_to_current_span(<br>                    SpanError(<br>                        message="Error running tool (non-fatal)",<br>                        data={<br>                            "tool_name": schema.name,<br>                            "error": str(e),<br>                        },<br>                    )<br>                )<br>                return result<br>        return FunctionTool(<br>            name=schema.name,<br>            description=schema.description or "",<br>            params_json_schema=schema.params_json_schema,<br>            on_invoke_tool=_on_invoke_tool,<br>        )<br>    # If func is actually a callable, we were used as @function_tool with no parentheses<br>    if callable(func):<br>        return _create_function_tool(func)<br>    # Otherwise, we were used as @function_tool(...), so return a decorator<br>    def decorator(real_func: ToolFunction[...]) -> FunctionTool:<br>        return _create_function_tool(real_func)<br>    return decorator<br>``` |