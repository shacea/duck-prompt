[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/run-id-langsmith/#how-to-pass-custom-run-id-or-set-tags-and-metadata-for-graph-runs-in-langsmith)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/run-id-langsmith.ipynb "Edit this page")

# How to pass custom run ID or set tags and metadata for graph runs in LangSmith [¶](https://langchain-ai.github.io/langgraph/how-tos/run-id-langsmith/\#how-to-pass-custom-run-id-or-set-tags-and-metadata-for-graph-runs-in-langsmith "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Platform](https://smith.langchain.com/)
- [RunnableConfig](https://api.python.langchain.com/en/latest/runnables/langchain_core.runnables.config.RunnableConfig.html#langchain_core.runnables.config.RunnableConfig)
- [Add metadata and tags to traces](https://docs.smith.langchain.com/how_to_guides/tracing/trace_with_langchain#add-metadata-and-tags-to-traces)
- [Customize run name](https://docs.smith.langchain.com/how_to_guides/tracing/trace_with_langchain#customize-run-name)

Debugging graph runs can sometimes be difficult to do in an IDE or terminal. [LangSmith](https://docs.smith.langchain.com/) lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read the [LangSmith documentation](https://docs.smith.langchain.com/) for more information on how to get started.

To make it easier to identify and analyzed traces generated during graph invocation, you can set additional configuration at run time (see [RunnableConfig](https://api.python.langchain.com/en/latest/runnables/langchain_core.runnables.config.RunnableConfig.html#langchain_core.runnables.config.RunnableConfig)):

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| run\_name | `str` | Name for the tracer run for this call. Defaults to the name of the class. |
| run\_id | `UUID` | Unique identifier for the tracer run for this call. If not provided, a new UUID will be generated. |
| tags | `List[str]` | Tags for this call and any sub-calls (e.g., a Chain calling an LLM). You can use these to filter calls. |
| metadata | `Dict[str, Any]` | Metadata for this call and any sub-calls (e.g., a Chain calling an LLM). Keys should be strings, values should be JSON-serializable. |

LangGraph graphs implement the [LangChain Runnable Interface](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.Runnable.html) and accept a second argument ( `RunnableConfig`) in methods like `invoke`, `ainvoke`, `stream` etc.

The LangSmith platform will allow you to search and filter traces based on `run_name`, `run_id`, `tags` and `metadata`.

## TLDR [¶](https://langchain-ai.github.io/langgraph/how-tos/run-id-langsmith/\#tldr "Permanent link")

```md-code__content
import uuid
# Generate a random UUID -- it must be a UUID
config = {"run_id": uuid.uuid4()}, "tags": ["my_tag1"], "metadata": {"a": 5}}
# Works with all standard Runnable methods
# like invoke, batch, ainvoke, astream_events etc
graph.stream(inputs, config, stream_mode="values")

```

The rest of the how to guide will show a full agent.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/run-id-langsmith/\#setup "Permanent link")

First, let's install the required packages and set our API keys

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
_set_env("LANGSMITH_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Define the graph [¶](https://langchain-ai.github.io/langgraph/how-tos/run-id-langsmith/\#define-the-graph "Permanent link")

For this example we will use the [prebuilt ReAct agent](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/).

API Reference: [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html)

```md-code__content
from langchain_openai import ChatOpenAI
from typing import Literal
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

# First we initialize the model we want to use.
model = ChatOpenAI(model="gpt-4o", temperature=0)

# For this tutorial we will use custom tool that returns pre-defined values for weather in two cities (NYC & SF)
@tool
def get_weather(city: Literal["nyc", "sf"]):
    """Use this to get weather information."""
    if city == "nyc":
        return "It might be cloudy in nyc"
    elif city == "sf":
        return "It's always sunny in sf"
    else:
        raise AssertionError("Unknown city")

tools = [get_weather]

# Define the graph
graph = create_react_agent(model, tools=tools)

```

## Run your graph [¶](https://langchain-ai.github.io/langgraph/how-tos/run-id-langsmith/\#run-your-graph "Permanent link")

Now that we've defined our graph let's run it once and view the trace in LangSmith. In order for our trace to be easily accessible in LangSmith, we will pass in a custom `run_id` in the config.

This assumes that you have set your `LANGSMITH_API_KEY` environment variable.

Note that you can also configure what project to trace to by setting the `LANGCHAIN_PROJECT` environment variable, by default runs will be traced to the `default` project.

```md-code__content
import uuid

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

inputs = {"messages": [("user", "what is the weather in sf")]}

config = {"run_name": "agent_007", "tags": ["cats are awesome"]}

print_stream(graph.stream(inputs, config, stream_mode="values"))

```

```md-code__content
================================[1m Human Message [0m=================================\
\
what is the weather in sf\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  get_weather (call_9ZudXyMAdlUjptq9oMGtQo8o)\
 Call ID: call_9ZudXyMAdlUjptq9oMGtQo8o\
  Args:\
    city: sf\
=================================[1m Tool Message [0m=================================\
Name: get_weather\
\
It's always sunny in sf\
==================================[1m Ai Message [0m==================================\
\
The weather in San Francisco is currently sunny.\
\
```\
\
## View the trace in LangSmith [¶](https://langchain-ai.github.io/langgraph/how-tos/run-id-langsmith/\#view-the-trace-in-langsmith "Permanent link")\
\
Now that we've ran our graph, let's head over to LangSmith and view our trace. First click into the project that you traced to (in our case the default project). You should see a run with the custom run name "agent\_007".\
\
![image.png](<Base64-Image-Removed>)\
\
In addition, you will be able to filter traces after the fact using the tags or metadata provided. For example,\
\
![image.png](<Base64-Image-Removed>)\
\
## Comments\
\
giscus\
\
#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/2171)\
\
👍1\
\
#### [0 comments](https://github.com/langchain-ai/langgraph/discussions/2171)\
\
_– powered by [giscus](https://giscus.app/)_\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Frun-id-langsmith%2F)