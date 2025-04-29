[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/#multi-agent-network)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/multi_agent/multi-agent-collaboration.ipynb "Edit this page")

# Multi-agent network [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/\#multi-agent-network "Permanent link")

A single agent can usually operate effectively using a handful of tools within a single domain, but even using powerful models like `gpt-4`, it can be less effective at using many tools.

One way to approach complicated tasks is through a "divide-and-conquer" approach: create a specialized agent for each task or domain and route tasks to the correct "expert". This is an example of a [multi-agent network](https://langchain-ai.github.io/langgraph/concepts/multi_agent/#network) architecture.

This notebook (inspired by the paper [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation](https://arxiv.org/abs/2308.08155), by Wu, et. al.) shows one way to do this using LangGraph.

The resulting graph will look something like the following diagram:

![multi_agent diagram](<Base64-Image-Removed>)

Before we get started, a quick note: this and other multi-agent notebooks are designed to show _how_ you can implement certain design patterns in LangGraph. If the pattern suits your needs, we recommend combining it with some of the other fundamental patterns described elsewhere in the docs for best performance.

## Setup [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/\#setup "Permanent link")

First, let's install our required packages and set our API keys:

```md-code__content
%%capture --no-stderr
%pip install -U langchain_community langchain_anthropic langchain_experimental matplotlib langgraph

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


## Define tools [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/\#define-tools "Permanent link")

We will also define some tools that our agents will use in the future

API Reference: [TavilySearchResults](https://python.langchain.com/api_reference/community/tools/langchain_community.tools.tavily_search.tool.TavilySearchResults.html) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [PythonREPL](https://python.langchain.com/api_reference/experimental/utilities/langchain_experimental.utilities.python.PythonREPL.html)

```md-code__content
from typing import Annotated

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

tavily_tool = TavilySearchResults(max_results=5)

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
    result_str = f"Successfully executed:\n\`\`\`python\n{code}\n\`\`\`\nStdout: {result}"
    return (
        result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."
    )

```

## Create graph [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/\#create-graph "Permanent link")

Now that we've defined our tools and made some helper functions, will create the individual agents below and tell them how to talk to each other using LangGraph.

### Define Agent Nodes [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/\#define-agent-nodes "Permanent link")

We now need to define the nodes.

First, we'll create a utility to create a system prompt for each agent.

```md-code__content
def make_system_prompt(suffix: str) -> str:
    return (
        "You are a helpful AI assistant, collaborating with other assistants."
        " Use the provided tools to progress towards answering the question."
        " If you are unable to fully answer, that's OK, another assistant with different tools "
        " will help where you left off. Execute what you can to make progress."
        " If you or any of the other assistants have the final answer or deliverable,"
        " prefix your response with FINAL ANSWER so the team knows to stop."
        f"\n{suffix}"
    )

```

API Reference: [BaseMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.base.BaseMessage.html) \| [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html) \| [ChatAnthropic](https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [Command](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Command)

```md-code__content
from typing import Literal

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.graph import MessagesState, END
from langgraph.types import Command

llm = ChatAnthropic(model="claude-3-5-sonnet-latest")

def get_next_node(last_message: BaseMessage, goto: str):
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return END
    return goto

# Research agent and node
research_agent = create_react_agent(
    llm,
    tools=[tavily_tool],
    prompt=make_system_prompt(
        "You can only do research. You are working with a chart generator colleague."
    ),
)

def research_node(
    state: MessagesState,
) -> Command[Literal["chart_generator", END]]:
    result = research_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "chart_generator")
    # wrap in a human message, as not all providers allow
    # AI message at the last position of the input messages list
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="researcher"
    )
    return Command(
        update={
            # share internal message history of research agent with other agents
            "messages": result["messages"],
        },
        goto=goto,
    )

# Chart generator agent and node
# NOTE: THIS PERFORMS ARBITRARY CODE EXECUTION, WHICH CAN BE UNSAFE WHEN NOT SANDBOXED
chart_agent = create_react_agent(
    llm,
    [python_repl_tool],
    prompt=make_system_prompt(
        "You can only generate charts. You are working with a researcher colleague."
    ),
)

def chart_node(state: MessagesState) -> Command[Literal["researcher", END]]:
    result = chart_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "researcher")
    # wrap in a human message, as not all providers allow
    # AI message at the last position of the input messages list
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="chart_generator"
    )
    return Command(
        update={
            # share internal message history of chart agent with other agents
            "messages": result["messages"],
        },
        goto=goto,
    )

```

### Define the Graph [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/\#define-the-graph "Permanent link")

We can now put it all together and define the graph!

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START)

```md-code__content
from langgraph.graph import StateGraph, START

workflow = StateGraph(MessagesState)
workflow.add_node("researcher", research_node)
workflow.add_node("chart_generator", chart_node)

workflow.add_edge(START, "researcher")
graph = workflow.compile()

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

## Invoke [¶](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/\#invoke "Permanent link")

With the graph created, you can invoke it! Let's have it chart some stats for us.

```md-code__content
events = graph.stream(
    {
        "messages": [\
            (\
                "user",\
                "First, get the UK's GDP over the past 5 years, then make a line chart of it. "\
                "Once you make the chart, finish.",\
            )\
        ],
    },
    # Maximum number of steps to take in the graph
    {"recursion_limit": 150},
)
for s in events:
    print(s)
    print("----")

```

