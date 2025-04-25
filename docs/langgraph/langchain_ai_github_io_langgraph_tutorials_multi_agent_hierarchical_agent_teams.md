[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/#hierarchical-agent-teams)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/multi_agent/hierarchical_agent_teams.ipynb "Edit this page")

# Hierarchical Agent Teams [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/\#hierarchical-agent-teams "Permanent link")

In our previous example ( [Agent Supervisor](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor)), we introduced the concept of a single [supervisor node](https://langchain-ai.github.io/langgraph/concepts/multi_agent/#supervisor) to route work between different worker nodes.

But what if the job for a single worker becomes too complex? What if the number of workers becomes too large?

For some applications, the system may be more effective if work is distributed _hierarchically_.

You can do this by composing different subgraphs and creating a top-level supervisor, along with mid-level supervisors.

To do this, let's build a simple research assistant! The graph will look something like the following:

![diagram](<Base64-Image-Removed>)

This notebook is inspired by the paper [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation](https://arxiv.org/abs/2308.08155), by Wu, et. al. In the rest of this notebook, you will:

1. Define the agents' tools to access the web and write files
2. Define some utilities to help create the graph and agents
3. Create and define each team (web research + doc writing)
4. Compose everything together.

## Setup [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/\#setup "Permanent link")

First, let's install our required packages and set our API keys

```md-code__content
%%capture --no-stderr
%pip install -U langgraph langchain_community langchain_anthropic langchain_experimental

```

```md-code__content
import getpass
import os

def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

_set_if_undefined("OPENAI_API_KEY")
_set_if_undefined("TAVILY_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Create Tools [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/\#create-tools "Permanent link")

Each team will be composed of one or more agents each with one or more tools. Below, define all the tools to be used by your different teams.

We'll start with the research team.

**ResearchTeam tools**

The research team can use a search engine and url scraper to find information on the web. Feel free to add additional functionality below to boost the team performance!

API Reference: [WebBaseLoader](https://python.langchain.com/api_reference/community/document_loaders/langchain_community.document_loaders.web_base.WebBaseLoader.html) \| [TavilySearchResults](https://python.langchain.com/api_reference/community/tools/langchain_community.tools.tavily_search.tool.TavilySearchResults.html) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html)

```md-code__content
from typing import Annotated, List

from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

tavily_tool = TavilySearchResults(max_results=5)

@tool
def scrape_webpages(urls: List[str]) -> str:
    """Use requests and bs4 to scrape the provided web pages for detailed information."""
    loader = WebBaseLoader(urls)
    docs = loader.load()
    return "\n\n".join(
        [\
            f'<Document name="{doc.metadata.get("title", "")}">\n{doc.page_content}\n</Document>'\
            for doc in docs\
        ]
    )

```

**Document writing team tools**

Next up, we will give some tools for the doc writing team to use.
We define some bare-bones file-access tools below.

Note that this gives the agents access to your file-system, which can be unsafe. We also haven't optimized the tool descriptions for performance.

API Reference: [PythonREPL](https://python.langchain.com/api_reference/experimental/utilities/langchain_experimental.utilities.python.PythonREPL.html)

```md-code__content
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Optional

from langchain_experimental.utilities import PythonREPL
from typing_extensions import TypedDict

_TEMP_DIRECTORY = TemporaryDirectory()
WORKING_DIRECTORY = Path(_TEMP_DIRECTORY.name)

@tool
def create_outline(
    points: Annotated[List[str], "List of main points or sections."],
    file_name: Annotated[str, "File path to save the outline."],
) -> Annotated[str, "Path of the saved outline file."]:
    """Create and save an outline."""
    with (WORKING_DIRECTORY / file_name).open("w") as file:
        for i, point in enumerate(points):
            file.write(f"{i + 1}. {point}\n")
    return f"Outline saved to {file_name}"

@tool
def read_document(
    file_name: Annotated[str, "File path to read the document from."],
    start: Annotated[Optional[int], "The start line. Default is 0"] = None,
    end: Annotated[Optional[int], "The end line. Default is None"] = None,
) -> str:
    """Read the specified document."""
    with (WORKING_DIRECTORY / file_name).open("r") as file:
        lines = file.readlines()
    if start is None:
        start = 0
    return "\n".join(lines[start:end])

@tool
def write_document(
    content: Annotated[str, "Text content to be written into the document."],
    file_name: Annotated[str, "File path to save the document."],
) -> Annotated[str, "Path of the saved document file."]:
    """Create and save a text document."""
    with (WORKING_DIRECTORY / file_name).open("w") as file:
        file.write(content)
    return f"Document saved to {file_name}"

@tool
def edit_document(
    file_name: Annotated[str, "Path of the document to be edited."],
    inserts: Annotated[\
        Dict[int, str],\
        "Dictionary where key is the line number (1-indexed) and value is the text to be inserted at that line.",\
    ],
) -> Annotated[str, "Path of the edited document file."]:
    """Edit a document by inserting text at specific line numbers."""

    with (WORKING_DIRECTORY / file_name).open("r") as file:
        lines = file.readlines()

    sorted_inserts = sorted(inserts.items())

    for line_number, text in sorted_inserts:
        if 1 <= line_number <= len(lines) + 1:
            lines.insert(line_number - 1, text + "\n")
        else:
            return f"Error: Line number {line_number} is out of range."

    with (WORKING_DIRECTORY / file_name).open("w") as file:
        file.writelines(lines)

    return f"Document edited and saved to {file_name}"

# Warning: This executes code locally, which can be unsafe when not sandboxed

repl = PythonREPL()

@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return f"Successfully executed:\n\`\`\`python\n{code}\n\`\`\`\nStdout: {result}"

```

## Helper Utilities [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/\#helper-utilities "Permanent link")

We are going to create a few utility functions to make it more concise when we want to:

1. Create a worker agent.
2. Create a supervisor for the sub-graph.

These will simplify the graph compositional code at the end for us so it's easier to see what's going on.

API Reference: [BaseChatModel](https://python.langchain.com/api_reference/core/language_models/langchain_core.language_models.chat_models.BaseChatModel.html) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [Command](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Command) \| [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html) \| [trim\_messages](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.utils.trim_messages.html)

```md-code__content
from typing import List, Optional, Literal
from langchain_core.language_models.chat_models import BaseChatModel

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, trim_messages

class State(MessagesState):
    next: str

def make_supervisor_node(llm: BaseChatModel, members: list[str]) -> str:
    options = ["FINISH"] + members
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        f" following workers: {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )

    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""

        next: Literal[*options]

    def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
        """An LLM-based router."""
        messages = [\
            {"role": "system", "content": system_prompt},\
        ] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END

        return Command(goto=goto, update={"next": goto})

    return supervisor_node

```

## Define Agent Teams [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/\#define-agent-teams "Permanent link")

Now we can get to define our hierarchical teams. "Choose your player!"

### Research Team [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/\#research-team "Permanent link")

The research team will have a search agent and a web scraping "research\_agent" as the two worker nodes. Let's create those, as well as the team supervisor.

API Reference: [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

```md-code__content
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(model="gpt-4o")

search_agent = create_react_agent(llm, tools=[tavily_tool])

def search_node(state: State) -> Command[Literal["supervisor"]]:
    result = search_agent.invoke(state)
    return Command(
        update={
            "messages": [\
                HumanMessage(content=result["messages"][-1].content, name="search")\
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )

web_scraper_agent = create_react_agent(llm, tools=[scrape_webpages])

def web_scraper_node(state: State) -> Command[Literal["supervisor"]]:
    result = web_scraper_agent.invoke(state)
    return Command(
        update={
            "messages": [\
                HumanMessage(content=result["messages"][-1].content, name="web_scraper")\
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )

research_supervisor_node = make_supervisor_node(llm, ["search", "web_scraper"])

```

Now that we've created the necessary components, defining their interactions is easy. Add the nodes to the team graph, and define the edges, which determine the transition criteria.

```md-code__content
research_builder = StateGraph(State)
research_builder.add_node("supervisor", research_supervisor_node)
research_builder.add_node("search", search_node)
research_builder.add_node("web_scraper", web_scraper_node)

research_builder.add_edge(START, "supervisor")
research_graph = research_builder.compile()

```

```md-code__content
from IPython.display import Image, display

display(Image(research_graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

We can give this team work directly. Try it out below.

```md-code__content
for s in research_graph.stream(
    {"messages": [("user", "when is Taylor Swift's next tour?")]},
    {"recursion_limit": 100},
):
    print(s)
    print("---")

```

```md-code__content
{'supervisor': {'next': 'search'}}
---
{'search': {'messages': [HumanMessage(content="Taylor Swift's next tour is The Eras Tour, which includes both U.S. and international dates. She announced additional U.S. dates for 2024. You can find more details about the tour and ticket information on platforms like Ticketmaster and official announcements.", additional_kwargs={}, response_metadata={}, name='search', id='4df8687b-50a8-4342-aad5-680732c4a10f')]}}
---
{'supervisor': {'next': 'web_scraper'}}
---
{'web_scraper': {'messages': [HumanMessage(content='Taylor Swift\'s next tour is "The Eras Tour." Here are some of the upcoming international dates for 2024 that were listed on Ticketmaster:\n\n1. **Toronto, ON, Canada** at Rogers Centre\n   - November 21, 2024\n   - November 22, 2024\n   - November 23, 2024\n\n2. **Vancouver, BC, Canada** at BC Place\n   - December 6, 2024\n   - December 7, 2024\n   - December 8, 2024\n\nFor the most current information and additional dates, you can check platforms like Ticketmaster or Taylor Swift\'s [official website](https://www.taylorswift.com/events).', additional_kwargs={}, response_metadata={}, name='web_scraper', id='27524ebc-d179-4733-831d-ee10a58a2528')]}}
---
{'supervisor': {'next': '__end__'}}
---

```

### Document Writing Team [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/\#document-writing-team "Permanent link")

Create the document writing team below using a similar approach. This time, we will give each agent access to different file-writing tools.

Note that we are giving file-system access to our agent here, which is not safe in all cases.

```md-code__content
llm = ChatOpenAI(model="gpt-4o")

doc_writer_agent = create_react_agent(
    llm,
    tools=[write_document, edit_document, read_document],
    prompt=(
        "You can read, write and edit documents based on note-taker's outlines. "
        "Don't ask follow-up questions."
    ),
)

def doc_writing_node(state: State) -> Command[Literal["supervisor"]]:
    result = doc_writer_agent.invoke(state)
    return Command(
        update={
            "messages": [\
                HumanMessage(content=result["messages"][-1].content, name="doc_writer")\
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )

note_taking_agent = create_react_agent(
    llm,
    tools=[create_outline, read_document],
    prompt=(
        "You can read documents and create outlines for the document writer. "
        "Don't ask follow-up questions."
    ),
)

def note_taking_node(state: State) -> Command[Literal["supervisor"]]:
    result = note_taking_agent.invoke(state)
    return Command(
        update={
            "messages": [\
                HumanMessage(content=result["messages"][-1].content, name="note_taker")\
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )

chart_generating_agent = create_react_agent(
    llm, tools=[read_document, python_repl_tool]
)

def chart_generating_node(state: State) -> Command[Literal["supervisor"]]:
    result = chart_generating_agent.invoke(state)
    return Command(
        update={
            "messages": [\
                HumanMessage(\
                    content=result["messages"][-1].content, name="chart_generator"\
                )\
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )

doc_writing_supervisor_node = make_supervisor_node(
    llm, ["doc_writer", "note_taker", "chart_generator"]
)

```

With the objects themselves created, we can form the graph.

```md-code__content
# Create the graph here
paper_writing_builder = StateGraph(State)
paper_writing_builder.add_node("supervisor", doc_writing_supervisor_node)
paper_writing_builder.add_node("doc_writer", doc_writing_node)
paper_writing_builder.add_node("note_taker", note_taking_node)
paper_writing_builder.add_node("chart_generator", chart_generating_node)

paper_writing_builder.add_edge(START, "supervisor")
paper_writing_graph = paper_writing_builder.compile()

```

```md-code__content
from IPython.display import Image, display

display(Image(paper_writing_graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

```md-code__content
for s in paper_writing_graph.stream(
    {
        "messages": [\
            (\
                "user",\
                "Write an outline for poem about cats and then write the poem to disk.",\
            )\
        ]
    },
    {"recursion_limit": 100},
):
    print(s)
    print("---")

```

```md-code__content
{'supervisor': {'next': 'note_taker'}}
---
{'note_taker': {'messages': [HumanMessage(content='The outline for the poem about cats has been created and saved as "cats_poem_outline.txt".', additional_kwargs={}, response_metadata={}, name='note_taker', id='14a5d8ca-9092-416f-96ee-ba16686e8658')]}}
---
{'supervisor': {'next': 'doc_writer'}}
---
{'doc_writer': {'messages': [HumanMessage(content='The poem about cats has been written and saved as "cats_poem.txt".', additional_kwargs={}, response_metadata={}, name='doc_writer', id='c4e31a94-63ae-4632-9e80-1166f3f138b2')]}}
---
{'supervisor': {'next': '__end__'}}
---

```

## Add Layers [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/\#add-layers "Permanent link")

In this design, we are enforcing a top-down planning policy. We've created two graphs already, but we have to decide how to route work between the two.

We'll create a _third_ graph to orchestrate the previous two, and add some connectors to define how this top-level state is shared between the different graphs.

API Reference: [BaseMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.base.BaseMessage.html)

```md-code__content
from langchain_core.messages import BaseMessage

llm = ChatOpenAI(model="gpt-4o")

teams_supervisor_node = make_supervisor_node(llm, ["research_team", "writing_team"])

```

```md-code__content
def call_research_team(state: State) -> Command[Literal["supervisor"]]:
    response = research_graph.invoke({"messages": state["messages"][-1]})
    return Command(
        update={
            "messages": [\
                HumanMessage(\
                    content=response["messages"][-1].content, name="research_team"\
                )\
            ]
        },
        goto="supervisor",
    )

def call_paper_writing_team(state: State) -> Command[Literal["supervisor"]]:
    response = paper_writing_graph.invoke({"messages": state["messages"][-1]})
    return Command(
        update={
            "messages": [\
                HumanMessage(\
                    content=response["messages"][-1].content, name="writing_team"\
                )\
            ]
        },
        goto="supervisor",
    )

# Define the graph.
super_builder = StateGraph(State)
super_builder.add_node("supervisor", teams_supervisor_node)
super_builder.add_node("research_team", call_research_team)
super_builder.add_node("writing_team", call_paper_writing_team)

super_builder.add_edge(START, "supervisor")
super_graph = super_builder.compile()

```

```md-code__content
from IPython.display import Image, display

display(Image(super_graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

```md-code__content
for s in super_graph.stream(
    {
        "messages": [\
            ("user", "Research AI agents and write a brief report about them.")\
        ],
    },
    {"recursion_limit": 150},
):
    print(s)
    print("---")

```

```md-code__content
{'supervisor': {'next': 'research_team'}}
---
{'research_team': {'messages': [HumanMessage(content="**AI Agents Overview 2023**\n\nAI agents are sophisticated technologies that automate and enhance various processes across industries, becoming increasingly integral to business operations. In 2023, these agents are notable for their advanced capabilities in communication, data visualization, and language processing.\n\n**Popular AI Agents in 2023:**\n1. **Auto GPT**: This agent is renowned for its seamless integration abilities, significantly impacting industries by improving communication and operational workflows.\n2. **ChartGPT**: Specializing in data visualization, ChartGPT enables users to interact with data innovatively, providing deeper insights and comprehension.\n3. **LLMops**: With advanced language capabilities, LLMops is a versatile tool seeing widespread use across multiple sectors.\n\n**Market Trends:**\nThe AI agents market is experiencing rapid growth, with significant advancements anticipated by 2030. There's a growing demand for AI agents in personalized interactions, particularly within customer service, healthcare, and marketing sectors. This trend is fueled by the need for more efficient and tailored customer experiences.\n\n**Key Players:**\nLeading companies such as Microsoft, IBM, Google, Oracle, and AWS are key players in the AI agents market, highlighting the widespread adoption and investment in these technologies.\n\n**Technological Innovations:**\nAI agents are being developed alongside simulation technologies for robust testing and deployment environments. Innovations in generative AI are accelerating, supported by advancements in large language models and platforms like ChatGPT.\n\n**Applications in Healthcare:**\nIn healthcare, AI agents are automating routine tasks, allowing medical professionals to focus more on patient care. They're poised to significantly enhance healthcare delivery and efficiency.\n\n**Future Prospects:**\nThe future of AI agents is promising, with continued evolution and integration into various platforms and ecosystems, offering more seamless and intelligent interactions. As these technologies advance, they are expected to redefine business operations and customer interactions.", additional_kwargs={}, response_metadata={}, name='research_team', id='5f6606e0-838c-406c-b50d-9f9f6a076322')]}}
---
{'supervisor': {'next': 'writing_team'}}
---
{'writing_team': {'messages': [HumanMessage(content="Here are the contents of the documents:\n\n### AI Agents Overview 2023\n\n**AI Agents Overview 2023**\n\nAI agents are sophisticated technologies that automate and enhance various processes across industries, becoming increasingly integral to business operations. In 2023, these agents are notable for their advanced capabilities in communication, data visualization, and language processing.\n\n**Popular AI Agents in 2023:**\n1. **Auto GPT**: This agent is renowned for its seamless integration abilities, significantly impacting industries by improving communication and operational workflows.\n2. **ChartGPT**: Specializing in data visualization, ChartGPT enables users to interact with data innovatively, providing deeper insights and comprehension.\n3. **LLMops**: With advanced language capabilities, LLMops is a versatile tool seeing widespread use across multiple sectors.\n\n**Market Trends:**\nThe AI agents market is experiencing rapid growth, with significant advancements anticipated by 2030. There's a growing demand for AI agents in personalized interactions, particularly within customer service, healthcare, and marketing sectors. This trend is fueled by the need for more efficient and tailored customer experiences.\n\n**Key Players:**\nLeading companies such as Microsoft, IBM, Google, Oracle, and AWS are key players in the AI agents market, highlighting the widespread adoption and investment in these technologies.\n\n**Technological Innovations:**\nAI agents are being developed alongside simulation technologies for robust testing and deployment environments. Innovations in generative AI are accelerating, supported by advancements in large language models and platforms like ChatGPT.\n\n**Applications in Healthcare:**\nIn healthcare, AI agents are automating routine tasks, allowing medical professionals to focus more on patient care. They're poised to significantly enhance healthcare delivery and efficiency.\n\n**Future Prospects:**\nThe future of AI agents is promising, with continued evolution and integration into various platforms and ecosystems, offering more seamless and intelligent interactions. As these technologies advance, they are expected to redefine business operations and customer interactions.\n\n### AI_Agents_Overview_2023_Outline\n\n1. Introduction to AI Agents in 2023\n2. Popular AI Agents: Auto GPT, ChartGPT, LLMops\n3. Market Trends and Growth\n4. Key Players in the AI Agents Market\n5. Technological Innovations: Simulation and Generative AI\n6. Applications of AI Agents in Healthcare\n7. Future Prospects of AI Agents", additional_kwargs={}, response_metadata={}, name='writing_team', id='851bd8a6-740e-488c-8928-1f9e05e96ea0')]}}
---
{'supervisor': {'next': 'writing_team'}}
---
{'writing_team': {'messages': [HumanMessage(content='The documents have been successfully created and saved:\n\n1. **AI_Agents_Overview_2023.txt** - Contains the detailed overview of AI agents in 2023.\n2. **AI_Agents_Overview_2023_Outline.txt** - Contains the outline of the document.', additional_kwargs={}, response_metadata={}, name='writing_team', id='c87c0778-a085-4a8e-8ee1-9b43b9b0b143')]}}
---
{'supervisor': {'next': '__end__'}}
---

```

## Comments

giscus

#### [2 reactions](https://github.com/langchain-ai/langgraph/discussions/521)

🚀2

#### [20 comments](https://github.com/langchain-ai/langgraph/discussions/521)

#### ·

#### 19 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@gregorybarnes](https://avatars.githubusercontent.com/u/18541851?u=43103d3ce048d553de82f58e5e261036d743110f&v=4)gregorybarnes](https://github.com/gregorybarnes) [May 22, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-9516704)

The 2nd test to "Write an outline for poem and then write the poem to disk." didn't seem to work with gpt-4o when I initially tried it. I retried using gpt-4 which seemed to work fine. I re-ran the test again using gpt-4o so that I could capture the stack trace and it actually worked the 2nd time around! I'm not 100% certain but I vaguely remember the error complaining about the function call format on the first run.

Anyone else testing with gpt-4o may need to re-run a few times to get it to work correctly.

Also, the last test to "Write a brief research report on the North American sturgeon. Include a chart." triggered rate limit errors when running with gpt-4o:

`RateLimitError: Error code: 429 - {'error': {'message': 'Request too large for gpt-4o in organization org-xxxxxxxxxx on tokens per min (TPM): Limit 30000, Requested 38324. The input or output tokens must be reduced in order to run successfully. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}`

I'm too lazy to add code to correctly handle rate limits...

I wasn't ever able to get the 3rd and final test to complete. gpt-4-1106-preview, gpt-4, and gpt-3.5-turbo all caused the same error on multiple runs:

`BadRequestError: Error code: 400 - {'error': {'message': "Invalid 'messages[3].name': string does not match pattern. Expected a string that matches the pattern '^[a-zA-Z0-9_-]+$'.", 'type': 'invalid_request_error', 'param': 'messages[3].name', 'code': 'invalid_value'}}`

One time when running the last test with gpt-4-1106-preview I got the following error:

`ValueError: An output parsing error occurred. In order to pass this error back to the agent and have it try again, pass ` handle\_parsing\_errors=True `to the AgentExecutor. This is the error: Could not parse tool input: {'arguments': 'scrape_webpages ', 'name': 'functions'} because the` arguments ` is not valid JSON.`

I even went back and updated all of the teams to use gpt-4-1106-preview but the 3rd and final test never actually worked.

I get the gist of things here and I understand that I may need to tweak things a bit with prompting but should I be concerned about reliability? So far while running the tutorials in the "Multi-Agent Systems" section things seem pretty brittle and very sensitive/dependent on specific model versions. Are there tricks to getting around this or do I just need to continue working through the other tutorials and learn other design patterns to account for these issues?

1

👍3

4 replies

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [May 22, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-9516878)

Contributor

I don't personally think multi agent architectures are necessary or optimal for most applications, if that's your question

[![@gregorybarnes](https://avatars.githubusercontent.com/u/18541851?u=43103d3ce048d553de82f58e5e261036d743110f&v=4)](https://github.com/gregorybarnes)

[gregorybarnes](https://github.com/gregorybarnes) [May 22, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-9525866)

edited

Ya, I think that cuts down to the core of my question. Basically, what you're suggesting is I should try to define a single agent architecture for most applications because each added layer of agents may expose opportunities and vectors for formatting issues in their responses?

I do have a very specific application that I'm building for Model Evaluations. The goal is to orchestrate multiple agents playing the social deduction game called " [Mafia](https://en.wikipedia.org/wiki/Mafia_(party_game))" (sometimes called Werewolf) together.

Do you know if any design patterns tend to be more reliable or optimal compared to others when working with multi agent applications (ex. Supervision design is better than Hierarchical design because it has fewer layers)? Or is reliability more of an exercise in Prompt Engineering (ex. specify example response formats). Or worst case scenario is it an exercise in fine-tuning &/or pre-training?

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [May 29, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-9591150)

Contributor

Oh good question. The honest answer is "it depends" and that I'd typically start with fewer moving parts and only add complexity if my evals identify something I can't easily solve with the simpler design.

I think a supervisor pattern or something similar (can do fun things with speaker selection, for instance) would work for this.

1 note: I view prompt engineering and fine-tuning different shades of the same thing -> ways of inducing better task-specific behavior while potentially (increase bias, decrease variance)

👍1

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [May 29, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-9591154)

Contributor

Cool application btw! Mafia/Werewolf is a really fun game

[![@goern](https://avatars.githubusercontent.com/u/260331?u=28efe0814f7220d09e0f49ca2a98fa0b289237fc&v=4)goern](https://github.com/goern) [Jun 6, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-9685968)

Contributor

[@gregorybarnes](https://github.com/gregorybarnes) could you have a look at [#608](https://github.com/langchain-ai/langgraph/pull/608) and let me know if it fixes your problem?

1

0 replies

[![@HiraveBapu](https://avatars.githubusercontent.com/u/468513?v=4)HiraveBapu](https://github.com/HiraveBapu) [Jun 12, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-9756808)

[@goen](https://github.com/goen)

great article. i created simple supervision agent system for arithmetic operation, just to get idea around.

lets say, i have agent "addition", it has its tool to do the job. That tool requires two arguments to run the addition, seems like supervisor and agent stuck in loop during multi-turn conversation

```notranslate
User: add numbers
{'supervisor': {'next': 'Addition'}}
----
{'Addition': {'messages': [HumanMessage(content='Please provide the two numbers you would like to add.', name='Addition')]}}
----
{'supervisor': {'next': 'Addition'}}
----
{'Addition': {'messages': [HumanMessage(content='Please provide the two numbers you would like to add.', name='Addition')]}}
----
{'supervisor': {'next': 'Addition'}}
----

```

any suggestion ?

1

0 replies

[![@konon4](https://avatars.githubusercontent.com/u/48845890?u=df0332ee062748d8275aff89fb2644197bcc1e09&v=4)konon4](https://github.com/konon4) [Jul 1, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-9922606)

In create\_agent system\_prompt will only include the first line:

```notranslate
    system_prompt += "\nWork autonomously according to your specialty, using the tools available to you."
    " Do not ask for clarification."
    " Your other team members (and other teams) will collaborate with you with their own specialties."
    " You are chosen for a reason! You are one of the following team members: {team_members}."

```

should be :

```notranslate
    system_prompt += (
        "\nWork autonomously according to your specialty, using the tools available to you."
        " Do not ask for clarification."
        " Your other team members (and other teams) will collaborate with you with their own specialties."
        " You are chosen for a reason! You are one of the following team members: {team_members}."
    )

```

2

👍1

0 replies

[![@terwayp](https://avatars.githubusercontent.com/u/166444312?v=4)terwayp](https://github.com/terwayp) [Jul 5, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-9963437)

```notranslate
def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}

```

Why do we need to convert the messages to HumanMessage? Can it be just a BaseMessage?

1

1 reply

[![@HoaNQ98](https://avatars.githubusercontent.com/u/182324486?u=9e4fa0fc8309982e3d4332c54c90e196f6ba561f&v=4)](https://github.com/HoaNQ98)

[HoaNQ98](https://github.com/HoaNQ98) [Sep 21, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-10711507)

I guess that they do that is because the last time, I got an issue with Claude 3.5 Sonnet. He says:

```notranslate
Error raised by bedrock service: An error occurred (ValidationException) when calling the InvokeModel operation: Your API request included an `assistant` message in the final position, which would pre-fill the `assistant` response. When using tools, pre-filling the `assistant` response is not supported.

```

Each sub supervisor will response a AI message, which is in the final position in `messages` and call the main supervisor back to act next. But the main supervisor find a last message is AI role, then the model returns the issue above.

I just guess. If I'm right, I also don't like the way: convert AI message to Human message too much.

[![@terwayp](https://avatars.githubusercontent.com/u/166444312?v=4)terwayp](https://github.com/terwayp) [Jul 5, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-9963531)

```notranslate
class State(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    next: str

def get_last_message(state: State) -> str:
    return state["messages"][-1].content

def join_graph(response: dict):
    return {"messages": [response["messages"][-1]]}

# Define the graph.
super_graph = StateGraph(State)
# First add the nodes, which will do the work
super_graph.add_node("ResearchTeam", get_last_message | research_chain | join_graph)
super_graph.add_node(
    "PaperWritingTeam", get_last_message | authoring_chain | join_graph
)
super_graph.add_node("supervisor", supervisor_node)

```

What is the logic behind joining graph? Why does ` return {"messages": [response["messages"][-1]]}` help in the join?

1

1 reply

[![@matamorosjuan1](https://avatars.githubusercontent.com/u/66024410?v=4)](https://github.com/matamorosjuan1)

[matamorosjuan1](https://github.com/matamorosjuan1) [Jul 25, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-10152839)

From what I can tell, the purpose of join graph is to return the last message generated by the chain and add that message to the 'messages' state. Then when the next node is called, the get\_last\_message function is able to retrieve the content of that last message previously added to the 'messages' state and use that in that processing. Hope that makes sense.

[![@PragalvhaSharma](https://avatars.githubusercontent.com/u/140682795?u=ca3912692bb01c8d595a2a2c5546806e1ea713ef&v=4)PragalvhaSharma](https://github.com/PragalvhaSharma) [Jul 5, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-9964802)

i cannot see the text file it created

1

0 replies

[![@Surizz](https://avatars.githubusercontent.com/u/23274089?u=078f270a59bc0875fc52248d63db31de75e67d27&v=4)Surizz](https://github.com/Surizz) [Jul 11, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-10022398)

Hi,

I have been following the tutorial on hierarchical agent teams and have a question regarding a specific scenario. When a lower-level agent encounters a human-in-the-loop situation, what is the best approach to handle it?

I am particularly interested in:

1. Ensuring smooth and efficient communication between the agent and the human by checkpoint.

2. Minimizing any delays or interruptions in the overall process.

3. Integrating the human's input back into the system effectively.


Any guidance or examples on this would be greatly appreciated.

1

0 replies

[![@inoue0426](https://avatars.githubusercontent.com/u/8393063?u=f362509118f0892b6800edf208ed3ce30e1c4abf&v=4)inoue0426](https://github.com/inoue0426) [Sep 23, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-10721100)

When I use `llm = ChatOllama(model="llama3.1")`, I got `AttributeError: 'ChatOllama' object has no attribute 'bind_functions'`.

When I use `llm = ChatOpenAI( api_key="ollama", model="llama3.1", base_url="http://localhost:11434/v1", ) `, got this error, \`\`\`

File ~/miniconda3/envs/multi/lib/python3.11/site-packages/langchain\_core/output\_parsers/openai\_functions.py:106, in JsonOutputFunctionsParser.parse\_result(self, result, partial)

104 return None

105 else:

--\> 106 raise OutputParserException(

107 f"Could not parse function call: {exc}"

108 ) from exc

109 try:

110 if partial:

OutputParserException: Could not parse function call: 'function\_call'\`\`\`

Do you know how to deal with this?

1

3 replies

[![@LuisMoralesAlonso](https://avatars.githubusercontent.com/u/2943577?u=dc52d184e7ec72acb2b9fc06c9d92f0ca17605a1&v=4)](https://github.com/LuisMoralesAlonso)

[LuisMoralesAlonso](https://github.com/LuisMoralesAlonso) [Nov 6, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11160697)

Hi [@inoue0426](https://github.com/inoue0426), got the same issue. My understanding is that bind\_functions is deprecated, and with local models you must use bind\_tools

This leads to change in the code this way (this works for me):

def create\_team\_supervisor(llm: ChatOllama, system\_prompt, members) -> str:

"""An LLM-based supervisor."""

options = \["FINISH"\] + members

```notranslate
# Data model
class RouteSupervisor(BaseModel):
    """Route to the next role one of """ + ', '.join(options)

    worker: Literal[tuple(options)] = Field(
        ...,
        description="Next worker, one of " + ', '.join(options),
    )

structured_llm_router = llm.with_structured_output(RouteSupervisor)

# Prompt
prompt = ChatPromptTemplate.from_messages(
    [\
        ("system", system_prompt),\
        ("human", "{message}"),\
    ]
)
return prompt | structured_llm_router

```

Once you instantiate your model you can create the supervisor:

#Supervisor Node

research\_prompt = "You are a supervisor tasked with managing a conversation between the following workers: Search, WebScraper. Given the following user request, respond with the worker to act next. Each worker will perform a task and respond with their results and status.When finished, respond with FINISH."

supervisor\_agent = create\_team\_supervisor(llm, research\_prompt, \["Search", "WebScraper"\])

😄1

[![@inoue0426](https://avatars.githubusercontent.com/u/8393063?u=f362509118f0892b6800edf208ed3ce30e1c4abf&v=4)](https://github.com/inoue0426)

[inoue0426](https://github.com/inoue0426) [Nov 6, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11167667)

Thanks [@LuisMoralesAlonso](https://github.com/LuisMoralesAlonso) !

I will try this!

[![@LuisMoralesAlonso](https://avatars.githubusercontent.com/u/2943577?u=dc52d184e7ec72acb2b9fc06c9d92f0ca17605a1&v=4)](https://github.com/LuisMoralesAlonso)

[LuisMoralesAlonso](https://github.com/LuisMoralesAlonso) [Nov 6, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11170681)

I'm reviewing the entire use case based on this kind of upgrades... hope i can share more changes in the coming days

[![@Karlusk](https://avatars.githubusercontent.com/u/25887920?u=3004fe23850bb2c89ecbd9967901aa2fd376c4f5&v=4)Karlusk](https://github.com/Karlusk) [Sep 24, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-10743329)

I got it working but have some questions on why it's working. Specifically, why the supervisor seems stuck in a loop and keeps picking the outline team over and over. It's almost like it cannot see the entire message queue or does not know when to "finish"

It feels like it would be better to have it see the entire message queue and let each helper go once. It just loops.

Am I missing something?

1

2 replies

[![@cris-m](https://avatars.githubusercontent.com/u/29815096?u=4b55bcd0d0e557e3cc2a483bfd427627d7e52493&v=4)](https://github.com/cris-m)

[cris-m](https://github.com/cris-m) [Nov 20, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11317781)

Try to choose advanced model like `gpt-4o` or `claude-3-5-sonnet` as `llm` for supervisor. I had the same issue but when I change the `llm` I got the response. I think the solution will be to change the model or change the prompt.

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)](https://github.com/HoangNguyen689)

[HoangNguyen689](https://github.com/HoangNguyen689) [Dec 23, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11650913)

Also got stuck because of supervisor in a loop of outline team over and over.

Tested with gpt-4o.

Maybe we need to specify the prompt more precisely.

[![@iamgauravpant](https://avatars.githubusercontent.com/u/64788558?v=4)iamgauravpant](https://github.com/iamgauravpant) [Sep 27, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-10772218)

Hi guys , I'm trying to add memory to this hierarchical agent system but no success so far .

I tried to integrate the most basic form of memory using in-memory checkpointer but it doesn't work .

Any idea on how to add memory to hierarchical agent system or multi-agent systems in general ?

1

👍1

2 replies

[![@Shahzaib-qlu](https://avatars.githubusercontent.com/u/181054026?v=4)](https://github.com/Shahzaib-qlu)

[Shahzaib-qlu](https://github.com/Shahzaib-qlu) [Nov 6, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11166748)

let me know if you got any way to do manage it.

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)](https://github.com/HoangNguyen689)

[HoangNguyen689](https://github.com/HoangNguyen689) [Dec 23, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11650902)

what do you mean memory? Is that about ask a question that in a thread (has chat history) ?

[![@Tman910](https://avatars.githubusercontent.com/u/39782734?v=4)Tman910](https://github.com/Tman910) [Oct 8, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-10874250)

Come someone explain the following snippet please? Is there any documentation for how this works?

```notranslate
function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [\
                        {"enum": options},\
                    ],
                },
            },
            "required": ["next"],
        },
    }

```

1

1 reply

[![@HamedHaddadi](https://avatars.githubusercontent.com/u/86529884?u=20494df363afbeaa2bf68b9119e884fb2f2fdedd&v=4)](https://github.com/HamedHaddadi)

[HamedHaddadi](https://github.com/HamedHaddadi) [Oct 10, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-10909536)

This is the json schema of the function passed to the 'bind\_function' method.

Consider this simple example:

```
from pydantic import BaseModel
from typing import Literal

class routeResponse(BaseModel):
    next: Literal['one', 'two']

routeResponse.model_json_schema()
```

```notranslate
{'properties': {'next': {'enum': ['one', 'two'],
   'title': 'Next',
   'type': 'string'}},
 'required': ['next'],
 'title': 'routeResponse',
 'type': 'object'}

```

👍1❤️1

[![@HamedHaddadi](https://avatars.githubusercontent.com/u/86529884?u=20494df363afbeaa2bf68b9119e884fb2f2fdedd&v=4)HamedHaddadi](https://github.com/HamedHaddadi) [Oct 10, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-10909453)

Just in case someone encounters a same error.

It is not possible to use a lambda as the 'path' to 'add\_conditional\_edges'.

The best way is to define a function, for instance:

def route\_agents(state):

return state\['next'\]

and pass this function as the path to add\_conditional\_edges.

The reason is in Graph.add\_conditional\_edges(self, source, path, path\_map, then) it requests for name of the RunnableCallable

...

name = path.name or "condition"

and lambda functions are anonymous.

1

❤️1

1 reply

[![@DanielOsorio01](https://avatars.githubusercontent.com/u/78004738?u=086390d6ddbb55fcaa6d27dc17f62439b9c5e505&v=4)](https://github.com/DanielOsorio01)

[DanielOsorio01](https://github.com/DanielOsorio01) [Nov 24, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11361063)

Thanks! I had this error too

[![@Zhuytt20](https://avatars.githubusercontent.com/u/166119175?v=4)Zhuytt20](https://github.com/Zhuytt20) [Oct 28, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11075073)

why? anyone help me

Traceback (most recent call last):

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langchain\_core\\output\_parsers\\openai\_functions.py", line 97, in parse\_result

function\_call = message.additional\_kwargs\["function\_call"\]

~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^

KeyError: 'function\_call'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):

File "D:\\langchain\_v3.0\\43 Hierarchical Agent Teams.py", line 293, in

for s in research\_chain.stream(

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langchain\_core\\runnables\\base.py", line 3407, in stream

yield from self.transform(iter(\[input\]), config, \*\*kwargs)

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langchain\_core\\runnables\\base.py", line 3394, in transform

yield from self.\_transform\_stream\_with\_config(

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langchain\_core\\runnables\\base.py", line 2197, in \_transform\_stream\_with\_config

chunk: Output = context.run(next, iterator) # type: ignore

^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langchain\_core\\runnables\\base.py", line 3357, in _transform_

_yield from final\_pipeline_

_File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langchain\_core\\runnables\\base.py", line 1431, in transform_

_yield from self.stream(final, config, \*\*kwargs)_

_File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langgraph\\pregel\_init_.py", line 1307, in stream

for \_ in runner.tick(

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langgraph\\pregel\\runner.py", line 56, in tick

run\_with\_retry(t, retry\_policy)

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langgraph\\pregel\\retry.py", line 29, in run\_with\_retry

task.proc.invoke(task.input, config)

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langgraph\\utils\\runnable.py", line 412, in invoke

input = context.run(step.invoke, input, config)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langchain\_core\\output\_parsers\\base.py", line 193, in invoke

return self.\_call\_with\_config(

^^^^^^^^^^^^^^^^^^^^^^^

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langchain\_core\\runnables\\base.py", line 1927, in \_call\_with\_config

context.run(

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langchain\_core\\runnables\\config.py", line 396, in call\_func\_with\_variable\_args

return func(input, \*\*kwargs) # type: ignore\[call-arg\]

^^^^^^^^^^^^^^^^^^^^^

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langchain\_core\\output\_parsers\\base.py", line 194, in

lambda inner\_input: self.parse\_result(

^^^^^^^^^^^^^^^^^^

File "D:\\anaconda\\envs\\lc\\Lib\\site-packages\\langchain\_core\\output\_parsers\\openai\_functions.py", line 103, in parse\_result

raise OutputParserException(msg) from exc

langchain\_core.exceptions.OutputParserException: Could not parse function call: 'function\_call'

Process finished with exit code 1

1

👍1

0 replies

[![@Silecne666](https://avatars.githubusercontent.com/u/58200177?u=8c71b3804b37c4eb3d406656da86991a2f7d0ffc&v=4)Silecne666](https://github.com/Silecne666) [Dec 12, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11540355)

I'm currently in the process of hierarchical\_agent\_teams, which have been successfully completed. However, the llm was found to summarize and optimize the responses returned by the tool. Now I expect the result to be the output returned by the tool without any modifications. Are there any parameters that need to be configured?

1

2 replies

[![@HoaNQ98](https://avatars.githubusercontent.com/u/182324486?u=9e4fa0fc8309982e3d4332c54c90e196f6ba561f&v=4)](https://github.com/HoaNQ98)

[HoaNQ98](https://github.com/HoaNQ98) [Dec 16, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11580275)

2 ways I think you can try:

1. You write the system prompt for AI that he does not modify any result from his managing tools and keep it as original. Of course, sometimes he can miss that
2. You can consider creating a custom node for your tool that the tool won't need to back to AI. Btw, you probably should configure a conditional edge for that

[![@Silecne666](https://avatars.githubusercontent.com/u/58200177?u=8c71b3804b37c4eb3d406656da86991a2f7d0ffc&v=4)](https://github.com/Silecne666)

[Silecne666](https://github.com/Silecne666) [Dec 17, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11589070)

Thanks, I'm going to try both of these methods,

but with debug, there's a ToolMessage, which is what I want,

[![@bphillab](https://avatars.githubusercontent.com/u/2706247?v=4)bphillab](https://github.com/bphillab) [Dec 27, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11677853)

After running this I keep getting

```notranslate
{'supervisor': None}

```

rather than what the expected output is. Does anyone know what's up with that?

1

1 reply

[![@bphillab](https://avatars.githubusercontent.com/u/2706247?v=4)](https://github.com/bphillab)

[bphillab](https://github.com/bphillab) [Dec 27, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11677858)

eg for the cat poem:

```notranslate
{'supervisor': None}
---
{'note_taker': {'messages': [HumanMessage(content='The outline for the poem about cats has been created and saved as "cats_poem_outline.txt."', additional_kwargs={}, response_metadata={}, name='note_taker', id='5e6e7f3d-64ad-4216-805b-90b75b23f905')]}}
---
{'supervisor': None}
---
{'doc_writer': {'messages': [HumanMessage(content='The poem about cats has been written and saved as "cats_poem.txt."', additional_kwargs={}, response_metadata={}, name='doc_writer', id='9c7b360e-36ca-47a9-ae13-75714e9db11b')]}}
---
{'supervisor': None}
---

```

The program is following the graph as expected, but rather than saying the next step for the supervisor it just kinda doesn't.

[![@HoangHao1009](https://avatars.githubusercontent.com/u/112957852?u=b252750a2c9733f294fa00ebba2c50b97524269d&v=4)HoangHao1009](https://github.com/HoangHao1009) [Dec 29, 2024](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11690668)

## Thank you, LangChain/LangGraph team, for the exclusive tutorial! I have a question about the logic behind selecting the next node (i.e., how the supervisor chooses the agent). Is the selection process solely determined by the system prompt, as shown below?

## system\_prompt = (   "You are a supervisor tasked with managing a conversation between the"   f" following workers: {members}. Given the following user request,"   " respond with the worker to act next. Each worker will perform a"   " task and respond with their results and status. When finished,"   " respond with FINISH."   )

Does the system rely only on the worker names for selection, or are there other factors or mechanisms at play that influence the choice? Additionally, how can I ensure the routing is accurate? Should I make the prompt more concise to improve its effectiveness?

Also, I noticed that the agents (e.g., search\_agent and web\_scraper\_agent) do not seem to have their own system prompts. When is it necessary to add system prompts to agents, and how should I decide whether to include them? I'd appreciate any clarification or tips! 😊

1

❤️1

0 replies

[![@namkyupar](https://avatars.githubusercontent.com/u/194640672?v=4)namkyupar](https://github.com/namkyupar) [Jan 11](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11808603)

Thank you very much for the example.

I tried to change only two things - search engine (duck) and LLM (ollama + llama3.1):

from langchain\_community.tools import DuckDuckGoSearchRun

duck\_tool = DuckDuckGoSearchRun(max\_results=5)

search\_agent = create\_react\_agent(llm, tools=\[duck\_tool\])

from langchain\_ollama import ChatOllama

llm = ChatOllama(model="llama3.1", temperature=0)

and I'm getting the following error:

python aaa.py

/Users/namkyup/vsc/langgraph/aaa.py:111: SyntaxWarning: invalid escape sequence '\`'

return f"Successfully executed:\\n\`\`\`python\\n{code}\\n\`\`\`\\nStdout: {result}"

/Users/namkyup/vsc/langgraph/aaa.py:111: SyntaxWarning: invalid escape sequence '\`'

return f"Successfully executed:\\n\`\`\`python\\n{code}\\n\`\`\`\\nStdout: {result}"

USER\_AGENT environment variable not set, consider setting it to identify your requests.

<IPython.core.display.Image object>

Traceback (most recent call last):

File "/Users/namkyup/vsc/langgraph/aaa.py", line 202, in

for s in research\_graph.stream(

~~~~~~~~~~~~~~~~~~~~~^

{"messages": \[("user", "when is Taylor Swift's next tour?")\]},

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

{"recursion\_limit": 100},

^^^^^^^^^^^^^^^^^^^^^^^^^

):

^

File "/Users/namkyup/vsc/langgraph/lib/python3.13/site-packages/langgraph/pregel/ **init**.py", line 1660, in stream

for \_ in runner.tick(

~~~~~~~~~~~^

loop.tasks.values(),

^^^^^^^^^^^^^^^^^^^^

...<2 lines>...

get\_waiter=get\_waiter,

^^^^^^^^^^^^^^^^^^^^^^

):

^

File "/Users/namkyup/vsc/langgraph/lib/python3.13/site-packages/langgraph/pregel/runner.py", line 167, in tick

run\_with\_retry(

~~~~~~~~~~~~~~^

t,

^^

...<4 lines>...

},

^^

)

^

File "/Users/namkyup/vsc/langgraph/lib/python3.13/site-packages/langgraph/pregel/retry.py", line 40, in run\_with\_retry

return task.proc.invoke(task.input, config)

~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^

File "/Users/namkyup/vsc/langgraph/lib/python3.13/site-packages/langgraph/utils/runnable.py", line 408, in invoke

input = step.invoke(input, config, \*\*kwargs)

File "/Users/namkyup/vsc/langgraph/lib/python3.13/site-packages/langgraph/utils/runnable.py", line 184, in invoke

ret = context.run(self.func, input, \*\*kwargs)

File "/Users/namkyup/vsc/langgraph/aaa.py", line 142, in supervisor\_node

goto = response\["next"\]

~~~~~~~~^^^^^^^^

TypeError: 'NoneType' object is not subscriptable

During task with name 'supervisor' and id '661bc734-8df6-309c-b3f3-3316809fa5e5'

I'm also not sure why I get the following two warnings at the beginning:

/Users/namkyup/vsc/langgraph/aaa.py:111: SyntaxWarning: invalid escape sequence '\`'

return f"Successfully executed:\\n\`\`\`python\\n{code}\\n\`\`\`\\nStdout: {result}"

/Users/namkyup/vsc/langgraph/aaa.py:111: SyntaxWarning: invalid escape sequence '\`'

return f"Successfully executed:\\n\`\`\`python\\n{code}\\n\`\`\`\\nStdout: {result}"

and

USER\_AGENT environment variable not set, consider setting it to identify your requests.

Any help would be highly appreciated!

1

0 replies

[![@akashAD98](https://avatars.githubusercontent.com/u/62583018?v=4)akashAD98](https://github.com/akashAD98) [Jan 23](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-11923977)

this code has lots of issue why cant you fix it all ?

1

1 reply

[![@catsled](https://avatars.githubusercontent.com/u/18079717?u=7c036868bdc6084d1cf8bc15c23e4fed8fbe63df&v=4)](https://github.com/catsled)

[catsled](https://github.com/catsled) [Mar 3](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-12373132)

example: the graph will be ended while the sub-graph goto END, it should be fixed.

[![@BlakeQG](https://avatars.githubusercontent.com/u/116970615?v=4)BlakeQG](https://github.com/BlakeQG) [26 days ago](https://github.com/langchain-ai/langgraph/discussions/521#discussioncomment-12659087)

There should be some guideline / explanation regarding why many agent / subgraph's output are wrapped in HumanMessage while it is generated by AI ?

I know properly it is because some AI model / langchain refuses to answer AI's question (require previous msg to be human), but it should be explained so people are aware of this

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Fmulti_agent%2Fhierarchical_agent_teams%2F)