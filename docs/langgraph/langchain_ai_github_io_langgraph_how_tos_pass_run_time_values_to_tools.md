[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/#how-to-pass-runtime-values-to-tools)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/pass-run-time-values-to-tools.ipynb "Edit this page")

# How to pass runtime values to tools [¶](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/\#how-to-pass-runtime-values-to-tools "Permanent link")

Sometimes, you want to let a tool-calling LLM populate a _subset_ of the tool functions' arguments and provide the other values for the other arguments at runtime. If you're using LangChain-style [tools](https://python.langchain.com/docs/concepts/#tools), an easy way to handle this is by annotating function parameters with [InjectedArg](https://python.langchain.com/docs/how_to/tool_runtime/). This annotation excludes that parameter from being shown to the LLM.

In LangGraph applications you might want to pass the graph state or [shared memory](https://langchain-ai.github.io/langgraph/how-tos/cross-thread-persistence/) (store) to the tools at runtime. This type of stateful tools is useful when a tool's output is affected by past agent steps (e.g. if you're using a sub-agent as a tool, and want to pass the message history in to the sub-agent), or when a tool's input needs to be validated given context from past agent steps.

In this guide we'll demonstrate how to do so using LangGraph's prebuilt [ToolNode](https://langchain-ai.github.io/langgraph/how-tos/tool-calling/).

Prerequisites

This guide targets \*\*LangChain tool calling\*\* assumes familiarity with the following:


- [Tools](https://python.langchain.com/docs/concepts/#tools)
- [State](https://langchain-ai.github.io/langgraph/concepts/low_level/#state)
- [Tool-calling](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/#tool-calling-agent)

You can still use tool calling in LangGraph using your provider SDK without losing any of LangGraph's core features.


The core technique in the examples below is to **annotate** a parameter as "injected", meaning it will be injected by your program and should not be seen or populated by the LLM. Let the following codesnippet serve as a tl;dr:

API Reference: [RunnableConfig](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.config.RunnableConfig.html) \| [InjectedToolArg](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.base.InjectedToolArg.html) \| [InjectedState](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.InjectedState)

```md-code__content
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from langgraph.store.base import BaseStore

from langgraph.prebuilt import InjectedState, InjectedStore

# Can be sync or async; @tool decorator not required
async def my_tool(
    # These arguments are populated by the LLM
    some_arg: str,
    another_arg: float,
    # The config: RunnableConfig is always available in LangChain calls
    # This is not exposed to the LLM
    config: RunnableConfig,
    # The following three are specific to the prebuilt ToolNode
    # (and `create_react_agent` by extension). If you are invoking the
    # tool on its own (in your own node), then you would need to provide these yourself.
    store: Annotated[BaseStore, InjectedStore],
    # This passes in the full state.
    state: Annotated[State, InjectedState],
    # You can also inject single fields from your state if you
    messages: Annotated[list, InjectedState("messages")]
    # The following is not compatible with create_react_agent or ToolNode
    # You can also exclude other arguments from being shown to the model.
    # These must be provided manually and are useful if you call the tools/functions in your own node
    # some_other_arg=Annotated["MyPrivateClass", InjectedToolArg],
):
    """Call my_tool to have an impact on the real world.

    Args:
        some_arg: a very important argument
        another_arg: another argument the LLM will provide
    """ # The docstring becomes the description for your tool and is passed to the model
    print(some_arg, another_arg, config, store, state, messages)
    # Config, some_other_rag, store, and state  are all "hidden" from
    # LangChain models when passed to bind_tools or with_structured_output
    return "... some response"

```

```md-code__content

```

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/\#setup "Permanent link")

First we need to install the packages required

```md-code__content
%%capture --no-stderr
%pip install --quiet -U langgraph langchain-openai

```

Next, we need to set API keys for OpenAI (the chat model we will use).

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


## Pass graph state to tools [¶](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/\#pass-graph-state-to-tools "Permanent link")

Let's first take a look at how to give our tools access to the graph state. We'll need to define our graph state:

API Reference: [Document](https://python.langchain.com/api_reference/core/documents/langchain_core.documents.base.Document.html)

```md-code__content
from typing import List

# this is the state schema used by the prebuilt create_react_agent we'll be using below
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.documents import Document

class State(AgentState):
    docs: List[str]

```

### Define the tools [¶](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/\#define-the-tools "Permanent link")

We'll want our tool to take graph state as an input, but we don't want the model to try to generate this input when calling the tool. We can use the `InjectedState` annotation to mark arguments as required graph state (or some field of graph state. These arguments will not be generated by the model. When using `ToolNode`, graph state will automatically be passed in to the relevant tools and arguments.

In this example we'll create a tool that returns Documents and then another tool that actually cites the Documents that justify a claim.

Using Pydantic with LangChain

This notebook uses Pydantic v2 `BaseModel`, which requires `langchain-core >= 0.3`. Using `langchain-core < 0.3` will result in errors due to mixing of Pydantic v1 and v2 `BaseModels`.


API Reference: [ToolMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.tool.ToolMessage.html) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [InjectedState](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.InjectedState)

```md-code__content
from typing import List, Tuple
from typing_extensions import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

@tool
def get_context(question: str, state: Annotated[dict, InjectedState]):
    """Get relevant context for answering the question."""
    return "\n\n".join(doc for doc in state["docs"])

```

If we look at the input schemas for these tools, we'll see that `state` is still listed:

```md-code__content
get_context.get_input_schema().schema()

```

```md-code__content
{'description': 'Get relevant context for answering the question.',
 'properties': {'question': {'title': 'Question', 'type': 'string'},
  'state': {'title': 'State', 'type': 'object'}},
 'required': ['question', 'state'],
 'title': 'get_context',
 'type': 'object'}

```

But if we look at the tool call schema, which is what is passed to the model for tool-calling, `state` has been removed:

```md-code__content
get_context.tool_call_schema.schema()

```

```md-code__content
{'description': 'Get relevant context for answering the question.',
 'properties': {'question': {'title': 'Question', 'type': 'string'}},
 'required': ['question'],
 'title': 'get_context',
 'type': 'object'}

```

### Define the graph [¶](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/\#define-the-graph "Permanent link")

In this example we will be using a [prebuilt ReAct agent](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/). We'll first need to define our model and a tool-calling node ( [ToolNode](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.ToolNode)):

API Reference: [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [ToolNode](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.ToolNode) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) \| [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver)

```md-code__content
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.checkpoint.memory import MemorySaver

model = ChatOpenAI(model="gpt-4o", temperature=0)
tools = [get_context]

# ToolNode will automatically take care of injecting state into tools
tool_node = ToolNode(tools)

checkpointer = MemorySaver()
graph = create_react_agent(model, tools, state_schema=State, checkpointer=checkpointer)

```

### Use it! [¶](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/\#use-it "Permanent link")

```md-code__content
docs = [\
    "FooBar company just raised 1 Billion dollars!",\
    "FooBar company was founded in 2019",\
]

inputs = {
    "messages": [{"type": "user", "content": "what's the latest news about FooBar"}],
    "docs": docs,
}
config = {"configurable": {"thread_id": "1"}}
for chunk in graph.stream(inputs, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

```

```md-code__content
================================[1m Human Message [0m=================================\
\
what's the latest news about FooBar\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  get_context (call_UkqfR7z2cLJQjhatUpDeEa5H)\
 Call ID: call_UkqfR7z2cLJQjhatUpDeEa5H\
  Args:\
    question: latest news about FooBar\
=================================[1m Tool Message [0m=================================\
Name: get_context\
\
FooBar company just raised 1 Billion dollars!\
\
FooBar company was founded in 2019\
==================================[1m Ai Message [0m==================================\
\
The latest news about FooBar is that the company has just raised 1 billion dollars.\
\
```\
\
## Pass shared memory (store) to the graph [¶](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/\#pass-shared-memory-store-to-the-graph "Permanent link")\
\
You might also want to give tools access to memory that is shared across multiple conversations or users. We can do it by passing LangGraph [Store](https://langchain-ai.github.io/langgraph/how-tos/cross-thread-persistence/) to the tools using a different annotation -- `InjectedStore`.\
\
Let's modify our example to save the documents in an in-memory store and retrieve them using `get_context` tool. We'll also make the documents accessible based on a user ID, so that some documents are only visible to certain users. The tool will then use the `user_id` provided in the [config](https://langchain-ai.github.io/langgraph/how-tos/pass-config-to-tools/) to retrieve a correct set of documents.\
\
Note\
\
Support for `Store` API and `InjectedStore` used in this notebook was added in LangGraph `v0.2.34`.\
\
`InjectedStore` annotation requires `langchain-core >= 0.3.8`\
\
```md-code__content\
from langgraph.store.memory import InMemoryStore\
\
doc_store = InMemoryStore()\
\
namespace = ("documents", "1")  # user ID\
doc_store.put(\
    namespace, "doc_0", {"doc": "FooBar company just raised 1 Billion dollars!"}\
)\
namespace = ("documents", "2")  # user ID\
doc_store.put(namespace, "doc_1", {"doc": "FooBar company was founded in 2019"})\
\
```\
\
### Define the tools [¶](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/\#define-the-tools_1 "Permanent link")\
\
API Reference: [RunnableConfig](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.config.RunnableConfig.html)\
\
```md-code__content\
from langgraph.store.base import BaseStore\
from langchain_core.runnables import RunnableConfig\
from langgraph.prebuilt import InjectedStore\
\
@tool\
def get_context(\
    question: str,\
    config: RunnableConfig,\
    store: Annotated[BaseStore, InjectedStore()],\
) -> Tuple[str, List[Document]]:\
    """Get relevant context for answering the question."""\
    user_id = config.get("configurable", {}).get("user_id")\
    docs = [item.value["doc"] for item in store.search(("documents", user_id))]\
    return "\n\n".join(doc for doc in docs)\
\
```\
\
We can also verify that the tool-calling model will ignore `store` arg of `get_context` tool:\
\
```md-code__content\
get_context.tool_call_schema.schema()\
\
```\
\
```md-code__content\
{'description': 'Get relevant context for answering the question.',\
 'properties': {'question': {'title': 'Question', 'type': 'string'}},\
 'required': ['question'],\
 'title': 'get_context',\
 'type': 'object'}\
\
```\
\
### Define the graph [¶](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/\#define-the-graph_1 "Permanent link")\
\
Let's update our ReAct agent:\
\
```md-code__content\
tools = [get_context]\
\
# ToolNode will automatically take care of injecting Store into tools\
tool_node = ToolNode(tools)\
\
checkpointer = MemorySaver()\
# NOTE: we need to pass our store to `create_react_agent` to make sure our graph is aware of it\
graph = create_react_agent(model, tools, checkpointer=checkpointer, store=doc_store)\
\
```\
\
### Use it! [¶](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/\#use-it_1 "Permanent link")\
\
Let's try running our graph with a `"user_id"` in the config.\
\
```md-code__content\
messages = [{"type": "user", "content": "what's the latest news about FooBar"}]\
config = {"configurable": {"thread_id": "1", "user_id": "1"}}\
for chunk in graph.stream({"messages": messages}, config, stream_mode="values"):\
    chunk["messages"][-1].pretty_print()\
\
```\
\
```md-code__content\
================================[1m Human Message [0m=================================\
\
what's the latest news about FooBar\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  get_context (call_ocyHBpGgF3LPFOgRKURBfkGG)\
 Call ID: call_ocyHBpGgF3LPFOgRKURBfkGG\
  Args:\
    question: latest news about FooBar\
=================================[1m Tool Message [0m=================================\
Name: get_context\
\
FooBar company just raised 1 Billion dollars!\
==================================[1m Ai Message [0m==================================\
\
The latest news about FooBar is that the company has just raised 1 billion dollars.\
\
```\
\
We can see that the tool only retrieved the correct document for user "1" when looking up the information in the store. Let's now try it again for a different user:\
\
```md-code__content\
messages = [{"type": "user", "content": "what's the latest news about FooBar"}]\
config = {"configurable": {"thread_id": "2", "user_id": "2"}}\
for chunk in graph.stream({"messages": messages}, config, stream_mode="values"):\
    chunk["messages"][-1].pretty_print()\
\
```\
\
```md-code__content\
================================[1m Human Message [0m=================================\
\
what's the latest news about FooBar\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  get_context (call_zxO9KVlL8UxFQUMb8ETeHNvs)\
 Call ID: call_zxO9KVlL8UxFQUMb8ETeHNvs\
  Args:\
    question: latest news about FooBar\
=================================[1m Tool Message [0m=================================\
Name: get_context\
\
FooBar company was founded in 2019\
==================================[1m Ai Message [0m==================================\
\
FooBar company was founded in 2019. If you need more specific or recent news, please let me know!\
\
```\
\
We can see that the tool pulled in a different document this time.\
\
## Comments\
\
giscus\
\
#### [7 reactions](https://github.com/langchain-ai/langgraph/discussions/681)\
\
👍6😕1\
\
#### [14 comments](https://github.com/langchain-ai/langgraph/discussions/681)\
\
#### ·\
\
#### 30 replies\
\
_– powered by [giscus](https://giscus.app/)_\
\
- Oldest\
- Newest\
\
[![@smathalikunnel](https://avatars.githubusercontent.com/u/8058707?v=4)smathalikunnel](https://github.com/smathalikunnel) [Jun 21, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-9836977)\
\
the document introduction mentions the usage of Runnable, and RunnableConfig -\
\
"To pass run time information, we will leverage the Runnable interface. The standard runnables methods (invoke, batch, stream etc.) accept a 2nd argument which is a RunnableConfig."\
\
But not clear from the tutorial if (or where) these objects are being used.\
\
1\
\
👍3\
\
0 replies\
\
[![@AFRT927](https://avatars.githubusercontent.com/u/96435047?u=ec35e7c52cfdd41d8bbee91f66f5b2a718174064&v=4)AFRT927](https://github.com/AFRT927) [Jul 12, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10032932)\
\
The documentation on this link: [https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/)\
\
is no longer accessible.\
\
Can you show me how pass run time values to tools when working with langgraph?\
\
1\
\
2 replies\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Jul 12, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10033136)\
\
Collaborator\
\
[@AFRT927](https://github.com/AFRT927) i think it might have been removed by mistake, check this out here in the meantime [https://github.com/langchain-ai/langgraph/blob/main/examples/pass-run-time-values-to-tools.ipynb](https://github.com/langchain-ai/langgraph/blob/main/examples/pass-run-time-values-to-tools.ipynb)\
\
👍1\
\
[![@AFRT927](https://avatars.githubusercontent.com/u/96435047?u=ec35e7c52cfdd41d8bbee91f66f5b2a718174064&v=4)](https://github.com/AFRT927)\
\
[AFRT927](https://github.com/AFRT927) [Jul 12, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10033171)\
\
[@vbarda](https://github.com/vbarda) It is correct, thank you very much!\
\
[![@cplog](https://avatars.githubusercontent.com/u/38715806?v=4)cplog](https://github.com/cplog) [Jul 23, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10121501)\
\
edited\
\
is this method still valide?\
\
with 0.1.9 version\
\
I got\
\
`ImportError: cannot import name 'InjectedState' from 'langgraph.prebuilt' (/.../llm_base/lib/python3.10/site-packages/langgraph/prebuilt/__init__.py)`\
\
1\
\
1 reply\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Jul 23, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10129822)\
\
Collaborator\
\
[@cplog](https://github.com/cplog) thanks for reporting! should be fixed in 0.1.10 -- please let us know if you run into any other issues\
\
👍1\
\
[![@chintagunta](https://avatars.githubusercontent.com/u/677413?u=c9e95a8bc1112c4f7e81d54bd8bf9183dda42a9f&v=4)chintagunta](https://github.com/chintagunta) [Jul 26, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10154129)\
\
I am able to read the state, but unable to update it, pls help.\
\
Tried: 1. Setting the value, 2. Returning the object {key, value}\
\
Didn't work.\
\
1\
\
👍3\
\
8 replies\
\
Show 3 previous replies\
\
[![@antoremin](https://avatars.githubusercontent.com/u/6918736?v=4)](https://github.com/antoremin)\
\
[antoremin](https://github.com/antoremin) [Sep 23, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10729263)\
\
edited\
\
Would love a native support for state updates in tool nodes!\
\
[![@dean2727](https://avatars.githubusercontent.com/u/47488483?u=1c7041b96f152e3093e65f1f977352249df5dead&v=4)](https://github.com/dean2727)\
\
[dean2727](https://github.com/dean2727) [Sep 23, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10731140)\
\
What I did to update my state was, inside of the function where I define my agent node, after `invoke()`, I can check the last message to see if it is of type `ToolMessage`. If it is, and my tool is defined with `response_format="content_and_artifact"`, then I can access the `.artifact` attribute of the message, which contains the the data (resulting from the tool call, the second element of the tuple) that I can then use to update state. And, because this is an agent node, I can update the state by returning a dictionary with whatever keys (aspects of the state) that were updated.\
\
[![@antoremin](https://avatars.githubusercontent.com/u/6918736?v=4)](https://github.com/antoremin)\
\
[antoremin](https://github.com/antoremin) [Sep 24, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10741302)\
\
For my case, I ended up getting len() of tool calls kwargs in agent node response and popping that number from the queue.\
\
[![@fletchertyler914](https://avatars.githubusercontent.com/u/3344498?u=be6f2ff193f913fb9b7ad2c9c1c98b6f8eaf93f4&v=4)](https://github.com/fletchertyler914)\
\
[fletchertyler914](https://github.com/fletchertyler914) [Sep 27, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10777438)\
\
You need to define a custom Tool Node, and after invoking the tool from the node, you can extract the properties you want to update the state with from the tool message/artifact.\
\
So Agent -> Tool Call -> Custom Tool Node -> Agent\
\
When the Custom Tool Node invokes the tool call, you can use the result to update the state directly by returning it from the Custom Tool Node.\
\
👍1\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Dec 17, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-11599206)\
\
Collaborator\
\
Hi folks! We have now added support for updating the state from the tools using the new [Command](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Command) type. Please see this how-to guide for reference [https://langchain-ai.github.io/langgraph/how-tos/update-state-from-tools/](https://langchain-ai.github.io/langgraph/how-tos/update-state-from-tools/). Let me know if you have any questions / feedback\
\
[![@ashantanu](https://avatars.githubusercontent.com/u/14858985?u=8a09fd313f96b28b53d810fd96a447108c736840&v=4)ashantanu](https://github.com/ashantanu) [Jul 30, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10185528)\
\
should we use `RunnableConfig` or `InjectedState`? what is the recommended way?\
\
3\
\
0 replies\
\
[![@hepbc](https://avatars.githubusercontent.com/u/11642637?v=4)hepbc](https://github.com/hepbc) [Aug 14, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10333229)\
\
Hi friends: this function's artifact is a list of Documents\
\
```notranslate\
@tool(parse_docstring=True, response_format="content_and_artifact")\
def get_context(question: List[str]) -> Tuple[str, List[Document]]:\
\
```\
\
How can I define it to return another data type like json or a pandas dataframe? Would appreciate some help here!\
\
Thanks\
\
1\
\
2 replies\
\
[![@hepbc](https://avatars.githubusercontent.com/u/11642637?v=4)](https://github.com/hepbc)\
\
[hepbc](https://github.com/hepbc) [Aug 14, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10333662)\
\
[@vbarda](https://github.com/vbarda) could you help? Application is as follows: a tool returning a dataframe, say dates and price, and another tool plotting it.\
\
Thanks and look forward!\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Aug 20, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10400109)\
\
Collaborator\
\
hm, have you tried returning the dataframe in your function instead of the document list? did you get any errors?\
\
[![@FMurray](https://avatars.githubusercontent.com/u/5853331?u=3aff951378adf180b922cbb9d0d609c495de49f6&v=4)FMurray](https://github.com/FMurray) [Aug 20, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10398708)\
\
Using version 0.2.4, my tool is always being invoked with the InjectedState parameter, even though the tool call schema shows that it's not included:\
\
from langgraph.prebuilt import InjectedState\
\
```notranslate\
class ChessMove(BaseModel):\
    san: str = Field(description="SAN (standard algebraic notation) of a chess move")\
\
@tool("make-move", args_schema=ChessMove)\
def make_move(san: str, state: Annotated[dict, InjectedState]) -> str:\
    """Make a move in the chess game"""\
    board = state.get("board")\
    board.push_san(san)\
    return board.fen()\
\
tool = make_move\
tools = [make_move]\
\
```\
\
Tool call schema:\
\
```notranslate\
{'title': 'make-move',\
 'description': 'Make a move in the chess game',\
 'type': 'object',\
 'properties': {'san': {'title': 'San',\
   'description': 'SAN (standard algebraic notation) of a chess move',\
   'type': 'string'}},\
 'required': ['san']}\
\
```\
\
1\
\
2 replies\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Aug 20, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10400128)\
\
Collaborator\
\
that's by design -- the state is not included in the schema because it's not sent to the LLM. see the end of this section [https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/#defining-the-tools](https://langchain-ai.github.io/langgraph/how-tos/pass-run-time-values-to-tools/#defining-the-tools)\
\
[![@FMurray](https://avatars.githubusercontent.com/u/5853331?u=3aff951378adf180b922cbb9d0d609c495de49f6&v=4)](https://github.com/FMurray)\
\
[FMurray](https://github.com/FMurray) [Aug 27, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10467531)\
\
I think you misread - the tool invoke is always passing the state arg, even though I've annotated it as previously mentioned\
\
[![@tmishinev](https://avatars.githubusercontent.com/u/77745398?v=4)tmishinev](https://github.com/tmishinev) [Sep 13, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10637080)\
\
is that valid when passing a PyDantic Schema to the [@tool](https://github.com/tool)(args\_schema = )\
\
still prompts me for the state as a missing arg\
\
2\
\
👍3\
\
8 replies\
\
Show 3 previous replies\
\
[![@Stihotvor](https://avatars.githubusercontent.com/u/22343775?u=98a2af5279c0b8debedf1682b81a425a59bb8c84&v=4)](https://github.com/Stihotvor)\
\
[Stihotvor](https://github.com/Stihotvor) [Sep 27, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10776993)\
\
[@haroldsnyers](https://github.com/haroldsnyers) But if You enable the docstring parser, doesn't it disable the pydantic validation? I need pydantic to validate the input....\
\
[![@fletchertyler914](https://avatars.githubusercontent.com/u/3344498?u=be6f2ff193f913fb9b7ad2c9c1c98b6f8eaf93f4&v=4)](https://github.com/fletchertyler914)\
\
[fletchertyler914](https://github.com/fletchertyler914) [Sep 27, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10777467)\
\
I just hit this same issue. I am needing a tool which passes config and state with no arguments. Passing config alone works fine, but as soon as I add state via `state: Annotated[dict, InjectedState]` I get a pydantic error:\
\
```notranslate\
ValidationError: 1 validation error for guest_sample_tool\
state\
  Field required [type=missing, input_value={}, input_type=dict]\
    For further information visit https://errors.pydantic.dev/2.9/v/missing\
\
```\
\
I did try to use the docstring but it doesnt help:\
\
```notranslate\
@tool(parse_docstring=True, response_format="content_and_artifact")\
def guest_sample_tool(\
    configs: RunnableConfig,\
    state: Annotated[dict, InjectedState]\
):\
    """\
    Call this tool to get a guest sample.\
\
    Args: None\
    """\
\
```\
\
[![@phfifofum](https://avatars.githubusercontent.com/u/178105107?v=4)](https://github.com/phfifofum)\
\
[phfifofum](https://github.com/phfifofum) [Nov 14, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-11254326)\
\
I have the same issue today, had to ditch structured tool... anyone got a fix or workaround?\
\
[![@haroldsnyers](https://avatars.githubusercontent.com/u/36260910?u=a81395f05f19f42347db00a5d7d109d185b76731&v=4)](https://github.com/haroldsnyers)\
\
[haroldsnyers](https://github.com/haroldsnyers) [Dec 11, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-11531461)\
\
edited\
\
> [@haroldsnyers](https://github.com/haroldsnyers) But if You enable the docstring parser, doesn't it disable the pydantic validation? I need pydantic to validate the input....\
\
[@Stihotvor](https://github.com/Stihotvor) Yeah I guess it does disable it, have you been able to use pydantic to get the state ?\
\
[![@SaujanyaV](https://avatars.githubusercontent.com/u/69972397?u=6fd625178b62cba03bfca06314059695e2a74046&v=4)](https://github.com/SaujanyaV)\
\
[SaujanyaV](https://github.com/SaujanyaV) [Dec 15, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-11572732)\
\
> I just hit this same issue. I am needing a tool which passes config and state with no arguments. Passing config alone works fine, but as soon as I add state via `state: Annotated[dict, InjectedState]` I get a pydantic error:\
>\
> ```notranslate\
> ValidationError: 1 validation error for guest_sample_tool\
> state\
>   Field required [type=missing, input_value={}, input_type=dict]\
>     For further information visit https://errors.pydantic.dev/2.9/v/missing\
>\
> ```\
\
Were you able to find a fix? I'm stuck with the same error.\
\
[![@rbaks](https://avatars.githubusercontent.com/u/67518685?u=0453280493c1c1f0d3bfecd697c27775ed42a1f6&v=4)rbaks](https://github.com/rbaks) [Oct 1, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-10810140)\
\
edited\
\
Using v0.2.4, I implemented a custom tool node like the one in the [documentation](https://langchain-ai.github.io/langgraph/how-tos/tool-calling-errors/).\
\
```\
def  call_tool(state: State):\
	tools_by_name = {...}\
	messages = state["messages"]\
	last_message = messages[-1]\
	output_messages = []\
	tool_results = {}\
	for  tool_call  in  last_message.tool_calls:\
		try:\
			result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])\
			output_messages.append(\
				ToolMessage(\
					content=json.dumps(result),\
					name=tool_call["name"],\
					tool_call_id=tool_call["id"],\
				)\
			)\
			tool_results.update(result)\
		except  Exception  as  e:\
			output_messages.append(\
				ToolMessage(\
					content="",\
					name=tool_call["name"],\
					tool_call_id=tool_call["id"],\
					additional_kwargs={"error": str(e)},\
				)\
			)\
\
	return {\
	    "messages": output_messages,\
	    **tool_results, # A way to update the state with the tool results\
	}\
```\
\
And then when I need to inject state into a tool:\
\
```\
@tool\
def  generate_chart(request: str, state: Annotated[dict, InjectedState]):\
	...\
```\
\
It outputs the error\
\
```\
{\
  "error": "1 validation error for generate_chartSchema\nstate\n  field required (type=value_error.missing)"\
}\
```\
\
I suspect it is caused by my custom tool node implementation. is there a way to solve this issue?\
\
2\
\
3 replies\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Nov 14, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-11256429)\
\
Collaborator\
\
yea you would need to add support for that in your tool-calling node -- see the implementation here [https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/prebuilt/tool\_node.py#L383](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/prebuilt/tool_node.py#L383)\
\
[![@rafael-siqueira-akad](https://avatars.githubusercontent.com/u/162999524?v=4)](https://github.com/rafael-siqueira-akad)\
\
[rafael-siqueira-akad](https://github.com/rafael-siqueira-akad) [Dec 9, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-11512713)\
\
Can you elaborate and how this can be easily done? I would believe that custom tool node implementations are fairly common among users. Thanks!\
\
[![@haroldsnyers](https://avatars.githubusercontent.com/u/36260910?u=a81395f05f19f42347db00a5d7d109d185b76731&v=4)](https://github.com/haroldsnyers)\
\
[haroldsnyers](https://github.com/haroldsnyers) [Dec 11, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-11531457)\
\
edited\
\
You can also simply add the content/response of other tools/generations in your state, and then as [@rbaks](https://github.com/rbaks) mentioned, use the [@tool](https://github.com/tool) to get your state. Here is an example tool definition\
\
```\
"""Code generation tool."""\
\
import logging\
\
from typing_extensions import Annotated\
\
from langgraph.prebuilt import InjectedState\
\
from genai.agents.mini_agents.tools.code.plotter.python_plot_prompt import (\
    prompt_template,\
)\
from genai.agents.mini_agents.tools.code.coder import cached_get_chain\
from langchain_core.tools import tool\
\
rag_chain = cached_get_chain(prompt_template)\
\
@tool(parse_docstring=True, response_format="content")\
def code_chart_tool(chart_message: str, state: Annotated[dict, InjectedState]):\
    """\
    Generate the python code related to plotting.\
      Can write code.\
      Input should be a code question related to plotting.\
      Output is the plotly code to generate a graph that answers the question.\
\
    Args:\
        chart_message: The question or message that describes the chart to be generated.\
\
    """\
    logging.info("FUNCTION get_coder_chart_tool")\
    if state.get("data"):\
        llm_response = rag_chain.invoke(\
            input={\
                "question": chart_message,\
                "data": state.get("data"),\
            },\
        )\
\
        return llm_response["output"]\
    else:\
        return "Error: Data is missing"\
```\
\
[![@kivy0](https://avatars.githubusercontent.com/u/132319545?v=4)kivy0](https://github.com/kivy0) [Oct 24, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-11039798)\
\
I'm trying to do the same thing with create\_tool\_calling\_agent. Nothing works, maybe someone knows if it is possible to achieve similar behavior. The state would be first passed from the graph to the agent and then to the tools.\
\
3\
\
0 replies\
\
[![@MrAlekhin](https://avatars.githubusercontent.com/u/24749983?u=c3f3739bd462f276b0c700777044d8beb2dce6db&v=4)MrAlekhin](https://github.com/MrAlekhin) [Nov 12, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-11229458)\
\
Is there a straightforward way to modify InjectedState inside the tool? or its only for reading the state?\
\
What's is suggested way to modify the state right from the [@tool](https://github.com/tool)?\
\
1\
\
2 replies\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Nov 14, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-11256398)\
\
Collaborator\
\
`InjectedState` is only for reading the state, we're working on adding support to modify state from tools as well, stay tuned\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Nov 14, 2024](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-11256415)\
\
Collaborator\
\
For now the suggested way would be to\
\
- return the outputs with desired state update from the tool (potentially via a tool artifact)\
- create a custom implementation for the tool-calling node that can take those artifacts and produce the final state update that includes the updates from the tool(s)\
\
👍1\
\
[![@alex-kowalczyk](https://avatars.githubusercontent.com/u/7422175?u=5ab01fb6c638ae1c1d3e438fa6ca7137ede28ada&v=4)alex-kowalczyk](https://github.com/alex-kowalczyk) [Feb 1](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-12027105)\
\
Is there a bug in the examples?\
\
`tool_node = ToolNode(tools)` is defined but never used in `create_react_agent` calls.\
\
1\
\
0 replies\
\
[![@JeffBasso](https://avatars.githubusercontent.com/u/197317618?v=4)JeffBasso](https://github.com/JeffBasso) [Feb 12](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-12177541)\
\
_This comment was deleted._\
\
1\
\
1 reply\
\
[![@JeffBasso](https://avatars.githubusercontent.com/u/197317618?v=4)](https://github.com/JeffBasso)\
\
[JeffBasso](https://github.com/JeffBasso) [Feb 12](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-12177585)\
\
I found the place to correct, never mind\
\
[![@Denis-root](https://avatars.githubusercontent.com/u/64244017?v=4)Denis-root](https://github.com/Denis-root) [3 days ago](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-12902373)\
\
But this only works with the pre-built agent create\_react\_agent.\
\
I have a basic React agent schema created with nodes only and using ToolNode, but I can't inject anything from the State class.\
\
class State(MessagesState):\
\
results: list\
\
def hacer\_post\_json(url: str, data: dict, config: RunnableConfig, res: Annotated\[list, InjectedState("resultados")\]) -> dict:\
\
I get an error that the results key doesn't exist...\
\
And if I use\
\
state: Annotated\[dict, InjectedState\]\
\
I only get the messages key.\
\
1\
\
1 reply\
\
[![@Denis-root](https://avatars.githubusercontent.com/u/64244017?v=4)](https://github.com/Denis-root)\
\
[Denis-root](https://github.com/Denis-root) [3 days ago](https://github.com/langchain-ai/langgraph/discussions/681#discussioncomment-12902635)\
\
After reading repeatedly and consulting gpt \[xd\], I think I found an answer. I don't know if it's the official one.\
\
According to the errors when running, it said that the "resultados" key was required but wasn't being passed as an argument.\
\
So I entered it manually in the invoke, and eurekaaa, I was able to intercept it within the method.\
\
for chunk in app.stream(\
\
{"messages": \[("human", x)\], "resultados": \[\]}, config, stream\_mode="values"\
\
):\
\
chunk\["messages"\]\[-1\].pretty\_print()\
\
I just don't understand why you can't set a default value when declaring the class. I tried, but it never worked.\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fpass-run-time-values-to-tools%2F)