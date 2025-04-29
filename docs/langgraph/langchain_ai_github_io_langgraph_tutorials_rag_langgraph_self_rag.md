[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#self-rag)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/rag/langgraph_self_rag.ipynb "Edit this page")

# Self-RAG [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/\#self-rag "Permanent link")

Self-RAG is a strategy for RAG that incorporates self-reflection / self-grading on retrieved documents and generations.

In the [paper](https://arxiv.org/abs/2310.11511), a few decisions are made:

01. Should I retrieve from retriever, `R` -

02. Input: `x (question)` OR `x (question)`, `y (generation)`

03. Decides when to retrieve `D` chunks with `R`
04. Output: `yes, no, continue`

05. Are the retrieved passages `D` relevant to the question `x` -

    - Input: ( `x (question)`, `d (chunk)`) for `d` in `D`
07. `d` provides useful information to solve `x`
08. Output: `relevant, irrelevant`

09. Are the LLM generation from each chunk in `D` is relevant to the chunk (hallucinations, etc) -

10. Input: `x (question)`, `d (chunk)`, `y (generation)` for `d` in `D`

11. All of the verification-worthy statements in `y (generation)` are supported by `d`
12. Output: `{fully supported, partially supported, no support`

13. The LLM generation from each chunk in `D` is a useful response to `x (question)` -

14. Input: `x (question)`, `y (generation)` for `d` in `D`

15. `y (generation)` is a useful response to `x (question)`.
16. Output: `{5, 4, 3, 2, 1}`

We will implement some of these ideas from scratch using [LangGraph](https://langchain-ai.github.io/langgraph/).

![Screenshot 2024-04-01 at 12.41.50 PM.png](<Base64-Image-Removed>)

## Setup [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/\#setup "Permanent link")

First let's install our required packages and set our API keys

```md-code__content
%pip install -U langchain_community tiktoken langchain-openai langchainhub chromadb langchain langgraph

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


## Retriever [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/\#retriever "Permanent link")

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

## LLMs [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/\#llms "Permanent link")

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
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm_grader = llm.with_structured_output(GradeDocuments)

# Prompt
system = """You are a grader assessing relevance of a retrieved document to a user question. \n
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
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
binary_score='no'

```

API Reference: [StrOutputParser](https://python.langchain.com/api_reference/core/output_parsers/langchain_core.output_parsers.string.StrOutputParser.html)

```md-code__content
### Generate

from langchain import hub
from langchain_core.output_parsers import StrOutputParser

# Prompt
prompt = hub.pull("rlm/rag-prompt")

# LLM
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

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
The design of generative agents combines LLM with memory, planning, and reflection mechanisms to enable agents to behave conditioned on past experience. Memory stream is a long-term memory module that records a comprehensive list of agents' experience in natural language. LLM functions as the agent's brain in an autonomous agent system.

```

```md-code__content
### Hallucination Grader

# Data model
class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )

# LLM with function call
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm_grader = llm.with_structured_output(GradeHallucinations)

# Prompt
system = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n
     Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""
hallucination_prompt = ChatPromptTemplate.from_messages(
    [\
        ("system", system),\
        ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),\
    ]
)

hallucination_grader = hallucination_prompt | structured_llm_grader
hallucination_grader.invoke({"documents": docs, "generation": generation})

```

```md-code__content
GradeHallucinations(binary_score='yes')

```

```md-code__content
### Answer Grader

# Data model
class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )

# LLM with function call
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm_grader = llm.with_structured_output(GradeAnswer)

# Prompt
system = """You are a grader assessing whether an answer addresses / resolves a question \n
     Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""
answer_prompt = ChatPromptTemplate.from_messages(
    [\
        ("system", system),\
        ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),\
    ]
)

answer_grader = answer_prompt | structured_llm_grader
answer_grader.invoke({"question": question, "generation": generation})

```

```md-code__content
GradeAnswer(binary_score='yes')

```

```md-code__content
### Question Re-writer

# LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Prompt
system = """You a question re-writer that converts an input question to a better version that is optimized \n
     for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""
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
"What is the role of memory in an agent's functioning?"

```

# Graph [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/\#graph "Permanent link")

Capture the flow in as a graph.

## Graph state [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/\#graph-state "Permanent link")

```md-code__content
from typing import List

from typing_extensions import TypedDict

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """

    question: str
    generation: str
    documents: List[str]

```

```md-code__content
### Nodes

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
            continue
    return {"documents": filtered_docs, "question": question}

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
    filtered_documents = state["documents"]

    if not filtered_documents:
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

def grade_generation_v_documents_and_question(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]

    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )
    grade = score.binary_score

    # Check hallucination
    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        # Check question-answering
        print("---GRADE GENERATION vs QUESTION---")
        score = answer_grader.invoke({"question": question, "generation": generation})
        grade = score.binary_score
        if grade == "yes":
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        pprint("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"

```

## Build Graph [¶](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/\#build-graph "Permanent link")

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
workflow.add_edge("transform_query", "retrieve")
workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {
        "not supported": "generate",
        "useful": END,
        "not useful": "transform_query",
    },
)

# Compile
app = workflow.compile()

```

```md-code__content
from pprint import pprint

# Run
inputs = {"question": "Explain how the different types of agent memory work?"}
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
---GRADE: DOCUMENT RELEVANT---
---GRADE: DOCUMENT NOT RELEVANT---
---GRADE: DOCUMENT RELEVANT---
---ASSESS GRADED DOCUMENTS---
---DECISION: GENERATE---
"Node 'grade_documents':"
'\n---\n'
---GENERATE---
---CHECK HALLUCINATIONS---
---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---
---GRADE GENERATION vs QUESTION---
---DECISION: GENERATION ADDRESSES QUESTION---
"Node 'generate':"
'\n---\n'
('Short-term memory is used for in-context learning in agents, allowing them '
 'to learn quickly. Long-term memory enables agents to retain and recall vast '
 'amounts of information over extended periods. Agents can also utilize '
 'external tools like APIs to access additional information beyond what is '
 'stored in their memory.')

```

```md-code__content
inputs = {"question": "Explain how chain of thought prompting works?"}
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
---GRADE: DOCUMENT RELEVANT---
---GRADE: DOCUMENT NOT RELEVANT---
---GRADE: DOCUMENT RELEVANT---
---GRADE: DOCUMENT RELEVANT---
---ASSESS GRADED DOCUMENTS---
---DECISION: GENERATE---
"Node 'grade_documents':"
'\n---\n'
---GENERATE---
---CHECK HALLUCINATIONS---
---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---
---GRADE GENERATION vs QUESTION---
---DECISION: GENERATION ADDRESSES QUESTION---
"Node 'generate':"
'\n---\n'
('Chain of thought prompting works by repeatedly prompting the model to ask '
 'follow-up questions to construct the thought process iteratively. This '
 'method can be combined with queries to search for relevant entities and '
 'content to add back into the context. It extends the thought process by '
 'exploring multiple reasoning possibilities at each step, creating a tree '
 'structure of thoughts.')

```

## Comments

giscus

#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/1079)

#### [6 comments](https://github.com/langchain-ai/langgraph/discussions/1079)

#### ·

#### 2 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@DhavalThkkar](https://avatars.githubusercontent.com/u/16734921?u=0806ac526d123c4f364578bf128022b8a4772783&v=4)DhavalThkkar](https://github.com/DhavalThkkar) [Jul 21, 2024](https://github.com/langchain-ai/langgraph/discussions/1079#discussioncomment-10108015)

Contributor

How can one add memory to the above Self-RAG implementation using checkpointers?

1

1 reply

[![@jong01045](https://avatars.githubusercontent.com/u/46094083?v=4)](https://github.com/jong01045)

[jong01045](https://github.com/jong01045) [Jul 22, 2024](https://github.com/langchain-ai/langgraph/discussions/1079#discussioncomment-10117026)

from langgraph.checkpoint.memory import MemorySaver

# Tracing the flow of the nodes, Snapshot facility to recall to a certain point

memory = MemorySaver()

# Compile graph

app = workflow.compile(checkpointer=memory)

This is how I added the checkpointer.

[![@HiraveBapu](https://avatars.githubusercontent.com/u/468513?v=4)HiraveBapu](https://github.com/HiraveBapu) [Jul 23, 2024](https://github.com/langchain-ai/langgraph/discussions/1079#discussioncomment-10120975)

I am looking for agent example which has RAG functions and non-RAG functions. So far all tutorials are only about either RAG or non-RAG tools chatbot.

also agent needs to have memory to serve rag and non-rag functions

1

0 replies

[![@alphaply](https://avatars.githubusercontent.com/u/52284596?u=1b2685e2a9d13d8024f1c67ebfdbe4d0855d92c3&v=4)alphaply](https://github.com/alphaply) [Jul 24, 2024](https://github.com/langchain-ai/langgraph/discussions/1079#discussioncomment-10141529)

I think what you want is to add context (history). One possible solution is to turn this workflow into a tool and give it to the agent to use.

1

1 reply

[![@HiraveBapu](https://avatars.githubusercontent.com/u/468513?v=4)](https://github.com/HiraveBapu)

[HiraveBapu](https://github.com/HiraveBapu) [Jul 24, 2024](https://github.com/langchain-ai/langgraph/discussions/1079#discussioncomment-10141627)

yeah, thats what i got. I have set of tools (non-rag related), and another tool for RAG only.

agents are not consistent on calling RAG tool more often, and rather respond to query based on its knowledge rather than using RAG tool

[![@sreedevi1249](https://avatars.githubusercontent.com/u/33509222?v=4)sreedevi1249](https://github.com/sreedevi1249) [Aug 22, 2024](https://github.com/langchain-ai/langgraph/discussions/1079#discussioncomment-10417916)

i have experimented the code there i got one question

suppose if i give the question which is not related to the context ideally it should generate and say that I don't know. I need context to answer your question, but that is not happening with the above code its going on loop i have fixed the code

please check the below link for the fix

[https://colab.research.google.com/drive/1tuFIh\_DrM\_VAUc5shu7L3tI-KdYt8u8O#scrollTo=3jBWX44IEWy-](https://colab.research.google.com/drive/1tuFIh_DrM_VAUc5shu7L3tI-KdYt8u8O#scrollTo=3jBWX44IEWy-)

please let me know if its correct

1

0 replies

[![@raulperula](https://avatars.githubusercontent.com/u/6907809?u=ed53f172930b0bbc721a9b42b8f9c37b39e98a27&v=4)raulperula](https://github.com/raulperula) [Oct 29, 2024](https://github.com/langchain-ai/langgraph/discussions/1079#discussioncomment-11086191)

What is the better way to avoid infinite loops in a Self-RAG solution when questions are unlikely to be related to data sources (aka the typical fallback)?

Should I create a new node or conditional edge to stop execution when the recursion limit is reached and predefine an answer for the user, e.g. "Sorry, but I don't have that information. Please ask questions related to blablabla..."?

1

👍1

0 replies

[![@kovla](https://avatars.githubusercontent.com/u/3816002?v=4)kovla](https://github.com/kovla) [Nov 26, 2024](https://github.com/langchain-ai/langgraph/discussions/1079#discussioncomment-11383562)

In this tutorial, `grade_generation_v_documents_and_question()` relies on `print` statements to convey information about its decisions. If the application were exposed through a GUI (e.g. py-shiny or gradio to stay in the Python world), how would one go about capturing decision from conditional edges?

For instance, is there a way to also update the graph state from the routing functions (i.e. something like `return "not_supported", {"last_decision": "re-generate"}`? In the front-end, this would be perceived as a state update and rendered in the GUI.

If graph updates from conditional edges are not supported, is it possible to pass a reactive GUI object (e.g. reactive value, an update to which would trigger an update in the GUI, such as this one: [https://shiny.posit.co/py/api/core/reactive.value.html](https://shiny.posit.co/py/api/core/reactive.value.html)) in the configurable dict?

A work-around would be simply adding an extra node that does nothing other than handling the output (I suppose it would be paradigmatic to update state only from nodes and not edges). That would add to latency though, however minimal. The original print statements suggest the necessity of relaying information to the user, so how this should be handled in a more robust way? Thank you.

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Frag%2Flanggraph_self_rag%2F)