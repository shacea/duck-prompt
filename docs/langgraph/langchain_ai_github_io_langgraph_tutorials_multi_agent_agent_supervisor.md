[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/#multi-agent-supervisor)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/multi_agent/agent_supervisor.ipynb "Edit this page")

# Multi-agent supervisor [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/\#multi-agent-supervisor "Permanent link")

The [previous example](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration) routed messages automatically based on the output of the initial researcher agent.

We can also choose to use an [LLM to orchestrate](https://langchain-ai.github.io/langgraph/concepts/multi_agent/#supervisor) the different agents.

Below, we will create an agent group, with an agent supervisor to help delegate tasks.

![diagram](<Base64-Image-Removed>)

To simplify the code in each agent node, we will use LangGraph's prebuilt [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent). This and other "advanced agent" notebooks are designed to show how you can implement certain design patterns in LangGraph. If the pattern suits your needs, we recommend combining it with some of the other fundamental patterns described elsewhere in the docs for best performance.

## Setup [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/\#setup "Permanent link")

First, let's install required packages and set our API keys

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

_set_if_undefined("ANTHROPIC_API_KEY")
_set_if_undefined("TAVILY_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Create tools [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/\#create-tools "Permanent link")

For this example, you will make an agent to do web research with a search engine, and one agent to create plots. Define the tools they'll use below:

API Reference: [TavilySearchResults](https://python.langchain.com/api_reference/community/tools/langchain_community.tools.tavily_search.tool.TavilySearchResults.html) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [PythonREPL](https://python.langchain.com/api_reference/experimental/utilities/langchain_experimental.utilities.python.PythonREPL.html)

```md-code__content
from typing import Annotated

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

tavily_tool = TavilySearchResults(max_results=5)

# This executes code locally, which can be unsafe
repl = PythonREPL()

@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code and do math. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n\`\`\`python\n{code}\n\`\`\`\nStdout: {result}"
    return result_str

```

### Create Agent Supervisor [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/\#create-agent-supervisor "Permanent link")

It will use LLM with structured output to choose the next worker node OR finish processing.

API Reference: [ChatAnthropic](https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [Command](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Command)

```md-code__content
from typing import Literal
from typing_extensions import TypedDict

from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState, END
from langgraph.types import Command

members = ["researcher", "coder"]
# Our team supervisor is an LLM node. It just picks the next agent to process
# and decides when the work is completed
options = members + ["FINISH"]

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

llm = ChatAnthropic(model="claude-3-5-sonnet-latest")

class State(MessagesState):
    next: str

def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
    messages = [\
        {"role": "system", "content": system_prompt},\
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
        goto = END

    return Command(goto=goto, update={"next": goto})

```

## Construct Graph [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/\#construct-graph "Permanent link")

We're ready to start building the graph. Below, define the state and worker nodes using the function we just defined.

API Reference: [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

```md-code__content
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent

research_agent = create_react_agent(
    llm, tools=[tavily_tool], prompt="You are a researcher. DO NOT do any math."
)

def research_node(state: State) -> Command[Literal["supervisor"]]:
    result = research_agent.invoke(state)
    return Command(
        update={
            "messages": [\
                HumanMessage(content=result["messages"][-1].content, name="researcher")\
            ]
        },
        goto="supervisor",
    )

# NOTE: THIS PERFORMS ARBITRARY CODE EXECUTION, WHICH CAN BE UNSAFE WHEN NOT SANDBOXED
code_agent = create_react_agent(llm, tools=[python_repl_tool])

def code_node(state: State) -> Command[Literal["supervisor"]]:
    result = code_agent.invoke(state)
    return Command(
        update={
            "messages": [\
                HumanMessage(content=result["messages"][-1].content, name="coder")\
            ]
        },
        goto="supervisor",
    )

builder = StateGraph(State)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", research_node)
builder.add_node("coder", code_node)
graph = builder.compile()

```

```md-code__content
from IPython.display import display, Image

display(Image(graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

## Invoke the team [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/\#invoke-the-team "Permanent link")

With the graph created, we can now invoke it and see how it performs!

```md-code__content
for s in graph.stream(
    {"messages": [("user", "What's the square root of 42?")]}, subgraphs=True
):
    print(s)
    print("----")

```

```````md-code__content
((), {'supervisor': {'next': 'coder'}})
----
``````output
Python REPL can execute arbitrary code. Use with caution.
``````output
(('coder:a0c2a6de-4a2d-3573-4049-cba490183bc1',), {'agent': {'messages': [AIMessage(content=[{'text': "I'll help you calculate the square root of 42 using Python.", 'type': 'text'}, {'id': 'toolu_011Nsa2En2Qk1SsYBdG6zveY', 'input': {'code': 'import math\nprint(math.sqrt(42))'}, 'name': 'python_repl_tool', 'type': 'tool_use'}], additional_kwargs={}, response_metadata={'id': 'msg_016CdBcK9JKm39tsuGH6skhN', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'tool_use', 'stop_sequence': None, 'usage': {'input_tokens': 435, 'output_tokens': 82}}, id='run-f9be84c7-1569-4f53-9063-b1244339755b-0', tool_calls=[{'name': 'python_repl_tool', 'args': {'code': 'import math\nprint(math.sqrt(42))'}, 'id': 'toolu_011Nsa2En2Qk1SsYBdG6zveY', 'type': 'tool_call'}], usage_metadata={'input_tokens': 435, 'output_tokens': 82, 'total_tokens': 517, 'input_token_details': {}})]}})
----
(('coder:a0c2a6de-4a2d-3573-4049-cba490183bc1',), {'tools': {'messages': [ToolMessage(content='Successfully executed:\n\`\`\`python\nimport math\nprint(math.sqrt(42))\n\`\`\`\nStdout: 6.48074069840786\n', name='python_repl_tool', id='8b6bd229-5c63-43a4-9d63-e3b4a8468e21', tool_call_id='toolu_011Nsa2En2Qk1SsYBdG6zveY')]}})
----
(('coder:a0c2a6de-4a2d-3573-4049-cba490183bc1',), {'agent': {'messages': [AIMessage(content='The square root of 42 is approximately 6.4807 (rounded to 4 decimal places).', additional_kwargs={}, response_metadata={'id': 'msg_01QYQtz84F1Mgqyp2ecw4TEu', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'end_turn', 'stop_sequence': None, 'usage': {'input_tokens': 561, 'output_tokens': 28}}, id='run-b9dfff5d-f1c4-44d6-98d7-80f0e8548bcd-0', usage_metadata={'input_tokens': 561, 'output_tokens': 28, 'total_tokens': 589, 'input_token_details': {}})]}})
----
((), {'coder': {'messages': [HumanMessage(content='The square root of 42 is approximately 6.4807 (rounded to 4 decimal places).', additional_kwargs={}, response_metadata={}, name='coder')]}})
----
((), {'supervisor': {'next': '__end__'}})
----

```````

```md-code__content
for s in graph.stream(
    {
        "messages": [\
            (\
                "user",\
                "Find the latest GDP of New York and California, then calculate the average",\
            )\
        ]
    },
    subgraphs=True,
):
    print(s)
    print("----")

```

```md-code__content
((), {'supervisor': {'next': 'researcher'}})
----
(('researcher:7daea379-a5b6-6d3d-ef85-fffc96d7472e',), {'agent': {'messages': [AIMessage(content=[{'text': "I'll help you search for the GDP data of New York and California using the search tool. Then I'll note the values, but as instructed, I won't perform the mathematical calculation myself.", 'type': 'text'}, {'id': 'toolu_01S9hPD5nFsW1A2nE4fwCvRc', 'input': {'query': 'latest GDP of New York state 2023'}, 'name': 'tavily_search_results_json', 'type': 'tool_use'}], additional_kwargs={}, response_metadata={'id': 'msg_01RetKetMGpP2Q51w4R8N81e', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'tool_use', 'stop_sequence': None, 'usage': {'input_tokens': 442, 'output_tokens': 107}}, id='run-6e738192-18ae-4c1a-bbc0-f8b8509fe656-0', tool_calls=[{'name': 'tavily_search_results_json', 'args': {'query': 'latest GDP of New York state 2023'}, 'id': 'toolu_01S9hPD5nFsW1A2nE4fwCvRc', 'type': 'tool_call'}], usage_metadata={'input_tokens': 442, 'output_tokens': 107, 'total_tokens': 549, 'input_token_details': {}})]}})
----
(('researcher:7daea379-a5b6-6d3d-ef85-fffc96d7472e',), {'tools': {'messages': [ToolMessage(content='[{"url": "https://usafacts.org/metrics/gross-domestic-product-gdp-by-state-new-york/", "content": "Gross domestic product (GDP) state — New York (dollars) Adjustment. None. Adjustment. Frequency. Yearly. Frequency. In 2022 (most recent), Gross domestic product (GDP) was $2,053,179,700,000 in the United States for New York (state). ... August 25, 2023. Suggested citation: Explore in... Less detail"}, {"url": "https://www.osc.ny.gov/reports/finance/2023-fcr/economic-and-demographic-trends", "content": "These include, but are not limited to:\\nBecause Google Translate™ is intellectual property owned by Google Inc., you must use Google Translate™ in accord with the Google license agreement, which includes potential liability for misuse: Google Terms of Service.\\nOffice of the NEW YORK\\nSTATE COMPTROLLER\\nNYS Comptroller Thomas P. DiNapoli\\nMain navigation\\nGET to KnowNew York State ComptrollerThomas P. DiNapoli\\nRead BIO\\nGET to KnowNew York State ComptrollerThomas P. DiNapoli\\nMenu\\nEconomic and Demographic Trends\\n2023 Financial Condition Report For Fiscal Year Ended March 31, 2023\\nEmployment Still Below Pre- Pandemic Levels in 2022\\nNew York Ranked 45th Nationwide for Personal Income Growth in 2022\\nNYS GDP Nearly $1.6 Trillion in 2022\\nA state’s Gross Domestic Product (GDP) is the value of production originating from all industries in the state, as defined by the U.S. Bureau of Economic Analysis.\\n The State of New York, its officers, employees, and/or agents are not liable to you, or to third parties, for damages or losses of any kind arising out of, or in connection with, the use or performance of such information. New York’s Population Continued to Decline in 2022\\nBook traversal links for Economic and Demographic Trends\\nTell us more about you to receive content related to your area or interests.\\n The Office of the State Comptroller does not warrant, promise, assure or guarantee the accuracy of the translations provided."}, {"url": "https://www.statista.com/statistics/188087/gdp-of-the-us-federal-state-of-new-york-since-1997/", "content": "Industry Overview\\nDigital & Trend reports\\nOverview and forecasts on trending topics\\nIndustry & Market reports\\nIndustry and market insights and forecasts\\nCompanies & Products reports\\nKey figures and rankings about companies and products\\nConsumer & Brand reports\\nConsumer and brand insights and preferences in various industries\\nPolitics & Society reports\\nDetailed information about political and social topics\\nCountry & Region reports\\nAll key figures about countries and regions\\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\\nInsights on consumer attitudes and behavior worldwide\\nBusiness information on 100m+ public and private companies\\nExplore Company Insights\\nDetailed information for 39,000+ online stores and marketplaces\\nDirectly accessible data for 170 industries from 150+ countries\\nand over 1\xa0Mio. facts.\\n Transforming data into design:\\nStatista Content & Design\\nStrategy and business building for the data-driven economy:\\nU.S. real GDP of New York 2000-2022\\nReal gross domestic product of New York in the United States\\nfrom 2000 to 2022\\n(in billion U.S. dollars)\\nAdditional Information\\nShow sources information\\nShow publisher information\\nUse Ask Statista Research Service\\nMarch 2023\\nUnited States\\n2000 to 2022\\nData presented here is in 2012 chained U.S. dollars.\\n Statistics on\\n\\"\\nNew York\\n\\"\\nOther statistics that may interest you New York\\nPopulation\\nEconomy\\nEmployment & Earnings\\nState & Local Government\\nNew York City\\nFurther related statistics\\nFurther Content: You might find this interesting as well\\nStatistics\\nTopics Other statistics on the topic\\nEconomy\\nU.S. real gross domestic product 2022, by state\\nPolitics & Government\\nU.S. state and local government outstanding debt 2021, by state\\nDemographics\\nResident population in New York 1960-2022\\nEconomy\\nU.S. New York metro area GDP 2001-2022\\nYou only have access to basic statistics.\\n Customized Research & Analysis projects:\\nGet quick analyses with our professional research service\\nThe best of the best: the portal for top lists & rankings:\\n"}, {"url": "https://www.statista.com/statistics/306777/new-york-gdp-growth/", "content": "Industry Overview\\nDigital & Trend reports\\nOverview and forecasts on trending topics\\nIndustry & Market reports\\nIndustry and market insights and forecasts\\nCompanies & Products reports\\nKey figures and rankings about companies and products\\nConsumer & Brand reports\\nConsumer and brand insights and preferences in various industries\\nPolitics & Society reports\\nDetailed information about political and social topics\\nCountry & Region reports\\nAll key figures about countries and regions\\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\\nInsights on consumer attitudes and behavior worldwide\\nBusiness information on 100m+ public and private companies\\nExplore Company Insights\\nDetailed information for 39,000+ online stores and marketplaces\\nDirectly accessible data for 170 industries from 150+ countries\\nand over 1\xa0Mio. facts.\\n Other statistics on the topic\\nEconomy\\nU.S. real gross domestic product 2022, by state\\nPolitics & Government\\nU.S. state and local government outstanding debt 2021, by state\\nDemographics\\nResident population in New York 1960-2022\\nEconomy\\nU.S. New York metro area GDP 2001-2022\\nTo download this statistic in XLS format you need a Statista Account\\nTo download this statistic in PNG format you need a Statista Account\\nTo download this statistic in PDF format you need a Statista Account\\nTo download this statistic in PPT format you need a Statista Account\\nAs a Premium user you get access to the detailed source references and background information about this statistic.\\n Statistics on\\n\\"\\nNew York\\n\\"\\nOther statistics that may interest you New York\\nPopulation\\nEconomy\\nEmployment & Earnings\\nState & Local Government\\nNew York City\\nFurther related statistics\\nFurther Content: You might find this interesting as well\\nStatistics\\nTopics U.S. annual GDP growth in New York 2000-2022\\nAnnual percent change in the real gross domestic product of New York in the United States from 2000 to 2022\\nAdditional Information\\nShow sources information\\nShow publisher information\\nUse Ask Statista Research Service\\nOctober 2023\\nUnited States (New York)\\n2000 to 2022\\n Transforming data into design:\\nStatista Content & Design\\nStrategy and business building for the data-driven economy:\\nIndustry-specific and extensively researched technical data (partially from exclusive partnerships)."}, {"url": "https://www.bea.gov/news/2024/gross-domestic-product-state-and-personal-income-state-4th-quarter-2023-and-preliminary", "content": "Real gross domestic product (GDP) increased in all 50 states and the District of Columbia in the fourth quarter of 2023, with the percent change ranging from 6.7 percent in Nevada to 0.2 percent in Nebraska (table 1), according to statistics released today by the U.S. Bureau of Economic Analysis (BEA). Current-dollar GDP increased in 49 states and the District of Columbia."}]', name='tavily_search_results_json', id='a7ba20fa-57d5-43e9-9d15-29e4e6476edf', tool_call_id='toolu_01S9hPD5nFsW1A2nE4fwCvRc', artifact={'query': 'latest GDP of New York state 2023', 'follow_up_questions': None, 'answer': None, 'images': [], 'results': [{'title': 'Gross domestic product (GDP) - USAFacts', 'url': 'https://usafacts.org/metrics/gross-domestic-product-gdp-by-state-new-york/', 'content': 'Gross domestic product (GDP) state — New York (dollars) Adjustment. None. Adjustment. Frequency. Yearly. Frequency. In 2022 (most recent), Gross domestic product (GDP) was $2,053,179,700,000 in the United States for New York (state). ... August 25, 2023. Suggested citation: Explore in... Less detail', 'score': 0.99883956, 'raw_content': None}, {'title': 'Economic and Demographic Trends - Office of the New York State Comptroller', 'url': 'https://www.osc.ny.gov/reports/finance/2023-fcr/economic-and-demographic-trends', 'content': 'These include, but are not limited to:\nBecause Google Translate™ is intellectual property owned by Google Inc., you must use Google Translate™ in accord with the Google license agreement, which includes potential liability for misuse: Google Terms of Service.\nOffice of the NEW YORK\nSTATE COMPTROLLER\nNYS Comptroller Thomas P. DiNapoli\nMain navigation\nGET to KnowNew York State ComptrollerThomas P. DiNapoli\nRead BIO\nGET to KnowNew York State ComptrollerThomas P. DiNapoli\nMenu\nEconomic and Demographic Trends\n2023 Financial Condition Report For Fiscal Year Ended March 31, 2023\nEmployment Still Below Pre- Pandemic Levels in 2022\nNew York Ranked 45th Nationwide for Personal Income Growth in 2022\nNYS GDP Nearly $1.6 Trillion in 2022\nA state’s Gross Domestic Product (GDP) is the value of production originating from all industries in the state, as defined by the U.S. Bureau of Economic Analysis.\n The State of New York, its officers, employees, and/or agents are not liable to you, or to third parties, for damages or losses of any kind arising out of, or in connection with, the use or performance of such information. New York’s Population Continued to Decline in 2022\nBook traversal links for Economic and Demographic Trends\nTell us more about you to receive content related to your area or interests.\n The Office of the State Comptroller does not warrant, promise, assure or guarantee the accuracy of the translations provided.', 'score': 0.97339284, 'raw_content': None}, {'title': 'Real GDP New York U.S. 2023 | Statista', 'url': 'https://www.statista.com/statistics/188087/gdp-of-the-us-federal-state-of-new-york-since-1997/', 'content': 'Industry Overview\nDigital & Trend reports\nOverview and forecasts on trending topics\nIndustry & Market reports\nIndustry and market insights and forecasts\nCompanies & Products reports\nKey figures and rankings about companies and products\nConsumer & Brand reports\nConsumer and brand insights and preferences in various industries\nPolitics & Society reports\nDetailed information about political and social topics\nCountry & Region reports\nAll key figures about countries and regions\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\nInsights on consumer attitudes and behavior worldwide\nBusiness information on 100m+ public and private companies\nExplore Company Insights\nDetailed information for 39,000+ online stores and marketplaces\nDirectly accessible data for 170 industries from 150+ countries\nand over 1\xa0Mio. facts.\n Transforming data into design:\nStatista Content & Design\nStrategy and business building for the data-driven economy:\nU.S. real GDP of New York 2000-2022\nReal gross domestic product of New York in the United States\nfrom 2000 to 2022\n(in billion U.S. dollars)\nAdditional Information\nShow sources information\nShow publisher information\nUse Ask Statista Research Service\nMarch 2023\nUnited States\n2000 to 2022\nData presented here is in 2012 chained U.S. dollars.\n Statistics on\n"\nNew York\n"\nOther statistics that may interest you New York\nPopulation\nEconomy\nEmployment & Earnings\nState & Local Government\nNew York City\nFurther related statistics\nFurther Content: You might find this interesting as well\nStatistics\nTopics Other statistics on the topic\nEconomy\nU.S. real gross domestic product 2022, by state\nPolitics & Government\nU.S. state and local government outstanding debt 2021, by state\nDemographics\nResident population in New York 1960-2022\nEconomy\nU.S. New York metro area GDP 2001-2022\nYou only have access to basic statistics.\n Customized Research & Analysis projects:\nGet quick analyses with our professional research service\nThe best of the best: the portal for top lists & rankings:\n', 'score': 0.76454014, 'raw_content': None}, {'title': 'Annual GDP growth New York U.S. 2023 | Statista', 'url': 'https://www.statista.com/statistics/306777/new-york-gdp-growth/', 'content': 'Industry Overview\nDigital & Trend reports\nOverview and forecasts on trending topics\nIndustry & Market reports\nIndustry and market insights and forecasts\nCompanies & Products reports\nKey figures and rankings about companies and products\nConsumer & Brand reports\nConsumer and brand insights and preferences in various industries\nPolitics & Society reports\nDetailed information about political and social topics\nCountry & Region reports\nAll key figures about countries and regions\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\nInsights on consumer attitudes and behavior worldwide\nBusiness information on 100m+ public and private companies\nExplore Company Insights\nDetailed information for 39,000+ online stores and marketplaces\nDirectly accessible data for 170 industries from 150+ countries\nand over 1\xa0Mio. facts.\n Other statistics on the topic\nEconomy\nU.S. real gross domestic product 2022, by state\nPolitics & Government\nU.S. state and local government outstanding debt 2021, by state\nDemographics\nResident population in New York 1960-2022\nEconomy\nU.S. New York metro area GDP 2001-2022\nTo download this statistic in XLS format you need a Statista Account\nTo download this statistic in PNG format you need a Statista Account\nTo download this statistic in PDF format you need a Statista Account\nTo download this statistic in PPT format you need a Statista Account\nAs a Premium user you get access to the detailed source references and background information about this statistic.\n Statistics on\n"\nNew York\n"\nOther statistics that may interest you New York\nPopulation\nEconomy\nEmployment & Earnings\nState & Local Government\nNew York City\nFurther related statistics\nFurther Content: You might find this interesting as well\nStatistics\nTopics U.S. annual GDP growth in New York 2000-2022\nAnnual percent change in the real gross domestic product of New York in the United States from 2000 to 2022\nAdditional Information\nShow sources information\nShow publisher information\nUse Ask Statista Research Service\nOctober 2023\nUnited States (New York)\n2000 to 2022\n Transforming data into design:\nStatista Content & Design\nStrategy and business building for the data-driven economy:\nIndustry-specific and extensively researched technical data (partially from exclusive partnerships).', 'score': 0.7212526, 'raw_content': None}, {'title': 'Gross Domestic Product by State and Personal Income by State, 4th ...', 'url': 'https://www.bea.gov/news/2024/gross-domestic-product-state-and-personal-income-state-4th-quarter-2023-and-preliminary', 'content': 'Real gross domestic product (GDP) increased in all 50 states and the District of Columbia in the fourth quarter of 2023, with the percent change ranging from 6.7 percent in Nevada to 0.2 percent in Nebraska (table 1), according to statistics released today by the U.S. Bureau of Economic Analysis (BEA). Current-dollar GDP increased in 49 states and the District of Columbia.', 'score': 0.36139008, 'raw_content': None}], 'response_time': 2.31})]}})
----
(('researcher:7daea379-a5b6-6d3d-ef85-fffc96d7472e',), {'agent': {'messages': [AIMessage(content=[{'id': 'toolu_015fdnpWUiuEshsEwn2nBJ1g', 'input': {'query': 'latest GDP of California state 2023'}, 'name': 'tavily_search_results_json', 'type': 'tool_use'}], additional_kwargs={}, response_metadata={'id': 'msg_01Cksgb2aaqcD2bPtam5HDPF', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'tool_use', 'stop_sequence': None, 'usage': {'input_tokens': 2534, 'output_tokens': 66}}, id='run-11d924ba-a494-49d6-b649-ac961e31c79c-0', tool_calls=[{'name': 'tavily_search_results_json', 'args': {'query': 'latest GDP of California state 2023'}, 'id': 'toolu_015fdnpWUiuEshsEwn2nBJ1g', 'type': 'tool_call'}], usage_metadata={'input_tokens': 2534, 'output_tokens': 66, 'total_tokens': 2600, 'input_token_details': {}})]}})
----
(('researcher:7daea379-a5b6-6d3d-ef85-fffc96d7472e',), {'tools': {'messages': [ToolMessage(content='[{"url": "https://www.gov.ca.gov/2024/04/16/california-remains-the-worlds-5th-largest-economy/", "content": "California remains the 5th largest economy in the world since 2017. California is the 5th largest economy in the world for the seventh consecutive year, with a nominal GDP of nearly $3.9 trillion in 2023 and a growth rate of 6.1% since the year prior, according to the U.S. Bureau of Economic Analysis (BEA). On a per capita basis, California is"}, {"url": "https://usafacts.org/metrics/gross-domestic-product-gdp-by-state-california/", "content": "USAFacts -- In 2022 (most recent), Gross domestic product (GDP) was 3598102700000.0 in the United States for California (state). This increased by 224,862,000,000 or 6.67% from 2021. Highest: 3,598,102,700,000 in 2022."}, {"url": "https://www.statista.com/statistics/187834/gdp-of-the-us-federal-state-of-california-since-1997/", "content": "Industry Overview\\nDigital & Trend reports\\nOverview and forecasts on trending topics\\nIndustry & Market reports\\nIndustry and market insights and forecasts\\nCompanies & Products reports\\nKey figures and rankings about companies and products\\nConsumer & Brand reports\\nConsumer and brand insights and preferences in various industries\\nPolitics & Society reports\\nDetailed information about political and social topics\\nCountry & Region reports\\nAll key figures about countries and regions\\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\\nInsights on consumer attitudes and behavior worldwide\\nBusiness information on 100m+ public and private companies\\nExplore Company Insights\\nDetailed information for 39,000+ online stores and marketplaces\\nDirectly accessible data for 170 industries from 150+ countries\\nand over 1\xa0Mio. facts.\\n Statistics on\\n\\"\\nCalifornia\\n\\"\\nOther statistics that may interest you California\\nPopulation\\nEconomy\\nEmployment & Earnings\\nState & Local Government\\nMetro Areas\\nFurther related statistics\\nFurther Content: You might find this interesting as well\\nStatistics\\nTopics Other statistics on the topicCalifornia\\nEconomy\\nU.S. leading companies headquartered in California 2023, by number of employees\\nEconomy\\nU.S. average annual wages in California 2018-2026\\nEconomy\\nU.S. California fastest growing private companies 2023, by three year growth rate\\nResidential Real Estate\\nHourly wages needed to afford a two-bedroom apartment in California 2021-23, by metro\\nYou only have access to basic statistics.\\n Additional Information\\nShow sources information\\nShow publisher information\\nUse Ask Statista Research Service\\nMarch 2023\\nUnited States\\n2000 to 2022\\nData presented here is in 2012 chained U.S. dollars.\\n Transforming data into design:\\nStatista Content & Design\\nStrategy and business building for the data-driven economy:\\nU.S. real GDP of California 2000-2022\\nReal gross domestic product of California in the United States from 2000 to 2022\\n(in billion U.S. dollars)\\n"}, {"url": "https://www.bea.gov/news/2024/gross-domestic-product-state-and-personal-income-state-4th-quarter-2023-and-preliminary", "content": "Real gross domestic product (GDP) increased in all 50 states and the District of Columbia in the fourth quarter of 2023, with the percent change ranging from 6.7 percent in Nevada to 0.2 percent in Nebraska (table 1), according to statistics released today by the U.S. Bureau of Economic Analysis (BEA). Current-dollar GDP increased in 49 states and the District of Columbia."}, {"url": "https://www.bea.gov/news/2023/gross-domestic-product-state-and-personal-income-state-1st-quarter-2023", "content": "Real gross domestic product (GDP) increased in all 50 states and the District of Columbia in the first quarter of 2023, with the percent change ranging from 12.4 percent in North Dakota to 0.1 percent in Rhode Island and Alabama (table 1), according to statistics released today by the U.S. Bureau of Economic Analysis (BEA). Current-dollar GDP increased in 47 states and the District of Columbia"}]', name='tavily_search_results_json', id='77de7955-ba39-4db3-9460-1a2bd7f602fb', tool_call_id='toolu_015fdnpWUiuEshsEwn2nBJ1g', artifact={'query': 'latest GDP of California state 2023', 'follow_up_questions': None, 'answer': None, 'images': [], 'results': [{'title': "California Remains the World's 5th Largest Economy", 'url': 'https://www.gov.ca.gov/2024/04/16/california-remains-the-worlds-5th-largest-economy/', 'content': 'California remains the 5th largest economy in the world since 2017. California is the 5th largest economy in the world for the seventh consecutive year, with a nominal GDP of nearly $3.9 trillion in 2023 and a growth rate of 6.1% since the year prior, according to the U.S. Bureau of Economic Analysis (BEA). On a per capita basis, California is', 'score': 0.99338466, 'raw_content': None}, {'title': 'Gross domestic product (GDP) - USAFacts', 'url': 'https://usafacts.org/metrics/gross-domestic-product-gdp-by-state-california/', 'content': 'USAFacts -- In 2022 (most recent), Gross domestic product (GDP) was 3598102700000.0 in the United States for California (state). This increased by 224,862,000,000 or 6.67% from 2021. Highest: 3,598,102,700,000 in 2022.', 'score': 0.99128854, 'raw_content': None}, {'title': 'Real GDP California U.S. 2023 | Statista', 'url': 'https://www.statista.com/statistics/187834/gdp-of-the-us-federal-state-of-california-since-1997/', 'content': 'Industry Overview\nDigital & Trend reports\nOverview and forecasts on trending topics\nIndustry & Market reports\nIndustry and market insights and forecasts\nCompanies & Products reports\nKey figures and rankings about companies and products\nConsumer & Brand reports\nConsumer and brand insights and preferences in various industries\nPolitics & Society reports\nDetailed information about political and social topics\nCountry & Region reports\nAll key figures about countries and regions\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\nInsights on consumer attitudes and behavior worldwide\nBusiness information on 100m+ public and private companies\nExplore Company Insights\nDetailed information for 39,000+ online stores and marketplaces\nDirectly accessible data for 170 industries from 150+ countries\nand over 1\xa0Mio. facts.\n Statistics on\n"\nCalifornia\n"\nOther statistics that may interest you California\nPopulation\nEconomy\nEmployment & Earnings\nState & Local Government\nMetro Areas\nFurther related statistics\nFurther Content: You might find this interesting as well\nStatistics\nTopics Other statistics on the topicCalifornia\nEconomy\nU.S. leading companies headquartered in California 2023, by number of employees\nEconomy\nU.S. average annual wages in California 2018-2026\nEconomy\nU.S. California fastest growing private companies 2023, by three year growth rate\nResidential Real Estate\nHourly wages needed to afford a two-bedroom apartment in California 2021-23, by metro\nYou only have access to basic statistics.\n Additional Information\nShow sources information\nShow publisher information\nUse Ask Statista Research Service\nMarch 2023\nUnited States\n2000 to 2022\nData presented here is in 2012 chained U.S. dollars.\n Transforming data into design:\nStatista Content & Design\nStrategy and business building for the data-driven economy:\nU.S. real GDP of California 2000-2022\nReal gross domestic product of California in the United States from 2000 to 2022\n(in billion U.S. dollars)\n', 'score': 0.58112484, 'raw_content': None}, {'title': 'Gross Domestic Product by State and Personal Income by State, 4th ...', 'url': 'https://www.bea.gov/news/2024/gross-domestic-product-state-and-personal-income-state-4th-quarter-2023-and-preliminary', 'content': 'Real gross domestic product (GDP) increased in all 50 states and the District of Columbia in the fourth quarter of 2023, with the percent change ranging from 6.7 percent in Nevada to 0.2 percent in Nebraska (table 1), according to statistics released today by the U.S. Bureau of Economic Analysis (BEA). Current-dollar GDP increased in 49 states and the District of Columbia.', 'score': 0.5455884, 'raw_content': None}, {'title': 'Gross Domestic Product by State and Personal Income by State, 1st ...', 'url': 'https://www.bea.gov/news/2023/gross-domestic-product-state-and-personal-income-state-1st-quarter-2023', 'content': 'Real gross domestic product (GDP) increased in all 50 states and the District of Columbia in the first quarter of 2023, with the percent change ranging from 12.4 percent in North Dakota to 0.1 percent in Rhode Island and Alabama (table 1), according to statistics released today by the U.S. Bureau of Economic Analysis (BEA). Current-dollar GDP increased in 47 states and the District of Columbia', 'score': 0.40857172, 'raw_content': None}], 'response_time': 3.04})]}})
----
(('researcher:7daea379-a5b6-6d3d-ef85-fffc96d7472e',), {'agent': {'messages': [AIMessage(content="Based on the search results, I can provide you with the latest GDP figures for both states:\n\nNew York:\n- GDP: $2.053 trillion (2022 figures)\n\nCalifornia:\n- GDP: $3.9 trillion (2023 figures)\n\nAs instructed, I won't calculate the average, but I've provided you with the most recent GDP figures for both states. Note that the figures are from different years (2022 for NY and 2023 for CA), which should be considered when calculating the average.", additional_kwargs={}, response_metadata={'id': 'msg_013yuy2PoBUNSGNDCYXvUL27', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'end_turn', 'stop_sequence': None, 'usage': {'input_tokens': 3748, 'output_tokens': 120}}, id='run-d775159b-c114-4db5-b425-416f0f2f957c-0', usage_metadata={'input_tokens': 3748, 'output_tokens': 120, 'total_tokens': 3868, 'input_token_details': {}})]}})
----
((), {'researcher': {'messages': [HumanMessage(content="Based on the search results, I can provide you with the latest GDP figures for both states:\n\nNew York:\n- GDP: $2.053 trillion (2022 figures)\n\nCalifornia:\n- GDP: $3.9 trillion (2023 figures)\n\nAs instructed, I won't calculate the average, but I've provided you with the most recent GDP figures for both states. Note that the figures are from different years (2022 for NY and 2023 for CA), which should be considered when calculating the average.", additional_kwargs={}, response_metadata={}, name='researcher')]}})
----
((), {'supervisor': {'next': 'coder'}})
----
(('coder:2c47a596-d75b-143e-9b4a-a99f78779aec',), {'agent': {'messages': [AIMessage(content=[{'text': "I'll help calculate the average GDP between New York ($2.053 trillion) and California ($3.9 trillion).", 'type': 'text'}, {'id': 'toolu_019yGU4aBc9H73jfRWr1iKtf', 'input': {'code': 'ny_gdp = 2.053\nca_gdp = 3.9\n\naverage_gdp = (ny_gdp + ca_gdp) / 2\n\nprint(f"New York GDP: ${ny_gdp} trillion")\nprint(f"California GDP: ${ca_gdp} trillion")\nprint(f"Average GDP: ${average_gdp:.3f} trillion")'}, 'name': 'python_repl_tool', 'type': 'tool_use'}], additional_kwargs={}, response_metadata={'id': 'msg_01PGbexsWGaf4LQbKDH8toJs', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'tool_use', 'stop_sequence': None, 'usage': {'input_tokens': 558, 'output_tokens': 175}}, id='run-355dc875-adcc-436c-b0f3-675dc1c099bd-0', tool_calls=[{'name': 'python_repl_tool', 'args': {'code': 'ny_gdp = 2.053\nca_gdp = 3.9\n\naverage_gdp = (ny_gdp + ca_gdp) / 2\n\nprint(f"New York GDP: ${ny_gdp} trillion")\nprint(f"California GDP: ${ca_gdp} trillion")\nprint(f"Average GDP: ${average_gdp:.3f} trillion")'}, 'id': 'toolu_019yGU4aBc9H73jfRWr1iKtf', 'type': 'tool_call'}], usage_metadata={'input_tokens': 558, 'output_tokens': 175, 'total_tokens': 733, 'input_token_details': {}})]}})
----
(('coder:2c47a596-d75b-143e-9b4a-a99f78779aec',), {'tools': {'messages': [ToolMessage(content='Successfully executed:\n\`\`\`python\nny_gdp = 2.053\nca_gdp = 3.9\n\naverage_gdp = (ny_gdp + ca_gdp) / 2\n\nprint(f"New York GDP: ${ny_gdp} trillion")\nprint(f"California GDP: ${ca_gdp} trillion")\nprint(f"Average GDP: ${average_gdp:.3f} trillion")\n\`\`\`\nStdout: New York GDP: $2.053 trillion\nCalifornia GDP: $3.9 trillion\nAverage GDP: $2.976 trillion\n', name='python_repl_tool', id='39106042-eb3e-485c-8d62-bb2f572fbf8b', tool_call_id='toolu_019yGU4aBc9H73jfRWr1iKtf')]}})
----
(('coder:2c47a596-d75b-143e-9b4a-a99f78779aec',), {'agent': {'messages': [AIMessage(content="Based on the calculations:\n- New York's GDP: $2.053 trillion (2022)\n- California's GDP: $3.9 trillion (2023)\n- The average GDP between the two states is $2.976 trillion\n\nNote: As mentioned earlier, these GDP figures are from different years (2022 for NY and 2023 for CA), which should be taken into consideration when interpreting the average.", additional_kwargs={}, response_metadata={'id': 'msg_016GGgrPRH3psSoWUw7TzTQu', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'end_turn', 'stop_sequence': None, 'usage': {'input_tokens': 877, 'output_tokens': 98}}, id='run-55436cea-0fab-4fa3-a691-3a80a0afb431-0', usage_metadata={'input_tokens': 877, 'output_tokens': 98, 'total_tokens': 975, 'input_token_details': {}})]}})
----
((), {'coder': {'messages': [HumanMessage(content="Based on the calculations:\n- New York's GDP: $2.053 trillion (2022)\n- California's GDP: $3.9 trillion (2023)\n- The average GDP between the two states is $2.976 trillion\n\nNote: As mentioned earlier, these GDP figures are from different years (2022 for NY and 2023 for CA), which should be taken into consideration when interpreting the average.", additional_kwargs={}, response_metadata={}, name='coder')]}})
----
((), {'supervisor': {'next': '__end__'}})
----

```

## Comments

giscus

#### [15 reactions](https://github.com/langchain-ai/langgraph/discussions/683)

👍10🎉2❤️3

#### [34 comments](https://github.com/langchain-ai/langgraph/discussions/683)

#### ·

#### 31+ replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@wsligter](https://avatars.githubusercontent.com/u/32930112?u=b4e0f76821bf3214be1a134eb93ae064a281b0b5&v=4)wsligter](https://github.com/wsligter) [Jul 1, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-9924955)

Question: Why are we passing 2 system messages? Or are we not?

or is this a bug and should the second 'system' role be changed to 'user'?

prompt = ChatPromptTemplate.from\_messages(

\[\
\
("system", system\_prompt),\
\
MessagesPlaceholder(variable\_name="messages"),\
\
(\
\
"system",\
\
"Given the conversation above, who should act next?"\
\
" Or should we FINISH? Select one of: {options}",\
\
),\
\
\]

).partial(options=str(options), members=", ".join(members))

1

👍1

3 replies

[![@MinLee0210](https://avatars.githubusercontent.com/u/57653278?u=175010b24bc3a15a5705424badf9b18823bfd67d&v=4)](https://github.com/MinLee0210)

[MinLee0210](https://github.com/MinLee0210) [Oct 10, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10899059)

You are correct, and I have encountered a situation that seems problematic.

In detail, I attempted to change the LLM-core of the supervisor to Gemini. However, it failed to execute properly when two consecutive 'system' prompts were placed in the sequence.

[![@alexandrebcaruso](https://avatars.githubusercontent.com/u/6711738?v=4)](https://github.com/alexandrebcaruso)

[alexandrebcaruso](https://github.com/alexandrebcaruso) [Oct 10, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10903760)

1 - system prompt to instruct the agent what it is and what it does;

2 - human request;

3 - system prompt to look at the human request and decide which agent should act.

that's how it is supposed to work.

[![@cris-m](https://avatars.githubusercontent.com/u/29815096?u=4b55bcd0d0e557e3cc2a483bfd427627d7e52493&v=4)](https://github.com/cris-m)

[cris-m](https://github.com/cris-m) [Oct 16, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10960462)

is that even correct. it will throw an error:

```notranslate
/usr/local/lib/python3.10/dist-packages/langchain_anthropic/chat_models.py in _format_messages(messages)
    176         if message.type == "system":
    177             if i != 0:
--> 178                 raise ValueError("System message must be at beginning of message list.")
    179             if isinstance(message.content, list):
    180                 system = [\
\
ValueError: System message must be at beginning of message list.\
\
```\
\
[![@jacktang](https://avatars.githubusercontent.com/u/44341?u=712b59639318ec30767b582661b9da35bcd04a45&v=4)jacktang](https://github.com/jacktang) [Jul 2, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-9935720)\
\
```notranslate\
function_def = {\
    "name": "route",\
    "description": "Select the next role.",\
    "parameters": {\
        "title": "routeSchema",\
        "type": "object",\
        "properties": {\
            "next": {\
                "title": "Next",\
                "anyOf": [\
                    {"enum": options},\
                ],\
            }\
        },\
        "required": ["next"],\
    },\
}\
\
supervisor_chain = (\
    prompt\
    | llm.bind_functions(functions=[function_def], function_call="route")\
    | JsonOutputFunctionsParser()\
)\
\
```\
\
Is there any simple implementation for `route`?\
\
1\
\
👍1\
\
2 replies\
\
[![@ToxicHu](https://avatars.githubusercontent.com/u/43336311?v=4)](https://github.com/ToxicHu)\
\
[ToxicHu](https://github.com/ToxicHu) [Jul 24, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10132646)\
\
hello, have you found the implementation? i have the same question\
\
[![@marcammann](https://avatars.githubusercontent.com/u/49620?u=f326e14ae90e6977924bc93d58ab83471fcffccf&v=4)](https://github.com/marcammann)\
\
[marcammann](https://github.com/marcammann) [Aug 16, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10353739)\
\
I think the idea is that there is no implementation, only a schema. The JsonOutputFunctionsParser is then used to get the argument that was passed into the function. I _think_ technically this should be do-able by just requesting a structured output response format from the chain, i.e. { "next": "..." } instead of going through a function call?\
\
[![@vaibhavp4](https://avatars.githubusercontent.com/u/4822281?v=4)vaibhavp4](https://github.com/vaibhavp4) [Jul 3, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-9952382)\
\
How is the agent invoked with state without providing specific keys?\
\
1\
\
👍1\
\
1 reply\
\
[![@woodswift](https://avatars.githubusercontent.com/u/15988956?u=091d00f8d0f0b3e323f27f6495a877000e15b361&v=4)](https://github.com/woodswift)\
\
[woodswift](https://github.com/woodswift) [Aug 20, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10399762)\
\
Printing that state value in mid of run shows it is just like what get\_state() returns. But this is still a valid question requiring clarification.\
\
[![@intern162](https://avatars.githubusercontent.com/u/175585727?v=4)intern162](https://github.com/intern162) [Jul 29, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10178571)\
\
Can someone please tell me how/where is the supervisor giving the relevant prompt to the agents? Like who is telling the agent what to do?\
\
1\
\
1 reply\
\
[![@gtnpromtior](https://avatars.githubusercontent.com/u/179978446?u=fc38617ebc30b96b28b0313bd08a40f781a23a4f&v=4)](https://github.com/gtnpromtior)\
\
[gtnpromtior](https://github.com/gtnpromtior) [Oct 25, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11046938)\
\
each agent have it's own prompt.\
\
```notranslate\
meta_campaigns_agent = create_react_agent(\
    llm_mini,\
    tools=initialize_tools_v2(),\
    state_modifier=meta_prompt,\
)\
\
```\
\
[![@alysonhower](https://avatars.githubusercontent.com/u/102027527?u=7e4bd66671a5a27ce6d7b2a94d9557ee387cf7d9&v=4)alysonhower](https://github.com/alysonhower) [Jul 30, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10192666)\
\
laughing in "escreva um relatório sobre pikas"\
\
1\
\
😄4\
\
0 replies\
\
[![@Dumplingisabeast](https://avatars.githubusercontent.com/u/154963829?u=fc1d41f377521e5ab738a1cf90af81a1b30c984d&v=4)Dumplingisabeast](https://github.com/Dumplingisabeast) [Jul 31, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10201932)\
\
In the following, create\_agent mentions about "agent\_scratchpad" but i can't find it mentioned anywhere in the subsequent code. Can someone help me understand how it works? Is it necessary?\
\
def create\_agent(llm: ChatOpenAI, tools: list, system\_prompt: str):\
\
\# Each worker node will be given a name and some tools.\
\
prompt = ChatPromptTemplate.from\_messages(\
\
\[\
\
(\
\
"system",\
\
system\_prompt,\
\
),\
\
MessagesPlaceholder(variable\_name="messages"),\
\
MessagesPlaceholder(variable\_name="agent\_scratchpad"),\
\
\]\
\
)\
\
agent = create\_openai\_tools\_agent(llm, tools, prompt)\
\
executor = AgentExecutor(agent=agent, tools=tools)\
\
return executor\
\
1\
\
1 reply\
\
[![@intern162](https://avatars.githubusercontent.com/u/175585727?v=4)](https://github.com/intern162)\
\
[intern162](https://github.com/intern162) [Aug 3, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10230304)\
\
It is necessary for using create\_openai\_tools\_agent, without that it is not necessary to use one\
\
[![@Smone5](https://avatars.githubusercontent.com/u/19376953?u=39c7109f972629c692819a7ba1a1ff3c8c20ecb0&v=4)Smone5](https://github.com/Smone5) [Jul 31, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10205680)\
\
I had a problem executing the Python code portion of this. Changing this code helped me:\
\
# This executes code locally, which can be unsafe\
\
#python\_repl\_tool = PythonREPLTool()\
\
from langchain\_experimental.utilities import PythonREPL\
\
from langchain\_core.tools import tool\
\
repl = PythonREPL()\
\
[@tool](https://github.com/tool)\
\
def python\_repl(code: Annotated\[str, "The python coder to execute python tasks"\],):\
\
"""Use this to execute python code. If you want to see the output of a value,\
\
you should print if out with 'print(....)'. This is visiable to the user."""\
\
````notranslate\
try:\
    result= repl.run(code)\
except Exception as e:\
    return f"Failed to execute. Error: {repr(e)}"\
result_str = f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"\
return (\
    result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."\
)\
\
````\
\
1\
\
0 replies\
\
[![@grantwag](https://avatars.githubusercontent.com/u/77765995?v=4)grantwag](https://github.com/grantwag) [Aug 9, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10292081)\
\
Could this example please be updated to not use the legacy create\_openai\_tools\_agent() and AgentExecutor().\
\
1\
\
0 replies\
\
[![@westernspion](https://avatars.githubusercontent.com/u/33697117?u=d4d3731dc195b65eedecb3a8915859ad73499e45&v=4)westernspion](https://github.com/westernspion) [Aug 13, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10329565)\
\
For those of you here using AzureChatOpenAI - `parallel_tool_calls` is unsupported and is slated for release in Sept'24 [Azure/azure-rest-api-specs#29545](https://github.com/Azure/azure-rest-api-specs/issues/29545)\
\
Otherwise, you'll run into this on any complex query that triggers your supervisory agent to call >1 sub-agent in parallel\
\
```notranslate\
BadRequestError: Error code: 400 - {'error': {'message': "An assistant message with 'tool_calls' must be followed by tool messages responding to each 'tool_call_id'. The following tool_call_ids did not have response messages: call_...`\
\
```\
\
Anyone with a solution to disable this, or better, handle parallel tool calls, would be excellent.\
\
Otherwise, the only alternative is to rearchitect the overall workflow in such a way that it can't call more than 1 tool at a time.\
\
1\
\
👎1\
\
0 replies\
\
[![@alexandrebcaruso](https://avatars.githubusercontent.com/u/6711738?v=4)alexandrebcaruso](https://github.com/alexandrebcaruso) [Aug 14, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10337073)\
\
`openai.BadRequestError: Error code: 400 - {'object': 'error', 'message': "[{'type': 'extra_forbidden', 'loc': ('body', 'function_call'), 'msg': 'Extra inputs are not permitted', 'input': {'name': 'route'}}, {'type': 'extra_forbidden', 'loc': ('body', 'functions'), 'msg': 'Extra inputs are not permitted', 'input': [{'name': 'route', 'description': 'Select the next role.', 'parameters': {'title': 'routeSchema', 'type': 'object', 'properties': {'next': {'title': 'Next', 'anyOf': [{'enum': ['FINISH', 'Ageant 1', 'Agent 2']}]}}, 'required': ['next']}}]}]", 'type': 'BadRequestError', 'param': None, 'code': 400}`\
\
I'm using Lamma 3 with openai and I have a custom base\_url. I have single agents with tools running fine (with create\_sql\_agents).\
\
the problem:\
\
multi-agents using bind\_tools or bind\_functions (following exactly what this tutorial shows).\
\
thanks!\
\
1\
\
2 replies\
\
[![@alexandrebcaruso](https://avatars.githubusercontent.com/u/6711738?v=4)](https://github.com/alexandrebcaruso)\
\
[alexandrebcaruso](https://github.com/alexandrebcaruso) [Aug 21, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10410160)\
\
the issue is probably with the custom base URL. somehow it doesn't accept "functions" or "tools" parameters, although it is just a wrapper around openai.\
\
I don't get this issue when I use local lamma.cpp with llama 3.1 model.\
\
[![@waywooKwong](https://avatars.githubusercontent.com/u/141756962?u=7685fb1ff688842d41213ae591cbd3ac255bbf4a&v=4)](https://github.com/waywooKwong)\
\
[waywooKwong](https://github.com/waywooKwong) [Aug 27, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10457840)\
\
" bind\_functions " are only supported in ChatOpenAI,\
\
bind\_tools are supported in different models,\
\
**llama3.1** make sense because llama3.1 has been fine-tuned for tool use,\
\
as well as **llama3-groq-tool-use**\
\
these two models are given in the tutorial "Tool calling" part, i find it updates after llama3.1 coming out.\
\
[https://python.langchain.com/v0.2/docs/integrations/chat/ollama/](https://python.langchain.com/v0.2/docs/integrations/chat/ollama/)\
\
👍1\
\
[![@woodswift](https://avatars.githubusercontent.com/u/15988956?u=091d00f8d0f0b3e323f27f6495a877000e15b361&v=4)woodswift](https://github.com/woodswift) [Aug 20, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10399783)\
\
Could you provide an example to show the supervisor can manage two agents all together? The current examples only shows that supervisor can invoke one of them but not prove they can collaborate together. Thanks!\
\
1\
\
2 replies\
\
[![@alexandrebcaruso](https://avatars.githubusercontent.com/u/6711738?v=4)](https://github.com/alexandrebcaruso)\
\
[alexandrebcaruso](https://github.com/alexandrebcaruso) [Aug 21, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10410191)\
\
I think the idea of the implementation on this tutorial is to prove the agents can collaborate via a supervisor. did you check the previous tutorial? is about exactly that: multi-agent direct collaboration. hope it helps!\
\
[![@Yazan-Hamdan](https://avatars.githubusercontent.com/u/74962091?v=4)](https://github.com/Yazan-Hamdan)\
\
[Yazan-Hamdan](https://github.com/Yazan-Hamdan) [Jan 4](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11731891)\
\
edited\
\
[@woodswift](https://github.com/woodswift) I think this is what you are looking for\
\
[https://langchain-ai.github.io/langgraph/tutorials/multi\_agent/multi-agent-collaboration/](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/)\
\
[![@waywooKwong](https://avatars.githubusercontent.com/u/141756962?u=7685fb1ff688842d41213ae591cbd3ac255bbf4a&v=4)waywooKwong](https://github.com/waywooKwong) [Aug 27, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10457816)\
\
In router-chain building,\
\
"function\_def" and then "bind\_functions" are only supported in ChatOpenAI, so far I haven't checked out any other wrapper which contains this function.\
\
But i find that "bind\_tools" are supported by different models in different way.\
\
I suggest import model through "from langchain\_community import ChatOllama(or your model)" and checkout if the wrapper contains bind\_tools\
\
1\
\
1 reply\
\
[![@alexandrebcaruso](https://avatars.githubusercontent.com/u/6711738?v=4)](https://github.com/alexandrebcaruso)\
\
[alexandrebcaruso](https://github.com/alexandrebcaruso) [Aug 31, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10507288)\
\
Llama.cpp with Llama 3.1 supports bind\_tools\
\
[![@alexandrebcaruso](https://avatars.githubusercontent.com/u/6711738?v=4)alexandrebcaruso](https://github.com/alexandrebcaruso) [Aug 31, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10507347)\
\
it seems that the code was updated, and now the supervisor\_chain is wrapped in a function def:\
\
```notranslate\
def supervisor_agent(state):\
    supervisor_chain = (\
        prompt\
        | llm.with_structured_output(routeResponse)\
    )\
    return supervisor_chain.invoke(state)\
\
```\
\
I guess the node definition should also be udpated?\
\
`workflow.add_node("supervisor", supervisor_chain)`\
\
1\
\
👀1\
\
3 replies\
\
[![@RafaelRViana](https://avatars.githubusercontent.com/u/520424?u=79b4e227eab25704da151c1ccc43c1bc3d54c3c6&v=4)](https://github.com/RafaelRViana)\
\
[RafaelRViana](https://github.com/RafaelRViana) [Sep 1, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10509838)\
\
Contributor\
\
This function is not being used in no other part of the code. I don't know why it was created, maybe it is used in another example.\
\
If you remove function and use code (without invoke) outside function scope. This example works well.\
\
supervisor\_chain = supervisor\_chain = (\
\
prompt\
\
\| llm.with\_structured\_output(routeResponse)\
\
)\
\
workflow.add\_node("supervisor", supervisor\_chain)\
\
[![@TaisukeIto](https://avatars.githubusercontent.com/u/56746159?v=4)](https://github.com/TaisukeIto)\
\
[TaisukeIto](https://github.com/TaisukeIto) [Sep 21, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10710626)\
\
It seems there's an inconsistency due to a version update of the LangGraph package or something.\
\
The program in this tutorial doesn't work.\
\
Message integration doesn't seem to work properly.\
\
[![@TaisukeIto](https://avatars.githubusercontent.com/u/56746159?v=4)](https://github.com/TaisukeIto)\
\
[TaisukeIto](https://github.com/TaisukeIto) [Sep 21, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10710638)\
\
Sorry, I posted to the wrong place.\
\
It's the Customer Support Bot that's not working.\
\
[![@avfranco-br](https://avatars.githubusercontent.com/u/20467839?u=5c3ec3af04b6f428ec7db760a0881e90b2267761&v=4)avfranco-br](https://github.com/avfranco-br) [Sep 21, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10715374)\
\
At least for me, in this code `def supervisor_agent(state): supervisor_chain = ( prompt | llm.with_structured_output(routeResponse) ) return supervisor_chain.invoke(state)`, returning supervisor\_chain.invoke(state) was causing my the graph enter in a recursion loop. Removing the .invoke(state) it worked.\
\
1\
\
0 replies\
\
[![@inoue0426](https://avatars.githubusercontent.com/u/8393063?u=f362509118f0892b6800edf208ed3ce30e1c4abf&v=4)inoue0426](https://github.com/inoue0426) [Sep 23, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10720888)\
\
I downloaded this file and try with Ollama with below code.\
\
```\
# llm = ChatOpenAI(\
#     api_key="ollama",\
#     model="llama3.1",\
#     base_url="http://localhost:11434/v1",\
# )\
\
from langchain_ollama import ChatOllama\
llm = ChatOllama(model='llama3.1')\
```\
\
Then I got below error.\
\
```\
File ~/miniconda3/envs/multi/lib/python3.11/site-packages/langgraph/utils/runnable.py:159, in RunnableCallable.invoke(self, input, config, **kwargs)\
    157     context = copy_context()\
    158     context.run(_set_config_context, child_config)\
--> 159     ret = context.run(self.func, input, **kwargs)\
    160 except BaseException as e:\
    161     run_manager.on_chain_error(e)\
\
Cell In[5], line 8, in <lambda>(x)\
      6 conditional_map = {k: k for k in members}\
      7 conditional_map["FINISH"] = END\
----> 8 workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)\
      9 # Finally, add entrypoint\
     10 workflow.add_edge(START, "supervisor")\
\
KeyError: 'next'\
```\
\
How can I fix this?\
\
Full log\
\-\-\-------------------------------------------------------------------------\
KeyError Traceback (most recent call last)\
Cell In\[15\], line 1\
----\> 1 for s in graph.stream(\
2 {\
3 "messages": \[\
4 HumanMessage(content="Code hello world and print it to the terminal")\
5 \]\
6 }\
7 ):\
8 if "\_\_end\_\_" not in s:\
9 print(s)\
\
File ~/miniconda3/envs/multi/lib/python3.11/site-packages/langgraph/pregel/ **init**.py:1278, in Pregel.stream(self, input, config, stream\_mode, output\_keys, interrupt\_before, interrupt\_after, debug, subgraphs)\
\
1267 # Similarly to Bulk Synchronous Parallel / Pregel model\
\
1268 # computation proceeds in steps, while there are channel updates\
\
1269 # channel updates from step N are only visible in step N+1\
\
1270 # channels are guaranteed to be immutable for the duration of the step,\
\
1271 # with channel updates applied only at the transition between steps\
\
1272 while loop.tick(\
\
1273 input\_keys=self.input\_channels,\
\
1274 interrupt\_before=interrupt\_before\_,\
\
1275 interrupt\_after=interrupt\_after\_,\
\
1276 manager=run\_manager,\
\
1277 ):\
\
-\> 1278 for \_ in runner.tick(\
\
1279 loop.tasks.values(),\
\
1280 timeout=self.step\_timeout,\
\
1281 retry\_policy=self.retry\_policy,\
\
1282 get\_waiter=get\_waiter,\
\
1283 ):\
\
1284 # emit output\
\
1285 yield from output()\
\
1286 # emit output\
\
File ~/miniconda3/envs/multi/lib/python3.11/site-packages/langgraph/pregel/runner.py:52, in PregelRunner.tick(self, tasks, reraise, timeout, retry\_policy, get\_waiter)\
\
50 t = tasks\[0\]\
\
51 try:\
\
---\> 52 run\_with\_retry(t, retry\_policy)\
\
53 self.commit(t, None)\
\
54 except Exception as exc:\
\
File ~/miniconda3/envs/multi/lib/python3.11/site-packages/langgraph/pregel/retry.py:29, in run\_with\_retry(task, retry\_policy)\
\
27 task.writes.clear()\
\
28 # run the task\
\
---\> 29 task.proc.invoke(task.input, config)\
\
30 # if successful, end\
\
31 break\
\
File ~/miniconda3/envs/multi/lib/python3.11/site-packages/langgraph/utils/runnable.py:387, in RunnableSeq.invoke(self, input, config, \*\*kwargs)\
\
385 input = context.run(step.invoke, input, config, \*\*kwargs)\
\
386 else:\
\
--\> 387 input = context.run(step.invoke, input, config)\
\
388 # finish the root run\
\
389 except BaseException as e:\
\
File ~/miniconda3/envs/multi/lib/python3.11/site-packages/langgraph/utils/runnable.py:167, in RunnableCallable.invoke(self, input, config, \*\*kwargs)\
\
165 else:\
\
166 context.run(\_set\_config\_context, config)\
\
--\> 167 ret = context.run(self.func, input, \*\*kwargs)\
\
168 if isinstance(ret, Runnable) and self.recurse:\
\
169 return ret.invoke(input, config)\
\
File ~/miniconda3/envs/multi/lib/python3.11/site-packages/langgraph/graph/graph.py:94, in Branch.\_route(self, input, config, reader, writer)\
\
92 else:\
\
93 value = input\
\
---\> 94 result = self.path.invoke(value, config)\
\
95 return self.\_finish(writer, input, result, config)\
\
File ~/miniconda3/envs/multi/lib/python3.11/site-packages/langgraph/utils/runnable.py:159, in RunnableCallable.invoke(self, input, config, \*\*kwargs)\
\
157 context = copy\_context()\
\
158 context.run(\_set\_config\_context, child\_config)\
\
--\> 159 ret = context.run(self.func, input, \*\*kwargs)\
\
160 except BaseException as e:\
\
161 run\_manager.on\_chain\_error(e)\
\
Cell In\[11\], line 8, in (x)\
\
6 conditional\_map = {k: k for k in members}\
\
7 conditional\_map\["FINISH"\] = END\
\
----\> 8 workflow.add\_conditional\_edges("supervisor", lambda x: x\["next"\], conditional\_map)\
\
9 # Finally, add entrypoint\
\
10 workflow.add\_edge(START, "supervisor")\
\
KeyError: 'next'\
\
1\
\
1 reply\
\
[![@100101010](https://avatars.githubusercontent.com/u/36503136?u=9db1533f49533137882e26a01afc6f3f16fc0308&v=4)](https://github.com/100101010)\
\
[100101010](https://github.com/100101010) [Oct 18, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-10980559)\
\
Hello, i got the same error, and i revised the routeResponse function as follows. Subsequently, it works.\
\
```\
class routeResponse(BaseModel):\
    # next: Literal[*options]\
    next: Literal["Researcher", "Coder", "FINISH"]\
```\
\
4 hidden itemsLoad more…\
\
[![@ahammi](https://avatars.githubusercontent.com/u/45977120?v=4)ahammi](https://github.com/ahammi) [Nov 19, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11309089)\
\
I had to change in the supervisor\_node so it returns this : return {"messages":state\["messages"\],"next": next\_} instead of {"next": next\_} . I don't have any explanation but that fixed my issue. Cheers.\
\
1\
\
👍1\
\
2 replies\
\
[![@cris-m](https://avatars.githubusercontent.com/u/29815096?u=4b55bcd0d0e557e3cc2a483bfd427627d7e52493&v=4)](https://github.com/cris-m)\
\
[cris-m](https://github.com/cris-m) [Nov 20, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11318098)\
\
By including the state with `next_`, the returned result will be `{"messages": state["messages"], "next": next_}` instead of just `{"next": next_}`.\
\
Here's the updated code:\
\
```\
def supervisor_node(state: AgentState) -> AgentState:\
    messages = [\
        {"role": "system", "content": system_prompt},\
    ] + state["messages"]\
    response = llm.with_structured_output(Router).invoke(messages)\
    next_ = response["next"]\
    if next_ == "FINISH":\
        next_ = END\
\
    return {**state, "next": next_}\
```\
\
[![@ahammi](https://avatars.githubusercontent.com/u/45977120?v=4)](https://github.com/ahammi)\
\
[ahammi](https://github.com/ahammi) [Nov 20, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11319193)\
\
ok thanks a lot. Do you have an explanation why we need to do that ? because it looks like for others it's working without that. Thanks.\
\
[![@igoro1975](https://avatars.githubusercontent.com/u/4538009?u=90771326230b71024999e0115c5ea407b453f010&v=4)igoro1975](https://github.com/igoro1975) [Nov 27, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11397632)\
\
Hello, I use this approach and ask the supervisor not to call the next agent if a response to the user's input is received from the previous agent. However, the supervisor calls it anyway.\
\
Do I have a bug in my implementation, or should I consider a different approach?\
\
1\
\
2 replies\
\
[![@AshfaaqF](https://avatars.githubusercontent.com/u/175560745?v=4)](https://github.com/AshfaaqF)\
\
[AshfaaqF](https://github.com/AshfaaqF) [Dec 2, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11433330)\
\
Hi, were you able to find a solution, i am having the same issue here.\
\
[![@igoro1975](https://avatars.githubusercontent.com/u/4538009?u=90771326230b71024999e0115c5ea407b453f010&v=4)](https://github.com/igoro1975)\
\
[igoro1975](https://github.com/igoro1975) [Dec 3, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11447520)\
\
Hi,\
\
Improving the prompt of the supervisor solved the issue.\
\
[![@byrocuy](https://avatars.githubusercontent.com/u/9263303?u=2c5d02e21fecc4900181f8f4f555b5a381bd2bbe&v=4)byrocuy](https://github.com/byrocuy) [Dec 4, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11457889)\
\
In the `researcher_node` and `code_node`, why we pass back the response from AI as a HumanMessage to the supervisor? Can we just output directly to the user after the research\_node invocation?\
\
```notranslate\
def research_node(state: AgentState) -> AgentState:\
    result = research_agent.invoke(state)\
    return {\
        "messages": [\
            HumanMessage(content=result["messages"][-1].content, name="researcher")\
        ]\
    }\
\
```\
\
1\
\
2 replies\
\
[![@byrocuy](https://avatars.githubusercontent.com/u/9263303?u=2c5d02e21fecc4900181f8f4f555b5a381bd2bbe&v=4)](https://github.com/byrocuy)\
\
[byrocuy](https://github.com/byrocuy) [Dec 4, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11457914)\
\
Also, what benefits are we getting with passing `name="researcher"` in the HumanMessage? Where does it used?\
\
[![@Yazan-Hamdan](https://avatars.githubusercontent.com/u/74962091?v=4)](https://github.com/Yazan-Hamdan)\
\
[Yazan-Hamdan](https://github.com/Yazan-Hamdan) [Jan 4](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11731916)\
\
[@byrocuy](https://github.com/byrocuy) It makes more sense to use AIMessage instead of HumanMessage in this case, since its a reply from an Agent, but as functionality, there is no difference\
\
👍1\
\
[![@superpadil](https://avatars.githubusercontent.com/u/124871479?u=a5f604542454a81897467756e5beb2a9851ca81d&v=4)superpadil](https://github.com/superpadil) [Dec 5, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11468578)\
\
the agent sometime unecessarily looping sometimes even though it has the suitable answer for the query, is there any solution to this?\
\
1\
\
2 replies\
\
[![@byrocuy](https://avatars.githubusercontent.com/u/9263303?u=2c5d02e21fecc4900181f8f4f555b5a381bd2bbe&v=4)](https://github.com/byrocuy)\
\
[byrocuy](https://github.com/byrocuy) [Dec 5, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11468685)\
\
Using smarter model or adjust the system prompt to return to the user after it got the answer usually help for me.\
\
[![@Yazan-Hamdan](https://avatars.githubusercontent.com/u/74962091?v=4)](https://github.com/Yazan-Hamdan)\
\
[Yazan-Hamdan](https://github.com/Yazan-Hamdan) [Jan 4](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11731848)\
\
As [@byrocuy](https://github.com/byrocuy) said, System prompt enhancement would solve the issue, I also suggest to use a custom state instead of storing everything in messages state\
\
[![@akashAD98](https://avatars.githubusercontent.com/u/62583018?v=4)akashAD98](https://github.com/akashAD98) [Dec 8, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11497786)\
\
im getting output but its\
\
also i need to do two changes\
\
```notranslate\
def supervisor_node(state: MessagesState) -> Command[Literal["researcher", "coder", "__end__"]]:\
\
```\
\
```notranslate\
class Router(TypedDict):\
    """Worker to route to next. If no workers needed, route to FINISH."""\
\
    next: Literal["researcher", "coder", "FINISH"]\
\
```\
\
output:\
\
```notranslate\
Messages passed to LLM: [{'role': 'system', 'content': "You are a supervisor tasked with managing a conversation between the following workers: ['researcher', 'coder']. Given the following user request, respond with the worker to act next. Each worker will perform a task and respond with their results and status. When finished, respond with FINISH."}, HumanMessage(content="What's the square root of 42?", additional_kwargs={}, response_metadata={}, id='1380ed1b-29f7-4f2c-be19-6748a73196ae')]\
LLM Response: {'next': 'coder'}\
Goto: coder\
((), {'supervisor': None})\
----\
Python REPL can execute arbitrary code. Use with caution.\
(('coder:faa59424-9d4a-cc0b-f281-94d77075d3e9',), {'agent': {'messages': [AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_H78k40PZo32ss26pncc2aHEA', 'function': {'arguments': '{"code":"import math\\nmath.sqrt(42)"}', 'name': 'python_repl_tool'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 23, 'prompt_tokens': 96, 'total_tokens': 119, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-2024-08-06', 'system_fingerprint': 'fp_c7ca0ebaca', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-db79c2e1-9e66-4d47-ab51-acf6968f68e2-0', tool_calls=[{'name': 'python_repl_tool', 'args': {'code': 'import math\nmath.sqrt(42)'}, 'id': 'call_H78k40PZo32ss26pncc2aHEA', 'type': 'tool_call'}], usage_metadata={'input_tokens': 96, 'output_tokens': 23, 'total_tokens': 119, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}})\
----\
(('coder:faa59424-9d4a-cc0b-f281-94d77075d3e9',), {'tools': {'messages': [ToolMessage(content='Successfully executed:\n\\`\\`\\`python\nimport math\nmath.sqrt(42)\n\\`\\`\\`\nStdout: ', name='python_repl_tool', id='77edad3b-9dcb-40c5-b140-a2f5a4e10c32', tool_call_id='call_H78k40PZo32ss26pncc2aHEA')]}})\
----\
(('coder:faa59424-9d4a-cc0b-f281-94d77075d3e9',), {'agent': {'messages': [AIMessage(content='The square root of 42 is approximately 6.4807.', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 15, 'prompt_tokens': 154, 'total_tokens': 169, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-2024-08-06', 'system_fingerprint': 'fp_c7ca0ebaca', 'finish_reason': 'stop', 'logprobs': None}, id='run-8b8400a5-9d39-408f-a35b-e1e4d21dc643-0', usage_metadata={'input_tokens': 154, 'output_tokens': 15, 'total_tokens': 169, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}})\
----\
((), {'coder': {'messages': [HumanMessage(content='The square root of 42 is approximately 6.4807.', additional_kwargs={}, response_metadata={}, name='coder')]}})\
----\
Messages passed to LLM: [{'role': 'system', 'content': "You are a supervisor tasked with managing a conversation between the following workers: ['researcher', 'coder']. Given the following user request, respond with the worker to act next. Each worker will perform a task and respond with their results and status. When finished, respond with FINISH."}, HumanMessage(content="What's the square root of 42?", additional_kwargs={}, response_metadata={}, id='1380ed1b-29f7-4f2c-be19-6748a73196ae'), HumanMessage(content='The square root of 42 is approximately 6.4807.', additional_kwargs={}, response_metadata={}, name='coder', id='b3f4512f-d18f-4042-b791-80aca0ce5032')]\
LLM Response: {'next': 'FINISH'}\
Goto: __end__\
((), {'supervisor': None})\
\
```\
\
((), {'supervisor': None})\
\
1\
\
👍2\
\
3 replies\
\
[![@ShowRounak](https://avatars.githubusercontent.com/u/113605089?u=6f4ad076ad04b06ec8dd57948ad695cf31887ed4&v=4)](https://github.com/ShowRounak)\
\
[ShowRounak](https://github.com/ShowRounak) [Dec 25, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11662487)\
\
Hey did you find any solution for this {'supervisor': None} ?\
\
[![@Yazan-Hamdan](https://avatars.githubusercontent.com/u/74962091?v=4)](https://github.com/Yazan-Hamdan)\
\
[Yazan-Hamdan](https://github.com/Yazan-Hamdan) [Jan 4](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11731821)\
\
[@ShowRounak](https://github.com/ShowRounak) in the supervisor node, use this as a return command\
\
```notranslate\
return Command(goto=goto, update={**state})\
\
```\
\
👍1\
\
[![@imooger](https://avatars.githubusercontent.com/u/141046333?v=4)](https://github.com/imooger)\
\
[imooger](https://github.com/imooger) [Jan 8](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11770647)\
\
[@ShowRounak](https://github.com/ShowRounak) You have to use your own state instead of MessagesState and then update it.\
\
import operator\
\
class State(TypedDict):\
\
messages: Annotated\[list, operator.add\]\
\
next: str\
\
class Router(TypedDict):\
\
"""Worker to route to next. If no workers needed, route to FINISH."""\
\
```notranslate\
next: Literal[*options]\
\
```\
\
llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)\
\
def supervisor\_node(state: State) -> Command\[Literal\[\*members, " **end**"\]\]:\
\
messages = \[\
\
{"role": "system", "content": system\_prompt},\
\
\] \+ state\["messages"\]\
\
response = llm.with\_structured\_output(Router).invoke(messages)\
\
goto = response\["next"\]\
\
if goto == "FINISH":\
\
goto = END\
\
```notranslate\
return Command(goto=goto, update={'next': goto})\
\
```\
\
👍1\
\
[![@amine-amaach](https://avatars.githubusercontent.com/u/65183673?u=7a2fc153d38467c9b955f799fcfae1a5a39c8ab9&v=4)amine-amaach](https://github.com/amine-amaach) [Dec 10, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11521934)\
\
Could you please explain why you returned the agent's messages as **HumanMessage**? Does it make a difference? I tried both **HumanMessage** and **AIMessage** and noticed no difference.\
\
2\
\
👍2\
\
1 reply\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Jan 8](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11774729)\
\
Collaborator\
\
Some providers don't allow you to return AIMessage in the last position in the chat history\
\
[![@Omkar1634](https://avatars.githubusercontent.com/u/64948764?u=69b1b7804977fea7d6192cfff7f893f11e9108f1&v=4)Omkar1634](https://github.com/Omkar1634) [Dec 20, 2024](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11628848)\
\
When the supervisor calls the agent, I do not get a response.\
\
Supervisor code:\
\
```notranslate\
class Router(BaseModel):\
    """Worker to route to next. If no workers needed, route to FINISH."""\
    next: Literal["fan-engagement", "brand-building", "music-promotion", "music-monetization", "songwriting", "gigging", "music-distribution", "music-business", "feedback","FINISH"]\
\
def supervisor_node(state: MessagesState) -> MessagesState:\
    messages = [\
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},\
    ] + state["messages"]\
\
    print("Messages being sent to LLM:")\
    print(messages)\
\
    response = llm.with_structured_output(Router).invoke(messages,timeout=60)\
\
    print(f"Response type: {type(response)}")\
    print(f"Response contents: {response}")\
\
\
    goto = response.next\
\
    if goto == "FINISH":\
        goto = END\
\
    return {**state, "next": goto}\
\
```\
\
```notranslate\
agent code:\
gigging_agent = create_react_agent(\
    llm,\
    tools=tool,\
    state_modifier=gigging_prompt  # Use the gigging prompt\
)\
def gigging_node(state: MessagesState) -> Command[Literal["supervisor"]]:\
    print("Gigging node invoked")\
    try:\
        result = gigging_agent.invoke(state)\
        last_message = result["messages"][-1].content if result["messages"] else "No response"\
        print(f"gigging_node result: {last_message}")\
\
        if "complete" in last_message.lower():\
            return Command(\
                update={\
                    "messages": [\
                        HumanMessage(content=last_message, name="gigging")\
                    ]\
                },\
                goto="FINISH",\
            )\
\
        return Command(\
            update={\
                "messages": [\
                    HumanMessage(content=last_message, name="gigging")\
                ]\
            },\
            goto="supervisor",\
        )\
    except Exception as e:\
        print(f"Error in gigging_node: {e}")\
        return Command(update={}, goto="supervisor")\
\
```\
\
````notranslate\
#output:\
Messages being sent to LLM:\
[{'role': 'system', 'content': "You are a supervisor tasked with managing a conversation between the following workers: ['fan-engagement', 'brand-building', 'music-promotion', 'music-monetization', 'songwriting', 'gigging', 'music-distribution', 'music-business', 'feedback']. Given the following user request, respond with the worker to act next. Each worker will perform a task and respond with their results and status. When finished, respond with FINISH."}, HumanMessage(content='how can i increase my fan on Instagram?.', additional_kwargs={}, response_metadata={}, id='b0eed0b5-601a-41ac-9fc5-2e60cca1f24b')]\
Response type: <class 'src.agents.supervisor_node.Router'>\
Response contents: next='fan-engagement'\
((), {'supervisor': {'messages': [HumanMessage(content='how can i increase my fan on Instagram?.', additional_kwargs={}, response_metadata={}, id='b0eed0b5-601a-41ac-9fc5-2e60cca1f24b')]}}) ```\
\
````\
\
1\
\
0 replies\
\
[![@Layvier](https://avatars.githubusercontent.com/u/12390725?u=a42152fa8fccfefa380badef69f108e47811d4d2&v=4)Layvier](https://github.com/Layvier) [Jan 10](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11802781)\
\
I see we are passing `name="<agent_name>"` to the agents replies, as HumanMessage. Does the llm see this information, and can differentiate between a user message and an agent message?\
\
1\
\
2 replies\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Jan 10](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11802884)\
\
Collaborator\
\
yes, that's exactly the reason. unfortunately this is not supported by all LLM providers -- we're thinking about better approaches for this\
\
[![@Layvier](https://avatars.githubusercontent.com/u/12390725?u=a42152fa8fccfefa380badef69f108e47811d4d2&v=4)](https://github.com/Layvier)\
\
[Layvier](https://github.com/Layvier) [Jan 10](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11802921)\
\
thanks for the fast answer! Which ones are supporting this, I'm guessing OpenAI (I checked their doc though and didn't see much).\
\
I've been experimenting with wrapping worker messages in tags as such:\
\
```notranslate\
async def research_agent_node(state: AgentState, config: RunnableConfig) -> Command[Literal["main_supervisor"]]:\
    result = await research_agent.ainvoke(state, config)\
    reply = result["messages"][-1].content\
    wrapped_reply = f"""<research_agent>\
{reply}\
</research_agent>\
"""\
    return Command(\
        update={"messages": [HumanMessage(content=wrapped_reply, name="research_agent")]},\
        goto="main_supervisor",\
    )\
\
```\
\
It's ok, but then I need a response writer node afterwards\
\
[![@severin-stadler](https://avatars.githubusercontent.com/u/84959706?v=4)severin-stadler](https://github.com/severin-stadler) [Jan 27](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-11967039)\
\
I am having some trouble with the react agents when using them with langgraph. I am following this pattern roughly when creating them and have code that looks something like this:\
\
```\
math_agent= create_react_agent(\
    llm,\
    [simple_math],\
    state_modifier=f"..."\
)\
...\
\
def math_(state: State) -> Command[Literal["supervisor"]]:\
    result = math_agent.invoke(state)\
    return Command(\
        update={\
            "messages": [\
                HumanMessage(content=result["messages"][-1].content, name="math_agent")\
            ]\
        },\
        goto="supervisor",\
    )\
```\
\
However two out of three times I am getting the following error using AzureChatOpenAI:\
\
```notranslate\
Error code: 400 - {'error': {'message': "'math_agent.functions.simple_math' does not match '^[a-zA-Z0-9_-]{1,64}$'....\
\
```\
\
does anyone know why this happens?\
\
1\
\
0 replies\
\
[![@BlakeQG](https://avatars.githubusercontent.com/u/116970615?v=4)BlakeQG](https://github.com/BlakeQG) [Feb 1](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-12024077)\
\
edited\
\
For this structure, every time when the user starts a conversion, does it mean the supervisor\_node would start from beginning (in other words, ignore previous discussion?). I see in the supervisor\_node, it adds the system\_prompt everytime, so just wonder\
\
```notranslate\
def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:\
    messages = [\
        {"role": "system", "content": system_prompt},\
    ] + state["messages"]\
\
```\
\
1\
\
0 replies\
\
[![@rickywck](https://avatars.githubusercontent.com/u/23309171?v=4)rickywck](https://github.com/rickywck) [Feb 12](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-12179281)\
\
With this example code, how does the LLM decide which tool to be used? With this code (after fixing the issue by adding explicit end to the list), I found that only OpenAI LLM can do the job correctly consistently. For other LLMs, many of them have issue to determine the next node correctly, e.g. when I used Gemini-Flash-2.0 to calculate the square root, it almost always recommended to route to the researcher node. The prompt itself doesn't seem to have any description and capability of those nodes, so the LLM will need to guess what is the next node just by the name of the tool?\
\
1\
\
0 replies\
\
[![@mtrhnv](https://avatars.githubusercontent.com/u/135822323?v=4)mtrhnv](https://github.com/mtrhnv) [Mar 4](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-12389755)\
\
edited\
\
Why Agents respond as a HumanMessage?\
\
Is it essential for a supervised agents to always act like a Human team?\
\
1\
\
0 replies\
\
[![@robyattoillah](https://avatars.githubusercontent.com/u/199728104?u=47ea3dccc13904cede68d20d00abe13c6ded6493&v=4)robyattoillah](https://github.com/robyattoillah) [Mar 24](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-12596398)\
\
Which graph I should pass the checkpointer? Am I should pass the checkpointer only in the supervisor graph, or need to pass both in supervisor and subgraphs?\
\
1\
\
0 replies\
\
[![@bhavan-kaya](https://avatars.githubusercontent.com/u/145102872?u=446bd12e4ea4c2e4b68fb9bb33eefac0e93a2d1c&v=4)bhavan-kaya](https://github.com/bhavan-kaya) [27 days ago](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-12653230)\
\
edited\
\
I'm trying to get this working with streaming\
\
```\
for s in graph.stream(\
    input=(\
        Command(resume=request.message)\
        if interrupt_exists\
        else {"messages": [("user", request.message)]}\
    ),\
    config=graph_config,\
    subgraphs=True,\
    stream_mode=["messages"],\
):\
    if s[1] == "messages":\
        if isinstance(s[-1][0], AIMessageChunk):\
            yield content\
```\
\
But I'm actually facing an issue where all the content is getting sent instead of only the message\
\
For example\
\
This is what I get as the response\
\
{"next":"agentnode-node-2"}I’m ready to help! Please let me know what specific topic or question you would like me to research, and I will gather the relevant information for you.{"next":" _end_\_"}\
\
But I only need\
\
`I’m ready to help! Please let me know what specific topic or question you would like me to research, and I will gather the relevant information for you.` to be yield\
\
1\
\
0 replies\
\
[![@ForeverYoungJay](https://avatars.githubusercontent.com/u/52807318?v=4)ForeverYoungJay](https://github.com/ForeverYoungJay) [3 days ago](https://github.com/langchain-ai/langgraph/discussions/683#discussioncomment-12895270)\
\
why the supervisor can‘t be agent？ only llm?\
\
1\
\
0 replies\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Fmulti_agent%2Fagent_supervisor%2F)