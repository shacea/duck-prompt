[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/memory/manage-conversation-history/#how-to-manage-conversation-history)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/memory/manage-conversation-history.ipynb "Edit this page")

# How to manage conversation history [¶](https://langchain-ai.github.io/langgraph/how-tos/memory/manage-conversation-history/\#how-to-manage-conversation-history "Permanent link")

One of the most common use cases for persistence is to use it to keep track of conversation history. This is great - it makes it easy to continue conversations. As conversations get longer and longer, however, this conversation history can build up and take up more and more of the context window. This can often be undesirable as it leads to more expensive and longer calls to the LLM, and potentially ones that error. In order to prevent this from happening, you need to properly manage the conversation history.

Note: this guide focuses on how to do this in LangGraph, where you can fully customize how this is done. If you want a more off-the-shelf solution, you can look into functionality provided in LangChain:

- [How to filter messages](https://python.langchain.com/docs/how_to/filter_messages/)
- [How to trim messages](https://python.langchain.com/docs/how_to/trim_messages/)

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/memory/manage-conversation-history/\#setup "Permanent link")

First, let's set up the packages we're going to want to use

```md-code__content
%%capture --no-stderr
%pip install --quiet -U langgraph langchain_anthropic

```

Next, we need to set API keys for Anthropic (the LLM we will use)

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


## Build the agent [¶](https://langchain-ai.github.io/langgraph/how-tos/memory/manage-conversation-history/\#build-the-agent "Permanent link")

Let's now build a simple ReAct style agent.

API Reference: [ChatAnthropic](https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [ToolNode](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.ToolNode)

```md-code__content
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode

memory = MemorySaver()

@tool
def search(query: str):
    """Call to surf the web."""
    # This is a placeholder for the actual implementation
    # Don't let the LLM know this though 😊
    return "It's sunny in San Francisco, but you better look out if you're a Gemini 😈."

tools = [search]
tool_node = ToolNode(tools)
model = ChatAnthropic(model_name="claude-3-haiku-20240307")
bound_model = model.bind_tools(tools)

def should_continue(state: MessagesState):
    """Return the next node to execute."""
    last_message = state["messages"][-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return END
    # Otherwise if there is, we continue
    return "action"

# Define the function that calls the model
def call_model(state: MessagesState):
    response = bound_model.invoke(state["messages"])
    # We return a list, because this will get added to the existing list
    return {"messages": response}

# Define a new graph
workflow = StateGraph(MessagesState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.add_edge(START, "agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Next, we pass in the path map - all the possible nodes this edge could go to
    ["action", END],
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("action", "agent")

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
app = workflow.compile(checkpointer=memory)

```

API Reference: [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html)

```md-code__content
from langchain_core.messages import HumanMessage

config = {"configurable": {"thread_id": "2"}}
input_message = HumanMessage(content="hi! I'm bob")
for event in app.stream({"messages": [input_message]}, config, stream_mode="values"):
    event["messages"][-1].pretty_print()

input_message = HumanMessage(content="what's my name?")
for event in app.stream({"messages": [input_message]}, config, stream_mode="values"):
    event["messages"][-1].pretty_print()

```

```md-code__content
================================[1m Human Message [0m=================================\
\
hi! I'm bob\
==================================[1m Ai Message [0m==================================\
\
Nice to meet you, Bob! As an AI assistant, I don't have a physical form, but I'm happy to chat with you and try my best to help out however I can. Please feel free to ask me anything, and I'll do my best to provide useful information or assistance.\
================================[1m Human Message [0m=================================\
\
what's my name?\
==================================[1m Ai Message [0m==================================\
\
You said your name is Bob, so that is the name I have for you.\
\
```\
\
## Filtering messages [¶](https://langchain-ai.github.io/langgraph/how-tos/memory/manage-conversation-history/\#filtering-messages "Permanent link")\
\
The most straight-forward thing to do to prevent conversation history from blowing up is to filter the list of messages before they get passed to the LLM. This involves two parts: defining a function to filter messages, and then adding it to the graph. See the example below which defines a really simple `filter_messages` function and then uses it.\
\
API Reference: [ChatAnthropic](https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [ToolNode](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.ToolNode)\
\
```md-code__content\
from typing import Literal\
\
from langchain_anthropic import ChatAnthropic\
from langchain_core.tools import tool\
\
from langgraph.checkpoint.memory import MemorySaver\
from langgraph.graph import MessagesState, StateGraph, START\
from langgraph.prebuilt import ToolNode\
\
memory = MemorySaver()\
\
@tool\
def search(query: str):\
    """Call to surf the web."""\
    # This is a placeholder for the actual implementation\
    # Don't let the LLM know this though 😊\
    return "It's sunny in San Francisco, but you better look out if you're a Gemini 😈."\
\
tools = [search]\
tool_node = ToolNode(tools)\
model = ChatAnthropic(model_name="claude-3-haiku-20240307")\
bound_model = model.bind_tools(tools)\
\
def should_continue(state: MessagesState):\
    """Return the next node to execute."""\
    last_message = state["messages"][-1]\
    # If there is no function call, then we finish\
    if not last_message.tool_calls:\
        return END\
    # Otherwise if there is, we continue\
    return "action"\
\
def filter_messages(messages: list):\
    # This is very simple helper function which only ever uses the last message\
    return messages[-1:]\
\
# Define the function that calls the model\
def call_model(state: MessagesState):\
    messages = filter_messages(state["messages"])\
    response = bound_model.invoke(messages)\
    # We return a list, because this will get added to the existing list\
    return {"messages": response}\
\
# Define a new graph\
workflow = StateGraph(MessagesState)\
\
# Define the two nodes we will cycle between\
workflow.add_node("agent", call_model)\
workflow.add_node("action", tool_node)\
\
# Set the entrypoint as `agent`\
# This means that this node is the first one called\
workflow.add_edge(START, "agent")\
\
# We now add a conditional edge\
workflow.add_conditional_edges(\
    # First, we define the start node. We use `agent`.\
    # This means these are the edges taken after the `agent` node is called.\
    "agent",\
    # Next, we pass in the function that will determine which node is called next.\
    should_continue,\
    # Next, we pass in the pathmap - all the possible nodes this edge could go to\
    ["action", END],\
)\
\
# We now add a normal edge from `tools` to `agent`.\
# This means that after `tools` is called, `agent` node is called next.\
workflow.add_edge("action", "agent")\
\
# Finally, we compile it!\
# This compiles it into a LangChain Runnable,\
# meaning you can use it as you would any other runnable\
app = workflow.compile(checkpointer=memory)\
\
```\
\
API Reference: [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html)\
\
```md-code__content\
from langchain_core.messages import HumanMessage\
\
config = {"configurable": {"thread_id": "2"}}\
input_message = HumanMessage(content="hi! I'm bob")\
for event in app.stream({"messages": [input_message]}, config, stream_mode="values"):\
    event["messages"][-1].pretty_print()\
\
# This will now not remember the previous messages\
# (because we set `messages[-1:]` in the filter messages argument)\
input_message = HumanMessage(content="what's my name?")\
for event in app.stream({"messages": [input_message]}, config, stream_mode="values"):\
    event["messages"][-1].pretty_print()\
\
```\
\
```md-code__content\
================================[1m Human Message [0m=================================\
\
hi! I'm bob\
==================================[1m Ai Message [0m==================================\
\
Nice to meet you, Bob! I'm Claude, an AI assistant created by Anthropic. It's a pleasure to chat with you. Feel free to ask me anything, I'm here to help!\
================================[1m Human Message [0m=================================\
\
what's my name?\
==================================[1m Ai Message [0m==================================\
\
I'm afraid I don't actually know your name. As an AI assistant, I don't have information about the specific identities of the people I talk to. I only know what is provided to me during our conversation.\
\
```\
\
In the above example we defined the `filter_messages` function ourselves. We also provide off-the-shelf ways to trim and filter messages in LangChain.\
\
- [How to filter messages](https://python.langchain.com/docs/how_to/filter_messages/)\
- [How to trim messages](https://python.langchain.com/docs/how_to/trim_messages/)\
\
## Comments\
\
giscus\
\
#### [2 reactions](https://github.com/langchain-ai/langgraph/discussions/1410)\
\
👍2\
\
#### [7 comments](https://github.com/langchain-ai/langgraph/discussions/1410)\
\
#### ·\
\
#### 7 replies\
\
_– powered by [giscus](https://giscus.app/)_\
\
- Oldest\
- Newest\
\
[![@jojohannsen](https://avatars.githubusercontent.com/u/88145?u=67f7837c4c93f51d8915d46bbc364244ae0bd4f6&v=4)jojohannsen](https://github.com/jojohannsen) [Aug 21, 2024](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-10407426)\
\
Thanks for making all these great How-to guides.\
\
In this one, I'm seeing a problem with that very last "what's my name?" -- the error is\
\
`anthropic.BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages: first message must use the "user" role'}}`\
\
[https://smith.langchain.com/o/89f6cd25-e2fd-498b-82ab-058e41888172/projects/p/e52b5fcf-4a6b-4663-8034-e4f7f4c20ed7?timeModel=%7B%22duration%22%3A%227d%22%7D](https://smith.langchain.com/o/89f6cd25-e2fd-498b-82ab-058e41888172/projects/p/e52b5fcf-4a6b-4663-8034-e4f7f4c20ed7?timeModel=%7B%22duration%22%3A%227d%22%7D)\
\
It doesn't make sense, since the first message actually is a HumanMessage. Also, if I add a second HumanMessage, then everything is fine (that's the successful one in the langsmith project)\
\
1\
\
👀1\
\
5 replies\
\
[![@hwchase17](https://avatars.githubusercontent.com/u/11986836?u=f4c4f21a82b2af6c9f91e1f1d99ea40062f7a101&v=4)](https://github.com/hwchase17)\
\
[hwchase17](https://github.com/hwchase17) [Aug 22, 2024](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-10414652)\
\
Contributor\
\
can you share a public version of your langsmith trace? dont think i can see that\
\
[![@jojohannsen](https://avatars.githubusercontent.com/u/88145?u=67f7837c4c93f51d8915d46bbc364244ae0bd4f6&v=4)](https://github.com/jojohannsen)\
\
[jojohannsen](https://github.com/jojohannsen) [Aug 22, 2024](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-10422153)\
\
[https://smith.langchain.com/public/866fa557-063c-4e56-94f2-9712d7a0caba/r](https://smith.langchain.com/public/866fa557-063c-4e56-94f2-9712d7a0caba/r) is the one with the error\
\
[https://smith.langchain.com/public/866fa557-063c-4e56-94f2-9712d7a0caba/r](https://smith.langchain.com/public/866fa557-063c-4e56-94f2-9712d7a0caba/r) is the exact same one, but with one additional human message, no error on this one\
\
[![@jojohannsen](https://avatars.githubusercontent.com/u/88145?u=67f7837c4c93f51d8915d46bbc364244ae0bd4f6&v=4)](https://github.com/jojohannsen)\
\
[jojohannsen](https://github.com/jojohannsen) [Aug 22, 2024](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-10422183)\
\
[https://smith.langchain.com/public/91ca3b3e-ffc6-4812-8883-7c0c9becfadd/r](https://smith.langchain.com/public/91ca3b3e-ffc6-4812-8883-7c0c9becfadd/r) this is the no-error one (above was error link twice...)\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Aug 22, 2024](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-10422852)\
\
Collaborator\
\
ah there was a mistake in the docs, updating! it should be messages\[-1:\] in the `filter_messages`\
\
👍1\
\
[![@archit-spec](https://avatars.githubusercontent.com/u/74809912?u=fd0ec982d5d87054c49e232b0d3ac3e78eb4e37c&v=4)](https://github.com/archit-spec)\
\
[archit-spec](https://github.com/archit-spec) [Dec 27, 2024](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-11675843)\
\
not able to access these traces\
\
[![@antoremin](https://avatars.githubusercontent.com/u/6918736?v=4)antoremin](https://github.com/antoremin) [Sep 24, 2024](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-10741479)\
\
Consider the following use case:\
\
I'm working on a research graph. The graph:\
\
1. takes in a request, plans a series of research actions (search, etc),\
2. runs these actions (usually 5-15 at the time)\
3. reviews results, compiles a search results document\
4. Reviews the request, the plan, results, checks if done, goes to the plan node once more.\
\
What would be the best way to manage trimming messages for history? I'm dealing with two issues:\
\
1. Tool calls get trimmed and # of tool calls and tool results don't match so model calls fall over.\
2. Message history overflows, but summarization doesn't deliver enough context granularity.\
\
\
Different nodes would benefit from certain parts of previous messages (e.g search results compiler should see all ToolMessage items from the previous run, whereas the planner should probably see previous HumanMessages and maybe some other select AIMessages)\
\
The first issue seems like something that should have a solution on Langchain side.\
\
The second is something that I think could be added for the benefit of many real world use cases: how do you support longer-running langgraphs that need to deal with granular information.\
\
1\
\
1 reply\
\
[![@eyurtsev](https://avatars.githubusercontent.com/u/3205522?v=4)](https://github.com/eyurtsev)\
\
[eyurtsev](https://github.com/eyurtsev) [Sep 27, 2024](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-10777238)\
\
Collaborator\
\
For (1), it really depends on what you're doing with the chat history downstream. If you want to feed it directly into a chat model, then the chat history must meet these criteria to be considered valid by most chat model providers:\
\
1. Start on system message or human message\
2. Ends on human message or tool message\
3. Any tool message only appears after a corresponding ai message\
\
To achieve this you can specify the following with `trim_messages`:\
\
- start\_on="human",\
- end\_on=("human", "tool"),\
\
Note that you will probably also want to include the system message (include\_system=True).\
\
This configuration will handle the simplest manipulation of the conversation history. If you need something more complex, you can use trim\_messages as a building block.\
\
For (2), we added this tutorial: [https://langchain-ai.github.io/langgraph/tutorials/memory/long\_term\_memory\_agent/](https://langchain-ai.github.io/langgraph/tutorials/memory/long_term_memory_agent/). Things can get complex for more complex use cases.\
\
[![@edwinow](https://avatars.githubusercontent.com/u/92256435?u=749a5ad13efef16ae7cd7a6b746d45f7db5179c1&v=4)edwinow](https://github.com/edwinow) [Oct 16, 2024](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-10954875)\
\
Thanks Eugene for the response, helpful to know about `trim_messages`!\
\
For others, here's updated link to [the latest docs for long term memory](https://langchain-ai.github.io/langgraph/concepts/memory/#long-term-memory) and there are a couple of really helpful new videos that the team have put out too on their youtube channel on the topic.\
\
1\
\
0 replies\
\
[![@ghost](https://avatars.githubusercontent.com/u/10137?s=64&v=4)ghost](https://github.com/ghost) [Oct 18, 2024](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-10981719)\
\
is there a way to implement this in the pre-built react agent? do we modify the code of the agent?\
\
1\
\
0 replies\
\
[![@Maheshbabu9199](https://avatars.githubusercontent.com/u/59558917?u=7a5a31c082030ce6794cf1da7a61edfcea731796&v=4)Maheshbabu9199](https://github.com/Maheshbabu9199) [Nov 26, 2024](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-11379338)\
\
Hello,\
\
I am trying to create an agent using create\_react\_agent. I am creating a memory using MemorySaver() class. But I am not able to find out how can I add custom messages to the agent's checkpointer. I've tried using aput\_writes of MemorySaver class, but it seems the agent is not using the memory. When I include these custom messages in the prompt, the agent is giving me expected answer around the messages but from checkpointer it is not retrieving that information.\
\
Can anyone help me in this ??\
\
Thanks!!\
\
3\
\
1 reply\
\
[![@rainsunsun](https://avatars.githubusercontent.com/u/199331754?u=f3ab16f7ef1e9e60f9009065735cdd67ae237e5b&v=4)](https://github.com/rainsunsun)\
\
[rainsunsun](https://github.com/rainsunsun) [Mar 14](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-12497205)\
\
你解决这个问题了吗，我也遇到了同样的问题\
\
[![@junbo2001](https://avatars.githubusercontent.com/u/50980865?u=4a506a974acdc6c03321d345dd5dd328b47c56be&v=4)junbo2001](https://github.com/junbo2001) [Mar 12](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-12470509)\
\
我有一个需求，当messages列表只有humanmessage和aimessage，model.invoke时能执行成功，如下是两轮对话的示例：\
\
```\
[\
#第一轮对话\
HumanMessage(content='指令：请结合自身能力进行回答\n\n  用户问题: 你是谁？'),\
 AIMessage(content='我是通义千问，阿里巴巴集团旗下的超大规模语言模型。我能够回答问题、创作文字，如写故事、公文、邮件、剧本等，还能进行逻辑推理、编程，甚至表达观点和玩游戏。我在多国语言上都有很好的掌握，能为你提供多样化的帮助。'),\
#第二轮对话\
HumanMessage(content='指令：请结合自身能力进行回答\n\n  用户问题: 我是小明')，\
AIMessage(content='你好，小明！很高兴认识你。作为一个语言模型，我可以帮助你解答问题、创作文字、进行逻辑推理、编程等。如果你有任何需要帮助的地方，尽管告诉我，我会尽力提供支持。有什么我可以帮到你的吗？'),\
]\
```\
\
然而，当我加入systemmessage时候，第一轮对话也是可以成功的，如下对话示例：\
\
```\
[\
#第一轮对话\
SystemMessage(content='你是豆丁网站平台的智能客服，工号001。你的任务是按照指定的规则回答用户问题，规则包括以下两种情况：\
1、严格依据提供的文档内容：对于具体步骤、细节或事实信息，必须完全按照文档回答，不得改写、总结或补充额外内容。\
 2、结合自身能力进行回答：在未提供文档或文档中未涵盖相关信息时，可根据自身知识进行合理解答，确保答案准确、有用。')\
HumanMessage(content='指令：请结合自身能力进行回答\n\n  用户问题: 你是谁？'),\
 AIMessage(content='我是通义千问，阿里巴巴集团旗下的超大规模语言模型。我能够回答问题、创作文字，如写故事、公文、邮件、剧本等，还能进行逻辑推理、编程，甚至表达观点和玩游戏。我在多国语言上都有很好的掌握，能为你提供多样化的帮助。'),\
]\
```\
\
在第二轮对话model.invoke时就会报错提示我SystemMessage类型消息只能存在一条，如下示例：\
\
```\
[\
 #第一轮对话\
SystemMessage(content='你是豆丁网站平台的智能客服，工号001。你的任务是按照指定的规则回答用户问题，规则包括以下两种情况：\
1、严格依据提供的文档内容：对于具体步骤、细节或事实信息，必须完全按照文档回答，不得改写、总结或补充额外内容。\
 2、结合自身能力进行回答：在未提供文档或文档中未涵盖相关信息时，可根据自身知识进行合理解答，确保答案准确、有用。')\
HumanMessage(content='指令：请结合自身能力进行回答\n\n  用户问题: 你是谁？'),\
 AIMessage(content='我是通义千问，阿里巴巴集团旗下的超大规模语言模型。我能够回答问题、创作文字，如写故事、公文、邮件、剧本等，还能进行逻辑推理、编程，甚至表达观点和玩游戏。我在多国语言上都有很好的掌握，能为你提供多样化的帮助。'),\
\
 #第二轮对话\
 SystemMessage(content='你是豆丁网站平台的智能客服，工号001。你的任务是按照指定的规则回答用户问题，规则包括以下两种情况：\
1、严格依据提供的文档内容：对于具体步骤、细节或事实信息，必须完全按照文档回答，不得改写、总结或补充额外内容。\
 2、结合自身能力进行回答：在未提供文档或文档中未涵盖相关信息时，可根据自身知识进行合理解答，确保答案准确、有用。')\
 HumanMessage(content='指令：请结合自身能力进行回答\n\n  用户问题: 你是谁？')\
]\
```\
\
我也很明白是在model.invoke时，消息列表内容不能有多条SystemMessage类型的消息，但是我应该在怎么让SystemMessage只有一条呢？我想到一点时在model.invoke之前循环判断SystemMessage类型的消息是否存在，但是我想求助有没有更简便一点的方式？\
\
0\
\
0 replies\
\
[![@Anandukc](https://avatars.githubusercontent.com/u/128222367?u=af4092fb58a943a3141444a6f813bf19e550b739&v=4)Anandukc](https://github.com/Anandukc) [Mar 20](https://github.com/langchain-ai/langgraph/discussions/1410#discussioncomment-12561231)\
\
while i implemented filter message iam getting the following error . can someone help me how to solve this:\
\
Error in chatbot execution: Error code: 400 - {'error': {'message': "Invalid parameter: messages with role 'tool' must be a response to a preceeding message with 'tool\_calls'.", 'type': 'invalid\_request\_error', 'param': 'messages.\[1\].role', 'code': None}}\
\
below is my code:\
\
def filter\_messages(messages: list):\
\
"""Returns the last 18 messages."""\
\
return messages\[-12:\]\
\
def delete\_messages(state: State) -> dict:\
\
"""Deletes older messages if there are more than 18."""\
\
messages = state\["messages"\]\
\
if len(messages) > 12:\
\
return {"messages": \[RemoveMessage(id=m.id) for m in messages\[:-5\]\]}\
\
return {}\
\
def should\_continue(state: State) -> str:\
\
"""\
\
Determines which node to execute next after the chatbot.\
\
This function checks if the last message has any tool calls.\
\
Direct-return is handled later in the tools node.\
\
"""\
\
last\_message = state\["messages"\]\[-1\]\
\
if not hasattr(last\_message, "tool\_calls") or not last\_message.tool\_calls:\
\
return "delete\_messages"\
\
return "tools"\
\
###############################################################################\
\
Build the Graph\
\
def build\_graph():\
\
"""\
\
Builds the decision-making graph by combining an LLM with various tools.\
\
"""\
\
try:\
\
primary\_llm = ChatOpenAI(\
\
model=TOOLS\_CFG.primary\_agent\_llm,\
\
temperature=TOOLS\_CFG.primary\_agent\_llm\_temperature,\
\
api\_key=openai\_key\
\
)\
\
except Exception as e:\
\
raise RuntimeError(f"Error initializing ChatOpenAI: {str(e)}")\
\
graph\_builder = StateGraph(State)\
\
# Define tools including query\_leave\_details\_tool (which should be configured as return\_direct)\
\
tools = \[leave\_request\_tool, get\_leave\_balances\_tool, sqlserver\_rag\_tool, query\_leave\_details\_tool,query\_employee\_details\_tool,query\_payroll\_details\_tool,query\_attendance\_details\_tool\]\
\
try:\
\
primary\_llm\_with\_tools = primary\_llm.bind\_tools(tools, parallel\_tool\_calls=False)\
\
except Exception as e:\
\
raise RuntimeError(f"Error binding tools to the LLM: {str(e)}")\
\
def chatbot(state: State):\
\
"""Executes the LLM with system instructions and conversation history."""\
\
try:\
\
messages = \[{"role": "system", "content": system\_message}\] + filter\_messages(state\["messages"\])\
\
\# Debug: Print messages being sent to the LLM\
\
print("\\n============================###")\
\
print("Messages sent to LLM:")\
\
for msg in messages:\
\
print(msg)\
\
print("============================###\\n")\
\
return {"messages": \[primary\_llm\_with\_tools.invoke(messages)\]}\
\
except Exception as e:\
\
print(f"Error in chatbot execution: {str(e)}")\
\
error\_msg = "An error occurred while processing your request."\
\
if 'insufficient\_quota' in str(e).lower():\
\
error\_msg = "Seems like your API key has exhausted. Please check your usage and recharge."\
\
return {"messages": \[{"role": "assistant", "content": error\_msg}\]}\
\
try:\
\
\# Add nodes\
\
graph\_builder.add\_node("chatbot", chatbot)\
\
tool\_node = BasicToolNode(tools=\[leave\_request\_tool, get\_leave\_balances\_tool, sqlserver\_rag\_tool, query\_leave\_details\_tool, query\_employee\_details\_tool,query\_payroll\_details\_tool,query\_attendance\_details\_tool\])\
\
graph\_builder.add\_node("tools", tool\_node)\
\
graph\_builder.add\_node("delete\_messages", delete\_messages)\
\
```notranslate\
# Conditional edge from chatbot to either tools or delete_messages\
graph_builder.add_conditional_edges(\
    "chatbot",\
    should_continue,\
    {"tools": "tools", "delete_messages": "delete_messages"}\
)\
\
# FIXED CONDITIONAL EDGE\
graph_builder.add_conditional_edges(\
    "tools",\
    lambda state: END if state.get("return_direct", False) else "chatbot"\
)\
\
# After delete_messages, end the flow.\
graph_builder.add_edge("delete_messages", END)\
# Set the entry point.\
graph_builder.add_edge(START, "chatbot")\
\
```\
\
except Exception as e:\
\
raise RuntimeError(f"Error adding nodes or edges to the graph: {str(e)}")\
\
1\
\
0 replies\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fmemory%2Fmanage-conversation-history%2F)