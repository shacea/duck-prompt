[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/#how-to-view-and-update-past-graph-state)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/human_in_the_loop/time-travel.ipynb "Edit this page")

# How to view and update past graph state [¶](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/\#how-to-view-and-update-past-graph-state "Permanent link")

Prerequisites

This guide assumes familiarity with the following concepts:

- [Time Travel](https://langchain-ai.github.io/langgraph/concepts/time-travel)
- [Breakpoints](https://langchain-ai.github.io/langgraph/concepts/breakpoints)
- [LangGraph Glossary](https://langchain-ai.github.io/langgraph/concepts/low_level)

Once you start [checkpointing](https://langchain-ai.github.io/langgraph/how-tos/persistence) your graphs, you can easily **get** or **update** the state of the agent at any point in time. This permits a few things:

1. You can surface a state during an interrupt to a user to let them accept an action.
2. You can **rewind** the graph to reproduce or avoid issues.
3. You can **modify** the state to embed your agent into a larger system, or to let the user better control its actions.

The key methods used for this functionality are:

- [get\_state](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.graph.CompiledGraph.get_state): fetch the values from the target config
- [update\_state](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.graph.CompiledGraph.update_state): apply the given values to the target state

**Note:** this requires passing in a checkpointer.

Below is a quick example.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/\#setup "Permanent link")

First we need to install the packages required

```md-code__content
%%capture --no-stderr
%pip install --quiet -U langgraph langchain_openai

```

Next, we need to set API keys for OpenAI (the LLM we will use)

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")

```

```md-code__content
ANTHROPIC_API_KEY:  ········

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Build the agent [¶](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/\#build-the-agent "Permanent link")

We can now build the agent. We will build a relatively simple ReAct-style agent that does tool calling. We will use Anthropic's models and fake tools (just for demo purposes).

API Reference: [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [ToolNode](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.ToolNode) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver)

```md-code__content
# Set up the tool
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import MessagesState, START
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

@tool
def play_song_on_spotify(song: str):
    """Play a song on Spotify"""
    # Call the spotify API ...
    return f"Successfully played {song} on Spotify!"

@tool
def play_song_on_apple(song: str):
    """Play a song on Apple Music"""
    # Call the apple music API ...
    return f"Successfully played {song} on Apple Music!"

tools = [play_song_on_apple, play_song_on_spotify]
tool_node = ToolNode(tools)

# Set up the model

model = ChatOpenAI(model="gpt-4o-mini")
model = model.bind_tools(tools, parallel_tool_calls=False)

# Define nodes and conditional edges

# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"

# Define the function that calls the model
def call_model(state):
    messages = state["messages"]
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}

# Define a new graph
workflow = StateGraph(MessagesState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.add_edge(START, "agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
    {
        # If `tools`, then we call the tool node.
        "continue": "action",
        # Otherwise we finish.
        "end": END,
    },
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("action", "agent")

# Set up memory
memory = MemorySaver()

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable

# We add in `interrupt_before=["action"]`
# This will add a breakpoint before the `action` node is called
app = workflow.compile(checkpointer=memory)

```

## Interacting with the Agent [¶](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/\#interacting-with-the-agent "Permanent link")

We can now interact with the agent. Let's ask it to play Taylor Swift's most popular song:

API Reference: [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html)

```md-code__content
from langchain_core.messages import HumanMessage

config = {"configurable": {"thread_id": "1"}}
input_message = HumanMessage(content="Can you play Taylor Swift's most popular song?")
for event in app.stream({"messages": [input_message]}, config, stream_mode="values"):
    event["messages"][-1].pretty_print()

```

```md-code__content
================================[1m Human Message [0m=================================\
\
Can you play Taylor Swift's most popular song?\
==================================[1m Ai Message [0m==================================\
Tool Calls:\
  play_song_on_apple (call_uhGY6Fv6Mr4ZOhSokintuoD7)\
 Call ID: call_uhGY6Fv6Mr4ZOhSokintuoD7\
  Args:\
    song: Anti-Hero by Taylor Swift\
=================================[1m Tool Message [0m=================================\
Name: play_song_on_apple\
\
Succesfully played Anti-Hero by Taylor Swift on Apple Music!\
==================================[1m Ai Message [0m==================================\
\
I've successfully played "Anti-Hero" by Taylor Swift on Apple Music! Enjoy the music!\
\
```\
\
## Checking history [¶](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/\#checking-history "Permanent link")\
\
Let's browse the history of this thread, from start to finish.\
\
```md-code__content\
app.get_state(config).values["messages"]\
\
```\
\
```md-code__content\
[HumanMessage(content="Can you play Taylor Swift's most popular song?", id='7e32f0f3-75f5-48e1-a4ae-d38ccc15973b'),\
 AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'function': {'arguments': '{"song":"Anti-Hero by Taylor Swift"}', 'name': 'play_song_on_apple'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 22, 'prompt_tokens': 80, 'total_tokens': 102}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_483d39d857', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-af077bc4-f03c-4afe-8d92-78bdae394412-0', tool_calls=[{'name': 'play_song_on_apple', 'args': {'song': 'Anti-Hero by Taylor Swift'}, 'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'type': 'tool_call'}], usage_metadata={'input_tokens': 80, 'output_tokens': 22, 'total_tokens': 102}),\
 ToolMessage(content='Succesfully played Anti-Hero by Taylor Swift on Apple Music!', name='play_song_on_apple', id='43a39ca7-326a-4033-8607-bf061615ed6b', tool_call_id='call_uhGY6Fv6Mr4ZOhSokintuoD7'),\
 AIMessage(content='I\'ve successfully played "Anti-Hero" by Taylor Swift on Apple Music! Enjoy the music!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 20, 'prompt_tokens': 126, 'total_tokens': 146}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_483d39d857', 'finish_reason': 'stop', 'logprobs': None}, id='run-bfee6b28-9f16-49cc-8d28-bfb5a5b9aea1-0', usage_metadata={'input_tokens': 126, 'output_tokens': 20, 'total_tokens': 146})]\
\
```\
\
```md-code__content\
all_states = []\
for state in app.get_state_history(config):\
    print(state)\
    all_states.append(state)\
    print("--")\
\
```\
\
```md-code__content\
StateSnapshot(values={'messages': [HumanMessage(content="Can you play Taylor Swift's most popular song?", id='7e32f0f3-75f5-48e1-a4ae-d38ccc15973b'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'function': {'arguments': '{"song":"Anti-Hero by Taylor Swift"}', 'name': 'play_song_on_apple'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 22, 'prompt_tokens': 80, 'total_tokens': 102}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_483d39d857', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-af077bc4-f03c-4afe-8d92-78bdae394412-0', tool_calls=[{'name': 'play_song_on_apple', 'args': {'song': 'Anti-Hero by Taylor Swift'}, 'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'type': 'tool_call'}], usage_metadata={'input_tokens': 80, 'output_tokens': 22, 'total_tokens': 102}), ToolMessage(content='Succesfully played Anti-Hero by Taylor Swift on Apple Music!', name='play_song_on_apple', id='43a39ca7-326a-4033-8607-bf061615ed6b', tool_call_id='call_uhGY6Fv6Mr4ZOhSokintuoD7'), AIMessage(content='I\'ve successfully played "Anti-Hero" by Taylor Swift on Apple Music! Enjoy the music!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 20, 'prompt_tokens': 126, 'total_tokens': 146}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_483d39d857', 'finish_reason': 'stop', 'logprobs': None}, id='run-bfee6b28-9f16-49cc-8d28-bfb5a5b9aea1-0', usage_metadata={'input_tokens': 126, 'output_tokens': 20, 'total_tokens': 146})]}, next=(), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6bcf1-364f-6228-8003-dd67a426334e'}}, metadata={'source': 'loop', 'writes': {'agent': {'messages': [AIMessage(content='I\'ve successfully played "Anti-Hero" by Taylor Swift on Apple Music! Enjoy the music!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 20, 'prompt_tokens': 126, 'total_tokens': 146}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_483d39d857', 'finish_reason': 'stop', 'logprobs': None}, id='run-bfee6b28-9f16-49cc-8d28-bfb5a5b9aea1-0', usage_metadata={'input_tokens': 126, 'output_tokens': 20, 'total_tokens': 146})]}}, 'step': 3, 'parents': {}}, created_at='2024-09-05T21:37:39.955948+00:00', parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6bcf1-318f-6dc8-8002-dbdf9aaeac83'}}, tasks=())\
--\
StateSnapshot(values={'messages': [HumanMessage(content="Can you play Taylor Swift's most popular song?", id='7e32f0f3-75f5-48e1-a4ae-d38ccc15973b'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'function': {'arguments': '{"song":"Anti-Hero by Taylor Swift"}', 'name': 'play_song_on_apple'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 22, 'prompt_tokens': 80, 'total_tokens': 102}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_483d39d857', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-af077bc4-f03c-4afe-8d92-78bdae394412-0', tool_calls=[{'name': 'play_song_on_apple', 'args': {'song': 'Anti-Hero by Taylor Swift'}, 'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'type': 'tool_call'}], usage_metadata={'input_tokens': 80, 'output_tokens': 22, 'total_tokens': 102}), ToolMessage(content='Succesfully played Anti-Hero by Taylor Swift on Apple Music!', name='play_song_on_apple', id='43a39ca7-326a-4033-8607-bf061615ed6b', tool_call_id='call_uhGY6Fv6Mr4ZOhSokintuoD7')]}, next=('agent',), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6bcf1-318f-6dc8-8002-dbdf9aaeac83'}}, metadata={'source': 'loop', 'writes': {'action': {'messages': [ToolMessage(content='Succesfully played Anti-Hero by Taylor Swift on Apple Music!', name='play_song_on_apple', id='43a39ca7-326a-4033-8607-bf061615ed6b', tool_call_id='call_uhGY6Fv6Mr4ZOhSokintuoD7')]}}, 'step': 2, 'parents': {}}, created_at='2024-09-05T21:37:39.458185+00:00', parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6bcf1-3185-663e-8001-12b1ec3114b8'}}, tasks=(PregelTask(id='3a4c5ddb-14b2-5def-a766-02ddc32948ba', name='agent', error=None, interrupts=(), state=None),))\
--\
StateSnapshot(values={'messages': [HumanMessage(content="Can you play Taylor Swift's most popular song?", id='7e32f0f3-75f5-48e1-a4ae-d38ccc15973b'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'function': {'arguments': '{"song":"Anti-Hero by Taylor Swift"}', 'name': 'play_song_on_apple'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 22, 'prompt_tokens': 80, 'total_tokens': 102}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_483d39d857', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-af077bc4-f03c-4afe-8d92-78bdae394412-0', tool_calls=[{'name': 'play_song_on_apple', 'args': {'song': 'Anti-Hero by Taylor Swift'}, 'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'type': 'tool_call'}], usage_metadata={'input_tokens': 80, 'output_tokens': 22, 'total_tokens': 102})]}, next=('action',), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6bcf1-3185-663e-8001-12b1ec3114b8'}}, metadata={'source': 'loop', 'writes': {'agent': {'messages': [AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'function': {'arguments': '{"song":"Anti-Hero by Taylor Swift"}', 'name': 'play_song_on_apple'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 22, 'prompt_tokens': 80, 'total_tokens': 102}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_483d39d857', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-af077bc4-f03c-4afe-8d92-78bdae394412-0', tool_calls=[{'name': 'play_song_on_apple', 'args': {'song': 'Anti-Hero by Taylor Swift'}, 'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'type': 'tool_call'}], usage_metadata={'input_tokens': 80, 'output_tokens': 22, 'total_tokens': 102})]}}, 'step': 1, 'parents': {}}, created_at='2024-09-05T21:37:39.453898+00:00', parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6bcf1-29b8-6370-8000-f9f6e7ca1b06'}}, tasks=(PregelTask(id='01f1dc72-5a39-5876-97a6-abdc12f70c2a', name='action', error=None, interrupts=(), state=None),))\
--\
StateSnapshot(values={'messages': [HumanMessage(content="Can you play Taylor Swift's most popular song?", id='7e32f0f3-75f5-48e1-a4ae-d38ccc15973b')]}, next=('agent',), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6bcf1-29b8-6370-8000-f9f6e7ca1b06'}}, metadata={'source': 'loop', 'writes': None, 'step': 0, 'parents': {}}, created_at='2024-09-05T21:37:38.635849+00:00', parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6bcf1-29b3-6514-bfff-fe07fb36f14f'}}, tasks=(PregelTask(id='348e1ba7-95c6-5b89-80c9-1fc4720e35ef', name='agent', error=None, interrupts=(), state=None),))\
--\
StateSnapshot(values={'messages': []}, next=('__start__',), config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef6bcf1-29b3-6514-bfff-fe07fb36f14f'}}, metadata={'source': 'input', 'writes': {'__start__': {'messages': [HumanMessage(content="Can you play Taylor Swift's most popular song?")]}}, 'step': -1, 'parents': {}}, created_at='2024-09-05T21:37:38.633849+00:00', parent_config=None, tasks=(PregelTask(id='f1cfbb8c-7792-5cf9-9d28-ae3ac7724cf3', name='__start__', error=None, interrupts=(), state=None),))\
--\
\
```\
\
## Replay a state [¶](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/\#replay-a-state "Permanent link")\
\
We can go back to any of these states and restart the agent from there! Let's go back to right before the tool call gets executed.\
\
```md-code__content\
to_replay = all_states[2]\
\
```\
\
```md-code__content\
to_replay.values\
\
```\
\
```md-code__content\
{'messages': [HumanMessage(content="Can you play Taylor Swift's most popular song?", id='7e32f0f3-75f5-48e1-a4ae-d38ccc15973b'),\
  AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'function': {'arguments': '{"song":"Anti-Hero by Taylor Swift"}', 'name': 'play_song_on_apple'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 22, 'prompt_tokens': 80, 'total_tokens': 102}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_483d39d857', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-af077bc4-f03c-4afe-8d92-78bdae394412-0', tool_calls=[{'name': 'play_song_on_apple', 'args': {'song': 'Anti-Hero by Taylor Swift'}, 'id': 'call_uhGY6Fv6Mr4ZOhSokintuoD7', 'type': 'tool_call'}], usage_metadata={'input_tokens': 80, 'output_tokens': 22, 'total_tokens': 102})]}\
\
```\
\
```md-code__content\
to_replay.next\
\
```\
\
```md-code__content\
('action',)\
\
```\
\
To replay from this place we just need to pass its config back to the agent. Notice that it just resumes from right where it left all - making a tool call.\
\
```md-code__content\
for event in app.stream(None, to_replay.config):\
    for v in event.values():\
        print(v)\
\
```\
\
```md-code__content\
{'messages': [ToolMessage(content='Succesfully played Anti-Hero by Taylor Swift on Apple Music!', name='play_song_on_apple', tool_call_id='call_uhGY6Fv6Mr4ZOhSokintuoD7')]}\
{'messages': [AIMessage(content='I\'ve started playing "Anti-Hero" by Taylor Swift on Apple Music! Enjoy the music!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 20, 'prompt_tokens': 126, 'total_tokens': 146}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_483d39d857', 'finish_reason': 'stop', 'logprobs': None}, id='run-dc338bbd-d623-40bb-b824-5d2307954b57-0', usage_metadata={'input_tokens': 126, 'output_tokens': 20, 'total_tokens': 146})]}\
\
```\
\
## Branch off a past state [¶](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/\#branch-off-a-past-state "Permanent link")\
\
Using LangGraph's checkpointing, you can do more than just replay past states. You can branch off previous locations to let the agent explore alternate trajectories or to let a user "version control" changes in a workflow.\
\
Let's show how to do this to edit the state at a particular point in time. Let's update the state to instead of playing the song on Apple to play it on Spotify:\
\
```md-code__content\
# Let's now get the last message in the state\
# This is the one with the tool calls that we want to update\
last_message = to_replay.values["messages"][-1]\
\
# Let's now update the tool we are calling\
last_message.tool_calls[0]["name"] = "play_song_on_spotify"\
\
branch_config = app.update_state(\
    to_replay.config,\
    {"messages": [last_message]},\
)\
\
```\
\
We can then invoke with this new `branch_config` to resume running from here with changed state. We can see from the log that the tool was called with different input.\
\
```md-code__content\
for event in app.stream(None, branch_config):\
    for v in event.values():\
        print(v)\
