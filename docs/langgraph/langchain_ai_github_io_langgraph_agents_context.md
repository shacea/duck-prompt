[Skip to content](https://langchain-ai.github.io/langgraph/agents/context/#context)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/agents/context.md "Edit this page")

# Context [¶](https://langchain-ai.github.io/langgraph/agents/context/\#context "Permanent link")

Agents often require more than a list of messages to function effectively. They need **context**.

Context includes _any_ data outside the message list that can shape agent behavior or tool execution. This can be:

- Information passed at runtime, like a `user_id` or API credentials.
- Internal state updated during a multi-step reasoning process.
- Persistent memory or facts from previous interactions.

LangGraph provides **three** primary ways to supply context:

| Type | Description | Mutable? | Lifetime |
| --- | --- | --- | --- |
| [**Config**](https://langchain-ai.github.io/langgraph/agents/context/#config-static-context) | data passed at the start of a run | ❌ | per run |
| [**State**](https://langchain-ai.github.io/langgraph/agents/context/#state-mutable-context) | dynamic data that can change during execution | ✅ | per run or conversation |
| [**Long-term Memory (Store)**](https://langchain-ai.github.io/langgraph/agents/context/#long-term-memory-cross-conversation-context) | data that can be shared between conversations | ✅ | across conversations |

You can use context to:

- Adjust the system prompt the model sees
- Feed tools with necessary inputs
- Track facts during an ongoing conversation

## Providing Runtime Context [¶](https://langchain-ai.github.io/langgraph/agents/context/\#providing-runtime-context "Permanent link")

Use this when you need to inject data into an agent at runtime.

### Config (static context) [¶](https://langchain-ai.github.io/langgraph/agents/context/\#config-static-context "Permanent link")

Config is for immutable data like user metadata or API keys. Use
when you have values that don't change mid-run.

Specify configuration using a key called **"configurable"** which is reserved
for this purpose:

```md-code__content
agent.invoke(
    {"messages": [{"role": "user", "content": "hi!"}]},
    config={"configurable": {"user_id": "user_123"}}
)

```

### State (mutable context) [¶](https://langchain-ai.github.io/langgraph/agents/context/\#state-mutable-context "Permanent link")

State acts as short-term memory during a run. It holds dynamic data that can evolve during execution, such as values derived from tools or LLM outputs.

```md-code__content
class CustomState(AgentState):
    user_name: str

agent = create_react_agent(
    # Other agent parameters...
    state_schema=CustomState,
)

agent.invoke({
    "messages": "hi!",
    "user_name": "Jane"
})

```

Turning on memory

Please see the [memory guide](https://langchain-ai.github.io/langgraph/agents/memory/) for more details on how to enable memory. This is a powerful feature that allows you to persist the agent's state across multiple invocations.
Otherwise, the state is scoped only to a single agent run.

### Long-Term Memory (cross-conversation context) [¶](https://langchain-ai.github.io/langgraph/agents/context/\#long-term-memory-cross-conversation-context "Permanent link")

For context that spans _across_ conversations or sessions, LangGraph allows access to **long-term memory** via a `store`. This can be used to read or update persistent facts (e.g., user profiles, preferences, prior interactions). For more, see the [Memory guide](https://langchain-ai.github.io/langgraph/agents/memory/).

## Customizing Prompts with Context [¶](https://langchain-ai.github.io/langgraph/agents/context/\#customizing-prompts-with-context "Permanent link")

Prompts define how the agent behaves. To incorporate runtime context, you can dynamically generate prompts based on the agent's state or config.

Common use cases:

- Personalization
- Role or goal customization
- Conditional behavior (e.g., user is admin)

[Using config](https://langchain-ai.github.io/langgraph/agents/context/#__tabbed_1_1)[Using state](https://langchain-ai.github.io/langgraph/agents/context/#__tabbed_1_2)

```md-code__content
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

def prompt(
    state: AgentState,
    config: RunnableConfig,
) -> list[AnyMessage]:
    user_name = config.get("configurable", {}).get("user_name")
    system_msg = f"You are a helpful assistant. User's name is {user_name}"
    return [{"role": "system", "content": system_msg}] + state["messages"]

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    prompt=prompt
)

agent.invoke(
    ...,
    config={"configurable": {"user_name": "John Smith"}}
)

```

```md-code__content
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

class CustomState(AgentState):
    user_name: str

def prompt(
    state: CustomState
) -> list[AnyMessage]:
    user_name = state["user_name"]
    system_msg = f"You are a helpful assistant. User's name is {user_name}"
    return [{"role": "system", "content": system_msg}] + state["messages"]

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[...],
    state_schema=CustomState,
    prompt=prompt
)

agent.invoke({
    "messages": "hi!",
    "user_name": "John Smith"
})

```

## Tools [¶](https://langchain-ai.github.io/langgraph/agents/context/\#tools "Permanent link")

Tools can access context through special parameter **annotations**.

- Use `RunnableConfig` for config access
- Use `Annotated[StateSchema, InjectedState]` for agent state

Tip

These annotations prevent LLMs from attempting to fill in the values. These parameters will be **hidden** from the LLM.

[Using config](https://langchain-ai.github.io/langgraph/agents/context/#__tabbed_2_1)[Using State](https://langchain-ai.github.io/langgraph/agents/context/#__tabbed_2_2)

```md-code__content
def get_user_info(
    config: RunnableConfig,
) -> str:
    """Look up user info."""
    user_id = config.get("configurable", {}).get("user_id")
    return "User is John Smith" if user_id == "user_123" else "Unknown user"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_user_info],
)

agent.invoke(
    {"messages": [{"role": "user", "content": "look up user information"}]},
    config={"configurable": {"user_id": "user_123"}}
)

```

```md-code__content
from typing import Annotated
from langgraph.prebuilt import InjectedState

class CustomState(AgentState):
    user_id: str

def get_user_info(
    state: Annotated[CustomState, InjectedState]
) -> str:
    """Look up user info."""
    user_id = state["user_id"]
    return "User is John Smith" if user_id == "user_123" else "Unknown user"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_user_info],
    state_schema=CustomState,
)

agent.invoke({
    "messages": "look up user information",
    "user_id": "user_123"
})

```

## Update context from tools [¶](https://langchain-ai.github.io/langgraph/agents/context/\#update-context-from-tools "Permanent link")

Tools can modify the agent's state during execution. This is useful for persisting intermediate results or making information accessible to subsequent tools or prompts.

API Reference: [InjectedToolCallId](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.base.InjectedToolCallId.html) \| [ToolMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.tool.ToolMessage.html) \| [InjectedState](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.InjectedState) \| [Command](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Command)

```md-code__content
from typing import Annotated
from langchain_core.tools import InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

class CustomState(AgentState):
    user_name: str

def get_user_info(
    tool_call_id: Annotated[str, InjectedToolCallId],
    config: RunnableConfig
) -> Command:
    """Look up user info."""
    user_id = config.get("configurable", {}).get("user_id")
    name = "John Smith" if user_id == "user_123" else "Unknown user"
    return Command(update={
        "user_name": name,
        # update the message history
        "messages": [\
            ToolMessage(\
                "Successfully looked up user information",\
                tool_call_id=tool_call_id\
            )\
        ]
    })

def greet(
    state: Annotated[CustomState, InjectedState]
) -> str:
    """Use this to greet the user once you found their info."""
    user_name = state["user_name"]
    return f"Hello {user_name}!"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_user_info, greet],
    state_schema=CustomState
)

agent.invoke(
    {"messages": [{"role": "user", "content": "greet the user"}]},
    config={"configurable": {"user_id": "user_123"}}
)

```

For more details, see [how to update state from tools](https://langchain-ai.github.io/langgraph/how-tos/update-state-from-tools/).

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fagents%2Fcontext%2F)