[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/memory/semantic-search/#how-to-add-semantic-search-to-your-agents-memory)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/memory/semantic-search.ipynb "Edit this page")

# How to add semantic search to your agent's memory [¶](https://langchain-ai.github.io/langgraph/how-tos/memory/semantic-search/\#how-to-add-semantic-search-to-your-agents-memory "Permanent link")

This guide shows how to enable semantic search in your agent's memory store. This lets search for items in the store by semantic similarity.

Tip

This guide assumes familiarity with the [memory in LangGraph](https://langchain-ai.github.io/langgraph/concepts/memory/).

First, install this guide's prerequisites.

```md-code__content
%%capture --no-stderr
%pip install -U langgraph langchain-openai langchain

```

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")

```

Next, create the store with an [index configuration](https://langchain-ai.github.io/langgraph/reference/store/#langgraph.store.base.IndexConfig). By default, stores are configured without semantic/vector search. You can opt in to indexing items when creating the store by providing an [IndexConfig](https://langchain-ai.github.io/langgraph/reference/store/#langgraph.store.base.IndexConfig) to the store's constructor. If your store class does not implement this interface, or if you do not pass in an index configuration, semantic search is disabled, and all `index` arguments passed to `put` or `aput` will have no effect. Below is an example.

API Reference: [init\_embeddings](https://python.langchain.com/api_reference/langchain/embeddings/langchain.embeddings.base.init_embeddings.html)

```md-code__content
from langchain.embeddings import init_embeddings
from langgraph.store.memory import InMemoryStore

# Create store with semantic search enabled
embeddings = init_embeddings("openai:text-embedding-3-small")
store = InMemoryStore(
    index={
        "embed": embeddings,
        "dims": 1536,
    }
)

```

```md-code__content
/var/folders/gf/6rnp_mbx5914kx7qmmh7xzmw0000gn/T/ipykernel_83572/2318027494.py:5: LangChainBetaWarning: The function `init_embeddings` is in beta. It is actively being worked on, so the API may change.
  embeddings = init_embeddings("openai:text-embedding-3-small")

```

Now let's store some memories:

```md-code__content
# Store some memories
store.put(("user_123", "memories"), "1", {"text": "I love pizza"})
store.put(("user_123", "memories"), "2", {"text": "I prefer Italian food"})
store.put(("user_123", "memories"), "3", {"text": "I don't like spicy food"})
store.put(("user_123", "memories"), "3", {"text": "I am studying econometrics"})
store.put(("user_123", "memories"), "3", {"text": "I am a plumber"})

```

Search memories using natural language:

```md-code__content
# Find memories about food preferences
memories = store.search(("user_123", "memories"), query="I like food?", limit=5)

for memory in memories:
    print(f'Memory: {memory.value["text"]} (similarity: {memory.score})')

```

```md-code__content
Memory: I prefer Italian food (similarity: 0.46482669521168163)
Memory: I love pizza (similarity: 0.35514845174380766)
Memory: I am a plumber (similarity: 0.155698702336571)

```

## Using in your agent [¶](https://langchain-ai.github.io/langgraph/how-tos/memory/semantic-search/\#using-in-your-agent "Permanent link")

Add semantic search to any node by injecting the store.

API Reference: [init\_chat\_model](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph)

```md-code__content
from typing import Optional

from langchain.chat_models import init_chat_model
from langgraph.store.base import BaseStore

from langgraph.graph import START, MessagesState, StateGraph

llm = init_chat_model("openai:gpt-4o-mini")

def chat(state, *, store: BaseStore):
    # Search based on user's last message
    items = store.search(
        ("user_123", "memories"), query=state["messages"][-1].content, limit=2
    )
    memories = "\n".join(item.value["text"] for item in items)
    memories = f"## Memories of user\n{memories}" if memories else ""
    response = llm.invoke(
        [\
            {"role": "system", "content": f"You are a helpful assistant.\n{memories}"},\
            *state["messages"],\
        ]
    )
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node(chat)
builder.add_edge(START, "chat")
graph = builder.compile(store=store)

for message, metadata in graph.stream(
    input={"messages": [{"role": "user", "content": "I'm hungry"}]},
    stream_mode="messages",
):
    print(message.content, end="")

```

```md-code__content
What are you in the mood for? Since you love Italian food and pizza, would you like to order a pizza or try making one at home?

```

## Using in `create_react_agent` [¶](https://langchain-ai.github.io/langgraph/how-tos/memory/semantic-search/\#using-in-create-react-agent "Permanent link")

Add semantic search to your tool calling agent by injecting the store in the `prompt` function. You can also use the store in a tool to let your agent manually store or search for memories.

API Reference: [init\_chat\_model](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

```md-code__content
import uuid
from typing import Optional

from langchain.chat_models import init_chat_model
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore
from typing_extensions import Annotated

from langgraph.prebuilt import create_react_agent

def prepare_messages(state, *, store: BaseStore):
    # Search based on user's last message
    items = store.search(
        ("user_123", "memories"), query=state["messages"][-1].content, limit=2
    )
    memories = "\n".join(item.value["text"] for item in items)
    memories = f"## Memories of user\n{memories}" if memories else ""
    return [\
        {"role": "system", "content": f"You are a helpful assistant.\n{memories}"}\
    ] + state["messages"]

# You can also use the store directly within a tool!
def upsert_memory(
    content: str,
    *,
    memory_id: Optional[uuid.UUID] = None,
    store: Annotated[BaseStore, InjectedStore],
):
    """Upsert a memory in the database."""
    # The LLM can use this tool to store a new memory
    mem_id = memory_id or uuid.uuid4()
    store.put(
        ("user_123", "memories"),
        key=str(mem_id),
        value={"text": content},
    )
    return f"Stored memory {mem_id}"

agent = create_react_agent(
    init_chat_model("openai:gpt-4o-mini"),
    tools=[upsert_memory],
    # The 'prompt' function is run to prepare the messages for the LLM. It is called
    # right before each LLM call
    prompt=prepare_messages,
    store=store,
)

```

```md-code__content
for message, metadata in agent.stream(
    input={"messages": [{"role": "user", "content": "I'm hungry"}]},
    stream_mode="messages",
):
    print(message.content, end="")

```

```md-code__content
What are you in the mood for? Since you love Italian food and pizza, maybe something in that realm would be great! Would you like suggestions for a specific dish or restaurant?

```

## Advanced Usage [¶](https://langchain-ai.github.io/langgraph/how-tos/memory/semantic-search/\#advanced-usage "Permanent link")

#### Multi-vector indexing [¶](https://langchain-ai.github.io/langgraph/how-tos/memory/semantic-search/\#multi-vector-indexing "Permanent link")

Store and search different aspects of memories separately to improve recall or omit certain fields from being indexed.

```md-code__content
# Configure store to embed both memory content and emotional context
store = InMemoryStore(
    index={"embed": embeddings, "dims": 1536, "fields": ["memory", "emotional_context"]}
)
# Store memories with different content/emotion pairs
store.put(
    ("user_123", "memories"),
    "mem1",
    {
        "memory": "Had pizza with friends at Mario's",
        "emotional_context": "felt happy and connected",
        "this_isnt_indexed": "I prefer ravioli though",
    },
)
store.put(
    ("user_123", "memories"),
    "mem2",
    {
        "memory": "Ate alone at home",
        "emotional_context": "felt a bit lonely",
        "this_isnt_indexed": "I like pie",
    },
)

# Search focusing on emotional state - matches mem2
results = store.search(
    ("user_123", "memories"), query="times they felt isolated", limit=1
)
print("Expect mem 2")
for r in results:
    print(f"Item: {r.key}; Score ({r.score})")
    print(f"Memory: {r.value['memory']}")
    print(f"Emotion: {r.value['emotional_context']}\n")

# Search focusing on social eating - matches mem1
print("Expect mem1")
results = store.search(("user_123", "memories"), query="fun pizza", limit=1)
for r in results:
    print(f"Item: {r.key}; Score ({r.score})")
    print(f"Memory: {r.value['memory']}")
    print(f"Emotion: {r.value['emotional_context']}\n")

print("Expect random lower score (ravioli not indexed)")
results = store.search(("user_123", "memories"), query="ravioli", limit=1)
for r in results:
    print(f"Item: {r.key}; Score ({r.score})")
    print(f"Memory: {r.value['memory']}")
    print(f"Emotion: {r.value['emotional_context']}\n")

```

```md-code__content
Expect mem 2
Item: mem2; Score (0.5895009051396596)
Memory: Ate alone at home
Emotion: felt a bit lonely

Expect mem1
Item: mem1; Score (0.6207546534134083)
Memory: Had pizza with friends at Mario's
Emotion: felt happy and connected

Expect random lower score (ravioli not indexed)
Item: mem1; Score (0.2686278787315685)
Memory: Had pizza with friends at Mario's
Emotion: felt happy and connected

```

#### Override fields at storage time [¶](https://langchain-ai.github.io/langgraph/how-tos/memory/semantic-search/\#override-fields-at-storage-time "Permanent link")

You can override which fields to embed when storing a specific memory using `put(..., index=[...fields])`, regardless of the store's default configuration.

```md-code__content
store = InMemoryStore(
    index={
        "embed": embeddings,
        "dims": 1536,
        "fields": ["memory"],
    }  # Default to embed memory field
)

# Store one memory with default indexing
store.put(
    ("user_123", "memories"),
    "mem1",
    {"memory": "I love spicy food", "context": "At a Thai restaurant"},
)

# Store another overriding which fields to embed
store.put(
    ("user_123", "memories"),
    "mem2",
    {"memory": "The restaurant was too loud", "context": "Dinner at an Italian place"},
    index=["context"],  # Override: only embed the context
)

# Search about food - matches mem1 (using default field)
print("Expect mem1")
results = store.search(
    ("user_123", "memories"), query="what food do they like", limit=1
)
for r in results:
    print(f"Item: {r.key}; Score ({r.score})")
    print(f"Memory: {r.value['memory']}")
    print(f"Context: {r.value['context']}\n")

# Search about restaurant atmosphere - matches mem2 (using overridden field)
print("Expect mem2")
results = store.search(
    ("user_123", "memories"), query="restaurant environment", limit=1
)
for r in results:
    print(f"Item: {r.key}; Score ({r.score})")
    print(f"Memory: {r.value['memory']}")
    print(f"Context: {r.value['context']}\n")

```

```md-code__content
Expect mem1
Item: mem1; Score (0.3374968677940555)
Memory: I love spicy food
Context: At a Thai restaurant

Expect mem2
Item: mem2; Score (0.36784461593247436)
Memory: The restaurant was too loud
Context: Dinner at an Italian place

```

#### Disable Indexing for Specific Memories [¶](https://langchain-ai.github.io/langgraph/how-tos/memory/semantic-search/\#disable-indexing-for-specific-memories "Permanent link")

Some memories shouldn't be searchable by content. You can disable indexing for these while still storing them using
`put(..., index=False)`. Example:

```md-code__content
store = InMemoryStore(index={"embed": embeddings, "dims": 1536, "fields": ["memory"]})

# Store a normal indexed memory
store.put(
    ("user_123", "memories"),
    "mem1",
    {"memory": "I love chocolate ice cream", "type": "preference"},
)

# Store a system memory without indexing
store.put(
    ("user_123", "memories"),
    "mem2",
    {"memory": "User completed onboarding", "type": "system"},
    index=False,  # Disable indexing entirely
)

# Search about food preferences - finds mem1
print("Expect mem1")
results = store.search(("user_123", "memories"), query="what food preferences", limit=1)
for r in results:
    print(f"Item: {r.key}; Score ({r.score})")
    print(f"Memory: {r.value['memory']}")
    print(f"Type: {r.value['type']}\n")

# Search about onboarding - won't find mem2 (not indexed)
print("Expect low score (mem2 not indexed)")
results = store.search(("user_123", "memories"), query="onboarding status", limit=1)
for r in results:
    print(f"Item: {r.key}; Score ({r.score})")
    print(f"Memory: {r.value['memory']}")
    print(f"Type: {r.value['type']}\n")

```

```md-code__content
Expect mem1
Item: mem1; Score (0.32269984224327286)
Memory: I love chocolate ice cream
Type: preference

Expect low score (mem2 not indexed)
Item: mem1; Score (0.010241633698527089)
Memory: I love chocolate ice cream
Type: preference

```

## Comments

giscus

#### [2 reactions](https://github.com/langchain-ai/langgraph/discussions/2769)

👍2

#### [2 comments](https://github.com/langchain-ai/langgraph/discussions/2769)

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@Michailbul](https://avatars.githubusercontent.com/u/137901836?u=e3e42050a917aef6f4ed1eb7ff91d869eb827424&v=4)Michailbul](https://github.com/Michailbul) [Dec 16, 2024](https://github.com/langchain-ai/langgraph/discussions/2769#discussioncomment-11575772)

Where can i find documentation for langraph.store.memory? to use third party store like pinecone or qdrant?

thanks!

1

👍5

0 replies

[![@sriakhil25](https://avatars.githubusercontent.com/u/165472988?u=7e9a463e931df9db2e87a8ce006aea57330f9cef&v=4)sriakhil25](https://github.com/sriakhil25) [Jan 12](https://github.com/langchain-ai/langgraph/discussions/2769#discussioncomment-11813251)

There seems an error while running this part of the code - Its making call to upset\_memory where the error exists.

for message, metadata in agent.stream(

input={"messages": \[{"role": "user", "content": "I'm hungry"}\]},

stream\_mode="messages",

):

print(message.content, end="")

Error: 1 validation error for upsert\_memory

store

Field required \[type=missing, input\_value={'content': "I'm hungry"}, input\_type=dict\]

For further information visit [https://errors.pydantic.dev/2.9/v/missing](https://errors.pydantic.dev/2.9/v/missing)

Please fix your mistakes. It seems there was an error in the code related to the upsert\_memory function. The error message suggests that the 'content' field is required but it is missing from the input data. You should make sure that the content field is included when calling the upsert\_memory function. Here's an example of how you can call the function with the correct format:

```
upsert_memory(content="I'm hungry")
```

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fmemory%2Fsemantic-search%2F)