\
```\
\
```md-code__content\
{'messages': [ToolMessage(content='Succesfully played Anti-Hero by Taylor Swift on Spotify!', name='play_song_on_spotify', tool_call_id='call_uhGY6Fv6Mr4ZOhSokintuoD7')]}\
{'messages': [AIMessage(content='I\'ve started playing "Anti-Hero" by Taylor Swift on Spotify. Enjoy the music!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 19, 'prompt_tokens': 125, 'total_tokens': 144}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_483d39d857', 'finish_reason': 'stop', 'logprobs': None}, id='run-7d8d5094-7029-4da3-9e0e-ef9d18b63615-0', usage_metadata={'input_tokens': 125, 'output_tokens': 19, 'total_tokens': 144})]}\
\
```\
\
Alternatively, we could update the state to not even call a tool!\
\
API Reference: [AIMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html)\
\
```md-code__content\
from langchain_core.messages import AIMessage\
\
# Let's now get the last message in the state\
# This is the one with the tool calls that we want to update\
last_message = to_replay.values["messages"][-1]\
\
# Let's now get the ID for the last message, and create a new message with that ID.\
new_message = AIMessage(\
    content="It's quiet hours so I can't play any music right now!", id=last_message.id\
)\
\
branch_config = app.update_state(\
    to_replay.config,\
    {"messages": [new_message]},\
)\
\
```\
\
```md-code__content\
branch_state = app.get_state(branch_config)\
\
```\
\
```md-code__content\
branch_state.values\
\
```\
\
```md-code__content\
{'messages': [HumanMessage(content="Can you play Taylor Swift's most popular song?", id='7e32f0f3-75f5-48e1-a4ae-d38ccc15973b'),\
  AIMessage(content="It's quiet hours so I can't play any music right now!", id='run-af077bc4-f03c-4afe-8d92-78bdae394412-0')]}\
