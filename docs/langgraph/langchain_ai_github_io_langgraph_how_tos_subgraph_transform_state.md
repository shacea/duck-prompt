[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/subgraph-transform-state/#how-to-transform-inputs-and-outputs-of-a-subgraph)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/subgraph-transform-state.ipynb "Edit this page")

# How to transform inputs and outputs of a subgraph [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraph-transform-state/\#how-to-transform-inputs-and-outputs-of-a-subgraph "Permanent link")

It's possible that your subgraph state is completely independent from the parent graph state, i.e. there are no overlapping channels (keys) between the two. For example, you might have a supervisor agent that needs to produce a report with a help of multiple ReAct agents. ReAct agent subgraphs might keep track of a list of messages whereas the supervisor only needs user input and final report in its state, and doesn't need to keep track of messages.

In such cases you need to transform the inputs to the subgraph before calling it and then transform its outputs before returning. This guide shows how to do that.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraph-transform-state/\#setup "Permanent link")

First, let's install the required packages

```md-code__content
%%capture --no-stderr
%pip install -U langgraph

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Define graph and subgraphs [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraph-transform-state/\#define-graph-and-subgraphs "Permanent link")

Let's define 3 graphs:
\- a parent graph
\- a child subgraph that will be called by the parent graph
\- a grandchild subgraph that will be called by the child graph

### Define grandchild [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraph-transform-state/\#define-grandchild "Permanent link")

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph)

```md-code__content
from typing_extensions import TypedDict
from langgraph.graph.state import StateGraph, START, END

class GrandChildState(TypedDict):
    my_grandchild_key: str

def grandchild_1(state: GrandChildState) -> GrandChildState:
    # NOTE: child or parent keys will not be accessible here
    return {"my_grandchild_key": state["my_grandchild_key"] + ", how are you"}

grandchild = StateGraph(GrandChildState)
grandchild.add_node("grandchild_1", grandchild_1)

grandchild.add_edge(START, "grandchild_1")
grandchild.add_edge("grandchild_1", END)

grandchild_graph = grandchild.compile()

```

```md-code__content
grandchild_graph.invoke({"my_grandchild_key": "hi Bob"})

```

```md-code__content
{'my_grandchild_key': 'hi Bob, how are you'}

```

### Define child [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraph-transform-state/\#define-child "Permanent link")

```md-code__content
class ChildState(TypedDict):
    my_child_key: str

def call_grandchild_graph(state: ChildState) -> ChildState:
    # NOTE: parent or grandchild keys won't be accessible here
    # we're transforming the state from the child state channels (`my_child_key`)
    # to the child state channels (`my_grandchild_key`)
    grandchild_graph_input = {"my_grandchild_key": state["my_child_key"]}
    # we're transforming the state from the grandchild state channels (`my_grandchild_key`)
    # back to the child state channels (`my_child_key`)
    grandchild_graph_output = grandchild_graph.invoke(grandchild_graph_input)
    return {"my_child_key": grandchild_graph_output["my_grandchild_key"] + " today?"}

child = StateGraph(ChildState)
# NOTE: we're passing a function here instead of just compiled graph (`child_graph`)
child.add_node("child_1", call_grandchild_graph)
child.add_edge(START, "child_1")
child.add_edge("child_1", END)
child_graph = child.compile()

```

```md-code__content
child_graph.invoke({"my_child_key": "hi Bob"})

```

```md-code__content
{'my_child_key': 'hi Bob, how are you today?'}

```

Note

We're wrapping the `grandchild_graph` invocation in a separate function ( `call_grandchild_graph`) that transforms the input state before calling the grandchild graph and then transforms the output of grandchild graph back to child graph state. If you just pass `grandchild_graph` directly to `.add_node` without the transformations, LangGraph will raise an error as there are no shared state channels (keys) between child and grandchild states.


Note that child and grandchild subgraphs have their own, **independent** state that is not shared with the parent graph.

### Define parent [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraph-transform-state/\#define-parent "Permanent link")

```md-code__content
class ParentState(TypedDict):
    my_key: str

def parent_1(state: ParentState) -> ParentState:
    # NOTE: child or grandchild keys won't be accessible here
    return {"my_key": "hi " + state["my_key"]}

def parent_2(state: ParentState) -> ParentState:
    return {"my_key": state["my_key"] + " bye!"}

def call_child_graph(state: ParentState) -> ParentState:
    # we're transforming the state from the parent state channels (`my_key`)
    # to the child state channels (`my_child_key`)
    child_graph_input = {"my_child_key": state["my_key"]}
    # we're transforming the state from the child state channels (`my_child_key`)
    # back to the parent state channels (`my_key`)
    child_graph_output = child_graph.invoke(child_graph_input)
    return {"my_key": child_graph_output["my_child_key"]}

parent = StateGraph(ParentState)
parent.add_node("parent_1", parent_1)
# NOTE: we're passing a function here instead of just a compiled graph (`<code>child_graph</code>`)
parent.add_node("child", call_child_graph)
parent.add_node("parent_2", parent_2)

parent.add_edge(START, "parent_1")
parent.add_edge("parent_1", "child")
parent.add_edge("child", "parent_2")
parent.add_edge("parent_2", END)

parent_graph = parent.compile()

```

Note

We're wrapping the `child_graph` invocation in a separate function ( `call_child_graph`) that transforms the input state before calling the child graph and then transforms the output of the child graph back to parent graph state. If you just pass `child_graph` directly to `.add_node` without the transformations, LangGraph will raise an error as there are no shared state channels (keys) between parent and child states.


Let's run the parent graph and make sure it correctly calls both the child and grandchild subgraphs:

```md-code__content
parent_graph.invoke({"my_key": "Bob"})

```

```md-code__content
{'my_key': 'hi Bob, how are you today? bye!'}

```

Perfect! The parent graph correctly calls both the child and grandchild subgraphs (which we know since the ", how are you" and "today?" are added to our original "my\_key" state value).

## Comments

giscus

#### [3 reactions](https://github.com/langchain-ai/langgraph/discussions/1684)

👍3

#### [2 comments](https://github.com/langchain-ai/langgraph/discussions/1684)

#### ·

#### 13 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@ezshen](https://avatars.githubusercontent.com/u/23181661?u=cde2275f4649d2d924e48eaab066ac6a06f3213e&v=4)ezshen](https://github.com/ezshen) [Sep 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-10618438)

edited

Hi, I can't seem to get the graph drawing functionality to correctly display the subgraph nodes for this example specifically.

If I run the code above and add the line `print(parent_graph.get_graph(xray=2).draw_ascii())`, I get the below output, which does not correctly display the nodes `child_1` or `grandchild_1`:

```notranslate
+-----------+
| __start__ |
+-----------+
      *
      *
      *
+----------+
| parent_1 |
+----------+
      *
      *
      *
  +-------+
  | child |
  +-------+
      *
      *
      *
+----------+
| parent_2 |
+----------+
      *
      *
      *
 +---------+
 | __end__ |
 +---------+

```

Any ideas? Thanks.

1

6 replies

Show 1 previous reply

[![@ezshen](https://avatars.githubusercontent.com/u/23181661?u=cde2275f4649d2d924e48eaab066ac6a06f3213e&v=4)](https://github.com/ezshen)

[ezshen](https://github.com/ezshen) [Sep 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-10618567)

edited

[@vbarda](https://github.com/vbarda) Thanks for getting back to me! I tried again and it still is not displaying the correct nodes for the subgraph. I may be totally off, but It doesn't look like the `CompiledGraph` is able to find any subgraphs...

```notranslate
print("SUBGRAPHS", dict(parent_graph.get_subgraphs()))
print("MAIN GRAPH", parent_graph.get_graph())
display(Image(parent_graph.get_graph(xray=2).draw_mermaid_png()))

```

Here is the output I get:

[![image](https://private-user-images.githubusercontent.com/23181661/366607714-63ad6585-284c-4c41-b1e3-6785f11bf4aa.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDU1MzM4NDYsIm5iZiI6MTc0NTUzMzU0NiwicGF0aCI6Ii8yMzE4MTY2MS8zNjY2MDc3MTQtNjNhZDY1ODUtMjg0Yy00YzQxLWIxZTMtNjc4NWYxMWJmNGFhLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA0MjQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNDI0VDIyMjU0NlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTQyMjM1OGFjZjIyZTU3NjY5ZjliNDhjMzkwZWViYjRmMzIzNzQ4ZTlhOTAyMDkzNjA4YjFkYzZlMzE0YTAzZWQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.axPus9NypP4boPhDYjSm97e4Xkc8mUaigc3oQKIWOwk)](https://private-user-images.githubusercontent.com/23181661/366607714-63ad6585-284c-4c41-b1e3-6785f11bf4aa.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NDU1MzM4NDYsIm5iZiI6MTc0NTUzMzU0NiwicGF0aCI6Ii8yMzE4MTY2MS8zNjY2MDc3MTQtNjNhZDY1ODUtMjg0Yy00YzQxLWIxZTMtNjc4NWYxMWJmNGFhLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA0MjQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNDI0VDIyMjU0NlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTQyMjM1OGFjZjIyZTU3NjY5ZjliNDhjMzkwZWViYjRmMzIzNzQ4ZTlhOTAyMDkzNjA4YjFkYzZlMzE0YTAzZWQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.axPus9NypP4boPhDYjSm97e4Xkc8mUaigc3oQKIWOwk)

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Sep 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-10619402)

Collaborator

ah, this is because in this example subgraphs are called inside the functions, so you won't be able to actually render them from the parent graph at the moment. we're not inspecting the function signatures to see if graphs are called when calling `app.get_graph()`

if you didn't have different schemas, you could pass the compiled graph to `add_node`

```
parent_graph.add_node("child", child_graph)
```

instead of

```notranslate
parent.add_node("child", call_child_graph)

```

and this would render correctly. hope this helps!

❤️1

[![@ezshen](https://avatars.githubusercontent.com/u/23181661?u=cde2275f4649d2d924e48eaab066ac6a06f3213e&v=4)](https://github.com/ezshen)

[ezshen](https://github.com/ezshen) [Sep 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-10619757)

Got it. Unfortunately, my parent and child graphs have different schemas, but I'll find a workaround! Thanks!

[![@LeonMusCoden](https://avatars.githubusercontent.com/u/53626026?v=4)](https://github.com/LeonMusCoden)

[LeonMusCoden](https://github.com/LeonMusCoden) [Feb 10](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-12120996)

Hi Ezshen,

Sorry for the late reply. I'm currently facing the exact same issue. Did you find a workaround?

[![@david101-hunter](https://avatars.githubusercontent.com/u/156736296?u=a733d3a1912f21d6300c34761c577ecf305107f7&v=4)](https://github.com/david101-hunter)

[david101-hunter](https://github.com/david101-hunter) [8 days ago](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-12849639)

when I use draw\_mermaid\_png(), I encoutered HTTPSConnectionPool(host='mermaid.ink', port=443): Read timed out. (read timeout=10). How can I fix that?

[![@marcammann](https://avatars.githubusercontent.com/u/49620?u=f326e14ae90e6977924bc93d58ab83471fcffccf&v=4)marcammann](https://github.com/marcammann) [Sep 18, 2024](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-10686474)

Similar to the issue with the diagram, something seems to break when using a function to invoke another graph. Can't access the state of subgraphs for some reason. Is there a way to call the subgraph from a function in a way that preserves that?

1

7 replies

Show 2 previous replies

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Nov 14, 2024](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-11261022)

Collaborator

Hi folks! We recently launched full support for subgraphs -- would love if you tried it out and let us know if you're still running into any issues!

[![@yunhzou](https://avatars.githubusercontent.com/u/59716776?u=93b776e7590f859cceba6b34d3aa937438cfe6c8&v=4)](https://github.com/yunhzou)

[yunhzou](https://github.com/yunhzou) [Dec 10, 2024](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-11525483)

Hi vbarda, the visualization is still not working when subgraph is invoke/wrapped by a function that is assigned to the node.

👍2

[![@tugbayatilla](https://avatars.githubusercontent.com/u/16705175?u=0d912a4d3a7ba0d452f7566cdc9e1613e9add0a3&v=4)](https://github.com/tugbayatilla)

[tugbayatilla](https://github.com/tugbayatilla) [Jan 28](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-11982057)

the issue is still there. (langgraph==0.2.62) Any progress?

[![@ioo0s](https://avatars.githubusercontent.com/u/82093214?u=8a658e1c075cc2c323e48a0356aa9bd96fa8cf2d&v=4)](https://github.com/ioo0s)

[ioo0s](https://github.com/ioo0s) [Mar 5](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-12397242)

`langgraph==0.2.70` have same issue, any solution now?

[![@XiaoLiuAI](https://avatars.githubusercontent.com/u/1553482?v=4)](https://github.com/XiaoLiuAI)

[XiaoLiuAI](https://github.com/XiaoLiuAI) [16 days ago](https://github.com/langchain-ai/langgraph/discussions/1684#discussioncomment-12761641)

langgraph==0.3.21 have same issue, any progress?

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fsubgraph-transform-state%2F)