[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/persistence/#how-to-add-thread-level-persistence-to-your-graph)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/persistence.ipynb "Edit this page")

# How to add thread-level persistence to your graph [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence/\#how-to-add-thread-level-persistence-to-your-graph "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [Memory](https://langchain-ai.github.io/langgraph/concepts/memory/)
- [Chat Models](https://python.langchain.com/docs/concepts/#chat-models/)

Not needed for LangGraph API users

If you're using the LangGraph API, you needn't manually implement a checkpointer. The API automatically handles checkpointing for you. This guide is relevant when implementing LangGraph in your own custom server.

Many AI applications need memory to share context across multiple interactions. In LangGraph, this kind of memory can be added to any [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.StateGraph) using [thread-level persistence](https://langchain-ai.github.io/langgraph/concepts/persistence) .

When creating any LangGraph graph, you can set it up to persist its state by adding a [checkpointer](https://langchain-ai.github.io/langgraph/reference/checkpoints/#basecheckpointsaver) when compiling the graph:

API Reference: [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver)

```md-code__content
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph.compile(checkpointer=checkpointer)

```

This guide shows how you can add thread-level persistence to your graph.

Note

If you need memory that is **shared** across multiple conversations or users (cross-thread persistence), check out this [how-to guide](https://langchain-ai.github.io/langgraph/how-tos/cross-thread-persistence/).


## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence/\#setup "Permanent link")

First we need to install the packages required

```md-code__content
%%capture --no-stderr
%pip install --quiet -U langgraph langchain_anthropic

```

Next, we need to set API key for Anthropic (the LLM we will use).

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("ANTHROPIC_API_KEY")

```

```md-code__content
ANTHROPIC_API_KEY:  ········

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Define graph [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence/\#define-graph "Permanent link")

We will be using a single-node graph that calls a [chat model](https://python.langchain.com/docs/concepts/#chat-models).

Let's first define the model we'll be using:

API Reference: [ChatAnthropic](https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html)

```md-code__content
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-3-5-sonnet-20240620")

```

Now we can define our `StateGraph` and add our model-calling node:

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START)

```md-code__content
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, MessagesState, START

def call_model(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": response}

builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_edge(START, "call_model")
graph = builder.compile()

```

If we try to use this graph, the context of the conversation will not be persisted across interactions:

```md-code__content
input_message = {"role": "user", "content": "hi! I'm bob"}
for chunk in graph.stream({"messages": [input_message]}, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

input_message = {"role": "user", "content": "what's my name?"}
for chunk in graph.stream({"messages": [input_message]}, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

```

```md-code__content
================================[1m Human Message [0m=================================\
\
hi! I'm bob\
==================================[1m Ai Message [0m==================================\
\
Hello Bob! It's nice to meet you. How are you doing today? Is there anything I can help you with or would you like to chat about something in particular?\
================================[1m Human Message [0m=================================\
\
what's my name?\
==================================[1m Ai Message [0m==================================\
\
I apologize, but I don't have access to your personal information, including your name. I'm an AI language model designed to provide general information and answer questions to the best of my ability based on my training data. I don't have any information about individual users or their personal details. If you'd like to share your name, you're welcome to do so, but I won't be able to recall it in future conversations.\
\
```\
\
## Add persistence [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence/\#add-persistence "Permanent link")\
\
To add in persistence, we need to pass in a [Checkpointer](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.base.BaseCheckpointSaver) when compiling the graph.\
\
API Reference: [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver)\
\
```md-code__content\
from langgraph.checkpoint.memory import MemorySaver\
\
memory = MemorySaver()\
graph = builder.compile(checkpointer=memory)\
# If you're using LangGraph Cloud or LangGraph Studio, you don't need to pass the checkpointer when compiling the graph, since it's done automatically.\
\
```\
\
Note\
\
If you're using LangGraph Cloud or LangGraph Studio, you **don't need** to pass checkpointer when compiling the graph, since it's done automatically.\
\
\
We can now interact with the agent and see that it remembers previous messages!\
\
```md-code__content\
config = {"configurable": {"thread_id": "1"}}\
input_message = {"role": "user", "content": "hi! I'm bob"}\
for chunk in graph.stream({"messages": [input_message]}, config, stream_mode="values"):\
    chunk["messages"][-1].pretty_print()\
\
```\
\
```md-code__content\
================================[1m Human Message [0m=================================\
\
hi! I'm bob\
==================================[1m Ai Message [0m==================================\
\
Hello Bob! It's nice to meet you. How are you doing today? Is there anything in particular you'd like to chat about or any questions you have that I can help you with?\
\
```\
\
You can always resume previous threads:\
\
```md-code__content\
input_message = {"role": "user", "content": "what's my name?"}\
for chunk in graph.stream({"messages": [input_message]}, config, stream_mode="values"):\
    chunk["messages"][-1].pretty_print()\
\
```\
\
```md-code__content\
================================[1m Human Message [0m=================================\
\
what's my name?\
==================================[1m Ai Message [0m==================================\
\
Your name is Bob, as you introduced yourself at the beginning of our conversation.\
\
```\
\
If we want to start a new conversation, we can pass in a different `thread_id`. Poof! All the memories are gone!\
\
```md-code__content\
input_message = {"role": "user", "content": "what's my name?"}\
for chunk in graph.stream(\
    {"messages": [input_message]},\
    {"configurable": {"thread_id": "2"}},\
    stream_mode="values",\
):\
    chunk["messages"][-1].pretty_print()\
\
```\
\
```md-code__content\
================================[1m Human Message [0m=================================\
\
what's is my name?\
==================================[1m Ai Message [0m==================================\
\
I apologize, but I don't have access to your personal information, including your name. As an AI language model, I don't have any information about individual users unless it's provided within the conversation. If you'd like to share your name, you're welcome to do so, but otherwise, I won't be able to know or guess it.\
\
```\
\
## Comments\
\
giscus\
\
#### [3 reactions](https://github.com/langchain-ai/langgraph/discussions/3696)\
\
❤️2🚀1\
\
#### [1 comment](https://github.com/langchain-ai/langgraph/discussions/3696)\
\
#### ·\
\
#### 1 reply\
\
_– powered by [giscus](https://giscus.app/)_\
\
- Oldest\
- Newest\
\
[![@satyaprakash1729](https://avatars.githubusercontent.com/u/3447411?v=4)satyaprakash1729](https://github.com/satyaprakash1729) [16 days ago](https://github.com/langchain-ai/langgraph/discussions/3696#discussioncomment-12763155)\
\
How do I ensure only last 10 messages are flown to Agent during the execution?\
\
Is there a way we can control what all messages are flown to the agent during execution as context?\
\
1\
\
1 reply\
\
[![@satyaprakash1729](https://avatars.githubusercontent.com/u/3447411?v=4)](https://github.com/satyaprakash1729)\
\
[satyaprakash1729](https://github.com/satyaprakash1729) [16 days ago](https://github.com/langchain-ai/langgraph/discussions/3696#discussioncomment-12766564)\
\
One more question - we're noticing that if the previous run has resulted in a failure due to tool call failure or any other reason then the subsequent runs (for same thread) are rejected with below error:\
\
```notranslate\
File "/usr/local/lib/python3.12/site-packages/langgraph/utils/runnable.py", line 359, in ainvoke\
    ret = await asyncio.create_task(coro, context=context)\
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\
\
  File "/usr/local/lib/python3.12/site-packages/langgraph/prebuilt/chat_agent_executor.py", line 695, in acall_model\
    _validate_chat_history(state["messages"])\
\
  File "/usr/local/lib/python3.12/site-packages/langgraph/prebuilt/chat_agent_executor.py", line 241, in _validate_chat_history\
    raise ValueError(error_message)\
\
ValueError: Found AIMessages with tool_calls that do not have a corresponding ToolMessage. Here are the first few of those tool calls:\
....\
\
Every tool call (LLM requesting to call a tool) in the message history MUST have a corresponding ToolMessage (result of a tool invocation to return to the LLM) - this is required by most LLM providers.\
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/INVALID_CHAT_HISTORY\
\
```\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fpersistence%2F)