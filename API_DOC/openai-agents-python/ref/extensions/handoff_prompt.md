[Skip to content](https://openai.github.io/openai-agents-python/ref/extensions/handoff_prompt/#handoff-prompt)

# `Handoff prompt`

### RECOMMENDED\_PROMPT\_PREFIX`module-attribute`

```md-code__content
RECOMMENDED_PROMPT_PREFIX = "# System context\nYou are part of a multi-agent system called the Agents SDK, designed to make agent coordination and execution easy. Agents uses two primary abstraction: **Agents** and **Handoffs**. An agent encompasses instructions and tools and can hand off a conversation to another agent when appropriate. Handoffs are achieved by calling a handoff function, generally named `transfer_to_<agent_name>`. Transfers between agents are handled seamlessly in the background; do not mention or draw attention to these transfers in your conversation with the user.\n"

```

### prompt\_with\_handoff\_instructions

```md-code__content
prompt_with_handoff_instructions(prompt: str) -> str

```

Add recommended instructions to the prompt for agents that use handoffs.

Source code in `src/agents/extensions/handoff_prompt.py`

|     |     |
| --- | --- |
| ```<br>15<br>16<br>17<br>18<br>19<br>``` | ```md-code__content<br>def prompt_with_handoff_instructions(prompt: str) -> str:<br>    """<br>    Add recommended instructions to the prompt for agents that use handoffs.<br>    """<br>    return f"{RECOMMENDED_PROMPT_PREFIX}\n\n{prompt}"<br>``` |