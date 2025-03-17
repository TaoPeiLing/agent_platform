[Skip to content](https://openai.github.io/openai-agents-python/ref/extensions/handoff_filters/#handoff-filters)

# `Handoff filters`

### remove\_all\_tools

```md-code__content
remove_all_tools(
    handoff_input_data: HandoffInputData,
) -> HandoffInputData

```

Filters out all tool items: file search, web search and function calls+output.

Source code in `src/agents/extensions/handoff_filters.py`

|     |     |
| --- | --- |
| ```<br>16<br>17<br>18<br>19<br>20<br>21<br>22<br>23<br>24<br>25<br>26<br>27<br>28<br>29<br>30<br>31<br>32<br>``` | ```md-code__content<br>def remove_all_tools(handoff_input_data: HandoffInputData) -> HandoffInputData:<br>    """Filters out all tool items: file search, web search and function calls+output."""<br>    history = handoff_input_data.input_history<br>    new_items = handoff_input_data.new_items<br>    filtered_history = (<br>        _remove_tool_types_from_input(history) if isinstance(history, tuple) else history<br>    )<br>    filtered_pre_handoff_items = _remove_tools_from_items(handoff_input_data.pre_handoff_items)<br>    filtered_new_items = _remove_tools_from_items(new_items)<br>    return HandoffInputData(<br>        input_history=filtered_history,<br>        pre_handoff_items=filtered_pre_handoff_items,<br>        new_items=filtered_new_items,<br>    )<br>``` |