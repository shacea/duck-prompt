[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/state-reducers/#how-to-update-graph-state-from-nodes)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/state-reducers.ipynb "Edit this page")

# How to update graph state from nodes [¶](https://langchain-ai.github.io/langgraph/how-tos/state-reducers/\#how-to-update-graph-state-from-nodes "Permanent link")

This guide demonstrates how to define and update [state](https://langchain-ai.github.io/langgraph/concepts/low_level/#state) in LangGraph. We will demonstrate:

1. How to use state to define a graph's [schema](https://langchain-ai.github.io/langgraph/concepts/low_level/#schema)
2. How to use [reducers](https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers) to control how state updates are processed.

We will use [messages](https://langchain-ai.github.io/langgraph/concepts/low_level/#messagesstate) in our examples. This represents a versatile formulation of state for many LLM applications. See our [concepts page](https://langchain-ai.github.io/langgraph/concepts/low_level/#working-with-messages-in-graph-state) for more detail.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/state-reducers/\#setup "Permanent link")

First, let's install langgraph:

```md-code__content
%%capture --no-stderr
%pip install -U langgraph

```

Set up [LangSmith](https://smith.langchain.com/) for better debugging

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM aps built with LangGraph — read more about how to get started in the [docs](https://docs.smith.langchain.com/).


## Example graph [¶](https://langchain-ai.github.io/langgraph/how-tos/state-reducers/\#example-graph "Permanent link")

### Define state [¶](https://langchain-ai.github.io/langgraph/how-tos/state-reducers/\#define-state "Permanent link")

[State](https://langchain-ai.github.io/langgraph/concepts/low_level/#state) in LangGraph can be a `TypedDict`, `Pydantic` model, or dataclass. Below we will use `TypedDict`. See [this guide](https://langchain-ai.github.io/langgraph/how-tos/state-model) for detail on using Pydantic.

By default, graphs will have the same input and output schema, and the state determines that schema. See [this guide](https://langchain-ai.github.io/langgraph/how-tos/input_output_schema/) for how to define distinct input and output schemas.

Let's consider a simple example:

API Reference: [AnyMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.AnyMessage.html)

```md-code__content
from langchain_core.messages import AnyMessage
from typing_extensions import TypedDict

class State(TypedDict):
    messages: list[AnyMessage]
    extra_field: int

```

This state tracks a list of [message](https://python.langchain.com/docs/concepts/messages/) objects, as well as an extra integer field.

### Define graph structure [¶](https://langchain-ai.github.io/langgraph/how-tos/state-reducers/\#define-graph-structure "Permanent link")

Let's build an example graph with a single node. Our [node](https://langchain-ai.github.io/langgraph/concepts/low_level/#nodes) is just a Python function that reads our graph's state and makes updates to it. The first argument to this function will always be the state:

API Reference: [AIMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html)

```md-code__content
from langchain_core.messages import AIMessage

def node(state: State):
    messages = state["messages"]
    new_message = AIMessage("Hello!")

    return {"messages": messages + [new_message], "extra_field": 10}

```

This node simply appends a message to our message list, and populates an extra field.

Important

Nodes should return updates to the state directly, instead of mutating the state.

Let's next define a simple graph containing this node. We use [StateGraph](https://langchain-ai.github.io/langgraph/concepts/low_level/#stategraph) to define a graph that operates on this state. We then use [add\_node](https://langchain-ai.github.io/langgraph/concepts/low_level/#messagesstate) populate our graph.

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph)

```md-code__content
from langgraph.graph import StateGraph

graph_builder = StateGraph(State)
graph_builder.add_node(node)
graph_builder.set_entry_point("node")
graph = graph_builder.compile()

```

LangGraph provides built-in utilities for visualizing your graph. Let's inspect our graph. See [this guide](https://langchain-ai.github.io/langgraph/how-tos/visualization) for detail on visualization.

```md-code__content
from IPython.display import Image, display

display(Image(graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

In this case, our graph just executes a single node.

### Use graph [¶](https://langchain-ai.github.io/langgraph/how-tos/state-reducers/\#use-graph "Permanent link")

Let's proceed with a simple invocation:

API Reference: [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html)

```md-code__content
from langchain_core.messages import HumanMessage

result = graph.invoke({"messages": [HumanMessage("Hi")]})
result

```

```md-code__content
{'messages': [HumanMessage(content='Hi', additional_kwargs={}, response_metadata={}),\
  AIMessage(content='Hello!', additional_kwargs={}, response_metadata={})],
 'extra_field': 10}

```

Note that:

- We kicked off invocation by updating a single key of the state.
- We receive the entire state in the invocation result.

For convenience, we frequently inspect the content of [message objects](https://python.langchain.com/docs/concepts/messages/) via pretty-print:

```md-code__content
for message in result["messages"]:
    message.pretty_print()

```

```md-code__content
================================[1m Human Message [0m=================================\
\
Hi\
==================================[1m Ai Message [0m==================================\
\
Hello!\
\
```\
\
## Process state updates with reducers [¶](https://langchain-ai.github.io/langgraph/how-tos/state-reducers/\#process-state-updates-with-reducers "Permanent link")\
\
Each key in the state can have its own independent [reducer](https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers) function, which controls how updates from nodes are applied. If no reducer function is explicitly specified then it is assumed that all updates to the key should override it.\
\
For `TypedDict` state schemas, we can define reducers by annotating the corresponding field of the state with a reducer function.\
\
In the earlier example, our node updated the `"messages"` key in the state by appending a message to it. Below, we add a reducer to this key, such that updates are automatically appended:\
\
```md-code__content\
from typing_extensions import Annotated\
\
def add(left, right):\
    """Can also import `add` from the `operator` built-in."""\
    return left + right\
\
class State(TypedDict):\
    messages: Annotated[list[AnyMessage], add]\
    extra_field: int\
\
```\
\
Now our node can be simplified:\
\
```md-code__content\
def node(state: State):\
    new_message = AIMessage("Hello!")\
    return {"messages": [new_message], "extra_field": 10}\
\
```\
\
API Reference: [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START)\
\
```md-code__content\
from langgraph.graph import START\
\
graph = StateGraph(State).add_node(node).add_edge(START, "node").compile()\
\
result = graph.invoke({"messages": [HumanMessage("Hi")]})\
\
for message in result["messages"]:\
    message.pretty_print()\
\
```\
\
```md-code__content\
================================[1m Human Message [0m=================================\
\
Hi\
==================================[1m Ai Message [0m==================================\
\
Hello!\
\
```\
\
### MessagesState [¶](https://langchain-ai.github.io/langgraph/how-tos/state-reducers/\#messagesstate "Permanent link")\
\
In practice, there are additional considerations for updating lists of messages:\
\
- We may wish to update an existing message in the state.\
- We may want to accept short-hands for [message formats](https://langchain-ai.github.io/langgraph/concepts/low_level/#using-messages-in-your-graph), such as [OpenAI format](https://python.langchain.com/docs/concepts/messages/#openai-format).\
\
LangGraph includes a built-in reducer `add_messages` that handles these considerations:\
\
API Reference: [add\_messages](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.message.add_messages)\
\
```md-code__content\
from langgraph.graph.message import add_messages\
\
class State(TypedDict):\
    messages: Annotated[list[AnyMessage], add_messages]\
    extra_field: int\
\
def node(state: State):\
    new_message = AIMessage("Hello!")\
    return {"messages": [new_message], "extra_field": 10}\
\
graph = StateGraph(State).add_node(node).set_entry_point("node").compile()\
\
```\
\
```md-code__content\
input_message = {"role": "user", "content": "Hi"}\
\
result = graph.invoke({"messages": [input_message]})\
\
for message in result["messages"]:\
    message.pretty_print()\
\
```\
\
```md-code__content\
================================[1m Human Message [0m=================================\
\
Hi\
==================================[1m Ai Message [0m==================================\
\
Hello!\
\
```\
\
This is a versatile representation of state for applications involving [chat models](https://python.langchain.com/docs/concepts/chat_models/). LangGraph includes a pre-built `MessagesState` for convenience, so that we can have:\
\
```md-code__content\
from langgraph.graph import MessagesState\
\
class State(MessagesState):\
    extra_field: int\
\
```\
\
## Next steps [¶](https://langchain-ai.github.io/langgraph/how-tos/state-reducers/\#next-steps "Permanent link")\
\
- Continue with the [Graph API Basics](https://langchain-ai.github.io/langgraph/how-tos/#graph-api-basics) guides.\
- See more detail on [state management](https://langchain-ai.github.io/langgraph/how-tos/#state-management).\
\
## Comments\
\
giscus\
\
#### [4 reactions](https://github.com/langchain-ai/langgraph/discussions/3466)\
\
👍4\
\
#### [1 comment](https://github.com/langchain-ai/langgraph/discussions/3466)\
\
_– powered by [giscus](https://giscus.app/)_\
\
- Oldest\
- Newest\
\
[![@Squidward1012](https://avatars.githubusercontent.com/u/95746383?v=4)Squidward1012](https://github.com/Squidward1012) [10 days ago](https://github.com/langchain-ai/langgraph/discussions/3466#discussioncomment-12832362)\
\
Can add a description to the state field? In this way, it is easy to get what each field does, and it is more conducive to collaborative development in engineering\
\
1\
\
0 replies\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fstate-reducers%2F)