```````md-code__content
{'researcher': {'messages': [HumanMessage(content="First, get the UK's GDP over the past 5 years, then make a line chart of it. Once you make the chart, finish.", additional_kwargs={}, response_metadata={}, id='fa1f5e95-9e1a-47d4-b4b6-e93f345e339d'), AIMessage(content=[{'text': "I'll help search for the UK's GDP data over the past 5 years. Then my colleague can help create the line chart.", 'type': 'text'}, {'id': 'toolu_01Jd9dxa4Ss2NhzBhCuwUX3E', 'input': {'query': 'UK GDP annual data past 5 years 2019-2023'}, 'name': 'tavily_search_results_json', 'type': 'tool_use'}], additional_kwargs={}, response_metadata={'id': 'msg_014nCkfVHnG6LAsiS6pY7zcd', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'tool_use', 'stop_sequence': None, 'usage': {'input_tokens': 555, 'output_tokens': 101}}, id='run-e2297529-9972-4de6-835d-23d920b0e29b-0', tool_calls=[{'name': 'tavily_search_results_json', 'args': {'query': 'UK GDP annual data past 5 years 2019-2023'}, 'id': 'toolu_01Jd9dxa4Ss2NhzBhCuwUX3E', 'type': 'tool_call'}], usage_metadata={'input_tokens': 555, 'output_tokens': 101, 'total_tokens': 656, 'input_token_details': {}}), ToolMessage(content='[{"url": "https://www.macrotrends.net/global-metrics/countries/GBR/united-kingdom/gdp-gross-domestic-product", "content": "Dollar figures for GDP are converted from domestic currencies using single year official exchange rates. For a few countries where the official exchange rate does not reflect the rate effectively applied to actual foreign exchange transactions, an alternative conversion factor is used. U.K. gdp for 2023 was $3,340.03B, a 8.13% increase from 2022."}, {"url": "https://www.statista.com/topics/3795/gdp-of-the-uk/", "content": "Monthly growth of gross domestic product in the United Kingdom from January 2019 to November 2023\\nContribution to GDP growth in the UK 2023, by sector\\nContribution to gross domestic product growth in the United Kingdom in January 2023, by sector\\nGDP growth rate in the UK 1999-2021, by country\\nAnnual growth rates of gross domestic product in the United Kingdom from 1999 to 2021, by country\\nGDP growth rate in the UK 2021, by region\\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\\nGDP growth of Scotland 2021, by local area\\nAnnual growth rates of gross domestic product in Scotland in 2021, by local (ITL 3) area\\nGDP growth of Wales 2021, by local area\\nAnnual growth rates of gross domestic product in Wales in 2021, by local (ITL 3) area\\nGDP growth of Northern Ireland 2021, by local area\\nAnnual growth rates of gross domestic product in Northern Ireland in 2021, by local (ITL 3) area\\nGDP per capita\\nGDP per capita\\nGDP per capita in the UK 1955-2022\\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\\nAnnual GDP per capita growth in the UK 1956-2022\\nAnnual GDP per capita growth in the United Kingdom from 1956 to 2022\\nQuarterly GDP per capita in the UK 2019-2023\\nQuarterly GDP per capita in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\\nQuarterly GDP per capita growth in the UK 2019-2023\\nQuarterly GDP per capita growth in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\\nGDP per capita of the UK 1999-2021, by country\\nGross domestic product per capita of the United Kingdom from 1999 to 2021, by country (in GBP)\\nGDP per capita of the UK 2021, by region\\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\\nGlobal Comparisons\\nGlobal Comparisons\\nCountries with the largest gross domestic product (GDP) 2022\\n Monthly GDP of the UK 2019-2023\\nMonthly index of gross domestic product in the United Kingdom from January 2019 to November 2023 (2019=100)\\nGVA of the UK 2022, by sector\\nGross value added of the United Kingdom in 2022, by industry sector (in million GBP)\\nGDP of the UK 2021, by country\\nGross domestic product of the United Kingdom in 2021, by country (in million GBP)\\nGDP of the UK 2021, by region\\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\\nGDP of Scotland 2021, by local area\\nGross domestic product of Scotland in 2021, by local (ITL 3) area (in million GBP)\\nGDP of Wales 2021, by local area\\nGross domestic product of Wales in 2021, by local (ITL 3) area (in million GBP)\\nGDP of Northern Ireland 2021, by local area\\nGross domestic product of Northern Ireland in 2021, by local (ITL 3) area (in million GBP)\\nGDP growth\\nGDP growth\\nGDP growth forecast for the UK 2000-2028\\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\\nAnnual GDP growth in the UK 1949-2022\\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\\nQuarterly GDP growth of the UK 2019-2023\\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023\\nMonthly GDP growth of the UK 2019-2023\\n Transforming data into design:\\nStatista Content & Design\\nStrategy and business building for the data-driven economy:\\nUK GDP - Statistics & Facts\\nUK economy expected to shrink in 2023\\nCharacteristics of UK GDP\\nKey insights\\nDetailed statistics\\nGDP of the UK 1948-2022\\nDetailed statistics\\nAnnual GDP growth in the UK 1949-2022\\nDetailed statistics\\nGDP per capita in the UK 1955-2022\\nEditor’s Picks\\nCurrent statistics on this topic\\nCurrent statistics on this topic\\nKey Economic Indicators\\nMonthly GDP growth of the UK 2019-2023\\nKey Economic Indicators\\nMonthly GDP of the UK 2019-2023\\nKey Economic Indicators\\nContribution to GDP growth in the UK 2023, by sector\\nRelated topics\\nRecommended\\nRecommended statistics\\nGDP\\nGDP\\nGDP of the UK 1948-2022\\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\\nQuarterly GDP of the UK 2019-2023\\nQuarterly gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in million GBP)\\n The 20 countries with the largest gross domestic product (GDP) in 2022 (in billion U.S. dollars)\\nGDP of European countries in 2022\\nGross domestic product at current market prices of selected European countries in 2022 (in million euros)\\nReal GDP growth rates in Europe 2023\\nAnnual real gross domestic product (GDP) growth rate in European countries in 2023\\nGross domestic product (GDP) of Europe\'s largest economies 1980-2028\\nGross domestic product (GDP) at current prices of Europe\'s largest economies from 1980 to 2028 (in billion U.S dollars)\\nUnited Kingdom\'s share of global gross domestic product (GDP) 2028\\nUnited Kingdom (UK): Share of global gross domestic product (GDP) adjusted for Purchasing Power Parity (PPP) from 2018 to 2028\\nRelated topics\\nRecommended\\nReport on the topic\\nKey figures\\nThe most important key figures provide you with a compact summary of the topic of \\"UK GDP\\" and take you straight to the corresponding statistics.\\n Industry Overview\\nDigital & Trend reports\\nOverview and forecasts on trending topics\\nIndustry & Market reports\\nIndustry and market insights and forecasts\\nCompanies & Products reports\\nKey figures and rankings about companies and products\\nConsumer & Brand reports\\nConsumer and brand insights and preferences in various industries\\nPolitics & Society reports\\nDetailed information about political and social topics\\nCountry & Region reports\\nAll key figures about countries and regions\\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\\nInsights on consumer attitudes and behavior worldwide\\nBusiness information on 100m+ public and private companies\\nExplore Company Insights\\nDetailed information for 39,000+ online stores and marketplaces\\nDirectly accessible data for 170 industries from 150+ countries\\nand over 1\xa0Mio. facts.\\n"}, {"url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB", "content": "GDP growth (annual %) - United Kingdom | Data - World Bank Data"}, {"url": "https://www.statista.com/topics/6500/the-british-economy/", "content": "Output per hour worked in the UK 1971 to 2023\\nEconomic output per hour worked in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023 (2019=100)\\nAnnual unemployment rate in the UK 2000-2028\\nAnnual unemployment rate in the United Kingdom from 2000 to 2028\\nInflation\\nInflation\\nInflation rate in the UK 1989-2023\\nInflation rate for the Consumer Price Index (CPI) in the United Kingdom from January 1989 to October 2023\\nRPI inflation rate in the UK 1948-2023\\nInflation rate for the Retail Price Index (RPI) in the United Kingdom from June 1948 to October 2023\\nCPIH inflation rate in the UK 1989-2023\\nInflation rate for the Consumer Price Index including owner occupiers\' housing costs (CPIH) in the United Kingdom from January 1989 to October 2023\\nPPI in the UK 2010-2023\\nProducer Price Index (PPI) in the United Kingdom from October 2010 to October 2023\\nCPI inflation rate in the UK 2023, by sector\\nInflation rate for the Consumer Price Index (CPI) in the United Kingdom in October 2023, by sector\\nConsumer Price Index in the UK 1988-2023\\nConsumer Price Index (CPI) in the United Kingdom from 1st quarter 1988 to 3rd quarter 2023\\nRetail Price Index in the UK 1987-2023\\nRetail Price Index (RPI) in the United Kingdom from 1st quarter 1987 to 3rd quarter 2023\\nConsumer Price Index including housing in the UK 1988-2023\\nConsumer Price Index including owner occupiers\' housing costs (CPIH) in the United Kingdom from 1st quarter 1988 to 3rd quarter 2023\\nRPI annual inflation rate UK 2000-2028\\nAnnual inflation rate of the Retail Price Index in the United Kingdom from 2000 to 2028\\nCPI annual inflation rate UK 2000-2028\\nAnnual inflation rate of the Consumer Price Index in the United Kingdom from 2000 to 2028\\nGovernment finances\\nGovernment finances\\nGovernment spending as a percentage of GDP in the UK 1900-2029\\nTotal managed expenditure expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\\nGovernment revenue as a percentage of GDP in the UK 1900-2029\\nTotal public sector current receipts expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29 (in million GBP)\\nGovernment borrowing as a percentage of GDP in the UK 1900-2029\\nPublic sector borrowing expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\\nNational debt as a percentage of GDP in the UK 1900-2029\\nPublic sector net debt expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\\nPublic sector spending in the United Kingdom 2023/24\\nBudgeted public sector expenditure on services in the United Kingdom in 2023/24, by function (in billion GBP)\\nGovernment revenue sources in the United Kingdom 2023/24\\nExpected public sector current receipts in the United Kingdom in 2023/24, by function (in billion GBP)\\nBusiness Enterprise\\nBusiness Enterprise\\nLargest companies in the United Kingdom based on revenue 2022\\nLargest companies in the United Kingdom based on revenue in 2022 (in billion US dollars)\\nLargest UK companies based on number of global employees 2020\\nLargest companies based in the United Kingdom on number of employees worldwide in 2020 (in 1,000s)\\nNumber of private sector businesses in the UK 2000-2023\\nNumber of private sector businesses in the United Kingdom from 2000 to 2023 (in millions)\\nNumber of private sector businesses in the UK 2023, by sector\\nNumber of private sector businesses in the United Kingdom in 2023, by sector\\nNumber of businesses by enterprise size in the UK 2023\\nNumber of private sector businesses in the United Kingdom in 2023, by employment size\\nNumber of private sector businesses in the UK 2023, by region\\nNumber of private sector businesses in the United Kingdom in 2023, by region\\nNumber of local business units in the UK 2012-2023\\nNumber of local units in VAT and/or PAYE based enterprises in the United Kingdom from 2012 to 2023 (in millions)\\nBusiness investment index in the UK 1997-2023\\nBusiness investment index in the United Kingdom from 1st quarter 1997 to 2nd quarter 2023 (Q1 1997=100)\\nBusiness confidence Index in the UK 1977-2023\\nBusiness confidence Index of the United Kingdom from March 1977 to November 2023 (100 = long-term average)\\nRelated topics\\nRecommended\\nReport on the topic\\nKey figures\\nThe most important key figures provide you with a compact summary of the topic of \\"The UK economy\\" and take you straight to the corresponding statistics.\\n Monthly GDP growth of the UK 2020-2023\\nMonthly growth of gross domestic product in the United Kingdom from January 2020 to September 2023\\nGDP of the UK 2021, by region\\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\\nGDP growth rate in the UK 2021, by region\\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\\nGDP per capita of the UK 2021, by region\\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\\nGDP growth forecast for the UK 2000-2028\\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\\nLabor Market\\nLabor Market\\nUnemployment rate of the UK 1971-2023\\nUnemployment rate in the United Kingdom from March 1971 to September 2023\\nEmployment rate in the UK 1971-2022\\nEmployment rate in the United Kingdom from March 1971 to July 2023\\nNumber of people unemployed in the UK 1971-2023\\nNumber of people unemployed in the United Kingdom from March 1971 to July 2023 (in 1,000s)\\nNumber of people employed in the UK 1971-2021\\nNumber of people employed in the United Kingdom from March 1971 to July 2023 (in 1,000s)\\nUnemployment rate in the UK 1971-2023, by gender\\nUnemployment rate in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023, by gender\\nUnemployment rate in the UK 1992-2023, by age group\\nUnemployment rate in the United Kingdom from May 1992 to July 2023, by age group\\nYouth unemployment rate in the UK 1992-2023\\nYouth unemployment rate in the United Kingdom from May 1992 to July 2023\\nAverage annual earnings for full-time employees in the UK 1999-2023\\nMedian annual earnings for full-time employees in the United Kingdom from 1999 to 2023 (in nominal GBP)\\nAverage weekly earning growth in the UK 2001-2023\\nAverage year-on-year growth of weekly earnings (3 month average) in the United Kingdom from March 2001 to October 2023\\nNumber of redundancies in the UK 1995-2023\\nAverage number of people made redundant in the United Kingdom from May 1995 to July 2023 (in 1,000s)\\nOverall weekly hours worked in the UK 1971-2023\\nOverall weekly hours worked for all employees in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023 (in million hours worked)\\n Transforming data into design:\\nStatista Content & Design\\nStrategy and business building for the data-driven economy:\\nThe UK economy - Statistics & Facts\\nUK households under pressure in 2023\\nCoronavirus devastates UK economy in 2020\\nKey insights\\nDetailed statistics\\nGDP of the UK 1948-2022\\nDetailed statistics\\nUnemployment rate of the UK 1971-2023\\nDetailed statistics\\nInflation rate in the UK 1989-2023\\nEditor’s Picks\\nCurrent statistics on this topic\\nCurrent statistics on this topic\\nWages & Salaries\\nAverage weekly earning growth in the UK 2001-2023\\nIncome & Expenditure\\nPublic sector spending in the United Kingdom 2023/24\\nEmployment\\nNumber of people employed in the UK 1971-2021\\nRelated topics\\nRecommended\\nRecommended statistics\\nGross domestic product\\nGross domestic product\\nGDP of the UK 1948-2022\\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\\nAnnual GDP growth in the UK 1949-2022\\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\\nGDP per capita in the UK 1955-2022\\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\\nQuarterly GDP of the UK 1955-2023\\nQuarterly gross domestic product in the United Kingdom from 1st quarter 1955 to 3rd quarter 2023 (in million GBP)\\nQuarterly GDP growth of the UK 2015-2023\\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2015 to 3rd quarter 2023\\nQuarterly GDP per capita in the UK 1955-2023\\nQuarterly GDP per capita in the United Kingdom from 1st quarter 1955 to 3rd quarter 2023 (in GBP)\\nMonthly GDP of the UK 1997-2023\\nMonthly index of gross domestic product in the United Kingdom from January 1997 to September 2023 (2019=100)\\n GDP\\nAnnual GDP growth in the UK 1949-2022\\nQuarterly GDP per capita growth in the UK 2015-2023\\nMonthly GDP growth of the UK 2020-2023\\nGDP per capita in the UK 1955-2022\\nLabor market\\nNumber of people employed in the UK 1971-2021\\nNumber of people unemployed in the UK 1971-2023\\nDaily number of jobs furloughed in the UK 2020-2021\\nAverage annual earnings for full-time employees in the UK 1999-2023\\nForecasts for 2023\\nGDP growth forecast for the UK 2000-2028\\nAnnual unemployment rate in the UK 2000-2028\\nCPI annual inflation rate UK 2000-2028\\nRPI annual inflation rate UK 2000-2028\\n Industry Overview\\nDigital & Trend reports\\nOverview and forecasts on trending topics\\nIndustry & Market reports\\nIndustry and market insights and forecasts\\nCompanies & Products reports\\nKey figures and rankings about companies and products\\nConsumer & Brand reports\\nConsumer and brand insights and preferences in various industries\\nPolitics & Society reports\\nDetailed information about political and social topics\\nCountry & Region reports\\nAll key figures about countries and regions\\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\\nInsights on consumer attitudes and behavior worldwide\\nBusiness information on 100m+ public and private companies\\nExplore Company Insights\\nDetailed information for 39,000+ online stores and marketplaces\\nDirectly accessible data for 170 industries from 150+ countries\\nand over 1\xa0Mio. facts.\\n"}, {"url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB&most_recent_value_desc=false", "content": "GDP growth (annual %) - United Kingdom | Data Data GDP growth (annual %)United Kingdom Data Catalog Data Programs International Debt Statistics Other Books and Reports For Developers GDP growth (annual %) - United Kingdom ====================================== Similar values Highest values Lowest values GDP (constant 2015 US$)  GDP (current US$)  GDP (constant LCU)  GDP: linked series (current LCU)  GDP, PPP (constant 2021 international $)  GDP (current LCU)  GDP, PPP (current international $)  GDP per capita growth (annual %)  Country Most Recent Value All Countries and Economies Country Most Recent Value This site uses cookies to optimize functionality and give you the best possible experience. If you continue to navigate this website beyond this page, cookies will be placed on your browser."}]', name='tavily_search_results_json', id='4c88089f-0ac4-4eeb-9141-722f0463b78d', tool_call_id='toolu_01Jd9dxa4Ss2NhzBhCuwUX3E', artifact={'query': 'UK GDP annual data past 5 years 2019-2023', 'follow_up_questions': None, 'answer': None, 'images': [], 'results': [{'title': 'U.K. GDP 1960-2024 - Macrotrends', 'url': 'https://www.macrotrends.net/global-metrics/countries/GBR/united-kingdom/gdp-gross-domestic-product', 'content': 'Dollar figures for GDP are converted from domestic currencies using single year official exchange rates. For a few countries where the official exchange rate does not reflect the rate effectively applied to actual foreign exchange transactions, an alternative conversion factor is used. U.K. gdp for 2023 was $3,340.03B, a 8.13% increase from 2022.', 'score': 0.97675806, 'raw_content': None}, {'title': 'UK GDP - Statistics & Facts | Statista', 'url': 'https://www.statista.com/topics/3795/gdp-of-the-uk/', 'content': 'Monthly growth of gross domestic product in the United Kingdom from January 2019 to November 2023\nContribution to GDP growth in the UK 2023, by sector\nContribution to gross domestic product growth in the United Kingdom in January 2023, by sector\nGDP growth rate in the UK 1999-2021, by country\nAnnual growth rates of gross domestic product in the United Kingdom from 1999 to 2021, by country\nGDP growth rate in the UK 2021, by region\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\nGDP growth of Scotland 2021, by local area\nAnnual growth rates of gross domestic product in Scotland in 2021, by local (ITL 3) area\nGDP growth of Wales 2021, by local area\nAnnual growth rates of gross domestic product in Wales in 2021, by local (ITL 3) area\nGDP growth of Northern Ireland 2021, by local area\nAnnual growth rates of gross domestic product in Northern Ireland in 2021, by local (ITL 3) area\nGDP per capita\nGDP per capita\nGDP per capita in the UK 1955-2022\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\nAnnual GDP per capita growth in the UK 1956-2022\nAnnual GDP per capita growth in the United Kingdom from 1956 to 2022\nQuarterly GDP per capita in the UK 2019-2023\nQuarterly GDP per capita in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\nQuarterly GDP per capita growth in the UK 2019-2023\nQuarterly GDP per capita growth in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\nGDP per capita of the UK 1999-2021, by country\nGross domestic product per capita of the United Kingdom from 1999 to 2021, by country (in GBP)\nGDP per capita of the UK 2021, by region\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\nGlobal Comparisons\nGlobal Comparisons\nCountries with the largest gross domestic product (GDP) 2022\n Monthly GDP of the UK 2019-2023\nMonthly index of gross domestic product in the United Kingdom from January 2019 to November 2023 (2019=100)\nGVA of the UK 2022, by sector\nGross value added of the United Kingdom in 2022, by industry sector (in million GBP)\nGDP of the UK 2021, by country\nGross domestic product of the United Kingdom in 2021, by country (in million GBP)\nGDP of the UK 2021, by region\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\nGDP of Scotland 2021, by local area\nGross domestic product of Scotland in 2021, by local (ITL 3) area (in million GBP)\nGDP of Wales 2021, by local area\nGross domestic product of Wales in 2021, by local (ITL 3) area (in million GBP)\nGDP of Northern Ireland 2021, by local area\nGross domestic product of Northern Ireland in 2021, by local (ITL 3) area (in million GBP)\nGDP growth\nGDP growth\nGDP growth forecast for the UK 2000-2028\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\nAnnual GDP growth in the UK 1949-2022\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\nQuarterly GDP growth of the UK 2019-2023\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023\nMonthly GDP growth of the UK 2019-2023\n Transforming data into design:\nStatista Content & Design\nStrategy and business building for the data-driven economy:\nUK GDP - Statistics & Facts\nUK economy expected to shrink in 2023\nCharacteristics of UK GDP\nKey insights\nDetailed statistics\nGDP of the UK 1948-2022\nDetailed statistics\nAnnual GDP growth in the UK 1949-2022\nDetailed statistics\nGDP per capita in the UK 1955-2022\nEditor’s Picks\nCurrent statistics on this topic\nCurrent statistics on this topic\nKey Economic Indicators\nMonthly GDP growth of the UK 2019-2023\nKey Economic Indicators\nMonthly GDP of the UK 2019-2023\nKey Economic Indicators\nContribution to GDP growth in the UK 2023, by sector\nRelated topics\nRecommended\nRecommended statistics\nGDP\nGDP\nGDP of the UK 1948-2022\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\nQuarterly GDP of the UK 2019-2023\nQuarterly gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in million GBP)\n The 20 countries with the largest gross domestic product (GDP) in 2022 (in billion U.S. dollars)\nGDP of European countries in 2022\nGross domestic product at current market prices of selected European countries in 2022 (in million euros)\nReal GDP growth rates in Europe 2023\nAnnual real gross domestic product (GDP) growth rate in European countries in 2023\nGross domestic product (GDP) of Europe\'s largest economies 1980-2028\nGross domestic product (GDP) at current prices of Europe\'s largest economies from 1980 to 2028 (in billion U.S dollars)\nUnited Kingdom\'s share of global gross domestic product (GDP) 2028\nUnited Kingdom (UK): Share of global gross domestic product (GDP) adjusted for Purchasing Power Parity (PPP) from 2018 to 2028\nRelated topics\nRecommended\nReport on the topic\nKey figures\nThe most important key figures provide you with a compact summary of the topic of "UK GDP" and take you straight to the corresponding statistics.\n Industry Overview\nDigital & Trend reports\nOverview and forecasts on trending topics\nIndustry & Market reports\nIndustry and market insights and forecasts\nCompanies & Products reports\nKey figures and rankings about companies and products\nConsumer & Brand reports\nConsumer and brand insights and preferences in various industries\nPolitics & Society reports\nDetailed information about political and social topics\nCountry & Region reports\nAll key figures about countries and regions\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\nInsights on consumer attitudes and behavior worldwide\nBusiness information on 100m+ public and private companies\nExplore Company Insights\nDetailed information for 39,000+ online stores and marketplaces\nDirectly accessible data for 170 industries from 150+ countries\nand over 1\xa0Mio. facts.\n', 'score': 0.97057647, 'raw_content': None}, {'title': 'GDP growth (annual %) - United Kingdom | Data - World Bank Data', 'url': 'https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB', 'content': 'GDP growth (annual %) - United Kingdom | Data - World Bank Data', 'score': 0.97052056, 'raw_content': None}, {'title': 'The UK economy - Statistics & Facts | Statista', 'url': 'https://www.statista.com/topics/6500/the-british-economy/', 'content': 'Output per hour worked in the UK 1971 to 2023\nEconomic output per hour worked in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023 (2019=100)\nAnnual unemployment rate in the UK 2000-2028\nAnnual unemployment rate in the United Kingdom from 2000 to 2028\nInflation\nInflation\nInflation rate in the UK 1989-2023\nInflation rate for the Consumer Price Index (CPI) in the United Kingdom from January 1989 to October 2023\nRPI inflation rate in the UK 1948-2023\nInflation rate for the Retail Price Index (RPI) in the United Kingdom from June 1948 to October 2023\nCPIH inflation rate in the UK 1989-2023\nInflation rate for the Consumer Price Index including owner occupiers\' housing costs (CPIH) in the United Kingdom from January 1989 to October 2023\nPPI in the UK 2010-2023\nProducer Price Index (PPI) in the United Kingdom from October 2010 to October 2023\nCPI inflation rate in the UK 2023, by sector\nInflation rate for the Consumer Price Index (CPI) in the United Kingdom in October 2023, by sector\nConsumer Price Index in the UK 1988-2023\nConsumer Price Index (CPI) in the United Kingdom from 1st quarter 1988 to 3rd quarter 2023\nRetail Price Index in the UK 1987-2023\nRetail Price Index (RPI) in the United Kingdom from 1st quarter 1987 to 3rd quarter 2023\nConsumer Price Index including housing in the UK 1988-2023\nConsumer Price Index including owner occupiers\' housing costs (CPIH) in the United Kingdom from 1st quarter 1988 to 3rd quarter 2023\nRPI annual inflation rate UK 2000-2028\nAnnual inflation rate of the Retail Price Index in the United Kingdom from 2000 to 2028\nCPI annual inflation rate UK 2000-2028\nAnnual inflation rate of the Consumer Price Index in the United Kingdom from 2000 to 2028\nGovernment finances\nGovernment finances\nGovernment spending as a percentage of GDP in the UK 1900-2029\nTotal managed expenditure expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\nGovernment revenue as a percentage of GDP in the UK 1900-2029\nTotal public sector current receipts expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29 (in million GBP)\nGovernment borrowing as a percentage of GDP in the UK 1900-2029\nPublic sector borrowing expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\nNational debt as a percentage of GDP in the UK 1900-2029\nPublic sector net debt expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\nPublic sector spending in the United Kingdom 2023/24\nBudgeted public sector expenditure on services in the United Kingdom in 2023/24, by function (in billion GBP)\nGovernment revenue sources in the United Kingdom 2023/24\nExpected public sector current receipts in the United Kingdom in 2023/24, by function (in billion GBP)\nBusiness Enterprise\nBusiness Enterprise\nLargest companies in the United Kingdom based on revenue 2022\nLargest companies in the United Kingdom based on revenue in 2022 (in billion US dollars)\nLargest UK companies based on number of global employees 2020\nLargest companies based in the United Kingdom on number of employees worldwide in 2020 (in 1,000s)\nNumber of private sector businesses in the UK 2000-2023\nNumber of private sector businesses in the United Kingdom from 2000 to 2023 (in millions)\nNumber of private sector businesses in the UK 2023, by sector\nNumber of private sector businesses in the United Kingdom in 2023, by sector\nNumber of businesses by enterprise size in the UK 2023\nNumber of private sector businesses in the United Kingdom in 2023, by employment size\nNumber of private sector businesses in the UK 2023, by region\nNumber of private sector businesses in the United Kingdom in 2023, by region\nNumber of local business units in the UK 2012-2023\nNumber of local units in VAT and/or PAYE based enterprises in the United Kingdom from 2012 to 2023 (in millions)\nBusiness investment index in the UK 1997-2023\nBusiness investment index in the United Kingdom from 1st quarter 1997 to 2nd quarter 2023 (Q1 1997=100)\nBusiness confidence Index in the UK 1977-2023\nBusiness confidence Index of the United Kingdom from March 1977 to November 2023 (100 = long-term average)\nRelated topics\nRecommended\nReport on the topic\nKey figures\nThe most important key figures provide you with a compact summary of the topic of "The UK economy" and take you straight to the corresponding statistics.\n Monthly GDP growth of the UK 2020-2023\nMonthly growth of gross domestic product in the United Kingdom from January 2020 to September 2023\nGDP of the UK 2021, by region\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\nGDP growth rate in the UK 2021, by region\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\nGDP per capita of the UK 2021, by region\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\nGDP growth forecast for the UK 2000-2028\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\nLabor Market\nLabor Market\nUnemployment rate of the UK 1971-2023\nUnemployment rate in the United Kingdom from March 1971 to September 2023\nEmployment rate in the UK 1971-2022\nEmployment rate in the United Kingdom from March 1971 to July 2023\nNumber of people unemployed in the UK 1971-2023\nNumber of people unemployed in the United Kingdom from March 1971 to July 2023 (in 1,000s)\nNumber of people employed in the UK 1971-2021\nNumber of people employed in the United Kingdom from March 1971 to July 2023 (in 1,000s)\nUnemployment rate in the UK 1971-2023, by gender\nUnemployment rate in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023, by gender\nUnemployment rate in the UK 1992-2023, by age group\nUnemployment rate in the United Kingdom from May 1992 to July 2023, by age group\nYouth unemployment rate in the UK 1992-2023\nYouth unemployment rate in the United Kingdom from May 1992 to July 2023\nAverage annual earnings for full-time employees in the UK 1999-2023\nMedian annual earnings for full-time employees in the United Kingdom from 1999 to 2023 (in nominal GBP)\nAverage weekly earning growth in the UK 2001-2023\nAverage year-on-year growth of weekly earnings (3 month average) in the United Kingdom from March 2001 to October 2023\nNumber of redundancies in the UK 1995-2023\nAverage number of people made redundant in the United Kingdom from May 1995 to July 2023 (in 1,000s)\nOverall weekly hours worked in the UK 1971-2023\nOverall weekly hours worked for all employees in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023 (in million hours worked)\n Transforming data into design:\nStatista Content & Design\nStrategy and business building for the data-driven economy:\nThe UK economy - Statistics & Facts\nUK households under pressure in 2023\nCoronavirus devastates UK economy in 2020\nKey insights\nDetailed statistics\nGDP of the UK 1948-2022\nDetailed statistics\nUnemployment rate of the UK 1971-2023\nDetailed statistics\nInflation rate in the UK 1989-2023\nEditor’s Picks\nCurrent statistics on this topic\nCurrent statistics on this topic\nWages & Salaries\nAverage weekly earning growth in the UK 2001-2023\nIncome & Expenditure\nPublic sector spending in the United Kingdom 2023/24\nEmployment\nNumber of people employed in the UK 1971-2021\nRelated topics\nRecommended\nRecommended statistics\nGross domestic product\nGross domestic product\nGDP of the UK 1948-2022\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\nAnnual GDP growth in the UK 1949-2022\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\nGDP per capita in the UK 1955-2022\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\nQuarterly GDP of the UK 1955-2023\nQuarterly gross domestic product in the United Kingdom from 1st quarter 1955 to 3rd quarter 2023 (in million GBP)\nQuarterly GDP growth of the UK 2015-2023\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2015 to 3rd quarter 2023\nQuarterly GDP per capita in the UK 1955-2023\nQuarterly GDP per capita in the United Kingdom from 1st quarter 1955 to 3rd quarter 2023 (in GBP)\nMonthly GDP of the UK 1997-2023\nMonthly index of gross domestic product in the United Kingdom from January 1997 to September 2023 (2019=100)\n GDP\nAnnual GDP growth in the UK 1949-2022\nQuarterly GDP per capita growth in the UK 2015-2023\nMonthly GDP growth of the UK 2020-2023\nGDP per capita in the UK 1955-2022\nLabor market\nNumber of people employed in the UK 1971-2021\nNumber of people unemployed in the UK 1971-2023\nDaily number of jobs furloughed in the UK 2020-2021\nAverage annual earnings for full-time employees in the UK 1999-2023\nForecasts for 2023\nGDP growth forecast for the UK 2000-2028\nAnnual unemployment rate in the UK 2000-2028\nCPI annual inflation rate UK 2000-2028\nRPI annual inflation rate UK 2000-2028\n Industry Overview\nDigital & Trend reports\nOverview and forecasts on trending topics\nIndustry & Market reports\nIndustry and market insights and forecasts\nCompanies & Products reports\nKey figures and rankings about companies and products\nConsumer & Brand reports\nConsumer and brand insights and preferences in various industries\nPolitics & Society reports\nDetailed information about political and social topics\nCountry & Region reports\nAll key figures about countries and regions\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\nInsights on consumer attitudes and behavior worldwide\nBusiness information on 100m+ public and private companies\nExplore Company Insights\nDetailed information for 39,000+ online stores and marketplaces\nDirectly accessible data for 170 industries from 150+ countries\nand over 1\xa0Mio. facts.\n', 'score': 0.95998776, 'raw_content': None}, {'title': 'GDP growth (annual %) - United Kingdom | Data - World Bank Data', 'url': 'https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB&most_recent_value_desc=false', 'content': 'GDP growth (annual %) - United Kingdom | Data Data GDP growth (annual %)United Kingdom Data Catalog Data Programs International Debt Statistics Other Books and Reports For Developers GDP growth (annual %) - United Kingdom ====================================== Similar values Highest values Lowest values GDP (constant 2015 US$)  GDP (current US$)  GDP (constant LCU)  GDP: linked series (current LCU)  GDP, PPP (constant 2021 international $)  GDP (current LCU)  GDP, PPP (current international $)  GDP per capita growth (annual %)  Country Most Recent Value All Countries and Economies Country Most Recent Value This site uses cookies to optimize functionality and give you the best possible experience. If you continue to navigate this website beyond this page, cookies will be placed on your browser.', 'score': 0.7892337, 'raw_content': None}], 'response_time': 2.3}), AIMessage(content=[{'text': 'Let me search for more specific data.', 'type': 'text'}, {'id': 'toolu_019dPRXojLJoVNYFLzzSWw4w', 'input': {'query': 'UK GDP values by year 2019 2020 2021 2022 2023'}, 'name': 'tavily_search_results_json', 'type': 'tool_use'}], additional_kwargs={}, response_metadata={'id': 'msg_01Ac9vcTFneb5dvcEYXJyf1P', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'tool_use', 'stop_sequence': None, 'usage': {'input_tokens': 5890, 'output_tokens': 87}}, id='run-3504417f-c0b5-4908-82e2-89a18abb1b8e-0', tool_calls=[{'name': 'tavily_search_results_json', 'args': {'query': 'UK GDP values by year 2019 2020 2021 2022 2023'}, 'id': 'toolu_019dPRXojLJoVNYFLzzSWw4w', 'type': 'tool_call'}], usage_metadata={'input_tokens': 5890, 'output_tokens': 87, 'total_tokens': 5977, 'input_token_details': {}}), ToolMessage(content='[{"url": "https://www.macrotrends.net/global-metrics/countries/GBR/united-kingdom/gdp-gross-domestic-product", "content": "U.K. gdp for 2023 was $3,340.03B, a 8.13% increase from 2022. U.K. gdp for 2022 was $3,088.84B, a 1.68% decline from 2021. U.K. gdp for 2021 was $3,141.51B, a 16.45% increase from 2020. U.K. gdp for 2020 was $2,697.81B, a 5.39% decline from 2019."}, {"url": "https://countryeconomy.com/gdp/uk?year=2023", "content": "Gross Domestic Product of United Kingdom grew 0.3% in 2023 compared to last year. This rate is 45 -tenths of one percent less than the figure of 4.8% published in 2022. The GDP figure in 2023 was $3,380,855 million, leaving United Kingdom placed 6th in the ranking of GDP of the 196 countries that we publish."}, {"url": "https://www.statista.com/topics/3795/gdp-of-the-uk/", "content": "Monthly growth of gross domestic product in the United Kingdom from January 2019 to November 2023\\nContribution to GDP growth in the UK 2023, by sector\\nContribution to gross domestic product growth in the United Kingdom in January 2023, by sector\\nGDP growth rate in the UK 1999-2021, by country\\nAnnual growth rates of gross domestic product in the United Kingdom from 1999 to 2021, by country\\nGDP growth rate in the UK 2021, by region\\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\\nGDP growth of Scotland 2021, by local area\\nAnnual growth rates of gross domestic product in Scotland in 2021, by local (ITL 3) area\\nGDP growth of Wales 2021, by local area\\nAnnual growth rates of gross domestic product in Wales in 2021, by local (ITL 3) area\\nGDP growth of Northern Ireland 2021, by local area\\nAnnual growth rates of gross domestic product in Northern Ireland in 2021, by local (ITL 3) area\\nGDP per capita\\nGDP per capita\\nGDP per capita in the UK 1955-2022\\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\\nAnnual GDP per capita growth in the UK 1956-2022\\nAnnual GDP per capita growth in the United Kingdom from 1956 to 2022\\nQuarterly GDP per capita in the UK 2019-2023\\nQuarterly GDP per capita in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\\nQuarterly GDP per capita growth in the UK 2019-2023\\nQuarterly GDP per capita growth in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\\nGDP per capita of the UK 1999-2021, by country\\nGross domestic product per capita of the United Kingdom from 1999 to 2021, by country (in GBP)\\nGDP per capita of the UK 2021, by region\\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\\nGlobal Comparisons\\nGlobal Comparisons\\nCountries with the largest gross domestic product (GDP) 2022\\n Monthly GDP of the UK 2019-2023\\nMonthly index of gross domestic product in the United Kingdom from January 2019 to November 2023 (2019=100)\\nGVA of the UK 2022, by sector\\nGross value added of the United Kingdom in 2022, by industry sector (in million GBP)\\nGDP of the UK 2021, by country\\nGross domestic product of the United Kingdom in 2021, by country (in million GBP)\\nGDP of the UK 2021, by region\\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\\nGDP of Scotland 2021, by local area\\nGross domestic product of Scotland in 2021, by local (ITL 3) area (in million GBP)\\nGDP of Wales 2021, by local area\\nGross domestic product of Wales in 2021, by local (ITL 3) area (in million GBP)\\nGDP of Northern Ireland 2021, by local area\\nGross domestic product of Northern Ireland in 2021, by local (ITL 3) area (in million GBP)\\nGDP growth\\nGDP growth\\nGDP growth forecast for the UK 2000-2028\\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\\nAnnual GDP growth in the UK 1949-2022\\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\\nQuarterly GDP growth of the UK 2019-2023\\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023\\nMonthly GDP growth of the UK 2019-2023\\n Transforming data into design:\\nStatista Content & Design\\nStrategy and business building for the data-driven economy:\\nUK GDP - Statistics & Facts\\nUK economy expected to shrink in 2023\\nCharacteristics of UK GDP\\nKey insights\\nDetailed statistics\\nGDP of the UK 1948-2022\\nDetailed statistics\\nAnnual GDP growth in the UK 1949-2022\\nDetailed statistics\\nGDP per capita in the UK 1955-2022\\nEditor’s Picks\\nCurrent statistics on this topic\\nCurrent statistics on this topic\\nKey Economic Indicators\\nMonthly GDP growth of the UK 2019-2023\\nKey Economic Indicators\\nMonthly GDP of the UK 2019-2023\\nKey Economic Indicators\\nContribution to GDP growth in the UK 2023, by sector\\nRelated topics\\nRecommended\\nRecommended statistics\\nGDP\\nGDP\\nGDP of the UK 1948-2022\\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\\nQuarterly GDP of the UK 2019-2023\\nQuarterly gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in million GBP)\\n The 20 countries with the largest gross domestic product (GDP) in 2022 (in billion U.S. dollars)\\nGDP of European countries in 2022\\nGross domestic product at current market prices of selected European countries in 2022 (in million euros)\\nReal GDP growth rates in Europe 2023\\nAnnual real gross domestic product (GDP) growth rate in European countries in 2023\\nGross domestic product (GDP) of Europe\'s largest economies 1980-2028\\nGross domestic product (GDP) at current prices of Europe\'s largest economies from 1980 to 2028 (in billion U.S dollars)\\nUnited Kingdom\'s share of global gross domestic product (GDP) 2028\\nUnited Kingdom (UK): Share of global gross domestic product (GDP) adjusted for Purchasing Power Parity (PPP) from 2018 to 2028\\nRelated topics\\nRecommended\\nReport on the topic\\nKey figures\\nThe most important key figures provide you with a compact summary of the topic of \\"UK GDP\\" and take you straight to the corresponding statistics.\\n Industry Overview\\nDigital & Trend reports\\nOverview and forecasts on trending topics\\nIndustry & Market reports\\nIndustry and market insights and forecasts\\nCompanies & Products reports\\nKey figures and rankings about companies and products\\nConsumer & Brand reports\\nConsumer and brand insights and preferences in various industries\\nPolitics & Society reports\\nDetailed information about political and social topics\\nCountry & Region reports\\nAll key figures about countries and regions\\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\\nInsights on consumer attitudes and behavior worldwide\\nBusiness information on 100m+ public and private companies\\nExplore Company Insights\\nDetailed information for 39,000+ online stores and marketplaces\\nDirectly accessible data for 170 industries from 150+ countries\\nand over 1\xa0Mio. facts.\\n"}, {"url": "https://www.ons.gov.uk/economy/grossdomesticproductgdp/compendium/unitedkingdomnationalaccountsthebluebook/2024/nationalaccountsataglance", "content": "Real gross domestic product (GDP) is estimated to have increased by 0.3% in 2023, following a recovery from the impacts of the coronavirus (COVID-19) pandemic over the two previous years (Figure 1). Data for the UK are the Office for National Statistics (ONS) measure of real gross domestic product (GDP). Figure 9: Real GDP per head fell in 2023 when compared with 2022 in six G10 economies, including the UK Data for the UK are the Office for National Statistics (ONS) measure of real gross domestic product (GDP) per head. Download this chart Figure 9: Real GDP per head fell in 2023 when compared with 2022 in six G10 economies, including the UK"}, {"url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB&most_recent_value_desc=false", "content": "GDP growth (annual %) - United Kingdom | Data Data GDP growth (annual %)United Kingdom Data Catalog Data Programs International Debt Statistics Other Books and Reports For Developers GDP growth (annual %) - United Kingdom ====================================== Similar values Highest values Lowest values GDP (constant 2015 US$)  GDP (current US$)  GDP (constant LCU)  GDP: linked series (current LCU)  GDP, PPP (constant 2021 international $)  GDP (current LCU)  GDP, PPP (current international $)  GDP per capita growth (annual %)  Country Most Recent Value All Countries and Economies Country Most Recent Value This site uses cookies to optimize functionality and give you the best possible experience. If you continue to navigate this website beyond this page, cookies will be placed on your browser."}]', name='tavily_search_results_json', id='84c571ca-27c6-4023-93a2-f0c2e8b6abb0', tool_call_id='toolu_019dPRXojLJoVNYFLzzSWw4w', artifact={'query': 'UK GDP values by year 2019 2020 2021 2022 2023', 'follow_up_questions': None, 'answer': None, 'images': [], 'results': [{'title': 'U.K. GDP 1960-2024 - Macrotrends', 'url': 'https://www.macrotrends.net/global-metrics/countries/GBR/united-kingdom/gdp-gross-domestic-product', 'content': 'U.K. gdp for 2023 was $3,340.03B, a 8.13% increase from 2022. U.K. gdp for 2022 was $3,088.84B, a 1.68% decline from 2021. U.K. gdp for 2021 was $3,141.51B, a 16.45% increase from 2020. U.K. gdp for 2020 was $2,697.81B, a 5.39% decline from 2019.', 'score': 0.9974491, 'raw_content': None}, {'title': 'United Kingdom (UK) GDP - Gross Domestic Product 2023', 'url': 'https://countryeconomy.com/gdp/uk?year=2023', 'content': 'Gross Domestic Product of United Kingdom grew 0.3% in 2023 compared to last year. This rate is 45 -tenths of one percent less than the figure of 4.8% published in 2022. The GDP figure in 2023 was $3,380,855 million, leaving United Kingdom placed 6th in the ranking of GDP of the 196 countries that we publish.', 'score': 0.9964064, 'raw_content': None}, {'title': 'UK GDP - Statistics & Facts | Statista', 'url': 'https://www.statista.com/topics/3795/gdp-of-the-uk/', 'content': 'Monthly growth of gross domestic product in the United Kingdom from January 2019 to November 2023\nContribution to GDP growth in the UK 2023, by sector\nContribution to gross domestic product growth in the United Kingdom in January 2023, by sector\nGDP growth rate in the UK 1999-2021, by country\nAnnual growth rates of gross domestic product in the United Kingdom from 1999 to 2021, by country\nGDP growth rate in the UK 2021, by region\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\nGDP growth of Scotland 2021, by local area\nAnnual growth rates of gross domestic product in Scotland in 2021, by local (ITL 3) area\nGDP growth of Wales 2021, by local area\nAnnual growth rates of gross domestic product in Wales in 2021, by local (ITL 3) area\nGDP growth of Northern Ireland 2021, by local area\nAnnual growth rates of gross domestic product in Northern Ireland in 2021, by local (ITL 3) area\nGDP per capita\nGDP per capita\nGDP per capita in the UK 1955-2022\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\nAnnual GDP per capita growth in the UK 1956-2022\nAnnual GDP per capita growth in the United Kingdom from 1956 to 2022\nQuarterly GDP per capita in the UK 2019-2023\nQuarterly GDP per capita in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\nQuarterly GDP per capita growth in the UK 2019-2023\nQuarterly GDP per capita growth in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\nGDP per capita of the UK 1999-2021, by country\nGross domestic product per capita of the United Kingdom from 1999 to 2021, by country (in GBP)\nGDP per capita of the UK 2021, by region\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\nGlobal Comparisons\nGlobal Comparisons\nCountries with the largest gross domestic product (GDP) 2022\n Monthly GDP of the UK 2019-2023\nMonthly index of gross domestic product in the United Kingdom from January 2019 to November 2023 (2019=100)\nGVA of the UK 2022, by sector\nGross value added of the United Kingdom in 2022, by industry sector (in million GBP)\nGDP of the UK 2021, by country\nGross domestic product of the United Kingdom in 2021, by country (in million GBP)\nGDP of the UK 2021, by region\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\nGDP of Scotland 2021, by local area\nGross domestic product of Scotland in 2021, by local (ITL 3) area (in million GBP)\nGDP of Wales 2021, by local area\nGross domestic product of Wales in 2021, by local (ITL 3) area (in million GBP)\nGDP of Northern Ireland 2021, by local area\nGross domestic product of Northern Ireland in 2021, by local (ITL 3) area (in million GBP)\nGDP growth\nGDP growth\nGDP growth forecast for the UK 2000-2028\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\nAnnual GDP growth in the UK 1949-2022\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\nQuarterly GDP growth of the UK 2019-2023\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023\nMonthly GDP growth of the UK 2019-2023\n Transforming data into design:\nStatista Content & Design\nStrategy and business building for the data-driven economy:\nUK GDP - Statistics & Facts\nUK economy expected to shrink in 2023\nCharacteristics of UK GDP\nKey insights\nDetailed statistics\nGDP of the UK 1948-2022\nDetailed statistics\nAnnual GDP growth in the UK 1949-2022\nDetailed statistics\nGDP per capita in the UK 1955-2022\nEditor’s Picks\nCurrent statistics on this topic\nCurrent statistics on this topic\nKey Economic Indicators\nMonthly GDP growth of the UK 2019-2023\nKey Economic Indicators\nMonthly GDP of the UK 2019-2023\nKey Economic Indicators\nContribution to GDP growth in the UK 2023, by sector\nRelated topics\nRecommended\nRecommended statistics\nGDP\nGDP\nGDP of the UK 1948-2022\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\nQuarterly GDP of the UK 2019-2023\nQuarterly gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in million GBP)\n The 20 countries with the largest gross domestic product (GDP) in 2022 (in billion U.S. dollars)\nGDP of European countries in 2022\nGross domestic product at current market prices of selected European countries in 2022 (in million euros)\nReal GDP growth rates in Europe 2023\nAnnual real gross domestic product (GDP) growth rate in European countries in 2023\nGross domestic product (GDP) of Europe\'s largest economies 1980-2028\nGross domestic product (GDP) at current prices of Europe\'s largest economies from 1980 to 2028 (in billion U.S dollars)\nUnited Kingdom\'s share of global gross domestic product (GDP) 2028\nUnited Kingdom (UK): Share of global gross domestic product (GDP) adjusted for Purchasing Power Parity (PPP) from 2018 to 2028\nRelated topics\nRecommended\nReport on the topic\nKey figures\nThe most important key figures provide you with a compact summary of the topic of "UK GDP" and take you straight to the corresponding statistics.\n Industry Overview\nDigital & Trend reports\nOverview and forecasts on trending topics\nIndustry & Market reports\nIndustry and market insights and forecasts\nCompanies & Products reports\nKey figures and rankings about companies and products\nConsumer & Brand reports\nConsumer and brand insights and preferences in various industries\nPolitics & Society reports\nDetailed information about political and social topics\nCountry & Region reports\nAll key figures about countries and regions\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\nInsights on consumer attitudes and behavior worldwide\nBusiness information on 100m+ public and private companies\nExplore Company Insights\nDetailed information for 39,000+ online stores and marketplaces\nDirectly accessible data for 170 industries from 150+ countries\nand over 1\xa0Mio. facts.\n', 'score': 0.97943294, 'raw_content': None}, {'title': 'National accounts at a glance - Office for National Statistics', 'url': 'https://www.ons.gov.uk/economy/grossdomesticproductgdp/compendium/unitedkingdomnationalaccountsthebluebook/2024/nationalaccountsataglance', 'content': 'Real gross domestic product (GDP) is estimated to have increased by 0.3% in 2023, following a recovery from the impacts of the coronavirus (COVID-19) pandemic over the two previous years (Figure 1). Data for the UK are the Office for National Statistics (ONS) measure of real gross domestic product (GDP). Figure 9: Real GDP per head fell in 2023 when compared with 2022 in six G10 economies, including the UK Data for the UK are the Office for National Statistics (ONS) measure of real gross domestic product (GDP) per head. Download this chart Figure 9: Real GDP per head fell in 2023 when compared with 2022 in six G10 economies, including the UK', 'score': 0.975249, 'raw_content': None}, {'title': 'GDP growth (annual %) - United Kingdom | Data - World Bank Data', 'url': 'https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB&most_recent_value_desc=false', 'content': 'GDP growth (annual %) - United Kingdom | Data Data GDP growth (annual %)United Kingdom Data Catalog Data Programs International Debt Statistics Other Books and Reports For Developers GDP growth (annual %) - United Kingdom ====================================== Similar values Highest values Lowest values GDP (constant 2015 US$)  GDP (current US$)  GDP (constant LCU)  GDP: linked series (current LCU)  GDP, PPP (constant 2021 international $)  GDP (current LCU)  GDP, PPP (current international $)  GDP per capita growth (annual %)  Country Most Recent Value All Countries and Economies Country Most Recent Value This site uses cookies to optimize functionality and give you the best possible experience. If you continue to navigate this website beyond this page, cookies will be placed on your browser.', 'score': 0.83775276, 'raw_content': None}], 'response_time': 2.37}), HumanMessage(content='Based on the search results, I can provide the UK\'s GDP values for the past 5 years (in billions of US dollars):\n\n2019: $2,851.54\n2020: $2,697.81\n2021: $3,141.51\n2022: $3,088.84\n2023: $3,340.03\n\nI\'ll pass this data to my chart generator colleague to create a line chart. They should create a line chart with:\n- Years 2019-2023 on the x-axis\n- GDP values in billions USD on the y-axis\n- Title: "UK GDP 2019-2023"\n- Clear data points showing the values\n\nOver to you, chart generator colleague!', additional_kwargs={}, response_metadata={}, name='researcher', id='7e790b7a-7b06-4b45-a595-8736b53db844')]}}
----
``````output
Python REPL can execute arbitrary code. Use with caution.

```````