\
```\
\
```md-code__content\
branch_state.next\
\
```\
\
```md-code__content\
()\
\
```\
\
You can see the snapshot was updated and now correctly reflects that there is no next step.\
\
## Comments\
\
giscus\
\
#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/882)\
\
👍1\
\
#### [6 comments](https://github.com/langchain-ai/langgraph/discussions/882)\
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
[![@ShayanTalaei](https://avatars.githubusercontent.com/u/62253512?u=0681dfd5dc7cada29002dce595a6472477be2056&v=4)ShayanTalaei](https://github.com/ShayanTalaei) [Jun 28, 2024](https://github.com/langchain-ai/langgraph/discussions/882#discussioncomment-9908169)\
\
Hi,\
\
Is it possible to use previous checkpoints even if the schema of the state has changed a bit?\
\
Let's say we had a GraphState with a field, foo, and we created some checkpoints by running our graph using this state schema. Then, we decided to add another field to the state schema, for instance bar. Now, we want to use some old checkpoints to resume the graph from an intermediate node (such that foo is according to the checkpoint and bar is in its default). Is it possible to do this?\
\
Thank you!\
\
1\
\
1 reply\
\
[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)\
\
[hinthornw](https://github.com/hinthornw) [Jun 28, 2024](https://github.com/langchain-ai/langgraph/discussions/882#discussioncomment-9908472)\
\
Contributor\
\
Yeah - schema changes are handled by whatever reducer you have.\
\
If you add a field, you'd just have to make surethat it's OK for it to start null (or if you're using a pydantic model as state, initialize it with a default value.\
\
If you drop a field, the dropped field from the previous checkpoint just wouldn't be used.\
\
If you change the type of a field, your reducer would see the previous values in the left argument and you'd need to be able to handle the migration of that type.\
\
👍1\
\
[![@riyavsinha](https://avatars.githubusercontent.com/u/33243383?u=15e456901b83fa42a0bd548e6cb2a1aed326c19c&v=4)riyavsinha](https://github.com/riyavsinha) [Jul 13, 2024](https://github.com/langchain-ai/langgraph/discussions/882#discussioncomment-10037264)\
\
Contributor\
\
How can you modify the next node to call in the graph? For example, say a user provides feedback during an interrupt-- we may want to reroute to a node to handle that feedback instead of continuing down the path.\
\
using `update_state()` doesn't seem to be able to change the actual StateSnapshot's next.\
\
1\
\
👍4\
\
0 replies\
\
[![@Eknathabhiram](https://avatars.githubusercontent.com/u/150422670?v=4)Eknathabhiram](https://github.com/Eknathabhiram) [Oct 29, 2024](https://github.com/langchain-ai/langgraph/discussions/882#discussioncomment-11085794)\
\
Hey Can you update the state in router functions? Because we can only return next node there\
\
2\
\
0 replies\
\
[![@PvH-SPC](https://avatars.githubusercontent.com/u/182779866?v=4)PvH-SPC](https://github.com/PvH-SPC) [Mar 6](https://github.com/langchain-ai/langgraph/discussions/882#discussioncomment-12413382)\
\
Hi this is great, question I am trying to figure out the deserialization process used by the get\_state function mentioned here and the response format of the state changes when streaming state changes back using StreaMode = 'values'. Specifically when using the messages array, in your state with `    messages: Annotated[list, add_messages]` when receiving using the get\_state it is well formatted json eg:\
\
"channel\_values": {\
\
"messages": \[\
\
{\
\
"content": "hi",\
\
"additional\_kwargs": {\
\
```notranslate\
    },\
    "response_metadata": {\
\
    },\
    "type": "human",\
    "name": null,\
    "id": "b5bf6178-bad4-4e47-9e60-01c98ce16374",\
    "example": false\
  },\
