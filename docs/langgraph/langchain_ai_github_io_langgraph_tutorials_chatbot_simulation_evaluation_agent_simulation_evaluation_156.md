[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation/?q=#chat-bot-evaluation-as-multi-agent-simulation)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation.ipynb "Edit this page")

# Chat Bot Evaluation as Multi-agent Simulation [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation/?q=\#chat-bot-evaluation-as-multi-agent-simulation "Permanent link")

When building a chat bot, such as a customer support assistant, it can be hard to properly evaluate your bot's performance. It's time-consuming to have to manually interact with it intensively for each code change.

One way to make the evaluation process easier and more reproducible is to simulate a user interaction.

With LangGraph, it's easy to set this up. Below is an example of how to create a "virtual user" to simulate a conversation.

The overall simulation looks something like this:

![diagram](<Base64-Image-Removed>)

## Setup [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation/?q=\#setup "Permanent link")

First, let's install the required packages and set our API keys

```md-code__content
%%capture --no-stderr
%pip install -U langgraph langchain langchain_openai

```

```md-code__content
import getpass
import os

def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

_set_if_undefined("OPENAI_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Define Chat Bot [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation/?q=\#define-chat-bot "Permanent link")

Next, we will define our chat bot. For this notebook, we assume the bot's API accepts a list of messages and responds with a message. If you want to update this, all you'll have to change is this section and the "get\_messages\_for\_agent" function in
the simulator below.

The implementation within `my_chat_bot` is configurable and can even be run on another system (e.g., if your system isn't running in python).

```md-code__content
from typing import List

import openai

# This is flexible, but you can define your agent here, or call your agent API here.
def my_chat_bot(messages: List[dict]) -> dict:
    system_message = {
        "role": "system",
        "content": "You are a customer support agent for an airline.",
    }
    messages = [system_message] + messages
    completion = openai.chat.completions.create(
        messages=messages, model="gpt-3.5-turbo"
    )
    return completion.choices[0].message.model_dump()

```

```md-code__content
my_chat_bot([{"role": "user", "content": "hi!"}])

```

```md-code__content
{'content': 'Hello! How can I assist you today?',
 'role': 'assistant',
 'function_call': None,
 'tool_calls': None}

```

## Define Simulated User [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation/?q=\#define-simulated-user "Permanent link")

We're now going to define the simulated user.
This can be anything we want, but we're going to build it as a LangChain bot.

API Reference: [ChatPromptTemplate](https://python.langchain.com/api_reference/core/prompts/langchain_core.prompts.chat.ChatPromptTemplate.html) \| [MessagesPlaceholder](https://python.langchain.com/api_reference/core/prompts/langchain_core.prompts.chat.MessagesPlaceholder.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html)

```md-code__content
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

system_prompt_template = """You are a customer of an airline company. \
You are interacting with a user who is a customer support person. \

{instructions}

When you are finished with the conversation, respond with a single word 'FINISHED'"""

prompt = ChatPromptTemplate.from_messages(
    [\
        ("system", system_prompt_template),\
        MessagesPlaceholder(variable_name="messages"),\
    ]
)
instructions = """Your name is Harrison. You are trying to get a refund for the trip you took to Alaska. \
You want them to give you ALL the money back. \
This trip happened 5 years ago."""

prompt = prompt.partial(name="Harrison", instructions=instructions)

model = ChatOpenAI()

simulated_user = prompt | model

```

API Reference: [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html)

```md-code__content
from langchain_core.messages import HumanMessage

messages = [HumanMessage(content="Hi! How can I help you?")]
simulated_user.invoke({"messages": messages})

```

```md-code__content
AIMessage(content='Hi, I would like to request a refund for a trip I took with your airline company to Alaska. Is it possible to get a refund for that trip?')

```

## Define the Agent Simulation [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation/?q=\#define-the-agent-simulation "Permanent link")

The code below creates a LangGraph workflow to run the simulation. The main components are:

1. The two nodes: one for the simulated user, the other for the chat bot.
2. The graph itself, with a conditional stopping criterion.

Read the comments in the code below for more information.

### Define nodes [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation/?q=\#define-nodes "Permanent link")

First, we define the nodes in the graph. These should take in a list of messages and return a list of messages to ADD to the state.
These will be thing wrappers around the chat bot and simulated user we have above.

**Note:** one tricky thing here is which messages are which. Because both the chat bot AND our simulated user are both LLMs, both of them will resond with AI messages. Our state will be a list of alternating Human and AI messages. This means that for one of the nodes, there will need to be some logic that flips the AI and human roles. In this example, we will assume that HumanMessages are messages from the simulated user. This means that we need some logic in the simulated user node to swap AI and Human messages.

First, let's define the chat bot node

API Reference: [convert\_message\_to\_dict](https://python.langchain.com/api_reference/community/adapters/langchain_community.adapters.openai.convert_message_to_dict.html) \| [AIMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html)

```md-code__content
from langchain_community.adapters.openai import convert_message_to_dict
from langchain_core.messages import AIMessage

def chat_bot_node(state):
    messages = state["messages"]
    # Convert from LangChain format to the OpenAI format, which our chatbot function expects.
    messages = [convert_message_to_dict(m) for m in messages]
    # Call the chat bot
    chat_bot_response = my_chat_bot(messages)
    # Respond with an AI Message
    return {"messages": [AIMessage(content=chat_bot_response["content"])]}

```

Next, let's define the node for our simulated user. This will involve a little logic to swap the roles of the messages.

```md-code__content
def _swap_roles(messages):
    new_messages = []
    for m in messages:
        if isinstance(m, AIMessage):
            new_messages.append(HumanMessage(content=m.content))
        else:
            new_messages.append(AIMessage(content=m.content))
    return new_messages

def simulated_user_node(state):
    messages = state["messages"]
    # Swap roles of messages
    new_messages = _swap_roles(messages)
    # Call the simulated user
    response = simulated_user.invoke({"messages": new_messages})
    # This response is an AI message - we need to flip this to be a human message
    return {"messages": [HumanMessage(content=response.content)]}

```

### Define edges [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation/?q=\#define-edges "Permanent link")

We now need to define the logic for the edges. The main logic occurs after the simulated user goes, and it should lead to one of two outcomes:

- Either we continue and call the customer support bot
- Or we finish and the conversation is over

So what is the logic for the conversation being over? We will define that as either the Human chatbot responds with `FINISHED` (see the system prompt) OR the conversation is more than 6 messages long (this is an arbitrary number just to keep this example short).

```md-code__content
def should_continue(state):
    messages = state["messages"]
    if len(messages) > 6:
        return "end"
    elif messages[-1].content == "FINISHED":
        return "end"
    else:
        return "continue"

```

### Define graph [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation/?q=\#define-graph "Permanent link")

We can now define the graph that sets up the simulation!

API Reference: [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [add\_messages](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.message.add_messages)

```md-code__content
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)
graph_builder.add_node("user", simulated_user_node)
graph_builder.add_node("chat_bot", chat_bot_node)
# Every response from  your chat bot will automatically go to the
# simulated user
graph_builder.add_edge("chat_bot", "user")
graph_builder.add_conditional_edges(
    "user",
    should_continue,
    # If the finish criteria are met, we will stop the simulation,
    # otherwise, the virtual user's message will be sent to your chat bot
    {
        "end": END,
        "continue": "chat_bot",
    },
)
# The input will first go to your chat bot
graph_builder.add_edge(START, "chat_bot")
simulation = graph_builder.compile()

