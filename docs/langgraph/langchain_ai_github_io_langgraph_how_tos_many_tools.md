[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/many-tools/#how-to-handle-large-numbers-of-tools)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/many-tools.ipynb "Edit this page")

# How to handle large numbers of tools [¶](https://langchain-ai.github.io/langgraph/how-tos/many-tools/\#how-to-handle-large-numbers-of-tools "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [Tools](https://python.langchain.com/docs/concepts/#tools)
- [Chat Models](https://python.langchain.com/docs/concepts/#chat-models/)
- [Embedding Models](https://python.langchain.com/docs/concepts/#embedding-models)
- [Vectorstores](https://python.langchain.com/docs/concepts/#vector-stores)
- [Document](https://python.langchain.com/docs/concepts/#documents)

The subset of available tools to call is generally at the discretion of the model (although many providers also enable the user to [specify or constrain the choice of tool](https://python.langchain.com/docs/how_to/tool_choice/)). As the number of available tools grows, you may want to limit the scope of the LLM's selection, to decrease token consumption and to help manage sources of error in LLM reasoning.

Here we will demonstrate how to dynamically adjust the tools available to a model. Bottom line up front: like [RAG](https://python.langchain.com/docs/concepts/#retrieval) and similar methods, we prefix the model invocation by retrieving over available tools. Although we demonstrate one implementation that searches over tool descriptions, the details of the tool selection can be customized as needed.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/many-tools/\#setup "Permanent link")

First, let's install the required packages and set our API keys

```md-code__content
%%capture --no-stderr
%pip install --quiet -U langgraph langchain_openai numpy

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


## Define the tools [¶](https://langchain-ai.github.io/langgraph/how-tos/many-tools/\#define-the-tools "Permanent link")

Let's consider a toy example in which we have one tool for each publicly traded company in the [S&P 500 index](https://en.wikipedia.org/wiki/S%26P_500). Each tool fetches company-specific information based on the year provided as a parameter.

We first construct a registry that associates a unique identifier with a schema for each tool. We will represent the tools using JSON schema, which can be bound directly to chat models supporting tool calling.

API Reference: [StructuredTool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.structured.StructuredTool.html)

```md-code__content
import re
import uuid

from langchain_core.tools import StructuredTool

def create_tool(company: str) -> dict:
    """Create schema for a placeholder tool."""
    # Remove non-alphanumeric characters and replace spaces with underscores for the tool name
    formatted_company = re.sub(r"[^\w\s]", "", company).replace(" ", "_")

    def company_tool(year: int) -> str:
        # Placeholder function returning static revenue information for the company and year
        return f"{company} had revenues of $100 in {year}."

    return StructuredTool.from_function(
        company_tool,
        name=formatted_company,
        description=f"Information about {company}",
    )

# Abbreviated list of S&P 500 companies for demonstration
s_and_p_500_companies = [\
    "3M",\
    "A.O. Smith",\
    "Abbott",\
    "Accenture",\
    "Advanced Micro Devices",\
    "Yum! Brands",\
    "Zebra Technologies",\
    "Zimmer Biomet",\
    "Zoetis",\
]

# Create a tool for each company and store it in a registry with a unique UUID as the key
tool_registry = {
    str(uuid.uuid4()): create_tool(company) for company in s_and_p_500_companies
}

```

## Define the graph [¶](https://langchain-ai.github.io/langgraph/how-tos/many-tools/\#define-the-graph "Permanent link")

### Tool selection [¶](https://langchain-ai.github.io/langgraph/how-tos/many-tools/\#tool-selection "Permanent link")

We will construct a node that retrieves a subset of available tools given the information in the state-- such as a recent user message. In general, the full scope of [retrieval solutions](https://python.langchain.com/docs/concepts/#retrieval) are available for this step. As a simple solution, we index embeddings of tool descriptions in a vector store, and associate user queries to tools via semantic search.

API Reference: [Document](https://python.langchain.com/api_reference/core/documents/langchain_core.documents.base.Document.html) \| [InMemoryVectorStore](https://python.langchain.com/api_reference/core/vectorstores/langchain_core.vectorstores.in_memory.InMemoryVectorStore.html) \| [OpenAIEmbeddings](https://python.langchain.com/api_reference/openai/embeddings/langchain_openai.embeddings.base.OpenAIEmbeddings.html)

```md-code__content
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings

tool_documents = [\
    Document(\
        page_content=tool.description,\
        id=id,\
        metadata={"tool_name": tool.name},\
    )\
    for id, tool in tool_registry.items()\
]

vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())
document_ids = vector_store.add_documents(tool_documents)

```

### Incorporating with an agent [¶](https://langchain-ai.github.io/langgraph/how-tos/many-tools/\#incorporating-with-an-agent "Permanent link")

We will use a typical React agent graph (e.g., as used in the [quickstart](https://langchain-ai.github.io/langgraph/tutorials/introduction/#part-2-enhancing-the-chatbot-with-tools)), with some modifications:

- We add a `selected_tools` key to the state, which stores our selected subset of tools;
- We set the entry point of the graph to be a `select_tools` node, which populates this element of the state;
- We bind the selected subset of tools to the chat model within the `agent` node.

API Reference: [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [add\_messages](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.message.add_messages) \| [ToolNode](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.ToolNode) \| [tools\_condition](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.tools_condition)

```md-code__content
from typing import Annotated

from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Define the state structure using TypedDict.
# It includes a list of messages (processed by add_messages)
# and a list of selected tool IDs.
class State(TypedDict):
    messages: Annotated[list, add_messages]
    selected_tools: list[str]

builder = StateGraph(State)

# Retrieve all available tools from the tool registry.
tools = list(tool_registry.values())
llm = ChatOpenAI()

# The agent function processes the current state
# by binding selected tools to the LLM.
def agent(state: State):
    # Map tool IDs to actual tools
    # based on the state's selected_tools list.
    selected_tools = [tool_registry[id] for id in state["selected_tools"]]
    # Bind the selected tools to the LLM for the current interaction.
    llm_with_tools = llm.bind_tools(selected_tools)
    # Invoke the LLM with the current messages and return the updated message list.
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# The select_tools function selects tools based on the user's last message content.
def select_tools(state: State):
    last_user_message = state["messages"][-1]
    query = last_user_message.content
    tool_documents = vector_store.similarity_search(query)
    return {"selected_tools": [document.id for document in tool_documents]}

builder.add_node("agent", agent)
builder.add_node("select_tools", select_tools)

tool_node = ToolNode(tools=tools)
builder.add_node("tools", tool_node)

builder.add_conditional_edges("agent", tools_condition, path_map=["tools", "__end__"])
builder.add_edge("tools", "agent")
builder.add_edge("select_tools", "agent")
builder.add_edge(START, "select_tools")
graph = builder.compile()

```

```md-code__content
from IPython.display import Image, display

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass

```

![](<Base64-Image-Removed>)

```md-code__content
user_input = "Can you give me some information about AMD in 2022?"

result = graph.invoke({"messages": [("user", user_input)]})

```

```md-code__content
print(result["selected_tools"])

```

```md-code__content
['ab9c0d59-3d16-448d-910c-73cf10a26020', 'f5eff8f6-7fb9-47b6-b54f-19872a52db84', '2962e168-9ef4-48dc-8b7c-9227e7956d39', '24a9fb82-19fe-4a88-944e-47bc4032e94a']

```

```md-code__content
for message in result["messages"]:
    message.pretty_print()

```

```md-code__content
================================[1m Human Message [0m=================================\
\
Can you give me some information about AMD in 2022?\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  Advanced_Micro_Devices (call_CRxQ0oT7NY7lqf35DaRNTJ35)\
 Call ID: call_CRxQ0oT7NY7lqf35DaRNTJ35\
  Args:\
    year: 2022\
=================================[1m Tool Message [0m=================================\
Name: Advanced_Micro_Devices\
\
Advanced Micro Devices had revenues of $100 in 2022.\
==================================[1m Ai Message [0m==================================\
\
In 2022, Advanced Micro Devices (AMD) had revenues of $100.\
\
```\
\
## Repeating tool selection [¶](https://langchain-ai.github.io/langgraph/how-tos/many-tools/\#repeating-tool-selection "Permanent link")\
\
To manage errors from incorrect tool selection, we could revisit the `select_tools` node. One option for implementing this is to modify `select_tools` to generate the vector store query using all messages in the state (e.g., with a chat model) and add an edge routing from `tools` to `select_tools`.\
\
We implement this change below. For demonstration purposes, we simulate an error in the initial tool selection by adding a `hack_remove_tool_condition` to the `select_tools` node, which removes the correct tool on the first iteration of the node. Note that on the second iteration, the agent finishes the run as it has access to the correct tool.\
\
Using Pydantic with LangChain\
\
This notebook uses Pydantic v2 `BaseModel`, which requires `langchain-core >= 0.3`. Using `langchain-core < 0.3` will result in errors due to mixing of Pydantic v1 and v2 `BaseModels`.\
\
\
API Reference: [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html) \| [SystemMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.system.SystemMessage.html) \| [ToolMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.tool.ToolMessage.html)\
\
```md-code__content\
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage\
from langgraph.pregel.retry import RetryPolicy\
\
from pydantic import BaseModel, Field\
\
class QueryForTools(BaseModel):\
    """Generate a query for additional tools."""\
\
    query: str = Field(..., description="Query for additional tools.")\
\
def select_tools(state: State):\
    """Selects tools based on the last message in the conversation state.\
\
    If the last message is from a human, directly uses the content of the message\
    as the query. Otherwise, constructs a query using a system message and invokes\
    the LLM to generate tool suggestions.\
    """\
    last_message = state["messages"][-1]\
    hack_remove_tool_condition = False  # Simulate an error in the first tool selection\
\
    if isinstance(last_message, HumanMessage):\
        query = last_message.content\
        hack_remove_tool_condition = True  # Simulate wrong tool selection\
    else:\
        assert isinstance(last_message, ToolMessage)\
        system = SystemMessage(\
            "Given this conversation, generate a query for additional tools. "\
            "The query should be a short string containing what type of information "\
            "is needed. If no further information is needed, "\
            "set more_information_needed False and populate a blank string for the query."\
        )\
        input_messages = [system] + state["messages"]\
        response = llm.bind_tools([QueryForTools], tool_choice=True).invoke(\
            input_messages\
        )\
        query = response.tool_calls[0]["args"]["query"]\
\
    # Search the tool vector store using the generated query\
    tool_documents = vector_store.similarity_search(query)\
    if hack_remove_tool_condition:\
        # Simulate error by removing the correct tool from the selection\
        selected_tools = [\
            document.id\
            for document in tool_documents\
            if document.metadata["tool_name"] != "Advanced_Micro_Devices"\
        ]\
    else:\
        selected_tools = [document.id for document in tool_documents]\
    return {"selected_tools": selected_tools}\
\
graph_builder = StateGraph(State)\
graph_builder.add_node("agent", agent)\
graph_builder.add_node("select_tools", select_tools, retry=RetryPolicy(max_attempts=3))\
\
tool_node = ToolNode(tools=tools)\
graph_builder.add_node("tools", tool_node)\
\
graph_builder.add_conditional_edges(\
    "agent",\
    tools_condition,\
)\
graph_builder.add_edge("tools", "select_tools")\
graph_builder.add_edge("select_tools", "agent")\
graph_builder.add_edge(START, "select_tools")\
graph = graph_builder.compile()\
\
```\
\
```md-code__content\
from IPython.display import Image, display\
\
try:\
    display(Image(graph.get_graph().draw_mermaid_png()))\
except Exception:\
    # This requires some extra dependencies and is optional\
    pass\
\
```\
\
![](<Base64-Image-Removed>)\
\
```md-code__content\
user_input = "Can you give me some information about AMD in 2022?"\
\
result = graph.invoke({"messages": [("user", user_input)]})\
\
```\
\
```md-code__content\
for message in result["messages"]:\
    message.pretty_print()\
\
```\
\
```md-code__content\
================================[1m Human Message [0m=================================\
\
Can you give me some information about AMD in 2022?\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  Accenture (call_qGmwFnENwwzHOYJXiCAaY5Mx)\
 Call ID: call_qGmwFnENwwzHOYJXiCAaY5Mx\
  Args:\
    year: 2022\
=================================[1m Tool Message [0m=================================\
Name: Accenture\
\
Accenture had revenues of $100 in 2022.\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  Advanced_Micro_Devices (call_u9e5UIJtiieXVYi7Y9GgyDpn)\
 Call ID: call_u9e5UIJtiieXVYi7Y9GgyDpn\
  Args:\
    year: 2022\
=================================[1m Tool Message [0m=================================\
Name: Advanced_Micro_Devices\
\
Advanced Micro Devices had revenues of $100 in 2022.\
==================================[1m Ai Message [0m==================================\
\
In 2022, AMD had revenues of $100.\
\
```\
\
## Next steps [¶](https://langchain-ai.github.io/langgraph/how-tos/many-tools/\#next-steps "Permanent link")\
\
This guide provides a minimal implementation for dynamically selecting tools. There is a host of possible improvements and optimizations:\
\
- **Repeating tool selection**: Here, we repeated tool selection by modifying the `select_tools` node. Another option is to equip the agent with a `reselect_tools` tool, allowing it to re-select tools at its discretion.\
- **Optimizing tool selection**: In general, the full scope of [retrieval solutions](https://python.langchain.com/docs/concepts/#retrieval) are available for tool selection. Additional options include:\
- Group tools and retrieve over groups;\
- Use a chat model to select tools or groups of tool.\
\
## Comments\
\
giscus\
\
#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/2057)\
\
👍1\
\
#### [4 comments](https://github.com/langchain-ai/langgraph/discussions/2057)\
\
#### ·\
\
#### 2 replies\
\
_– powered by [giscus](https://giscus.app/)_\
\
- Oldest\
- Newest\
\
[![@jojohannsen](https://avatars.githubusercontent.com/u/88145?u=67f7837c4c93f51d8915d46bbc364244ae0bd4f6&v=4)jojohannsen](https://github.com/jojohannsen) [Oct 8, 2024](https://github.com/langchain-ai/langgraph/discussions/2057#discussioncomment-10886092)\
\
The first graph has conditional edge from 'agent':\
\
```\
builder.add_conditional_edges(\
    "agent",\
    tools_condition,\
)\
```\
\
and the 'tools\_condition' code and signature show:\
\
```\
Signature:\
tools_condition(\
    state: 'Union[list[AnyMessage], dict[str, Any], BaseModel]',\
) -> "Literal['tools', '__end__']"\
```\
\
The visual graph is showing three branches out of agent -- the branches to 'tools' and ' **end**' that's in that signature, which makes sense.\
\
But there's also a branch from 'agent' back to 'select\_tools' -- it doesn't seem to be from the `tools_condition`, since that's not a return value. Why is this branch showing? Is it in the code somewhere?\
\
1\
\
2 replies\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Oct 9, 2024](https://github.com/langchain-ai/langgraph/discussions/2057#discussioncomment-10886529)\
\
Collaborator\
\
[@jojohannsen](https://github.com/jojohannsen) thanks for spotting! the conditional edge was missing `path_map` to properly indicate possible node destinations from the "agent" node. we rely on these for constructing the chart\
\
````\
builder.add_conditional_edges(\
    "agent",\
    tools_condition,\
    path_map=["tools", "__end__"]\
)```\
````\
\
👍1\
\
[![@davibc90](https://avatars.githubusercontent.com/u/175640160?u=95a7eb6802c4dea5e3484b4d4558d99ac6c958c8&v=4)](https://github.com/davibc90)\
\
[davibc90](https://github.com/davibc90) [Jan 24](https://github.com/langchain-ai/langgraph/discussions/2057#discussioncomment-11948216)\
\
I've been looking into this code for a while.... If I got your point, there is no conditional routing implementation back to select\_tools node from the agent node!\
\
It's done automatically by setting up the retry policy when adding the node as part of the graph!\
\
Once the last ToolMessage returns an error, the execution goes back and restarts from the select\_tools node, as if it had just started from the beginning!\
\
The main difference is in the last\_message\[-1\]... This time is gonna evaluate the ToolMessage condition as true, running query over tools using the full history of the chat!\
\
[![@rasulv](https://avatars.githubusercontent.com/u/72885841?u=582192b9c92d9cfdf06ca7638c0164a1db1d069d&v=4)rasulv](https://github.com/rasulv) [Nov 23, 2024](https://github.com/langchain-ai/langgraph/discussions/2057#discussioncomment-11356701)\
\
edited\
\
I'm using the first code above and getting direct answer from the llm, the function tools is not calling by agent/graph.\
\
I'm using the mistralai with following packages:\
\
```notranslate\
langchain==0.2.17\
langchain-community==0.2.19\
langchain-core==0.2.43\
langchain-elasticsearch==0.2.2\
langchain-experimental==0.0.65\
langchain-mistralai==0.1.10\
langgraph==0.2.52\
\
```\
\
output:\
\
````notranslate\
================================ Human Message =================================\
\
Can you give me some information about AMD in 2022?\
================================== Ai Message ==================================\
\
Sure, I can provide some information about AMD (Advanced Micro Devices) as of 2022. However, please note that the situation may change as time goes on, and I recommend checking the latest news and financial reports for the most up-to-date information.\
\
As of early 2022, AMD is a leading manufacturer of microprocessors, graphics processors, and related technologies for the computer, gaming, and cloud computing industries. The company has a strong presence in both the consumer and enterprise markets, with its products used in a wide range of devices, from laptops and desktops to servers and gaming consoles.\
\
In recent years, AMD has made significant strides in gaining market share in the CPU (central processing unit) market, which has long been dominated by Intel. AMD's Ryzen processors have been well-received by critics and consumers alike, offering strong performance and value compared to Intel's offerings. Additionally, AMD's EPYC processors have gained traction in the data center market, challenging Intel's dominance in this space as well.\
\
In the GPU (graphics processing unit) market, AMD competes with Nvidia for share in the discrete GPU market, which is used for gaming and other graphics-intensive applications. AMD's Radeon graphics cards have a strong following among gamers and enthusiasts, although Nvidia has maintained a lead in this market in terms of market share and performance.\
\
In terms of financial performance, AMD has reported strong revenue growth in recent years, driven by demand for its CPUs and GPUs. The company has also benefited from the ongoing shift to remote work and learning, which has increased demand for PCs and cloud computing resources. However, like other tech companies, AMD has faced supply chain challenges and component shortages due to the COVID-19 pandemic, which may impact its ability to meet demand in the short term.\
\
Looking ahead, AMD is expected to continue its momentum in the CPU and GPU markets, with new product launches and technology innovations on the horizon. The company is also investing in emerging technologies such as AI and machine learning, which could present new growth opportunities in the coming years.```\
\
````\
\
2\
\
👀1\
\
0 replies\
\
[![@PovedaAqui](https://avatars.githubusercontent.com/u/9494679?u=112ef7fc2990fc0a83ccf2e26f71a7afad3c2dd5&v=4)PovedaAqui](https://github.com/PovedaAqui) [Dec 15, 2024](https://github.com/langchain-ai/langgraph/discussions/2057#discussioncomment-11574180)\
\
It would be great to have an educational video on this topic.\
\
2\
\
👍2\
\
0 replies\
\
[![@LittleSix1](https://avatars.githubusercontent.com/u/44064956?u=b164af60a76485c4153e47e1e908f13f9ccefb73&v=4)LittleSix1](https://github.com/LittleSix1) [Mar 7](https://github.com/langchain-ai/langgraph/discussions/2057#discussioncomment-12430336)\
\
def agent(state: State):\
\
\# Map tool IDs to actual tools\
\
\# based on the state's selected\_tools list.\
\
selected\_tools = \[tool\_registry\[id\] for id in state\["selected\_tools"\]\]\
\
\# Bind the selected tools to the LLM for the current interaction.\
\
llm\_with\_tools = llm.bind\_tools(selected\_tools)\
\
\# Invoke the LLM with the current messages and return the updated message list.\
\
\# print(state\["messages"\])\
\
\# print(llm\_with\_tools.invoke(state\["messages"\]))\
\
return {"messages": \[llm\_with\_tools.invoke(state\["messages"\])\]}\
\
ValidationError: 1 validation error for AIMessage\
\
tool\_calls.0.args\
\
Input should be a valid dictionary \[type=dict\_type, input\_value=3, input\_type=int\]\
\
For further information visit [https://errors.pydantic.dev/2.10/v/dict\_type](https://errors.pydantic.dev/2.10/v/dict_type)\
\
Has anyone experienced the above situation?\
\
1\
\
0 replies\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fmany-tools%2F)