# Tool schemas from the agent's code

A recorded call where the model could choose a tool is only replayed when every tool it used has a schema. Kitaru takes schemas from the recorded call first, then from the `tool_schemas` parameter. When coverage shows `missing_tool_schema` skips, get the schemas from the user's agent code.

## Procedure

1. Find the agent's tool definitions in the repository: decorated functions, tool lists passed to the agent, or JSON tool specs. Include output or final-answer tools (for example Pydantic AI's `final_result`) when the framework exposes structured output as a tool.
2. Prefer generating schemas with the framework itself over writing them by hand, so they match what the model saw. Use the recipes below.
3. Show the user the tool names and a short summary of each schema (parameter names and types), and ask them to confirm before using them. Point out any tool that appears in the traces but not in the code, or the reverse: the code may have changed since the traces were recorded.
4. Pass them as `"tool_schemas": {"tool_name": {...json schema...}}`, with `tool_descriptions` when available, and keep `use_recorded_tools: true` so recorded definitions still win where they exist.
5. Rerun the dry run and confirm the skip count dropped.

Do not use `infer_missing_schemas` to replace this step. Use it only when the user cannot provide code, and say that those calls are excluded from the headline numbers.

## Recipes

Run these in the agent's own environment. They make no model call.

Pydantic AI: run the agent once against a `FunctionModel` that records the tool definitions and stops.

```python
import json

from pydantic_ai.models.function import AgentInfo, FunctionModel

schemas = {}


def capture(_messages, info: AgentInfo):
    for tool in [*info.function_tools, *info.output_tools]:
        schemas[tool.name] = tool.parameters_json_schema
    raise RuntimeError("captured")


try:
    agent.run_sync("x", model=FunctionModel(capture))  # the user's agent
except RuntimeError:
    pass
print(json.dumps(schemas))
```

OpenAI Agents SDK: for each `FunctionTool` in `agent.tools`, use `tool.name` and `tool.params_json_schema`.

LangChain and LangGraph: for each tool, use `langchain_core.utils.function_calling.convert_to_openai_tool(tool)["function"]["parameters"]`.

OpenAI or compatible SDK called directly: reuse the `tools` list the code passes to `chat.completions.create`; take each entry's `function.parameters`.

Other frameworks: find the JSON schema the framework sends to the model. Write one by hand only as a last resort, and tell the user it was hand-written.