```

## Run Simulation [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation/?q=\#run-simulation "Permanent link")

Now we can evaluate our chat bot! We can invoke it with empty messages (this will simulate letting the chat bot start the initial conversation)

```md-code__content
for chunk in simulation.stream({"messages": []}):
    # Print out all events aside from the final end chunk
    if END not in chunk:
        print(chunk)
        print("----")

```

```md-code__content
{'chat_bot': AIMessage(content='How may I assist you today regarding your flight or any other concerns?')}
----
{'user': HumanMessage(content='Hi, my name is Harrison. I am reaching out to request a refund for a trip I took to Alaska with your airline company. The trip occurred about 5 years ago. I would like to receive a refund for the entire amount I paid for the trip. Can you please assist me with this?')}
----
{'chat_bot': AIMessage(content="Hello, Harrison. Thank you for reaching out to us. I understand you would like to request a refund for a trip you took to Alaska five years ago. I'm afraid that our refund policy typically has a specific timeframe within which refund requests must be made. Generally, refund requests need to be submitted within 24 to 48 hours after the booking is made, or in certain cases, within a specified cancellation period.\n\nHowever, I will do my best to assist you. Could you please provide me with some additional information? Can you recall any specific details about the booking, such as the flight dates, booking reference or confirmation number? This will help me further look into the possibility of processing a refund for you.")}
----
{'user': HumanMessage(content="Hello, thank you for your response. I apologize for not requesting the refund earlier. Unfortunately, I don't have the specific details such as the flight dates, booking reference, or confirmation number at the moment. Is there any other way we can proceed with the refund request without these specific details? I would greatly appreciate your assistance in finding a solution.")}
----
{'chat_bot': AIMessage(content="I understand the situation, Harrison. Without specific details like flight dates, booking reference, or confirmation number, it becomes challenging to locate and process the refund accurately. However, I can still try to help you.\n\nTo proceed further, could you please provide me with any additional information you might remember? This could include the approximate date of travel, the departure and arrival airports, the names of the passengers, or any other relevant details related to the booking. The more information you can provide, the better we can investigate the possibility of processing a refund for you.\n\nAdditionally, do you happen to have any documentation related to your trip, such as receipts, boarding passes, or emails from our airline? These documents could assist in verifying your trip and processing the refund request.\n\nI apologize for any inconvenience caused, and I'll do my best to assist you further based on the information you can provide.")}
----
{'user': HumanMessage(content="I apologize for the inconvenience caused. Unfortunately, I don't have any additional information or documentation related to the trip. It seems that I am unable to provide you with the necessary details to process the refund request. I understand that this may limit your ability to assist me further, but I appreciate your efforts in trying to help. Thank you for your time. \n\nFINISHED")}
----
{'chat_bot': AIMessage(content="I understand, Harrison. I apologize for any inconvenience caused, and I appreciate your understanding. If you happen to locate any additional information or documentation in the future, please don't hesitate to reach out to us again. Our team will be more than happy to assist you with your refund request or any other travel-related inquiries. Thank you for contacting us, and have a great day!")}
----
{'user': HumanMessage(content='FINISHED')}
----

