[Skip to content](https://langchain-ai.github.io/langgraph/agents/run_agents/#running-agents)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/agents/run_agents.md "Edit this page")

# Running agents [¶](https://langchain-ai.github.io/langgraph/agents/run_agents/\#running-agents "Permanent link")

Agents support both synchronous and asynchronous execution using either `.invoke()` / `await .invoke()` for full responses, or `.stream()` / `.astream()` for **incremental** [streaming](https://langchain-ai.github.io/langgraph/agents/streaming/) output. This section explains how to provide input, interpret output, enable streaming, and control execution limits.

## Basic usage [¶](https://langchain-ai.github.io/langgraph/agents/run_agents/\#basic-usage "Permanent link")

Agents can be executed in two primary modes:

- **Synchronous** using `.invoke()` or `.stream()`
- **Asynchronous** using `await .invoke()` or `async for` with `.astream()`

[Sync invocation](https://langchain-ai.github.io/langgraph/agents/run_agents/#__tabbed_1_1)[Async invocation](https://langchain-ai.github.io/langgraph/agents/run_agents/#__tabbed_1_2)

```md-code__content
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(...)

response = agent.invoke({"messages": [{"role": "user", "content": "what is the weather in sf"}]})

```

```md-code__content
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(...)
response = await agent.ainvoke({"messages": [{"role": "user", "content": "what is the weather in sf"}]})

```

## Inputs and outputs [¶](https://langchain-ai.github.io/langgraph/agents/run_agents/\#inputs-and-outputs "Permanent link")

Agents use a language model that expects a list of `messages` as an input. Therefore, agent inputs and outputs are stored as a list of `messages` under the `messages` key in the agent [state](https://langchain-ai.github.io/langgraph/concepts/low_level/#working-with-messages-in-graph-state).

## Input format [¶](https://langchain-ai.github.io/langgraph/agents/run_agents/\#input-format "Permanent link")

Agent input must be a dictionary with a `messages` key. Supported formats are:

| Format | Example |
| --- | --- |
| String | `{"messages": "Hello"}` — Interpreted as a [HumanMessage](https://python.langchain.com/docs/concepts/messages/#humanmessage) |
| Message dictionary | `{"messages": {"role": "user", "content": "Hello"}}` |
| List of messages | `{"messages": [{"role": "user", "content": "Hello"}]}` |
| With custom state | `{"messages": [{"role": "user", "content": "Hello"}], "user_name": "Alice"}` — If using a custom `state_schema` |

Messages are automatically converted into LangChain's internal message format. You can read
more about [LangChain messages](https://python.langchain.com/docs/concepts/messages/#langchain-messages) in the LangChain documentation.

Using custom agent state

You can provide additional fields defined in your agent’s state schema directly in the input dictionary. This allows dynamic behavior based on runtime data or prior tool outputs.

See the [context guide](https://langchain-ai.github.io/langgraph/agents/context/) for full details.

Note

A string input for `messages` is converted to a [HumanMessage](https://python.langchain.com/docs/concepts/messages/#humanmessage). This behavior differs from the `prompt` parameter in `create_react_agent`, which is interpreted as a [SystemMessage](https://python.langchain.com/docs/concepts/messages/#systemmessage) when passed as a string.

## Output format [¶](https://langchain-ai.github.io/langgraph/agents/run_agents/\#output-format "Permanent link")

Agent output is a dictionary containing:

- `messages`: A list of all messages exchanged during execution (user input, assistant replies, tool invocations).
- Optionally, `structured_response` if [structured output](https://langchain-ai.github.io/langgraph/agents/agents/#structured-output) is configured.
- If using a custom `state_schema`, additional keys corresponding to your defined fields may also be present in the output. These can hold updated state values from tool execution or prompt logic.

See the [context guide](https://langchain-ai.github.io/langgraph/agents/context/) for more details on working with custom state schemas and accessing context.

## Streaming output [¶](https://langchain-ai.github.io/langgraph/agents/run_agents/\#streaming-output "Permanent link")

Agents support streaming responses for more responsive applications. This includes:

- **Progress updates** after each step
- **LLM tokens** as they're generated
- **Custom tool messages** during execution

Streaming is available in both sync and async modes:

[Sync streaming](https://langchain-ai.github.io/langgraph/agents/run_agents/#__tabbed_2_1)[Async streaming](https://langchain-ai.github.io/langgraph/agents/run_agents/#__tabbed_2_2)

```md-code__content
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    stream_mode="updates"
):
    print(chunk)

```

```md-code__content
async for chunk in agent.astream(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    stream_mode="updates"
):
    print(chunk)

```

Tip

For full details, see the [streaming guide](https://langchain-ai.github.io/langgraph/agents/streaming/).

## Max iterations [¶](https://langchain-ai.github.io/langgraph/agents/run_agents/\#max-iterations "Permanent link")

To control agent execution and avoid infinite loops, set a recursion limit. This defines the maximum number of steps the agent can take before raising a `GraphRecursionError`. You can configure `recursion_limit` at runtime or when defining agent via `.with_config()`:

[Runtime](https://langchain-ai.github.io/langgraph/agents/run_agents/#__tabbed_3_1)[`.with_config()`](https://langchain-ai.github.io/langgraph/agents/run_agents/#__tabbed_3_2)

```md-code__content
from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import create_react_agent

max_iterations = 3
recursion_limit = 2 * max_iterations + 1
agent = create_react_agent(
    model="anthropic:claude-3-5-haiku-latest",
    tools=[get_weather]
)

try:
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "what's the weather in sf"}]},
        {"recursion_limit": recursion_limit},
    )
except GraphRecursionError:
    print("Agent stopped due to max iterations.")

```

```md-code__content
from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import create_react_agent

max_iterations = 3
recursion_limit = 2 * max_iterations + 1
agent = create_react_agent(
    model="anthropic:claude-3-5-haiku-latest",
    tools=[get_weather]
)
agent_with_recursion_limit = agent.with_config(recursion_limit=recursion_limit)

try:
    response = agent_with_recursion_limit.invoke(
        {"messages": [{"role": "user", "content": "what's the weather in sf"}]},
    )
except GraphRecursionError:
    print("Agent stopped due to max iterations.")

```

## Additional Resources [¶](https://langchain-ai.github.io/langgraph/agents/run_agents/\#additional-resources "Permanent link")

- [Async programming in LangChain](https://python.langchain.com/docs/concepts/async)

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fagents%2Frun_agents%2F)