[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/branching/#how-to-create-branches-for-parallel-node-execution)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/branching.ipynb "Edit this page")

# How to create branches for parallel node execution [¶](https://langchain-ai.github.io/langgraph/how-tos/branching/\#how-to-create-branches-for-parallel-node-execution "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [Node](https://langchain-ai.github.io/langgraph/concepts/low_level/#nodes)
- [Edge](https://langchain-ai.github.io/langgraph/concepts/low_level/#edges)
- [Reducer](https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers)

Parallel execution of nodes is essential to speed up overall graph operation. LangGraph offers native support for parallel execution of nodes, which can significantly enhance the performance of graph-based workflows. This parallelization is achieved through fan-out and fan-in mechanisms, utilizing both standard edges and [conditional\_edges](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.MessageGraph.add_conditional_edges). Below are some examples showing how to add create branching dataflows that work for you.

![Screenshot 2024-07-09 at 2.55.56 PM.png](<Base64-Image-Removed>)

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/branching/\#setup "Permanent link")

First, let's install the required packages

```md-code__content
%%capture --no-stderr
%pip install -U langgraph

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## How to run graph nodes in parallel [¶](https://langchain-ai.github.io/langgraph/how-tos/branching/\#how-to-run-graph-nodes-in-parallel "Permanent link")

In this example, we fan out from `Node A` to `B and C` and then fan in to `D`. With our state, [we specify the reducer add operation](https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers). This will combine or accumulate values for the specific key in the State, rather than simply overwriting the existing value. For lists, this means concatenating the new list with the existing list. See [this guide](https://langchain-ai.github.io/langgraph/how-tos/state-reducers) for more detail on updating state with reducers.

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END)

```md-code__content
import operator
from typing import Annotated, Any

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    # The operator.add reducer fn makes this append-only
    aggregate: Annotated[list, operator.add]

def a(state: State):
    print(f'Adding "A" to {state["aggregate"]}')
    return {"aggregate": ["A"]}

def b(state: State):
    print(f'Adding "B" to {state["aggregate"]}')
    return {"aggregate": ["B"]}

def c(state: State):
    print(f'Adding "C" to {state["aggregate"]}')
    return {"aggregate": ["C"]}

def d(state: State):
    print(f'Adding "D" to {state["aggregate"]}')
    return {"aggregate": ["D"]}

builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)
builder.add_node(c)
builder.add_node(d)
builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("a", "c")
builder.add_edge("b", "d")
builder.add_edge("c", "d")
builder.add_edge("d", END)
graph = builder.compile()

```

```md-code__content
from IPython.display import Image, display

display(Image(graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

With the reducer, you can see that the values added in each node are accumulated.

```md-code__content
graph.invoke({"aggregate": []}, {"configurable": {"thread_id": "foo"}})

```

```md-code__content
Adding "A" to []
Adding "B" to ['A']
Adding "C" to ['A']
Adding "D" to ['A', 'B', 'C']

```

```md-code__content
{'aggregate': ['A', 'B', 'C', 'D']}

```

Note

In the above example, nodes `"b"` and `"c"` are executed concurrently in the same [superstep](https://langchain-ai.github.io/langgraph/concepts/low_level/#graphs). Because they are in the same step, node `"d"` executes after both `"b"` and `"c"` are finished.

Importantly, updates from a parallel superstep may not be ordered consistently. If you need a consistent, predetermined ordering of updates from a parallel superstep, you should write the outputs to a separate field in the state together with a value with which to order them.

Exception handling?

LangGraph executes nodes within ["supersteps"](https://langchain-ai.github.io/langgraph/concepts/low_level/#graphs), meaning that while parallel branches are executed in parallel, the entire superstep is **transactional**. If any of these branches raises an exception, **none** of the updates are applied to the state (the entire superstep errors).

Importantly, when using a [checkpointer](https://langchain-ai.github.io/langgraph/concepts/persistence/), results from successful nodes within a superstep are saved, and don't repeat when resumed.

If you have error-prone (perhaps want to handle flakey API calls), LangGraph provides two ways to address this:

1. You can write regular python code within your node to catch and handle exceptions.
2. You can set a **[retry\_policy](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.graph.CompiledGraph.retry_policy)** to direct the graph to retry nodes that raise certain types of exceptions. Only failing branches are retried, so you needn't worry about performing redundant work.

Together, these let you perform parallel execution and fully control exception handling.

## Parallel node fan-out and fan-in with extra steps [¶](https://langchain-ai.github.io/langgraph/how-tos/branching/\#parallel-node-fan-out-and-fan-in-with-extra-steps "Permanent link")

The above example showed how to fan-out and fan-in when each path was only one step. But what if one path had more than one step? Let's add a node `b_2` in the "b" branch:

```md-code__content
def b_2(state: State):
    print(f'Adding "B_2" to {state["aggregate"]}')
    return {"aggregate": ["B_2"]}

builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)
builder.add_node(b_2)
builder.add_node(c)
builder.add_node(d)
builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("a", "c")
builder.add_edge("b", "b_2")
builder.add_edge(["b_2", "c"], "d")
builder.add_edge("d", END)
graph = builder.compile()

```

```md-code__content
from IPython.display import Image, display

display(Image(graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

```md-code__content
graph.invoke({"aggregate": []})

```

```md-code__content
Adding "A" to []
Adding "B" to ['A']
Adding "C" to ['A']
Adding "B_2" to ['A', 'B', 'C']
Adding "D" to ['A', 'B', 'C', 'B_2']

```

```md-code__content
{'aggregate': ['A', 'B', 'C', 'B_2', 'D']}

```

Note

In the above example, nodes `"b"` and `"c"` are executed concurrently in the same [superstep](https://langchain-ai.github.io/langgraph/concepts/low_level/#graphs). What happens in the next step?

We use `add_edge(["b_2", "c"], "d")` here to force node `"d"` to only run when both nodes `"b_2"` and `"c"` have finished execution. If we added two separate edges,
node `"d"` would run twice: after node `b2` finishes and once again after node `c` (in whichever order those nodes finish).

## Conditional Branching [¶](https://langchain-ai.github.io/langgraph/how-tos/branching/\#conditional-branching "Permanent link")

If your fan-out is not deterministic, you can use [add\_conditional\_edges](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.StateGraph.add_conditional_edges) directly.

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END)

```md-code__content
import operator
from typing import Annotated, Sequence

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    aggregate: Annotated[list, operator.add]
    # Add a key to the state. We will set this key to determine
    # how we branch.
    which: str

def a(state: State):
    print(f'Adding "A" to {state["aggregate"]}')
    return {"aggregate": ["A"]}

def b(state: State):
    print(f'Adding "B" to {state["aggregate"]}')
    return {"aggregate": ["B"]}

def c(state: State):
    print(f'Adding "C" to {state["aggregate"]}')
    return {"aggregate": ["C"]}

def d(state: State):
    print(f'Adding "D" to {state["aggregate"]}')
    return {"aggregate": ["D"]}

def e(state: State):
    print(f'Adding "E" to {state["aggregate"]}')
    return {"aggregate": ["E"]}

builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)
builder.add_node(c)
builder.add_node(d)
builder.add_node(e)
builder.add_edge(START, "a")

def route_bc_or_cd(state: State) -> Sequence[str]:
    if state["which"] == "cd":
        return ["c", "d"]
    return ["b", "c"]

intermediates = ["b", "c", "d"]
builder.add_conditional_edges(
    "a",
    route_bc_or_cd,
    intermediates,
)
for node in intermediates:
    builder.add_edge(node, "e")

builder.add_edge("e", END)
graph = builder.compile()

```

```md-code__content
from IPython.display import Image, display

display(Image(graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

```md-code__content
graph.invoke({"aggregate": [], "which": "bc"})

```

```md-code__content
Adding "A" to []
Adding "B" to ['A']
Adding "C" to ['A']
Adding "E" to ['A', 'B', 'C']

```

```md-code__content
{'aggregate': ['A', 'B', 'C', 'E'], 'which': 'bc'}

```

```md-code__content
graph.invoke({"aggregate": [], "which": "cd"})

```

```md-code__content
Adding "A" to []
Adding "C" to ['A']
Adding "D" to ['A']
Adding "E" to ['A', 'C', 'D']

```

```md-code__content
{'aggregate': ['A', 'C', 'D', 'E'], 'which': 'cd'}

```

## Next steps [¶](https://langchain-ai.github.io/langgraph/how-tos/branching/\#next-steps "Permanent link")

- Continue with the [Graph API Basics](https://langchain-ai.github.io/langgraph/how-tos/#graph-api-basics) guides.
- Learn how to create [map-reduce](https://langchain-ai.github.io/langgraph/how-tos/map-reduce/) branches in which different states can be distributed to multiple instances of a node.

## Comments

giscus

#### [11 reactions](https://github.com/langchain-ai/langgraph/discussions/540)

👍11

#### [15 comments](https://github.com/langchain-ai/langgraph/discussions/540)

#### ·

#### 16 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@HUNZALAMUSHTAQ](https://avatars.githubusercontent.com/u/75185145?u=3dab89b989644ec0647946de0c701394b9933035&v=4)HUNZALAMUSHTAQ](https://github.com/HUNZALAMUSHTAQ) [Jun 27, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-9897627)

Hi i am implementing this parallel tool calling but it raises exception

openai.BadRequestError: Error code: 400 - {'error': {'message': "An assistant message with 'tool\_calls' must be followed by tool messages responding to each 'tool\_call\_id'. The following tool\_call\_ids did not have response messages: call\_i1R8a78yTqv2IpDGUve2xPNZ", 'type': 'invalid\_request\_error', 'param': 'messages', 'code': None}}

mermaid syntax for diagram

graph TD;

_start\[start_\]:::startclass;

_end\[end_\]:::endclass;

primary\_assistant(\[primary\_assistant\]):::otherclass;

primary\_assistant\_tools(\[primary\_assistant\_tools\]):::otherclass;

enter\_order\_assistant(\[enter\_order\_assistant\]):::otherclass;

order\_assistant(\[order\_assistant\]):::otherclass;

order\_assistant\_tools(\[order\_assistant\_tools\]):::otherclass;

leave\_skill(\[leave\_skill\]):::otherclass;

enter\_supply\_assistant(\[enter\_supply\_assistant\]):::otherclass;

supply\_assistant(\[supply\_assistant\]):::otherclass;

supply\_tools(\[supply\_tools\]):::otherclass;

_start_ --\> primary\_assistant;

enter\_order\_assistant --> order\_assistant;

enter\_supply\_assistant --> supply\_assistant;

leave\_skill --> primary\_assistant;

order\_assistant\_tools --> order\_assistant;

primary\_assistant\_tools --> primary\_assistant;

supply\_tools --> supply\_assistant;

primary\_assistant -.-> enter\_order\_assistant;

primary\_assistant -.-> enter\_supply\_assistant;

primary\_assistant -.-> primary\_assistant\_tools;

primary\_assistant -.-> _end_;

order\_assistant -.-> order\_assistant\_tools;

order\_assistant -.-> leave\_skill;

order\_assistant -.-> _end_;

supply\_assistant -.-> leave\_skill;

supply\_assistant -.-> supply\_tools;

supply\_assistant -.-> _end_;

classDef startclass fill:#ffdfba;

classDef endclass fill:#baffc9;

classDef otherclass fill:#fad7de;

1

❤️1

3 replies

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Jun 27, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-9897925)

Contributor

[@HUNZALAMUSHTAQ](https://github.com/HUNZALAMUSHTAQ) , if you want to fan out then back in and then pass back to an LLM, you need to ensure the message history contains a properly ordered list of messages, including a tool message for each tool call the AI might have.

❤️1

[![@ibrahim77gh](https://avatars.githubusercontent.com/u/91305685?u=514e034870793995de202d2dfb4291c1718e1b29&v=4)](https://github.com/ibrahim77gh)

[ibrahim77gh](https://github.com/ibrahim77gh) [Jun 27, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-9898055)

Hi William , thanks for the reply we really appreciate it!

This is how we are maintaining the Message History, we followed the Customer Support Bot example.

We are getting the error on parallel tool call (when the same tool is called multiple times in parallel) by the agent

Can you please provide a little more guidance, We would highly appreciate it,

Thanks.

from typing import Callable, Annotated, Literal, Optional

from langgraph.graph.message import AnyMessage, add\_messages

from typing\_extensions import TypedDict

def update\_dialog\_stack(left: list\[str\], right: Optional\[str\]) -> list\[str\]:

"""Push or pop the state."""

if right is None:

return left

if right == "pop":

return left\[:-1\]

return left + \[right\]

class State(TypedDict):

messages: Annotated\[list\[AnyMessage\], add\_messages\]

user\_info: str

dialog\_state: Annotated\[\
\
list\[\
\
Literal\[\
\
"assistant",\
\
"order\_assistant",\
\
"supply\_assistant",\
\
\]\
\
\],\
\
update\_dialog\_stack,\
\
\]

This is how we are maintaining the

[![@ibrahim77gh](https://avatars.githubusercontent.com/u/91305685?u=514e034870793995de202d2dfb4291c1718e1b29&v=4)](https://github.com/ibrahim77gh)

[ibrahim77gh](https://github.com/ibrahim77gh) [Jun 27, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-9898782)

[@hinthornw](https://github.com/hinthornw)

[![@gengyabc](https://avatars.githubusercontent.com/u/12781437?v=4)gengyabc](https://github.com/gengyabc) [Jul 6, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-9972269)

Thanks for these wonderful guildes. I got a quesiton on the state update.

In the last guides on Create subgraphs, the states got some duplicates, but here there is no duplicates after fan-in even though the reduce function is just "add".

So what is happening under the hood?

1

0 replies

[![@LordO54](https://avatars.githubusercontent.com/u/119976077?v=4)LordO54](https://github.com/LordO54) [Jul 12, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-10027298)

When it comes to executing langchain chains, is it possible to execute parallel calling with these graph structure?

1

0 replies

[![@LordO54](https://avatars.githubusercontent.com/u/119976077?v=4)LordO54](https://github.com/LordO54) [Jul 14, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-10045412)

I have been trying to execute this kind of structure via streaming\_events but it does not work. the answer is always waited to be finished, before showing it:

try:

inputs = {"question": data.message, "sessionid": session\_id, "user\_data":user\_data}

response\_data = \[\]

async for event in langgraph\_app.astream\_events(inputs, version="v2"):

print("empezando")

kind= event\["event"\]

tags = event.get("tags", \[\])

if "langgraph\_node" in event\["metadata"\]:

if event\["metadata"\]\["langgraph\_node"\]=="generateCommon":

if "input" in event\["data"\] and "generation" in event\["data"\]\["input"\]:

data = event\["data"\]\["input"\]\["generation"\]\[0\].content

print(data)

if data:

response\_data.append(data)

await manager.send\_personal\_message("".join(response\_data), websocket)

1

0 replies

[![@zetyquickly](https://avatars.githubusercontent.com/u/25350960?u=cc19a11eec2a58aebe10ded22dbd680c8eeb6879&v=4)zetyquickly](https://github.com/zetyquickly) [Jul 22, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-10118063)

May I ask regarding the "Parallel node fan-out and fan-in with extra steps", what is the point of having parallel paths if both branches share the same state? I mean if "C" sees not only "A", but also the change made in "B". I mean in here:

```notranslate
Adding I'm A to []
Adding I'm B to ["I'm A"]
Adding I'm C to ["I'm A"]
Adding I'm B2 to ["I'm A", "I'm B", "I'm C"]
...

```

1

👍1

8 replies

Show 3 previous replies

[![@jacopo-chevallard](https://avatars.githubusercontent.com/u/8123595?u=828d4872797e5d1bbda3e8f0a4700171f3a302ff&v=4)](https://github.com/jacopo-chevallard)

[jacopo-chevallard](https://github.com/jacopo-chevallard) [Sep 26, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-10761178)

[@rlancemartin](https://github.com/rlancemartin) I tried to modify the map-reduce example to introduce a further step (refine\_jokes) along the branch before the reduce operation. The goal would be to be able to branch out (using Send) and have several steps in each branch (executed in parallel) before the reduce operation. I guess that this can be achieved using sub-graphs, but perhaps there is a simpler solution?

The error I'm getting is

```notranslate
    raise InvalidUpdateError(
langgraph.errors.InvalidUpdateError: At key 'joke': Can receive only one value per step. Use an Annotated key to handle multiple values.

```

Here my code

```
import operator
from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic

from langgraph.types import Send
from langgraph.graph import END, StateGraph, START

from pydantic import BaseModel, Field

# Model and prompts
# Define model and prompts we will use
subjects_prompt = """Generate a comma separated list of between 2 and 5 examples related to: {topic}."""
joke_prompt = """Generate a joke about {subject}"""
best_joke_prompt = """Below are a bunch of jokes about {topic}. Select the best one! Return the ID of the best one.

{jokes}"""

refine_joke_prompt = """Refine the following joke to make it even funnier: {joke}."""

class Subjects(BaseModel):
    subjects: list[str]

class Joke(BaseModel):
    joke: str

class BestJoke(BaseModel):
    id: int = Field(description="Index of the best joke, starting with 0", ge=0)

model = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# Graph components: define the components that will make up the graph

# This will be the overall state of the main graph.
# It will contain a topic (which we expect the user to provide)
# and then will generate a list of subjects, and then a joke for
# each subject
class OverallState(TypedDict):
    topic: str
    subjects: list
    # Notice here we use the operator.add
    # This is because we want combine all the jokes we generate
    # from individual nodes back into one list - this is essentially
    # the "reduce" part
    jokes: Annotated[list, operator.add]
    best_selected_joke: str

# This will be the state of the node that we will "map" all
# subjects to in order to generate a joke
class JokeState(TypedDict):
    subject: str
    joke: str

# This is the function we will use to generate the subjects of the jokes
def generate_topics(state: OverallState) -> OverallState:
    prompt = subjects_prompt.format(topic=state["topic"])
    response = model.with_structured_output(Subjects).invoke(prompt)
    return {"subjects": response.subjects}

# Here we generate a joke, given a subject
def generate_joke(state: JokeState) -> JokeState:
    prompt = joke_prompt.format(subject=state["subject"])
    response = model.with_structured_output(Joke).invoke(prompt)
    return {"joke": [response.joke]}

def refine_joke(state: JokeState) -> OverallState:
    prompt = refine_joke_prompt.format(joke=state["joke"])
    response = model.with_structured_output(Joke).invoke(prompt)
    return {"jokes": [response.joke]}

# Here we define the logic to map out over the generated subjects
# We will use this an edge in the graph
def continue_to_jokes(state: OverallState):
    # We will return a list of `Send` objects
    # Each `Send` object consists of the name of a node in the graph
    # as well as the state to send to that node
    return [Send("generate_joke", {"subject": s}) for s in state["subjects"]]

# Here we will judge the best joke
def best_joke(state: OverallState) -> OverallState:
    jokes = "\n\n".join(state["jokes"])
    prompt = best_joke_prompt.format(topic=state["topic"], jokes=jokes)
    response = model.with_structured_output(BestJoke).invoke(prompt)
    return {"best_selected_joke": state["jokes"][response.id]}

def compile_graph():
    # Construct the graph: here we put everything together to construct our graph
    graph = StateGraph(OverallState)
    graph.add_node("generate_topics", generate_topics)
    graph.add_node("generate_joke", generate_joke)
    graph.add_node("refine_joke", refine_joke)
    graph.add_node("best_joke", best_joke)
    graph.add_edge(START, "generate_topics")
    graph.add_conditional_edges("generate_topics", continue_to_jokes, ["generate_joke"])
    graph.add_edge("generate_joke", "refine_joke")
    graph.add_edge("refine_joke", "best_joke")
    graph.add_edge("best_joke", END)
    app = graph.compile()
    return app

if __name__ == "__main__":
    app = compile_graph()
        # Call the graph: here we call it to generate a list of jokes
    for s in app.stream({"topic": "animals"}):
        print(s)
```

[![@TomTom101](https://avatars.githubusercontent.com/u/872712?u=c6e76fb451e3a0c1528a8d0e95ef3ed669483690&v=4)](https://github.com/TomTom101)

[TomTom101](https://github.com/TomTom101) [Nov 22, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-11349792)

Have you been able to solve this? I'm still struggling with exactly the same problem. Thanks!

[![@EliezerIsrael](https://avatars.githubusercontent.com/u/226930?v=4)](https://github.com/EliezerIsrael)

[EliezerIsrael](https://github.com/EliezerIsrael) [Dec 18, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-11602158)

Also looking at the same issue. It's clear that "refine\_joke" is acting as the sink - there's nothing in the graph structure to distinguish it from "best\_joke" - but it's not clear how to keep the second step in each mapped branch isolated.

[![@EliezerIsrael](https://avatars.githubusercontent.com/u/226930?v=4)](https://github.com/EliezerIsrael)

[EliezerIsrael](https://github.com/EliezerIsrael) [Dec 18, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-11602508)

If I understand correctly, the `add_edge` method adds an edge to a single node identified by its name. In your case, you want a different node on each branch. I believe that you can use the `Send` method again, at the second step, to create that node dynamically. In other words, the pattern currently used in `continue_to_jokes` will work for the edge between `generate_joke` and `refine_joke`.

Remove the explicit edge

`graph.add_edge("generate_joke", "refine_joke")`

and replace it with

`graph.add_conditional_edges("generate_joke", continue_to_refine, ["refine_joke"])`

Add a function:

```notranslate
def continue_to_refine(state: JokeState):
    return Send("refine_joke", state)

```

[![@EliezerIsrael](https://avatars.githubusercontent.com/u/226930?v=4)](https://github.com/EliezerIsrael)

[EliezerIsrael](https://github.com/EliezerIsrael) [Dec 18, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-11602514)

In my case, I want each mapped branch to use tools with something like a ReAct architecture. I haven't cracked that one yet.

[![@tianyi-fca](https://avatars.githubusercontent.com/u/176463495?u=1d44b033eebcc188c2cc3ce86e5d7723c44d37ee&v=4)tianyi-fca](https://github.com/tianyi-fca) [Aug 14, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-10331579)

I found an interesting unexpected behaviour:

In the basic fan-out and fan-in case, the method 1 and method 2 shown below do exactly the same thing.

```notranslate
// add nodes to the graph
workflow
  .addNode("A", nodeA)
  .addNode("B", nodeB)
  .addNode("C", nodeC)
  .addNode("D", nodeD)
  // add edges to the graph

  // *** fan out from Node A to B and C and then fan in to D ***
  .addEdge(START, "A")
  .addEdge("A", "B")
  .addEdge("A", "C")

  // >>> method 1 <<<
  .addEdge("B", "D")
  .addEdge("C", "D")

  // >>> method 2 <<<
  // .addEdge(["B", "C"], "D")

  .addEdge("D", END);

```

Output from method 1 and method 2 are identical

```notranslate
Adding A to
Adding B to A
Adding C to A
Adding D to A,B,C
{ aggregate: [ 'A', 'B', 'C', 'D' ] }

```

However, in the fan-out and fan-in with extra steps, method 1 and method 2 (below) give different output

```notranslate
workflow
  .addNode("a", nodeA.call.bind(nodeA))
  .addNode("b", nodeB.call.bind(nodeB))
  .addNode("b2", nodeB2.call.bind(nodeB2))
  .addNode("c", nodeC.call.bind(nodeC))
  .addNode("d", nodeD.call.bind(nodeD))
  .addEdge(START, "a")
  .addEdge("a", "b")
  .addEdge("b", "b2")
  .addEdge("a", "c")

  // >>> method 1 (right way) <<<
  .addEdge(["b2", "c"], "d")

  // method 2 (wrong way) - The following will add one extra `I'm D` to the aggregate
  // .addEdge("b2", "d")
  // .addEdge("c", "d")

  .addEdge("d", END);

```

The output:

```notranslate
// from method 1
Adding I'm A to
Adding I'm B to I'm A
Adding I'm C to I'm A
Adding I'm B2 to I'm A,I'm B,I'm C
Adding I'm D to I'm A,I'm B,I'm C,I'm B2
{ aggregate: [ "I'm A", "I'm B", "I'm C", "I'm B2", "I'm D" ] }

```

```notranslate
// From method 2
Adding I'm A to
Adding I'm B to I'm A
Adding I'm C to I'm A
Adding I'm B2 to I'm A,I'm B,I'm C
Adding I'm D to I'm A,I'm B,I'm C
Adding I'm D to I'm A,I'm B,I'm C,I'm B2,I'm D
{
  aggregate: [ "I'm A", "I'm B", "I'm C", "I'm B2", "I'm D", "I'm D" ]
}

```

1

👍2

1 reply

[![@lean-zone](https://avatars.githubusercontent.com/u/52621749?u=c751fa13fed12fb10eb243cc384ffb4ad00729b3&v=4)](https://github.com/lean-zone)

[lean-zone](https://github.com/lean-zone) [29 days ago](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-12622796)

The current version 0.3.20 also has this problem，when will it be fixed?

[![@freshchen](https://avatars.githubusercontent.com/u/37622341?u=6c9240858ca8eca1d693f81c2474f8671cf84aa4&v=4)freshchen](https://github.com/freshchen) [Aug 21, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-10402432)

In Parallel node fan-out and fan-in with extra steps。

It seems that b2 needs to be executed after c is completed

I expect the execution of b and b2 to be independent of c. Should I use subgraph?

2

👍1

2 replies

[![@Huarong](https://avatars.githubusercontent.com/u/1487879?v=4)](https://github.com/Huarong)

[Huarong](https://github.com/Huarong) [Aug 22, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-10417723)

I used subgraph and got real parallel successfully.

👀1

[![@freshchen](https://avatars.githubusercontent.com/u/37622341?u=6c9240858ca8eca1d693f81c2474f8671cf84aa4&v=4)](https://github.com/freshchen)

[freshchen](https://github.com/freshchen) [Aug 22, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-10417778)

Thanks. it seems that multi steps parallel only subgraph can be used.

I feel a little uncomfortable splitting the graph for technical reasons rather than business reasons

👍1

[![@ibrahim-omer-621](https://avatars.githubusercontent.com/u/121984167?v=4)ibrahim-omer-621](https://github.com/ibrahim-omer-621) [Sep 24, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-10743803)

Is it possible to define how each Node transforms the state rather than defining it globally within the global Graph State?

1

1 reply

[![@quantumqoder](https://avatars.githubusercontent.com/u/78647354?u=81abf894651605122b2bc9f75b725b009e1166d6&v=4)](https://github.com/quantumqoder)

[quantumqoder](https://github.com/quantumqoder) [Feb 26](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-12330065)

I'm also facing a similar issue, but it seems that returning from a node always modifies (adds into) the global state. If we want to remove any values (say, from the `messages` field), there's no way to do so.

[![@ashantanu](https://avatars.githubusercontent.com/u/14858985?u=8a09fd313f96b28b53d810fd96a447108c736840&v=4)ashantanu](https://github.com/ashantanu) [Sep 27, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-10780331)

another interesting behaviour, if i do

```notranslate
builder.add_edge("b2", "d")
builder.add_edge("c", "d")

```

instead of

```notranslate
builder.add_edge(["b2", "c"], "d")

```

then d is executed twice and doesn't wait for both to complete

1

👍1

0 replies

[![@khw11044](https://avatars.githubusercontent.com/u/51473705?u=fc7de0c8339a3ffdce70a93a12375a50f8a69843&v=4)khw11044](https://github.com/khw11044) [Oct 4, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-10840119)

edited

I have solved this problem.

ValueError: Already found path for node 'page\_element\_extractor\_node'.

For multiple edges, use StateGraph with an annotated state key.

[https://hyundoil.tistory.com/383](https://hyundoil.tistory.com/383)

2

0 replies

[![@ganeshghag](https://avatars.githubusercontent.com/u/3908312?u=7285d1a9499cb14c56a2ca4976c1cf9db9cc535e&v=4)ganeshghag](https://github.com/ganeshghag) [Dec 10, 2024](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-11520136)

parallel paths for execution entails, any given instance of workflow may have 2 or more current nodes of execution and therefore 2 or more rejoin-points,

if each parallel branch had a human-in-loop, then to continue the workflow instance, how will we specify which parallel branch to continue?

does agentexecutor invoke function support specifying branch-id?

1

0 replies

[![@djprawns](https://avatars.githubusercontent.com/u/3663330?u=35367c8a7be62f945e489c43d25e5481f1f616f7&v=4)djprawns](https://github.com/djprawns) [Jan 24](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-11937553)

Correct me if im wrong, but I tested out the below code with some time delay to see whether the parallel nodes (which do run parallely) run in a fashion that if one finishes then it moves ahead to the next node. But I observed that the nodes at a particular parallel layer wait until both finished. Why is this happening. You can observe this in the following example. How can make two branches run in a way that they run parallely and "asynchronously".

```notranslate
import time
import random
import operator
from typing import Annotated, Any

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

import operator
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph

class State(TypedDict):
    # The operator.add reducer fn makes this append-only
    aggregate: Annotated[list, operator.add]

class ReturnNodeValue:
    def __init__(self, node_secret: str):
        self._value = node_secret

    def __call__(self, state: State) -> Any:
        print(f"Adding {self._value} to {state['aggregate']}")
        time.sleep(random.random())
        return {"aggregate": [self._value]}

builder = StateGraph(State)
builder.add_node("a", ReturnNodeValue("I'm A"))
builder.add_edge(START, "a")
builder.add_node("b", ReturnNodeValue("I'm B"))
builder.add_node("b2", ReturnNodeValue("I'm B2"))
builder.add_node("c", ReturnNodeValue("I'm C"))
builder.add_node("d", ReturnNodeValue("I'm D"))
builder.add_edge("a", "b")
builder.add_edge("a", "c")
builder.add_edge("b", "b2")
builder.add_edge(["b2", "c"], "d")
builder.add_edge("d", END)
graph = builder.compile()

graph.invoke({"aggregate": []})

```

1

0 replies

[![@italoricardogeskeseg](https://avatars.githubusercontent.com/u/151568113?v=4)italoricardogeskeseg](https://github.com/italoricardogeskeseg) [Feb 5](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-12074432)

I have two parallel agents in two different subgraphs, they dont know each other, they are independent. Each agent will output its own response when it finishes. Is it possible to get specific agent output? I want to display each agent response in different space at same time.

2

1 reply

[![@TJKlein](https://avatars.githubusercontent.com/u/7634373?v=4)](https://github.com/TJKlein)

[TJKlein](https://github.com/TJKlein) [Feb 18](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-12230347)

Yes, I am also interested in this. Aggregating the result from two branches and showing some intermediate result.

[![@quantumqoder](https://avatars.githubusercontent.com/u/78647354?u=81abf894651605122b2bc9f75b725b009e1166d6&v=4)quantumqoder](https://github.com/quantumqoder) [Feb 26](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-12329996)

Langgraph is really a great framework and I really prefer it above any other in the market, but what I can't understand is how do I edit the graph state (remove certain values) from within a node. To make it more clear, lets consider that I've a `GraphState` as follows:

```
class GraphState(TypedDict):
    messages: Annotated[list, operator.add]
```

Now, if I return from a node something like: `{"messages": ["hi"]}`, it'll add into the `messages` field of the `GraphState` modifying it as (say) `{"messages": [..., "hello", "everyone", "hi"]}`. This is great in the sense that I don't need to manually append and update the state when fanning-in, but becomes a problem when I need to update (replace few values) the state in a node as follows:

```
def node_x(state: GraphState):
    messages = state["messages"]
    messages = state["messages"][:-2] + ["world"]
    return {"messages": messages}
```

Now, since the `messages` field is annotated with `operator.add`, it just modifies the state as `{"messages": [..., "hello", "everyone", "hi", ..., "hello", "world"]}`. Rather, I wanted something like `{"messages": [..., "hello", "world"]}`.

Of course, I also tried without the `Annotated` and defining the `GraphState` as:

```
class GraphState(TypedDict):
    messages: list
```

But, then while fanning-in, I'm encountering the following error:

```
langgraph.errors.InvalidUpdateError: At key 'messages': Can receive only one value per step. Use an Annotated key to handle multiple values.
```

I've even tried using the [Command](https://langchain-ai.github.io/langgraph/concepts/low_level/#command), but it's still causing the same issue for me. There seems to be no way to remove values once they've been added into the state.

1

0 replies

[![@crimson206](https://avatars.githubusercontent.com/u/110409356?u=a4263e61404dfc44c6c7a6273269c95a2526fbe3&v=4)crimson206](https://github.com/crimson206) [Mar 8](https://github.com/langchain-ai/langgraph/discussions/540#discussioncomment-12435646)

I've created additional simple examples to expand on this topic. Please refer to the link below:

- [Conditional Edge](https://github.com/crimson206/langgraph-dev-tool/blob/main/example/langgraph/conditional_edge.ipynb)

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fbranching%2F)