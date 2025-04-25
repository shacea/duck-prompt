[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-memory/#how-to-add-thread-level-memory-to-a-react-agent)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/create-react-agent-memory.ipynb "Edit this page")

# How to add thread-level memory to a ReAct Agent [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-memory/\#how-to-add-thread-level-memory-to-a-react-agent "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [Checkpointer interface](https://langchain-ai.github.io/langgraph/concepts/persistence/#checkpointer-interface)
- [Agent Architectures](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/)
- [Chat Models](https://python.langchain.com/docs/concepts/chat_models/)
- [Tools](https://python.langchain.com/docs/concepts/tools/)

This guide will show how to add memory to the prebuilt ReAct agent. Please see [this tutorial](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent) for how to get started with the prebuilt ReAct agent

We can add memory to the agent, by passing a [checkpointer](https://langchain-ai.github.io/langgraph/reference/checkpoints/) to the [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) function.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-memory/\#setup "Permanent link")

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


## Code [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-memory/\#code "Permanent link")

API Reference: [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

```md-code__content
# First we initialize the model we want to use.
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o", temperature=0)

# For this tutorial we will use custom tool that returns pre-defined values for weather in two cities (NYC & SF)

from langchain_core.tools import tool

@tool
def get_weather(location: str) -> str:
    """Use this to get weather information."""
    if any([city in location.lower() for city in ["nyc", "new york city"]]):
        return "It might be cloudy in nyc"
    elif any([city in location.lower() for city in ["sf", "san francisco"]]):
        return "It's always sunny in sf"
    else:
        return f"I am not sure what the weather is in {location}"

tools = [get_weather]

# We can add "chat memory" to the graph with LangGraph's checkpointer
# to retain the chat context between interactions
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

# Define the graph

from langgraph.prebuilt import create_react_agent

graph = create_react_agent(model, tools=tools, checkpointer=memory)

```

## Usage [¶](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-memory/\#usage "Permanent link")

Let's interact with it multiple times to show that it can remember

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
config = {"configurable": {"thread_id": "1"}}
inputs = {"messages": [("user", "What's the weather in NYC?")]}

print_stream(graph.stream(inputs, config=config, stream_mode="values"))

```

```md-code__content
================================[1m Human Message [0m=================================\
\
What's the weather in NYC?\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  get_weather (call_xM1suIq26KXvRFqJIvLVGfqG)\
 Call ID: call_xM1suIq26KXvRFqJIvLVGfqG\
  Args:\
    city: nyc\
=================================[1m Tool Message [0m=================================\
Name: get_weather\
\
It might be cloudy in nyc\
==================================[1m Ai Message [0m==================================\
\
The weather in NYC might be cloudy.\
\
```\
\
Notice that when we pass the same thread ID, the chat history is preserved.\
\
```md-code__content\
inputs = {"messages": [("user", "What's it known for?")]}\
print_stream(graph.stream(inputs, config=config, stream_mode="values"))\
\
```\
\
```md-code__content\
================================[1m Human Message [0m=================================\
\
What's it known for?\
==================================[1m Ai Message [0m==================================\
\
New York City (NYC) is known for a variety of iconic landmarks, cultural institutions, and vibrant neighborhoods. Some of the most notable aspects include:\
\
1. **Statue of Liberty**: A symbol of freedom and democracy.\
2. **Times Square**: Known for its bright lights, Broadway theaters, and bustling atmosphere.\
3. **Central Park**: A large urban park offering a green oasis in the middle of the city.\
4. **Empire State Building**: An iconic skyscraper with an observation deck offering panoramic views of the city.\
5. **Broadway**: Famous for its world-class theater productions.\
6. **Wall Street**: The financial hub of the United States.\
7. **Museums**: Including the Metropolitan Museum of Art, the Museum of Modern Art (MoMA), and the American Museum of Natural History.\
8. **Diverse Cuisine**: A melting pot of culinary experiences from around the world.\
9. **Cultural Diversity**: A rich tapestry of cultures, languages, and traditions.\
10. **Fashion**: A global fashion capital, home to New York Fashion Week.\
\
These are just a few highlights of what makes NYC a unique and vibrant city.\
\
```\
\
```md-code__content\
\
```\
\
## Comments\
\
giscus\
\
#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/964)\
\
#### [8 comments](https://github.com/langchain-ai/langgraph/discussions/964)\
\
#### ·\
\
#### 13 replies\
\
_– powered by [giscus](https://giscus.app/)_\
\
- Oldest\
- Newest\
\
[![@honoured-1](https://avatars.githubusercontent.com/u/53032993?u=e9a6e7fb3774e99ae0db2f556b8d6c89bf578bcd&v=4)honoured-1](https://github.com/honoured-1) [Jul 9, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-9998901)\
\
Where is the rephrasel of the question happening?\
\
1\
\
3 replies\
\
[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)\
\
[hinthornw](https://github.com/hinthornw) [Jul 9, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-9998945)\
\
Contributor\
\
Could you elaborate? What rephrasing are you talking about?\
\
[![@honoured-1](https://avatars.githubusercontent.com/u/53032993?u=e9a6e7fb3774e99ae0db2f556b8d6c89bf578bcd&v=4)](https://github.com/honoured-1)\
\
[honoured-1](https://github.com/honoured-1) [Jul 9, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-9998992)\
\
so when you ask a follow up question, while working with memory\
\
suppose if a ask\
\
what is bank holidays api\
\
follow up question "what are it's endpoint"\
\
so before the followup question goes to a tool it gets rephrased as "what are endpoints of bank holidays api"\
\
how is that happening\
\
if you look into the harrison chase prompt for react agent, there is no mention of rephrasing the question\
\
what if i want to control the rephrasing, how can I do that with react\_agent\
\
[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)\
\
[hinthornw](https://github.com/hinthornw) [Jul 9, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10001276)\
\
Contributor\
\
You'd do it with the messages\_modifier!\
\
The LLM receives the input messages and then generates text to invoke the tool based on that message list. If you want to tell the LLM to do so in a certain way, you'd either do that by adding a system prompt or by making the tool's description more prescriptive\
\
[![@Raza25](https://avatars.githubusercontent.com/u/43875409?u=2eb31116e61d5708c0001844bc06522356021ea0&v=4)Raza25](https://github.com/Raza25) [Jul 9, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-9999811)\
\
I'm initializing the react agent in this way,\
\
```notranslate\
tools = [fetch_calendar_events, read_calendar_events, fetch_emails, search_emails]\
memory = MemorySaver()\
\
chat_prompt_template = ChatPromptTemplate.from_messages(\
    [\
        ("system", "You are a helpful assistant."),\
        ("human", "{messages}"),\
        ("placeholder", "{agent_scratchpad}"),\
    ]\
)\
def modify_messages(messages: list):\
    return chat_prompt_template.invoke({"messages": messages})\
config = {"configurable": {"thread_id": "thread-1"}}\
agent_executor = create_react_agent(model, tools, messages_modifier=modify_messages)\
agent_executor.invoke({"messages": [( "user", user_input)]} )["messages"][-1].content\
\
```\
\
1- Calling the agent with input often takes it to a recursive loop, that causes the agent to stop, how can this be avoided?\
\
2- The agent often repeats the output response, and goes in a loop and never stop, how can this be controlled?\
\
3- The agent when called with input where tool is not needed, it doesn't return a response or even if it does, its wrong, how can this be achieved?\
\
1\
\
5 replies\
\
[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)\
\
[hinthornw](https://github.com/hinthornw) [Jul 9, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10001285)\
\
Contributor\
\
At a glance, one thing that looks off is that\
\
```notranslate\
chat_prompt_template = ChatPromptTemplate.from_messages(\
    [\
        ("system", "You are a helpful assistant."),\
        ("human", "{messages}"),\
        ("placeholder", "{agent_scratchpad}"),\
    ]\
)\
\
```\
\
should be\
\
```notranslate\
chat_prompt_template = ChatPromptTemplate.from_messages(\
    [\
        ("system", "You are a helpful assistant."),\
        ("placeholder", "{messages}"),\
    ]\
)\
\
```\
\
since there isn't an agent\_scratchpad variable being passed in.\
\
You can see the difference in a langsmith trace\
\
[![@Raza25](https://avatars.githubusercontent.com/u/43875409?u=2eb31116e61d5708c0001844bc06522356021ea0&v=4)](https://github.com/Raza25)\
\
[Raza25](https://github.com/Raza25) [Jul 9, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10001417)\
\
edited\
\
Thankyou for identifying that, however when I try to add memory to ReAct agent, it often goes in a recursive loop, hence costing more with no reasonable response, how can that be stopped?\
\
my code snippet\
\
```notranslate\
memory = MemorySaver()\
config = {"configurable": {"thread_id": "thread-1"}}\
agent_executor = create_react_agent(model, tools, messages_modifier=modify_messages, checkpointer=memory)\
agent_executor.invoke({"messages": [("user", user_input)]}, config,)\
\
```\
\
[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)\
\
[hinthornw](https://github.com/hinthornw) [Jul 10, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10004939)\
\
Contributor\
\
Could you share a trace illustrating the issue?\
\
[![@Raza25](https://avatars.githubusercontent.com/u/43875409?u=2eb31116e61d5708c0001844bc06522356021ea0&v=4)](https://github.com/Raza25)\
\
[Raza25](https://github.com/Raza25) [Jul 10, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10006275)\
\
Strangely I'm not getting the error now, could the removal of `{agent_scratchpad}` from placeholder had it resolved?\
\
[![@Raza25](https://avatars.githubusercontent.com/u/43875409?u=2eb31116e61d5708c0001844bc06522356021ea0&v=4)](https://github.com/Raza25)\
\
[Raza25](https://github.com/Raza25) [Jul 10, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10006343)\
\
Also could you tell me, which approach is better i.e. calling the agent with `agent_executor.invoke()` or `agent_executor.stream()`, are these equivalent or like one is better than the other?\
\
[![@Pythonista7](https://avatars.githubusercontent.com/u/36104244?u=1ac6ba4051e99094406e1bd812475c123ef8481a&v=4)Pythonista7](https://github.com/Pythonista7) [Jul 14, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10045084)\
\
Anyway we can have structured outputs as part of the react agent?\
\
1\
\
0 replies\
\
[![@abprime](https://avatars.githubusercontent.com/u/4160047?v=4)abprime](https://github.com/abprime) [Aug 6, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10256194)\
\
Contributor\
\
Is there a way to remove messages from the react agent memory similar to [https://langchain-ai.github.io/langgraph/how-tos/memory/add-summary-conversation-history/](https://langchain-ai.github.io/langgraph/how-tos/memory/add-summary-conversation-history/).?\
\
Because overtime the messages in react agent will keep growing.\
\
1\
\
👍1\
\
3 replies\
\
[![@vigneshethiraj](https://avatars.githubusercontent.com/u/26295316?u=be326661ee7ccb467eef2ee6c3e8580f56e425a6&v=4)](https://github.com/vigneshethiraj)\
\
[vigneshethiraj](https://github.com/vigneshethiraj) [Aug 29, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10483111)\
\
I'm looking for the same, Please let me know if you have figured out a way to solve this.\
\
I'm using postgres for keep track of checkpointer memory.\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Aug 29, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10487825)\
\
Collaborator\
\
would this solve your problem? [https://langchain-ai.github.io/langgraph/how-tos/memory/delete-messages/](https://langchain-ai.github.io/langgraph/how-tos/memory/delete-messages/)\
\
👍1\
\
[![@vigneshethiraj](https://avatars.githubusercontent.com/u/26295316?u=be326661ee7ccb467eef2ee6c3e8580f56e425a6&v=4)](https://github.com/vigneshethiraj)\
\
[vigneshethiraj](https://github.com/vigneshethiraj) [Sep 1, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10511843)\
\
Thanks for suggesting this. I'm able to delete the messages using this. But the immediate message after delete messages is resulting in error,\
\
`httpx.HTTPStatusError: Error response 400 while fetching https://api.mistral.ai/v1/chat/completions: {"object":"error","message":"Not the same number of function calls and responses","type":"invalid_request_error","param":null,"code":null}   `\
\
# Below are the logs generated on the message sent next to delete message operation on the same conversation,\
\
\` _2024-09-01 17:08:57.580 \| DEBUG \| **main**:troubleshootingCoPilotChat:279_ \- Loaded state from checkpointer: {'v': 1, 'id': '1ef6856c-2865-6e57-800c-65eca0b7215e', 'ts': '2024-09-01T11:38:51.183675+00:00', 'pending\_sends': \[\], 'versions\_seen': {'agent': {'action': '00000000000000000000000000000012.cb655b525c5cd87240c140a2318d19f1', 'start:agent': '00000000000000000000000000000010.d6f25946c3108fc12f27abbcf9b4cedc'}, 'action': {'branch:agent:should\_continue:action': '00000000000000000000000000000011.065d90dd7f7cd091f0233855210bb2af'}, ' **input**': {}, ' **start**': {' **start**': '00000000000000000000000000000009.0685f2e4991ae202c1f4492ffabbbcde'}, 'delete\_messages': {'branch:agent:should\_continue:delete\_messages': '00000000000000000000000000000013.065d90dd7f7cd091f0233855210bb2af'}}, 'channel\_versions': {'agent': '00000000000000000000000000000014.', 'action': '00000000000000000000000000000013.', 'messages': '00000000000000000000000000000014.60aeacbb9a62c254ef74c324297b40de', ' **start**': '00000000000000000000000000000010.', 'start:agent': '00000000000000000000000000000011.', 'delete\_messages': '00000000000000000000000000000014.d8f0b6f5e4cf4418777b2484e45aa5a2', 'branch:agent:should\_continue:action': '00000000000000000000000000000012.', 'branch:agent:should\_continue:delete\_messages': '00000000000000000000000000000014.'}, 'channel\_values': {'messages': \[ _AIMessage_(content='', additional\_kwargs={'tool\_calls': \[{'id': 'JsYmtQq0E', 'function': {'name': 'get-assigned-jira-tickets', 'arguments': '{"emailId": " [vigneshethiraj@gmail.com](mailto:vigneshethiraj@gmail.com)", "username": "vignesh ethiraj"}'}}\]}, response\_metadata={'token\_usage': {'prompt\_tokens': 1716, 'total\_tokens': 1759, 'completion\_tokens': 43}, 'model': 'open-mistral-nemo-2407', 'finish\_reason': 'tool\_calls'}, id='run-ff5bf439-c39b-400f-9091-d1fafd5aa9cd-0', tool\_calls=\[{'name': 'get-assigned-jira-tickets', 'args': {'emailId': ' [vigneshethiraj@gmail.com](mailto:vigneshethiraj@gmail.com)', 'username': 'vignesh ethiraj'}, 'id': 'JsYmtQq0E', 'type': 'tool\_call'}\], usage\_metadata={'input\_tokens': 1716, 'output\_tokens': 43, 'total\_tokens': 1759}), ToolMessage(content='{"expand": "schema,names", "startAt": 0, "maxResults": 2, "total": 20, "issues": \[{"expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields", "id": "10260", "self": "https:///rest/api/3/issue/10260", "key": "SUP-90", "fields": {"summary": "Interface Gi4/0(): Link down", "assignee": {"self": "https:///rest/api/3/user?accountId=", "accountId": "", "emailAddress": " [vigneshethiraj@gmail.com](mailto:vigneshethiraj@gmail.com)"}}}}, {"expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields", "id": "10189", "self": "https:///rest/api/3/issue/10189", "key": "SCRUM-81", "fields": {"summary": "Derive intelligence from all network operations chat", "displayName": "vignesh ethiraj", "active": true, "timeZone": "Asia/Kolkata", "accountType": "atlassian"}}}\]}', name='get-assigned-jira-tickets', id='4dbde2db-066b-4e12-9d57-f1bb5f52badc', tool\_call\_id='JsYmtQq0E'), _AIMessage_(content='Here are the tickets assigned to you:\\n\\n1. SUP-90 - Interface Gi4/0(): Link down\\n2. SCRUM-81 -\
\
Derive intelligence \\n\\nWhich one would you like to start working on?', response\_metadata={'token\_usage': {'prompt\_tokens': 3222, 'total\_tokens': 3279, 'completion\_tokens': 57}, 'model': 'open-mistral-nemo-2407', 'finish\_reason': 'stop'}, id='run-b3f32205-026d-470f-b94a-6e571b966a22-0', usage\_metadata={'input\_tokens': 3222, 'output\_tokens': 57, 'total\_tokens': 3279})\], 'delete\_messages': 'delete\_messages'}}\
\
_2024-09-01 17:08:58.031 \| ERROR \| **main**:troubleshootingCoPilotChat:287_ \- Error during app.invoke(): Error response\
\
400 while fetching [https://api.mistral.ai/v1/chat/completions](https://api.mistral.ai/v1/chat/completions): {"object":"error","message":"Not the same number of function calls and responses","type":"invalid\_request\_error","param":null,"code":null}\
\
_2024-09-01 17:08:58.037 \| ERROR \| **main**:troubleshootingCoPilotChat:288_ \- Traceback (most recent call last):\
\
File "d:\\NetoAI\\GiNet workflows\\Gi-Net-Workflows\\Troubleshooting Co-Pilot Upgrade\\main.py", line 284, in troubleshootingCoPilotChat\
\
final\_state = application.invoke({"messages":input\_message}, config=config)\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langgraph\\pregel\_ _init_\_.py", line 1312, in invoke\
\
for chunk in self.stream(\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langgraph\\pregel\_ _init_\_.py", line 997, in stream\
\
_panic\_or\_proceed(done, inflight, loop.step)_\
\
_File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langgraph\\pregel\_init_.py", line 1398, in \_panic\_or\_proceed\
\
raise exc\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langgraph\\pregel\\executor.py", line 60,\
\
in done\
\
task.result()\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\concurrent\\futures\_base.py", line 438, in result\
\
return self.\_\_get\_result()\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\concurrent\\futures\_base.py", line 390, in \_\_get\_result\
\
raise self.\_exception\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\concurrent\\futures\\thread.py", line 52, in run\
\
result = self.fn(\*self.args, \*\*self.kwargs)\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langgraph\\pregel\\retry.py", line 25, in\
\
run\_with\_retry\
\
task.proc.invoke(task.input, task.config)\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langchain\_core\\runnables\\base.py", line\
\
2876, in invoke\
\
input = context.run(step.invoke, input, config, \*\*kwargs)\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langgraph\\utils.py", line 102, in invoke ret = context.run(self.func, input, \*\*kwargs)\
\
File "d:\\NetoAI\\GiNet workflows\\Gi-Net-Workflows\\Troubleshooting Co-Pilot Upgrade\\main.py", line 174, in call\_model\
\
response = bound\_model.invoke(state\["messages"\])\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langchain\_core\\runnables\\base.py", line\
\
5092, in invoke\
\
return self.bound.invoke(\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langchain\_core\\language\_models\\chat\_models.py", line 276, in invoke\
\
self.generate\_prompt(\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langchain\_core\\language\_models\\chat\_models.py", line 776, in generate\_prompt\
\
return self.generate(prompt\_messages, stop=stop, callbacks=callbacks, \*\*kwargs)\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langchain\_core\\language\_models\\chat\_models.py", line 633, in generate\
\
raise e\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langchain\_core\\language\_models\\chat\_models.py", line 623, in generate\
\
self.\_generate\_with\_cache(\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langchain\_core\\language\_models\\chat\_models.py", line 845, in \_generate\_with\_cache\
\
result = self.\_generate(\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langchain\_mistralai\\chat\_models.py", line 526, in \_generate\
\
response = self.completion\_with\_retry(\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langchain\_mistralai\\chat\_models.py", line 449, in completion\_with\_retry\
\
rtn = \_completion\_with\_retry(\*\*kwargs)\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langchain\_mistralai\\chat\_models.py", line 446, in \_completion\_with\_retry\
\
\_raise\_on\_error(response)\
\
File "C:\\Users\\MY PC\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\langchain\_mistralai\\chat\_models.py", line 167, in \_raise\_on\_error\
\
raise httpx.HTTPStatusError(\
\
httpx.HTTPStatusError: Error response 400 while fetching [https://api.mistral.ai/v1/chat/completions](https://api.mistral.ai/v1/chat/completions): {"object":"error","message":"Not the same number of function calls and responses","type":"invalid\_request\_error","param":null,"code":null}\
\
\`\
\
[![@nick-youngblut](https://avatars.githubusercontent.com/u/2468572?u=257f896c1ce6dca97e0a7d840725cbc023a71839&v=4)nick-youngblut](https://github.com/nick-youngblut) [Aug 10, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10300441)\
\
Using `checkpointer` results in the following:\
\
```notranslate\
ValueError: Checkpointer requires one or more of the following 'configurable' keys: ['thread_id', 'checkpoint_ns', 'checkpoint_id']\
\
```\
\
No clear docs on this page about dealing with this checkpointer requirement\
\
1\
\
2 replies\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Aug 12, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10314892)\
\
Collaborator\
\
you always need to pass `{"configurable": {"thread_id": <thread-id>}}` when using a checkpointer\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Aug 12, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-10314899)\
\
Collaborator\
\
see more here [https://langchain-ai.github.io/langgraph/how-tos/persistence/](https://langchain-ai.github.io/langgraph/how-tos/persistence/)\
\
[![@Maheshbabu9199](https://avatars.githubusercontent.com/u/59558917?u=7a5a31c082030ce6794cf1da7a61edfcea731796&v=4)Maheshbabu9199](https://github.com/Maheshbabu9199) [Nov 26, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-11386044)\
\
Can we add custom messages to agent's memory using MemorySaver()? Is it even possible or is it just that only after the agent is initalised the conversations only gets stored in the memorysaver, not the prior custom information.\
\
1\
\
0 replies\
\
[![@spatnala-eightfold](https://avatars.githubusercontent.com/u/133627309?v=4)spatnala-eightfold](https://github.com/spatnala-eightfold) [Dec 2, 2024](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-11435450)\
\
How do I force create\_react\_agent to return a json object without any additional text ?\
\
1\
\
0 replies\
\
[![@crykrypta](https://avatars.githubusercontent.com/u/140960438?u=f2612b47c8da16da6e54065a28b9563e7736109d&v=4)crykrypta](https://github.com/crykrypta) [Feb 21](https://github.com/langchain-ai/langgraph/discussions/964#discussioncomment-12277394)\
\
In this case, checkpointer will endlessly accumulate the dialog in RAM. Is there any way to limit short-term memory?\
\
2\
\
0 replies\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fcreate-react-agent-memory%2F)