[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/chatbots/information-gather-prompting/#prompt-generation-from-user-requirements)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/chatbots/information-gather-prompting.ipynb "Edit this page")

# Prompt Generation from User Requirements [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbots/information-gather-prompting/\#prompt-generation-from-user-requirements "Permanent link")

In this example we will create a chat bot that helps a user generate a prompt.
It will first collect requirements from the user, and then will generate the prompt (and refine it based on user input).
These are split into two separate states, and the LLM decides when to transition between them.

A graphical representation of the system can be found below.

![prompt-generator.png](<Base64-Image-Removed>)

## Setup [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbots/information-gather-prompting/\#setup "Permanent link")

First, let's install our required packages and set our OpenAI API key (the LLM we will use)

```md-code__content
%%capture --no-stderr
% pip install -U langgraph langchain_openai

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


## Gather information [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbots/information-gather-prompting/\#gather-information "Permanent link")

First, let's define the part of the graph that will gather user requirements. This will be an LLM call with a specific system message. It will have access to a tool that it can call when it is ready to generate the prompt.

Using Pydantic with LangChain

This notebook uses Pydantic v2 `BaseModel`, which requires `langchain-core >= 0.3`. Using `langchain-core < 0.3` will result in errors due to mixing of Pydantic v1 and v2 `BaseModels`.


API Reference: [SystemMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.system.SystemMessage.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html)

```md-code__content
from typing import List

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from pydantic import BaseModel

```

```md-code__content
template = """Your job is to get information from a user about what type of prompt template they want to create.

You should get the following information from them:

- What the objective of the prompt is
- What variables will be passed into the prompt template
- Any constraints for what the output should NOT do
- Any requirements that the output MUST adhere to

If you are not able to discern this info, ask them to clarify! Do not attempt to wildly guess.

After you are able to discern all the information, call the relevant tool."""

def get_messages_info(messages):
    return [SystemMessage(content=template)] + messages

class PromptInstructions(BaseModel):
    """Instructions on how to prompt the LLM."""

    objective: str
    variables: List[str]
    constraints: List[str]
    requirements: List[str]

llm = ChatOpenAI(temperature=0)
llm_with_tool = llm.bind_tools([PromptInstructions])

def info_chain(state):
    messages = get_messages_info(state["messages"])
    response = llm_with_tool.invoke(messages)
    return {"messages": [response]}

```

## Generate Prompt [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbots/information-gather-prompting/\#generate-prompt "Permanent link")

We now set up the state that will generate the prompt.
This will require a separate system message, as well as a function to filter out all message PRIOR to the tool invocation (as that is when the previous state decided it was time to generate the prompt

API Reference: [AIMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html) \| [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html) \| [ToolMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.tool.ToolMessage.html)

```md-code__content
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# New system prompt
prompt_system = """Based on the following requirements, write a good prompt template:

{reqs}"""

# Function to get the messages for the prompt
# Will only get messages AFTER the tool call
def get_prompt_messages(messages: list):
    tool_call = None
    other_msgs = []
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            tool_call = m.tool_calls[0]["args"]
        elif isinstance(m, ToolMessage):
            continue
        elif tool_call is not None:
            other_msgs.append(m)
    return [SystemMessage(content=prompt_system.format(reqs=tool_call))] + other_msgs

def prompt_gen_chain(state):
    messages = get_prompt_messages(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [response]}

```

## Define the state logic [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbots/information-gather-prompting/\#define-the-state-logic "Permanent link")

This is the logic for what state the chatbot is in.
If the last message is a tool call, then we are in the state where the "prompt creator" ( `prompt`) should respond.
Otherwise, if the last message is not a HumanMessage, then we know the human should respond next and so we are in the `END` state.
If the last message is a HumanMessage, then if there was a tool call previously we are in the `prompt` state.
Otherwise, we are in the "info gathering" ( `info`) state.

API Reference: [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END)

```md-code__content
from typing import Literal

from langgraph.graph import END

def get_state(state):
    messages = state["messages"]
    if isinstance(messages[-1], AIMessage) and messages[-1].tool_calls:
        return "add_tool_message"
    elif not isinstance(messages[-1], HumanMessage):
        return END
    return "info"

```

## Create the graph [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbots/information-gather-prompting/\#create-the-graph "Permanent link")

We can now the create the graph.
We will use a SqliteSaver to persist conversation history.

API Reference: [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [add\_messages](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.message.add_messages)

```md-code__content
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list, add_messages]

