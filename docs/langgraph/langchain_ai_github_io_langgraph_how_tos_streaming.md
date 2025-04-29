[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/streaming/#how-to-stream)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/streaming.ipynb "Edit this page")

# How to stream [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming/\#how-to-stream "Permanent link")

Prerequisites

This guide assumes familiarity with the following:

- [Streaming](https://langchain-ai.github.io/langgraph/concepts/streaming/)
- [Chat Models](https://python.langchain.com/docs/concepts/chat_models/)

Streaming is crucial for enhancing the responsiveness of applications built on LLMs. By displaying output progressively, even before a complete response is ready, streaming significantly improves user experience (UX), particularly when dealing with the latency of LLMs.

LangGraph is built with first class support for streaming. There are several different ways to stream back outputs from a graph run:

- `"values"`: Emit all values in the state after each step.
- `"updates"`: Emit only the node names and updates returned by the nodes after each step.
If multiple updates are made in the same step (e.g. multiple nodes are run) then those updates are emitted separately.
- `"custom"`: Emit custom data from inside nodes using `StreamWriter`.
- [`"messages"`](https://langchain-ai.github.io/langgraph/how-tos/streaming-tokens): Emit LLM messages token-by-token together with metadata for any LLM invocations inside nodes.
- `"debug"`: Emit debug events with as much information as possible for each step.

You can stream outputs from the graph by using `graph.stream(..., stream_mode=<stream_mode>)` method, e.g.:

[Sync](https://langchain-ai.github.io/langgraph/how-tos/streaming/#__tabbed_1_1)[Async](https://langchain-ai.github.io/langgraph/how-tos/streaming/#__tabbed_1_2)

```md-code__content
for chunk in graph.stream(inputs, stream_mode="updates"):
    print(chunk)

```

```md-code__content
async for chunk in graph.astream(inputs, stream_mode="updates"):
    print(chunk)

```

You can also combine multiple streaming mode by providing a list to `stream_mode` parameter:

[Sync](https://langchain-ai.github.io/langgraph/how-tos/streaming/#__tabbed_2_1)[Async](https://langchain-ai.github.io/langgraph/how-tos/streaming/#__tabbed_2_2)

```md-code__content
for chunk in graph.stream(inputs, stream_mode=["updates", "custom"]):
    print(chunk)

```

```md-code__content
async for chunk in graph.astream(inputs, stream_mode=["updates", "custom"]):
    print(chunk)

```

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming/\#setup "Permanent link")

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

```md-code__content
OPENAI_API_KEY:  ········

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


Let's define a simple graph with two nodes:

## Define graph [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming/\#define-graph "Permanent link")

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START)

```md-code__content
from typing import TypedDict
from langgraph.graph import StateGraph, START

class State(TypedDict):
    topic: str
    joke: str

def refine_topic(state: State):
    return {"topic": state["topic"] + " and cats"}

def generate_joke(state: State):
    return {"joke": f"This is a joke about {state['topic']}"}

graph = (
    StateGraph(State)
    .add_node(refine_topic)
    .add_node(generate_joke)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_joke")
    .compile()
)

```

## Stream all values in the state (stream\_mode="values") [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming/\#values "Permanent link")

Use this to stream **all values** in the state after each step.

```md-code__content
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode="values",
):
    print(chunk)

```

```md-code__content
{'topic': 'ice cream'}
{'topic': 'ice cream and cats'}
{'topic': 'ice cream and cats', 'joke': 'This is a joke about ice cream and cats'}

```

## Stream state updates from the nodes (stream\_mode="updates") [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming/\#updates "Permanent link")

Use this to stream only the **state updates** returned by the nodes after each step. The streamed outputs include the name of the node as well as the update.

```md-code__content
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode="updates",
):
    print(chunk)

```

```md-code__content
{'refine_topic': {'topic': 'ice cream and cats'}}
{'generate_joke': {'joke': 'This is a joke about ice cream and cats'}}

```

## Stream debug events (stream\_mode="debug") [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming/\#debug "Permanent link")

Use this to stream **debug events** with as much information as possible for each step. Includes information about tasks that were scheduled to be executed as well as the results of the task executions.

```md-code__content
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode="debug",
):
    print(chunk)

```

```md-code__content
{'type': 'task', 'timestamp': '2025-01-28T22:06:34.789803+00:00', 'step': 1, 'payload': {'id': 'eb305d74-3460-9510-d516-beed71a63414', 'name': 'refine_topic', 'input': {'topic': 'ice cream'}, 'triggers': ['start:refine_topic']}}
{'type': 'task_result', 'timestamp': '2025-01-28T22:06:34.790013+00:00', 'step': 1, 'payload': {'id': 'eb305d74-3460-9510-d516-beed71a63414', 'name': 'refine_topic', 'error': None, 'result': [('topic', 'ice cream and cats')], 'interrupts': []}}
{'type': 'task', 'timestamp': '2025-01-28T22:06:34.790165+00:00', 'step': 2, 'payload': {'id': '74355cb8-6284-25e0-579f-430493c1bdab', 'name': 'generate_joke', 'input': {'topic': 'ice cream and cats'}, 'triggers': ['refine_topic']}}
{'type': 'task_result', 'timestamp': '2025-01-28T22:06:34.790337+00:00', 'step': 2, 'payload': {'id': '74355cb8-6284-25e0-579f-430493c1bdab', 'name': 'generate_joke', 'error': None, 'result': [('joke', 'This is a joke about ice cream and cats')], 'interrupts': []}}

```

## Stream LLM tokens ( [stream\_mode="messages"](https://langchain-ai.github.io/langgraph/how-tos/streaming-tokens)) [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming/\#messages "Permanent link")

Use this to stream **LLM messages token-by-token** together with metadata for any LLM invocations inside nodes or tasks. Let's modify the above example to include LLM calls:

API Reference: [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html)

```md-code__content
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

def generate_joke(state: State):
    llm_response = llm.invoke(
        [\
            {"role": "user", "content": f"Generate a joke about {state['topic']}"}\
        ]
    )
    return {"joke": llm_response.content}

graph = (
    StateGraph(State)
    .add_node(refine_topic)
    .add_node(generate_joke)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_joke")
    .compile()
)

```

```md-code__content
for message_chunk, metadata in graph.stream(
    {"topic": "ice cream"},
    stream_mode="messages",
):
    if message_chunk.content:
        print(message_chunk.content, end="|", flush=True)

```

```md-code__content
Why| did| the| cat| sit| on| the| ice| cream| cone|?

|Because| it| wanted| to| be| a| "|p|urr|-f|ect|"| scoop|!| 🍦|🐱|

```

```md-code__content
metadata

```

```md-code__content
{'langgraph_step': 2,
 'langgraph_node': 'generate_joke',
 'langgraph_triggers': ['refine_topic'],
 'langgraph_path': ('__pregel_pull', 'generate_joke'),
 'langgraph_checkpoint_ns': 'generate_joke:568879bc-8800-2b0d-a5b5-059526a4bebf',
 'checkpoint_ns': 'generate_joke:568879bc-8800-2b0d-a5b5-059526a4bebf',
 'ls_provider': 'openai',
 'ls_model_name': 'gpt-4o-mini',
 'ls_model_type': 'chat',
 'ls_temperature': 0.7}

```

## Stream custom data (stream\_mode="custom") [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming/\#custom "Permanent link")

Use this to stream custom data from inside nodes using [`StreamWriter`](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.StreamWriter "<code class=\"doc-symbol doc-symbol-heading doc-symbol-attribute\"></code>            <span class=\"doc doc-object-name doc-attribute-name\">StreamWriter</span>     <span class=\"doc doc-labels\">       <small class=\"doc doc-label doc-label-module-attribute\"><code>module-attribute</code></small>   </span>").

API Reference: [StreamWriter](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.StreamWriter)

```md-code__content
from langgraph.types import StreamWriter

def generate_joke(state: State, writer: StreamWriter):
    writer({"custom_key": "Writing custom data while generating a joke"})
    return {"joke": f"This is a joke about {state['topic']}"}

graph = (
    StateGraph(State)
    .add_node(refine_topic)
    .add_node(generate_joke)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_joke")
    .compile()
)

```

```md-code__content
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode="custom",
):
    print(chunk)

```

```md-code__content
{'custom_key': 'Writing custom data while generating a joke'}

```

## Configure multiple streaming modes [¶](https://langchain-ai.github.io/langgraph/how-tos/streaming/\#multiple "Permanent link")

Use this to combine multiple streaming modes. The outputs are streamed as tuples `(stream_mode, streamed_output)`.

```md-code__content
for stream_mode, chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode=["updates", "custom"],
):
    print(f"Stream mode: {stream_mode}")
    print(chunk)
    print("\n")

```

```md-code__content
Stream mode: updates
{'refine_topic': {'topic': 'ice cream and cats'}}

Stream mode: custom
{'custom_key': 'Writing custom data while generating a joke'}

Stream mode: updates
{'generate_joke': {'joke': 'This is a joke about ice cream and cats'}}

```

## Comments

giscus

#### [2 reactions](https://github.com/langchain-ai/langgraph/discussions/3768)

👍2

#### [6 comments](https://github.com/langchain-ai/langgraph/discussions/3768)

#### ·

#### 5 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@manuelImageMakerLatam](https://avatars.githubusercontent.com/u/141082230?v=4)manuelImageMakerLatam](https://github.com/manuelImageMakerLatam) [Mar 19](https://github.com/langchain-ai/langgraph/discussions/3768#discussioncomment-12555584)

In the latest version (langgraph==0.3.14) the shared key with the state of the parent graph is not being updated.

1

0 replies

[![@simon-lighthouse](https://avatars.githubusercontent.com/u/125604509?u=e437b42a6b8e58beafc043d28db48aba38674939&v=4)simon-lighthouse](https://github.com/simon-lighthouse) [Mar 23](https://github.com/langchain-ai/langgraph/discussions/3768#discussioncomment-12594968)

What doesn't seem clear here, is how to stream with a structured output parser on an LLM. When I do so, I get incomplete JSON under the 'content' key. e.g. {"content": "{\\n "summary": "• The LIM"} which fails in front end parsing. I have tried to implement a JSONOutputParser but this doesn't impact the LLM run which is streamed, it only runs at the end of the LLM call

1

1 reply

[![@Veshek](https://avatars.githubusercontent.com/u/46017835?v=4)](https://github.com/Veshek)

[Veshek](https://github.com/Veshek) [23 days ago](https://github.com/langchain-ai/langgraph/discussions/3768#discussioncomment-12693388)

If you're using the langgraph api, then you could setup a websocket and stream the messages using a for loop like this. Not sure how exactly you will handle the streamed messages on the frontend though :

async def stream\_response(user\_input: str):

"""Stream response from LangGraph agent."""

\# Replace this with the URL of your own deployed graph

client = get\_client(url=LANGGRAPH\_SERVER)

input\_message = HumanMessage(content=user\_input)

thread = await client.threads.create()

\# Start conversation with the initial message

async for event in client.runs.stream(thread\["thread\_id"\],

assistant\_id="agent",

input={"messages": \[input\_message\],"user\_id":"1"},

stream\_mode="messages-tuple"):

if event.event == 'messages':

yield event.data\[0\]\["content"\]

[![@YisusLinkon](https://avatars.githubusercontent.com/u/97560623?u=e755eae9235fc9d9efbb817bb1a18b4f08b815a3&v=4)YisusLinkon](https://github.com/YisusLinkon) [27 days ago](https://github.com/langchain-ai/langgraph/discussions/3768#discussioncomment-12646716)

I require to invoke my graph fron a specific node, any of you knows how to do this?

I'm doing this:

invoke = await compiled\_graph.ainvoke(agent\_state)

I would like to be able to specify the node name to continue an in-progress execution

1

2 replies

[![@XiaoLiuAI](https://avatars.githubusercontent.com/u/1553482?v=4)](https://github.com/XiaoLiuAI)

[XiaoLiuAI](https://github.com/XiaoLiuAI) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/3768#discussioncomment-12695151)

I tried that as well, but astream does not return any subgraph output as well as llm token (stream does).

[![@RalissonMattias](https://avatars.githubusercontent.com/u/92331757?u=e97dcb47b824debdf0b029445196087f20e1080d&v=4)](https://github.com/RalissonMattias)

[RalissonMattias](https://github.com/RalissonMattias) [17 days ago](https://github.com/langchain-ai/langgraph/discussions/3768#discussioncomment-12744609)

+1

[![@XiaoLiuAI](https://avatars.githubusercontent.com/u/1553482?v=4)XiaoLiuAI](https://github.com/XiaoLiuAI) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/3768#discussioncomment-12695142)

The code in tutor works, but when I switch stream to astream, subgraph outputs are gone. How can I stream subgraph output with async?

1

👍1

0 replies

[![@crazyyanchao](https://avatars.githubusercontent.com/u/19403898?u=653236a54c30bcaf89100a4eb3f6684c97be8664&v=4)crazyyanchao](https://github.com/crazyyanchao) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/3768#discussioncomment-12697358)

Great article. Also, I wanted to ask, graph.get\_graph().draw\_mermaid doesn't visualize subgraphs very well. Are there any better visualization functions that can be used for this?

1

1 reply

[![@crazyyanchao](https://avatars.githubusercontent.com/u/19403898?u=653236a54c30bcaf89100a4eb3f6684c97be8664&v=4)](https://github.com/crazyyanchao)

[crazyyanchao](https://github.com/crazyyanchao) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/3768#discussioncomment-12697496)

I overlooked using the parameters, but now it works perfectly! set xray=1

```
print(graph.get_graph(xray=1).draw_mermaid(
    node_colors=NodeStyles(
        default="fill:#ffe6e6,stroke:#ff6666,stroke-width:2px,line-height:1.2",
        first="fill-opacity:0,stroke:#ff6666",
        last="fill:#ff6666,stroke:#b80000")
))
```

[![@palakkala](https://avatars.githubusercontent.com/u/6775553?v=4)palakkala](https://github.com/palakkala) [17 days ago](https://github.com/langchain-ai/langgraph/discussions/3768#discussioncomment-12754114)

how to stream when subgraph=True

1

1 reply

[![@palakkala](https://avatars.githubusercontent.com/u/6775553?v=4)](https://github.com/palakkala)

[palakkala](https://github.com/palakkala) [17 days ago](https://github.com/langchain-ai/langgraph/discussions/3768#discussioncomment-12754209)

trying to implement streaming in router as start

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fstreaming%2F)