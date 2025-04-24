[Skip to content](https://langchain-ai.github.io/langgraph/agents/memory/#memory)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/agents/memory.md "Edit this page")

# Memory [¶](https://langchain-ai.github.io/langgraph/agents/memory/\#memory "Permanent link")

LangGraph supports two types of memory essential for building conversational agents:

- **[Short-term memory](https://langchain-ai.github.io/langgraph/agents/memory/#short-term-memory)**: Tracks the ongoing conversation by maintaining message history within a session.
- **[Long-term memory](https://langchain-ai.github.io/langgraph/agents/memory/#long-term-memory)**: Stores user-specific or application-level data across sessions.

This guide demonstrates how to use both memory types with agents in LangGraph. For a deeper
understanding of memory concepts, refer to the [LangGraph memory documentation](https://langchain-ai.github.io/langgraph/concepts/memory/).

![image](https://langchain-ai.github.io/langgraph/agents/assets/memory.png)

Both **short-term** and **long-term** memory require persistent storage to maintain continuity across LLM interactions. In production environments, this data is typically stored in a database.

Terminology

In LangGraph:

- _Short-term memory_ is also referred to as **thread-level memory**.
- _Long-term memory_ is also called **cross-thread memory**.

A [thread](https://langchain-ai.github.io/langgraph/concepts/persistence/#threads) represents a sequence of related runs
grouped by the same `thread_id`.

## Short-term memory [¶](https://langchain-ai.github.io/langgraph/agents/memory/\#short-term-memory "Permanent link")

Short-term memory enables agents to track multi-turn conversations. To use it, you must:

1. Provide a `checkpointer` when creating the agent. The `checkpointer` enables [persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/) of the agent's state.
2. Supply a `thread_id` in the config when running the agent. The `thread_id` is a unique identifier for the conversation session.

API Reference: [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) \| [InMemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.InMemorySaver)

```md-code__content
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    checkpointer=checkpointer
)

# Run the agent
config = {
    "configurable": {
        "thread_id": "1"
    }
}

sf_response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]},
    config
)

# Continue the conversation using the same thread_id
ny_response = agent.invoke(
    {"messages": [{"role": "user", "content": "what about new york?"}]},
    config
)

```

When the agent is invoked the second time with the same `thread_id`, the original message history from the first conversation is automatically included, allowing the agent to infer that the user is asking specifically about the **weather** in New York.

LangGraph Platform providers a production-ready checkpointer

If you're using [LangGraph Platform](https://langchain-ai.github.io/langgraph/agents/deployment/), during deployment your checkpointer will be automatically configured to use a production-ready database.

### Message history summarization [¶](https://langchain-ai.github.io/langgraph/agents/memory/\#message-history-summarization "Permanent link")

![image](https://langchain-ai.github.io/langgraph/agents/assets/summary.png)

Message history can grow quickly and exceed the LLM's context window. A common solution is to maintain a running summary of the conversation. This allows the agent to keep track of the conversation without exceeding the LLM's context window.

Long conversations can exceed the LLM's context window. To handle this, you can summarize older messages by specifying a [`pre_model_hook`](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent "<code class=\"doc-symbol doc-symbol-heading doc-symbol-function\"></code>            <span class=\"doc doc-object-name doc-function-name\">create_react_agent</span>"), such as the prebuilt [`SummarizationNode`](https://langchain-ai.github.io/langmem/reference/short_term/#langmem.short_term.SummarizationNode):

API Reference: [ChatAnthropic](https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html) \| [count\_tokens\_approximately](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.utils.count_tokens_approximately.html) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) \| [InMemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.InMemorySaver)

```md-code__content
from langchain_anthropic import ChatAnthropic
from langmem.short_term import SummarizationNode
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.checkpoint.memory import InMemorySaver
from typing import Any

model = ChatAnthropic(model="claude-3-7-sonnet-latest")

summarization_node = SummarizationNode(
    token_counter=count_tokens_approximately,
    model=model,
    max_tokens=384,
    max_summary_tokens=128,
    output_messages_key="llm_input_messages",
)

class State(AgentState):
    # NOTE: we're adding this key to keep track of previous summary information
    # to make sure we're not summarizing on every LLM call
    context: dict[str, Any]

checkpointer = InMemorySaver()

agent = create_react_agent(
    model=model,
    tools=tools,
    pre_model_hook=summarization_node,
    state_schema=State,
    checkpointer=checkpointer,
)

```

To learn more about using `pre_model_hook` for managing message history, see this [how-to guide](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-manage-message-history/)

## Long-term memory [¶](https://langchain-ai.github.io/langgraph/agents/memory/\#long-term-memory "Permanent link")

Use long-term memory to store user-specific or application-specific data across conversations. This is useful for applications like chatbots, where you want to remember user preferences or other information.

To use long-term memory, you need to:

1. [Configure a store](https://langchain-ai.github.io/langgraph/how-tos/cross-thread-persistence/) to persist data across invocations.
2. Use the [`get_store`](https://langchain-ai.github.io/langgraph/reference/config/#langgraph.config.get_store "<code class=\"doc-symbol doc-symbol-heading doc-symbol-function\"></code>            <span class=\"doc doc-object-name doc-function-name\">get_store</span>") function to access the store from within tools or prompts.

### Reading [¶](https://langchain-ai.github.io/langgraph/agents/memory/\#reading "Permanent link")

A tool the agent can use to look up user information

```md-code__content
from langgraph.config import get_store
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

store.put(
    ("users",),
    "user_123",
    {
        "name": "John Smith",
        "language": "English",
    }
)

def get_user_info(config: RunnableConfig) -> str:
    """Look up user info."""
    # Same as that provided to `create_react_agent`
    store = get_store()
    user_id = config.get("configurable", {}).get("user_id")
    user_info = store.get(("users",), user_id)
    return str(user_info.value) if user_info else "Unknown user"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_user_info],
    store=store
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "look up user information"}]},
    config={"configurable": {"user_id": "user_123"}}
)

```

### Writing [¶](https://langchain-ai.github.io/langgraph/agents/memory/\#writing "Permanent link")

Example of a tool that updates user information

```md-code__content
from typing_extensions import TypedDict

from langgraph.config import get_store
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

class UserInfo(TypedDict):
    name: str

def save_user_info(user_info: UserInfo, config: RunnableConfig) -> str:
    """Save user info."""
    # Same as that provided to `create_react_agent`
    store = get_store()
    user_id = config.get("configurable", {}).get("user_id")
    store.put(("users",), user_id, user_info)
    return "Successfully saved user info."

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[save_user_info],
    store=store
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "My name is John Smith"}]},
    config={"configurable": {"user_id": "user_123"}}
)

# You can access the store directly to get the value
store.get(("users",), "user_123").value

```

### Prebuilt memory tools [¶](https://langchain-ai.github.io/langgraph/agents/memory/\#prebuilt-memory-tools "Permanent link")

**LangMem** is a LangChain-maintained library that offers tools for managing long-term memories in your agent. See the [LangMem documentation](https://langchain-ai.github.io/langmem/) for usage examples.

## Additional resources [¶](https://langchain-ai.github.io/langgraph/agents/memory/\#additional-resources "Permanent link")

- [Memory in LangGraph](https://langchain-ai.github.io/langgraph/concepts/memory/)

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fagents%2Fmemory%2F)