[Skip to content](https://openai.github.io/openai-agents-python/models/#models)

# Models

The Agents SDK comes with out-of-the-box support for OpenAI models in two flavors:

- **Recommended**: the [`OpenAIResponsesModel`](https://openai.github.io/openai-agents-python/ref/models/openai_responses/#agents.models.openai_responses.OpenAIResponsesModel "OpenAIResponsesModel"), which calls OpenAI APIs using the new [Responses API](https://platform.openai.com/docs/api-reference/responses).
- The [`OpenAIChatCompletionsModel`](https://openai.github.io/openai-agents-python/ref/models/openai_chatcompletions/#agents.models.openai_chatcompletions.OpenAIChatCompletionsModel "OpenAIChatCompletionsModel"), which calls OpenAI APIs using the [Chat Completions API](https://platform.openai.com/docs/api-reference/chat).

## Mixing and matching models

Within a single workflow, you may want to use different models for each agent. For example, you could use a smaller, faster model for triage, while using a larger, more capable model for complex tasks. When configuring an [`Agent`](https://openai.github.io/openai-agents-python/ref/agent/#agents.agent.Agent "Agent            dataclass   "), you can select a specific model by either:

1. Passing the name of an OpenAI model.
2. Passing any model name + a [`ModelProvider`](https://openai.github.io/openai-agents-python/ref/models/interface/#agents.models.interface.ModelProvider "ModelProvider") that can map that name to a Model instance.
3. Directly providing a [`Model`](https://openai.github.io/openai-agents-python/ref/models/interface/#agents.models.interface.Model "Model") implementation.

Note

While our SDK supports both the [`OpenAIResponsesModel`](https://openai.github.io/openai-agents-python/ref/models/openai_responses/#agents.models.openai_responses.OpenAIResponsesModel "OpenAIResponsesModel") and the [`OpenAIChatCompletionsModel`](https://openai.github.io/openai-agents-python/ref/models/openai_chatcompletions/#agents.models.openai_chatcompletions.OpenAIChatCompletionsModel "OpenAIChatCompletionsModel") shapes, we recommend using a single model shape for each workflow because the two shapes support a different set of features and tools. If your workflow requires mixing and matching model shapes, make sure that all the features you're using are available on both.

```md-code__content
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
import asyncio

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You only speak Spanish.",
    model="o3-mini",
)

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
    model=OpenAIChatCompletionsModel(
        model="gpt-4o",
        openai_client=AsyncOpenAI()
    ),
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent],
    model="gpt-3.5-turbo",
)

async def main():
    result = await Runner.run(triage_agent, input="Hola, ¿cómo estás?")
    print(result.final_output)

```

## Using other LLM providers

Many providers also support the OpenAI API format, which means you can pass a `base_url` to the existing OpenAI model implementations and use them easily. `ModelSettings` is used to configure tuning parameters (e.g., temperature, top\_p) for the model you select.

```md-code__content
external_client = AsyncOpenAI(
    api_key="EXTERNAL_API_KEY",
    base_url="https://api.external.com/v1/",
)

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You only speak Spanish.",
    model=OpenAIChatCompletionsModel(
        model="EXTERNAL_MODEL_NAME",
        openai_client=external_client,
    ),
    model_settings=ModelSettings(temperature=0.5),
)

```