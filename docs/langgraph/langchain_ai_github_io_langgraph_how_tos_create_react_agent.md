[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/#how-to-use-the-pre-built-react-agent)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/create-react-agent.ipynb "Edit this page")

# How to use the pre-built ReAct agent [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/\#how-to-use-the-pre-built-react-agent "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [Agent Architectures](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/)
- [Chat Models](https://python.langchain.com/docs/concepts/chat_models/)
- [Tools](https://python.langchain.com/docs/concepts/tools/)

In this how-to we'll create a simple [ReAct](https://arxiv.org/abs/2210.03629) agent app that can check the weather. The app consists of an agent (LLM) and tools. As we interact with the app, we will first call the agent (LLM) to decide if we should use tools. Then we will run a loop:

1. If the agent said to take an action (i.e. call tool), we'll run the tools and pass the results back to the agent
2. If the agent did not ask to run tools, we will finish (respond to the user)

Prebuilt Agent

Please note that here will we use [a prebuilt agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent). One of the big benefits of LangGraph is that you can easily create your own agent architectures. So while it's fine to start here to build an agent quickly, we would strongly recommend learning how to build your own agent so that you can take full advantage of LangGraph.


## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/\#setup "Permanent link")

First let's install the required packages and set our API keys

```md-code__content
%%capture --no-stderr
%pip install -U langgraph langchain-openai

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


## Code [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/\#code "Permanent link")

API Reference: [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

```md-code__content
# First we initialize the model we want to use.
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o", temperature=0)

# For this tutorial we will use custom tool that returns pre-defined values for weather in two cities (NYC & SF)

from typing import Literal

from langchain_core.tools import tool

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

from langgraph.prebuilt import create_react_agent

graph = create_react_agent(model, tools=tools)

```

## Usage [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/\#usage "Permanent link")

First, let's visualize the graph we just created

```md-code__content
from IPython.display import Image, display

display(Image(graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

```md-code__content
def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

```

Let's run the app with an input that needs a tool call

```md-code__content
inputs = {"messages": [("user", "what is the weather in sf")]}
print_stream(graph.stream(inputs, stream_mode="values"))

```

```md-code__content
================================[1m Human Message [0m=================================\
\
what is the weather in sf\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  get_weather (call_zVvnU9DKr6jsNnluFIl59mHb)\
 Call ID: call_zVvnU9DKr6jsNnluFIl59mHb\
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
Now let's try a question that doesn't need tools\
\
```md-code__content\
inputs = {"messages": [("user", "who built you?")]}\
print_stream(graph.stream(inputs, stream_mode="values"))\
\
```\
\
```md-code__content\
================================[1m Human Message [0m=================================\
\
who built you?\
==================================[1m Ai Message [0m==================================\
\
I was created by OpenAI, a research organization focused on developing and advancing artificial intelligence technology.\
\
```\
\
## Comments\
\
giscus\
\
#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/4393)\
\
👍1\
\
#### [0 comments](https://github.com/langchain-ai/langgraph/discussions/4393)\
\
_– powered by [giscus](https://giscus.app/)_\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fcreate-react-agent%2F)