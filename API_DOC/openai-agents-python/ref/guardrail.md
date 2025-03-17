[Skip to content](https://openai.github.io/openai-agents-python/ref/guardrail/#guardrails)

# `Guardrails`

### GuardrailFunctionOutput`dataclass`

The output of a guardrail function.

Source code in `src/agents/guardrail.py`

|     |     |
| --- | --- |
| ```<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>``` | ```md-code__content<br>@dataclass<br>class GuardrailFunctionOutput:<br>    """The output of a guardrail function."""<br>    output_info: Any<br>    """<br>    Optional information about the guardrail's output. For example, the guardrail could include<br>    information about the checks it performed and granular results.<br>    """<br>    tripwire_triggered: bool<br>    """<br>    Whether the tripwire was triggered. If triggered, the agent's execution will be halted.<br>    """<br>``` |

#### output\_info`instance-attribute`

```md-code__content
output_info: Any

```

Optional information about the guardrail's output. For example, the guardrail could include
information about the checks it performed and granular results.

#### tripwire\_triggered`instance-attribute`

```md-code__content
tripwire_triggered: bool

```

Whether the tripwire was triggered. If triggered, the agent's execution will be halted.

### InputGuardrailResult`dataclass`

The result of a guardrail run.

Source code in `src/agents/guardrail.py`

|     |     |
| --- | --- |
| ```<br>35<br>36<br>37<br>38<br>39<br>40<br>41<br>42<br>43<br>44<br>45<br>``` | ```md-code__content<br>@dataclass<br>class InputGuardrailResult:<br>    """The result of a guardrail run."""<br>    guardrail: InputGuardrail[Any]<br>    """<br>    The guardrail that was run.<br>    """<br>    output: GuardrailFunctionOutput<br>    """The output of the guardrail function."""<br>``` |

#### guardrail`instance-attribute`

```md-code__content
guardrail: InputGuardrail[Any]

```

The guardrail that was run.

#### output`instance-attribute`

```md-code__content
output: GuardrailFunctionOutput

```

The output of the guardrail function.

### OutputGuardrailResult`dataclass`

The result of a guardrail run.

Source code in `src/agents/guardrail.py`

|     |     |
| --- | --- |
| ```<br>48<br>49<br>50<br>51<br>52<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>64<br>65<br>66<br>67<br>68<br>``` | ```md-code__content<br>@dataclass<br>class OutputGuardrailResult:<br>    """The result of a guardrail run."""<br>    guardrail: OutputGuardrail[Any]<br>    """<br>    The guardrail that was run.<br>    """<br>    agent_output: Any<br>    """<br>    The output of the agent that was checked by the guardrail.<br>    """<br>    agent: Agent[Any]<br>    """<br>    The agent that was checked by the guardrail.<br>    """<br>    output: GuardrailFunctionOutput<br>    """The output of the guardrail function."""<br>``` |

#### guardrail`instance-attribute`

```md-code__content
guardrail: OutputGuardrail[Any]

```

The guardrail that was run.

#### agent\_output`instance-attribute`

```md-code__content
agent_output: Any

```

The output of the agent that was checked by the guardrail.

#### agent`instance-attribute`

```md-code__content
agent: Agent[Any]

```

The agent that was checked by the guardrail.

#### output`instance-attribute`

```md-code__content
output: GuardrailFunctionOutput

```

The output of the guardrail function.

### InputGuardrail`dataclass`

Bases: `Generic[TContext]`

Input guardrails are checks that run in parallel to the agent's execution.
They can be used to do things like:
\- Check if input messages are off-topic
\- Take over control of the agent's execution if an unexpected input is detected

You can use the `@input_guardrail()` decorator to turn a function into an `InputGuardrail`, or
create an `InputGuardrail` manually.

Guardrails return a `GuardrailResult`. If `result.tripwire_triggered` is `True`, the agent
execution will immediately stop and a `InputGuardrailTripwireTriggered` exception will be raised

Source code in `src/agents/guardrail.py`

|     |     |
| --- | --- |
| ```<br> 71<br> 72<br> 73<br> 74<br> 75<br> 76<br> 77<br> 78<br> 79<br> 80<br> 81<br> 82<br> 83<br> 84<br> 85<br> 86<br> 87<br> 88<br> 89<br> 90<br> 91<br> 92<br> 93<br> 94<br> 95<br> 96<br> 97<br> 98<br> 99<br>100<br>101<br>102<br>103<br>104<br>105<br>106<br>107<br>108<br>109<br>110<br>111<br>112<br>113<br>114<br>115<br>116<br>117<br>118<br>119<br>120<br>121<br>122<br>123<br>124<br>``` | ```md-code__content<br>@dataclass<br>class InputGuardrail(Generic[TContext]):<br>    """Input guardrails are checks that run in parallel to the agent's execution.<br>    They can be used to do things like:<br>    - Check if input messages are off-topic<br>    - Take over control of the agent's execution if an unexpected input is detected<br>    You can use the `@input_guardrail()` decorator to turn a function into an `InputGuardrail`, or<br>    create an `InputGuardrail` manually.<br>    Guardrails return a `GuardrailResult`. If `result.tripwire_triggered` is `True`, the agent<br>    execution will immediately stop and a `InputGuardrailTripwireTriggered` exception will be raised<br>    """<br>    guardrail_function: Callable[<br>        [RunContextWrapper[TContext], Agent[Any], str | list[TResponseInputItem]],<br>        MaybeAwaitable[GuardrailFunctionOutput],<br>    ]<br>    """A function that receives the agent input and the context, and returns a<br>     `GuardrailResult`. The result marks whether the tripwire was triggered, and can optionally<br>     include information about the guardrail's output.<br>    """<br>    name: str | None = None<br>    """The name of the guardrail, used for tracing. If not provided, we'll use the guardrail<br>    function's name.<br>    """<br>    def get_name(self) -> str:<br>        if self.name:<br>            return self.name<br>        return self.guardrail_function.__name__<br>    async def run(<br>        self,<br>        agent: Agent[Any],<br>        input: str | list[TResponseInputItem],<br>        context: RunContextWrapper[TContext],<br>    ) -> InputGuardrailResult:<br>        if not callable(self.guardrail_function):<br>            raise UserError(f"Guardrail function must be callable, got {self.guardrail_function}")<br>        output = self.guardrail_function(context, agent, input)<br>        if inspect.isawaitable(output):<br>            return InputGuardrailResult(<br>                guardrail=self,<br>                output=await output,<br>            )<br>        return InputGuardrailResult(<br>            guardrail=self,<br>            output=output,<br>        )<br>``` |

#### guardrail\_function`instance-attribute`

```md-code__content
guardrail_function: Callable[\
    [\
        RunContextWrapper[TContext],\
        Agent[Any],\
        str | list[TResponseInputItem],\
    ],\
    MaybeAwaitable[GuardrailFunctionOutput],\
]

```

A function that receives the agent input and the context, and returns a
`GuardrailResult`. The result marks whether the tripwire was triggered, and can optionally
include information about the guardrail's output.

#### name`class-attribute``instance-attribute`

```md-code__content
name: str | None = None

```

The name of the guardrail, used for tracing. If not provided, we'll use the guardrail
function's name.

### OutputGuardrail`dataclass`

Bases: `Generic[TContext]`

Output guardrails are checks that run on the final output of an agent.
They can be used to do check if the output passes certain validation criteria

You can use the `@output_guardrail()` decorator to turn a function into an `OutputGuardrail`,
or create an `OutputGuardrail` manually.

Guardrails return a `GuardrailResult`. If `result.tripwire_triggered` is `True`, a
`OutputGuardrailTripwireTriggered` exception will be raised.

Source code in `src/agents/guardrail.py`

|     |     |
| --- | --- |
| ```<br>127<br>128<br>129<br>130<br>131<br>132<br>133<br>134<br>135<br>136<br>137<br>138<br>139<br>140<br>141<br>142<br>143<br>144<br>145<br>146<br>147<br>148<br>149<br>150<br>151<br>152<br>153<br>154<br>155<br>156<br>157<br>158<br>159<br>160<br>161<br>162<br>163<br>164<br>165<br>166<br>167<br>168<br>169<br>170<br>171<br>172<br>173<br>174<br>175<br>176<br>177<br>178<br>179<br>``` | ```md-code__content<br>@dataclass<br>class OutputGuardrail(Generic[TContext]):<br>    """Output guardrails are checks that run on the final output of an agent.<br>    They can be used to do check if the output passes certain validation criteria<br>    You can use the `@output_guardrail()` decorator to turn a function into an `OutputGuardrail`,<br>    or create an `OutputGuardrail` manually.<br>    Guardrails return a `GuardrailResult`. If `result.tripwire_triggered` is `True`, a<br>    `OutputGuardrailTripwireTriggered` exception will be raised.<br>    """<br>    guardrail_function: Callable[<br>        [RunContextWrapper[TContext], Agent[Any], Any],<br>        MaybeAwaitable[GuardrailFunctionOutput],<br>    ]<br>    """A function that receives the final agent, its output, and the context, and returns a<br>     `GuardrailResult`. The result marks whether the tripwire was triggered, and can optionally<br>     include information about the guardrail's output.<br>    """<br>    name: str | None = None<br>    """The name of the guardrail, used for tracing. If not provided, we'll use the guardrail<br>    function's name.<br>    """<br>    def get_name(self) -> str:<br>        if self.name:<br>            return self.name<br>        return self.guardrail_function.__name__<br>    async def run(<br>        self, context: RunContextWrapper[TContext], agent: Agent[Any], agent_output: Any<br>    ) -> OutputGuardrailResult:<br>        if not callable(self.guardrail_function):<br>            raise UserError(f"Guardrail function must be callable, got {self.guardrail_function}")<br>        output = self.guardrail_function(context, agent, agent_output)<br>        if inspect.isawaitable(output):<br>            return OutputGuardrailResult(<br>                guardrail=self,<br>                agent=agent,<br>                agent_output=agent_output,<br>                output=await output,<br>            )<br>        return OutputGuardrailResult(<br>            guardrail=self,<br>            agent=agent,<br>            agent_output=agent_output,<br>            output=output,<br>        )<br>``` |

#### guardrail\_function`instance-attribute`

```md-code__content
guardrail_function: Callable[\
    [RunContextWrapper[TContext], Agent[Any], Any],\
    MaybeAwaitable[GuardrailFunctionOutput],\
]

```

A function that receives the final agent, its output, and the context, and returns a
`GuardrailResult`. The result marks whether the tripwire was triggered, and can optionally
include information about the guardrail's output.

#### name`class-attribute``instance-attribute`

```md-code__content
name: str | None = None

```

The name of the guardrail, used for tracing. If not provided, we'll use the guardrail
function's name.

### input\_guardrail

```md-code__content
input_guardrail(
    func: _InputGuardrailFuncSync[TContext_co],
) -> InputGuardrail[TContext_co]

```

```md-code__content
input_guardrail(
    func: _InputGuardrailFuncAsync[TContext_co],
) -> InputGuardrail[TContext_co]

```

```md-code__content
input_guardrail(
    *, name: str | None = None
) -> Callable[\
    [\
        _InputGuardrailFuncSync[TContext_co]\
        | _InputGuardrailFuncAsync[TContext_co]\
    ],\
    InputGuardrail[TContext_co],\
]

```

```md-code__content
input_guardrail(
    func: _InputGuardrailFuncSync[TContext_co]
    | _InputGuardrailFuncAsync[TContext_co]
    | None = None,
    *,
    name: str | None = None,
) -> (
    InputGuardrail[TContext_co]
    | Callable[\
        [\
            _InputGuardrailFuncSync[TContext_co]\
            | _InputGuardrailFuncAsync[TContext_co]\
        ],\
        InputGuardrail[TContext_co],\
    ]
)

```

Decorator that transforms a sync or async function into an `InputGuardrail`.
It can be used directly (no parentheses) or with keyword args, e.g.:

```
@input_guardrail
def my_sync_guardrail(...): ...

@input_guardrail(name="guardrail_name")
async def my_async_guardrail(...): ...

```

Source code in `src/agents/guardrail.py`

|     |     |
| --- | --- |
| ```<br>217<br>218<br>219<br>220<br>221<br>222<br>223<br>224<br>225<br>226<br>227<br>228<br>229<br>230<br>231<br>232<br>233<br>234<br>235<br>236<br>237<br>238<br>239<br>240<br>241<br>242<br>243<br>244<br>245<br>246<br>247<br>248<br>249<br>250<br>251<br>``` | ```md-code__content<br>def input_guardrail(<br>    func: _InputGuardrailFuncSync[TContext_co]<br>    | _InputGuardrailFuncAsync[TContext_co]<br>    | None = None,<br>    *,<br>    name: str | None = None,<br>) -> (<br>    InputGuardrail[TContext_co]<br>    | Callable[<br>        [_InputGuardrailFuncSync[TContext_co] | _InputGuardrailFuncAsync[TContext_co]],<br>        InputGuardrail[TContext_co],<br>    ]<br>):<br>    """<br>    Decorator that transforms a sync or async function into an `InputGuardrail`.<br>    It can be used directly (no parentheses) or with keyword args, e.g.:<br>        @input_guardrail<br>        def my_sync_guardrail(...): ...<br>        @input_guardrail(name="guardrail_name")<br>        async def my_async_guardrail(...): ...<br>    """<br>    def decorator(<br>        f: _InputGuardrailFuncSync[TContext_co] | _InputGuardrailFuncAsync[TContext_co],<br>    ) -> InputGuardrail[TContext_co]:<br>        return InputGuardrail(guardrail_function=f, name=name)<br>    if func is not None:<br>        # Decorator was used without parentheses<br>        return decorator(func)<br>    # Decorator used with keyword arguments<br>    return decorator<br>``` |

### output\_guardrail

```md-code__content
output_guardrail(
    func: _OutputGuardrailFuncSync[TContext_co],
) -> OutputGuardrail[TContext_co]

```

```md-code__content
output_guardrail(
    func: _OutputGuardrailFuncAsync[TContext_co],
) -> OutputGuardrail[TContext_co]

```

```md-code__content
output_guardrail(
    *, name: str | None = None
) -> Callable[\
    [\
        _OutputGuardrailFuncSync[TContext_co]\
        | _OutputGuardrailFuncAsync[TContext_co]\
    ],\
    OutputGuardrail[TContext_co],\
]

```

```md-code__content
output_guardrail(
    func: _OutputGuardrailFuncSync[TContext_co]
    | _OutputGuardrailFuncAsync[TContext_co]
    | None = None,
    *,
    name: str | None = None,
) -> (
    OutputGuardrail[TContext_co]
    | Callable[\
        [\
            _OutputGuardrailFuncSync[TContext_co]\
            | _OutputGuardrailFuncAsync[TContext_co]\
        ],\
        OutputGuardrail[TContext_co],\
    ]
)

```

Decorator that transforms a sync or async function into an `OutputGuardrail`.
It can be used directly (no parentheses) or with keyword args, e.g.:

```
@output_guardrail
def my_sync_guardrail(...): ...

@output_guardrail(name="guardrail_name")
async def my_async_guardrail(...): ...

```

Source code in `src/agents/guardrail.py`

|     |     |
| --- | --- |
| ```<br>286<br>287<br>288<br>289<br>290<br>291<br>292<br>293<br>294<br>295<br>296<br>297<br>298<br>299<br>300<br>301<br>302<br>303<br>304<br>305<br>306<br>307<br>308<br>309<br>310<br>311<br>312<br>313<br>314<br>315<br>316<br>317<br>318<br>319<br>320<br>``` | ```md-code__content<br>def output_guardrail(<br>    func: _OutputGuardrailFuncSync[TContext_co]<br>    | _OutputGuardrailFuncAsync[TContext_co]<br>    | None = None,<br>    *,<br>    name: str | None = None,<br>) -> (<br>    OutputGuardrail[TContext_co]<br>    | Callable[<br>        [_OutputGuardrailFuncSync[TContext_co] | _OutputGuardrailFuncAsync[TContext_co]],<br>        OutputGuardrail[TContext_co],<br>    ]<br>):<br>    """<br>    Decorator that transforms a sync or async function into an `OutputGuardrail`.<br>    It can be used directly (no parentheses) or with keyword args, e.g.:<br>        @output_guardrail<br>        def my_sync_guardrail(...): ...<br>        @output_guardrail(name="guardrail_name")<br>        async def my_async_guardrail(...): ...<br>    """<br>    def decorator(<br>        f: _OutputGuardrailFuncSync[TContext_co] | _OutputGuardrailFuncAsync[TContext_co],<br>    ) -> OutputGuardrail[TContext_co]:<br>        return OutputGuardrail(guardrail_function=f, name=name)<br>    if func is not None:<br>        # Decorator was used without parentheses<br>        return decorator(func)<br>    # Decorator used with keyword arguments<br>    return decorator<br>``` |