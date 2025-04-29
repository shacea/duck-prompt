[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/autogen-langgraph-platform/#how-to-use-langgraph-platform-to-deploy-crewai-autogen-and-other-frameworks)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/autogen-langgraph-platform.ipynb "Edit this page")

# How to use LangGraph Platform to deploy CrewAI, AutoGen, and other frameworks [¶](https://langchain-ai.github.io/langgraph/how-tos/autogen-langgraph-platform/\#how-to-use-langgraph-platform-to-deploy-crewai-autogen-and-other-frameworks "Permanent link")

[LangGraph Platform](https://langchain-ai.github.io/langgraph/concepts/langgraph_platform/) provides infrastructure for deploying agents. This integrates seamlessly with LangGraph, but can also work with other frameworks. The way to make this work is to wrap the agent in a single LangGraph node, and have that be the entire graph.

Doing so will allow you to deploy to LangGraph Platform, and allows you to get a lot of the [benefits](https://langchain-ai.github.io/langgraph/concepts/langgraph_platform/). You get horizontally scalable infrastructure, a task queue to handle bursty operations, a persistence layer to power short term memory, and long term memory support.

In this guide we show how to do this with an AutoGen agent, but this method should work for agents defined in other frameworks like CrewAI, LlamaIndex, and others as well.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/autogen-langgraph-platform/\#setup "Permanent link")

```md-code__content
%pip install autogen langgraph

```

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")

```

## Define autogen agent [¶](https://langchain-ai.github.io/langgraph/how-tos/autogen-langgraph-platform/\#define-autogen-agent "Permanent link")

Here we define our AutoGen agent. From [https://github.com/microsoft/autogen/blob/0.2/notebook/agentchat\_web\_info.ipynb](https://github.com/microsoft/autogen/blob/0.2/notebook/agentchat_web_info.ipynb)

```md-code__content
import autogen
import os

config_list = [{"model": "gpt-4o", "api_key": os.environ["OPENAI_API_KEY"]}]

llm_config = {
    "timeout": 600,
    "cache_seed": 42,
    "config_list": config_list,
    "temperature": 0,
}

autogen_agent = autogen.AssistantAgent(
    name="assistant",
    llm_config=llm_config,
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "web",
        "use_docker": False,
    },  # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
    llm_config=llm_config,
    system_message="Reply TERMINATE if the task has been solved at full satisfaction. Otherwise, reply CONTINUE, or the reason why the task is not solved yet.",
)

```

## Wrap in LangGraph [¶](https://langchain-ai.github.io/langgraph/how-tos/autogen-langgraph-platform/\#wrap-in-langgraph "Permanent link")

We now wrap the AutoGen agent in a single LangGraph node, and make that the entire graph.
The main thing this involves is defining an Input and Output schema for the node, which you would need to do if deploying this manually, so it's no extra work

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph)

```md-code__content
from langgraph.graph import StateGraph, MessagesState

def call_autogen_agent(state: MessagesState):
    last_message = state["messages"][-1]
    response = user_proxy.initiate_chat(autogen_agent, message=last_message.content)
    # get the final response from the agent
    content = response.chat_history[-1]["content"]
    return {"messages": {"role": "assistant", "content": content}}

graph = StateGraph(MessagesState)
graph.add_node(call_autogen_agent)
graph.set_entry_point("call_autogen_agent")
graph = graph.compile()

```

## Deploy with LangGraph Platform [¶](https://langchain-ai.github.io/langgraph/how-tos/autogen-langgraph-platform/\#deploy-with-langgraph-platform "Permanent link")

You can now deploy this as you normally would with LangGraph Platform. See [these instructions](https://langchain-ai.github.io/langgraph/concepts/deployment_options/) for more details.

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fautogen-langgraph-platform%2F)