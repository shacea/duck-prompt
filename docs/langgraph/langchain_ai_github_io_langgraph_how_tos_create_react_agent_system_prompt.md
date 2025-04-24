[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-system-prompt/#how-to-add-a-custom-system-prompt-to-the-prebuilt-react-agent)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/create-react-agent-system-prompt.ipynb "Edit this page")

# How to add a custom system prompt to the prebuilt ReAct agent [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-system-prompt/\#how-to-add-a-custom-system-prompt-to-the-prebuilt-react-agent "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [SystemMessage](https://python.langchain.com/docs/concepts/messages/#systemmessage)
- [Agent Architectures](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/)
- [Chat Models](https://python.langchain.com/docs/concepts/chat_models/)
- [Tools](https://python.langchain.com/docs/concepts/tools/)

This tutorial will show how to add a custom system prompt to the [prebuilt ReAct agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent). Please see [this tutorial](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent) for how to get started with the prebuilt ReAct agent

You can add a custom system prompt by passing a string to the `prompt` param.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-system-prompt/\#setup "Permanent link")

First, let's install the required packages and set our API keys

```md-code__content
%%capture --no-stderr
%pip install -U langgraph langchain-openai

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


## Code [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-system-prompt/\#code "Permanent link")

API Reference: [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

```md-code__content
# First we initialize the model we want to use.
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o", temperature=0)

# For this tutorial we will use custom tool that returns pre-defined values for weather in two cities (NYC & SF)

from typing import Literal

from langchain_core.tools import tool

@tool
def get_weather(city: Literal["nyc", "sf"]):
    """Use this to get weather information."""
    if city == "nyc":
        return "It might be cloudy in nyc"
    elif city == "sf":
        return "It's always sunny in sf"
    else:
        raise AssertionError("Unknown city")

tools = [get_weather]

# We can add our system prompt here

prompt = "Respond in Italian"

# Define the graph

from langgraph.prebuilt import create_react_agent

graph = create_react_agent(model, tools=tools, prompt=prompt)

```

## Usage [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-system-prompt/\#usage "Permanent link")

```md-code__content
def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

```

```md-code__content
inputs = {"messages": [("user", "What's the weather in NYC?")]}

print_stream(graph.stream(inputs, stream_mode="values"))

```

```md-code__content
================================[1m Human Message [0m=================================\
\
What's the weather in NYC?\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  get_weather (call_b02uzBRrIm2uciJa8zDXCDxT)\
 Call ID: call_b02uzBRrIm2uciJa8zDXCDxT\
  Args:\
    city: nyc\
=================================[1m Tool Message [0m=================================\
Name: get_weather\
\
It might be cloudy in nyc\
==================================[1m Ai Message [0m==================================\
\
A New York potrebbe essere nuvoloso.\
\
```\
\
## Comments\
\
giscus\
\
#### [2 reactions](https://github.com/langchain-ai/langgraph/discussions/1060)\
\
👍2\
\
#### [13 comments](https://github.com/langchain-ai/langgraph/discussions/1060)\
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
[![@Rohianon](https://avatars.githubusercontent.com/u/41194018?u=8c81461d1acb685b9fa82a5f755ea3979ac15fec&v=4)Rohianon](https://github.com/Rohianon) [Jul 18, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-10087392)\
\
Is there a way a system prompt can be added to a self-discover model?\
\
Also, how does one integrate the human-in-the-loop in self-discover so that the model allows self updates.\
\
1\
\
0 replies\
\
[![@SH781-a](https://avatars.githubusercontent.com/u/152229783?v=4)SH781-a](https://github.com/SH781-a) [Jul 25, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-10152889)\
\
edited\
\
Caught me out\
\
the state\_modifier was removed see below:\
\
@deprecated\_parameter("messages\_modifier", "0.1.9", "state\_modifier", removal="0.2.0")\
\
def create\_react\_agent(\
\
model: LanguageModelLike,\
\
tools: Union\[ToolExecutor, Sequence\[BaseTool\]\],\
\
\*,\
\
state\_schema: Optional\[StateSchemaType\] = None,\
\
messages\_modifier: Optional\[MessagesModifier\] = None,\
\
state\_modifier: Optional\[StateModifier\] = None,\
\
checkpointer: Optional\[BaseCheckpointSaver\] = None,\
\
interrupt\_before: Optional\[Sequence\[str\]\] = None,\
\
interrupt\_after: Optional\[Sequence\[str\]\] = None,\
\
debug: bool = False,\
\
```notranslate\
so check your versoin\
\
```\
\
1\
\
2 replies\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Jul 25, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-10152982)\
\
Collaborator\
\
[@SH781-a](https://github.com/SH781-a) no, the documentation is correct, you're misreading the deprecation message. `messages_modifier` is the parameter that will be deprecated, `state_modifier` is the one that should be used\
\
[![@SH781-a](https://avatars.githubusercontent.com/u/152229783?v=4)](https://github.com/SH781-a)\
\
[SH781-a](https://github.com/SH781-a) [Jul 25, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-10152988)\
\
you are correct I was changing as I got your comment, apologies\
\
🎉2\
\
[![@duob-ai](https://avatars.githubusercontent.com/u/141818514?v=4)duob-ai](https://github.com/duob-ai) [Aug 4, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-10234808)\
\
I try to use this react agent in a FastAPI server where I create an endpoint with langserve.\
\
Problem is data validation. Currently deploying the endpoint with:\
\
add\_routes(app, agent, path="/agent", input\_type=Any)\
\
Is there any documentation on what the data model has to look like for LangGraph if you want to do input validation?\
\
1\
\
0 replies\
\
[![@EthanChen39](https://avatars.githubusercontent.com/u/47092704?u=7e3ff9838c49f7ef5a6a0ff1af3beeb4dfa8b4eb&v=4)EthanChen39](https://github.com/EthanChen39) [Aug 8, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-10279021)\
\
Is there a way to integrate ReAct agent with StateGraph?\
\
2\
\
0 replies\
\
[![@nick-youngblut](https://avatars.githubusercontent.com/u/2468572?u=257f896c1ce6dca97e0a7d840725cbc023a71839&v=4)nick-youngblut](https://github.com/nick-youngblut) [Aug 10, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-10300468)\
\
Why no use of `langchain.agents.AgentExecutor` for `create_react_agent`, even though `langchain.agents.AgentExecutor` is used for other agents, such as `langchain.agents.create_openai_tools_agent`?\
\
1\
\
1 reply\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Aug 12, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-10314913)\
\
Collaborator\
\
we do not recommend using langchain's `AgentExecutor` \-\- using `create_react_agent` or a custom langgraph implementation based on that is the recommended way\
\
👍1\
\
[![@qianL93](https://avatars.githubusercontent.com/u/11720452?u=fec4cc9123f4d55d00a56a60e5a74a15a0b6dfef&v=4)qianL93](https://github.com/qianL93) [Aug 13, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-10320428)\
\
edited\
\
What is the difference between 'tool calling agent'?\
\
1\
\
0 replies\
\
[![@afbarbaro](https://avatars.githubusercontent.com/u/18277423?u=e20dbaed2b1eede4ba8dd65682f548c1f99111a1&v=4)afbarbaro](https://github.com/afbarbaro) [Oct 22, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-11019484)\
\
I have a simple use of `create_react_agent` where I want to add different system messages, depending on the value of a property that I track in the agent `state`. Here's a simple example, where I want to track the number of calls to the LLM and key off that:\
\
```\
            def state_modifier(state: AgentState) -> Sequence[BaseMessage]:\
                # Track the number of calls to the agent\
                llm_calls = state.get("llm_calls", 0)\
                state["llm_calls"] = llm_calls + 1       # problem, this does NOT update state\
\
                # Add the adequate system message to the beginning of the messages\
                messages = list(state.get("messages", []))\
                content = (\
                    SystemMessages.lg_react_last()\
                    if llm_calls > 0\
                    else SystemMessages.lg_react_first(self.seeq_context)\
                )\
                messages.insert(0, SystemMessage(content))\
\
                # Return the messages\
                return messages\
```\
\
So my question is how can I mutate the `state` so that new properties and/or values stick?\
\
2\
\
2 replies\
\
[![@p19ky](https://avatars.githubusercontent.com/u/61684270?u=f3087c4730e295651c2b6c73903997428489fa42&v=4)](https://github.com/p19ky)\
\
[p19ky](https://github.com/p19ky) [Nov 1, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-11126549)\
\
You can maybe use the `checkpointer` parameter of `create_react_agent`? I am also new to langgraph but I am looking at the `create_react_agent` docs now. [https://langchain-ai.github.io/langgraph/reference/prebuilt/](https://langchain-ai.github.io/langgraph/reference/prebuilt/)\
\
[![@vkvashistha](https://avatars.githubusercontent.com/u/2606583?u=ef7d0fa1710a9e731c7d3b82a71719a5b12c1a49&v=4)](https://github.com/vkvashistha)\
\
[vkvashistha](https://github.com/vkvashistha) [Jan 10](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-11794844)\
\
state\_modifier seems not modifying the state.\
\
```\
def custom_state_modifier(self, state: InvoiceAgentState, config: RunnableConfig) -> Sequence[BaseMessage]:\
  state["my_key"] = "my value" # <--- This value is not sticky\
  system_prompt = "You're. a helpful assistant"\
  messages = state['messages']\
  return [SystemMessage(content=system_prompt, *messages]\
\
create_react_agent(tools=tools, model=self.llm, state_schema=MyCustomState,state_modifier=custom_state_modifier, checkpointer=MemorySaver(), debug=True)\
```\
\
Reason I found is that there is one bug in `create_react_agent`, under `call_model` and `acall_model` . It's returning { "messages" : response }, which do not consider the changes made by `custom_state_modifier`. Ideally it should be :\
\
```\
state["messages"] = response\
return state\
```\
\
[![@kevinkelin](https://avatars.githubusercontent.com/u/2595465?u=6e9a9eff137079cf07c908c18b14c3a06b85b9e8&v=4)kevinkelin](https://github.com/kevinkelin) [Dec 25, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-11661985)\
\
`graph = create_react_agent(model, tools=tools, state_modifier=prompt)`\
\
Is there a problem here?\
\
It should `graph = create_react_agent(model, tools=tools, messages_modifier=prompt)`\
\
It should be messages\_modifier, not state\_modifier ?\
\
1\
\
1 reply\
\
[![@kevinkelin](https://avatars.githubusercontent.com/u/2595465?u=6e9a9eff137079cf07c908c18b14c3a06b85b9e8&v=4)](https://github.com/kevinkelin)\
\
[kevinkelin](https://github.com/kevinkelin) [Dec 25, 2024](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-11662018)\
\
Ignore about it\
\
[![@PersonalRec](https://avatars.githubusercontent.com/u/45102782?v=4)PersonalRec](https://github.com/PersonalRec) [Jan 7](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-11763075)\
\
How can I control memory size (its summarization or cutting-off messages) in the pre-built agents like this?\
\
1\
\
👀1\
\
0 replies\
\
[![@vkvashistha](https://avatars.githubusercontent.com/u/2606583?u=ef7d0fa1710a9e731c7d3b82a71719a5b12c1a49&v=4)vkvashistha](https://github.com/vkvashistha) [Jan 10](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-11794829)\
\
state\_modifier seems not modifying the state.\
\
```\
def custom_state_modifier(self, state: InvoiceAgentState, config: RunnableConfig) -> Sequence[BaseMessage]:\
  state["my_key"] = "my value" # <--- This value is not sticky\
  system_prompt = "You're. a helpful assistant"\
  messages = state['messages']\
  return [SystemMessage(content=system_prompt, *messages]\
\
create_react_agent(tools=tools, model=self.llm, state_schema=MyCustomState,state_modifier=custom_state_modifier, checkpointer=MemorySaver(), debug=True)\
```\
\
Reason I found is that there is one bug in create\_react\_agent, under `call_model` and `acall_model` . It's returning `{ "messages" : response }`, which do not consider the changes made by `custom_state_modifier`. Ideally it should be :\
\
```\
state["messages"] = response\
return state\
```\
\
1\
\
👍1\
\
0 replies\
\
[![@moctarjallo](https://avatars.githubusercontent.com/u/23138961?u=bfa9024040c456d2e5e25b452c63d4ee6abf19c4&v=4)moctarjallo](https://github.com/moctarjallo) [Jan 26](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-11955240)\
\
But this function doesn't perform `persistence` right ? How to add that after creating the agent with this function ? (When i check `graph.checkpointer`, it is null and when i check `graph.compiled` it is `True`\
\
1\
\
0 replies\
\
[![@Giambapisasale](https://avatars.githubusercontent.com/u/8735065?u=49f6217af4e422ea1f53e86b882a8d75c898d520&v=4)Giambapisasale](https://github.com/Giambapisasale) [Feb 7](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-12093352)\
\
Good morning! what about tools with artifact and react agent? Is there a way to manage pre-built tools like tavily that return artifact and custom tools that use that artifacts? please help!\
\
thanks in advance\
\
1\
\
0 replies\
\
[![@chwenjun225](https://avatars.githubusercontent.com/u/93820624?u=d76f6cd58ded4e8013122b738cc036f519c588cf&v=4)chwenjun225](https://github.com/chwenjun225) [Feb 12](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-12171133)\
\
Not working, there is no tool in this output.\
\
================================ Human Message =================================\
\
what is the weather in sf?\
\
================================== Ai Message ==================================\
\
I don't have real-time weather data for San Francisco. For the most up-to-date and accurate information, I recommend checking a reliable weather website or app specifically for San Francisco. They offer the latest details on temperature, precipitation, and other weather conditions. Let me know if you'd like help with anything else!\
\
2\
\
1 reply\
\
[![@chwenjun225](https://avatars.githubusercontent.com/u/93820624?u=d76f6cd58ded4e8013122b738cc036f519c588cf&v=4)](https://github.com/chwenjun225)\
\
[chwenjun225](https://github.com/chwenjun225) [Feb 13](https://github.com/langchain-ai/langgraph/discussions/1060#discussioncomment-12181869)\
\
Update: after change from deepseek-r1-1.5B to llama3.2-1b-instruct, the model can use tool-call.\
\
Appendix: deepseek-r1 don't have tool-call feature ( [deepseek-ai/DeepSeek-R1#9 (comment)](https://github.com/deepseek-ai/DeepSeek-R1/issues/9#issuecomment-2604747754))\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fcreate-react-agent-system-prompt%2F)