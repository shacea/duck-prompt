[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/command/#how-to-combine-control-flow-and-state-updates-with-command)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/command.ipynb "Edit this page")

# How to combine control flow and state updates with Command [¶](https://langchain-ai.github.io/langgraph/how-tos/command/\#how-to-combine-control-flow-and-state-updates-with-command "Permanent link")

Prerequisites

This guide assumes familiarity with the following:

- [State](https://langchain-ai.github.io/langgraph/concepts/low_level#state)
- [Nodes](https://langchain-ai.github.io/langgraph/concepts/low_level#nodes)
- [Edges](https://langchain-ai.github.io/langgraph/concepts/low_level#edges)
- [Command](https://langchain-ai.github.io/langgraph/concepts/low_level#command)

It can be useful to combine control flow (edges) and state updates (nodes). For example, you might want to BOTH perform state updates AND decide which node to go to next in the SAME node. LangGraph provides a way to do so by returning a `Command` object from node functions:

```md-code__content
def my_node(state: State) -> Command[Literal["my_other_node"]]:
    return Command(
        # state update
        update={"foo": "bar"},
        # control flow
        goto="my_other_node"
    )

```

If you are using [subgraphs](https://langchain-ai.github.io/langgraph/how-tos/command/#subgraphs), you might want to navigate from a node within a subgraph to a different subgraph (i.e. a different node in the parent graph). To do so, you can specify `graph=Command.PARENT` in `Command`:

```md-code__content
def my_node(state: State) -> Command[Literal["my_other_node"]]:
    return Command(
        update={"foo": "bar"},
        goto="other_subgraph",  # where `other_subgraph` is a node in the parent graph
        graph=Command.PARENT
    )

```

State updates with `Command.PARENT`

When you send updates from a subgraph node to a parent graph node for a key that's shared by both parent and subgraph [state schemas](https://langchain-ai.github.io/langgraph/concepts/low_level#schema), you **must** define a [reducer](https://langchain-ai.github.io/langgraph/concepts/low_level#reducers) for the key you're updating in the parent graph state. See this [example](https://langchain-ai.github.io/langgraph/how-tos/command/#navigating-to-a-node-in-a-parent-graph) below.

This guide shows how you can do use `Command` to add dynamic control flow in your LangGraph app.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/command/\#setup "Permanent link")

First, let's install the required packages

```md-code__content
%%capture --no-stderr
%pip install -U langgraph

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


Let's create a simple graph with 3 nodes: A, B and C. We will first execute node A, and then decide whether to go to Node B or Node C next based on the output of node A.

## Basic usage [¶](https://langchain-ai.github.io/langgraph/how-tos/command/\#basic-usage "Permanent link")

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [Command](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Command)

```md-code__content
import random
from typing_extensions import TypedDict, Literal

from langgraph.graph import StateGraph, START
from langgraph.types import Command

# Define graph state
class State(TypedDict):
    foo: str

# Define the nodes

def node_a(state: State) -> Command[Literal["node_b", "node_c"]]:
    print("Called A")
    value = random.choice(["a", "b"])
    # this is a replacement for a conditional edge function
    if value == "a":
        goto = "node_b"
    else:
        goto = "node_c"

    # note how Command allows you to BOTH update the graph state AND route to the next node
    return Command(
        # this is the state update
        update={"foo": value},
        # this is a replacement for an edge
        goto=goto,
    )

def node_b(state: State):
    print("Called B")
    return {"foo": state["foo"] + "b"}

def node_c(state: State):
    print("Called C")
    return {"foo": state["foo"] + "c"}

```

We can now create the `StateGraph` with the above nodes. Notice that the graph doesn't have [conditional edges](https://langchain-ai.github.io/langgraph/concepts/low_level#conditional-edges) for routing! This is because control flow is defined with `Command` inside `node_a`.

```md-code__content
builder = StateGraph(State)
builder.add_edge(START, "node_a")
builder.add_node(node_a)
builder.add_node(node_b)
builder.add_node(node_c)
# NOTE: there are no edges between nodes A, B and C!

graph = builder.compile()

```

Important

You might have noticed that we used `Command` as a return type annotation, e.g. `Command[Literal["node_b", "node_c"]]`. This is necessary for the graph rendering and tells LangGraph that `node_a` can navigate to `node_b` and `node_c`.

```md-code__content
from IPython.display import display, Image

display(Image(graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

If we run the graph multiple times, we'd see it take different paths (A -> B or A -> C) based on the random choice in node A.

```md-code__content
graph.invoke({"foo": ""})

```

```md-code__content
Called A
Called C

```

```md-code__content
{'foo': 'bc'}

```

## Navigating to a node in a parent graph [¶](https://langchain-ai.github.io/langgraph/how-tos/command/\#navigating-to-a-node-in-a-parent-graph "Permanent link")

Now let's demonstrate how you can navigate from inside a subgraph to a different node in a parent graph. We'll do so by changing `node_a` in the above example into a single-node graph that we'll add as a subgraph to our parent graph.

State updates with `Command.PARENT`

When you send updates from a subgraph node to a parent graph node for a key that's shared by both parent and subgraph [state schemas](https://langchain-ai.github.io/langgraph/concepts/low_level#schema), you **must** define a [reducer](https://langchain-ai.github.io/langgraph/concepts/low_level#reducers) for the key you're updating in the parent graph state.

```md-code__content
import operator
from typing_extensions import Annotated

class State(TypedDict):
    # NOTE: we define a reducer here
    foo: Annotated[str, operator.add]

def node_a(state: State):
    print("Called A")
    value = random.choice(["a", "b"])
    # this is a replacement for a conditional edge function
    if value == "a":
        goto = "node_b"
    else:
        goto = "node_c"

    # note how Command allows you to BOTH update the graph state AND route to the next node
    return Command(
        update={"foo": value},
        goto=goto,
        # this tells LangGraph to navigate to node_b or node_c in the parent graph
        # NOTE: this will navigate to the closest parent graph relative to the subgraph
        graph=Command.PARENT,
    )

subgraph = StateGraph(State).add_node(node_a).add_edge(START, "node_a").compile()

def node_b(state: State):
    print("Called B")
    # NOTE: since we've defined a reducer, we don't need to manually append
    # new characters to existing 'foo' value. instead, reducer will append these
    # automatically (via operator.add)
    return {"foo": "b"}

def node_c(state: State):
    print("Called C")
    return {"foo": "c"}

```

```md-code__content
builder = StateGraph(State)
builder.add_edge(START, "subgraph")
builder.add_node("subgraph", subgraph)
builder.add_node(node_b)
builder.add_node(node_c)

graph = builder.compile()

```

```md-code__content
graph.invoke({"foo": ""})

```

```md-code__content
Called A
Called C

```

```md-code__content
{'foo': 'bc'}

```

Was this page helpful?






Thanks for your feedback!






Thanks for your feedback! Please help us improve this page by adding to the discussion below.


## Comments

[iframe](https://giscus.app/en/widget?origin=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fcommand%2F&session=&theme=preferred_color_scheme&reactionsEnabled=1&emitMetadata=0&inputPosition=bottom&repo=langchain-ai%2Flanggraph&repoId=R_kgDOKFU0lQ&category=Discussions&categoryId=DIC_kwDOKFU0lc4CfZgA&strict=0&description=Build+reliable%2C+stateful+AI+systems%2C+without+giving+up+control&backLink=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fcommand%2F&term=langgraph%2Fhow-tos%2Fcommand%2F)

Back to top