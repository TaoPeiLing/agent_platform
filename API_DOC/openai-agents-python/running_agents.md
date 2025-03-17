[Skip to content](https://openai.github.io/openai-agents-python/running_agents/#running-agents)

# Running agents

You can run agents via the [`Runner`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.Runner "Runner") class. You have 3 options:

1. [`Runner.run()`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.Runner.run "run            async       classmethod   "), which runs async and returns a [`RunResult`](https://openai.github.io/openai-agents-python/ref/result/#agents.result.RunResult "RunResult            dataclass   ").
2. [`Runner.run_sync()`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.Runner.run_sync "run_sync            classmethod   "), which is a sync method and just runs `.run()` under the hood.
3. [`Runner.run_streamed()`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.Runner.run_streamed "run_streamed            classmethod   "), which runs async and returns a [`RunResultStreaming`](https://openai.github.io/openai-agents-python/ref/result/#agents.result.RunResultStreaming "RunResultStreaming            dataclass   "). It calls the LLM in streaming mode, and streams those events to you as they are received.

```md-code__content
from agents import Agent, Runner

async def main():
    agent = Agent(name="Assistant", instructions="You are a helpful assistant")

    result = await Runner.run(agent, "Write a haiku about recursion in programming.")
    print(result.final_output)
    # Code within the code,
    # Functions calling themselves,
    # Infinite loop's dance.

```

Read more in the [results guide](https://openai.github.io/openai-agents-python/results/).

## The agent loop

When you use the run method in `Runner`, you pass in a starting agent and input. The input can either be a string (which is considered a user message), or a list of input items, which are the items in the OpenAI Responses API.

The runner then runs a loop:

1. We call the LLM for the current agent, with the current input.
2. The LLM produces its output.
1. If the LLM returns a `final_output`, the loop ends and we return the result.
2. If the LLM does a handoff, we update the current agent and input, and re-run the loop.
3. If the LLM produces tool calls, we run those tool calls, append the results, and re-run the loop.
3. If we exceed the `max_turns` passed, we raise a [`MaxTurnsExceeded`](https://openai.github.io/openai-agents-python/ref/exceptions/#agents.exceptions.MaxTurnsExceeded "MaxTurnsExceeded") exception.

Note

The rule for whether the LLM output is considered as a "final output" is that it produces text output with the desired type, and there are no tool calls.

## Streaming

Streaming allows you to additionally receive streaming events as the LLM runs. Once the stream is done, the [`RunResultStreaming`](https://openai.github.io/openai-agents-python/ref/result/#agents.result.RunResultStreaming "RunResultStreaming            dataclass   ") will contain the complete information about the run, including all the new outputs produces. You can call `.stream_events()` for the streaming events. Read more in the [streaming guide](https://openai.github.io/openai-agents-python/streaming/).

## Run config

The `run_config` parameter lets you configure some global settings for the agent run:

- [`model`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.model "model            class-attribute       instance-attribute   "): Allows setting a global LLM model to use, irrespective of what `model` each Agent has.
- [`model_provider`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.model_provider "model_provider            class-attribute       instance-attribute   "): A model provider for looking up model names, which defaults to OpenAI.
- [`model_settings`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.model_settings "model_settings            class-attribute       instance-attribute   "): Overrides agent-specific settings. For example, you can set a global `temperature` or `top_p`.
- [`input_guardrails`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.input_guardrails "input_guardrails            class-attribute       instance-attribute   "), [`output_guardrails`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.output_guardrails "output_guardrails            class-attribute       instance-attribute   "): A list of input or output guardrails to include on all runs.
- [`handoff_input_filter`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.handoff_input_filter "handoff_input_filter            class-attribute       instance-attribute   "): A global input filter to apply to all handoffs, if the handoff doesn't already have one. The input filter allows you to edit the inputs that are sent to the new agent. See the documentation in [`Handoff.input_filter`](https://openai.github.io/openai-agents-python/ref/handoffs/#agents.handoffs.Handoff.input_filter "input_filter            class-attribute       instance-attribute   ") for more details.
- [`tracing_disabled`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.tracing_disabled "tracing_disabled            class-attribute       instance-attribute   "): Allows you to disable [tracing](https://openai.github.io/openai-agents-python/tracing/) for the entire run.
- [`trace_include_sensitive_data`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.trace_include_sensitive_data "trace_include_sensitive_data            class-attribute       instance-attribute   "): Configures whether traces will include potentially sensitive data, such as LLM and tool call inputs/outputs.
- [`workflow_name`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.workflow_name "workflow_name            class-attribute       instance-attribute   "), [`trace_id`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.trace_id "trace_id            class-attribute       instance-attribute   "), [`group_id`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.group_id "group_id            class-attribute       instance-attribute   "): Sets the tracing workflow name, trace ID and trace group ID for the run. We recommend at least setting `workflow_name`. The session ID is an optional field that lets you link traces across multiple runs.
- [`trace_metadata`](https://openai.github.io/openai-agents-python/ref/run/#agents.run.RunConfig.trace_metadata "trace_metadata            class-attribute       instance-attribute   "): Metadata to include on all traces.

## Conversations/chat threads

Calling any of the run methods can result in one or more agents running (and hence one or more LLM calls), but it represents a single logical turn in a chat conversation. For example:

1. User turn: user enter text
2. Runner run: first agent calls LLM, runs tools, does a handoff to a second agent, second agent runs more tools, and then produces an output.

At the end of the agent run, you can choose what to show to the user. For example, you might show the user every new item generated by the agents, or just the final output. Either way, the user might then ask a followup question, in which case you can call the run method again.

You can use the base [`RunResultBase.to_input_list()`](https://openai.github.io/openai-agents-python/ref/result/#agents.result.RunResultBase.to_input_list "to_input_list") method to get the inputs for the next turn.

```md-code__content
async def main():
    agent = Agent(name="Assistant", instructions="Reply very concisely.")

    with trace(workflow_name="Conversation", group_id=thread_id):
        # First turn
        result = await Runner.run(agent, "What city is the Golden Gate Bridge in?")
        print(result.final_output)
        # San Francisco

        # Second turn
        new_input = result.to_input_list() + [{"role": "user", "content": "What state is it in?"}]
        result = await Runner.run(agent, new_input)
        print(result.final_output)
        # California

```

## Exceptions

The SDK raises exceptions in certain cases. The full list is in [`agents.exceptions`](https://openai.github.io/openai-agents-python/ref/exceptions/#agents.exceptions). As an overview:

- [`AgentsException`](https://openai.github.io/openai-agents-python/ref/exceptions/#agents.exceptions.AgentsException "AgentsException") is the base class for all exceptions raised in the SDK.
- [`MaxTurnsExceeded`](https://openai.github.io/openai-agents-python/ref/exceptions/#agents.exceptions.MaxTurnsExceeded "MaxTurnsExceeded") is raised when the run exceeds the `max_turns` passed to the run methods.
- [`ModelBehaviorError`](https://openai.github.io/openai-agents-python/ref/exceptions/#agents.exceptions.ModelBehaviorError "ModelBehaviorError") is raised when the model produces invalid outputs, e.g. malformed JSON or using non-existent tools.
- [`UserError`](https://openai.github.io/openai-agents-python/ref/exceptions/#agents.exceptions.UserError "UserError") is raised when you (the person writing code using the SDK) make an error using the SDK.
- [`InputGuardrailTripwireTriggered`](https://openai.github.io/openai-agents-python/ref/exceptions/#agents.exceptions.InputGuardrailTripwireTriggered "InputGuardrailTripwireTriggered"), [`OutputGuardrailTripwireTriggered`](https://openai.github.io/openai-agents-python/ref/exceptions/#agents.exceptions.OutputGuardrailTripwireTriggered "OutputGuardrailTripwireTriggered") is raised when a [guardrail](https://openai.github.io/openai-agents-python/guardrails/) is tripped.