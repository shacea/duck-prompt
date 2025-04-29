[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/state-model/#how-to-use-pydantic-model-as-graph-state)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/state-model.ipynb "Edit this page")

# How to use Pydantic model as graph state [¶](https://langchain-ai.github.io/langgraph/how-tos/state-model/\#how-to-use-pydantic-model-as-graph-state "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [State](https://langchain-ai.github.io/langgraph/concepts/low_level/#state)
- [Nodes](https://langchain-ai.github.io/langgraph/concepts/low_level/#nodes)
- [Pydantic](https://github.com/pydantic/pydantic): this is a popular Python library for run time validation.


A [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.StateGraph) accepts a `state_schema` argument on initialization that specifies the "shape" of the state that the nodes in the graph can access and update.

In our examples, we typically use a python-native `TypedDict` for `state_schema` (or in the case of [MessageGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#messagegraph), a [list](https://docs.python.org/3/library/stdtypes.html#list)), but `state_schema` can be any [type](https://docs.python.org/3/library/stdtypes.html#type-objects).

In this how-to guide, we'll see how a [Pydantic BaseModel](https://docs.pydantic.dev/latest/api/base_model/). can be used for `state_schema` to add run time validation on **inputs**.

Known Limitations

- This notebook uses Pydantic v2 `BaseModel`, which requires `langchain-core >= 0.3`. Using `langchain-core < 0.3` will result in errors due to mixing of Pydantic v1 and v2 `BaseModels`.

- Currently, the \`output\` of the graph will \*\*NOT\*\* be an instance of a pydantic model.

- Run-time validation only occurs on \*\*inputs\*\* into nodes, not on the outputs.

- The validation error trace from pydantic does not show which node the error arises in.


## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/state-model/\#setup "Permanent link")

First we need to install the packages required

```md-code__content
%%capture --no-stderr
%pip install --quiet -U langgraph

```

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Input Validation [¶](https://langchain-ai.github.io/langgraph/how-tos/state-model/\#input-validation "Permanent link")

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END)

```md-code__content
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from pydantic import BaseModel

# The overall state of the graph (this is the public state shared across nodes)
class OverallState(BaseModel):
    a: str

def node(state: OverallState):
    return {"a": "goodbye"}

# Build the state graph
builder = StateGraph(OverallState)
builder.add_node(node)  # node_1 is the first node
builder.add_edge(START, "node")  # Start the graph with node_1
builder.add_edge("node", END)  # End the graph after node_1
graph = builder.compile()

# Test the graph with a valid input
graph.invoke({"a": "hello"})

```

```md-code__content
{'a': 'goodbye'}

```

Invoke the graph with an **invalid** input

```md-code__content
try:
    graph.invoke({"a": 123})  # Should be a string
except Exception as e:
    print("An exception was raised because `a` is an integer rather than a string.")
    print(e)

```

```md-code__content
An exception was raised because `a` is an integer rather than a string.
1 validation error for OverallState
a
  Input should be a valid string [type=string_type, input_value=123, input_type=int]
    For further information visit https://errors.pydantic.dev/2.9/v/string_type

```

## Multiple Nodes [¶](https://langchain-ai.github.io/langgraph/how-tos/state-model/\#multiple-nodes "Permanent link")

Run-time validation will also work in a multi-node graph. In the example below `bad_node` updates `a` to an integer.

Because run-time validation occurs on **inputs**, the validation error will occur when `ok_node` is called (not when `bad_node` returns an update to the state which is inconsistent with the schema).

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END)

```md-code__content
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from pydantic import BaseModel

# The overall state of the graph (this is the public state shared across nodes)
class OverallState(BaseModel):
    a: str

def bad_node(state: OverallState):
    return {
        "a": 123  # Invalid
    }

def ok_node(state: OverallState):
    return {"a": "goodbye"}

# Build the state graph
builder = StateGraph(OverallState)
builder.add_node(bad_node)
builder.add_node(ok_node)
builder.add_edge(START, "bad_node")
builder.add_edge("bad_node", "ok_node")
builder.add_edge("ok_node", END)
graph = builder.compile()

# Test the graph with a valid input
try:
    graph.invoke({"a": "hello"})
except Exception as e:
    print("An exception was raised because bad_node sets `a` to an integer.")
    print(e)

```

```md-code__content
An exception was raised because bad_node sets `a` to an integer.
1 validation error for OverallState
a
  Input should be a valid string [type=string_type, input_value=123, input_type=int]
    For further information visit https://errors.pydantic.dev/2.9/v/string_type

```

## Multiple Nodes [¶](https://langchain-ai.github.io/langgraph/how-tos/state-model/\#multiple-nodes_1 "Permanent link")

Run-time validation will also work in a multi-node graph. In the example below `bad_node` updates `a` to an integer.

Because run-time validation occurs on **inputs**, the validation error will occur when `ok_node` is called (not when `bad_node` returns an update to the state which is inconsistent with the schema).

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END)

```md-code__content
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from pydantic import BaseModel

# The overall state of the graph (this is the public state shared across nodes)
class OverallState(BaseModel):
    a: str

def bad_node(state: OverallState):
    return {
        "a": 123  # Invalid
    }

def ok_node(state: OverallState):
    return {"a": "goodbye"}

# Build the state graph
builder = StateGraph(OverallState)
builder.add_node(bad_node)
builder.add_node(ok_node)
builder.add_edge(START, "bad_node")
builder.add_edge("bad_node", "ok_node")
builder.add_edge("ok_node", END)
graph = builder.compile()

# Test the graph with a valid input
try:
    graph.invoke({"a": "hello"})
except Exception as e:
    print("An exception was raised because bad_node sets `a` to an integer.")
    print(e)

```

## Advanced Pydantic Model Usage [¶](https://langchain-ai.github.io/langgraph/how-tos/state-model/\#advanced-pydantic-model-usage "Permanent link")

This section covers more advanced topics when using Pydantic models with LangGraph.

### Serialization Behavior [¶](https://langchain-ai.github.io/langgraph/how-tos/state-model/\#serialization-behavior "Permanent link")

When using Pydantic models as state schemas, it's important to understand how serialization works, especially when:
\- Passing Pydantic objects as inputs
\- Receiving outputs from the graph
\- Working with nested Pydantic models

Let's see these behaviors in action:

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END)

```md-code__content
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

class NestedModel(BaseModel):
    value: str

class ComplexState(BaseModel):
    text: str
    count: int
    nested: NestedModel

def process_node(state: ComplexState):
    # Node receives a validated Pydantic object
    print(f"Input state type: {type(state)}")
    print(f"Nested type: {type(state.nested)}")

    # Return a dictionary update
    return {"text": state.text + " processed", "count": state.count + 1}

# Build the graph
builder = StateGraph(ComplexState)
builder.add_node("process", process_node)
builder.add_edge(START, "process")
builder.add_edge("process", END)
graph = builder.compile()

# Create a Pydantic instance for input
input_state = ComplexState(text="hello", count=0, nested=NestedModel(value="test"))
print(f"Input object type: {type(input_state)}")

# Invoke graph with a Pydantic instance
result = graph.invoke(input_state)
print(f"Output type: {type(result)}")
print(f"Output content: {result}")

# Convert back to Pydantic model if needed
output_model = ComplexState(**result)
print(f"Converted back to Pydantic: {type(output_model)}")

```

### Runtime Type Coercion [¶](https://langchain-ai.github.io/langgraph/how-tos/state-model/\#runtime-type-coercion "Permanent link")

Pydantic performs runtime type coercion for certain data types. This can be helpful but also lead to unexpected behavior if you're not aware of it.

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END)

```md-code__content
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

class CoercionExample(BaseModel):
    # Pydantic will coerce string numbers to integers
    number: int
    # Pydantic will parse string booleans to bool
    flag: bool

def inspect_node(state: CoercionExample):
    print(f"number: {state.number} (type: {type(state.number)})")
    print(f"flag: {state.flag} (type: {type(state.flag)})")
    return {}

builder = StateGraph(CoercionExample)
builder.add_node("inspect", inspect_node)
builder.add_edge(START, "inspect")
builder.add_edge("inspect", END)
graph = builder.compile()

# Demonstrate coercion with string inputs that will be converted
result = graph.invoke({"number": "42", "flag": "true"})

# This would fail with a validation error
try:
    graph.invoke({"number": "not-a-number", "flag": "true"})
except Exception as e:
    print(f"\nExpected validation error: {e}")

```

### Working with Message Models [¶](https://langchain-ai.github.io/langgraph/how-tos/state-model/\#working-with-message-models "Permanent link")

When working with LangChain message types in your state schema, there are important considerations for serialization. You should use `AnyMessage` (rather than `BaseMessage`) for proper serialization/deserialization when using message objects over the wire:

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html) \| [AIMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html) \| [AnyMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.AnyMessage.html)

```md-code__content
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from typing import List

class ChatState(BaseModel):
    messages: List[AnyMessage]
    context: str

def add_message(state: ChatState):
    return {"messages": state.messages + [AIMessage(content="Hello there!")]}

builder = StateGraph(ChatState)
builder.add_node("add_message", add_message)
builder.add_edge(START, "add_message")
builder.add_edge("add_message", END)
graph = builder.compile()

# Create input with a message
initial_state = ChatState(
    messages=[HumanMessage(content="Hi")], context="Customer support chat"
)

result = graph.invoke(initial_state)
print(f"Output: {result}")

# Convert back to Pydantic model to see message types
output_model = ChatState(**result)
for i, msg in enumerate(output_model.messages):
    print(f"Message {i}: {type(msg).__name__} - {msg.content}")

```

## Comments

giscus

#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/1306)

#### [9 comments](https://github.com/langchain-ai/langgraph/discussions/1306)

#### ·

#### 5 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@whamsicore](https://avatars.githubusercontent.com/u/571679?u=ced9e37dfa926ed906b6e6da33d2cc75872c99d4&v=4)whamsicore](https://github.com/whamsicore) [Aug 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-10301688)

This is pretty cool, but i don't like how black box the model is. Can new tools be added to the model, post compile? Doesn't seem so. This is more of a defect of langchain, however

1

2 replies

[![@eloko7](https://avatars.githubusercontent.com/u/165784400?u=a9fe2bf9f0bca7796ca8a31b80376a804764bcfa&v=4)](https://github.com/eloko7)

[eloko7](https://github.com/eloko7) [Aug 13, 2024](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-10321811)

You can place `tool_executor = ToolExecutor(tools)` and ` model = model.bind_tools(tools)` inside a function that you invoke doing runtime. This function can also take config or state as input variables where you can hide some logic for changing or adding tools after compiling the graph.

[![@whamsicore](https://avatars.githubusercontent.com/u/571679?u=ced9e37dfa926ed906b6e6da33d2cc75872c99d4&v=4)](https://github.com/whamsicore)

[whamsicore](https://github.com/whamsicore) [Aug 14, 2024](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-10332661)

That's very cool. Thx for the tip!

[![@whamsicore](https://avatars.githubusercontent.com/u/571679?u=ced9e37dfa926ed906b6e6da33d2cc75872c99d4&v=4)whamsicore](https://github.com/whamsicore) [Aug 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-10301725)

also, in the description of pydantic state it says:

"If you want to apply additional validation on state updates, you could instead opt for a pydantic BaseModel."

Does this example actually implement any additional validation on state updates? The only affect seems to be "messages attribute is treated as "append-only". How do I actually add validation on state change, then?

1

👍2

0 replies

[![@rhlarora84](https://avatars.githubusercontent.com/u/15618263?u=e3d3c5fd1d9fe4d09dbc0cbb0564de2f9bc57654&v=4)rhlarora84](https://github.com/rhlarora84) [Aug 13, 2024](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-10330256)

Can you please help me understand other attributes when creating StateGraph?

`StateGraph(AgentState, input=MessagesState, output=OutputState, config_schema=ConfigSchema)`

- What is the difference between AgentState & input? Does the input reflects the input to the entrypoint and AgentState represents the state of the graph?
- Same applies for OutputState but before the END?

1

1 reply

[![@rhlarora84](https://avatars.githubusercontent.com/u/15618263?u=e3d3c5fd1d9fe4d09dbc0cbb0564de2f9bc57654&v=4)](https://github.com/rhlarora84)

[rhlarora84](https://github.com/rhlarora84) [Aug 13, 2024](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-10330262)

Found the answer [https://langchain-ai.github.io/langgraph/how-tos/input\_output\_schema/](https://langchain-ai.github.io/langgraph/how-tos/input_output_schema/)

[![@Sergears](https://avatars.githubusercontent.com/u/58189334?u=752260bb527f5637d31e91d74da6551543f195cd&v=4)Sergears](https://github.com/Sergears) [Sep 16, 2024](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-10661974)

When I try to run this example, I get an error from the `ToolNode`: `'AgentState' object has no attribute 'get'`. So seems like it still expects a `TypedDict` object for state (dependency versions langgraph=0.2.18, langchain-core=0.2.39)

1

👍1

0 replies

[![@tomas-herman](https://avatars.githubusercontent.com/u/45421964?v=4)tomas-herman](https://github.com/tomas-herman) [Dec 20, 2024](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-11630898)

When I use BaseModel for the agent state and inside it I use a list of class also defined as BaseModel I am getting serialisation issues and "type":"not\_implemented

Precise example is agent state

class AgentState(BaseModel):

"""State class for the chat agent.

```notranslate
This class uses Pydantic for type validation while maintaining compatibility
with LangGraph's message management system.

Attributes:
    user_id: Unique identifier for the user
    project_id: Unique identifier for the project
    messages: List of chat messages managed by LangGraph's add_messages function
    follow_up_questions: List of follow-up questions as strings
    references: List of Reference objects containing title and URL

"""

user_id: str = Field(..., description="Unique identifier for the user")
project_id: str = Field(..., description="Unique identifier for the project")
messages: Annotated[list[AnyMessage], add_messages] = Field(
    default_factory=list, description="List of chat messages managed by LangGraph"
)
follow_up_questions: list[str] = Field(
    default_factory=list, description="List of follow-up questions"
)
references: list[Reference] = Field(
    default_factory=list, description="List of references with title and URL"
)

```

And reference defnied as

class Reference(BaseModel):

"""Model representing a reference with a title and URL."""

```notranslate
title: str = Field(..., description="Title of the reference")
url: str = Field(..., description="URL link of the reference")

```

Are causing type not implemented

references":\[{"lc":1,"type":"not\_implemented","id":\["app","state","Reference"\],"repr":"Reference(title='How to Create a Successful Startup', url='https://example.com/startup-guide')"},{"lc":1,"type":"not\_implemented","id":\["app","state","Reference"\],"repr":"Reference(title='Market Research Fundamentals', url='https://example.com/market-research')"},{"lc":1,"type":"not\_implemented","id":\["app","state","Reference"\],"repr":"Reference(title='Startup Funding Strategies', url='https://example.com/funding-guide')"}\]}"

While if I define the reference as TypedDict

class Reference(TypedDict):

"""Dictionary representing a reference with a title and URL."""

```notranslate
title: str  # Title of the reference
url: str  # URL link of the reference

```

All is fine

"references":\[{"title":"How to Create a Successful Startup","url":"https://example.com/startup-guide"},{"title":"Market Research Fundamentals","url":"https://example.com/market-research"},{"title":"Startup Funding Strategies","url":"https://example.com/funding-guide"}\]}"

Am I doing something wrong or why is the nested BaseModel not recognised correctly and the nested TypedDict works fine?

2

0 replies

[![@Jackoder](https://avatars.githubusercontent.com/u/3930446?u=71bf357cc7cb9769cd9e60dd7e6df8b0da522047&v=4)Jackoder](https://github.com/Jackoder) [Dec 25, 2024](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-11662311)

When I run `python agent.py`, everything is fine. But it throws exception when I run `langgraph dev` and submit with LangGraph Studio. What's the difference?

```notranslate
Traceback (most recent call last):
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langgraph_api\queue.py", line 156, in worker
    await asyncio.wait_for(consume(stream, run_id), timeout)
  File "D:\AI\Anaconda3\envs\py311\Lib\asyncio\tasks.py", line 489, in wait_for
    return fut.result()
           ^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langgraph_api\stream.py", line 285, in consume
    raise e from None
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langgraph_api\stream.py", line 275, in consume
    async for mode, payload in stream:
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langgraph_api\stream.py", line 226, in astream_state
    event = await wait_if_not_done(anext(stream, sentinel), done)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langgraph_api\asyncio.py", line 67, in wait_if_not_done
    raise e.exceptions[0] from None
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langgraph\pregel\__init__.py", line 1874, in astream
    async for _ in runner.atick(
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langgraph\pregel\runner.py", line 444, in atick
    _panic_or_proceed(
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langgraph\pregel\runner.py", line 539, in _panic_or_proceed
    raise exc
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langgraph\pregel\retry.py", line 132, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langgraph\utils\runnable.py", line 445, in ainvoke
    input = await step.ainvoke(input, config, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langgraph\utils\runnable.py", line 236, in ainvoke
    ret = await asyncio.create_task(coro, context=context)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langchain_core\runnables\config.py", line 588, in run_in_executor
    return await asyncio.get_running_loop().run_in_executor(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\concurrent\futures\thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langchain_core\runnables\config.py", line 579, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\llm-rag\./src/app.py", line 276, in grade_documents
    score = retrieval_grader.invoke(
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langchain_core\runnables\base.py", line 3024, in invoke
    input = context.run(step.invoke, input, config)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langchain_core\output_parsers\base.py", line 193, in invoke
    return self._call_with_config(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langchain_core\runnables\base.py", line 1927, in _call_with_config
    context.run(
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langchain_core\runnables\config.py", line 396, in call_func_with_variable_args
    return func(input, **kwargs)  # type: ignore[call-arg]
           ^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langchain_core\output_parsers\base.py", line 194, in <lambda>
    lambda inner_input: self.parse_result(
                        ^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langchain_core\output_parsers\openai_tools.py", line 298, in parse_result
    raise e
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\langchain_core\output_parsers\openai_tools.py", line 293, in parse_result
    pydantic_objects.append(name_dict[res["type"]](**res["args"]))
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\AI\Anaconda3\envs\py311\Lib\site-packages\pydantic\main.py", line 193, in __init__
    self.__pydantic_validator__.validate_python(data, self_instance=self)
pydantic_core._pydantic_core.ValidationError: 1 validation error for GradeDocuments
binary_score
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.8/v/missing
During task with name 'grade_documents' and id '3d60efe6-16a6-f1da-fca0-46ad323838ce'

```

1

0 replies

[![@Nvillaluenga](https://avatars.githubusercontent.com/u/32406287?u=6bd57124651db60c2b7ca7e125aee026f58a45c1&v=4)Nvillaluenga](https://github.com/Nvillaluenga) [Jan 28](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-11986123)

Is there a way to set a state with default values? something like this

```
from langgraph.graph import MessagesState

class State(MessagesState):
    summary: str
    catalog: list = []
    cart: list = []
```

Because even if I do this I don't see the cart and catalog attributes inited in my graph and that leads to errors when trying to inserte them to tools for later using the InjectedState

1

0 replies

[![@justuswolff-audit](https://avatars.githubusercontent.com/u/155981214?u=c896ea0a18fb022b2845925da508495b24f46900&v=4)justuswolff-audit](https://github.com/justuswolff-audit) [Feb 11](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-12136079)

Something is not working for me. If I switch the order of the nodes the example breaks:

```
# Build the state graph
builder = StateGraph(OverallState)
builder.add_node(bad_node)
builder.add_node(ok_node)
builder.add_edge(START, "ok_node")
builder.add_edge("ok_node", "bad_node")
builder.add_edge("bad_node", END)
graph = builder.compile()

# Test the graph with a valid input
try:
    print(graph.invoke(OverallState(a="hello")))
except Exception as e:
    print("An exception was raised because bad_node sets a to an integer.")
    print(e)
```

and does not throw an exception. Anyone know why?

1

1 reply

[![@justuswolff-audit](https://avatars.githubusercontent.com/u/155981214?u=c896ea0a18fb022b2845925da508495b24f46900&v=4)](https://github.com/justuswolff-audit)

[justuswolff-audit](https://github.com/justuswolff-audit) [Feb 11](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-12136112)

Can't delete this, but the reason is noted above: "Because run-time validation occurs on inputs, the validation error will occur when ok\_node is called (not when bad\_node returns an update to the state which is inconsistent with the schema)." It was just the last node in the graph....

[![@Hamza5](https://avatars.githubusercontent.com/u/7011111?v=4)Hamza5](https://github.com/Hamza5) [Feb 12](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-12177264)

edited

This tutorial is missing an important stuff: the `add_messages` function. Using `TypedDict` we can write:

```
from typing_extensions import Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

class MessagesGraphState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
```

How to have the same exact effect (with `add_messages`) using Pydantic fields?

1

1 reply

[![@dakilasera](https://avatars.githubusercontent.com/u/63289411?v=4)](https://github.com/dakilasera)

[dakilasera](https://github.com/dakilasera) [Mar 4](https://github.com/langchain-ai/langgraph/discussions/1306#discussioncomment-12386227)

you can do like this..

```notranslate
messages: Annotated[list[AnyMessage], add_messages] = Field(
    default_factory=list, description="List of chat messages managed by LangGraph"
)

```

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fstate-model%2F)