[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/#corrective-rag-crag)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/rag/langgraph_crag.ipynb "Edit this page")

# Corrective RAG (CRAG) [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/\#corrective-rag-crag "Permanent link")

Corrective-RAG (CRAG) is a strategy for RAG that incorporates self-reflection / self-grading on retrieved documents.

In the paper [here](https://arxiv.org/pdf/2401.15884.pdf), a few steps are taken:

- If at least one document exceeds the threshold for relevance, then it proceeds to generation
- Before generation, it performs knowledge refinement
- This partitions the document into "knowledge strips"
- It grades each strip, and filters our irrelevant ones
- If all documents fall below the relevance threshold or if the grader is unsure, then the framework seeks an additional datasource
- It will use web search to supplement retrieval

We will implement some of these ideas from scratch using [LangGraph](https://langchain-ai.github.io/langgraph/):

- Let's skip the knowledge refinement phase as a first pass. This can be added back as a node, if desired.
- If _any_ documents are irrelevant, let's opt to supplement retrieval with web search.
- We'll use [Tavily Search](https://python.langchain.com/docs/integrations/tools/tavily_search/) for web search.
- Let's use query re-writing to optimize the query for web search.

![Screenshot 2024-04-01 at 9.28.30 AM.png](<Base64-Image-Removed>)

## Setup [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/\#setup "Permanent link")

First, let's download our required packages and set our API keys

```md-code__content
! pip install langchain_community tiktoken langchain-openai langchainhub chromadb langchain langgraph tavily-python

```

```md-code__content
import getpass
import os

def _set_env(key: str):
    if key not in os.environ:
        os.environ[key] = getpass.getpass(f"{key}:")

_set_env("OPENAI_API_KEY")
_set_env("TAVILY_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Create Index [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/\#create-index "Permanent link")

Let's index 3 blog posts.

API Reference: [RecursiveCharacterTextSplitter](https://python.langchain.com/api_reference/text_splitters/character/langchain_text_splitters.character.RecursiveCharacterTextSplitter.html) \| [WebBaseLoader](https://python.langchain.com/api_reference/community/document_loaders/langchain_community.document_loaders.web_base.WebBaseLoader.html) \| [Chroma](https://python.langchain.com/api_reference/community/vectorstores/langchain_community.vectorstores.chroma.Chroma.html) \| [OpenAIEmbeddings](https://python.langchain.com/api_reference/openai/embeddings/langchain_openai.embeddings.base.OpenAIEmbeddings.html)

```md-code__content
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

urls = [\
    "https://lilianweng.github.io/posts/2023-06-23-agent/",\
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",\
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",\
]

docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
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

## LLMs [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/\#llms "Permanent link")

Using Pydantic with LangChain

This notebook uses Pydantic v2 `BaseModel`, which requires `langchain-core >= 0.3`. Using `langchain-core < 0.3` will result in errors due to mixing of Pydantic v1 and v2 `BaseModels`.


API Reference: [ChatPromptTemplate](https://python.langchain.com/api_reference/core/prompts/langchain_core.prompts.chat.ChatPromptTemplate.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html)

```md-code__content
### Retrieval Grader

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field

# Data model
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

# LLM with function call
llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
structured_llm_grader = llm.with_structured_output(GradeDocuments)

# Prompt
system = """You are a grader assessing relevance of a retrieved document to a user question. \n
    If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
grade_prompt = ChatPromptTemplate.from_messages(
    [\
        ("system", system),\
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),\
    ]
)

retrieval_grader = grade_prompt | structured_llm_grader
question = "agent memory"
docs = retriever.invoke(question)
doc_txt = docs[1].page_content
print(retrieval_grader.invoke({"question": question, "document": doc_txt}))

```

```md-code__content
binary_score='yes'

```

API Reference: [StrOutputParser](https://python.langchain.com/api_reference/core/output_parsers/langchain_core.output_parsers.string.StrOutputParser.html)

```md-code__content
### Generate

from langchain import hub
from langchain_core.output_parsers import StrOutputParser

# Prompt
prompt = hub.pull("rlm/rag-prompt")

# LLM
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Chain
rag_chain = prompt | llm | StrOutputParser()

# Run
generation = rag_chain.invoke({"context": docs, "question": question})
print(generation)

```

```md-code__content
The design of generative agents combines LLM with memory, planning, and reflection mechanisms to enable agents to behave conditioned on past experience. Memory stream is a long-term memory module that records a comprehensive list of agents' experience in natural language. Short-term memory is utilized for in-context learning, while long-term memory allows agents to retain and recall information over extended periods.

```

```md-code__content
### Question Re-writer

# LLM
llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

# Prompt
system = """You a question re-writer that converts an input question to a better version that is optimized \n
     for web search. Look at the input and try to reason about the underlying semantic intent / meaning."""
re_write_prompt = ChatPromptTemplate.from_messages(
    [\
        ("system", system),\
        (\
            "human",\
            "Here is the initial question: \n\n {question} \n Formulate an improved question.",\
        ),\
    ]
)

question_rewriter = re_write_prompt | llm | StrOutputParser()
question_rewriter.invoke({"question": question})

```

```md-code__content
'What is the role of memory in artificial intelligence agents?'

```

## Web Search Tool [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/\#web-search-tool "Permanent link")

API Reference: [TavilySearchResults](https://python.langchain.com/api_reference/community/tools/langchain_community.tools.tavily_search.tool.TavilySearchResults.html)

```md-code__content
### Search

from langchain_community.tools.tavily_search import TavilySearchResults

web_search_tool = TavilySearchResults(k=3)

```

## Create Graph [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/\#create-graph "Permanent link")

Now let's create our graph that will use CRAG

### Define Graph State [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/\#define-graph-state "Permanent link")

```md-code__content
from typing import List

from typing_extensions import TypedDict

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        web_search: whether to add search
        documents: list of documents
    """

    question: str
    generation: str
    web_search: str
    documents: List[str]

```

API Reference: [Document](https://python.langchain.com/api_reference/core/documents/langchain_core.documents.base.Document.html)

```md-code__content
from langchain.schema import Document

def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]

    # Retrieval
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}

def generate(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    # RAG generation
    generation = rag_chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}

def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]

    # Score each doc
    filtered_docs = []
    web_search = "No"
    for d in documents:
        score = retrieval_grader.invoke(
            {"question": question, "document": d.page_content}
        )
        grade = score.binary_score
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            web_search = "Yes"
            continue
    return {"documents": filtered_docs, "question": question, "web_search": web_search}

def transform_query(state):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """

    print("---TRANSFORM QUERY---")
    question = state["question"]
    documents = state["documents"]

    # Re-write question
    better_question = question_rewriter.invoke({"question": question})
    return {"documents": documents, "question": better_question}

def web_search(state):
    """
    Web search based on the re-phrased question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with appended web results
    """

    print("---WEB SEARCH---")
    question = state["question"]
    documents = state["documents"]

    # Web search
    docs = web_search_tool.invoke({"query": question})
    web_results = "\n".join([d["content"] for d in docs])
    web_results = Document(page_content=web_results)
    documents.append(web_results)

    return {"documents": documents, "question": question}

### Edges

def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    print("---ASSESS GRADED DOCUMENTS---")
    state["question"]
    web_search = state["web_search"]
    state["documents"]

    if web_search == "Yes":
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"

```

### Compile Graph [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/\#compile-graph "Permanent link")

The just follows the flow we outlined in the figure above.

API Reference: [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START)

```md-code__content
from langgraph.graph import END, StateGraph, START

workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("retrieve", retrieve)  # retrieve
workflow.add_node("grade_documents", grade_documents)  # grade documents
workflow.add_node("generate", generate)  # generatae
workflow.add_node("transform_query", transform_query)  # transform_query
workflow.add_node("web_search_node", web_search)  # web search

# Build graph
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    },
)
workflow.add_edge("transform_query", "web_search_node")
workflow.add_edge("web_search_node", "generate")
workflow.add_edge("generate", END)

# Compile
app = workflow.compile()

```

## Use the graph [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/\#use-the-graph "Permanent link")

```md-code__content
from pprint import pprint

# Run
inputs = {"question": "What are the types of agent memory?"}
for output in app.stream(inputs):
    for key, value in output.items():
        # Node
        pprint(f"Node '{key}':")
        # Optional: print full state at each node
        # pprint.pprint(value["keys"], indent=2, width=80, depth=None)
    pprint("\n---\n")

# Final generation
pprint(value["generation"])

```

```md-code__content
---RETRIEVE---
"Node 'retrieve':"
'\n---\n'
---CHECK DOCUMENT RELEVANCE TO QUESTION---
---GRADE: DOCUMENT NOT RELEVANT---
---GRADE: DOCUMENT NOT RELEVANT---
---GRADE: DOCUMENT RELEVANT---
---GRADE: DOCUMENT RELEVANT---
"Node 'grade_documents':"
'\n---\n'
---ASSESS GRADED DOCUMENTS---
---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---
---TRANSFORM QUERY---
"Node 'transform_query':"
'\n---\n'
---WEB SEARCH---
"Node 'web_search_node':"
'\n---\n'
---GENERATE---
"Node 'generate':"
'\n---\n'
"Node '__end__':"
'\n---\n'
('Agents possess short-term memory, which is utilized for in-context learning, '
 'and long-term memory, allowing them to retain and recall vast amounts of '
 'information over extended periods. Some experts also classify working memory '
 'as a distinct type, although it can be considered a part of short-term '
 'memory in many cases.')

```

```md-code__content
from pprint import pprint

# Run
inputs = {"question": "How does the AlphaCodium paper work?"}
for output in app.stream(inputs):
    for key, value in output.items():
        # Node
        pprint(f"Node '{key}':")
        # Optional: print full state at each node
        # pprint.pprint(value["keys"], indent=2, width=80, depth=None)
    pprint("\n---\n")

# Final generation
pprint(value["generation"])

```

```md-code__content
---RETRIEVE---
"Node 'retrieve':"
'\n---\n'
---CHECK DOCUMENT RELEVANCE TO QUESTION---
---GRADE: DOCUMENT NOT RELEVANT---
---GRADE: DOCUMENT NOT RELEVANT---
---GRADE: DOCUMENT NOT RELEVANT---
---GRADE: DOCUMENT RELEVANT---
"Node 'grade_documents':"
'\n---\n'
---ASSESS GRADED DOCUMENTS---
---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---
---TRANSFORM QUERY---
"Node 'transform_query':"
'\n---\n'
---WEB SEARCH---
"Node 'web_search_node':"
'\n---\n'
---GENERATE---
"Node 'generate':"
'\n---\n'
"Node '__end__':"
'\n---\n'
('The AlphaCodium paper functions by proposing a code-oriented iterative flow '
 'that involves repeatedly running and fixing generated code against '
 'input-output tests. Its key mechanisms include generating additional data '
 'like problem reflection and test reasoning to aid the iterative process, as '
 'well as enriching the code generation process. AlphaCodium aims to improve '
 'the performance of Large Language Models on code problems by following a '
 'test-based, multi-stage approach.')

```

LangSmith Traces -

- [https://smith.langchain.com/public/f6b1716c-e842-4282-9112-1026b93e246b/r](https://smith.langchain.com/public/f6b1716c-e842-4282-9112-1026b93e246b/r)

- [https://smith.langchain.com/public/497c8ed9-d9e2-429e-8ada-e64de3ec26c9/r](https://smith.langchain.com/public/497c8ed9-d9e2-429e-8ada-e64de3ec26c9/r)


## Comments

giscus

#### [9 reactions](https://github.com/langchain-ai/langgraph/discussions/2663)

👍9

#### [2 comments](https://github.com/langchain-ai/langgraph/discussions/2663)

#### ·

#### 3 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@jinhon-chen](https://avatars.githubusercontent.com/u/59403621?v=4)jinhon-chen](https://github.com/jinhon-chen) [Jan 11](https://github.com/langchain-ai/langgraph/discussions/2663#discussioncomment-11804793)

as running "Use the graph", there are something wrong:

TypeError: string indices must be integers, not 'str'

During task with name 'web\_search\_node' and id '64250822-9000-ddc1-2589-b29219660108'

Can someone tell me why?

1

2 replies

[![@Hamza5](https://avatars.githubusercontent.com/u/7011111?v=4)](https://github.com/Hamza5)

[Hamza5](https://github.com/Hamza5) [Jan 11](https://github.com/langchain-ai/langgraph/discussions/2663#discussioncomment-11805782)

It seems that you posted the comment on the wrong page, because there is no tutorial on this page.

Also, your error seems to be a mistake in the tool.

[![@houssemjebari](https://avatars.githubusercontent.com/u/69901448?u=73d683a2189963adf0ba8aa64ba7ca1b1eb765a5&v=4)](https://github.com/houssemjebari)

[houssemjebari](https://github.com/houssemjebari) [14 days ago](https://github.com/langchain-ai/langgraph/discussions/2663#discussioncomment-12793165)

Hi Jinhon,

Can you provide a screenshot or more context for your issue?

Best,

Houssem J.

[![@ZiggyReQurv](https://avatars.githubusercontent.com/u/115216906?u=05b1c6daa24d99cd064a3fe4f046e4a0e9ac87d2&v=4)ZiggyReQurv](https://github.com/ZiggyReQurv) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/2663#discussioncomment-12702318)

Hi I've add this part:

memory = MemorySaver()

# Compile

app = workflow.compile(checkpointer=memory)

and

config = {"configurable": {"thread\_id": "1"}}

# Run

inputs = {"question": "di cosa parla l'OIC14?"}

for output in app.stream(inputs, config):

in order to persist memory but it does not work can you explain why?

thanks

1

1 reply

[![@houssemjebari](https://avatars.githubusercontent.com/u/69901448?u=73d683a2189963adf0ba8aa64ba7ca1b1eb765a5&v=4)](https://github.com/houssemjebari)

[houssemjebari](https://github.com/houssemjebari) [14 days ago](https://github.com/langchain-ai/langgraph/discussions/2663#discussioncomment-12793226)

Hi Ziggy,

From what I am seeing here it seems that you are trying to persist the conversation across sessions right? Correct me if I am wrong.

If that is your goal `MemorySaver` stores memory in **memory (RAM)** and resets when the script ends. It’s not persisted across sessions.

To make the session persist try:

```notranslate
checkpointer = FileCheckpointer("./checkpoints")
app = workflow.compile(checkpointer=checkpointer)

```

Best,

Houssem J.

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Frag%2Flanggraph_crag%2F)