![](<Base64-Image-Removed>)

```md-code__content
{'chart_generator': {'messages': [HumanMessage(content="First, get the UK's GDP over the past 5 years, then make a line chart of it. Once you make the chart, finish.", additional_kwargs={}, response_metadata={}, id='fa1f5e95-9e1a-47d4-b4b6-e93f345e339d'), AIMessage(content=[{'text': "I'll help search for the UK's GDP data over the past 5 years. Then my colleague can help create the line chart.", 'type': 'text'}, {'id': 'toolu_01Jd9dxa4Ss2NhzBhCuwUX3E', 'input': {'query': 'UK GDP annual data past 5 years 2019-2023'}, 'name': 'tavily_search_results_json', 'type': 'tool_use'}], additional_kwargs={}, response_metadata={'id': 'msg_014nCkfVHnG6LAsiS6pY7zcd', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'tool_use', 'stop_sequence': None, 'usage': {'input_tokens': 555, 'output_tokens': 101}}, id='run-e2297529-9972-4de6-835d-23d920b0e29b-0', tool_calls=[{'name': 'tavily_search_results_json', 'args': {'query': 'UK GDP annual data past 5 years 2019-2023'}, 'id': 'toolu_01Jd9dxa4Ss2NhzBhCuwUX3E', 'type': 'tool_call'}], usage_metadata={'input_tokens': 555, 'output_tokens': 101, 'total_tokens': 656, 'input_token_details': {}}), ToolMessage(content='[{"url": "https://www.macrotrends.net/global-metrics/countries/GBR/united-kingdom/gdp-gross-domestic-product", "content": "Dollar figures for GDP are converted from domestic currencies using single year official exchange rates. For a few countries where the official exchange rate does not reflect the rate effectively applied to actual foreign exchange transactions, an alternative conversion factor is used. U.K. gdp for 2023 was $3,340.03B, a 8.13% increase from 2022."}, {"url": "https://www.statista.com/topics/3795/gdp-of-the-uk/", "content": "Monthly growth of gross domestic product in the United Kingdom from January 2019 to November 2023\\nContribution to GDP growth in the UK 2023, by sector\\nContribution to gross domestic product growth in the United Kingdom in January 2023, by sector\\nGDP growth rate in the UK 1999-2021, by country\\nAnnual growth rates of gross domestic product in the United Kingdom from 1999 to 2021, by country\\nGDP growth rate in the UK 2021, by region\\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\\nGDP growth of Scotland 2021, by local area\\nAnnual growth rates of gross domestic product in Scotland in 2021, by local (ITL 3) area\\nGDP growth of Wales 2021, by local area\\nAnnual growth rates of gross domestic product in Wales in 2021, by local (ITL 3) area\\nGDP growth of Northern Ireland 2021, by local area\\nAnnual growth rates of gross domestic product in Northern Ireland in 2021, by local (ITL 3) area\\nGDP per capita\\nGDP per capita\\nGDP per capita in the UK 1955-2022\\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\\nAnnual GDP per capita growth in the UK 1956-2022\\nAnnual GDP per capita growth in the United Kingdom from 1956 to 2022\\nQuarterly GDP per capita in the UK 2019-2023\\nQuarterly GDP per capita in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\\nQuarterly GDP per capita growth in the UK 2019-2023\\nQuarterly GDP per capita growth in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\\nGDP per capita of the UK 1999-2021, by country\\nGross domestic product per capita of the United Kingdom from 1999 to 2021, by country (in GBP)\\nGDP per capita of the UK 2021, by region\\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\\nGlobal Comparisons\\nGlobal Comparisons\\nCountries with the largest gross domestic product (GDP) 2022\\n Monthly GDP of the UK 2019-2023\\nMonthly index of gross domestic product in the United Kingdom from January 2019 to November 2023 (2019=100)\\nGVA of the UK 2022, by sector\\nGross value added of the United Kingdom in 2022, by industry sector (in million GBP)\\nGDP of the UK 2021, by country\\nGross domestic product of the United Kingdom in 2021, by country (in million GBP)\\nGDP of the UK 2021, by region\\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\\nGDP of Scotland 2021, by local area\\nGross domestic product of Scotland in 2021, by local (ITL 3) area (in million GBP)\\nGDP of Wales 2021, by local area\\nGross domestic product of Wales in 2021, by local (ITL 3) area (in million GBP)\\nGDP of Northern Ireland 2021, by local area\\nGross domestic product of Northern Ireland in 2021, by local (ITL 3) area (in million GBP)\\nGDP growth\\nGDP growth\\nGDP growth forecast for the UK 2000-2028\\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\\nAnnual GDP growth in the UK 1949-2022\\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\\nQuarterly GDP growth of the UK 2019-2023\\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023\\nMonthly GDP growth of the UK 2019-2023\\n Transforming data into design:\\nStatista Content & Design\\nStrategy and business building for the data-driven economy:\\nUK GDP - Statistics & Facts\\nUK economy expected to shrink in 2023\\nCharacteristics of UK GDP\\nKey insights\\nDetailed statistics\\nGDP of the UK 1948-2022\\nDetailed statistics\\nAnnual GDP growth in the UK 1949-2022\\nDetailed statistics\\nGDP per capita in the UK 1955-2022\\nEditor’s Picks\\nCurrent statistics on this topic\\nCurrent statistics on this topic\\nKey Economic Indicators\\nMonthly GDP growth of the UK 2019-2023\\nKey Economic Indicators\\nMonthly GDP of the UK 2019-2023\\nKey Economic Indicators\\nContribution to GDP growth in the UK 2023, by sector\\nRelated topics\\nRecommended\\nRecommended statistics\\nGDP\\nGDP\\nGDP of the UK 1948-2022\\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\\nQuarterly GDP of the UK 2019-2023\\nQuarterly gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in million GBP)\\n The 20 countries with the largest gross domestic product (GDP) in 2022 (in billion U.S. dollars)\\nGDP of European countries in 2022\\nGross domestic product at current market prices of selected European countries in 2022 (in million euros)\\nReal GDP growth rates in Europe 2023\\nAnnual real gross domestic product (GDP) growth rate in European countries in 2023\\nGross domestic product (GDP) of Europe\'s largest economies 1980-2028\\nGross domestic product (GDP) at current prices of Europe\'s largest economies from 1980 to 2028 (in billion U.S dollars)\\nUnited Kingdom\'s share of global gross domestic product (GDP) 2028\\nUnited Kingdom (UK): Share of global gross domestic product (GDP) adjusted for Purchasing Power Parity (PPP) from 2018 to 2028\\nRelated topics\\nRecommended\\nReport on the topic\\nKey figures\\nThe most important key figures provide you with a compact summary of the topic of \\"UK GDP\\" and take you straight to the corresponding statistics.\\n Industry Overview\\nDigital & Trend reports\\nOverview and forecasts on trending topics\\nIndustry & Market reports\\nIndustry and market insights and forecasts\\nCompanies & Products reports\\nKey figures and rankings about companies and products\\nConsumer & Brand reports\\nConsumer and brand insights and preferences in various industries\\nPolitics & Society reports\\nDetailed information about political and social topics\\nCountry & Region reports\\nAll key figures about countries and regions\\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\\nInsights on consumer attitudes and behavior worldwide\\nBusiness information on 100m+ public and private companies\\nExplore Company Insights\\nDetailed information for 39,000+ online stores and marketplaces\\nDirectly accessible data for 170 industries from 150+ countries\\nand over 1\xa0Mio. facts.\\n"}, {"url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB", "content": "GDP growth (annual %) - United Kingdom | Data - World Bank Data"}, {"url": "https://www.statista.com/topics/6500/the-british-economy/", "content": "Output per hour worked in the UK 1971 to 2023\\nEconomic output per hour worked in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023 (2019=100)\\nAnnual unemployment rate in the UK 2000-2028\\nAnnual unemployment rate in the United Kingdom from 2000 to 2028\\nInflation\\nInflation\\nInflation rate in the UK 1989-2023\\nInflation rate for the Consumer Price Index (CPI) in the United Kingdom from January 1989 to October 2023\\nRPI inflation rate in the UK 1948-2023\\nInflation rate for the Retail Price Index (RPI) in the United Kingdom from June 1948 to October 2023\\nCPIH inflation rate in the UK 1989-2023\\nInflation rate for the Consumer Price Index including owner occupiers\' housing costs (CPIH) in the United Kingdom from January 1989 to October 2023\\nPPI in the UK 2010-2023\\nProducer Price Index (PPI) in the United Kingdom from October 2010 to October 2023\\nCPI inflation rate in the UK 2023, by sector\\nInflation rate for the Consumer Price Index (CPI) in the United Kingdom in October 2023, by sector\\nConsumer Price Index in the UK 1988-2023\\nConsumer Price Index (CPI) in the United Kingdom from 1st quarter 1988 to 3rd quarter 2023\\nRetail Price Index in the UK 1987-2023\\nRetail Price Index (RPI) in the United Kingdom from 1st quarter 1987 to 3rd quarter 2023\\nConsumer Price Index including housing in the UK 1988-2023\\nConsumer Price Index including owner occupiers\' housing costs (CPIH) in the United Kingdom from 1st quarter 1988 to 3rd quarter 2023\\nRPI annual inflation rate UK 2000-2028\\nAnnual inflation rate of the Retail Price Index in the United Kingdom from 2000 to 2028\\nCPI annual inflation rate UK 2000-2028\\nAnnual inflation rate of the Consumer Price Index in the United Kingdom from 2000 to 2028\\nGovernment finances\\nGovernment finances\\nGovernment spending as a percentage of GDP in the UK 1900-2029\\nTotal managed expenditure expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\\nGovernment revenue as a percentage of GDP in the UK 1900-2029\\nTotal public sector current receipts expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29 (in million GBP)\\nGovernment borrowing as a percentage of GDP in the UK 1900-2029\\nPublic sector borrowing expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\\nNational debt as a percentage of GDP in the UK 1900-2029\\nPublic sector net debt expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\\nPublic sector spending in the United Kingdom 2023/24\\nBudgeted public sector expenditure on services in the United Kingdom in 2023/24, by function (in billion GBP)\\nGovernment revenue sources in the United Kingdom 2023/24\\nExpected public sector current receipts in the United Kingdom in 2023/24, by function (in billion GBP)\\nBusiness Enterprise\\nBusiness Enterprise\\nLargest companies in the United Kingdom based on revenue 2022\\nLargest companies in the United Kingdom based on revenue in 2022 (in billion US dollars)\\nLargest UK companies based on number of global employees 2020\\nLargest companies based in the United Kingdom on number of employees worldwide in 2020 (in 1,000s)\\nNumber of private sector businesses in the UK 2000-2023\\nNumber of private sector businesses in the United Kingdom from 2000 to 2023 (in millions)\\nNumber of private sector businesses in the UK 2023, by sector\\nNumber of private sector businesses in the United Kingdom in 2023, by sector\\nNumber of businesses by enterprise size in the UK 2023\\nNumber of private sector businesses in the United Kingdom in 2023, by employment size\\nNumber of private sector businesses in the UK 2023, by region\\nNumber of private sector businesses in the United Kingdom in 2023, by region\\nNumber of local business units in the UK 2012-2023\\nNumber of local units in VAT and/or PAYE based enterprises in the United Kingdom from 2012 to 2023 (in millions)\\nBusiness investment index in the UK 1997-2023\\nBusiness investment index in the United Kingdom from 1st quarter 1997 to 2nd quarter 2023 (Q1 1997=100)\\nBusiness confidence Index in the UK 1977-2023\\nBusiness confidence Index of the United Kingdom from March 1977 to November 2023 (100 = long-term average)\\nRelated topics\\nRecommended\\nReport on the topic\\nKey figures\\nThe most important key figures provide you with a compact summary of the topic of \\"The UK economy\\" and take you straight to the corresponding statistics.\\n Monthly GDP growth of the UK 2020-2023\\nMonthly growth of gross domestic product in the United Kingdom from January 2020 to September 2023\\nGDP of the UK 2021, by region\\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\\nGDP growth rate in the UK 2021, by region\\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\\nGDP per capita of the UK 2021, by region\\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\\nGDP growth forecast for the UK 2000-2028\\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\\nLabor Market\\nLabor Market\\nUnemployment rate of the UK 1971-2023\\nUnemployment rate in the United Kingdom from March 1971 to September 2023\\nEmployment rate in the UK 1971-2022\\nEmployment rate in the United Kingdom from March 1971 to July 2023\\nNumber of people unemployed in the UK 1971-2023\\nNumber of people unemployed in the United Kingdom from March 1971 to July 2023 (in 1,000s)\\nNumber of people employed in the UK 1971-2021\\nNumber of people employed in the United Kingdom from March 1971 to July 2023 (in 1,000s)\\nUnemployment rate in the UK 1971-2023, by gender\\nUnemployment rate in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023, by gender\\nUnemployment rate in the UK 1992-2023, by age group\\nUnemployment rate in the United Kingdom from May 1992 to July 2023, by age group\\nYouth unemployment rate in the UK 1992-2023\\nYouth unemployment rate in the United Kingdom from May 1992 to July 2023\\nAverage annual earnings for full-time employees in the UK 1999-2023\\nMedian annual earnings for full-time employees in the United Kingdom from 1999 to 2023 (in nominal GBP)\\nAverage weekly earning growth in the UK 2001-2023\\nAverage year-on-year growth of weekly earnings (3 month average) in the United Kingdom from March 2001 to October 2023\\nNumber of redundancies in the UK 1995-2023\\nAverage number of people made redundant in the United Kingdom from May 1995 to July 2023 (in 1,000s)\\nOverall weekly hours worked in the UK 1971-2023\\nOverall weekly hours worked for all employees in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023 (in million hours worked)\\n Transforming data into design:\\nStatista Content & Design\\nStrategy and business building for the data-driven economy:\\nThe UK economy - Statistics & Facts\\nUK households under pressure in 2023\\nCoronavirus devastates UK economy in 2020\\nKey insights\\nDetailed statistics\\nGDP of the UK 1948-2022\\nDetailed statistics\\nUnemployment rate of the UK 1971-2023\\nDetailed statistics\\nInflation rate in the UK 1989-2023\\nEditor’s Picks\\nCurrent statistics on this topic\\nCurrent statistics on this topic\\nWages & Salaries\\nAverage weekly earning growth in the UK 2001-2023\\nIncome & Expenditure\\nPublic sector spending in the United Kingdom 2023/24\\nEmployment\\nNumber of people employed in the UK 1971-2021\\nRelated topics\\nRecommended\\nRecommended statistics\\nGross domestic product\\nGross domestic product\\nGDP of the UK 1948-2022\\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\\nAnnual GDP growth in the UK 1949-2022\\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\\nGDP per capita in the UK 1955-2022\\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\\nQuarterly GDP of the UK 1955-2023\\nQuarterly gross domestic product in the United Kingdom from 1st quarter 1955 to 3rd quarter 2023 (in million GBP)\\nQuarterly GDP growth of the UK 2015-2023\\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2015 to 3rd quarter 2023\\nQuarterly GDP per capita in the UK 1955-2023\\nQuarterly GDP per capita in the United Kingdom from 1st quarter 1955 to 3rd quarter 2023 (in GBP)\\nMonthly GDP of the UK 1997-2023\\nMonthly index of gross domestic product in the United Kingdom from January 1997 to September 2023 (2019=100)\\n GDP\\nAnnual GDP growth in the UK 1949-2022\\nQuarterly GDP per capita growth in the UK 2015-2023\\nMonthly GDP growth of the UK 2020-2023\\nGDP per capita in the UK 1955-2022\\nLabor market\\nNumber of people employed in the UK 1971-2021\\nNumber of people unemployed in the UK 1971-2023\\nDaily number of jobs furloughed in the UK 2020-2021\\nAverage annual earnings for full-time employees in the UK 1999-2023\\nForecasts for 2023\\nGDP growth forecast for the UK 2000-2028\\nAnnual unemployment rate in the UK 2000-2028\\nCPI annual inflation rate UK 2000-2028\\nRPI annual inflation rate UK 2000-2028\\n Industry Overview\\nDigital & Trend reports\\nOverview and forecasts on trending topics\\nIndustry & Market reports\\nIndustry and market insights and forecasts\\nCompanies & Products reports\\nKey figures and rankings about companies and products\\nConsumer & Brand reports\\nConsumer and brand insights and preferences in various industries\\nPolitics & Society reports\\nDetailed information about political and social topics\\nCountry & Region reports\\nAll key figures about countries and regions\\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\\nInsights on consumer attitudes and behavior worldwide\\nBusiness information on 100m+ public and private companies\\nExplore Company Insights\\nDetailed information for 39,000+ online stores and marketplaces\\nDirectly accessible data for 170 industries from 150+ countries\\nand over 1\xa0Mio. facts.\\n"}, {"url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB&most_recent_value_desc=false", "content": "GDP growth (annual %) - United Kingdom | Data Data GDP growth (annual %)United Kingdom Data Catalog Data Programs International Debt Statistics Other Books and Reports For Developers GDP growth (annual %) - United Kingdom ====================================== Similar values Highest values Lowest values GDP (constant 2015 US$)  GDP (current US$)  GDP (constant LCU)  GDP: linked series (current LCU)  GDP, PPP (constant 2021 international $)  GDP (current LCU)  GDP, PPP (current international $)  GDP per capita growth (annual %)  Country Most Recent Value All Countries and Economies Country Most Recent Value This site uses cookies to optimize functionality and give you the best possible experience. If you continue to navigate this website beyond this page, cookies will be placed on your browser."}]', name='tavily_search_results_json', id='4c88089f-0ac4-4eeb-9141-722f0463b78d', tool_call_id='toolu_01Jd9dxa4Ss2NhzBhCuwUX3E', artifact={'query': 'UK GDP annual data past 5 years 2019-2023', 'follow_up_questions': None, 'answer': None, 'images': [], 'results': [{'title': 'U.K. GDP 1960-2024 - Macrotrends', 'url': 'https://www.macrotrends.net/global-metrics/countries/GBR/united-kingdom/gdp-gross-domestic-product', 'content': 'Dollar figures for GDP are converted from domestic currencies using single year official exchange rates. For a few countries where the official exchange rate does not reflect the rate effectively applied to actual foreign exchange transactions, an alternative conversion factor is used. U.K. gdp for 2023 was $3,340.03B, a 8.13% increase from 2022.', 'score': 0.97675806, 'raw_content': None}, {'title': 'UK GDP - Statistics & Facts | Statista', 'url': 'https://www.statista.com/topics/3795/gdp-of-the-uk/', 'content': 'Monthly growth of gross domestic product in the United Kingdom from January 2019 to November 2023\nContribution to GDP growth in the UK 2023, by sector\nContribution to gross domestic product growth in the United Kingdom in January 2023, by sector\nGDP growth rate in the UK 1999-2021, by country\nAnnual growth rates of gross domestic product in the United Kingdom from 1999 to 2021, by country\nGDP growth rate in the UK 2021, by region\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\nGDP growth of Scotland 2021, by local area\nAnnual growth rates of gross domestic product in Scotland in 2021, by local (ITL 3) area\nGDP growth of Wales 2021, by local area\nAnnual growth rates of gross domestic product in Wales in 2021, by local (ITL 3) area\nGDP growth of Northern Ireland 2021, by local area\nAnnual growth rates of gross domestic product in Northern Ireland in 2021, by local (ITL 3) area\nGDP per capita\nGDP per capita\nGDP per capita in the UK 1955-2022\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\nAnnual GDP per capita growth in the UK 1956-2022\nAnnual GDP per capita growth in the United Kingdom from 1956 to 2022\nQuarterly GDP per capita in the UK 2019-2023\nQuarterly GDP per capita in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\nQuarterly GDP per capita growth in the UK 2019-2023\nQuarterly GDP per capita growth in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\nGDP per capita of the UK 1999-2021, by country\nGross domestic product per capita of the United Kingdom from 1999 to 2021, by country (in GBP)\nGDP per capita of the UK 2021, by region\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\nGlobal Comparisons\nGlobal Comparisons\nCountries with the largest gross domestic product (GDP) 2022\n Monthly GDP of the UK 2019-2023\nMonthly index of gross domestic product in the United Kingdom from January 2019 to November 2023 (2019=100)\nGVA of the UK 2022, by sector\nGross value added of the United Kingdom in 2022, by industry sector (in million GBP)\nGDP of the UK 2021, by country\nGross domestic product of the United Kingdom in 2021, by country (in million GBP)\nGDP of the UK 2021, by region\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\nGDP of Scotland 2021, by local area\nGross domestic product of Scotland in 2021, by local (ITL 3) area (in million GBP)\nGDP of Wales 2021, by local area\nGross domestic product of Wales in 2021, by local (ITL 3) area (in million GBP)\nGDP of Northern Ireland 2021, by local area\nGross domestic product of Northern Ireland in 2021, by local (ITL 3) area (in million GBP)\nGDP growth\nGDP growth\nGDP growth forecast for the UK 2000-2028\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\nAnnual GDP growth in the UK 1949-2022\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\nQuarterly GDP growth of the UK 2019-2023\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023\nMonthly GDP growth of the UK 2019-2023\n Transforming data into design:\nStatista Content & Design\nStrategy and business building for the data-driven economy:\nUK GDP - Statistics & Facts\nUK economy expected to shrink in 2023\nCharacteristics of UK GDP\nKey insights\nDetailed statistics\nGDP of the UK 1948-2022\nDetailed statistics\nAnnual GDP growth in the UK 1949-2022\nDetailed statistics\nGDP per capita in the UK 1955-2022\nEditor’s Picks\nCurrent statistics on this topic\nCurrent statistics on this topic\nKey Economic Indicators\nMonthly GDP growth of the UK 2019-2023\nKey Economic Indicators\nMonthly GDP of the UK 2019-2023\nKey Economic Indicators\nContribution to GDP growth in the UK 2023, by sector\nRelated topics\nRecommended\nRecommended statistics\nGDP\nGDP\nGDP of the UK 1948-2022\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\nQuarterly GDP of the UK 2019-2023\nQuarterly gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in million GBP)\n The 20 countries with the largest gross domestic product (GDP) in 2022 (in billion U.S. dollars)\nGDP of European countries in 2022\nGross domestic product at current market prices of selected European countries in 2022 (in million euros)\nReal GDP growth rates in Europe 2023\nAnnual real gross domestic product (GDP) growth rate in European countries in 2023\nGross domestic product (GDP) of Europe\'s largest economies 1980-2028\nGross domestic product (GDP) at current prices of Europe\'s largest economies from 1980 to 2028 (in billion U.S dollars)\nUnited Kingdom\'s share of global gross domestic product (GDP) 2028\nUnited Kingdom (UK): Share of global gross domestic product (GDP) adjusted for Purchasing Power Parity (PPP) from 2018 to 2028\nRelated topics\nRecommended\nReport on the topic\nKey figures\nThe most important key figures provide you with a compact summary of the topic of "UK GDP" and take you straight to the corresponding statistics.\n Industry Overview\nDigital & Trend reports\nOverview and forecasts on trending topics\nIndustry & Market reports\nIndustry and market insights and forecasts\nCompanies & Products reports\nKey figures and rankings about companies and products\nConsumer & Brand reports\nConsumer and brand insights and preferences in various industries\nPolitics & Society reports\nDetailed information about political and social topics\nCountry & Region reports\nAll key figures about countries and regions\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\nInsights on consumer attitudes and behavior worldwide\nBusiness information on 100m+ public and private companies\nExplore Company Insights\nDetailed information for 39,000+ online stores and marketplaces\nDirectly accessible data for 170 industries from 150+ countries\nand over 1\xa0Mio. facts.\n', 'score': 0.97057647, 'raw_content': None}, {'title': 'GDP growth (annual %) - United Kingdom | Data - World Bank Data', 'url': 'https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB', 'content': 'GDP growth (annual %) - United Kingdom | Data - World Bank Data', 'score': 0.97052056, 'raw_content': None}, {'title': 'The UK economy - Statistics & Facts | Statista', 'url': 'https://www.statista.com/topics/6500/the-british-economy/', 'content': 'Output per hour worked in the UK 1971 to 2023\nEconomic output per hour worked in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023 (2019=100)\nAnnual unemployment rate in the UK 2000-2028\nAnnual unemployment rate in the United Kingdom from 2000 to 2028\nInflation\nInflation\nInflation rate in the UK 1989-2023\nInflation rate for the Consumer Price Index (CPI) in the United Kingdom from January 1989 to October 2023\nRPI inflation rate in the UK 1948-2023\nInflation rate for the Retail Price Index (RPI) in the United Kingdom from June 1948 to October 2023\nCPIH inflation rate in the UK 1989-2023\nInflation rate for the Consumer Price Index including owner occupiers\' housing costs (CPIH) in the United Kingdom from January 1989 to October 2023\nPPI in the UK 2010-2023\nProducer Price Index (PPI) in the United Kingdom from October 2010 to October 2023\nCPI inflation rate in the UK 2023, by sector\nInflation rate for the Consumer Price Index (CPI) in the United Kingdom in October 2023, by sector\nConsumer Price Index in the UK 1988-2023\nConsumer Price Index (CPI) in the United Kingdom from 1st quarter 1988 to 3rd quarter 2023\nRetail Price Index in the UK 1987-2023\nRetail Price Index (RPI) in the United Kingdom from 1st quarter 1987 to 3rd quarter 2023\nConsumer Price Index including housing in the UK 1988-2023\nConsumer Price Index including owner occupiers\' housing costs (CPIH) in the United Kingdom from 1st quarter 1988 to 3rd quarter 2023\nRPI annual inflation rate UK 2000-2028\nAnnual inflation rate of the Retail Price Index in the United Kingdom from 2000 to 2028\nCPI annual inflation rate UK 2000-2028\nAnnual inflation rate of the Consumer Price Index in the United Kingdom from 2000 to 2028\nGovernment finances\nGovernment finances\nGovernment spending as a percentage of GDP in the UK 1900-2029\nTotal managed expenditure expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\nGovernment revenue as a percentage of GDP in the UK 1900-2029\nTotal public sector current receipts expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29 (in million GBP)\nGovernment borrowing as a percentage of GDP in the UK 1900-2029\nPublic sector borrowing expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\nNational debt as a percentage of GDP in the UK 1900-2029\nPublic sector net debt expressed as a percentage of GDP in the United Kingdom from 1900/01 to 2028/29\nPublic sector spending in the United Kingdom 2023/24\nBudgeted public sector expenditure on services in the United Kingdom in 2023/24, by function (in billion GBP)\nGovernment revenue sources in the United Kingdom 2023/24\nExpected public sector current receipts in the United Kingdom in 2023/24, by function (in billion GBP)\nBusiness Enterprise\nBusiness Enterprise\nLargest companies in the United Kingdom based on revenue 2022\nLargest companies in the United Kingdom based on revenue in 2022 (in billion US dollars)\nLargest UK companies based on number of global employees 2020\nLargest companies based in the United Kingdom on number of employees worldwide in 2020 (in 1,000s)\nNumber of private sector businesses in the UK 2000-2023\nNumber of private sector businesses in the United Kingdom from 2000 to 2023 (in millions)\nNumber of private sector businesses in the UK 2023, by sector\nNumber of private sector businesses in the United Kingdom in 2023, by sector\nNumber of businesses by enterprise size in the UK 2023\nNumber of private sector businesses in the United Kingdom in 2023, by employment size\nNumber of private sector businesses in the UK 2023, by region\nNumber of private sector businesses in the United Kingdom in 2023, by region\nNumber of local business units in the UK 2012-2023\nNumber of local units in VAT and/or PAYE based enterprises in the United Kingdom from 2012 to 2023 (in millions)\nBusiness investment index in the UK 1997-2023\nBusiness investment index in the United Kingdom from 1st quarter 1997 to 2nd quarter 2023 (Q1 1997=100)\nBusiness confidence Index in the UK 1977-2023\nBusiness confidence Index of the United Kingdom from March 1977 to November 2023 (100 = long-term average)\nRelated topics\nRecommended\nReport on the topic\nKey figures\nThe most important key figures provide you with a compact summary of the topic of "The UK economy" and take you straight to the corresponding statistics.\n Monthly GDP growth of the UK 2020-2023\nMonthly growth of gross domestic product in the United Kingdom from January 2020 to September 2023\nGDP of the UK 2021, by region\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\nGDP growth rate in the UK 2021, by region\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\nGDP per capita of the UK 2021, by region\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\nGDP growth forecast for the UK 2000-2028\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\nLabor Market\nLabor Market\nUnemployment rate of the UK 1971-2023\nUnemployment rate in the United Kingdom from March 1971 to September 2023\nEmployment rate in the UK 1971-2022\nEmployment rate in the United Kingdom from March 1971 to July 2023\nNumber of people unemployed in the UK 1971-2023\nNumber of people unemployed in the United Kingdom from March 1971 to July 2023 (in 1,000s)\nNumber of people employed in the UK 1971-2021\nNumber of people employed in the United Kingdom from March 1971 to July 2023 (in 1,000s)\nUnemployment rate in the UK 1971-2023, by gender\nUnemployment rate in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023, by gender\nUnemployment rate in the UK 1992-2023, by age group\nUnemployment rate in the United Kingdom from May 1992 to July 2023, by age group\nYouth unemployment rate in the UK 1992-2023\nYouth unemployment rate in the United Kingdom from May 1992 to July 2023\nAverage annual earnings for full-time employees in the UK 1999-2023\nMedian annual earnings for full-time employees in the United Kingdom from 1999 to 2023 (in nominal GBP)\nAverage weekly earning growth in the UK 2001-2023\nAverage year-on-year growth of weekly earnings (3 month average) in the United Kingdom from March 2001 to October 2023\nNumber of redundancies in the UK 1995-2023\nAverage number of people made redundant in the United Kingdom from May 1995 to July 2023 (in 1,000s)\nOverall weekly hours worked in the UK 1971-2023\nOverall weekly hours worked for all employees in the United Kingdom from 1st quarter 1971 to 2nd quarter 2023 (in million hours worked)\n Transforming data into design:\nStatista Content & Design\nStrategy and business building for the data-driven economy:\nThe UK economy - Statistics & Facts\nUK households under pressure in 2023\nCoronavirus devastates UK economy in 2020\nKey insights\nDetailed statistics\nGDP of the UK 1948-2022\nDetailed statistics\nUnemployment rate of the UK 1971-2023\nDetailed statistics\nInflation rate in the UK 1989-2023\nEditor’s Picks\nCurrent statistics on this topic\nCurrent statistics on this topic\nWages & Salaries\nAverage weekly earning growth in the UK 2001-2023\nIncome & Expenditure\nPublic sector spending in the United Kingdom 2023/24\nEmployment\nNumber of people employed in the UK 1971-2021\nRelated topics\nRecommended\nRecommended statistics\nGross domestic product\nGross domestic product\nGDP of the UK 1948-2022\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\nAnnual GDP growth in the UK 1949-2022\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\nGDP per capita in the UK 1955-2022\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\nQuarterly GDP of the UK 1955-2023\nQuarterly gross domestic product in the United Kingdom from 1st quarter 1955 to 3rd quarter 2023 (in million GBP)\nQuarterly GDP growth of the UK 2015-2023\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2015 to 3rd quarter 2023\nQuarterly GDP per capita in the UK 1955-2023\nQuarterly GDP per capita in the United Kingdom from 1st quarter 1955 to 3rd quarter 2023 (in GBP)\nMonthly GDP of the UK 1997-2023\nMonthly index of gross domestic product in the United Kingdom from January 1997 to September 2023 (2019=100)\n GDP\nAnnual GDP growth in the UK 1949-2022\nQuarterly GDP per capita growth in the UK 2015-2023\nMonthly GDP growth of the UK 2020-2023\nGDP per capita in the UK 1955-2022\nLabor market\nNumber of people employed in the UK 1971-2021\nNumber of people unemployed in the UK 1971-2023\nDaily number of jobs furloughed in the UK 2020-2021\nAverage annual earnings for full-time employees in the UK 1999-2023\nForecasts for 2023\nGDP growth forecast for the UK 2000-2028\nAnnual unemployment rate in the UK 2000-2028\nCPI annual inflation rate UK 2000-2028\nRPI annual inflation rate UK 2000-2028\n Industry Overview\nDigital & Trend reports\nOverview and forecasts on trending topics\nIndustry & Market reports\nIndustry and market insights and forecasts\nCompanies & Products reports\nKey figures and rankings about companies and products\nConsumer & Brand reports\nConsumer and brand insights and preferences in various industries\nPolitics & Society reports\nDetailed information about political and social topics\nCountry & Region reports\nAll key figures about countries and regions\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\nInsights on consumer attitudes and behavior worldwide\nBusiness information on 100m+ public and private companies\nExplore Company Insights\nDetailed information for 39,000+ online stores and marketplaces\nDirectly accessible data for 170 industries from 150+ countries\nand over 1\xa0Mio. facts.\n', 'score': 0.95998776, 'raw_content': None}, {'title': 'GDP growth (annual %) - United Kingdom | Data - World Bank Data', 'url': 'https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB&most_recent_value_desc=false', 'content': 'GDP growth (annual %) - United Kingdom | Data Data GDP growth (annual %)United Kingdom Data Catalog Data Programs International Debt Statistics Other Books and Reports For Developers GDP growth (annual %) - United Kingdom ====================================== Similar values Highest values Lowest values GDP (constant 2015 US$)  GDP (current US$)  GDP (constant LCU)  GDP: linked series (current LCU)  GDP, PPP (constant 2021 international $)  GDP (current LCU)  GDP, PPP (current international $)  GDP per capita growth (annual %)  Country Most Recent Value All Countries and Economies Country Most Recent Value This site uses cookies to optimize functionality and give you the best possible experience. If you continue to navigate this website beyond this page, cookies will be placed on your browser.', 'score': 0.7892337, 'raw_content': None}], 'response_time': 2.3}), AIMessage(content=[{'text': 'Let me search for more specific data.', 'type': 'text'}, {'id': 'toolu_019dPRXojLJoVNYFLzzSWw4w', 'input': {'query': 'UK GDP values by year 2019 2020 2021 2022 2023'}, 'name': 'tavily_search_results_json', 'type': 'tool_use'}], additional_kwargs={}, response_metadata={'id': 'msg_01Ac9vcTFneb5dvcEYXJyf1P', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'tool_use', 'stop_sequence': None, 'usage': {'input_tokens': 5890, 'output_tokens': 87}}, id='run-3504417f-c0b5-4908-82e2-89a18abb1b8e-0', tool_calls=[{'name': 'tavily_search_results_json', 'args': {'query': 'UK GDP values by year 2019 2020 2021 2022 2023'}, 'id': 'toolu_019dPRXojLJoVNYFLzzSWw4w', 'type': 'tool_call'}], usage_metadata={'input_tokens': 5890, 'output_tokens': 87, 'total_tokens': 5977, 'input_token_details': {}}), ToolMessage(content='[{"url": "https://www.macrotrends.net/global-metrics/countries/GBR/united-kingdom/gdp-gross-domestic-product", "content": "U.K. gdp for 2023 was $3,340.03B, a 8.13% increase from 2022. U.K. gdp for 2022 was $3,088.84B, a 1.68% decline from 2021. U.K. gdp for 2021 was $3,141.51B, a 16.45% increase from 2020. U.K. gdp for 2020 was $2,697.81B, a 5.39% decline from 2019."}, {"url": "https://countryeconomy.com/gdp/uk?year=2023", "content": "Gross Domestic Product of United Kingdom grew 0.3% in 2023 compared to last year. This rate is 45 -tenths of one percent less than the figure of 4.8% published in 2022. The GDP figure in 2023 was $3,380,855 million, leaving United Kingdom placed 6th in the ranking of GDP of the 196 countries that we publish."}, {"url": "https://www.statista.com/topics/3795/gdp-of-the-uk/", "content": "Monthly growth of gross domestic product in the United Kingdom from January 2019 to November 2023\\nContribution to GDP growth in the UK 2023, by sector\\nContribution to gross domestic product growth in the United Kingdom in January 2023, by sector\\nGDP growth rate in the UK 1999-2021, by country\\nAnnual growth rates of gross domestic product in the United Kingdom from 1999 to 2021, by country\\nGDP growth rate in the UK 2021, by region\\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\\nGDP growth of Scotland 2021, by local area\\nAnnual growth rates of gross domestic product in Scotland in 2021, by local (ITL 3) area\\nGDP growth of Wales 2021, by local area\\nAnnual growth rates of gross domestic product in Wales in 2021, by local (ITL 3) area\\nGDP growth of Northern Ireland 2021, by local area\\nAnnual growth rates of gross domestic product in Northern Ireland in 2021, by local (ITL 3) area\\nGDP per capita\\nGDP per capita\\nGDP per capita in the UK 1955-2022\\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\\nAnnual GDP per capita growth in the UK 1956-2022\\nAnnual GDP per capita growth in the United Kingdom from 1956 to 2022\\nQuarterly GDP per capita in the UK 2019-2023\\nQuarterly GDP per capita in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\\nQuarterly GDP per capita growth in the UK 2019-2023\\nQuarterly GDP per capita growth in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\\nGDP per capita of the UK 1999-2021, by country\\nGross domestic product per capita of the United Kingdom from 1999 to 2021, by country (in GBP)\\nGDP per capita of the UK 2021, by region\\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\\nGlobal Comparisons\\nGlobal Comparisons\\nCountries with the largest gross domestic product (GDP) 2022\\n Monthly GDP of the UK 2019-2023\\nMonthly index of gross domestic product in the United Kingdom from January 2019 to November 2023 (2019=100)\\nGVA of the UK 2022, by sector\\nGross value added of the United Kingdom in 2022, by industry sector (in million GBP)\\nGDP of the UK 2021, by country\\nGross domestic product of the United Kingdom in 2021, by country (in million GBP)\\nGDP of the UK 2021, by region\\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\\nGDP of Scotland 2021, by local area\\nGross domestic product of Scotland in 2021, by local (ITL 3) area (in million GBP)\\nGDP of Wales 2021, by local area\\nGross domestic product of Wales in 2021, by local (ITL 3) area (in million GBP)\\nGDP of Northern Ireland 2021, by local area\\nGross domestic product of Northern Ireland in 2021, by local (ITL 3) area (in million GBP)\\nGDP growth\\nGDP growth\\nGDP growth forecast for the UK 2000-2028\\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\\nAnnual GDP growth in the UK 1949-2022\\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\\nQuarterly GDP growth of the UK 2019-2023\\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023\\nMonthly GDP growth of the UK 2019-2023\\n Transforming data into design:\\nStatista Content & Design\\nStrategy and business building for the data-driven economy:\\nUK GDP - Statistics & Facts\\nUK economy expected to shrink in 2023\\nCharacteristics of UK GDP\\nKey insights\\nDetailed statistics\\nGDP of the UK 1948-2022\\nDetailed statistics\\nAnnual GDP growth in the UK 1949-2022\\nDetailed statistics\\nGDP per capita in the UK 1955-2022\\nEditor’s Picks\\nCurrent statistics on this topic\\nCurrent statistics on this topic\\nKey Economic Indicators\\nMonthly GDP growth of the UK 2019-2023\\nKey Economic Indicators\\nMonthly GDP of the UK 2019-2023\\nKey Economic Indicators\\nContribution to GDP growth in the UK 2023, by sector\\nRelated topics\\nRecommended\\nRecommended statistics\\nGDP\\nGDP\\nGDP of the UK 1948-2022\\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\\nQuarterly GDP of the UK 2019-2023\\nQuarterly gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in million GBP)\\n The 20 countries with the largest gross domestic product (GDP) in 2022 (in billion U.S. dollars)\\nGDP of European countries in 2022\\nGross domestic product at current market prices of selected European countries in 2022 (in million euros)\\nReal GDP growth rates in Europe 2023\\nAnnual real gross domestic product (GDP) growth rate in European countries in 2023\\nGross domestic product (GDP) of Europe\'s largest economies 1980-2028\\nGross domestic product (GDP) at current prices of Europe\'s largest economies from 1980 to 2028 (in billion U.S dollars)\\nUnited Kingdom\'s share of global gross domestic product (GDP) 2028\\nUnited Kingdom (UK): Share of global gross domestic product (GDP) adjusted for Purchasing Power Parity (PPP) from 2018 to 2028\\nRelated topics\\nRecommended\\nReport on the topic\\nKey figures\\nThe most important key figures provide you with a compact summary of the topic of \\"UK GDP\\" and take you straight to the corresponding statistics.\\n Industry Overview\\nDigital & Trend reports\\nOverview and forecasts on trending topics\\nIndustry & Market reports\\nIndustry and market insights and forecasts\\nCompanies & Products reports\\nKey figures and rankings about companies and products\\nConsumer & Brand reports\\nConsumer and brand insights and preferences in various industries\\nPolitics & Society reports\\nDetailed information about political and social topics\\nCountry & Region reports\\nAll key figures about countries and regions\\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\\nInsights on consumer attitudes and behavior worldwide\\nBusiness information on 100m+ public and private companies\\nExplore Company Insights\\nDetailed information for 39,000+ online stores and marketplaces\\nDirectly accessible data for 170 industries from 150+ countries\\nand over 1\xa0Mio. facts.\\n"}, {"url": "https://www.ons.gov.uk/economy/grossdomesticproductgdp/compendium/unitedkingdomnationalaccountsthebluebook/2024/nationalaccountsataglance", "content": "Real gross domestic product (GDP) is estimated to have increased by 0.3% in 2023, following a recovery from the impacts of the coronavirus (COVID-19) pandemic over the two previous years (Figure 1). Data for the UK are the Office for National Statistics (ONS) measure of real gross domestic product (GDP). Figure 9: Real GDP per head fell in 2023 when compared with 2022 in six G10 economies, including the UK Data for the UK are the Office for National Statistics (ONS) measure of real gross domestic product (GDP) per head. Download this chart Figure 9: Real GDP per head fell in 2023 when compared with 2022 in six G10 economies, including the UK"}, {"url": "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB&most_recent_value_desc=false", "content": "GDP growth (annual %) - United Kingdom | Data Data GDP growth (annual %)United Kingdom Data Catalog Data Programs International Debt Statistics Other Books and Reports For Developers GDP growth (annual %) - United Kingdom ====================================== Similar values Highest values Lowest values GDP (constant 2015 US$)  GDP (current US$)  GDP (constant LCU)  GDP: linked series (current LCU)  GDP, PPP (constant 2021 international $)  GDP (current LCU)  GDP, PPP (current international $)  GDP per capita growth (annual %)  Country Most Recent Value All Countries and Economies Country Most Recent Value This site uses cookies to optimize functionality and give you the best possible experience. If you continue to navigate this website beyond this page, cookies will be placed on your browser."}]', name='tavily_search_results_json', id='84c571ca-27c6-4023-93a2-f0c2e8b6abb0', tool_call_id='toolu_019dPRXojLJoVNYFLzzSWw4w', artifact={'query': 'UK GDP values by year 2019 2020 2021 2022 2023', 'follow_up_questions': None, 'answer': None, 'images': [], 'results': [{'title': 'U.K. GDP 1960-2024 - Macrotrends', 'url': 'https://www.macrotrends.net/global-metrics/countries/GBR/united-kingdom/gdp-gross-domestic-product', 'content': 'U.K. gdp for 2023 was $3,340.03B, a 8.13% increase from 2022. U.K. gdp for 2022 was $3,088.84B, a 1.68% decline from 2021. U.K. gdp for 2021 was $3,141.51B, a 16.45% increase from 2020. U.K. gdp for 2020 was $2,697.81B, a 5.39% decline from 2019.', 'score': 0.9974491, 'raw_content': None}, {'title': 'United Kingdom (UK) GDP - Gross Domestic Product 2023', 'url': 'https://countryeconomy.com/gdp/uk?year=2023', 'content': 'Gross Domestic Product of United Kingdom grew 0.3% in 2023 compared to last year. This rate is 45 -tenths of one percent less than the figure of 4.8% published in 2022. The GDP figure in 2023 was $3,380,855 million, leaving United Kingdom placed 6th in the ranking of GDP of the 196 countries that we publish.', 'score': 0.9964064, 'raw_content': None}, {'title': 'UK GDP - Statistics & Facts | Statista', 'url': 'https://www.statista.com/topics/3795/gdp-of-the-uk/', 'content': 'Monthly growth of gross domestic product in the United Kingdom from January 2019 to November 2023\nContribution to GDP growth in the UK 2023, by sector\nContribution to gross domestic product growth in the United Kingdom in January 2023, by sector\nGDP growth rate in the UK 1999-2021, by country\nAnnual growth rates of gross domestic product in the United Kingdom from 1999 to 2021, by country\nGDP growth rate in the UK 2021, by region\nAnnual growth rates of gross domestic product in the United Kingdom in 2021, by region\nGDP growth of Scotland 2021, by local area\nAnnual growth rates of gross domestic product in Scotland in 2021, by local (ITL 3) area\nGDP growth of Wales 2021, by local area\nAnnual growth rates of gross domestic product in Wales in 2021, by local (ITL 3) area\nGDP growth of Northern Ireland 2021, by local area\nAnnual growth rates of gross domestic product in Northern Ireland in 2021, by local (ITL 3) area\nGDP per capita\nGDP per capita\nGDP per capita in the UK 1955-2022\nGross domestic product per capita in the United Kingdom from 1955 to 2022 (in GBP)\nAnnual GDP per capita growth in the UK 1956-2022\nAnnual GDP per capita growth in the United Kingdom from 1956 to 2022\nQuarterly GDP per capita in the UK 2019-2023\nQuarterly GDP per capita in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\nQuarterly GDP per capita growth in the UK 2019-2023\nQuarterly GDP per capita growth in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in GBP)\nGDP per capita of the UK 1999-2021, by country\nGross domestic product per capita of the United Kingdom from 1999 to 2021, by country (in GBP)\nGDP per capita of the UK 2021, by region\nGross domestic product per capita of the United Kingdom in 2021, by region (in GBP)\nGlobal Comparisons\nGlobal Comparisons\nCountries with the largest gross domestic product (GDP) 2022\n Monthly GDP of the UK 2019-2023\nMonthly index of gross domestic product in the United Kingdom from January 2019 to November 2023 (2019=100)\nGVA of the UK 2022, by sector\nGross value added of the United Kingdom in 2022, by industry sector (in million GBP)\nGDP of the UK 2021, by country\nGross domestic product of the United Kingdom in 2021, by country (in million GBP)\nGDP of the UK 2021, by region\nGross domestic product of the United Kingdom in 2021, by region (in million GBP)\nGDP of Scotland 2021, by local area\nGross domestic product of Scotland in 2021, by local (ITL 3) area (in million GBP)\nGDP of Wales 2021, by local area\nGross domestic product of Wales in 2021, by local (ITL 3) area (in million GBP)\nGDP of Northern Ireland 2021, by local area\nGross domestic product of Northern Ireland in 2021, by local (ITL 3) area (in million GBP)\nGDP growth\nGDP growth\nGDP growth forecast for the UK 2000-2028\nForecasted annual growth of gross domestic product in the United Kingdom from 2000 to 2028\nAnnual GDP growth in the UK 1949-2022\nAnnual growth of gross domestic product in the United Kingdom from 1949 to 2022\nQuarterly GDP growth of the UK 2019-2023\nQuarterly growth of gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023\nMonthly GDP growth of the UK 2019-2023\n Transforming data into design:\nStatista Content & Design\nStrategy and business building for the data-driven economy:\nUK GDP - Statistics & Facts\nUK economy expected to shrink in 2023\nCharacteristics of UK GDP\nKey insights\nDetailed statistics\nGDP of the UK 1948-2022\nDetailed statistics\nAnnual GDP growth in the UK 1949-2022\nDetailed statistics\nGDP per capita in the UK 1955-2022\nEditor’s Picks\nCurrent statistics on this topic\nCurrent statistics on this topic\nKey Economic Indicators\nMonthly GDP growth of the UK 2019-2023\nKey Economic Indicators\nMonthly GDP of the UK 2019-2023\nKey Economic Indicators\nContribution to GDP growth in the UK 2023, by sector\nRelated topics\nRecommended\nRecommended statistics\nGDP\nGDP\nGDP of the UK 1948-2022\nGross domestic product of the United Kingdom from 1948 to 2022 (in million GBP)\nQuarterly GDP of the UK 2019-2023\nQuarterly gross domestic product in the United Kingdom from 1st quarter 2019 to 3rd quarter 2023 (in million GBP)\n The 20 countries with the largest gross domestic product (GDP) in 2022 (in billion U.S. dollars)\nGDP of European countries in 2022\nGross domestic product at current market prices of selected European countries in 2022 (in million euros)\nReal GDP growth rates in Europe 2023\nAnnual real gross domestic product (GDP) growth rate in European countries in 2023\nGross domestic product (GDP) of Europe\'s largest economies 1980-2028\nGross domestic product (GDP) at current prices of Europe\'s largest economies from 1980 to 2028 (in billion U.S dollars)\nUnited Kingdom\'s share of global gross domestic product (GDP) 2028\nUnited Kingdom (UK): Share of global gross domestic product (GDP) adjusted for Purchasing Power Parity (PPP) from 2018 to 2028\nRelated topics\nRecommended\nReport on the topic\nKey figures\nThe most important key figures provide you with a compact summary of the topic of "UK GDP" and take you straight to the corresponding statistics.\n Industry Overview\nDigital & Trend reports\nOverview and forecasts on trending topics\nIndustry & Market reports\nIndustry and market insights and forecasts\nCompanies & Products reports\nKey figures and rankings about companies and products\nConsumer & Brand reports\nConsumer and brand insights and preferences in various industries\nPolitics & Society reports\nDetailed information about political and social topics\nCountry & Region reports\nAll key figures about countries and regions\nMarket forecast and expert KPIs for 1000+ markets in 190+ countries & territories\nInsights on consumer attitudes and behavior worldwide\nBusiness information on 100m+ public and private companies\nExplore Company Insights\nDetailed information for 39,000+ online stores and marketplaces\nDirectly accessible data for 170 industries from 150+ countries\nand over 1\xa0Mio. facts.\n', 'score': 0.97943294, 'raw_content': None}, {'title': 'National accounts at a glance - Office for National Statistics', 'url': 'https://www.ons.gov.uk/economy/grossdomesticproductgdp/compendium/unitedkingdomnationalaccountsthebluebook/2024/nationalaccountsataglance', 'content': 'Real gross domestic product (GDP) is estimated to have increased by 0.3% in 2023, following a recovery from the impacts of the coronavirus (COVID-19) pandemic over the two previous years (Figure 1). Data for the UK are the Office for National Statistics (ONS) measure of real gross domestic product (GDP). Figure 9: Real GDP per head fell in 2023 when compared with 2022 in six G10 economies, including the UK Data for the UK are the Office for National Statistics (ONS) measure of real gross domestic product (GDP) per head. Download this chart Figure 9: Real GDP per head fell in 2023 when compared with 2022 in six G10 economies, including the UK', 'score': 0.975249, 'raw_content': None}, {'title': 'GDP growth (annual %) - United Kingdom | Data - World Bank Data', 'url': 'https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=GB&most_recent_value_desc=false', 'content': 'GDP growth (annual %) - United Kingdom | Data Data GDP growth (annual %)United Kingdom Data Catalog Data Programs International Debt Statistics Other Books and Reports For Developers GDP growth (annual %) - United Kingdom ====================================== Similar values Highest values Lowest values GDP (constant 2015 US$)  GDP (current US$)  GDP (constant LCU)  GDP: linked series (current LCU)  GDP, PPP (constant 2021 international $)  GDP (current LCU)  GDP, PPP (current international $)  GDP per capita growth (annual %)  Country Most Recent Value All Countries and Economies Country Most Recent Value This site uses cookies to optimize functionality and give you the best possible experience. If you continue to navigate this website beyond this page, cookies will be placed on your browser.', 'score': 0.83775276, 'raw_content': None}], 'response_time': 2.37}), HumanMessage(content='Based on the search results, I can provide the UK\'s GDP values for the past 5 years (in billions of US dollars):\n\n2019: $2,851.54\n2020: $2,697.81\n2021: $3,141.51\n2022: $3,088.84\n2023: $3,340.03\n\nI\'ll pass this data to my chart generator colleague to create a line chart. They should create a line chart with:\n- Years 2019-2023 on the x-axis\n- GDP values in billions USD on the y-axis\n- Title: "UK GDP 2019-2023"\n- Clear data points showing the values\n\nOver to you, chart generator colleague!', additional_kwargs={}, response_metadata={}, name='researcher', id='7e790b7a-7b06-4b45-a595-8736b53db844'), AIMessage(content=[{'text': "I'll create a line chart with the specified GDP data and requirements using Python and matplotlib.", 'type': 'text'}, {'id': 'toolu_017HmYWRMpnhPaw3SamZCQua', 'input': {'code': "import matplotlib.pyplot as plt\n\nyears = [2019, 2020, 2021, 2022, 2023]\ngdp = [2851.54, 2697.81, 3141.51, 3088.84, 3340.03]\n\nplt.figure(figsize=(10, 6))\nplt.plot(years, gdp, marker='o', linewidth=2, markersize=8)\n\nplt.title('UK GDP 2019-2023', pad=15, size=14)\nplt.xlabel('Year', labelpad=10)\nplt.ylabel('GDP (Billions USD)', labelpad=10)\n\n# Add value labels above each point\nfor i, value in enumerate(gdp):\n    plt.text(years[i], value + 30, f'${value}B', ha='center')\n\nplt.grid(True, linestyle='--', alpha=0.7)\nplt.show()"}, 'name': 'python_repl_tool', 'type': 'tool_use'}], additional_kwargs={}, response_metadata={'id': 'msg_01Y29F46KJQzTmefwQL6s9Dp', 'model': 'claude-3-5-sonnet-20241022', 'stop_reason': 'tool_use', 'stop_sequence': None, 'usage': {'input_tokens': 8744, 'output_tokens': 295}}, id='run-e0ee838e-1c18-46d9-bed7-459330376276-0', tool_calls=[{'name': 'python_repl_tool', 'args': {'code': "import matplotlib.pyplot as plt\n\nyears = [2019, 2020, 2021, 2022, 2023]\ngdp = [2851.54, 2697.81, 3141.51, 3088.84, 3340.03]\n\nplt.figure(figsize=(10, 6))\nplt.plot(years, gdp, marker='o', linewidth=2, markersize=8)\n\nplt.title('UK GDP 2019-2023', pad=15, size=14)\nplt.xlabel('Year', labelpad=10)\nplt.ylabel('GDP (Billions USD)', labelpad=10)\n\n# Add value labels above each point\nfor i, value in enumerate(gdp):\n    plt.text(years[i], value + 30, f'${value}B', ha='center')\n\nplt.grid(True, linestyle='--', alpha=0.7)\nplt.show()"}, 'id': 'toolu_017HmYWRMpnhPaw3SamZCQua', 'type': 'tool_call'}], usage_metadata={'input_tokens': 8744, 'output_tokens': 295, 'total_tokens': 9039, 'input_token_details': {}}), ToolMessage(content="Successfully executed:\n\`\`\`python\nimport matplotlib.pyplot as plt\n\nyears = [2019, 2020, 2021, 2022, 2023]\ngdp = [2851.54, 2697.81, 3141.51, 3088.84, 3340.03]\n\nplt.figure(figsize=(10, 6))\nplt.plot(years, gdp, marker='o', linewidth=2, markersize=8)\n\nplt.title('UK GDP 2019-2023', pad=15, size=14)\nplt.xlabel('Year', labelpad=10)\nplt.ylabel('GDP (Billions USD)', labelpad=10)\n\n# Add value labels above each point\nfor i, value in enumerate(gdp):\n    plt.text(years[i], value + 30, f'${value}B', ha='center')\n\nplt.grid(True, linestyle='--', alpha=0.7)\nplt.show()\n\`\`\`\nStdout: \n\nIf you have completed all tasks, respond with FINAL ANSWER.", name='python_repl_tool', id='5421128d-9996-4dc5-b14c-77b862912d94', tool_call_id='toolu_017HmYWRMpnhPaw3SamZCQua'), HumanMessage(content='FINAL ANSWER: I have created a line chart showing the UK\'s GDP from 2019 to 2023. The chart includes:\n- A clear line with marked data points\n- Years on the x-axis\n- GDP values in billions USD on the y-axis\n- Value labels above each data point\n- A grid for better readability\n- The title "UK GDP 2019-2023"\n\nThe chart clearly shows the GDP drop in 2020 due to the pandemic, followed by recovery and growth through 2023, with the most recent value reaching $3,340.03 billion.', additional_kwargs={}, response_metadata={}, name='chart_generator', id='4a649455-eed8-4b4f-a19f-c172140430c3')]}}
----

```

