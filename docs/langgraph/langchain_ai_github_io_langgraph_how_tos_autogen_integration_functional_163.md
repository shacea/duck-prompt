[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/autogen-integration-functional/?q=#how-to-integrate-langgraph-functional-api-with-autogen-crewai-and-other-frameworks)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/autogen-integration-functional.ipynb "Edit this page")

# How to integrate LangGraph (functional API) with AutoGen, CrewAI, and other frameworks [¶](https://langchain-ai.github.io/langgraph/how-tos/autogen-integration-functional/?q=\#how-to-integrate-langgraph-functional-api-with-autogen-crewai-and-other-frameworks "Permanent link")

LangGraph is a framework for building agentic and multi-agent applications. LangGraph can be easily integrated with other agent frameworks.

The primary reasons you might want to integrate LangGraph with other agent frameworks:

- create [multi-agent systems](https://langchain-ai.github.io/langgraph/concepts/multi_agent) where individual agents are built with different frameworks
- leverage LangGraph to add features like [persistence](https://langchain-ai.github.io/langgraph/concepts/persistence), [streaming](https://langchain-ai.github.io/langgraph/concepts/streaming), [short and long-term memory](https://langchain-ai.github.io/langgraph/concepts/memory) and more

The simplest way to integrate agents from other frameworks is by calling those agents inside a LangGraph [node](https://langchain-ai.github.io/langgraph/concepts/low_level/#nodes):

```md-code__content
import autogen
from langgraph.func import entrypoint, task

autogen_agent = autogen.AssistantAgent(name="assistant", ...)
user_proxy = autogen.UserProxyAgent(name="user_proxy", ...)

@task
def call_autogen_agent(messages):
    response = user_proxy.initiate_chat(
        autogen_agent,
        message=messages[-1],
        ...
    )
    ...

@entrypoint()
def workflow(messages):
    response = call_autogen_agent(messages).result()
    return response

workflow.invoke(
    [\
        {\
            "role": "user",\
            "content": "Find numbers between 10 and 30 in fibonacci sequence",\
        }\
    ]
)

```

In this guide we show how to build a LangGraph chatbot that integrates with AutoGen, but you can follow the same approach with other frameworks.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/autogen-integration-functional/?q=\#setup "Permanent link")

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

```md-code__content
OPENAI_API_KEY:  ········

```

## Define AutoGen agent [¶](https://langchain-ai.github.io/langgraph/how-tos/autogen-integration-functional/?q=\#define-autogen-agent "Permanent link")

Here we define our AutoGen agent. Adapted from official tutorial [here](https://github.com/microsoft/autogen/blob/0.2/notebook/agentchat_web_info.ipynb).

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

* * *

## Create the workflow [¶](https://langchain-ai.github.io/langgraph/how-tos/autogen-integration-functional/?q=\#create-the-workflow "Permanent link")

We will now create a LangGraph chatbot graph that calls AutoGen agent.

API Reference: [convert\_to\_openai\_messages](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.utils.convert_to_openai_messages.html) \| [BaseMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.base.BaseMessage.html) \| [entrypoint](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.entrypoint) \| [task](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.task) \| [add\_messages](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.message.add_messages) \| [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver)

```md-code__content
from langchain_core.messages import convert_to_openai_messages, BaseMessage
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages
from langgraph.checkpoint.memory import MemorySaver

@task
def call_autogen_agent(messages: list[BaseMessage]):
    # convert to openai-style messages
    messages = convert_to_openai_messages(messages)
    response = user_proxy.initiate_chat(
        autogen_agent,
        message=messages[-1],
        # pass previous message history as context
        carryover=messages[:-1],
    )
    # get the final response from the agent
    content = response.chat_history[-1]["content"]
    return {"role": "assistant", "content": content}

# add short-term memory for storing conversation history
checkpointer = MemorySaver()

@entrypoint(checkpointer=checkpointer)
def workflow(messages: list[BaseMessage], previous: list[BaseMessage]):
    messages = add_messages(previous or [], messages)
    response = call_autogen_agent(messages).result()
    return entrypoint.final(value=response, save=add_messages(messages, response))

```

## Run the graph [¶](https://langchain-ai.github.io/langgraph/how-tos/autogen-integration-functional/?q=\#run-the-graph "Permanent link")

We can now run the graph.

```md-code__content
# pass the thread ID to persist agent outputs for future interactions
config = {"configurable": {"thread_id": "1"}}

for chunk in workflow.stream(
    [\
        {\
            "role": "user",\
            "content": "Find numbers between 10 and 30 in fibonacci sequence",\
        }\
    ],
    config,
):
    print(chunk)

```

```md-code__content
[33muser_proxy[0m (to assistant):\
\
Find numbers between 10 and 30 in fibonacci sequence\
\
--------------------------------------------------------------------------------\
[33massistant[0m (to user_proxy):\
\
To find numbers between 10 and 30 in the Fibonacci sequence, we can generate the Fibonacci sequence and check which numbers fall within this range. Here's a plan:\
\
1. Generate Fibonacci numbers starting from 0.\
2. Continue generating until the numbers exceed 30.\
3. Collect and print the numbers that are between 10 and 30.\
\
Let's implement this in Python:\
\
\`\`\`python\
# filename: fibonacci_range.py\
\
def fibonacci_sequence():\
    a, b = 0, 1\
    while a <= 30:\
        if 10 <= a <= 30:\
            print(a)\
        a, b = b, a + b\
\
fibonacci_sequence()\
\`\`\`\
\
This script will print the Fibonacci numbers between 10 and 30. Please execute the code to see the result.\
\
--------------------------------------------------------------------------------\
[31m\
>>>>>>>> EXECUTING CODE BLOCK 0 (inferred language is python)...[0m\
[33muser_proxy[0m (to assistant):\
\
exitcode: 0 (execution succeeded)\
Code output:\
13\
21\
\
--------------------------------------------------------------------------------\
[33massistant[0m (to user_proxy):\
\
The Fibonacci numbers between 10 and 30 are 13 and 21.\
\
These numbers are part of the Fibonacci sequence, which is generated by adding the two preceding numbers to get the next number, starting from 0 and 1.\
\
The sequence goes: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, ...\
\
As you can see, 13 and 21 are the only numbers in this sequence that fall between 10 and 30.\
\
TERMINATE\
\
--------------------------------------------------------------------------------\
{'call_autogen_agent': {'role': 'assistant', 'content': 'The Fibonacci numbers between 10 and 30 are 13 and 21. \n\nThese numbers are part of the Fibonacci sequence, which is generated by adding the two preceding numbers to get the next number, starting from 0 and 1. \n\nThe sequence goes: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, ...\n\nAs you can see, 13 and 21 are the only numbers in this sequence that fall between 10 and 30.\n\nTERMINATE'}}\
{'workflow': {'role': 'assistant', 'content': 'The Fibonacci numbers between 10 and 30 are 13 and 21. \n\nThese numbers are part of the Fibonacci sequence, which is generated by adding the two preceding numbers to get the next number, starting from 0 and 1. \n\nThe sequence goes: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, ...\n\nAs you can see, 13 and 21 are the only numbers in this sequence that fall between 10 and 30.\n\nTERMINATE'}}\
\
```\
\
Since we're leveraging LangGraph's [persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/) features we can now continue the conversation using the same thread ID -- LangGraph will automatically pass previous history to the AutoGen agent:\
\
```md-code__content\
for chunk in workflow.stream(\
    [\
        {\
            "role": "user",\
            "content": "Multiply the last number by 3",\
        }\
    ],\
    config,\
):\
    print(chunk)\
\
```\
\
```md-code__content\
[33muser_proxy[0m (to assistant):\
\
Multiply the last number by 3\
Context:\
Find numbers between 10 and 30 in fibonacci sequence\
The Fibonacci numbers between 10 and 30 are 13 and 21.\
\
These numbers are part of the Fibonacci sequence, which is generated by adding the two preceding numbers to get the next number, starting from 0 and 1.\
\
The sequence goes: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, ...\
\
As you can see, 13 and 21 are the only numbers in this sequence that fall between 10 and 30.\
\
TERMINATE\
\
--------------------------------------------------------------------------------\
[33massistant[0m (to user_proxy):\
\
The last number in the Fibonacci sequence between 10 and 30 is 21. Multiplying 21 by 3 gives:\
\
21 * 3 = 63\
\
TERMINATE\
\
--------------------------------------------------------------------------------\
{'call_autogen_agent': {'role': 'assistant', 'content': 'The last number in the Fibonacci sequence between 10 and 30 is 21. Multiplying 21 by 3 gives:\n\n21 * 3 = 63\n\nTERMINATE'}}\
{'workflow': {'role': 'assistant', 'content': 'The last number in the Fibonacci sequence between 10 and 30 is 21. Multiplying 21 by 3 gives:\n\n21 * 3 = 63\n\nTERMINATE'}}\
\
```\
\
## Comments\
\
giscus\
\
#### 0 reactions\
\
#### 0 comments\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fautogen-integration-functional%2F%3Fq%3D)