```

## Comments

giscus

#### [2 reactions](https://github.com/langchain-ai/langgraph/discussions/1296)

❤️1🚀1

#### [2 comments](https://github.com/langchain-ai/langgraph/discussions/1296)

#### ·

#### 3 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@neuralninja7](https://avatars.githubusercontent.com/u/177924199?v=4)neuralninja7](https://github.com/neuralninja7) [Aug 9, 2024](https://github.com/langchain-ai/langgraph/discussions/1296#discussioncomment-10288553)

Sorry but how do i get simulation\_utils ?

1

2 replies

[![@hwchase17](https://avatars.githubusercontent.com/u/11986836?u=f4c4f21a82b2af6c9f91e1f1d99ea40062f7a101&v=4)](https://github.com/hwchase17)

[hwchase17](https://github.com/hwchase17) [Aug 9, 2024](https://github.com/langchain-ai/langgraph/discussions/1296#discussioncomment-10288782)

Contributor

good question, they are in here: [https://github.com/langchain-ai/langgraph/tree/main/examples/chatbot-simulation-evaluation](https://github.com/langchain-ai/langgraph/tree/main/examples/chatbot-simulation-evaluation)

👍2

[![@neuralninja7](https://avatars.githubusercontent.com/u/177924199?v=4)](https://github.com/neuralninja7)

[neuralninja7](https://github.com/neuralninja7) [Aug 10, 2024](https://github.com/langchain-ai/langgraph/discussions/1296#discussioncomment-10294973)

cheers Harrison!

[![@achernodub](https://avatars.githubusercontent.com/u/10548179?u=19218b9817e0575edc9e1209eb2d9750b3ec31cf&v=4)achernodub](https://github.com/achernodub) [Mar 25](https://github.com/langchain-ai/langgraph/discussions/1296#discussioncomment-12618666)

When I'm trying to replicate I'm getting this error:

LangSmithAuthError: Authentication failed for /datasets. HTTPError('401 Client Error: Unauthorized for url: [https://api.smith.langchain.com/datasets?limit=1&name=Airline+Red+Teaming](https://api.smith.langchain.com/datasets?limit=1&name=Airline+Red+Teaming)', '{"detail":"Invalid token"}')

1

😕1

1 reply

[![@juanguerralatam](https://avatars.githubusercontent.com/u/18199412?u=551b7187d8c9c68057148df0ecb58a98edce712f&v=4)](https://github.com/juanguerralatam)

[juanguerralatam](https://github.com/juanguerralatam) [20 days ago](https://github.com/langchain-ai/langgraph/discussions/1296#discussioncomment-12725301)

me too

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Fchatbot-simulation-evaluation%2Fagent-simulation-evaluation%2F%3Fq%3D)