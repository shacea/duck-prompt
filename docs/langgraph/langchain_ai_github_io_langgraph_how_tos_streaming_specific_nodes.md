[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/streaming-specific-nodes/#how-to-stream-llm-tokens-from-specific-nodes)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/streaming-specific-nodes.ipynb "Edit this page")

# How to stream LLM tokens from specific nodes [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming-specific-nodes/\#how-to-stream-llm-tokens-from-specific-nodes "Permanent link")

Prerequisites

This guide assumes familiarity with the following:

- [Streaming](https://langchain-ai.github.io/langgraph/concepts/streaming/)
- [Chat Models](https://python.langchain.com/docs/concepts/chat_models/)

A common use case when [streaming LLM tokens](https://langchain-ai.github.io/langgraph/how-tos/streaming-tokens) is to only stream them from specific nodes. To do so, you can use `stream_mode="messages"` and filter the outputs by the `langgraph_node` field in the streamed metadata:

```md-code__content
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI

model = ChatOpenAI()

def node_a(state: State):
    model.invoke(...)
    ...

def node_b(state: State):
    model.invoke(...)
    ...

graph = (
    StateGraph(State)
    .add_node(node_a)
    .add_node(node_b)
    ...
    .compile()

for msg, metadata in graph.stream(
    inputs,
    stream_mode="messages"
):
    # stream from 'node_a'
    if metadata["langgraph_node"] == "node_a":
        print(msg)

```

Streaming from a specific LLM invocation

If you need to instead filter streamed LLM tokens to a specific LLM invocation, check out [this guide](https://langchain-ai.github.io/langgraph/how-tos/streaming-tokens#filter-to-specific-llm-invocation)

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming-specific-nodes/\#setup "Permanent link")

First we need to install the packages required

```md-code__content
%%capture --no-stderr
%pip install --quiet -U langgraph langchain_openai

```

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")

```

## Example [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming-specific-nodes/\#example "Permanent link")

API Reference: [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html)

```md-code__content
from typing import TypedDict
from langgraph.graph import START, StateGraph, MessagesState
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o-mini")

class State(TypedDict):
    topic: str
    joke: str
    poem: str

def write_joke(state: State):
    topic = state["topic"]
    joke_response = model.invoke(
        [{"role": "user", "content": f"Write a joke about {topic}"}]
    )
    return {"joke": joke_response.content}

def write_poem(state: State):
    topic = state["topic"]
    poem_response = model.invoke(
        [{"role": "user", "content": f"Write a short poem about {topic}"}]
    )
    return {"poem": poem_response.content}

graph = (
    StateGraph(State)
    .add_node(write_joke)
    .add_node(write_poem)
    # write both the joke and the poem concurrently
    .add_edge(START, "write_joke")
    .add_edge(START, "write_poem")
    .compile()
)

```

```md-code__content
for msg, metadata in graph.stream(
    {"topic": "cats"},
    stream_mode="messages",
):
    if msg.content and metadata["langgraph_node"] == "write_poem":
        print(msg.content, end="|", flush=True)

```

```md-code__content
In| shadows| soft|,| they| quietly| creep|,|
|Wh|isk|ered| wonders|,| in| dreams| they| leap|.|
|With| eyes| like| lantern|s|,| bright| and| wide|,|
|Myst|eries| linger| where| they| reside|.|

|P|aws| that| pat|ter| on| silent| floors|,|
|Cur|led| in| sun|be|ams|,| they| seek| out| more|.|
|A| flick| of| a| tail|,| a| leap|,| a| p|ounce|,|
|In| their| playful| world|,| we| can't| help| but| bounce|.|

|Guard|ians| of| secrets|,| with| gentle| grace|,|
|Each| little| me|ow|,| a| warm| embrace|.|
|Oh|,| the| joy| that| they| bring|,| so| pure| and| true|,|
|In| the| heart| of| a| cat|,| there's| magic| anew|.|  |

```

## Comments

giscus

#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/3650)

👍1

#### [3 comments](https://github.com/langchain-ai/langgraph/discussions/3650)

#### ·

#### 2 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@Huyueeer](https://avatars.githubusercontent.com/u/40758588?u=572dfe5e13cafc5ae6484828d6d32f55afc4ace2&v=4)Huyueeer](https://github.com/Huyueeer) [Mar 1](https://github.com/langchain-ai/langgraph/discussions/3650#discussioncomment-12357995)

I have a question, how do I control which agent performs streaming output? For example, if mode is value

```notranslate
for msg, metadata in graph.stream(
    {"topic": "cats"},
    stream_mode="values",
):

```

1

2 replies

[![@tsensei](https://avatars.githubusercontent.com/u/65123233?u=2f7b6f3357d10c614f66638d839ade4a2387e574&v=4)](https://github.com/tsensei)

[tsensei](https://github.com/tsensei) [Mar 1](https://github.com/langchain-ai/langgraph/discussions/3650#discussioncomment-12359094)

Check the following code

```notranslate
async for event in graph.astream_events(
            graph_options, graph_config, version="v1"
        ):
            if event.get("event") == "on_chat_model_stream":
                # Extract and accumulate the chunk content
                message_content = event["data"]["chunk"].content

```

This event dict will have many identifiers, from there you can check and choose which node/(agent?) to let stream the output

👍1

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Mar 1](https://github.com/langchain-ai/langgraph/discussions/3650#discussioncomment-12360524)

Collaborator

we don't recommend using `astream_events`, you can filter either using metadata w/ stream mode messages, as per the guide or use `stream_mode=updates` and filter directly on the node (agent) that is performing the update

❤️1

[![@junbo2001](https://avatars.githubusercontent.com/u/50980865?u=4a506a974acdc6c03321d345dd5dd328b47c56be&v=4)junbo2001](https://github.com/junbo2001) [Mar 4](https://github.com/langchain-ai/langgraph/discussions/3650#discussioncomment-12382390)

我有一个需求，就是在我的图中有三个节点，node\_1、node\_2、node\_3，起始节点是node\_1，然后动态走向node\_2或者node\_3，是不固定的，最后有node\_2和node\_3分别走向结束 `END`，而在我的流式输出中设置的是 `stream_mode="messages"`（代码如下）：

```
    for msg, metadata in graph.stream(
            input={"messages": [HumanMessage(content)]},
            config=config,
            stream_mode="messages",
        ):
        if (
                msg.content
                and not isinstance(msg, HumanMessage)
                and metadata["langgraph_node"] == "node_2"
        ):
            yield msg.content
```

if条件中限制了 `metadata["langgraph_node"] == "node_2"`，然后当某些用户条件走到node\_3的时候，在node\_3节点中的输出内容返回不到客户端，然而我不知道怎么在if判断中动态获取图的走向，对于我的这个需求，我应该怎么调整？感谢各位前辈的指导。

1

0 replies

[![@sethi-ishmeet](https://avatars.githubusercontent.com/u/17765279?v=4)sethi-ishmeet](https://github.com/sethi-ishmeet) [yesterday](https://github.com/langchain-ai/langgraph/discussions/3650#discussioncomment-12916573)

How would you do this using LangGraph server APIs?

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fstreaming-specific-nodes%2F)