memory = MemorySaver()
workflow = StateGraph(State)
workflow.add_node("info", info_chain)
workflow.add_node("prompt", prompt_gen_chain)

@workflow.add_node
def add_tool_message(state: State):
    return {
        "messages": [\
            ToolMessage(\
                content="Prompt generated!",\
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],\
            )\
        ]
    }

workflow.add_conditional_edges("info", get_state, ["add_tool_message", "info", END])
workflow.add_edge("add_tool_message", "prompt")
workflow.add_edge("prompt", END)
workflow.add_edge(START, "info")
graph = workflow.compile(checkpointer=memory)

```

```md-code__content
from IPython.display import Image, display

display(Image(graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

## Use the graph [¶](https://langchain-ai.github.io/langgraph/tutorials/chatbots/information-gather-prompting/\#use-the-graph "Permanent link")

We can now use the created chatbot.

```md-code__content
import uuid

cached_human_responses = ["hi!", "rag prompt", "1 rag, 2 none, 3 no, 4 no", "red", "q"]
cached_response_index = 0
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
while True:
    try:
        user = input("User (q/Q to quit): ")
    except:
        user = cached_human_responses[cached_response_index]
        cached_response_index += 1
    print(f"User (q/Q to quit): {user}")
    if user in {"q", "Q"}:
        print("AI: Byebye")
        break
    output = None
    for output in graph.stream(
        {"messages": [HumanMessage(content=user)]}, config=config, stream_mode="updates"
    ):
        last_message = next(iter(output.values()))["messages"][-1]
        last_message.pretty_print()

    if output and "prompt" in output:
        print("Done!")

```

```md-code__content
User (q/Q to quit): hi!
==================================[1m Ai Message [0m==================================\
\
Hello! How can I assist you today?\
User (q/Q to quit): rag prompt\
==================================[1m Ai Message [0m==================================\
\
Sure! I can help you create a prompt template. To get started, could you please provide me with the following information:\
\
1. What is the objective of the prompt?\
2. What variables will be passed into the prompt template?\
3. Any constraints for what the output should NOT do?\
4. Any requirements that the output MUST adhere to?\
\
Once I have this information, I can assist you in creating the prompt template.\
User (q/Q to quit): 1 rag, 2 none, 3 no, 4 no\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  PromptInstructions (call_tcz0foifsaGKPdZmsZxNnepl)\
 Call ID: call_tcz0foifsaGKPdZmsZxNnepl\
  Args:\
    objective: rag\
    variables: ['none']\
    constraints: ['no']\
    requirements: ['no']\
=================================[1m Tool Message [0m=================================\
\
Prompt generated!\
==================================[1m Ai Message [0m==================================\
\
Please write a response using the RAG (Red, Amber, Green) rating system.\
Done!\
User (q/Q to quit): red\
==================================[1m Ai Message [0m==================================\
\
Response: The status is RED.\
User (q/Q to quit): q\
AI: Byebye\
\
```\
\
## Comments\
\
giscus\
\
#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/501)\
\
#### [9 comments](https://github.com/langchain-ai/langgraph/discussions/501)\
\
#### ·\
\
#### 11 replies\
\
_– powered by [giscus](https://giscus.app/)_\
\
- Oldest\
- Newest\
\
[![@alonsoir](https://avatars.githubusercontent.com/u/2405946?u=e1b1c7c06377ff6291b4888885a1d94e29f47c91&v=4)alonsoir](https://github.com/alonsoir) [May 20, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-9499033)\
\
Input User (q/Q to quit): the schema to extract, and the text to extract it from\
\
Traceback (most recent call last):\
\
File "/Users/aironman/git/reliable-rag-using-langGraph/chat\_bot\_info\_gathering.py", line 96, in\
\
for output in graph.stream(\[HumanMessage(content=user)\], config=config):\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/langgraph/pregel/ **init**.py", line 834, in stream\
\
\_panic\_or\_proceed(done, inflight, step)\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/langgraph/pregel/ **init**.py", line 1334, in \_panic\_or\_proceed\
\
raise exc\
\
File "/usr/local/Cellar/python@3.11/3.11.9/Frameworks/Python.framework/Versions/3.11/lib/python3.11/concurrent/futures/thread.py", line 58, in run\
\
result = self.fn(\*self.args, \*\*self.kwargs)\
\
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/langgraph/pregel/retry.py", line 66, in run\_with\_retry\
\
task.proc.invoke(task.input, task.config)\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/langchain\_core/runnables/base.py", line 2368, in invoke\
\
input = step.invoke(\
\
^^^^^^^^^^^^\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/langchain\_core/runnables/base.py", line 4396, in invoke\
\
return self.bound.invoke(\
\
^^^^^^^^^^^^^^^^^^\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/langchain\_core/language\_models/chat\_models.py", line 170, in invoke\
\
self.generate\_prompt(\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/langchain\_core/language\_models/chat\_models.py", line 599, in generate\_prompt\
\
return self.generate(prompt\_messages, stop=stop, callbacks=callbacks, \*\*kwargs)\
\
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/langchain\_core/language\_models/chat\_models.py", line 456, in generate\
\
raise e\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/langchain\_core/language\_models/chat\_models.py", line 446, in generate\
\
self.\_generate\_with\_cache(\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/langchain\_core/language\_models/chat\_models.py", line 671, in \_generate\_with\_cache\
\
result = self.\_generate(\
\
^^^^^^^^^^^^^^^\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/langchain\_openai/chat\_models/base.py", line 522, in \_generate\
\
response = self.client.create(messages=message\_dicts, \*\*params)\
\
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/openai/\_utils/\_utils.py", line 277, in wrapper\
\
return func(\*args, \*\*kwargs)\
\
^^^^^^^^^^^^^^^^^^^^^\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/openai/resources/chat/completions.py", line 590, in create\
\
return self.\_post(\
\
^^^^^^^^^^^\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/openai/\_base\_client.py", line 1240, in post\
\
return cast(ResponseT, self.request(cast\_to, opts, stream=stream, stream\_cls=stream\_cls))\
\
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/openai/\_base\_client.py", line 921, in request\
\
return self.\_request(\
\
^^^^^^^^^^^^^^\
\
File "/Users/aironman/Library/Caches/pypoetry/virtualenvs/reliable-rag-using-langgraph-Jr5kRkNJ-py3.11/lib/python3.11/site-packages/openai/\_base\_client.py", line 1020, in \_request\
\
raise self.\_make\_status\_error\_from\_response(err.response) from None\
\
openai.BadRequestError: Error code: 400 - {'error': {'message': "An assistant message with 'tool\_calls' must be followed by tool messages responding to each 'tool\_call\_id'. The following tool\_call\_ids did not have response messages: call\_ImYUXkktr09rjRrEYsZTkhTe", 'type': 'invalid\_request\_error', 'param': 'messages.\[9\].role', 'code': None}}\
\
Process finished with exit code 1\
\
1\
\
4 replies\
\
[![@CARYCHEN04](https://avatars.githubusercontent.com/u/165979990?v=4)](https://github.com/CARYCHEN04)\
\
[CARYCHEN04](https://github.com/CARYCHEN04) [May 29, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-9588471)\
\
try "llm = ChatOpenAI(model="gpt-4",temperature=0)"，it appears work fine.\
\
👍1\
\
[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)\
\
[hinthornw](https://github.com/hinthornw) [Jun 4, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-9670246)\
\
Contributor\
\
edited\
\
[@alonsoir](https://github.com/alonsoir) if you continue looping after it's completed then you'll have to add a ToolMessage to the history!\
\
👍1😄1\
\
[![@Klafi11](https://avatars.githubusercontent.com/u/128471755?v=4)](https://github.com/Klafi11)\
\
[Klafi11](https://github.com/Klafi11) [Jun 5, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-9677960)\
\
[@hinthornw](https://github.com/hinthornw) do you know if it's possible to kind of reset the llm after it finished the tool\_call, that you can query again. Im using the Information gathering chat bot to get User Information for a Project they want to participate. it can be the case that the User may want to requery another project. Currently im using streamlit as application and i need to refresh the page to query again.\
\
[![@Klafi11](https://avatars.githubusercontent.com/u/128471755?v=4)](https://github.com/Klafi11)\
\
[Klafi11](https://github.com/Klafi11) [Jun 10, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-9731642)\
\
solved it. Thanks anyway :)\
\
[![@alonsoir](https://avatars.githubusercontent.com/u/2405946?u=e1b1c7c06377ff6291b4888885a1d94e29f47c91&v=4)alonsoir](https://github.com/alonsoir) [Jun 5, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-9675191)\
\
Thanks for the updates, you are great people!!\
\
I would like to know your opinion about the use of graphs together with vector databases so that LLMs do not stop scanning certain areas of knowledge and thus stop hallucinating, at least, that is what I understand about this phenomenon , since the LLM does not find the relevant areas in its scan of embedded areas, it has a tendency to be more creative. In theory, if when translating our prompt you are able to go through all the graphs that contain said information, and said information is of quality, the vector database will be able to select the information stored in those nodes using similar cosine. , correct?\
\
I would like to know your expert opinion, because I see above all that regardless of whether this technique is relevant or not with this technology, what has always given me problems is how difficult it is to save and maintain updated information in a graph, especially with neo4j and that peculiar language. I suppose it must be very effective so that they don't deprecate it, because to me it seems horrible and worthy of the hottest flames of one of Dante's infernos.\
\
Ideally, using this technology cries out for an NLP process capable of reading all the information in the text, detecting what a node is, what information about that node is, and what the relationships are with other nodes, so that when you pass it other text, By doing the same thing and finding nodes, information and relationships, come to some agreement on maintaining validity between different versions.\
\
1\
\
0 replies\
\
[![@Nagahemachand](https://avatars.githubusercontent.com/u/42846711?u=d81710deb82217adf57cb184566aeaa046fde4d3&v=4)Nagahemachand](https://github.com/Nagahemachand) [Jun 28, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-9907585)\
\
Is this more like proactive retrieval instead of reactive retreival?\
\
1\
\
0 replies\
\
[![@yuting1214](https://avatars.githubusercontent.com/u/31685881?u=c4041ca7fb103cfa9bde8e73b459f0760adb91d7&v=4)yuting1214](https://github.com/yuting1214) [Jul 27, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10169029)\
\
Is this article deprecated?\
\
There should be using StateGraph instead of MessageGraph?\
\
1\
\
0 replies\
\
[![@HDO504](https://avatars.githubusercontent.com/u/74007396?v=4)HDO504](https://github.com/HDO504) [Aug 18, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10370950)\
\
User (q/Q to quit): hello\
\
Traceback (most recent call last):\
\
File "D:\\research\\LLM\_FULL\_STACK\\LLM\_AID\\LLM\_fullstack\\multi\_agents.py", line 134, in\
\
for output in graph.stream(\
\
File "D:\\anaconda\\Lib\\site-packages\\langgraph\\pregel\_ _init_\_.py", line 997, in stream\
\
_panic\_or\_proceed(done, inflight, loop.step)_\
\
_File "D:\\anaconda\\Lib\\site-packages\\langgraph\\pregel\_init_.py", line 1398, in \_panic\_or\_proceed\
\
raise exc\
\
File "D:\\anaconda\\Lib\\site-packages\\langgraph\\pregel\\executor.py", line 60, in done\
\
task.result()\
\
File "D:\\anaconda\\Lib\\concurrent\\futures\_base.py", line 449, in result\
\
return self.\_\_get\_result()\
\
^^^^^^^^^^^^^^^^^^^\
\
File "D:\\anaconda\\Lib\\concurrent\\futures\_base.py", line 401, in \_\_get\_result\
\
raise self.\_exception\
\
File "D:\\anaconda\\Lib\\concurrent\\futures\\thread.py", line 58, in run\
\
result = self.fn(\*self.args, \*\*self.kwargs)\
\
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\
\
File "D:\\anaconda\\Lib\\site-packages\\langgraph\\pregel\\retry.py", line 25, in run\_with\_retry\
\
task.proc.invoke(task.input, task.config)\
\
File "D:\\anaconda\\Lib\\site-packages\\langgraph\\utils.py", line 93, in invoke\
\
ret = self.\_call\_with\_config(\
\
^^^^^^^^^^^^^^^^^^^^^^^\
\
File "D:\\anaconda\\Lib\\site-packages\\langchain\_core\\runnables\\base.py", line 1785, in \_call\_with\_config\
\
context.run(\
\
File "D:\\anaconda\\Lib\\site-packages\\langchain\_core\\runnables\\config.py", line 427, in call\_func\_with\_variable\_args\
\
return func(input, \*\*kwargs) # type: ignore\[call-arg\]\
\
^^^^^^^^^^^^^^^^^^^^^\
\
File "D:\\anaconda\\Lib\\site-packages\\langgraph\\pregel\\write.py", line 97, in \_write\
\
values = \[\
\
^\
\
File "D:\\anaconda\\Lib\\site-packages\\langgraph\\pregel\\write.py", line 98, in\
\
val if write.mapper is None else write.mapper.invoke(val, config)\
\
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\
\
File "D:\\anaconda\\Lib\\site-packages\\langgraph\\utils.py", line 102, in invoke\
\
ret = context.run(self.func, input, \*\*kwargs)\
\
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\
\
File "D:\\anaconda\\Lib\\site-packages\\langgraph\\graph\\state.py", line 527, in \_get\_state\_key\
\
raise InvalidUpdateError(f"Expected dict, got {input}")\
\
langgraph.errors.InvalidUpdateError: Expected dict, got \[HumanMessage(content='hello')\]\
\
I just paste this code to my pycharm, but it didn't work\
\
1\
\
0 replies\
\
[![@yuxiaojian](https://avatars.githubusercontent.com/u/9577948?v=4)yuxiaojian](https://github.com/yuxiaojian) [Aug 19, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10377696)\
\
looks like this article is deprecated. it doesn't work. the "graph.stream" should have "State" type input\
\
1\
\
6 replies\
\
Show 1 previous reply\
\
[![@haimh](https://avatars.githubusercontent.com/u/5346314?v=4)](https://github.com/haimh)\
\
[haimh](https://github.com/haimh) [Aug 21, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10405161)\
\
I've faced the same issue here!\
\
So, I've tried to put TypeDict into graph as bellow:\
\
user\_question = messages\[-1\].content\
\
inputs = { "messages": \[HumanMessage(content=user\_question)\] }\
\
...\
\
async for event in chatbot.astream\_events(\
\
inputs,\
\
config,\
\
stream\_mode="updates",\
\
version="v2"\
\
):\
\
and it throw out error:\
\
ValueError: Message dict must contain 'role' and 'content' keys, got {'messages': \[HumanMessage(content='What could you do?', id='950572\
\
ce-d259-41fa-9c21-c70a3d88365c')\]}\
\
Then, I've tried with convert all mesages into dict with key "role" and "content", but it refuse to run with the same error.\
\
I think it could be a bug with langchain libraries or need to update elsewhere.\
\
Have you got any ideas or suggestion?\
\
Thank in advance.\
\
Richard.\
\
[![@haimh](https://avatars.githubusercontent.com/u/5346314?v=4)](https://github.com/haimh)\
\
[haimh](https://github.com/haimh) [Aug 23, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10424905)\
\
I've just seen latest update from Langchain team. It worked like a champ! Thanks for great effort <3\
\
[![@deepakjoshi-ekline](https://avatars.githubusercontent.com/u/166969196?u=deef435f3a9d8e0111448efeb494910f57b6fe8a&v=4)](https://github.com/deepakjoshi-ekline)\
\
[deepakjoshi-ekline](https://github.com/deepakjoshi-ekline) [Aug 23, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10426112)\
\
[@haimh](https://github.com/haimh) could you please provide your code or code repo here ?\
\
[![@haimh](https://avatars.githubusercontent.com/u/5346314?v=4)](https://github.com/haimh)\
\
[haimh](https://github.com/haimh) [Aug 23, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10426126)\
\
Here it is:\
\
Link: [https://github.com/langchain-ai/langgraph/blob/main/examples/chatbots/information-gather-prompting.ipynb](https://github.com/langchain-ai/langgraph/blob/main/examples/chatbots/information-gather-prompting.ipynb)\
\
[![@deepakjoshi-ekline](https://avatars.githubusercontent.com/u/166969196?u=deef435f3a9d8e0111448efeb494910f57b6fe8a&v=4)](https://github.com/deepakjoshi-ekline)\
\
[deepakjoshi-ekline](https://github.com/deepakjoshi-ekline) [Aug 23, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10426139)\
\
Thanks\
\
[![@jellis18](https://avatars.githubusercontent.com/u/3458354?u=5206fd4a08faaab285474a5f23726a0077605b0c&v=4)jellis18](https://github.com/jellis18) [Aug 30, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10498895)\
\
I'm somewhat new to langchain/langgraph. I'm a bit confused here as to why you have the `add_tool_message` tool. Could we not just have the graph with the `info` node and `prompt` node and the conditional edge to route between them.\
\
I'm guessing this is a kind of hack to make things work in the framework of tools but its not clear and maybe some explanation in the sample would clear it up.\
\
Thanks\
\
1\
\
0 replies\
\
[![@RafaelRViana](https://avatars.githubusercontent.com/u/520424?u=79b4e227eab25704da151c1ccc43c1bc3d54c3c6&v=4)RafaelRViana](https://github.com/RafaelRViana) [Sep 3, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10526205)\
\
Contributor\
\
Did anybody understand how variables, constraints and requirements inside PromptInstructions were filled?\
\
1\
\
1 reply\
\
[![@haimh](https://avatars.githubusercontent.com/u/5346314?v=4)](https://github.com/haimh)\
\
[haimh](https://github.com/haimh) [Sep 5, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10554700)\
\
They were filled through collaboration between Pydantic class interaction with model (bind.tool). For more detail, you should print out the `tool_call` in function `get_prompt_messages0` for further info.\
\
Hope that help,\
\
Richard.\
\
[![@cris-m](https://avatars.githubusercontent.com/u/29815096?u=4b55bcd0d0e557e3cc2a483bfd427627d7e52493&v=4)cris-m](https://github.com/cris-m) [Oct 16, 2024](https://github.com/langchain-ai/langgraph/discussions/501#discussioncomment-10953987)\
\
there is issue with this example. I am getting the following exception:\
\
```notranslate\
/usr/local/lib/python3.10/dist-packages/anthropic/_base_client.py in _request(self, cast_to, options, retries_taken, stream, stream_cls)\
   1056\
   1057             log.debug("Re-raising status error")\
-> 1058             raise self._make_status_error_from_response(err.response) from None\
   1059\
   1060         return self._process_response(\
\
BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages: at least one message is required'}}\
\
```\
\
this is the tool called from `get_prompt_messages`:\
\
```\
{'name': 'PromptInstructions', 'args': {'objective': 1, 'variables': ['rag'], 'constraints': [], 'requirements': []}, 'id': 'toolu_011mh6syf4XjdP91GC8oaiv9', 'type': 'tool_call'}\
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
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Fchatbots%2Finformation-gather-prompting%2F)