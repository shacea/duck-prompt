[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/#agentic-rag)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/rag/langgraph_agentic_rag.ipynb "Edit this page")

# Agentic RAG [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/\#agentic-rag "Permanent link")

[Retrieval Agents](https://python.langchain.com/docs/tutorials/qa_chat_history/#agents) are useful when we want to make decisions about whether to retrieve from an index.

To implement a retrieval agent, we simply need to give an LLM access to a retriever tool.

We can incorporate this into [LangGraph](https://langchain-ai.github.io/langgraph/).

## Setup [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/\#setup "Permanent link")

First, let's download the required packages and set our API keys:

```md-code__content
%%capture --no-stderr
%pip install -U --quiet langchain-community tiktoken langchain-openai langchainhub chromadb langchain langgraph langchain-text-splitters beautifulsoup4

```

```md-code__content
import getpass
import os

def _set_env(key: str):
    if key not in os.environ:
        os.environ[key] = getpass.getpass(f"{key}:")

_set_env("OPENAI_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Retriever [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/\#retriever "Permanent link")

First, we index 3 blog posts.

API Reference: [WebBaseLoader](https://python.langchain.com/api_reference/community/document_loaders/langchain_community.document_loaders.web_base.WebBaseLoader.html) \| [Chroma](https://python.langchain.com/api_reference/community/vectorstores/langchain_community.vectorstores.chroma.Chroma.html) \| [OpenAIEmbeddings](https://python.langchain.com/api_reference/openai/embeddings/langchain_openai.embeddings.base.OpenAIEmbeddings.html) \| [RecursiveCharacterTextSplitter](https://python.langchain.com/api_reference/text_splitters/character/langchain_text_splitters.character.RecursiveCharacterTextSplitter.html)

```md-code__content
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

urls = [\
    "https://lilianweng.github.io/posts/2023-06-23-agent/",\
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",\
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",\
]

docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=100, chunk_overlap=50
)
doc_splits = text_splitter.split_documents(docs_list)

# Add to vectorDB
vectorstore = Chroma.from_documents(
    documents=doc_splits,
    collection_name="rag-chroma",
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever()

```

Then we create a retriever tool.

API Reference: [create\_retriever\_tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.retriever.create_retriever_tool.html)

```md-code__content
from langchain.tools.retriever import create_retriever_tool

retriever_tool = create_retriever_tool(
    retriever,
    "retrieve_blog_posts",
    "Search and return information about Lilian Weng blog posts on LLM agents, prompt engineering, and adversarial attacks on LLMs.",
)

tools = [retriever_tool]

```

## Agent State [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/\#agent-state "Permanent link")

We will define a graph.

A `state` object that it passes around to each node.

Our state will be a list of `messages`.

Each node in our graph will append to it.

API Reference: [BaseMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.base.BaseMessage.html) \| [add\_messages](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.message.add_messages)

```md-code__content
from typing import Annotated, Sequence
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage

from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
    # Default is to replace. add_messages says "append"
    messages: Annotated[Sequence[BaseMessage], add_messages]

```

## Nodes and Edges [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/\#nodes-and-edges "Permanent link")

We can lay out an agentic RAG graph like this:

- The state is a set of messages
- Each node will update (append to) state
- Conditional edges decide which node to visit next

![Screenshot 2024-02-14 at 3.43.58 PM.png](<Base64-Image-Removed>)

Using Pydantic with LangChain

This notebook uses Pydantic v2 `BaseModel`, which requires `langchain-core >= 0.3`. Using `langchain-core < 0.3` will result in errors due to mixing of Pydantic v1 and v2 `BaseModels`.


API Reference: [BaseMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.base.BaseMessage.html) \| [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html) \| [StrOutputParser](https://python.langchain.com/api_reference/core/output_parsers/langchain_core.output_parsers.string.StrOutputParser.html) \| [PromptTemplate](https://python.langchain.com/api_reference/core/prompts/langchain_core.prompts.prompt.PromptTemplate.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [tools\_condition](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.tools_condition)

```md-code__content
from typing import Annotated, Literal, Sequence
from typing_extensions import TypedDict

from langchain import hub
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field

from langgraph.prebuilt import tools_condition

### Edges

def grade_documents(state) -> Literal["generate", "rewrite"]:
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (messages): The current state

    Returns:
        str: A decision for whether the documents are relevant or not
    """

    print("---CHECK RELEVANCE---")

    # Data model
    class grade(BaseModel):
        """Binary score for relevance check."""

        binary_score: str = Field(description="Relevance score 'yes' or 'no'")

    # LLM
    model = ChatOpenAI(temperature=0, model="gpt-4o", streaming=True)

    # LLM with tool and validation
    llm_with_tool = model.with_structured_output(grade)

    # Prompt
    prompt = PromptTemplate(
        template="""You are a grader assessing relevance of a retrieved document to a user question. \n
        Here is the retrieved document: \n\n {context} \n\n
        Here is the user question: {question} \n
        If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.""",
        input_variables=["context", "question"],
    )

    # Chain
    chain = prompt | llm_with_tool

    messages = state["messages"]
    last_message = messages[-1]

    question = messages[0].content
    docs = last_message.content

    scored_result = chain.invoke({"question": question, "context": docs})

    score = scored_result.binary_score

    if score == "yes":
        print("---DECISION: DOCS RELEVANT---")
        return "generate"

    else:
        print("---DECISION: DOCS NOT RELEVANT---")
        print(score)
        return "rewrite"

### Nodes

def agent(state):
    """
    Invokes the agent model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply end.

    Args:
        state (messages): The current state

    Returns:
        dict: The updated state with the agent response appended to messages
    """
    print("---CALL AGENT---")
    messages = state["messages"]
    model = ChatOpenAI(temperature=0, streaming=True, model="gpt-4-turbo")
    model = model.bind_tools(tools)
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}

def rewrite(state):
    """
    Transform the query to produce a better question.

    Args:
        state (messages): The current state

    Returns:
        dict: The updated state with re-phrased question
    """

    print("---TRANSFORM QUERY---")
    messages = state["messages"]
    question = messages[0].content

    msg = [\
        HumanMessage(\
            content=f""" \n\
    Look at the input and try to reason about the underlying semantic intent / meaning. \n\
    Here is the initial question:\
    \n ------- \n\
    {question}\
    \n ------- \n\
    Formulate an improved question: """,\
        )\
    ]

    # Grader
    model = ChatOpenAI(temperature=0, model="gpt-4-0125-preview", streaming=True)
    response = model.invoke(msg)
    return {"messages": [response]}

def generate(state):
    """
    Generate answer

    Args:
        state (messages): The current state

    Returns:
         dict: The updated state with re-phrased question
    """
    print("---GENERATE---")
    messages = state["messages"]
    question = messages[0].content
    last_message = messages[-1]

    docs = last_message.content

    # Prompt
    prompt = hub.pull("rlm/rag-prompt")

    # LLM
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, streaming=True)

    # Post-processing
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Chain
    rag_chain = prompt | llm | StrOutputParser()

    # Run
    response = rag_chain.invoke({"context": docs, "question": question})
    return {"messages": [response]}

print("*" * 20 + "Prompt[rlm/rag-prompt]" + "*" * 20)
prompt = hub.pull("rlm/rag-prompt").pretty_print()  # Show what the prompt looks like

```

```md-code__content
********************Prompt[rlm/rag-prompt]********************
================================[1m Human Message [0m=================================\
\
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.\
Question: [33;1m[1;3m{question}[0m\
Context: [33;1m[1;3m{context}[0m\
Answer:\
\
```\
\
## Graph [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/\#graph "Permanent link")\
\
- Start with an agent, `call_model`\
- Agent make a decision to call a function\
- If so, then `action` to call tool (retriever)\
- Then call agent with the tool output added to messages ( `state`)\
\
API Reference: [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [ToolNode](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.ToolNode)\
\
```md-code__content\
from langgraph.graph import END, StateGraph, START\
from langgraph.prebuilt import ToolNode\
\
# Define a new graph\
workflow = StateGraph(AgentState)\
\
# Define the nodes we will cycle between\
workflow.add_node("agent", agent)  # agent\
retrieve = ToolNode([retriever_tool])\
workflow.add_node("retrieve", retrieve)  # retrieval\
workflow.add_node("rewrite", rewrite)  # Re-writing the question\
workflow.add_node(\
    "generate", generate\
)  # Generating a response after we know the documents are relevant\
# Call agent node to decide to retrieve or not\
workflow.add_edge(START, "agent")\
\
# Decide whether to retrieve\
workflow.add_conditional_edges(\
    "agent",\
    # Assess agent decision\
    tools_condition,\
    {\
        # Translate the condition outputs to nodes in our graph\
        "tools": "retrieve",\
        END: END,\
    },\
)\
\
# Edges taken after the `action` node is called.\
workflow.add_conditional_edges(\
    "retrieve",\
    # Assess agent decision\
    grade_documents,\
)\
workflow.add_edge("generate", END)\
workflow.add_edge("rewrite", "agent")\
\
# Compile\
graph = workflow.compile()\
\
```\
\
```md-code__content\
from IPython.display import Image, display\
\
try:\
    display(Image(graph.get_graph(xray=True).draw_mermaid_png()))\
except Exception:\
    # This requires some extra dependencies and is optional\
    pass\
\
```\
\
![](<Base64-Image-Removed>)\
\
```md-code__content\
import pprint\
\
inputs = {\
    "messages": [\
        ("user", "What does Lilian Weng say about the types of agent memory?"),\
    ]\
}\
for output in graph.stream(inputs):\
    for key, value in output.items():\
        pprint.pprint(f"Output from node '{key}':")\
        pprint.pprint("---")\
        pprint.pprint(value, indent=2, width=80, depth=None)\
    pprint.pprint("\n---\n")\
\
```\
\
```md-code__content\
---CALL AGENT---\
"Output from node 'agent':"\
'---'\
{ 'messages': [ AIMessage(content='', additional_kwargs={'tool_calls': [{'index': 0, 'id': 'call_z36oPZN8l1UC6raxrebqc1bH', 'function': {'arguments': '{"query":"types of agent memory"}', 'name': 'retrieve_blog_posts'}, 'type': 'function'}]}, response_metadata={'finish_reason': 'tool_calls'}, id='run-2bad2518-8187-4d8f-8e23-2b9501becb6f-0', tool_calls=[{'name': 'retrieve_blog_posts', 'args': {'query': 'types of agent memory'}, 'id': 'call_z36oPZN8l1UC6raxrebqc1bH'}])]}\
'\n---\n'\
---CHECK RELEVANCE---\
---DECISION: DOCS RELEVANT---\
"Output from node 'retrieve':"\
'---'\
{ 'messages': [ ToolMessage(content='Table of Contents\n\n\n\nAgent System Overview\n\nComponent One: Planning\n\nTask Decomposition\n\nSelf-Reflection\n\n\nComponent Two: Memory\n\nTypes of Memory\n\nMaximum Inner Product Search (MIPS)\n\n\nComponent Three: Tool Use\n\nCase Studies\n\nScientific Discovery Agent\n\nGenerative Agents Simulation\n\nProof-of-Concept Examples\n\n\nChallenges\n\nCitation\n\nReferences\n\nPlanning\n\nSubgoal and decomposition: The agent breaks down large tasks into smaller, manageable subgoals, enabling efficient handling of complex tasks.\nReflection and refinement: The agent can do self-criticism and self-reflection over past actions, learn from mistakes and refine them for future steps, thereby improving the quality of final results.\n\n\nMemory\n\nMemory\n\nShort-term memory: I would consider all the in-context learning (See Prompt Engineering) as utilizing short-term memory of the model to learn.\nLong-term memory: This provides the agent with the capability to retain and recall (infinite) information over extended periods, often by leveraging an external vector store and fast retrieval.\n\n\nTool use\n\nThe design of generative agents combines LLM with memory, planning and reflection mechanisms to enable agents to behave conditioned on past experience, as well as to interact with other agents.', name='retrieve_blog_posts', id='d815f283-868c-4660-a1c6-5f6e5373ca06', tool_call_id='call_z36oPZN8l1UC6raxrebqc1bH')]}\
'\n---\n'\
---GENERATE---\
"Output from node 'generate':"\
'---'\
{ 'messages': [ 'Lilian Weng discusses short-term and long-term memory in '\
                'agent systems. Short-term memory is used for in-context '\
                'learning, while long-term memory allows agents to retain and '\
                'recall information over extended periods.']}\
'\n---\n'\
\
```\
\
## Comments\
\
giscus\
\
#### [8 reactions](https://github.com/langchain-ai/langgraph/discussions/722)\
\
👍7❤️1\
\
#### [19 comments](https://github.com/langchain-ai/langgraph/discussions/722)\
\
#### ·\
\
#### 26 replies\
\
_– powered by [giscus](https://giscus.app/)_\
\
- Oldest\
- Newest\
\
[![@andresucv96](https://avatars.githubusercontent.com/u/31028659?v=4)andresucv96](https://github.com/andresucv96) [Jun 20, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-9827547)\
\
Hello,\
\
Is it only me that whenever the decision is to reformulate the question and the state goes back to the agent, it stops there. It is not going back to the retriever to get more and better context...\
\
1\
\
3 replies\
\
[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)\
\
[hinthornw](https://github.com/hinthornw) [Jun 21, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-9835577)\
\
Contributor\
\
By any chance, do you have a LangSmith trace you could share to illustrate the issue?\
\
[![@100stacks](https://avatars.githubusercontent.com/u/10120600?u=cbc2052573647e9473b8b63b001d960a3d197043&v=4)](https://github.com/100stacks)\
\
[100stacks](https://github.com/100stacks) [Aug 6, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10248460)\
\
edited\
\
Hi [@hinthornw](https://github.com/hinthornw),\
\
It appears this warning in [https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10041240](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10041240):\
\
```notranslate\
USER_AGENT environment variable not set, consider setting it to identify your requests.\
\
```\
\
was introduced with this [`community: add user agent for web scraping loaders PR`](https://github.com/langchain-ai/langchain/pull/22480). This PR is referring to [User Agent](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent) in a [HTTP Request Header](https://developer.mozilla.org/en-US/docs/Glossary/Request_header) to support [web scrapping](https://python.langchain.com/v0.1/docs/use_cases/web_scraping/) use cases for LLMs.\
\
Unfortunately, this warning is rendered whenever anyone imports and uses `langchain_community.document_loaders` that calls\
\
[user\_agent.py](https://github.com/langchain-ai/langchain/blame/master/libs/community/langchain_community/utils/user_agent.py). Btw **v0.1** docs reference web scrapping directly, though Idk if the page was ported to **v0.2** docs. 🤔\
\
I don't think this environment variable is needed for a majority of LangChain use cases, and recommend it be made an optional environment variable or simply do not render a warning if `USER_AGENT` is not present.\
\
👍1\
\
[![@VladAndronik](https://avatars.githubusercontent.com/u/21131388?v=4)](https://github.com/VladAndronik)\
\
[VladAndronik](https://github.com/VladAndronik) [Dec 27, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11677682)\
\
[@andresucv96](https://github.com/andresucv96) It is because Agent node sees full history of messages after rewrite, so he always comes to decision to use existing context for the answer without the need for new retrieval, basically taking up the role of Grader. If you only give him the rewritten question he would decide upon that. However, the loop could become infinite and you need to write stop condition.\
\
[![@bnbabu55](https://avatars.githubusercontent.com/u/56356022?v=4)bnbabu55](https://github.com/bnbabu55) [Jul 4, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-9955373)\
\
[@andresucv96](https://github.com/andresucv96), I am facing the same issue, I see that Rewrite is setting the **end** condition, not able to figure out why.\
\
1\
\
1 reply\
\
[![@bnbabu55](https://avatars.githubusercontent.com/u/56356022?v=4)](https://github.com/bnbabu55)\
\
[bnbabu55](https://github.com/bnbabu55) [Jul 4, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-9958801)\
\
[@hinthornw](https://github.com/hinthornw), here is my langsmith trace for the issue above. [https://smith.langchain.com/o/8045ed60-fa03-5794-b09c-62794425fd1a/projects/p/f7928a5e-dad0-4325-9fde-8ae6719672aa?timeModel=%7B%22duration%22%3A%227d%22%7D&peek=eca9a236-582b-48bf-b8da-d55ee786fa8a&tab=0&Volume=Success&Latency=P50&Tokens=P50&Cost=P50&Streaming=P50](https://smith.langchain.com/o/8045ed60-fa03-5794-b09c-62794425fd1a/projects/p/f7928a5e-dad0-4325-9fde-8ae6719672aa?timeModel=%7B%22duration%22%3A%227d%22%7D&peek=eca9a236-582b-48bf-b8da-d55ee786fa8a&tab=0&Volume=Success&Latency=P50&Tokens=P50&Cost=P50&Streaming=P50)\
\
[![@raselai](https://avatars.githubusercontent.com/u/157653592?v=4)raselai](https://github.com/raselai) [Jul 14, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10041240)\
\
Whenever I run this Agentic RAG I am getting this error bellow:\
\
"USER\_AGENT environment variable not set, consider setting it to identify your requests."\
\
1\
\
6 replies\
\
Show 1 previous reply\
\
[![@bnbabu55](https://avatars.githubusercontent.com/u/56356022?v=4)](https://github.com/bnbabu55)\
\
[bnbabu55](https://github.com/bnbabu55) [Jul 18, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10080744)\
\
I am just running this as a standalone python script, even then this is happening.\
\
[![@Haopeng138](https://avatars.githubusercontent.com/u/58230486?u=257f6a6618753db29982bc7e47a41b73fe7d2085&v=4)](https://github.com/Haopeng138)\
\
[Haopeng138](https://github.com/Haopeng138) [Jul 24, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10136799)\
\
```\
export USER_AGENT=myagent\
```\
\
This work for me\
\
[![@Muyuu77](https://avatars.githubusercontent.com/u/80953548?u=3a6c10e17ea27368ccd7b964c5aeed3e06a9b58b&v=4)](https://github.com/Muyuu77)\
\
[Muyuu77](https://github.com/Muyuu77) [Aug 1, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10209189)\
\
```notranslate\
import os\
os.environ['USER_AGENT'] = 'myagent'\
\
```\
\
Maybe try to put these lines at the beginning of your python file.\
\
[![@pengyulong](https://avatars.githubusercontent.com/u/9189026?u=cc90fdfcb456740422aebc45f6b6b98a6cfdb290&v=4)](https://github.com/pengyulong)\
\
[pengyulong](https://github.com/pengyulong) [Oct 18, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10978396)\
\
Setting "USE\_AGENT" like this seems to be of no use.\
\
[![@alirezava](https://avatars.githubusercontent.com/u/20642661?v=4)](https://github.com/alirezava)\
\
[alirezava](https://github.com/alirezava) [Mar 3](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12376996)\
\
for anyone with this issue,\
\
This is not an error. This is just a notice/warning.\
\
Look at the whole stacktrace for what actual issue is.\
\
If you're missing bs4 => pip install beautifulsoup4\
\
If you're missing chroma db => pip install chromadb\
\
[![@Dumplingisabeast](https://avatars.githubusercontent.com/u/154963829?u=fc1d41f377521e5ab738a1cf90af81a1b30c984d&v=4)Dumplingisabeast](https://github.com/Dumplingisabeast) [Jul 30, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10191630)\
\
when defining the state class, when would you use:\
\
Annotated\[Sequence\[BaseMessage\],...\] vs. Annotated\[list\[AnyMessage\],...\]?\
\
1\
\
0 replies\
\
[![@pguatibonza](https://avatars.githubusercontent.com/u/69604116?v=4)pguatibonza](https://github.com/pguatibonza) [Aug 9, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10280996)\
\
Hello! I want to build an agentic rag with other tools as well, but I dont know yet how to handle it. For example, If I have another tool(i.e web search), how can I ensure that it follows another path, instead of the rag path(grade, rewrite, generate)\
\
1\
\
2 replies\
\
[![@woodswift](https://avatars.githubusercontent.com/u/15988956?u=091d00f8d0f0b3e323f27f6495a877000e15b361&v=4)](https://github.com/woodswift)\
\
[woodswift](https://github.com/woodswift) [Aug 22, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10423127)\
\
format\_docs() is defined, but it is not used? Could you please explain why?\
\
[![@sreedevi1249](https://avatars.githubusercontent.com/u/33509222?v=4)](https://github.com/sreedevi1249)\
\
[sreedevi1249](https://github.com/sreedevi1249) [Oct 8, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10878396)\
\
create web\_search node and in the grade\_doucment node if documents are not relavent then you can return web\_search instead of rewrite that way you can achieve adding one more tool web\_search\
\
[![@Jimmy-L99](https://avatars.githubusercontent.com/u/53935505?u=793da26de35587e4edda9976299fcd96de0f3aba&v=4)Jimmy-L99](https://github.com/Jimmy-L99) [Sep 3, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10529187)\
\
I use my own deployed llm and db, meet error as follow:\
\
> AttributeError: 'NoneType' object has no attribute 'binary\_score'\
\
1\
\
4 replies\
\
[![@yuehua-s](https://avatars.githubusercontent.com/u/41819795?u=0a9188ac8e8f29fb749170193c7dfb56e5966c13&v=4)](https://github.com/yuehua-s)\
\
[yuehua-s](https://github.com/yuehua-s) [Oct 26, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11058541)\
\
You can try replacing `score = scored_result.binary_score` with `score = scored_result["binary_score"]`, which works for me.\
\
[![@minmie](https://avatars.githubusercontent.com/u/40080081?v=4)](https://github.com/minmie)\
\
[minmie](https://github.com/minmie) [Dec 31, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11701537)\
\
I have this error too, the scored\_result is None.\
\
dose any one has a solution？\
\
```notranslate\
  File "/home/chenjq/miniconda3/envs/RAG/lib/python3.10/site-packages/langgraph/utils/runnable.py", line 176, in invoke\
    ret = context.run(self.func, input, **kwargs)\
  File "/home/chenjq/pythonWork/RAG/langgraphDemo/langgraph_agentic_rag.py", line 136, in grade_documents\
    score = scored_result.binary_score\
AttributeError: 'NoneType' object has no attribute 'binary_score'\
\
```\
\
[![@minmie](https://avatars.githubusercontent.com/u/40080081?v=4)](https://github.com/minmie)\
\
[minmie](https://github.com/minmie) [Dec 31, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11701581)\
\
i think this may cause by your llm dosen't support structured output.\
\
[![@AlcebiadesFilho](https://avatars.githubusercontent.com/u/78539159?u=d5915a088f6b312ea44681760a5cc44051d6ca02&v=4)](https://github.com/AlcebiadesFilho)\
\
[AlcebiadesFilho](https://github.com/AlcebiadesFilho) [Feb 5](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12072496)\
\
try binaryScore\
\
[![@ricardo-casa](https://avatars.githubusercontent.com/u/79927012?u=b8af748193f4dd37f669c475a659ece27e2222bb&v=4)ricardo-casa](https://github.com/ricardo-casa) [Sep 3, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10533741)\
\
what benefits does this architecture have over adaptive rag?\
\
1\
\
1 reply\
\
[![@sreedevi1249](https://avatars.githubusercontent.com/u/33509222?v=4)](https://github.com/sreedevi1249)\
\
[sreedevi1249](https://github.com/sreedevi1249) [Oct 8, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10878311)\
\
i tried little different way where if the agent is unable to answer the question meaning out of context we can include the web search which is almost similar to adaptive rag\
\
[![@Meshinfo](https://avatars.githubusercontent.com/u/55117672?v=4)Meshinfo](https://github.com/Meshinfo) [Oct 8, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10876956)\
\
For all the examples, the index had already been created and did not require updating. However, in a real chat assistant scenario, the index is only created after the user uploads files. It is only at this point that the retrieval tool can be instantiated. Do you have any idea to handle such situations?\
\
1\
\
0 replies\
\
[![@itsihsan](https://avatars.githubusercontent.com/u/35091017?v=4)itsihsan](https://github.com/itsihsan) [Oct 9, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-10892771)\
\
The following two issues need to be addressed within the code:\
\
#### Handling Compound Questions:\
\
1 - When a user asks a compound question (for instance., _What is an agent, and what is prompt engineering?_), the Agent node splits the question into multiple (in this case two) sub-questions (e.g., _What is an agent?_, and _What is prompt engineering?_).\
\
2 - The `retrieve` node retrieves documents for each sub-question, resulting in two tool messages (each containing the retrieved documents for corresponding sub-question in their `content` part).\
\
3 - Currently, the `grade_documents` node is grading the contents of the _last message_ only, i.e., the retrieved documents from the last tool message (ignoring the documents that were retrieved in the earlier tool message(s).)\
\
```notranslate\
last_message = messages[-1]\
docs = last_message.content\
\
```\
\
This content is then graded against the original compound question in the `grade_documents` node, i.e., `question = messages[0].content`.\
\
I believe the following modifications will address this problem for compound questions:\
\
4 - Ensure the grading logic handles multiple sub-questions. This means to generalize the code to ensure that _documents_ retrieved as a result of the `retrieve` node for each _sub-question_ are graded against their corresponding _sub-question_ in the `grade_documents` node.\
\
5 - If all retrieved documents for the compound question are deemed relevant, update the `generate` node to consider all documents, and not just the ones from the last tool message. Currently,\
\
```notranslate\
messages = state["messages"]\
question = messages[0].content\
last_message = messages[-1]\
docs = last_message.content\
\
```\
\
#### Issue with Memory Checkpoint:\
\
1 - When a memory checkpoint is added to the graph as below,\
\
```notranslate\
from langgraph.checkpoint.memory import MemorySaver\
\
memory = MemorySaver()\
graph = workflow.compile(checkpointer=memory)\
\
```\
\
the question, i.e., `question = messages[0].content` will always reference the _first_ question in the conversation, instead of the most recent user question. This causes the _rewrite_ node to engage incorrectly due to the outdated questions.\
\
This can be addressed by capturing the user's question and storing/calling it appropriately as below,\
\
```notranslate\
class AgentState(TypedDict):\
    messages: Annotated[Sequence[BaseMessage], add_messages]\
    user_question: str\
\
```\
\
```notranslate\
def agent(state):\
    print("---CALL AGENT---")\
    messages = state["messages"]\
    user_question = messages[-1].content\
    model = ChatOpenAI(temperature=0, streaming=True, model="gpt-4-turbo")\
    model = model.bind_tools(tools)\
    response = model.invoke(messages)\
    # We return a list, because this will get added to the existing list\
    return {"messages": [response], "user_question":user_question}\
\
```\
\
Calling the stored question in the `generate` node as below:\
\
```notranslate\
def generate(state: State):\
    print("---GENERATE---")\
    question = state["user_question"]\
    # The rest of the code stays the same\
\
```\
\
I would appreciate feedback from anyone who has addressed the first part. If so, please share the updated code.\
\
2\
\
0 replies\
\
[![@kishorekkota](https://avatars.githubusercontent.com/u/18434114?v=4)kishorekkota](https://github.com/kishorekkota) [Oct 31, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11115670)\
\
Trying to implement this with Azure Search and Azure Hosted Open AI. My retrieval call is not being invoked at all and straight getting responses from Open AI vs sourcing from Vector Store.\
\
1\
\
1 reply\
\
[![@kishorekkota](https://avatars.githubusercontent.com/u/18434114?v=4)](https://github.com/kishorekkota)\
\
[kishorekkota](https://github.com/kishorekkota) [Nov 3, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11136363)\
\
Any help would be appreciated. I do not think I am missing any step.\
\
I have two python program created for this.\
\
rag\_assistant.py ( this is the program that creates the LangGraph Workflow.\
\
````notranslate\
# rag_assistant.py\
\
import os\
import uuid\
import logging\
\
os.environ["AZURESEARCH_FIELDS_ID"] = "chunk_id"\
os.environ["AZURESEARCH_FIELDS_CONTENT"] = "chunk"\
os.environ["AZURESEARCH_FIELDS_CONTENT_VECTOR"] = "text_vector"\
\
from typing import Literal\
\
from langchain_openai import AzureChatOpenAI\
from langchain.schema import HumanMessage\
from langgraph.graph import START, END, StateGraph, MessagesState\
from langgraph.prebuilt import ToolNode, tools_condition\
from langgraph.checkpoint.postgres import PostgresSaver\
from langchain_core.output_parsers import StrOutputParser\
from langchain.prompts import PromptTemplate\
from langchain import hub\
\
from db_connection import pool\
from chat_response import ChatBot\
from azure_search import create_vector_store, create_vector_store_tool\
from agent_state import AgentState\
import prettyprinter as pp\
\
logger = logging.getLogger(__name__)\
logger.setLevel(logging.ERROR)\
\
class RAGAIAssistant:\
    def __init__(self, thread_id: str, new_conversation: bool = True):\
        self.azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY")\
        self.azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")\
\
        if not self.azure_openai_api_key:\
            raise ValueError("AZURE_OPENAI_API_KEY environment variable not set.")\
        if not self.azure_openai_endpoint:\
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable not set.")\
\
        self.thread_id = thread_id\
        self.user_message = None\
        self.new_conversation = new_conversation\
\
        # Initialize the language model\
        self.llm = AzureChatOpenAI(\
            deployment_name='gpt-35-turbo',\
            openai_api_key=self.azure_openai_api_key,\
            openai_api_version="2024-05-01-preview",\
            openai_api_type="azure",\
            azure_endpoint=self.azure_openai_endpoint,\
            temperature=0\
        )\
\
        # Create vector store and retriever tool\
        vector_store = create_vector_store()\
        self.retrieval_tool = create_vector_store_tool(vector_store)\
\
        # Bind the retriever tool to the LLM\
        self.model_tool = self.llm.bind_tools([self.retrieval_tool])\
\
        # Set up the workflow\
        self._setup_workflow()\
\
    def _setup_workflow(self):\
        logger.info("Setting up workflow...")\
\
        # Initialize the StateGraph with AgentState\
        workflow = StateGraph(AgentState)\
\
        # Add nodes to the workflow\
        workflow.add_node("agent", self.agent)\
        retrieve_node = ToolNode([self.retrieval_tool])\
        workflow.add_node("retrieve", retrieve_node)\
        workflow.add_node("rewrite", self.rewrite)\
        workflow.add_node("generate", self.generate)\
\
        # Define the workflow edges\
        workflow.add_edge(START, "agent")\
\
        # Conditional edges based on the agent's decision\
        workflow.add_conditional_edges(\
            "agent",\
            tools_condition,\
            {\
                "tools": "retrieve",\
                END: END,\
            },\
        )\
\
        # Conditional edges after retrieval\
        workflow.add_conditional_edges(\
            "retrieve",\
            self.grade_documents,\
            {\
                "generate": "generate",\
                "rewrite": "rewrite",\
            },\
        )\
\
        workflow.add_edge("generate", END)\
        workflow.add_edge("rewrite", "agent")\
\
        # Set up memory with PostgresSaver\
        memory = PostgresSaver(pool)\
        memory.setup()\
        logger.info("Workflow setup completed.")\
\
        self.workflow = workflow.compile(checkpointer=memory)\
\
    def start_new_session(self):\
        self.thread_id = uuid.uuid4().hex\
        self.new_conversation = False\
        logger.info(f"Started new session with thread_id: {self.thread_id}")\
\
    def run(self, user_message: str) -> ChatBot:\
        self.user_message = user_message\
        if self.new_conversation:\
            self.start_new_session()\
        config = {"configurable": {"thread_id": self.thread_id}}\
\
        logger.info(f"Running workflow for message: {user_message}")\
        response_state = self.workflow.invoke(\
            {"messages": [HumanMessage(content=self.user_message)]},\
            config=config\
        )\
\
        messages = response_state.get("messages", [])\
        if messages:\
            last_message = messages[-1].content\
        else:\
            last_message = ""\
\
        response = ChatBot(self.user_message, last_message, self.thread_id)\
\
        return response\
\
    def grade_documents(self, state: MessagesState) -> Literal["generate", "rewrite"]:\
        logger.info("Starting document grading process.")\
\
        class Grade(BaseModel):\
            binary_score: str = Field(description="Relevance score 'yes' or 'no'.")\
\
        try:\
            model = AzureChatOpenAI(\
                deployment_name='gpt-35-turbo',\
                openai_api_key=self.azure_openai_api_key,\
                openai_api_base=self.azure_openai_endpoint,\
                openai_api_version="2024-05-01-preview",\
                openai_api_type="azure",\
                temperature=0\
            )\
            llm_with_tool = model.with_structured_output(Grade)\
\
            prompt = PromptTemplate(\
                template=(\
                    "You are a grader assessing relevance of a retrieved document to a user question.\n"\
                    "Here is the retrieved document:\n{context}\n\n"\
                    "Here is the user question: {question}\n"\
                    "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.\n"\
                    "Give a binary 'yes' or 'no' score to indicate whether the document is relevant to the question."\
                ),\
                input_variables=["context", "question"],\
            )\
\
            chain = prompt | llm_with_tool\
\
            messages = state["messages"]\
            if not messages:\
                logger.error("No messages found in state.")\
                return "rewrite"\
\
            last_message = messages[-1]\
            question = messages[0].content\
            docs = last_message.content\
\
            scored_result = chain.invoke({"question": question, "context": docs})\
            score = scored_result.binary_score.strip().lower()\
\
            logger.info(f"Grading result: {score}")\
\
            if score == "yes":\
                logger.info("Decision: Documents are relevant. Proceeding to generate.")\
                return "generate"\
            else:\
                logger.info("Decision: Documents are not relevant. Proceeding to rewrite.")\
                return "rewrite"\
\
        except Exception as e:\
            logger.error(f"An error occurred during document grading: {e}")\
            return "rewrite"\
\
    def agent(self, state: MessagesState):\
        """\
        Invokes the agent model to generate a response based on the current state. Given\
        the question, it will decide to retrieve using the retriever tool, or simply end.\
\
        Args:\
            state (messages): The current state\
\
        Returns:\
            dict: The updated state with the agent response appended to messages\
        """\
        logger.info("Invoking agent.")\
        try:\
            messages = state["messages"]\
            if not messages:\
                logger.error("No messages found in state.")\
                return {"messages": []}\
\
            pp.pprint(self.model_tool)\
            response = self.model_tool.invoke(messages)\
            logger.info("Agent invoked successfully.")\
\
            print(response.pretty_print())\
\
            return {"messages": [response]}\
\
        except Exception as e:\
            logger.error(f"An error occurred in agent: {e}")\
            return {"messages": []}\
\
    def rewrite(self, state: MessagesState):\
        logger.info("Starting query rewrite process.")\
\
        try:\
            messages = state["messages"]\
            if not messages:\
                logger.error("No messages found in state.")\
                return {"messages": []}\
\
            question = messages[0].content\
\
            msg = [\
                HumanMessage(\
                    content=(\
                        "Look at the input and try to reason about the underlying semantic intent/meaning.\n"\
                        "Here is the initial question:\n"\
                        "-------\n"\
                        f"{question}\n"\
                        "-------\n"\
                        "Formulate an improved question:"\
                    ),\
                )\
            ]\
\
            model = AzureChatOpenAI(\
                deployment_name='gpt-35-turbo',\
                openai_api_key=self.azure_openai_api_key,\
                openai_api_base=self.azure_openai_endpoint,\
                openai_api_version="2024-05-01-preview",\
                openai_api_type="azure",\
                temperature=0\
            )\
            response = model.invoke(msg)\
            logger.info("Query rewritten successfully.")\
\
            return {"messages": [response]}\
\
        except Exception as e:\
            logger.error(f"An error occurred during query rewrite: {e}")\
            return {"messages": []}\
\
    def generate(self, state: MessagesState):\
        logger.info("Starting answer generation process.")\
\
        try:\
            messages = state["messages"]\
            if not messages:\
                logger.error("No messages found in state.")\
                return {"messages": []}\
\
            question = messages[0].content\
            last_message = messages[-1]\
            docs = last_message.content\
\
            prompt = hub.pull("rlm/rag-prompt")\
            logger.debug("Prompt pulled from hub.")\
\
            model = AzureChatOpenAI(\
                deployment_name='gpt-35-turbo',\
                openai_api_key=self.azure_openai_api_key,\
                openai_api_base=self.azure_openai_endpoint,\
                openai_api_version="2024-05-01-preview",\
                openai_api_type="azure",\
                temperature=0\
            )\
\
            rag_chain = prompt | model | StrOutputParser()\
\
            response = rag_chain.invoke({"context": docs, "question": question})\
            logger.info("Answer generated successfully.")\
\
            return {"messages": [response]}\
\
        except Exception as e:\
            logger.error(f"An error occurred during answer generation: {e}")\
            return {"messages": []}\
\
if __name__ == "__main__":\
    logging.basicConfig(level=logging.INFO)\
\
\
    rag_assistant = RAGAIAssistant(thread_id="test_thread_id", new_conversation=True)\
    #rag_assistant.retriever_tool(" What is the leave policy ? ")\
    create_vector_store().search(" What is the leave policy ? ",search_type='similarity')\
    response = rag_assistant.run("What is process for taking extended leave in New York?")\
    print(f"Assistant: {response}")\
\
    ```\
\
Azure_search.py which creates Azure Search as retriever tool.\
\
````\
\
# azure\_search.py\
\
import os\
\
import logging\
\
os.environ\["AZURESEARCH\_FIELDS\_ID"\] = "chunk\_id"\
\
os.environ\["AZURESEARCH\_FIELDS\_CONTENT"\] = "chunk"\
\
os.environ\["AZURESEARCH\_FIELDS\_CONTENT\_VECTOR"\] = "text\_vector"\
\
from langchain\_community.vectorstores.azuresearch import AzureSearch\
\
from langchain\_openai import AzureOpenAIEmbeddings\
\
from langchain.tools.retriever import create\_retriever\_tool\
\
from azure.identity import DefaultAzureCredential\
\
from langchain\_core.tools import tool\
\
from azure.search.documents.indexes.models import SimpleField\
\
# Configure logging\
\
logging.basicConfig(level=logging.ERROR)\
\
logger = logging.getLogger( **name**)\
\
def create\_vector\_store() -> AzureSearch:\
\
"""\
\
Creates and returns an AzureSearch vector store instance.\
\
```notranslate\
Returns:\
    AzureSearch: An instance of the AzureSearch vector store.\
\
Raises:\
    ValueError: If required environment variables are missing.\
"""\
print("Creating AzureSearch vector store...")\
# Retrieve environment variables\
azure_search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')\
azure_search_key = os.getenv('AZURE_SEARCH_KEY')\
search_index_name = os.getenv('SEARCH_INDEX_NAME')\
embedding_model_name = os.getenv('EMBEDDING_MODEL_NAME', 'text-embedding-3-large')\
\
print(azure_search_endpoint, azure_search_key, search_index_name, embedding_model_name)\
\
if not azure_search_endpoint or not azure_search_key or not search_index_name:\
    logger.error("Missing Azure Search configuration environment variables.")\
    raise ValueError("Missing Azure Search configuration environment variables.")\
\
try:\
    # Initialize embeddings\
    embeddings = AzureOpenAIEmbeddings(model=embedding_model_name,azure_deployment="text-embedding-3-large")\
\
    # Create the vector store\
    vector_store = AzureSearch(\
        azure_search_endpoint=azure_search_endpoint,\
        azure_search_key=azure_search_key,\
        index_name=search_index_name,\
        embedding_function=embeddings.embed_query,\
        vector_field_name="nasa-ai-vector-1730294759623",\
        search_type="similarity",\
        fields=[SimpleField(id="text_vector", name="text_vector", type="Edm.String", key=True)]\
    )\
\
    logger.info("AzureSearch vector store created successfully.")\
    return vector_store\
\
except Exception as e:\
    logger.error(f"An error occurred while creating the vector store: {e}")\
    raise\
\
```\
\
def create\_vector\_store\_tool(vector\_store: AzureSearch):\
\
"""\
\
Creates and returns a retriever tool from the provided vector store.\
\
```notranslate\
Args:\
    vector_store (AzureSearch): The vector store instance.\
\
Returns:\
    Tool: A retriever tool instance.\
"""\
print("Retrieving documents for query: {query}")\
try:\
    retriever_ = vector_store.as_retriever()\
\
    retrieve_policy_document = create_retriever_tool(\
        retriever=retriever_,\
        name="retrieve_policy_document",\
        description="Search and Return  tool for HR Related questions and Leave Policy in NewYork.",\
    )\
    logger.info("Retriever tool created successfully.")\
\
    print(retrieve_policy_document)\
    print(type(retrieve_policy_document))\
    print("--------------------------------")\
    return retrieve_policy_document\
\
except Exception as e:\
    logger.error(f"An error occurred while creating the retriever tool: {e}")\
    raise\
\
```\
\
def test\_query\_vector\_store():\
\
"""\
\
Tests querying the AzureCognitiveSearch vector store directly.\
\
"""\
\
print("--------------------------------")\
\
print("Testing query on AzureCognitiveSearch vector store...")\
\
try:\
\
\# Create the vector store\
\
vector\_store = create\_vector\_store()\
\
```notranslate\
    # Get the retriever from the vector store\
    retriever = vector_store.as_retriever()\
\
    # Define a test query\
    test_query = "What is the company's leave policy?"\
\
    print(f"Running test query: {test_query}")\
\
    # Retrieve relevant documents\
    results = retriever.get_relevant_documents(test_query)\
\
    # Print the retrieved documents\
    if results:\
        print(f"Retrieved {len(results)} documents:")\
        for i, doc in enumerate(results, start=1):\
            print(f"\nDocument {i} Content:\n{doc.page_content}\n")\
    else:\
        print("No documents were retrieved.")\
\
except Exception as e:\
    logger.error(f"An error occurred during the test query: {e}")\
\
```\
\
def test\_retriever\_tool():\
\
"""\
\
Tests the retriever tool created from the vector store.\
\
"""\
\
logger.info("Testing the retriever tool...")\
\
try:\
\
\# Create the vector store\
\
vector\_store = create\_vector\_store()\
\
```notranslate\
    # Create the retriever tool\
    retriever_tool = create_vector_store_tool(vector_store)\
\
    # Define a test query\
    test_query = "What is the company's leave policy?"\
\
    results = retriever_tool.invoke(test_query)\
\
    logger.info(f"Running test query using the retriever tool: {test_query}")\
\
    print(results)\
\
    # import inspect\
\
    # logger.info("Listing all methods of retriever_tool:")\
    # methods = [method_name for method_name in dir(retriever_tool)\
    #            if callable(getattr(retriever_tool, method_name)) and not method_name.startswith("__")]\
    # for method_name in methods:\
    #     print(method_name)\
\
    # # Alternatively, using inspect.getmembers to get more detailed information\
    # logger.info("Detailed inspection of retriever_tool methods and attributes:")\
    # for name, member in inspect.getmembers(retriever_tool):\
    #     if inspect.ismethod(member) or inspect.isfunction(member):\
    #         print(f"Method: {name}")\
    #     elif not name.startswith("__"):\
    #         print(f"Attribute: {name}")\
\
    # Use the retriever tool to retrieve relevant documents\
    # results = retriever_tool.retriever.get_relevant_documents(test_query)\
\
    # Print the retrieved documents\
    # if results:\
    #     logger.info(f"Retrieved {len(results)} documents:")\
    #     for i, doc in enumerate(results, start=1):\
    #         print(doc)\
    # else:\
    #     logger.info("No documents were retrieved.")\
\
except Exception as e:\
    logger.error(f"An error occurred during the retriever tool test: {e}")\
\
```\
\
if **name** == " **main**":\
\
logger.info("Starting test execution for azure\_search.py...")\
\
#test\_query\_vector\_store()\
\
test\_retriever\_tool()\
\
```notranslate\
I am successfully validate Azure search retriever tool independently. However, I am getting invalid tool call when trying to do this.\
\
There two different issue I am seeing depending on the code. If i create my retriever like below, then it executes fine, but does not invoke retriever tool, instead it returns reponse from LLM without invokving the tool for querying my RAG source.\
\
```\
\
```notranslate\
    retrieve_policy_document = create_retriever_tool(\
        retriever=retriever_,\
        name="retriever",\
        description="Search and Return  tool for HR Related questions and Leave Policy in NewYork.",\
    )\
\
```\
\
```notranslate\
\
When I change the name='retriever_policy_document', it runs into an error saying invalid tool call, as it is trying to find a method called retriever for tool call via function.\
\
```\
\
```notranslate\
    retrieve_policy_document = create_retriever_tool(\
        retriever=retriever_,\
        name="retriever_policy_document",\
        description="Search and Return  tool for HR Related questions and Leave Policy in NewYork.",\
    )\
\
```\
\
```notranslate\
\
Lets me know if more details are needed.\
\
```\
\
[![@tsuzukia21](https://avatars.githubusercontent.com/u/132349459?u=27d42b2d3bb3b369935980d15d42e3c9bbc8fd42&v=4)tsuzukia21](https://github.com/tsuzukia21) [Nov 6, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11162938)\
\
I demonstrated an article, but the last message is a HumanMessage instead of an AIMessage. Is this the correct behavior? When I want to accumulate conversation history, this specification requires editing.\
\
1\
\
0 replies\
\
[![@pankajxyz](https://avatars.githubusercontent.com/u/3924040?v=4)pankajxyz](https://github.com/pankajxyz) [Dec 3, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11445243)\
\
I used Bedrock with Claude. When retrieved docs are not relevant to question, it tries to reformulate the question. However, the response format from "rewrite" is not in correct format for "agent" to understand. Do I need to modify the response using regex etc or is there an elegant way? Below is the error, I am getting:\
\
EventStreamError('An error occurred (validationException) when calling the InvokeModelWithResponseStream operation: Your API request included an `assistant` message in the final position, which would pre-fill the `assistant` response. When using tools, pre-filling the `assistant` response is not supported.')Traceback (most recent call last):\
\
........\
\
botocore.exceptions.EventStreamError: An error occurred (validationException) when calling the InvokeModelWithResponseStream operation: Your API request included an `assistant` message in the final position, which would pre-fill the `assistant` response. When using tools, pre-filling the `assistant` response is not supported.\
\
1\
\
1 reply\
\
[![@KKllwetr](https://avatars.githubusercontent.com/u/44864417?v=4)](https://github.com/KKllwetr)\
\
[KKllwetr](https://github.com/KKllwetr) [Feb 26](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12331585)\
\
The elegant solution is to just write a good prompt and say what you want. For example, rewrite the previous request and give me a new detailed request in one sentence.\
\
[![@kush2022](https://avatars.githubusercontent.com/u/97630619?u=7cae4ff570c23b9857e4875d14c9c7f4a53f9766&v=4)kush2022](https://github.com/kush2022) [Dec 11, 2024](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11530350)\
\
I want to get the final output when am using print.\
\
``\
`import pprint``\
\
`\
`\
\
``inputs = {\
"messages": [\
("user", "What does Lilian Weng say about the types of agent memory?"),\
]\
}\
for output in graph.stream(inputs):\
for key, value in output.items():\
pprint.pprint(f"Output from node '{key}':")\
pprint.pprint("---")\
pprint.pprint(value, indent=2, width=80, depth=None)\
pprint.pprint("\n---\n") `\
``\
\
am getting this out:\
\
> ---CALL AGENT---\
>\
> "Output from node 'agent':"\
>\
> '---'\
>\
> { 'messages': \[ AIMessage(content='', additional\_kwargs={'tool\_calls': \[{'id': 'call\_j1pe', 'function': {'arguments': '{"query": "Lilian Weng agent memory types"}', 'name': 'retrieve\_blog\_posts'}, 'type': 'function'}\]}, response\_metadata={'token\_usage': {'completion\_tokens': 22, 'prompt\_tokens': 280, 'total\_tokens': 302, 'completion\_time': 0.08, 'prompt\_time': 0.038491926, 'queue\_time': 0.18712725, 'total\_time': 0.118491926}, 'model\_name': 'llama-3.3-70b-versatile', 'system\_fingerprint': 'fp\_4e32347616', 'finish\_reason': 'tool\_calls', 'logprobs': None}, id='run-fbf0acc1-b2c2-4ed8-bdf7-2bc0f86d83eb-0', tool\_calls=\[{'name': 'retrieve\_blog\_posts', 'args': {'query': 'Lilian Weng agent memory types'}, 'id': 'call\_j1pe', 'type': 'tool\_call'}\], usage\_metadata={'input\_tokens': 280, 'output\_tokens': 22, 'total\_tokens': 302})\]}\
>\
> '\\n---\\n'\
>\
> ---CHECK RELEVANCE---\
>\
> ---DECISION: DOCS NOT RELEVANT---\
>\
> no\
>\
> "Output from node 'retrieve':"\
>\
> '---'\
>\
> { 'messages': \[ ToolMessage(content='', name='retrieve\_blog\_posts', id='634613d9-6458-48a6-94fd-3b5f1367bedb', tool\_call\_id='call\_j1pe')\]}\
>\
> '\\n---\\n'\
>\
> ---TRANSFORM QUERY---\
>\
> "Output from node 'rewrite':"\
>\
> '---'\
>\
> { 'messages': \[ AIMessage(content='To create an improved question, let's break down the initial query and consider how it can be refined for better clarity and specificity:\\n\\n1. **Subject**: The subject of the question is Lilian Weng, presumably a researcher or expert in a field related to agents and their memory types.\\n2. **Topic**: The topic is about the types of agent memory, which suggests a context of artificial intelligence, cognitive science, or a related field where "agents" can refer to software programs, robots, or other entities that can perceive their environment and take actions.\\n3. **Information Sought**: The question seeks information on what Lilian Weng has stated or written about the types of agent memory.\\n\\nGiven these components, an improved version of the question could be more specific about the context or the type of information being sought. For example:\\n\\n- **Improved Question**: What specific types of agent memory does Lilian Weng discuss in her research or publications, and how does she categorize or differentiate between them?\\n\\nThis reformulated question aims to:\\n- Specify that the question is about Lilian Weng's research or publications, which could help in narrowing down the sources to consult.\\n- Ask for specific types of agent memory, which could elicit a more detailed and informative response.\\n- Inquire about how Lilian Weng categorizes or differentiates between these types, which could provide insight into her perspective or contributions to the field.\\n\\nBy refining the question in this way, the inquiry becomes more targeted and is likely to yield a more precise and useful answer.', additional\_kwargs={}, response\_metadata={'token\_usage': {'completion\_tokens': 313, 'prompt\_tokens': 90, 'total\_tokens': 403, 'completion\_time': 1.138181818, 'prompt\_time': 0.012991012, 'queue\_time': 0.007083786000000002, 'total\_time': 1.15117283}, 'model\_name': 'llama-3.3-70b-versatile', 'system\_fingerprint': 'fp\_4e32347616', 'finish\_reason': 'stop', 'logprobs': None}, id='run-b734b154-1151-4c98-927e-534b30264bb3-0', usage\_metadata={'input\_tokens': 90, 'output\_tokens': 313, 'total\_tokens': 403})\]}\
>\
> '\\n---\\n'\
>\
> ---CALL AGENT---\
>\
> "Output from node 'agent':"\
>\
> '---'\
>\
> { 'messages': \[ AIMessage(content='', additional\_kwargs={}, response\_metadata={'token\_usage': {'completion\_tokens': 1, 'prompt\_tokens': 624, 'total\_tokens': 625, 'completion\_time': 0.003636364, 'prompt\_time': 0.079468607, 'queue\_time': -9223372036.934244, 'total\_time': 0.083104971}, 'model\_name': 'llama-3.3-70b-versatile', 'system\_fingerprint': 'fp\_fcc3b74982', 'finish\_reason': 'stop', 'logprobs': None}, id='run-1289a22f-ae47-4a70-9a91-9855fe1634e9-0', usage\_metadata={'input\_tokens': 624, 'output\_tokens': 1, 'total\_tokens': 625})\]}\
>\
> '\\n---\\n'\
\
when I use print:\
\
`\
for ouput in graph.stream(inputs): for key, value in output.items(): if key == 'generate': print(value['messages'][0])\
`\
\
am getting this output:\
\
> ---CALL AGENT---\
>\
> ---CHECK RELEVANCE---\
>\
> ---DECISION: DOCS NOT RELEVANT---\
>\
> no\
>\
> ---TRANSFORM QUERY---\
>\
> ---CALL AGENT---\
\
how can I get only the message generated as the final answer ?\
\
1\
\
1 reply\
\
[![@KKllwetr](https://avatars.githubusercontent.com/u/44864417?v=4)](https://github.com/KKllwetr)\
\
[KKllwetr](https://github.com/KKllwetr) [Feb 26](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12331563)\
\
```\
inputs = {\
    "messages": [\
        ("user", "What does Lilian Weng say about the types of agent memory?"),\
    ]\
}\
for output in graph.stream(inputs):\
    for key, value in output.items():\
        pass\
        #pprint(f"Output from node '{key}':")\
        #pprint("---")\
       #pprint(value, indent=2, width=80, depth=None)\
    #pprint("\n---\n")\
value['messages'][0] # your final answer\
```\
\
[![@nterizakis](https://avatars.githubusercontent.com/u/5749463?v=4)nterizakis](https://github.com/nterizakis) [Jan 13](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11823984)\
\
I might be missing something but :\
\
# Post-processing\
\
```notranslate\
def format_docs(docs):\
    return "\n\n".join(doc.page_content for doc in docs)\
\
```\
\
does not tie with:\
\
```notranslate\
# Chain\
rag_chain = prompt | llm | StrOutputParser()\
\
```\
\
I believe the StrOutputParser cal should have been StrOutputParser(format\_docs). Otherwise, how does StrOutputParser know how to parse? The function has not been made into a runable.\
\
This would explain why people are getting errors as well.\
\
1\
\
2 replies\
\
[![@bnbabu55](https://avatars.githubusercontent.com/u/56356022?v=4)](https://github.com/bnbabu55)\
\
[bnbabu55](https://github.com/bnbabu55) [Jan 14](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11827389)\
\
I think format\_docs has to do with prompt not StrOutputParser, to prepare the prompt you extract the page\_content text from the document and then call LLM with that prompt, you should be able to get the output.\
\
StrOutputParser() does not take any arguments, you just call and your response will be a string.\
\
[![@nterizakis](https://avatars.githubusercontent.com/u/5749463?v=4)](https://github.com/nterizakis)\
\
[nterizakis](https://github.com/nterizakis) [Jan 14](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-11830121)\
\
Either I am blind, or I cannot see where it is called then (format\_docs that is).\
\
It would appear that StrOutputParser() does take parameters: [https://python.langchain.com/api\_reference/core/output\_parsers/langchain\_core.output\_parsers.string.StrOutputParser.html](https://python.langchain.com/api_reference/core/output_parsers/langchain_core.output_parsers.string.StrOutputParser.html)\
\
I have used a formatting function for it in the past, if I recall. Will scour my code to find it.\
\
👍1\
\
[![@rukawa917](https://avatars.githubusercontent.com/u/61721762?v=4)rukawa917](https://github.com/rukawa917) [Feb 22](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12287322)\
\
I am trying this with ollama models and the flow just ends at agent level. Can this happen in other models?\
\
---CALL AGENT---\
\
content='' additional\_kwargs={} response\_metadata={'model': 'mistral', 'created\_at': '2025-02-22T17:40:46.684942Z', 'done': True, 'done\_reason': 'stop', 'total\_duration': 24743576875, 'load\_duration': 549610958, 'prompt\_eval\_count': 108, 'prompt\_eval\_duration': 2591000000, 'eval\_count': 277, 'eval\_duration': 21600000000, 'message': Message(role='assistant', content='', images=None, tool\_calls=None)} id='run-e62b7f03-167c-4a20-9737-45d4bc3ddfbb-0' tool\_calls=\[{'name': 'retrieve\_blog\_posts', 'args': {'query': 'types of agent memory'}, 'id': '16df67b7-d8dd-47d9-9357-809c9bd419da', 'type': 'tool\_call'}\] usage\_metadata={'input\_tokens': 108, 'output\_tokens': 277, 'total\_tokens': 385}\
\
"Output from node 'agent':"\
\
'---'\
\
{ 'messages': \[ AIMessage(content='', additional\_kwargs={}, response\_metadata={'model': 'mistral', 'created\_at': '2025-02-22T17:40:46.684942Z', 'done': True, 'done\_reason': 'stop', 'total\_duration': 24743576875, 'load\_duration': 549610958, 'prompt\_eval\_count': 108, 'prompt\_eval\_duration': 2591000000, 'eval\_count': 277, 'eval\_duration': 21600000000, 'message': Message(role='assistant', content='', images=None, tool\_calls=None)}, id='run-e62b7f03-167c-4a20-9737-45d4bc3ddfbb-0', tool\_calls=\[{'name': 'retrieve\_blog\_posts', 'args': {'query': 'types of agent memory'}, 'id': '16df67b7-d8dd-47d9-9357-809c9bd419da', 'type': 'tool\_call'}\], usage\_metadata={'input\_tokens': 108, 'output\_tokens': 277, 'total\_tokens': 385})\]}\
\
'\\n---\\n'\
\
1\
\
2 replies\
\
[![@KKllwetr](https://avatars.githubusercontent.com/u/44864417?v=4)](https://github.com/KKllwetr)\
\
[KKllwetr](https://github.com/KKllwetr) [Feb 26](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12331510)\
\
It depends on what kind of retriever you're using, specifically which model you get your embeddings from. I recommend looking at the embedding model and trying to get your responses by calling it directly. It is also recommended to remove ToolNode and manually write your own function to process the request and retrieve the documents.\
\
[![@rukawa917](https://avatars.githubusercontent.com/u/61721762?v=4)](https://github.com/rukawa917)\
\
[rukawa917](https://github.com/rukawa917) [Feb 28](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12350975)\
\
Thx for the suggestion. I will try and share how it goes.\
\
[![@hkailee](https://avatars.githubusercontent.com/u/13162113?u=12acc42efcb3629c3e502d72b27f5b010aa4e2fc&v=4)hkailee](https://github.com/hkailee) [Mar 11](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12456507)\
\
I am just being a bit funny here - Is the code solution generated by AI ? It doesn't work as expected.\
\
1\
\
0 replies\
\
[![@tiwarikaran](https://avatars.githubusercontent.com/u/66107781?u=7bb1e5e4440db49d61c2ea33e25c62600296600f&v=4)tiwarikaran](https://github.com/tiwarikaran) [Mar 12](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12470863)\
\
Has anyone tried this out on Dataiku using LLM Mesh? Seems like there are gonna be fundamental changes.\
\
1\
\
0 replies\
\
[![@khteh](https://avatars.githubusercontent.com/u/3871483?u=8434f4d49eefb670c9cd64152fad5e6c504fc459&v=4)khteh](https://github.com/khteh) [Mar 21](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12572578)\
\
Anybody using Google VertexAI for this tutorial? I use:\
\
```notranslate\
self._llm = init_chat_model("gemini-2.0-flash", model_provider="google_vertexai", streaming=True)\
\
```\
\
And in `Agent`, it has problem with the extra arguments in the `HumanMessage` which is inherent of the `BaseMessage`, therefore the following error:\
\
```notranslate\
2025-03-21 12:51:19 WARNING  Retrying langchain_google_vertexai.chat_models._acompletion_with_retry.<locals>._completion_with_retry_inner in 4.0 seconds as it raised InvalidArgument: 400 Request contains an invalid argument..\
\
```\
\
1\
\
2 replies\
\
[![@khteh](https://avatars.githubusercontent.com/u/3871483?u=8434f4d49eefb670c9cd64152fad5e6c504fc459&v=4)](https://github.com/khteh)\
\
[khteh](https://github.com/khteh) [Mar 21](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12572599)\
\
```notranslate\
=== Agent ===\
2025-03-21 12:47:17 DEBUG    state: {'messages': [HumanMessage(content='Hello, who are you?', additional_kwargs={}, response_metadata={}, id='2f89e180-a290-489d-95d9-cd74708a07f7')], 'is_last_step': False}\
2025-03-21 12:47:17 DEBUG    https://api.smith.langchain.com:443 "GET /info HTTP/1.1" 200 672\
2025-03-21 12:47:17 DEBUG    Starting new HTTPS connection (1): api.smith.langchain.com:443\
2025-03-21 12:47:18 DEBUG    Using AsyncIOEngine.POLLER as I/O engine\
2025-03-21 12:47:18 DEBUG    Starting new HTTPS connection (1): oauth2.googleapis.com:443\
2025-03-21 12:47:18 DEBUG    https://api.smith.langchain.com:443 "POST /runs/multipart HTTP/1.1" 202 34\
\
2025-03-21 12:51:18 DEBUG    https://oauth2.googleapis.com:443 "POST /token HTTP/1.1" 200 None\
2025-03-21 12:51:19 WARNING  Retrying langchain_google_vertexai.chat_models._acompletion_with_retry.<locals>._completion_with_retry_inner in 4.0 seconds as it raised InvalidArgument: 400 Request contains an invalid argument..\
\
```\
\
[![@khteh](https://avatars.githubusercontent.com/u/3871483?u=8434f4d49eefb670c9cd64152fad5e6c504fc459&v=4)](https://github.com/khteh)\
\
[khteh](https://github.com/khteh) [Mar 21](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12572607)\
\
If the code is written to retrieve the `content` s of the messages to `invoke`, then there will be performance implication.\
\
[![@tenghaha](https://avatars.githubusercontent.com/u/27665473?v=4)tenghaha](https://github.com/tenghaha) [8 days ago](https://github.com/langchain-ai/langgraph/discussions/722#discussioncomment-12852827)\
\
In a multi-turn dialogue scenario, what is the structure of the `state["messages"]` passed between nodes? Can I still use numeric indexing as in `generate` to locate user input and document content? Or should I adopt other methods for positioning?\
\
```\
print("---GENERATE---")\
messages = state["messages"]\
question = messages[0].content\
last_message = messages[-1]\
docs = last_message.content\
```\
\
1\
\
0 replies\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Frag%2Flanggraph_agentic_rag%2F)