\
```\
\
however when getting the events back, while they are proper python objects, how do you get them to the format that matches the state returned from the state store? EG we are getting this:\
\
{'messages': \[{'lc': 1, 'type': 'constructor', 'id': \['langchain', 'schema', 'messages', 'HumanMessage'\], 'kwargs': {'content': 'hi', 'type': 'human', 'id': 'b5bf6178-bad4-4e47-9e60-01c98ce16374'}}\]}\
\
I have tried using the various loaders (from langchain\_core.load.dump import default, dumpd, dumps), id really like to stay clear of building custom code for this, as in theory it seems logical that the representation format of getting the full state from the store/snapshot, should match exactly and easily to that returned by the state changes (either update or values).\
\
1\
\
0 replies\
\
[![@Samll-Kosmos](https://avatars.githubusercontent.com/u/47004748?v=4)Samll-Kosmos](https://github.com/Samll-Kosmos) [Mar 15](https://github.com/langchain-ai/langgraph/discussions/882#discussioncomment-12506825)\
\
Hi,\
\
What is the best way to obtain all the node names that have been already executed?\
\
1\
\
1 reply\
\
[![@misterworker](https://avatars.githubusercontent.com/u/178368791?u=9f36401d40b14b999c21d2b673d8c9e4ea1ae11c&v=4)](https://github.com/misterworker)\
\
[misterworker](https://github.com/misterworker) [26 days ago](https://github.com/langchain-ai/langgraph/discussions/882#discussioncomment-12660100)\
\
```notranslate\
    for state in graph.get_state_history(config):\
        print("Num Messages: ", len(state.values["messages"]), "Next: ", state.next)\
        print("-" * 80)\
\
```\
\
[![@sivaTwks010928](https://avatars.githubusercontent.com/u/178696152?v=4)sivaTwks010928](https://github.com/sivaTwks010928) [10 days ago](https://github.com/langchain-ai/langgraph/discussions/882#discussioncomment-12823754)\
\
Let’s say I’m using interrupt from langgraph.types inside some nodes of a subgraph. I have two subgraphs, both of which contain nodes that use interrupt, and I’ve combined them into a parent graph (each subgraph is compiled into a node in the parent graph).\
\
Now, suppose I want to "travel back in time" — meaning I want the user to be able to select a checkpoint to return to, and then resume execution from that point, potentially following a different path than the original one.\
\
How can I implement this kind of behavior, especially considering that the subgraphs are already compiled into the parent graph?\
\
1\
\
0 replies\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fhuman_in_the_loop%2Ftime-travel%2F)