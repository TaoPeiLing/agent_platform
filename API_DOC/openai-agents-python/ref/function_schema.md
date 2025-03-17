[Skip to content](https://openai.github.io/openai-agents-python/ref/function_schema/#function-schema)

# `Function schema`

### FuncSchema`dataclass`

Captures the schema for a python function, in preparation for sending it to an LLM as a tool.

Source code in `src/agents/function_schema.py`

|     |     |
| --- | --- |
| ```<br>18<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>69<br>``` | ```md-code__content<br>@dataclass<br>class FuncSchema:<br>    """<br>    Captures the schema for a python function, in preparation for sending it to an LLM as a tool.<br>    """<br>    name: str<br>    """The name of the function."""<br>    description: str | None<br>    """The description of the function."""<br>    params_pydantic_model: type[BaseModel]<br>    """A Pydantic model that represents the function's parameters."""<br>    params_json_schema: dict[str, Any]<br>    """The JSON schema for the function's parameters, derived from the Pydantic model."""<br>    signature: inspect.Signature<br>    """The signature of the function."""<br>    takes_context: bool = False<br>    """Whether the function takes a RunContextWrapper argument (must be the first argument)."""<br>    def to_call_args(self, data: BaseModel) -> tuple[list[Any], dict[str, Any]]:<br>        """<br>        Converts validated data from the Pydantic model into (args, kwargs), suitable for calling<br>        the original function.<br>        """<br>        positional_args: list[Any] = []<br>        keyword_args: dict[str, Any] = {}<br>        seen_var_positional = False<br>        # Use enumerate() so we can skip the first parameter if it's context.<br>        for idx, (name, param) in enumerate(self.signature.parameters.items()):<br>            # If the function takes a RunContextWrapper and this is the first parameter, skip it.<br>            if self.takes_context and idx == 0:<br>                continue<br>            value = getattr(data, name, None)<br>            if param.kind == param.VAR_POSITIONAL:<br>                # e.g. *args: extend positional args and mark that *args is now seen<br>                positional_args.extend(value or [])<br>                seen_var_positional = True<br>            elif param.kind == param.VAR_KEYWORD:<br>                # e.g. **kwargs handling<br>                keyword_args.update(value or {})<br>            elif param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):<br>                # Before *args, add to positional args. After *args, add to keyword args.<br>                if not seen_var_positional:<br>                    positional_args.append(value)<br>                else:<br>                    keyword_args[name] = value<br>            else:<br>                # For KEYWORD_ONLY parameters, always use keyword args.<br>                keyword_args[name] = value<br>        return positional_args, keyword_args<br>``` |

#### name`instance-attribute`

```md-code__content
name: str

```

The name of the function.

#### description`instance-attribute`

```md-code__content
description: str | None

```

The description of the function.

#### params\_pydantic\_model`instance-attribute`

```md-code__content
params_pydantic_model: type[BaseModel]

```

A Pydantic model that represents the function's parameters.

#### params\_json\_schema`instance-attribute`

```md-code__content
params_json_schema: dict[str, Any]

```

The JSON schema for the function's parameters, derived from the Pydantic model.

#### signature`instance-attribute`

```md-code__content
signature: Signature

```

The signature of the function.

#### takes\_context`class-attribute``instance-attribute`

```md-code__content
takes_context: bool = False

```

Whether the function takes a RunContextWrapper argument (must be the first argument).

#### to\_call\_args

```md-code__content
to_call_args(
    data: BaseModel,
) -> tuple[list[Any], dict[str, Any]]

```

Converts validated data from the Pydantic model into (args, kwargs), suitable for calling
the original function.

Source code in `src/agents/function_schema.py`

|     |     |
| --- | --- |
| ```<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>69<br>``` | ```md-code__content<br>def to_call_args(self, data: BaseModel) -> tuple[list[Any], dict[str, Any]]:<br>    """<br>    Converts validated data from the Pydantic model into (args, kwargs), suitable for calling<br>    the original function.<br>    """<br>    positional_args: list[Any] = []<br>    keyword_args: dict[str, Any] = {}<br>    seen_var_positional = False<br>    # Use enumerate() so we can skip the first parameter if it's context.<br>    for idx, (name, param) in enumerate(self.signature.parameters.items()):<br>        # If the function takes a RunContextWrapper and this is the first parameter, skip it.<br>        if self.takes_context and idx == 0:<br>            continue<br>        value = getattr(data, name, None)<br>        if param.kind == param.VAR_POSITIONAL:<br>            # e.g. *args: extend positional args and mark that *args is now seen<br>            positional_args.extend(value or [])<br>            seen_var_positional = True<br>        elif param.kind == param.VAR_KEYWORD:<br>            # e.g. **kwargs handling<br>            keyword_args.update(value or {})<br>        elif param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):<br>            # Before *args, add to positional args. After *args, add to keyword args.<br>            if not seen_var_positional:<br>                positional_args.append(value)<br>            else:<br>                keyword_args[name] = value<br>        else:<br>            # For KEYWORD_ONLY parameters, always use keyword args.<br>            keyword_args[name] = value<br>    return positional_args, keyword_args<br>``` |

### FuncDocumentation`dataclass`

Contains metadata about a python function, extracted from its docstring.

Source code in `src/agents/function_schema.py`

|     |     |
| --- | --- |
| ```<br>72<br>73<br>74<br>75<br>76<br>77<br>78<br>79<br>80<br>81<br>``` | ```md-code__content<br>@dataclass<br>class FuncDocumentation:<br>    """Contains metadata about a python function, extracted from its docstring."""<br>    name: str<br>    """The name of the function, via `__name__`."""<br>    description: str | None<br>    """The description of the function, derived from the docstring."""<br>    param_descriptions: dict[str, str] | None<br>    """The parameter descriptions of the function, derived from the docstring."""<br>``` |

#### name`instance-attribute`

```md-code__content
name: str

```

The name of the function, via `__name__`.

#### description`instance-attribute`

```md-code__content
description: str | None

```

The description of the function, derived from the docstring.

#### param\_descriptions`instance-attribute`

```md-code__content
param_descriptions: dict[str, str] | None

```

The parameter descriptions of the function, derived from the docstring.

### generate\_func\_documentation

```md-code__content
generate_func_documentation(
    func: Callable[..., Any],
    style: DocstringStyle | None = None,
) -> FuncDocumentation

```

Extracts metadata from a function docstring, in preparation for sending it to an LLM as a tool.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `func` | `Callable[..., Any]` | The function to extract documentation from. | _required_ |
| `style` | `DocstringStyle | None` | The style of the docstring to use for parsing. If not provided, we will attempt to<br>auto-detect the style. | `None` |

Returns:

| Type | Description |
| --- | --- |
| `FuncDocumentation` | A FuncDocumentation object containing the function's name, description, and parameter |
| `FuncDocumentation` | descriptions. |

Source code in `src/agents/function_schema.py`

|     |     |
| --- | --- |
| ```<br>141<br>142<br>143<br>144<br>145<br>146<br>147<br>148<br>149<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>157<br>158<br>159<br>160<br>161<br>162<br>163<br>164<br>165<br>166<br>167<br>168<br>169<br>170<br>171<br>172<br>173<br>174<br>175<br>176<br>177<br>178<br>179<br>180<br>``` | ```md-code__content<br>def generate_func_documentation(<br>    func: Callable[..., Any], style: DocstringStyle | None = None<br>) -> FuncDocumentation:<br>    """<br>    Extracts metadata from a function docstring, in preparation for sending it to an LLM as a tool.<br>    Args:<br>        func: The function to extract documentation from.<br>        style: The style of the docstring to use for parsing. If not provided, we will attempt to<br>            auto-detect the style.<br>    Returns:<br>        A FuncDocumentation object containing the function's name, description, and parameter<br>        descriptions.<br>    """<br>    name = func.__name__<br>    doc = inspect.getdoc(func)<br>    if not doc:<br>        return FuncDocumentation(name=name, description=None, param_descriptions=None)<br>    with _suppress_griffe_logging():<br>        docstring = Docstring(doc, lineno=1, parser=style or _detect_docstring_style(doc))<br>        parsed = docstring.parse()<br>    description: str | None = next(<br>        (section.value for section in parsed if section.kind == DocstringSectionKind.text), None<br>    )<br>    param_descriptions: dict[str, str] = {<br>        param.name: param.description<br>        for section in parsed<br>        if section.kind == DocstringSectionKind.parameters<br>        for param in section.value<br>    }<br>    return FuncDocumentation(<br>        name=func.__name__,<br>        description=description,<br>        param_descriptions=param_descriptions or None,<br>    )<br>``` |

### function\_schema

```md-code__content
function_schema(
    func: Callable[..., Any],
    docstring_style: DocstringStyle | None = None,
    name_override: str | None = None,
    description_override: str | None = None,
    use_docstring_info: bool = True,
    strict_json_schema: bool = True,
) -> FuncSchema

```

Given a python function, extracts a `FuncSchema` from it, capturing the name, description,
parameter descriptions, and other metadata.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `func` | `Callable[..., Any]` | The function to extract the schema from. | _required_ |
| `docstring_style` | `DocstringStyle | None` | The style of the docstring to use for parsing. If not provided, we will<br>attempt to auto-detect the style. | `None` |
| `name_override` | `str | None` | If provided, use this name instead of the function's `__name__`. | `None` |
| `description_override` | `str | None` | If provided, use this description instead of the one derived from the<br>docstring. | `None` |
| `use_docstring_info` | `bool` | If True, uses the docstring to generate the description and parameter<br>descriptions. | `True` |
| `strict_json_schema` | `bool` | Whether the JSON schema is in strict mode. If True, we'll ensure that<br>the schema adheres to the "strict" standard the OpenAI API expects. We **strongly**<br>recommend setting this to True, as it increases the likelihood of the LLM providing<br>correct JSON input. | `True` |

Returns:

| Type | Description |
| --- | --- |
| `FuncSchema` | A `FuncSchema` object containing the function's name, description, parameter descriptions, |
| `FuncSchema` | and other metadata. |

Source code in `src/agents/function_schema.py`

|     |     |
| --- | --- |
| ```<br>183<br>184<br>185<br>186<br>187<br>188<br>189<br>190<br>191<br>192<br>193<br>194<br>195<br>196<br>197<br>198<br>199<br>200<br>201<br>202<br>203<br>204<br>205<br>206<br>207<br>208<br>209<br>210<br>211<br>212<br>213<br>214<br>215<br>216<br>217<br>218<br>219<br>220<br>221<br>222<br>223<br>224<br>225<br>226<br>227<br>228<br>229<br>230<br>231<br>232<br>233<br>234<br>235<br>236<br>237<br>238<br>239<br>240<br>241<br>242<br>243<br>244<br>245<br>246<br>247<br>248<br>249<br>250<br>251<br>252<br>253<br>254<br>255<br>256<br>257<br>258<br>259<br>260<br>261<br>262<br>263<br>264<br>265<br>266<br>267<br>268<br>269<br>270<br>271<br>272<br>273<br>274<br>275<br>276<br>277<br>278<br>279<br>280<br>281<br>282<br>283<br>284<br>285<br>286<br>287<br>288<br>289<br>290<br>291<br>292<br>293<br>294<br>295<br>296<br>297<br>298<br>299<br>300<br>301<br>302<br>303<br>304<br>305<br>306<br>307<br>308<br>309<br>310<br>311<br>312<br>313<br>314<br>315<br>316<br>317<br>318<br>319<br>320<br>321<br>322<br>323<br>324<br>325<br>326<br>327<br>328<br>329<br>330<br>331<br>332<br>333<br>334<br>335<br>336<br>337<br>338<br>339<br>340<br>``` | ```md-code__content<br>def function_schema(<br>    func: Callable[..., Any],<br>    docstring_style: DocstringStyle | None = None,<br>    name_override: str | None = None,<br>    description_override: str | None = None,<br>    use_docstring_info: bool = True,<br>    strict_json_schema: bool = True,<br>) -> FuncSchema:<br>    """<br>    Given a python function, extracts a `FuncSchema` from it, capturing the name, description,<br>    parameter descriptions, and other metadata.<br>    Args:<br>        func: The function to extract the schema from.<br>        docstring_style: The style of the docstring to use for parsing. If not provided, we will<br>            attempt to auto-detect the style.<br>        name_override: If provided, use this name instead of the function's `__name__`.<br>        description_override: If provided, use this description instead of the one derived from the<br>            docstring.<br>        use_docstring_info: If True, uses the docstring to generate the description and parameter<br>            descriptions.<br>        strict_json_schema: Whether the JSON schema is in strict mode. If True, we'll ensure that<br>            the schema adheres to the "strict" standard the OpenAI API expects. We **strongly**<br>            recommend setting this to True, as it increases the likelihood of the LLM providing<br>            correct JSON input.<br>    Returns:<br>        A `FuncSchema` object containing the function's name, description, parameter descriptions,<br>        and other metadata.<br>    """<br>    # 1. Grab docstring info<br>    if use_docstring_info:<br>        doc_info = generate_func_documentation(func, docstring_style)<br>        param_descs = doc_info.param_descriptions or {}<br>    else:<br>        doc_info = None<br>        param_descs = {}<br>    func_name = name_override or doc_info.name if doc_info else func.__name__<br>    # 2. Inspect function signature and get type hints<br>    sig = inspect.signature(func)<br>    type_hints = get_type_hints(func)<br>    params = list(sig.parameters.items())<br>    takes_context = False<br>    filtered_params = []<br>    if params:<br>        first_name, first_param = params[0]<br>        # Prefer the evaluated type hint if available<br>        ann = type_hints.get(first_name, first_param.annotation)<br>        if ann != inspect._empty:<br>            origin = get_origin(ann) or ann<br>            if origin is RunContextWrapper:<br>                takes_context = True  # Mark that the function takes context<br>            else:<br>                filtered_params.append((first_name, first_param))<br>        else:<br>            filtered_params.append((first_name, first_param))<br>    # For parameters other than the first, raise error if any use RunContextWrapper.<br>    for name, param in params[1:]:<br>        ann = type_hints.get(name, param.annotation)<br>        if ann != inspect._empty:<br>            origin = get_origin(ann) or ann<br>            if origin is RunContextWrapper:<br>                raise UserError(<br>                    f"RunContextWrapper param found at non-first position in function"<br>                    f" {func.__name__}"<br>                )<br>        filtered_params.append((name, param))<br>    # We will collect field definitions for create_model as a dict:<br>    #   field_name -> (type_annotation, default_value_or_Field(...))<br>    fields: dict[str, Any] = {}<br>    for name, param in filtered_params:<br>        ann = type_hints.get(name, param.annotation)<br>        default = param.default<br>        # If there's no type hint, assume `Any`<br>        if ann == inspect._empty:<br>            ann = Any<br>        # If a docstring param description exists, use it<br>        field_description = param_descs.get(name, None)<br>        # Handle different parameter kinds<br>        if param.kind == param.VAR_POSITIONAL:<br>            # e.g. *args: extend positional args<br>            if get_origin(ann) is tuple:<br>                # e.g. def foo(*args: tuple[int, ...]) -> treat as List[int]<br>                args_of_tuple = get_args(ann)<br>                if len(args_of_tuple) == 2 and args_of_tuple[1] is Ellipsis:<br>                    ann = list[args_of_tuple[0]]  # type: ignore<br>                else:<br>                    ann = list[Any]<br>            else:<br>                # If user wrote *args: int, treat as List[int]<br>                ann = list[ann]  # type: ignore<br>            # Default factory to empty list<br>            fields[name] = (<br>                ann,<br>                Field(default_factory=list, description=field_description),  # type: ignore<br>            )<br>        elif param.kind == param.VAR_KEYWORD:<br>            # **kwargs handling<br>            if get_origin(ann) is dict:<br>                # e.g. def foo(**kwargs: dict[str, int])<br>                dict_args = get_args(ann)<br>                if len(dict_args) == 2:<br>                    ann = dict[dict_args[0], dict_args[1]]  # type: ignore<br>                else:<br>                    ann = dict[str, Any]<br>            else:<br>                # e.g. def foo(**kwargs: int) -> Dict[str, int]<br>                ann = dict[str, ann]  # type: ignore<br>            fields[name] = (<br>                ann,<br>                Field(default_factory=dict, description=field_description),  # type: ignore<br>            )<br>        else:<br>            # Normal parameter<br>            if default == inspect._empty:<br>                # Required field<br>                fields[name] = (<br>                    ann,<br>                    Field(..., description=field_description),<br>                )<br>            else:<br>                # Parameter with a default value<br>                fields[name] = (<br>                    ann,<br>                    Field(default=default, description=field_description),<br>                )<br>    # 3. Dynamically build a Pydantic model<br>    dynamic_model = create_model(f"{func_name}_args", __base__=BaseModel, **fields)<br>    # 4. Build JSON schema from that model<br>    json_schema = dynamic_model.model_json_schema()<br>    if strict_json_schema:<br>        json_schema = ensure_strict_json_schema(json_schema)<br>    # 5. Return as a FuncSchema dataclass<br>    return FuncSchema(<br>        name=func_name,<br>        description=description_override or doc_info.description if doc_info else None,<br>        params_pydantic_model=dynamic_model,<br>        params_json_schema=json_schema,<br>        signature=sig,<br>        takes_context=takes_context,<br>    )<br>``` |