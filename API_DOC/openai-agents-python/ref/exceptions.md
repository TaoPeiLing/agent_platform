[Skip to content](https://openai.github.io/openai-agents-python/ref/exceptions/#exceptions)

# `Exceptions`

### AgentsException

Bases: `Exception`

Base class for all exceptions in the Agents SDK.

Source code in `src/agents/exceptions.py`

|     |     |
| --- | --- |
| ```<br>7<br>8<br>``` | ```md-code__content<br>class AgentsException(Exception):<br>    """Base class for all exceptions in the Agents SDK."""<br>``` |

### MaxTurnsExceeded

Bases: `AgentsException`

Exception raised when the maximum number of turns is exceeded.

Source code in `src/agents/exceptions.py`

|     |     |
| --- | --- |
| ```<br>11<br>12<br>13<br>14<br>15<br>16<br>17<br>``` | ```md-code__content<br>class MaxTurnsExceeded(AgentsException):<br>    """Exception raised when the maximum number of turns is exceeded."""<br>    message: str<br>    def __init__(self, message: str):<br>        self.message = message<br>``` |

### ModelBehaviorError

Bases: `AgentsException`

Exception raised when the model does something unexpected, e.g. calling a tool that doesn't
exist, or providing malformed JSON.

Source code in `src/agents/exceptions.py`

|     |     |
| --- | --- |
| ```<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28<br>``` | ```md-code__content<br>class ModelBehaviorError(AgentsException):<br>    """Exception raised when the model does something unexpected, e.g. calling a tool that doesn't<br>    exist, or providing malformed JSON.<br>    """<br>    message: str<br>    def __init__(self, message: str):<br>        self.message = message<br>``` |

### UserError

Bases: `AgentsException`

Exception raised when the user makes an error using the SDK.

Source code in `src/agents/exceptions.py`

|     |     |
| --- | --- |
| ```<br>31<br>32<br>33<br>34<br>35<br>36<br>37<br>``` | ```md-code__content<br>class UserError(AgentsException):<br>    """Exception raised when the user makes an error using the SDK."""<br>    message: str<br>    def __init__(self, message: str):<br>        self.message = message<br>``` |

### InputGuardrailTripwireTriggered

Bases: `AgentsException`

Exception raised when a guardrail tripwire is triggered.

Source code in `src/agents/exceptions.py`

|     |     |
| --- | --- |
| ```<br>40<br>41<br>42<br>43<br>44<br>45<br>46<br>47<br>48<br>49<br>50<br>``` | ```md-code__content<br>class InputGuardrailTripwireTriggered(AgentsException):<br>    """Exception raised when a guardrail tripwire is triggered."""<br>    guardrail_result: "InputGuardrailResult"<br>    """The result data of the guardrail that was triggered."""<br>    def __init__(self, guardrail_result: "InputGuardrailResult"):<br>        self.guardrail_result = guardrail_result<br>        super().__init__(<br>            f"Guardrail {guardrail_result.guardrail.__class__.__name__} triggered tripwire"<br>        )<br>``` |

#### guardrail\_result`instance-attribute`

```md-code__content
guardrail_result: InputGuardrailResult = guardrail_result

```

The result data of the guardrail that was triggered.

### OutputGuardrailTripwireTriggered

Bases: `AgentsException`

Exception raised when a guardrail tripwire is triggered.

Source code in `src/agents/exceptions.py`

|     |     |
| --- | --- |
| ```<br>53<br>54<br>55<br>56<br>57<br>58<br>59<br>60<br>61<br>62<br>63<br>``` | ```md-code__content<br>class OutputGuardrailTripwireTriggered(AgentsException):<br>    """Exception raised when a guardrail tripwire is triggered."""<br>    guardrail_result: "OutputGuardrailResult"<br>    """The result data of the guardrail that was triggered."""<br>    def __init__(self, guardrail_result: "OutputGuardrailResult"):<br>        self.guardrail_result = guardrail_result<br>        super().__init__(<br>            f"Guardrail {guardrail_result.guardrail.__class__.__name__} triggered tripwire"<br>        )<br>``` |

#### guardrail\_result`instance-attribute`

```md-code__content
guardrail_result: OutputGuardrailResult = guardrail_result

```

The result data of the guardrail that was triggered.