## Comments

giscus

#### [5 reactions](https://github.com/langchain-ai/langgraph/discussions/511)

👍3😕1❤️1

#### [27 comments](https://github.com/langchain-ai/langgraph/discussions/511)

#### ·

#### 27 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@Fancyfoot](https://avatars.githubusercontent.com/u/34892276?u=81f9c08d1b8dc7a11d2a8c189460ff0b7a323a2d&v=4)Fancyfoot](https://github.com/Fancyfoot) [May 21, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9502199)

awesome but how can we change to start to legal Team collaboration for searching and retrieving text ?

1

1 reply

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [May 21, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9503287)

Contributor

Could you share more about what you're struggling with? Are you asking whether the design pattern permits other agent personas and tools beyond the ones shown in the example?

❤️1

[![@kurtinau](https://avatars.githubusercontent.com/u/16972334?v=4)kurtinau](https://github.com/kurtinau) [May 21, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9505221)

This tutorial cannot run on gpt-4o, will give bugs " keyerror: chart\_generator". But works fine when use gpt-4-1106-preview.

1

👍2

3 replies

[![@guangyuxu](https://avatars.githubusercontent.com/u/5019200?u=ae791aadb06e47f24a1923a3a32101039e31c5d2&v=4)](https://github.com/guangyuxu)

[guangyuxu](https://github.com/guangyuxu) [Aug 15, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10343135)

Neither gpt-4o, nor gpt-4-turbo, gpt-4-1106-preview works.

The AI message content is missing

[![@bhumikaZysk](https://avatars.githubusercontent.com/u/179929104?v=4)](https://github.com/bhumikaZysk)

[bhumikaZysk](https://github.com/bhumikaZysk) [Sep 12, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10625010)

Did you resolve it?

If yes, how?

[![@hjerpe](https://avatars.githubusercontent.com/u/1935882?u=17ea3003344cfc018e23674610814269b809818a&v=4)](https://github.com/hjerpe)

[hjerpe](https://github.com/hjerpe) [Jan 15](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-11845075)

I just ran it with gpt-4o, it works good. I'm using the `AzureChatOpenAI` though, but I do not think it would matter.

[![@gregorybarnes](https://avatars.githubusercontent.com/u/18541851?u=43103d3ce048d553de82f58e5e261036d743110f&v=4)gregorybarnes](https://github.com/gregorybarnes) [May 22, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9516190)

edited

Looks like gpt-3.5-turbo also causes the "KeyError: 'chart\_generator'" and gpt-4 triggers rate limit issues:

`RateLimitError: Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4 in organization org-xxxxxxxxxxxxx on tokens per min (TPM): Limit 10000, Used 6299, Requested 3987. Please try again in 1.716s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}`.

I'm too lazy to add code to handle rate limits but interestingly it works fine for "gpt-4-1106-preview" which is enough to prove out the concept.

1

0 replies

[![@chuangzhidan](https://avatars.githubusercontent.com/u/62476420?v=4)chuangzhidan](https://github.com/chuangzhidan) [May 28, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9574943)

me2："KeyError: 'chart\_generator'"

1

😕1

0 replies

[![@s-spillias](https://avatars.githubusercontent.com/u/47622332?v=4)s-spillias](https://github.com/s-spillias) [May 30, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9601396)

I'm using gpt-4-turbo and it works.

But, when I tried swapping out the 'tavily\_tool' for a duckduckgo search tool. Everything works perfectly retrieving information from the internet but then encounters the same error when generating the plot: KeyError: 'chart\_generator'

1

1 reply

[![@chuangzhidan](https://avatars.githubusercontent.com/u/62476420?v=4)](https://github.com/chuangzhidan)

[chuangzhidan](https://github.com/chuangzhidan) [May 30, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9601543)

really annoying，isn't It

[![@Vesnica](https://avatars.githubusercontent.com/u/1401615?v=4)Vesnica](https://github.com/Vesnica) [Jun 6, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9686497)

For gpt-4o, change the following code to make it work:

```
...
research_agent = create_agent(
    llm,
    [tavily_tool],
    system_message="You should provide accurate data for use, "
        "and source code shouldn't be the final answer",
)
...
chart_agent = create_agent(
    llm,
    [python_repl],
    system_message="Run the python code to display the chart.",
)
```

2

👍1

4 replies

[![@chuangzhidan](https://avatars.githubusercontent.com/u/62476420?v=4)](https://github.com/chuangzhidan)

[chuangzhidan](https://github.com/chuangzhidan) [Jun 6, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9686783)

edited

> For gpt-4o, change the following code to make it work:
>
> ```
> ...
> research_agent = create_agent(
>     llm,
>     [tavily_tool],
>     system_message="You should provide accurate data for use, "
>         "and source code shouldn't be the final answer",
> )
> ...
> chart_agent = create_agent(
>     llm,
>     [python_repl],
>     system_message="Run the python code to display the chart.",
> )
> ```

do you know how to make this work with opensource models?

[![@chuangzhidan](https://avatars.githubusercontent.com/u/62476420?v=4)](https://github.com/chuangzhidan)

[chuangzhidan](https://github.com/chuangzhidan) [Jun 6, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9688289)

> For gpt-4o, change the following code to make it work:
>
> ```
> ...
> research_agent = create_agent(
>     llm,
>     [tavily_tool],
>     system_message="You should provide accurate data for use, "
>         "and source code shouldn't be the final answer",
> )
> ...
> chart_agent = create_agent(
>     llm,
>     [python_repl],
>     system_message="Run the python code to display the chart.",
> )
> ```

all you need to do is change those two prompts?

[![@Vesnica](https://avatars.githubusercontent.com/u/1401615?v=4)](https://github.com/Vesnica)

[Vesnica](https://github.com/Vesnica) [Jun 7, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9695354)

Yes, the key point lies in the prompt. The previous prompt caused errors under gpt-4o because it thought it needed to call a tool named chat\_generator(which doesn't exist), and it also believed that showing the source code to the user would be sufficient to conclude. The modifications to these two prompts were made to correct these issues. Other open-source LLM may also exhibit different behaviors, requiring appropriate adjustments to the prompts.

👍1

[![@chuangzhidan](https://avatars.githubusercontent.com/u/62476420?v=4)](https://github.com/chuangzhidan)

[chuangzhidan](https://github.com/chuangzhidan) [Jun 7, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9695647)

thank u for sharing,it's very insightful. :)

the real issue with open-source LLMs is they do not support ChatOpenAI lib so well to begin with.

[![@petkovikjandrej](https://avatars.githubusercontent.com/u/101216266?v=4)petkovikjandrej](https://github.com/petkovikjandrej) [Jun 24, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9863571)

Has anyone encountered this error :

ValidationException: An error occurred (ValidationException) when calling the InvokeModel operation: Your API request included an `assistant` message in the final position, which would pre-fill the `assistant` response. When using tools, pre-filling the `assistant` response is not supported.

I can't seem to find anything related to it. This error occurs in a multi-agent graph set up when trying to invoke a Bedrock model.

1

1 reply

[![@petkovikjandrej](https://avatars.githubusercontent.com/u/101216266?v=4)](https://github.com/petkovikjandrej)

[petkovikjandrej](https://github.com/petkovikjandrej) [Jun 24, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9863619)

## I am trying to set up a react sql agent to work together with a chart\_generator agent.   Got:   {'SQLAgent': {'messages': \[AIMessage(content='', additional\_kwargs={'usage': {'prompt\_tokens': 1045, 'completion\_tokens': 83, 'total\_tokens': 1128}, 'stop\_reason': 'tool\_use', 'model\_id': 'anthropic.claude-3-haiku-20240307-v1:0'}, response\_metadata={'usage': {'prompt\_tokens': 1045, 'completion\_tokens': 83, 'total\_tokens': 1128}, 'stop\_reason': 'tool\_use', 'model\_id': 'anthropic.claude-3-haiku-20240307-v1:0'}, name='SQLAgent', id='run-c24f62ea-355c-4db8-9f05-9698e5198765-0', tool\_calls=\[{'name': 'sql\_db\_list\_tables', 'args': {'tool\_input': ''}, 'id': 'toolu\_bdrk\_01XC2TpLh94rZgiDtnjXKKUa'}\])\], 'sender': 'SQLAgent'}}

[![@bab-git](https://avatars.githubusercontent.com/u/39730592?u=f10ec00ff4b21a481f40d3e9be5298c56406d730&v=4)bab-git](https://github.com/bab-git) [Jun 25, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9870194)

Your pipeline has a complicated yet effective automated process. But your sample invoke shows how it can get trapped in a local infinity loop between two Nodes/Agents. Beside using hard limits such as revision\_number or tried\_number to escape from such loop, do you have any architectural idea to solve such issues?

Can supervision architecture be a solution here?

1

0 replies

[![@petkovikjandrej](https://avatars.githubusercontent.com/u/101216266?v=4)petkovikjandrej](https://github.com/petkovikjandrej) [Jun 25, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9874052)

I've broken the graph to the to only SQLAgent, sql\_tool\_node and the **end** state. Here everything works as intended, so I am assuming the problem is in the router with passing of the state to the chart\_generator. Does the chart\_generator have to have access to the sql\_tool\_node in order to call py\_repl\_node to perform the plotting? And what does the router do? Here is my router:

```notranslate
def router(state: AgentState) -> Literal["py_repl_tool", "sql_tool", "__end__", "continue"]:
    # This is the router
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        # The previous agent is invoking a tool
        return "sql_tool"
    if "function_call" in last_message.additional_kwargs:
        return "py_repl_tool"
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return "__end__"
    return "__end__"

```

1

0 replies

[![@ChenBinbin2023](https://avatars.githubusercontent.com/u/141984003?v=4)ChenBinbin2023](https://github.com/ChenBinbin2023) [Jun 28, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9900178)

Got error：

ValueError: status\_code: 400

code: InvalidParameter

message: Role must be user or assistant and Content length must be greater than 0

1

1 reply

[![@jason571](https://avatars.githubusercontent.com/u/22809213?u=502f53cda238b9dab373225952300013af9603b7&v=4)](https://github.com/jason571)

[jason571](https://github.com/jason571) [Sep 19, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10692980)

> Got error：
>
> ValueError: status\_code: 400 code: InvalidParameter message: Role must be user or assistant and Content length must be greater than 0

I was fine before, using the same model, and I've been getting this error lately, and I'm not sure why

[![@gabayben](https://avatars.githubusercontent.com/u/9704848?v=4)gabayben](https://github.com/gabayben) [Jun 30, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9914392)

You should format the json response that you display. It's really hard to follow.

1

0 replies

[![@padusumilli](https://avatars.githubusercontent.com/u/5116290?v=4)padusumilli](https://github.com/padusumilli) [Jul 3, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9948192)

I tried to customize this example with my own tools, but I see below error.

```notranslate
    lambda x: x["sender"],
              ~^^^^^^^^^^
KeyError: 'sender'

```

Any suggestions, please?

1

2 replies

[![@buddypia](https://avatars.githubusercontent.com/u/743904?u=f87a0fb50fba62dcd3efe27103d386e16abd2b7b&v=4)](https://github.com/buddypia)

[buddypia](https://github.com/buddypia) [Jul 6, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9973507)

You will need to use the gpt-4-1106-preview model or use this as a reference to change to the gpt-4o model and prompt.

[https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9688289](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9688289)

[![@Tulyakai](https://avatars.githubusercontent.com/u/59692444?u=2a14efaafa031f721415be7ebb038ce8b653e864&v=4)](https://github.com/Tulyakai)

[Tulyakai](https://github.com/Tulyakai) [Jul 9, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-9995860)

Check on the State model. Have it already defined sender key

[![@jimjosephjohn](https://avatars.githubusercontent.com/u/35094079?u=dca164fa10b1e9eac84df310d12b6fb3bbbff9a9&v=4)jimjosephjohn](https://github.com/jimjosephjohn) [Jul 10, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10004949)

I am getting the following error when. running multi-agent-collobration.ipynb. Can someone help?

Error code: 400 - {'error': {'message': "An assistant message with 'tool\_calls' must be followed by tool messages responding to each 'tool\_call\_id'. The following tool\_call\_ids did not have response messages: call\_NEv19stcIQYKEzIodrGshzRv", 'type': 'invalid\_request\_error', 'param': 'messages', 'code': None}}

Output is truncated. View as a scrollable element or open in a text editor. Adjust cell output settings...

1

4 replies

[![@Hetens](https://avatars.githubusercontent.com/u/92987462?u=2cbbc8b002e3a15a2f585058d8b19f1c614e7695&v=4)](https://github.com/Hetens)

[Hetens](https://github.com/Hetens) [Jul 12, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10027447)

Same error

[![@Smone5](https://avatars.githubusercontent.com/u/19376953?u=39c7109f972629c692819a7ba1a1ff3c8c20ecb0&v=4)](https://github.com/Smone5)

[Smone5](https://github.com/Smone5) [Jul 30, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10194997)

edited

For me it seemed to be a timing error and LLM creativity error. With 4o, the agent was going a lot faster, but when I went to gpt-4-1106-preview, the agent went a lot slower. For a quick hack, I just added a time delay to the call\_tool edge:

from typing import Literal

import time

def router(state) -> Literal\["call\_tool", " **end**", "continue"\]:

messages = state\['messages'\]

last\_message = messages\[-1\]

if last\_message.tool\_calls:

time.sleep(10)

return "call\_tool"

if "FINAL ANSWER" in last\_message.content:

return " **end**"

return "continue"

I also had the issue mentioned above where the LLM was thinking there was tool called chart\_generator, so I made sure I loaded the LLM with temperature of 0:

llm = ChatOpenAI(model="gpt-4o", temperature=0)

Those seemed to help me. I think we need an intelligent tool that can figure out all these API call rate limit errors for these agents.

[![@Hetens](https://avatars.githubusercontent.com/u/92987462?u=2cbbc8b002e3a15a2f585058d8b19f1c614e7695&v=4)](https://github.com/Hetens)

[Hetens](https://github.com/Hetens) [Aug 5, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10242866)

Oh this is actually helpful let me try thanks a bunch

[![@Hetens](https://avatars.githubusercontent.com/u/92987462?u=2cbbc8b002e3a15a2f585058d8b19f1c614e7695&v=4)](https://github.com/Hetens)

[Hetens](https://github.com/Hetens) [Aug 5, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10242872)

I tried using the agent-executor and it works do you think agent executor delays it on purpose

[![@Changsoo-Park](https://avatars.githubusercontent.com/u/28660773?v=4)Changsoo-Park](https://github.com/Changsoo-Park) [Jul 22, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10117804)

I'm running into an error with this sample code and need some help figuring out how to fix it.

Here's the error message I'm getting:

'''

Traceback (most recent call last):

File "c:\\doug\_AI\\LangChain\\catchupLangChain\\LangGraph\_MultiAgentCollaboration.py", line 193, in

for s in events:

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langgraph\\pregel\_ _init_\_.py", line 1111, in stream

_panic\_or\_proceed(done, inflight, step)_

_File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langgraph\\pregel\_init_.py", line 1758, in \_panic\_or\_proceed

raise exc

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langgraph\\pregel\\executor.py", line 43, in done

task.result()

File "C:\\Program Files\\WindowsApps\\PythonSoftwareFoundation.Python.3.12\_3.12.1264.0\_x64\_\_qbz5n2kfra8p0\\Lib\\concurrent\\futures\_base.py", line 449, in result

return self.\_\_get\_result()

^^^^^^^^^^^^^^^^^^^

File "C:\\Program Files\\WindowsApps\\PythonSoftwareFoundation.Python.3.12\_3.12.1264.0\_x64\_\_qbz5n2kfra8p0\\Lib\\concurrent\\futures\_base.py", line 401, in \_\_get\_result

raise self.\_exception

File "C:\\Program Files\\WindowsApps\\PythonSoftwareFoundation.Python.3.12\_3.12.1264.0\_x64\_\_qbz5n2kfra8p0\\Lib\\concurrent\\futures\\thread.py", line 58, in run

result = self.fn(\*self.args, \*\*self.kwargs)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langgraph\\pregel\\retry.py", line 25, in run\_with\_retry

task.proc.invoke(task.input, task.config)

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langchain\_core\\runnables\\base.py", line 2871, in invoke

input = step.invoke(input, config, \*\*kwargs)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langgraph\\utils.py", line 102, in invoke

ret = context.run(self.func, input, \*\*kwargs)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "c:\\doug\_AI\\LangChain\\catchupLangChain\\LangGraph\_MultiAgentCollaboration.py", line 82, in agent\_node

result = agent.invoke(state)

^^^^^^^^^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langchain\_core\\runnables\\base.py", line 2873, in invoke

input = step.invoke(input, config)

^^^^^^^^^^^^^^^^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langchain\_core\\runnables\\base.py", line 5055, in invoke

return self.bound.invoke(

^^^^^^^^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langchain\_core\\language\_models\\chat\_models.py", line 265, in invoke

self.generate\_prompt(

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langchain\_core\\language\_models\\chat\_models.py", line 698, in generate\_prompt

return self.generate(prompt\_messages, stop=stop, callbacks=callbacks, \*\*kwargs)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langchain\_core\\language\_models\\chat\_models.py", line 555, in generate

raise e

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langchain\_core\\language\_models\\chat\_models.py", line 545, in generate

self.\_generate\_with\_cache(

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langchain\_core\\language\_models\\chat\_models.py", line 770, in \_generate\_with\_cache

result = self.\_generate(

^^^^^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\langchain\_openai\\chat\_models\\base.py", line 549, in \_generate

response = self.client.create(messages=message\_dicts, \*\*params)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\openai\_utils\_utils.py", line 277, in wrapper

return func(\*args, \*\*kwargs)

^^^^^^^^^^^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\openai\\resources\\chat\\completions.py", line 643, in create

return self.\_post(

^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\openai\_base\_client.py", line 1250, in post

return cast(ResponseT, self.request(cast\_to, opts, stream=stream, stream\_cls=stream\_cls))

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\openai\_base\_client.py", line 931, in request

return self.\_request(

^^^^^^^^^^^^^^

File "C:\\doug\_AI\\LangChain\\catchupLangChain\\dougVenv\\Lib\\site-packages\\openai\_base\_client.py", line 1030, in \_request

raise self.\_make\_status\_error\_from\_response(err.response) from None

openai.BadRequestError: Error code: 400 - {'error': {'message': "Missing required parameter: 'messages\[3\].content\[0\].type'.", 'type': 'invalid\_request\_error', 'param': 'messages\[3\].content\[0\].type', 'code': 'missing\_required\_parameter'}}

'''

3

2 replies

[![@arisylafeta](https://avatars.githubusercontent.com/u/58523898?u=ee5ef32bdab1a4f8876b8ff4f67fc4645b2b8ef2&v=4)](https://github.com/arisylafeta)

[arisylafeta](https://github.com/arisylafeta) [Aug 5, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10243871)

use a better LLM. The arguments in the tool call are wrong and therefore you're getting the error. The code is fine

[![@Hetens](https://avatars.githubusercontent.com/u/92987462?u=2cbbc8b002e3a15a2f585058d8b19f1c614e7695&v=4)](https://github.com/Hetens)

[Hetens](https://github.com/Hetens) [Sep 23, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10722208)

edited

Your llm might be passing parameters incorrectly so you can use an abstract syntax tree format in python to conform the parameters in the function. you can do this by using a dictionary with a fallback. Include in your prompt, "write it in dictionary format with the following keys."

````notranslate
    print("The input for the file reader tool is : ", inputs)
    try:
        dictionary = ast.literal_eval(inputs)
        file_path = dictionary['file_path']
        start_line = dictionary['start_line']
        end_line = dictionary['end_line']
        file_path = file_path.strip("'\"")
        full_path = os.path.join(os.getcwd(), 'TestRepositories', file_path)
        full_path = os.path.normpath(full_path)

        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as file:
                logging.info(f"Reading file: {full_path}")
                lines = file.readlines()
                snippet = "".join(lines[start_line-1:end_line])
                return snippet   # Truncate to 5000 characters
        return f"File not found: {full_path}"
    except Exception as e:
        return f"Error reading file: {e}"
        file_reader_tool = Tool(
    name="FileReader",
    func=read_file_contents,
    description="Reads the contents of a file given its 'file_path' ,'start_line' and 'end_line' line numbers in dictionary format"
)```




````

[![@hepbc](https://avatars.githubusercontent.com/u/11642637?v=4)hepbc](https://github.com/hepbc) [Aug 6, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10249549)

Hi folks: thanks for the tutorial. Here if I have a tool that gives the result as a pandas df (for e.g. dates and stock prices) and another that plots it (using matplotlib and not a REPL) then how do I "pass" the data (which is a df or lists) between the 2 tools?

Thanks for the help!

1

0 replies

[![@hepbc](https://avatars.githubusercontent.com/u/11642637?v=4)hepbc](https://github.com/hepbc) [Aug 6, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10250434)

Hi folks: thanks for the tutorial. I replaced the told above with the following - 1 that gives the dates and prices as a pandas df and another that plots it (using matplotlib and not a REPL). Will the data pass seamlessly between the 2?

```notranslate
def get_price_history(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
"""
Returns the historical price history of a given stock ticker from a start date to an end date with dates in the DD-MM-YYYY format as a pandas dataframe
"""
@tool
def plot_chart(x_axis: list, y_axis: list):
"""
plots a chart for a given list of x-axis value and y-axis values
"""
# Research agent and node
research_agent = create_agent(
    llm,
    [get_price_history],
    system_message="You should provide accurate data for the chart_generator to use.",
)
research_node = functools.partial(agent_node, agent=research_agent, name="Researcher")

# chart_generator
chart_agent = create_agent(
    llm,
    [plot_chart],
    system_message="Any charts you display will be visible by the user.",
)
chart_node = functools.partial(agent_node, agent=chart_agent, name="chart_generator")
tools = [get_price_history, plot_chart]
tool_node = ToolNode(tools)

events = graph.stream(
    {
        "messages": [\
            HumanMessage(\
                content="Fetch MSFT's price history for the past 1 year,"\
                " then draw a line graph of it."\
                " Once you code it up, finish."\
            )\
        ],
    },
    # Maximum number of steps to take in the graph
    {"recursion_limit": 150},
)
'''

```

Getting the following output. Is it a tool call issue or a data format (json vs pandas) issue?

Thanks for the help!

```notranslate
{'Researcher': {'messages': [AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_9lOuiHopP7fqn3cod5UwxxWm', 'function': {'arguments': '{"ticker":"MSFT","start_date":"23-04-2022","end_date":"23-04-2023"}', 'name': 'get_price_history'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 36, 'prompt_tokens': 220, 'total_tokens': 256}, 'model_name': 'gpt-4-1106-preview', 'system_fingerprint': None, 'finish_reason': 'tool_calls', 'logprobs': None}, name='Researcher', id='run-bd9a4c3f-b14f-486d-ba1c-1a6878d511f4-0', tool_calls=[{'name': 'get_price_history', 'args': {'ticker': 'MSFT', 'start_date': '23-04-2022', 'end_date': '23-04-2023'}, 'id': 'call_9lOuiHopP7fqn3cod5UwxxWm', 'type': 'tool_call'}], usage_metadata={'input_tokens': 220, 'output_tokens': 36, 'total_tokens': 256})], 'sender': 'Researcher'}}
----
[*********************100%%**********************]  1 of 1 completed
<class 'pandas.core.series.Series'>
DatetimeIndex: 250 entries, 2022-04-25 to 2023-04-21
Series name: Adj Close
Non-Null Count  Dtype
--------------  -----
250 non-null    float64
dtypes: float64(1)
memory usage: 3.9 KB
None
{'call_tool': {'messages': [ToolMessage(content='Date\n2022-04-25    275.233368\n2022-04-26    264.938599\n2022-04-27    277.684509\n2022-04-28    283.969208\n2022-04-29    272.095886\n                 ...    \n2023-04-17    285.933319\n2023-04-18    285.507507\n2023-04-19    285.586792\n2023-04-20    283.269989\n2023-04-21    282.923462\nName: Adj Close, Length: 250, dtype: float64', name='get_price_history', tool_call_id='call_9lOuiHopP7fqn3cod5UwxxWm')]}}
----
{'Researcher': {'messages': [AIMessage(content="Now that we have the price history for MSFT over the past year, we can proceed to draw a line graph. Here's the data that will be used to plot the graph:\n\n- X-axis: Dates from 25-04-2022 to 21-04-2023\n- Y-axis: Adjusted closing prices for MSFT\n\nThe line graph will show the trend in the stock price of MSFT over the past year.\n\nFinish.", response_metadata={'token_usage': {'completion_tokens': 93, 'prompt_tokens': 417, 'total_tokens': 510}, 'model_name': 'gpt-4-1106-preview', 'system_fingerprint': None, 'finish_reason': 'stop', 'logprobs': None}, name='Researcher', id='run-01ba4c4b-048e-4870-83d8-b5c51e20a59b-0', usage_metadata={'input_tokens': 417, 'output_tokens': 93, 'total_tokens': 510})], 'sender': 'Researcher'}}
----
{'chart_generator': {'messages': [AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_mxJEaVi0m9AORNwiCR2JXkpN', 'function': {'arguments': '{"x_axis":["2022-04-25","2022-04-26","2022-04-27","2022-04-28","2022-04-29","2022-04-30","2022-05-01","2022-05-02","2022-05-03","2022-05-04","2022-05-05","2022-05-06","2022-05-07","2022-05-08","2022-05-09","2022-05-10","2022-05-11","2022-05-12","2022-05-13","2022-05-14","2022-05-15","2022-05-16","2022-05-17","2022-05-18","2022-05-19","2022-05-20","2022-05-21","2022-05-22","2022-05-23","2022-05-24","2022-05-25","2022-05-26","2022-05-27","2022-05-28","2022-05-29","2022-05-30","2022-05-31","2022-06-01","2022-06-02","2022-06-03","2022-06-04","2022-06-05","2022-06-06","2022-06-07","2022-06-08","2022-06-09","2022-06-10","2022-06-11","2022-06-12","2022-06-13","2022-06-14","2022-06-15","2022-06-16","2022-06-17","2022-06-18","2022-06-19","2022-06-20","2022-06-21","2022-06-22","2022-06-23","2022-06-24","2022-06-25","2022-06-26","2022-06-27","2022-06-28","2022-06-29","2022-06-30","2022-07-01","2022-07-02","2022-07-03","2022-07-04","2022-07-05","2022-07-06","2022-07-07","2022-07-08","2022-07-09","2022-07-10","2022-07-11","2022-07-12","2022-07-13","2022-07-14","2022-07-15","2022-07-16","2022-07-17","2022-07-18","2022-07-19","2022-07-20","2022-07-21","2022-07-22","2022-07-23","2022-07-24","2022-07-25","2022-07-26","2022-07-27","2022-07-28","2022-07-29","2022-07-30","2022-07-31","2022-08-01","2022-08-02","2022-08-03","2022-08-04","2022-08-05","2022-08-06","2022-08-07","2022-08-08","2022-08-09","2022-08-10","2022-08-11","2022-08-12","2022-08-13","2022-08-14","2022-08-15","2022-08-16","2022-08-17","2022-08-18","2022-08-19","2022-08-20","2022-08-21","2022-08-22","2022-08-23","2022-08-24","2022-08-25","2022-08-26","2022-08-27","2022-08-28","2022-08-29","2022-08-30","2022-08-31","2022-09-01","2022-09-02","2022-09-03","2022-09-04","2022-09-05","2022-09-06","2022-09-07","2022-09-08","2022-09-09","2022-09-10","2022-09-11","2022-09-12","2022-09-13","2022-09-14","2022-09-15","2022-09-16","2022-09-17","2022-09-18","2022-09-19","2022-09-20","2022-09-21","2022-09-22","2022-09-23","2022-09-24","2022-09-25","2022-09-26","2022-09-27","2022-09-28","2022-09-29","2022-09-30","2022-10-01","2022-10-02","2022-10-03","2022-10-04","2022-10-05","2022-10-06","2022-10-07","2022-10-08","2022-10-09","2022-10-10","2022-10-11","2022-10-12","2022-10-13","2022-10-14","2022-10-15","2022-10-16","2022-10-17","2022-10-18","2022-10-19","2022-10-20","2022-10-21","2022-10-22","2022-10-23","2022-10-24","2022-10-25","2022-10-26","2022-10-27","2022-10-28","2022-10-29","2022-10-30","2022-10-31","2022-11-01","2022-11-02","2022-11-03","2022-11-04","2022-11-05","2022-11-06","2022-11-07","2022-11-08","2022-11-09","2022-11-10","2022-11-11","2022-11-12","2022-11-13","2022-11-14","2022-11-15","2022-11-16","2022-11-17","2022-11-18","2022-11-19","2022-11-20","2022-11-21","2022-11-22","2022-11-23","2022-11-24","2022-11-25","2022-11-26","2022-11-27","2022-11-28","2022-11-29","2022-11-30","2022-12-01","2022-12-02","2022-12-03","2022-12-04","2022-12-05","2022-12-06","2022-12-07","2022-12-08","2022-12-09","2022-12-10","2022-12-11","2022-12-12","2022-12-13","2022-12-14","2022-12-15","2022-12-16","2022-12-17","2022-12-18","2022-12-19","2022-12-20","2022-12-21","2022-12-22","2022-12-23","2022-12-24","2022-12-25","2022-12-26","2022-12-27","2022-12-28","2022-12-29","2022-12-30","2022-12-31","2023-01-01","2023-01-02","2023-01-03","2023-01-04","2023-01-05","2023-01-06","2023-01-07","2023-01-08","2023-01-09","2023-01-10","2023-01-11","2023-01-12","2023-01-13","2023-01-14","2023-01-15","2023-01-16","2023-01-17","2023-01-18","2023-01-19","2023-01-20","2023-01-21","2023-01-22","2023-01-23","2023-01-24","2023-01-25","2023-01-26","2023-01-27","2023-01-28","2023-01-29","2023-01-30","2023-01-31","2023-02-01","2023-02-02","2023-02-03","2023-02-04","2023-02-05","2023-02-06","2023-02-07","2023-02-08","2023-02-09","2023-02-10","2023-02-11","2023-02-12","2023-02-13","2023-02-14","2023-02-15","2023-02-16","2023-02-17","2023-02-18","2023-02-19","2023-02-20","2023-02-21","2023-02-22","2023-02-23","2023-02-24","2023-02-25","2023-02-26","2023-02-27","2023-02-28","2023-03-01","2023-03-02","2023-03-03","2023-03-04","2023-03-05","2023-03-06","2023-03-07","2023-03-08","2023-03-09","2023-03-10","2023-03-11","2023-03-12","2023-03-13","2023-03-14","2023-03-15","2023-03-16","2023-03-17","2023-03-18","2023-03-19","2023-03-20","2023-03-21","2023-03-22","2023-03-23","2023-03-24","2023-03-25","2023-03-26","2023-03-27","2023-03-28","2023-03-29","2023-03-30","2023-03-31","2023-04-01","2023-04-02","2023-04-03","2023-04-04","2023-04-05","2023-04-06","2023-04-07","2023-04-08","2023-04-09","2023-04-10","2023-04-11","2023-04-12","2023-04-13","2023-04-14","2023-04-15","2023-04-16","2023-04-17","2023-04-18","2023-04-19","2023-04-20","2023-04-21"],"y_axis":[275.233368,264.938599,277.684509,283.969208,272.095886,272.095886,272.095886,277.092285,275.263763,274.454529,268.959564,260.903076,260.903076,260.903076,260.903076,259.554199,253.579102,254.638718,252.421631,252.421631,252.421631,254.748566,249.863388,245.978226,243.211914,244.101593,244.101593,244.101593,244.101593,245.218918,238.893433,233.42865,232.619415,232.619415,232.619415,232.619415,232.619415,267.930267,267.930267,267.930267,267.930267,267.930267,267.930267,272.455841,271.536621,265.131561,265.131561,265.131561,265.131561,265.131561,261.242432,258.63559,260.243622,260.243622,260.243622,260.243622,260.243622,257.146851,254.42923,246.672821,246.672821,246.672821,246.672821,246.672821,246.672821,252.931702,256.070007,256.720001,256.720001,256.720001,256.720001,256.720001,256.720001,256.720001,253.289993,250.039993,251.899994,251.899994,251.899994,251.899994,251.899994,253.679993,255.350006,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25', 'name': 'plot_chart'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 4096, 'prompt_tokens': 494, 'total_tokens': 4590}, 'model_name': 'gpt-4-1106-preview', 'system_fingerprint': None, 'finish_reason': 'length', 'logprobs': None}, name='chart_generator', id='run-0a268614-b937-4756-9d22-47e0fa76d4c8-0', invalid_tool_calls=[{'name': 'plot_chart', 'args': '{"x_axis":["2022-04-25","2022-04-26","2022-04-27","2022-04-28","2022-04-29","2022-04-30","2022-05-01","2022-05-02","2022-05-03","2022-05-04","2022-05-05","2022-05-06","2022-05-07","2022-05-08","2022-05-09","2022-05-10","2022-05-11","2022-05-12","2022-05-13","2022-05-14","2022-05-15","2022-05-16","2022-05-17","2022-05-18","2022-05-19","2022-05-20","2022-05-21","2022-05-22","2022-05-23","2022-05-24","2022-05-25","2022-05-26","2022-05-27","2022-05-28","2022-05-29","2022-05-30","2022-05-31","2022-06-01","2022-06-02","2022-06-03","2022-06-04","2022-06-05","2022-06-06","2022-06-07","2022-06-08","2022-06-09","2022-06-10","2022-06-11","2022-06-12","2022-06-13","2022-06-14","2022-06-15","2022-06-16","2022-06-17","2022-06-18","2022-06-19","2022-06-20","2022-06-21","2022-06-22","2022-06-23","2022-06-24","2022-06-25","2022-06-26","2022-06-27","2022-06-28","2022-06-29","2022-06-30","2022-07-01","2022-07-02","2022-07-03","2022-07-04","2022-07-05","2022-07-06","2022-07-07","2022-07-08","2022-07-09","2022-07-10","2022-07-11","2022-07-12","2022-07-13","2022-07-14","2022-07-15","2022-07-16","2022-07-17","2022-07-18","2022-07-19","2022-07-20","2022-07-21","2022-07-22","2022-07-23","2022-07-24","2022-07-25","2022-07-26","2022-07-27","2022-07-28","2022-07-29","2022-07-30","2022-07-31","2022-08-01","2022-08-02","2022-08-03","2022-08-04","2022-08-05","2022-08-06","2022-08-07","2022-08-08","2022-08-09","2022-08-10","2022-08-11","2022-08-12","2022-08-13","2022-08-14","2022-08-15","2022-08-16","2022-08-17","2022-08-18","2022-08-19","2022-08-20","2022-08-21","2022-08-22","2022-08-23","2022-08-24","2022-08-25","2022-08-26","2022-08-27","2022-08-28","2022-08-29","2022-08-30","2022-08-31","2022-09-01","2022-09-02","2022-09-03","2022-09-04","2022-09-05","2022-09-06","2022-09-07","2022-09-08","2022-09-09","2022-09-10","2022-09-11","2022-09-12","2022-09-13","2022-09-14","2022-09-15","2022-09-16","2022-09-17","2022-09-18","2022-09-19","2022-09-20","2022-09-21","2022-09-22","2022-09-23","2022-09-24","2022-09-25","2022-09-26","2022-09-27","2022-09-28","2022-09-29","2022-09-30","2022-10-01","2022-10-02","2022-10-03","2022-10-04","2022-10-05","2022-10-06","2022-10-07","2022-10-08","2022-10-09","2022-10-10","2022-10-11","2022-10-12","2022-10-13","2022-10-14","2022-10-15","2022-10-16","2022-10-17","2022-10-18","2022-10-19","2022-10-20","2022-10-21","2022-10-22","2022-10-23","2022-10-24","2022-10-25","2022-10-26","2022-10-27","2022-10-28","2022-10-29","2022-10-30","2022-10-31","2022-11-01","2022-11-02","2022-11-03","2022-11-04","2022-11-05","2022-11-06","2022-11-07","2022-11-08","2022-11-09","2022-11-10","2022-11-11","2022-11-12","2022-11-13","2022-11-14","2022-11-15","2022-11-16","2022-11-17","2022-11-18","2022-11-19","2022-11-20","2022-11-21","2022-11-22","2022-11-23","2022-11-24","2022-11-25","2022-11-26","2022-11-27","2022-11-28","2022-11-29","2022-11-30","2022-12-01","2022-12-02","2022-12-03","2022-12-04","2022-12-05","2022-12-06","2022-12-07","2022-12-08","2022-12-09","2022-12-10","2022-12-11","2022-12-12","2022-12-13","2022-12-14","2022-12-15","2022-12-16","2022-12-17","2022-12-18","2022-12-19","2022-12-20","2022-12-21","2022-12-22","2022-12-23","2022-12-24","2022-12-25","2022-12-26","2022-12-27","2022-12-28","2022-12-29","2022-12-30","2022-12-31","2023-01-01","2023-01-02","2023-01-03","2023-01-04","2023-01-05","2023-01-06","2023-01-07","2023-01-08","2023-01-09","2023-01-10","2023-01-11","2023-01-12","2023-01-13","2023-01-14","2023-01-15","2023-01-16","2023-01-17","2023-01-18","2023-01-19","2023-01-20","2023-01-21","2023-01-22","2023-01-23","2023-01-24","2023-01-25","2023-01-26","2023-01-27","2023-01-28","2023-01-29","2023-01-30","2023-01-31","2023-02-01","2023-02-02","2023-02-03","2023-02-04","2023-02-05","2023-02-06","2023-02-07","2023-02-08","2023-02-09","2023-02-10","2023-02-11","2023-02-12","2023-02-13","2023-02-14","2023-02-15","2023-02-16","2023-02-17","2023-02-18","2023-02-19","2023-02-20","2023-02-21","2023-02-22","2023-02-23","2023-02-24","2023-02-25","2023-02-26","2023-02-27","2023-02-28","2023-03-01","2023-03-02","2023-03-03","2023-03-04","2023-03-05","2023-03-06","2023-03-07","2023-03-08","2023-03-09","2023-03-10","2023-03-11","2023-03-12","2023-03-13","2023-03-14","2023-03-15","2023-03-16","2023-03-17","2023-03-18","2023-03-19","2023-03-20","2023-03-21","2023-03-22","2023-03-23","2023-03-24","2023-03-25","2023-03-26","2023-03-27","2023-03-28","2023-03-29","2023-03-30","2023-03-31","2023-04-01","2023-04-02","2023-04-03","2023-04-04","2023-04-05","2023-04-06","2023-04-07","2023-04-08","2023-04-09","2023-04-10","2023-04-11","2023-04-12","2023-04-13","2023-04-14","2023-04-15","2023-04-16","2023-04-17","2023-04-18","2023-04-19","2023-04-20","2023-04-21"],"y_axis":[275.233368,264.938599,277.684509,283.969208,272.095886,272.095886,272.095886,277.092285,275.263763,274.454529,268.959564,260.903076,260.903076,260.903076,260.903076,259.554199,253.579102,254.638718,252.421631,252.421631,252.421631,254.748566,249.863388,245.978226,243.211914,244.101593,244.101593,244.101593,244.101593,245.218918,238.893433,233.42865,232.619415,232.619415,232.619415,232.619415,232.619415,267.930267,267.930267,267.930267,267.930267,267.930267,267.930267,272.455841,271.536621,265.131561,265.131561,265.131561,265.131561,265.131561,261.242432,258.63559,260.243622,260.243622,260.243622,260.243622,260.243622,257.146851,254.42923,246.672821,246.672821,246.672821,246.672821,246.672821,246.672821,252.931702,256.070007,256.720001,256.720001,256.720001,256.720001,256.720001,256.720001,256.720001,253.289993,250.039993,251.899994,251.899994,251.899994,251.899994,251.899994,253.679993,255.350006,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25', 'id': 'call_mxJEaVi0m9AORNwiCR2JXkpN', 'error': 'Function plot_chart arguments:\n\n{"x_axis":["2022-04-25","2022-04-26","2022-04-27","2022-04-28","2022-04-29","2022-04-30","2022-05-01","2022-05-02","2022-05-03","2022-05-04","2022-05-05","2022-05-06","2022-05-07","2022-05-08","2022-05-09","2022-05-10","2022-05-11","2022-05-12","2022-05-13","2022-05-14","2022-05-15","2022-05-16","2022-05-17","2022-05-18","2022-05-19","2022-05-20","2022-05-21","2022-05-22","2022-05-23","2022-05-24","2022-05-25","2022-05-26","2022-05-27","2022-05-28","2022-05-29","2022-05-30","2022-05-31","2022-06-01","2022-06-02","2022-06-03","2022-06-04","2022-06-05","2022-06-06","2022-06-07","2022-06-08","2022-06-09","2022-06-10","2022-06-11","2022-06-12","2022-06-13","2022-06-14","2022-06-15","2022-06-16","2022-06-17","2022-06-18","2022-06-19","2022-06-20","2022-06-21","2022-06-22","2022-06-23","2022-06-24","2022-06-25","2022-06-26","2022-06-27","2022-06-28","2022-06-29","2022-06-30","2022-07-01","2022-07-02","2022-07-03","2022-07-04","2022-07-05","2022-07-06","2022-07-07","2022-07-08","2022-07-09","2022-07-10","2022-07-11","2022-07-12","2022-07-13","2022-07-14","2022-07-15","2022-07-16","2022-07-17","2022-07-18","2022-07-19","2022-07-20","2022-07-21","2022-07-22","2022-07-23","2022-07-24","2022-07-25","2022-07-26","2022-07-27","2022-07-28","2022-07-29","2022-07-30","2022-07-31","2022-08-01","2022-08-02","2022-08-03","2022-08-04","2022-08-05","2022-08-06","2022-08-07","2022-08-08","2022-08-09","2022-08-10","2022-08-11","2022-08-12","2022-08-13","2022-08-14","2022-08-15","2022-08-16","2022-08-17","2022-08-18","2022-08-19","2022-08-20","2022-08-21","2022-08-22","2022-08-23","2022-08-24","2022-08-25","2022-08-26","2022-08-27","2022-08-28","2022-08-29","2022-08-30","2022-08-31","2022-09-01","2022-09-02","2022-09-03","2022-09-04","2022-09-05","2022-09-06","2022-09-07","2022-09-08","2022-09-09","2022-09-10","2022-09-11","2022-09-12","2022-09-13","2022-09-14","2022-09-15","2022-09-16","2022-09-17","2022-09-18","2022-09-19","2022-09-20","2022-09-21","2022-09-22","2022-09-23","2022-09-24","2022-09-25","2022-09-26","2022-09-27","2022-09-28","2022-09-29","2022-09-30","2022-10-01","2022-10-02","2022-10-03","2022-10-04","2022-10-05","2022-10-06","2022-10-07","2022-10-08","2022-10-09","2022-10-10","2022-10-11","2022-10-12","2022-10-13","2022-10-14","2022-10-15","2022-10-16","2022-10-17","2022-10-18","2022-10-19","2022-10-20","2022-10-21","2022-10-22","2022-10-23","2022-10-24","2022-10-25","2022-10-26","2022-10-27","2022-10-28","2022-10-29","2022-10-30","2022-10-31","2022-11-01","2022-11-02","2022-11-03","2022-11-04","2022-11-05","2022-11-06","2022-11-07","2022-11-08","2022-11-09","2022-11-10","2022-11-11","2022-11-12","2022-11-13","2022-11-14","2022-11-15","2022-11-16","2022-11-17","2022-11-18","2022-11-19","2022-11-20","2022-11-21","2022-11-22","2022-11-23","2022-11-24","2022-11-25","2022-11-26","2022-11-27","2022-11-28","2022-11-29","2022-11-30","2022-12-01","2022-12-02","2022-12-03","2022-12-04","2022-12-05","2022-12-06","2022-12-07","2022-12-08","2022-12-09","2022-12-10","2022-12-11","2022-12-12","2022-12-13","2022-12-14","2022-12-15","2022-12-16","2022-12-17","2022-12-18","2022-12-19","2022-12-20","2022-12-21","2022-12-22","2022-12-23","2022-12-24","2022-12-25","2022-12-26","2022-12-27","2022-12-28","2022-12-29","2022-12-30","2022-12-31","2023-01-01","2023-01-02","2023-01-03","2023-01-04","2023-01-05","2023-01-06","2023-01-07","2023-01-08","2023-01-09","2023-01-10","2023-01-11","2023-01-12","2023-01-13","2023-01-14","2023-01-15","2023-01-16","2023-01-17","2023-01-18","2023-01-19","2023-01-20","2023-01-21","2023-01-22","2023-01-23","2023-01-24","2023-01-25","2023-01-26","2023-01-27","2023-01-28","2023-01-29","2023-01-30","2023-01-31","2023-02-01","2023-02-02","2023-02-03","2023-02-04","2023-02-05","2023-02-06","2023-02-07","2023-02-08","2023-02-09","2023-02-10","2023-02-11","2023-02-12","2023-02-13","2023-02-14","2023-02-15","2023-02-16","2023-02-17","2023-02-18","2023-02-19","2023-02-20","2023-02-21","2023-02-22","2023-02-23","2023-02-24","2023-02-25","2023-02-26","2023-02-27","2023-02-28","2023-03-01","2023-03-02","2023-03-03","2023-03-04","2023-03-05","2023-03-06","2023-03-07","2023-03-08","2023-03-09","2023-03-10","2023-03-11","2023-03-12","2023-03-13","2023-03-14","2023-03-15","2023-03-16","2023-03-17","2023-03-18","2023-03-19","2023-03-20","2023-03-21","2023-03-22","2023-03-23","2023-03-24","2023-03-25","2023-03-26","2023-03-27","2023-03-28","2023-03-29","2023-03-30","2023-03-31","2023-04-01","2023-04-02","2023-04-03","2023-04-04","2023-04-05","2023-04-06","2023-04-07","2023-04-08","2023-04-09","2023-04-10","2023-04-11","2023-04-12","2023-04-13","2023-04-14","2023-04-15","2023-04-16","2023-04-17","2023-04-18","2023-04-19","2023-04-20","2023-04-21"],"y_axis":[275.233368,264.938599,277.684509,283.969208,272.095886,272.095886,272.095886,277.092285,275.263763,274.454529,268.959564,260.903076,260.903076,260.903076,260.903076,259.554199,253.579102,254.638718,252.421631,252.421631,252.421631,254.748566,249.863388,245.978226,243.211914,244.101593,244.101593,244.101593,244.101593,245.218918,238.893433,233.42865,232.619415,232.619415,232.619415,232.619415,232.619415,267.930267,267.930267,267.930267,267.930267,267.930267,267.930267,272.455841,271.536621,265.131561,265.131561,265.131561,265.131561,265.131561,261.242432,258.63559,260.243622,260.243622,260.243622,260.243622,260.243622,257.146851,254.42923,246.672821,246.672821,246.672821,246.672821,246.672821,246.672821,252.931702,256.070007,256.720001,256.720001,256.720001,256.720001,256.720001,256.720001,256.720001,253.289993,250.039993,251.899994,251.899994,251.899994,251.899994,251.899994,253.679993,255.350006,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25,253.25\n\nare not valid JSON. Received JSONDecodeError Expecting \',\' delimiter: line 1 column 7619 (char 7618)', 'type': 'invalid_tool_call'}], usage_metadata={'input_tokens': 494, 'output_tokens': 4096, 'total_tokens': 4590})], 'sender': 'chart_generator'}}\
----\
---------------------------------------------------------------------------\
BadRequestError                           Traceback (most recent call last)\
<ipython-input-15-8a862aa8c956> in <cell line: 14>()\
     12     {"recursion_limit": 150},\
     13 )\
---> 14 for s in events:\
     15     print(s)\
     16     print("----")\
\
22 frames\
/usr/local/lib/python3.10/dist-packages/openai/_base_client.py in _request(self, cast_to, options, remaining_retries, stream, stream_cls)\
1044\
1045             log.debug("Re-raising status error")\
-> 1046             raise self._make_status_error_from_response(err.response) from None\
1047\
1048         return self._process_response(\
\
BadRequestError: Error code: 400 - {'error': {'message': "An assistant message with 'tool_calls' must be followed by tool messages responding to each 'tool_call_id'. The following tool_call_ids did not have response messages: call_mxJEaVi0m9AORNwiCR2JXkpN", 'type': 'invalid_request_error', 'param': 'messages', 'code': None}}\
'\
\
```\
\
1\
\
1 reply\
\
[![@hepbc](https://avatars.githubusercontent.com/u/11642637?v=4)](https://github.com/hepbc)\
\
[hepbc](https://github.com/hepbc) [Aug 6, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10250570)\
\
Taking out the data from the errors messages to give a clearer picture:\
\
```notranslate\
<class 'pandas.core.series.Series'>\
DatetimeIndex: 250 entries, 2022-04-25 to 2023-04-21\
Series name: Adj Close\
Non-Null Count  Dtype\
--------------  -----\
250 non-null    float64\
dtypes: float64(1)\
memory usage: 3.9 KB\
None\
{'call_tool': {'messages': [ToolMessage(content='Date\n2022-04-25    275.233368\n2022-04-26    264.938599\n2022-04-27    277.684509\n2022-04-28    283.969208\n2022-04-29    272.095886\n                 ...    \n2023-04-17    285.933319\n2023-04-18    285.507507\n2023-04-19    285.586792\n2023-04-20    283.269989\n2023-04-21    282.923462\nName: Adj Close, Length: 250, dtype: float64', name='get_price_history', tool_call_id='call_9lOuiHopP7fqn3cod5UwxxWm')]}}\
----\
{'Researcher': {'messages': [AIMessage(content="Now that we have the price history for MSFT over the past year, we can proceed to draw a line graph. Here's the data that will be used to plot the graph:\n\n- X-axis: Dates from 25-04-2022 to 21-04-2023\n- Y-axis: Adjusted closing prices for MSFT\n\nThe line graph will show the trend in the stock price of MSFT over the past year.\n\nFinish.", response_metadata={'token_usage': {'completion_tokens': 93, 'prompt_tokens': 417, 'total_tokens': 510}, 'model_name': 'gpt-4-1106-preview', 'system_fingerprint': None, 'finish_reason': 'stop', 'logprobs': None}, name='Researcher', id='run-01ba4c4b-048e-4870-83d8-b5c51e20a59b-0', usage_metadata={'input_tokens': 417, 'output_tokens': 93, 'total_tokens': 510})], 'sender': 'Researcher'}}\
----\
{'chart_generator': {'messages': [AIMessage(content='', additional_kwargs={'tool_calls': [{'id':\
'call_mxJEaVi0m9AORNwiCR2JXkpN', 'function': {'arguments': '{"x_axis":[DATA], "y_axis":[DATA], 'name':\
'plot_chart'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 4096,\
'prompt_tokens': 494, 'total_tokens': 4590}, 'model_name': 'gpt-4-1106-preview', 'system_fingerprint':\
None, 'finish_reason': 'length', 'logprobs': None}, name='chart_generator', id='run-0a268614-b937\
-4756-9d22-47e0fa76d4c8-0', invalid_tool_calls=[{'name': 'plot_chart', 'args': '{"x_axis":[DATA], "y_axis":\
[DATA], 'id': 'call_mxJEaVi0m9AORNwiCR2JXkpN', 'error': 'Function plot_chart arguments:\n\n{"x_axis":\
[DATA], "y_axis":[DATA]\n\nare not valid JSON. Received JSONDecodeError Expecting \',\' delimiter: line\
1 column 7619 (char 7618)', 'type': 'invalid_tool_call'}], usage_metadata={'input_tokens': 494,\
'output_tokens': 4096, 'total_tokens': 4590})], 'sender': 'chart_generator'}}\
----\
---------------------------------------------------------------------------\
BadRequestError                           Traceback (most recent call last)\
<ipython-input-15-8a862aa8c956> in <cell line: 14>()\
     12     {"recursion_limit": 150},\
     13 )\
---> 14 for s in events:\
     15     print(s)\
     16     print("----")\
\
________________________________________\
22 frames\
________________________________________\
/usr/local/lib/python3.10/dist-packages/openai/_base_client.py in _request(self, cast_to, options, remaining_retries, stream, stream_cls)\
1044\
1045             log.debug("Re-raising status error")\
-> 1046             raise self._make_status_error_from_response(err.response) from None\
1047\
1048         return self._process_response(\
\
BadRequestError: Error code: 400 - {'error': {'message': "An assistant message with 'tool_calls' must be followed by tool messages responding to each 'tool_call_id'. The following tool_call_ids did not have response messages: call_mxJEaVi0m9AORNwiCR2JXkpN", 'type': 'invalid_request_error', 'param': 'messages', 'code': None}}\
\
```\
\
```notranslate\
\
```\
\
[![@Player256](https://avatars.githubusercontent.com/u/92082372?u=106a417c2a38b518715902fb332119179527276c&v=4)Player256](https://github.com/Player256) [Aug 7, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10269255)\
\
Hey guys I've been getting this error `ValueError: Error raised by bedrock service: An error occurred (ValidationException) when calling the InvokeModel operation: Your API request included an ` assistant `message in the final position, which would pre-fill the` assistant `response. When using tools, pre-filling the` assistant ` response is not supported.`.\
\
I am using ChatBedrock's claude-3-sonnet. Any help would be great.\
\
1\
\
2 replies\
\
[![@Player256](https://avatars.githubusercontent.com/u/92082372?u=106a417c2a38b518715902fb332119179527276c&v=4)](https://github.com/Player256)\
\
[Player256](https://github.com/Player256) [Aug 7, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10269256)\
\
Used the same code\
\
[![@carrickcheah](https://avatars.githubusercontent.com/u/138642124?u=055c9fea496d8d880b91a1f49f4ad3431cbf7409&v=4)](https://github.com/carrickcheah)\
\
[carrickcheah](https://github.com/carrickcheah) [Aug 15, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10343287)\
\
use openai gpt4. Dont waste time on other LLM. why u wan to drive toyota, when u can drive Lamborghini.\
\
[![@yadgire7](https://avatars.githubusercontent.com/u/47882001?u=4c14b35f94a49ec92a7309653c8cff68c2713df0&v=4)yadgire7](https://github.com/yadgire7) [Aug 19, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10388053)\
\
Can we use LlamaCpp models to create an agent?\
\
1\
\
0 replies\
\
[![@G3ndek](https://avatars.githubusercontent.com/u/158774073?u=d446259d9e1af508ad8d057012ffe20108a2e382&v=4)G3ndek](https://github.com/G3ndek) [Sep 4, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10543705)\
\
Hey I have a question about state. So we have messages and sender which is fine. Although if we have so many iterations and messages are stacking. So let's say after 14 iterations we have a messages that contains 14 elements. This is a dangerous scenerio in 2 cases.\
\
1. We can have a token limit if model is generating response based on all of the messages.\
2. High risk of hallucinations in input like this.\
\
Does state take care of it or we do have to control it in some sense ?\
\
1\
\
0 replies\
\
[![@bhumikaZysk](https://avatars.githubusercontent.com/u/179929104?v=4)bhumikaZysk](https://github.com/bhumikaZysk) [Sep 12, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10625105)\
\
Everything except the AI message content is displayed.\
\
Only content is missing (content=' ')\
\
How to resolve this issue?\
\
1\
\
0 replies\
\
[![@TaisukeIto](https://avatars.githubusercontent.com/u/56746159?v=4)TaisukeIto](https://github.com/TaisukeIto) [Sep 14, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10646853)\
\
In LangGraph, the string &npsb (which means space) is attached to the edge string, making it difficult to read.\
\
How to resolve this issue?\
\
1\
\
2 replies\
\
[![@TaisukeIto](https://avatars.githubusercontent.com/u/56746159?v=4)](https://github.com/TaisukeIto)\
\
[TaisukeIto](https://github.com/TaisukeIto) [Sep 14, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10646978)\
\
If you run the following program in jupyterlab, the graph will be displayed nicely.\
\
from IPython.display import Image, display\
\
display(Image(graph.get\_graph(xray=True).draw\_mermaid\_png()))\
\
If you convert it to a python script,\
\
from PIL import Image as PilImage\
\
import matplotlib.pyplot as plt\
\
mermaid = graph.get\_graph(xray=False).draw\_mermaid\_png()\
\
with open('graph.png', 'wb') as f:\
\
f.write(mermaid)\
\
When you do this, the string &nbsp is attached to the edge, making it difficult to see.\
\
Do you know what to do?\
\
[![@TaisukeIto](https://avatars.githubusercontent.com/u/56746159?v=4)](https://github.com/TaisukeIto)\
\
[TaisukeIto](https://github.com/TaisukeIto) [Sep 14, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10647613)\
\
I removed the &nbsp string in graph\_mermaid.py.　（Solved.）\
\
.venv/lib/python3.12/site-packages/langchain\_core/runnables/graph\_mermaid.py\
\
edge\_data = "&nbsp\
\
&nbsp".join(" ".join(words\[i : i + wrap\_label\_n\_words\]) for i in range(0, len(words), wrap\_label\_n\_words))\
\
↓\
\
edge\_data = "\
\
".join(" ".join(words\[i : i + wrap\_label\_n\_words\]) for i in range(0, len(words), wrap\_label\_n\_words))\
\
[![@jason571](https://avatars.githubusercontent.com/u/22809213?u=502f53cda238b9dab373225952300013af9603b7&v=4)jason571](https://github.com/jason571) [Sep 19, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10692913)\
\
```notranslate\
    research_agent = self.create_agent(\
        llm,\
        [tavily_tool],\
        system_message="You should provide accurate data for the chart_generator to use. and source code shouldn't be the final answer"\
    )\
    self.research_agent_node = functools.partial(self.agent_node, agent=research_agent, name="Researcher")\
\
```\
\
File "/home/flyang/anaconda3/envs/LLMs/lib/python3.11/site-packages/openai/\_base\_client.py", line 1040, in \_request\
\
raise self.\_make\_status\_error\_from\_response(err.response) from None\
\
openai.BadRequestError: Error code: 400 - {'object': 'error', 'message': '"auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set', 'type': 'BadRequestError', 'param': None, 'code': 400}\
\
```notranslate\
def agent_node(self, state, agent, name):\
    mylogging.info(f"Invoking {name} agent with input: {state}, {agent}")\
    result = agent.invoke(state)\
    mylogging.info(f"Agent '{name}' invoked. Result type: {type(result)}")\
    # If result is a ToolMessage, set the sender to 'call_tool'\
    # We convert the agent output into a format that is suitable to append to the global state\
    if isinstance(result, ToolMessage):\
        mylogging.vip(f"ToolMessage: {result}")\
        return {\
            "messages": [result],\
            "sender": "call_tool",\
        }\
    else:\
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)\
        return {\
            "messages": [result],\
            "sender": name,\
        }\
\
```\
\
3\
\
0 replies\
\
[![@HilalSoorty](https://avatars.githubusercontent.com/u/140046101?u=a2fdbfd4ddffe6407a03c236084683b07ea0eef3&v=4)HilalSoorty](https://github.com/HilalSoorty) [Oct 12, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10922340)\
\
Can I run this with Gemini 1.5 flash or Ollama?\
\
1\
\
2 replies\
\
[![@Hetens](https://avatars.githubusercontent.com/u/92987462?u=2cbbc8b002e3a15a2f585058d8b19f1c614e7695&v=4)](https://github.com/Hetens)\
\
[Hetens](https://github.com/Hetens) [Oct 13, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10927613)\
\
yupp\
\
[![@Fancyfoot](https://avatars.githubusercontent.com/u/34892276?u=81f9c08d1b8dc7a11d2a8c189460ff0b7a323a2d&v=4)](https://github.com/Fancyfoot)\
\
[Fancyfoot](https://github.com/Fancyfoot) [Oct 13, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10930824)\
\
Yes of course !\
\
[![@gz927cool](https://avatars.githubusercontent.com/u/26042185?u=e9693f257f5b907aead0bf30489be403a27a5d69&v=4)gz927cool](https://github.com/gz927cool) [Oct 17, 2024](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-10965950)\
\
Thanks for the tutorial; however, why is there an additional incomplete image here?\
\
1\
\
0 replies\
\
[![@vvasylkovskyi](https://avatars.githubusercontent.com/u/25831789?u=fbb61237656e5d2e8aedefa6245e83ce77574097&v=4)vvasylkovskyi](https://github.com/vvasylkovskyi) [Jan 3](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-11725959)\
\
Arent the edges from researcher to charter missing?\
\
1\
\
1 reply\
\
[![@Sasha-BabyBird](https://avatars.githubusercontent.com/u/44008518?u=bc80888d239226352a3d2815b216776d04dc0d58&v=4)](https://github.com/Sasha-BabyBird)\
\
[Sasha-BabyBird](https://github.com/Sasha-BabyBird) [Jan 8](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-11779885)\
\
There is `get_next_node` function which is called from each of the nodes to change to another one.\
\
[![@balu72](https://avatars.githubusercontent.com/u/12568392?u=95e7f0ff80dc7277c471d224ba7803c7ed0975a7&v=4)balu72](https://github.com/balu72) [Jan 19](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-11882670)\
\
I am trying to set up a two agent system with one as hiring manager & other as HRBP negotiating to finalise a JD for hiring. When both agents approve the JD, the JD goes for hiring.\
\
1. Messaged between Hiring manager & HRBP are different on each direction. Can I create two AgentStates and pass to each other?\
2. Can I add more than one str\[\] in an agent?\
\
1\
\
0 replies\
\
[![@kagaho](https://avatars.githubusercontent.com/u/19654630?u=e85c53afeecf0688b72f5b030bb4c30c2508c9ca&v=4)kagaho](https://github.com/kagaho) [Mar 11](https://github.com/langchain-ai/langgraph/discussions/511#discussioncomment-12467325)\
\
Thanks for the awesome tutorial!\
\
Work pretty well with local 14B qwen2.5-coder-tools (the local LLM needs to support tooling). Fun fact the graph is generated inverse, which means the X axis graph starts with 2023, 2022, 2021... 2019 :-)\
\
1\
\
0 replies\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Fmulti_agent%2Fmulti-agent-collaboration%2F)