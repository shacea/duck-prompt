[Skip to content](https://langchain-ai.github.io/langgraph/agents/tools/#tools)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/agents/tools.md "Edit this page")

# Tools [¶](https://langchain-ai.github.io/langgraph/agents/tools/\#tools "Permanent link")

[Tools](https://python.langchain.com/docs/concepts/tools/) are a way to encapsulate a function and its input schema in a way that can be passed to a chat model that supports tool calling. This allows the model to request the execution of this function with specific inputs.

You can either [define your own tools](https://langchain-ai.github.io/langgraph/agents/tools/#define-simple-tools) or use [prebuilt integrations](https://langchain-ai.github.io/langgraph/agents/tools/#prebuilt-tools) that LangChain provides.

## Define simple tools [¶](https://langchain-ai.github.io/langgraph/agents/tools/\#define-simple-tools "Permanent link")

You can pass a vanilla function to `create_react_agent` to use as a tool:

API Reference: [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

```md-code__content
from langgraph.prebuilt import create_react_agent

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

create_react_agent(
    model="anthropic:claude-3-7-sonnet",
    tools=[multiply]
)

```

`create_react_agent` automatically converts vanilla functions to [LangChain tools](https://python.langchain.com/docs/concepts/tools/#tool-interface).

## Customize tools [¶](https://langchain-ai.github.io/langgraph/agents/tools/\#customize-tools "Permanent link")

For more control over tool behavior, use the `@tool` decorator:

API Reference: [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html)

```md-code__content
from langchain_core.tools import tool

@tool("multiply_tool", parse_docstring=True)
def multiply(a: int, b: int) -> int:
    """Multiply two numbers.

    Args:
        a: First operand
        b: Second operand
    """
    return a * b

```

You can also define a custom input schema using Pydantic:

```md-code__content
from pydantic import BaseModel, Field

class MultiplyInputSchema(BaseModel):
    """Multiply two numbers"""
    a: int = Field(description="First operand")
    b: int = Field(description="Second operand")

@tool("multiply_tool", args_schema=MultiplyInputSchema)
def multiply(a: int, b: int) -> int:
   return a * b

```

For additional customization, refer to the [custom tools guide](https://python.langchain.com/docs/how_to/custom_tools/).

## Hide arguments from the model [¶](https://langchain-ai.github.io/langgraph/agents/tools/\#hide-arguments-from-the-model "Permanent link")

Some tools require runtime-only arguments (e.g., user ID or session context) that should not be controllable by the model.

You can put these arguments in the `state` or `config` of the agent, and access
this information inside the tool:

API Reference: [InjectedState](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.InjectedState) \| [RunnableConfig](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.config.RunnableConfig.html)

```md-code__content
from langgraph.prebuilt import InjectedState
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.runnables import RunnableConfig

def my_tool(
    # This will be populated by an LLM
    tool_arg: str,
    # access information that's dynamically updated inside the agent
    state: Annotated[AgentState, InjectedState],
    # access static data that is passed at agent invocation
    config: RunnableConfig,
) -> str:
    """My tool."""
    do_something_with_state(state["messages"])
    do_something_with_config(config)
    ...

```

## Disable parallel tool calling [¶](https://langchain-ai.github.io/langgraph/agents/tools/\#disable-parallel-tool-calling "Permanent link")

Some model providers support executing multiple tools in parallel, but
allow users to disable this feature.

For supported providers, you can disable parallel tool calling by setting `parallel_tool_calls=False` via the `model.bind_tools()` method:

API Reference: [init\_chat\_model](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html)

```md-code__content
from langchain.chat_models import init_chat_model

def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

model = init_chat_model("anthropic:claude-3-5-sonnet-latest", temperature=0)
tools = [add, multiply]
agent = create_react_agent(
    # disable parallel tool calls
    model=model.bind_tools(tools, parallel_tool_calls=False),
    tools=tools
)

agent.invoke(
    {"messages": [{"role": "user", "content": "what's 3 + 5 and 4 * 7?"}]}
)

```

## Return tool results directly [¶](https://langchain-ai.github.io/langgraph/agents/tools/\#return-tool-results-directly "Permanent link")

Use `return_direct=True` to return tool results immediately and stop the agent loop:

API Reference: [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html)

```md-code__content
from langchain_core.tools import tool

@tool(return_direct=True)
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[add]
)

agent.invoke(
    {"messages": [{"role": "user", "content": "what's 3 + 5?"}]}
)

```

## Force tool use [¶](https://langchain-ai.github.io/langgraph/agents/tools/\#force-tool-use "Permanent link")

To force the agent to use specific tools, you can set the `tool_choice` option in `model.bind_tools()`:

API Reference: [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html)

```md-code__content
from langchain_core.tools import tool

@tool(return_direct=True)
def greet(user_name: str) -> int:
    """Greet user."""
    return f"Hello {user_name}!"

tools = [greet]

agent = create_react_agent(
    model=model.bind_tools(tools, tool_choice={"type": "tool", "name": "greet"}),
    tools=tools
)

agent.invoke(
    {"messages": [{"role": "user", "content": "Hi, I am Bob"}]}
)

```

Avoid infinite loops

Forcing tool usage without stopping conditions can create infinite loops. Use one of the following safeguards:

- Mark the tool with [`return_direct=True`](https://langchain-ai.github.io/langgraph/agents/tools/#return-tool-results-directly) to end the loop after execution.
- Set [`recursion_limit`](https://langchain-ai.github.io/langgraph/concepts/low_level/#recursion-limit) to restrict the number of execution steps.

## Handle tool errors [¶](https://langchain-ai.github.io/langgraph/agents/tools/\#handle-tool-errors "Permanent link")

By default, the agent will catch all exceptions raised during tool calls and will pass those as tool messages to the LLM. To control how the errors are handled, you can use the prebuilt [`ToolNode`](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.ToolNode "<code class=\"doc-symbol doc-symbol-heading doc-symbol-class\"></code>            <span class=\"doc doc-object-name doc-class-name\">ToolNode</span>") — the node that executes tools inside `create_react_agent` — via its `handle_tool_errors` parameter:

[Enable error handling (default)](https://langchain-ai.github.io/langgraph/agents/tools/#__tabbed_1_1)[Disable error handling](https://langchain-ai.github.io/langgraph/agents/tools/#__tabbed_1_2)[Custom error handling](https://langchain-ai.github.io/langgraph/agents/tools/#__tabbed_1_3)

```md-code__content
from langgraph.prebuilt import create_react_agent

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    if a == 42:
        raise ValueError("The ultimate error")
    return a * b

# Run with error handling (default)
agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[multiply]
)
agent.invoke(
    {"messages": [{"role": "user", "content": "what's 42 x 7?"}]}
)

```

```md-code__content
from langgraph.prebuilt import create_react_agent, ToolNode

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    if a == 42:
        raise ValueError("The ultimate error")
    return a * b

tool_node = ToolNode(
    [multiply],
    handle_tool_errors=False
)
agent_no_error_handling = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=tool_node
)
agent_no_error_handling.invoke(
    {"messages": [{"role": "user", "content": "what's 42 x 7?"}]}
)

```

```md-code__content
from langgraph.prebuilt import create_react_agent, ToolNode

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    if a == 42:
        raise ValueError("The ultimate error")
    return a * b

tool_node = ToolNode(
    [multiply],
    handle_tool_errors=(
        "Can't use 42 as a first operand, you must switch operands!"
    )
)
agent_custom_error_handling = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=tool_node
)
agent_custom_error_handling.invoke(
    {"messages": [{"role": "user", "content": "what's 42 x 7?"}]}
)

```

See [API reference](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.ToolNode "<code class=\"doc-symbol doc-symbol-heading doc-symbol-class\"></code>            <span class=\"doc doc-object-name doc-class-name\">ToolNode</span>") for more information on different tool error handling options.

## Prebuilt tools [¶](https://langchain-ai.github.io/langgraph/agents/tools/\#prebuilt-tools "Permanent link")

LangChain supports a wide range of prebuilt tool integrations for interacting with APIs, databases, file systems, web data, and more. These tools extend the functionality of agents and enable rapid development.

You can browse the full list of available integrations in the [LangChain integrations directory](https://python.langchain.com/docs/integrations/tools/).

Some commonly used tool categories include:

- **Search**: Bing, SerpAPI, Tavily
- **Code interpreters**: Python REPL, Node.js REPL
- **Databases**: SQL, MongoDB, Redis
- **Web data**: Web scraping and browsing
- **APIs**: OpenWeatherMap, NewsAPI, and others

These integrations can be configured and added to your agents using the same `tools` parameter shown in the examples above.

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fagents%2Ftools%2F)