[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/configuration/#how-to-add-runtime-configuration-to-your-graph)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/configuration.ipynb "Edit this page")

# How to add runtime configuration to your graph [¶](https://langchain-ai.github.io/langgraph/how-tos/configuration/\#how-to-add-runtime-configuration-to-your-graph "Permanent link")

Sometimes you want to be able to configure your agent when calling it.
Examples of this include configuring which LLM to use.
Below we walk through an example of doing so.

Prerequisites

This guide assumes familiarity with the following:


- [LangGraph State](https://langchain-ai.github.io/langgraph/concepts/low_level/#state)
- [Chat Models](https://python.langchain.com/docs/concepts/#chat-models/)

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/configuration/\#setup "Permanent link")

First, let's install the required packages and set our API keys

```md-code__content
%%capture --no-stderr
%pip install -U langgraph langchain_anthropic

```

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("ANTHROPIC_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Define graph [¶](https://langchain-ai.github.io/langgraph/how-tos/configuration/\#define-graph "Permanent link")

First, let's create a very simple graph

API Reference: [ChatAnthropic](https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html) \| [BaseMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.base.BaseMessage.html) \| [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START)

```md-code__content
import operator
from typing import Annotated, Sequence
from typing_extensions import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage

from langgraph.graph import END, StateGraph, START

model = ChatAnthropic(model_name="claude-2.1")

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

def _call_model(state):
    state["messages"]
    response = model.invoke(state["messages"])
    return {"messages": [response]}

# Define a new graph
builder = StateGraph(AgentState)
builder.add_node("model", _call_model)
builder.add_edge(START, "model")
builder.add_edge("model", END)

graph = builder.compile()

```

## Configure the graph [¶](https://langchain-ai.github.io/langgraph/how-tos/configuration/\#configure-the-graph "Permanent link")

Great! Now let's suppose that we want to extend this example so the user is able to choose from multiple llms.
We can easily do that by passing in a config. Any configuration information needs to be passed inside `configurable` key as shown below.
This config is meant to contain things are not part of the input (and therefore that we don't want to track as part of the state).

API Reference: [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [RunnableConfig](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.config.RunnableConfig.html)

```md-code__content
from langchain_openai import ChatOpenAI
from typing import Optional
from langchain_core.runnables.config import RunnableConfig

openai_model = ChatOpenAI()

models = {
    "anthropic": model,
    "openai": openai_model,
}

def _call_model(state: AgentState, config: RunnableConfig):
    # Access the config through the configurable key
    model_name = config["configurable"].get("model", "anthropic")
    model = models[model_name]
    response = model.invoke(state["messages"])
    return {"messages": [response]}

# Define a new graph
builder = StateGraph(AgentState)
builder.add_node("model", _call_model)
builder.add_edge(START, "model")
builder.add_edge("model", END)

graph = builder.compile()

```

If we call it with no configuration, it will use the default as we defined it (Anthropic).

```md-code__content
graph.invoke({"messages": [HumanMessage(content="hi")]})

```

```md-code__content
{'messages': [HumanMessage(content='hi', additional_kwargs={}, response_metadata={}),\
  AIMessage(content='Hello!', additional_kwargs={}, response_metadata={'id': 'msg_01WFXkfgK8AvSckLvYYrHshi', 'model': 'claude-2.1', 'stop_reason': 'end_turn', 'stop_sequence': None, 'usage': {'input_tokens': 10, 'output_tokens': 6}}, id='run-ece54b16-f8fc-4201-8405-b97122edf8d8-0', usage_metadata={'input_tokens': 10, 'output_tokens': 6, 'total_tokens': 16})]}

```

We can also call it with a config to get it to use a different model.

```md-code__content
config = {"configurable": {"model": "openai"}}
graph.invoke({"messages": [HumanMessage(content="hi")]}, config=config)

```

```md-code__content
{'messages': [HumanMessage(content='hi', additional_kwargs={}, response_metadata={}),\
  AIMessage(content='Hello! How can I assist you today?', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 9, 'prompt_tokens': 8, 'total_tokens': 17, 'completion_tokens_details': {'reasoning_tokens': 0}}, 'model_name': 'gpt-3.5-turbo-0125', 'system_fingerprint': None, 'finish_reason': 'stop', 'logprobs': None}, id='run-f8331964-d811-4b44-afb8-56c30ade7c15-0', usage_metadata={'input_tokens': 8, 'output_tokens': 9, 'total_tokens': 17})]}

```

We can also adapt our graph to take in more configuration! Like a system message for example.

API Reference: [SystemMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.system.SystemMessage.html)

```md-code__content
from langchain_core.messages import SystemMessage

# We can define a config schema to specify the configuration options for the graph
# A config schema is useful for indicating which fields are available in the configurable dict inside the config
class ConfigSchema(TypedDict):
    model: Optional[str]
    system_message: Optional[str]

def _call_model(state: AgentState, config: RunnableConfig):
    # Access the config through the configurable key
    model_name = config["configurable"].get("model", "anthropic")
    model = models[model_name]
    messages = state["messages"]
    if "system_message" in config["configurable"]:
        messages = [\
            SystemMessage(content=config["configurable"]["system_message"])\
        ] + messages
    response = model.invoke(messages)
    return {"messages": [response]}

# Define a new graph - note that we pass in the configuration schema here, but it is not necessary
workflow = StateGraph(AgentState, ConfigSchema)
workflow.add_node("model", _call_model)
workflow.add_edge(START, "model")
workflow.add_edge("model", END)

graph = workflow.compile()

```

```md-code__content
graph.invoke({"messages": [HumanMessage(content="hi")]})

```

```md-code__content
{'messages': [HumanMessage(content='hi', additional_kwargs={}, response_metadata={}),\
  AIMessage(content='Hello!', additional_kwargs={}, response_metadata={'id': 'msg_01VgCANVHr14PsHJSXyKkLVh', 'model': 'claude-2.1', 'stop_reason': 'end_turn', 'stop_sequence': None, 'usage': {'input_tokens': 10, 'output_tokens': 6}}, id='run-f8c5f18c-be58-4e44-9a4e-d43692d7eed1-0', usage_metadata={'input_tokens': 10, 'output_tokens': 6, 'total_tokens': 16})]}

```

```md-code__content
config = {"configurable": {"system_message": "respond in italian"}}
graph.invoke({"messages": [HumanMessage(content="hi")]}, config=config)

```

```md-code__content
{'messages': [HumanMessage(content='hi', additional_kwargs={}, response_metadata={}),\
  AIMessage(content='Ciao!', additional_kwargs={}, response_metadata={'id': 'msg_011YuCYQk1Rzc8PEhVCpQGr6', 'model': 'claude-2.1', 'stop_reason': 'end_turn', 'stop_sequence': None, 'usage': {'input_tokens': 14, 'output_tokens': 7}}, id='run-a583341e-5868-4e8c-a536-881338f21252-0', usage_metadata={'input_tokens': 14, 'output_tokens': 7, 'total_tokens': 21})]}

```

## Comments

giscus

#### [5 reactions](https://github.com/langchain-ai/langgraph/discussions/702)

👍3❤️2

#### [4 comments](https://github.com/langchain-ai/langgraph/discussions/702)

#### ·

#### 4 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@mehdihosseinimoghadam](https://avatars.githubusercontent.com/u/53477752?u=9e37e04c6af96e7a068b6112d798f6770ca8f861&v=4)mehdihosseinimoghadam](https://github.com/mehdihosseinimoghadam) [Jun 19, 2024](https://github.com/langchain-ai/langgraph/discussions/702#discussioncomment-9816438)

Hi here is my code and I am trying to pass both 'thread\_id' and 'recursion\_limit', but it terminates the conversation after 25 rounds, why is this happening? Thanks

config = {"configurable": {"thread\_id": "2", "recursion\_limit": "100"}}

for event in simulation.stream(\[\], config):

print(event)

1

2 replies

[![@mehdihosseinimoghadam](https://avatars.githubusercontent.com/u/53477752?u=9e37e04c6af96e7a068b6112d798f6770ca8f861&v=4)](https://github.com/mehdihosseinimoghadam)

[mehdihosseinimoghadam](https://github.com/mehdihosseinimoghadam) [Jun 19, 2024](https://github.com/langchain-ai/langgraph/discussions/702#discussioncomment-9816494)

Error Message

GraphRecursionError: Recursion limit of 25 reachedwithout hitting a stop condition. You can increase the limit by setting the `recursion_limit` config key.

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Jun 21, 2024](https://github.com/langchain-ai/langgraph/discussions/702#discussioncomment-9835573)

Contributor

Hello! `recursion_limit` goes at the top level of the config. See the reference doc: [RunnableConfig](https://api.python.langchain.com/en/latest/runnables/langchain_core.runnables.config.RunnableConfig.html#langchain_core.runnables.config.RunnableConfig), linked from [CompiledGraph.invoke](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.graph.CompiledGraph.invoke).

👍2

[![@TomTom101](https://avatars.githubusercontent.com/u/872712?u=c6e76fb451e3a0c1528a8d0e95ef3ed669483690&v=4)TomTom101](https://github.com/TomTom101) [Jun 20, 2024](https://github.com/langchain-ai/langgraph/discussions/702#discussioncomment-9832993)

Keep them guides coming, very useful!

1

👍1❤️3

0 replies

[![@804701332](https://avatars.githubusercontent.com/u/18359123?v=4)804701332](https://github.com/804701332) [Jul 6, 2024](https://github.com/langchain-ai/langgraph/discussions/702#discussioncomment-9975736)

How to use configuration in an asynchronous environment？

2

2 replies

[![@TomTom101](https://avatars.githubusercontent.com/u/872712?u=c6e76fb451e3a0c1528a8d0e95ef3ed669483690&v=4)](https://github.com/TomTom101)

[TomTom101](https://github.com/TomTom101) [Jul 6, 2024](https://github.com/langchain-ai/langgraph/discussions/702#discussioncomment-9975859)

```
async for event in graph.astream_events(
        {"messages": [HumanMessage(content="Say hi")]},
        config={"configurable": {"thread_id": 123}},
        version="v1",
    ):
     ...
```

[![@804701332](https://avatars.githubusercontent.com/u/18359123?v=4)](https://github.com/804701332)

[804701332](https://github.com/804701332) [Jul 7, 2024](https://github.com/langchain-ai/langgraph/discussions/702#discussioncomment-9977233)

My statement was not complete. Actually, I wanted to ask how to use the ensure\_config() method in an asynchronous environment, similar to the Customer Support case:

config = ensure\_config() # Fetch from the context

configuration = config.get("configurable", {})

passenger\_id = configuration.get("passenger\_id", None)

if not passenger\_id:

raise ValueError("No passenger ID configured.")

[![@hariprasad-sobeys](https://avatars.githubusercontent.com/u/183298644?v=4)hariprasad-sobeys](https://github.com/hariprasad-sobeys) [Oct 17, 2024](https://github.com/langchain-ai/langgraph/discussions/702#discussioncomment-10975782)

How to pass config to as input when we deploy langgraph code as model in MLFlow?

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fconfiguration%2F)