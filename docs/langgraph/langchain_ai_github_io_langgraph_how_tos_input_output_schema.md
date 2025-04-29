[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/input_output_schema/#how-to-define-inputoutput-schema-for-your-graph)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/input_output_schema.ipynb "Edit this page")

# How to define input/output schema for your graph [¶](https://langchain-ai.github.io/langgraph/how-tos/input_output_schema/\#how-to-define-inputoutput-schema-for-your-graph "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [Multiple Schemas](https://langchain-ai.github.io/langgraph/concepts/low_level/#multiple-schemas)
- [State Graph](https://langchain-ai.github.io/langgraph/concepts/low_level/#stategraph)

By default, `StateGraph` operates with a single schema, and all nodes are expected to communicate using that schema. However, it's also possible to define distinct input and output schemas for a graph.

When distinct schemas are specified, an internal schema will still be used for communication between nodes. The input schema ensures that the provided input matches the expected structure, while the output schema filters the internal data to return only the relevant information according to the defined output schema.

In this example, we'll see how to define distinct input and output schema.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/input_output_schema/\#setup "Permanent link")

First, let's install the required packages

```md-code__content
%%capture --no-stderr
%pip install -U langgraph

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Define and use the graph [¶](https://langchain-ai.github.io/langgraph/how-tos/input_output_schema/\#define-and-use-the-graph "Permanent link")

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END)

```md-code__content
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

# Define the schema for the input
class InputState(TypedDict):
    question: str

# Define the schema for the output
class OutputState(TypedDict):
    answer: str

# Define the overall schema, combining both input and output
class OverallState(InputState, OutputState):
    pass

# Define the node that processes the input and generates an answer
def answer_node(state: InputState):
    # Example answer and an extra key
    return {"answer": "bye", "question": state["question"]}

# Build the graph with input and output schemas specified
builder = StateGraph(OverallState, input=InputState, output=OutputState)
builder.add_node(answer_node)  # Add the answer node
builder.add_edge(START, "answer_node")  # Define the starting edge
builder.add_edge("answer_node", END)  # Define the ending edge
graph = builder.compile()  # Compile the graph

# Invoke the graph with an input and print the result
print(graph.invoke({"question": "hi"}))

```

```md-code__content
{'answer': 'bye'}

```

Notice that the output of invoke only includes the output schema.

Was this page helpful?






Thanks for your feedback!






Thanks for your feedback! Please help us improve this page by adding to the discussion below.


## Comments

[iframe](https://giscus.app/en/widget?origin=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Finput_output_schema%2F&session=&theme=preferred_color_scheme&reactionsEnabled=1&emitMetadata=0&inputPosition=bottom&repo=langchain-ai%2Flanggraph&repoId=R_kgDOKFU0lQ&category=Discussions&categoryId=DIC_kwDOKFU0lc4CfZgA&strict=0&description=Build+reliable%2C+stateful+AI+systems%2C+without+giving+up+control&backLink=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Finput_output_schema%2F&term=langgraph%2Fhow-tos%2Finput_output_schema%2F)

Back to top