[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/multi-agent-multi-turn-convo/#how-to-add-multi-turn-conversation-in-a-multi-agent-application)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/multi-agent-multi-turn-convo.ipynb "Edit this page")

# How to add multi-turn conversation in a multi-agent application [¶](https://langchain-ai.github.io/langgraph/how-tos/multi-agent-multi-turn-convo/\#how-to-add-multi-turn-conversation-in-a-multi-agent-application "Permanent link")

Prerequisites

This guide assumes familiarity with the following:

- [How to implement handoffs between agents](https://langchain-ai.github.io/langgraph/how-tos/agent-handoffs)
- [Multi-agent systems](https://langchain-ai.github.io/langgraph/concepts/multi_agent)
- [Human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop)
- [Command](https://langchain-ai.github.io/langgraph/concepts/low_level/#command)
- [LangGraph Glossary](https://langchain-ai.github.io/langgraph/concepts/low_level/)

In this how-to guide, we’ll build an application that allows an end-user to engage in a _multi-turn conversation_ with one or more agents. We'll create a node that uses an [`interrupt`](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.interrupt) to collect user input and routes back to the **active** agent.

The agents will be implemented as nodes in a graph that executes agent steps and determines the next action:

1. **Wait for user input** to continue the conversation, or
2. **Route to another agent** (or back to itself, such as in a loop) via a [**handoff**](https://langchain-ai.github.io/langgraph/concepts/multi_agent/#handoffs).

```md-code__content
def human(state: MessagesState) -> Command[Literal["agent", "another_agent"]]:
    """A node for collecting user input."""
    user_input = interrupt(value="Ready for user input.")

    # Determine the active agent.
    active_agent = ...

    ...
    return Command(
        update={
            "messages": [{\
                "role": "human",\
                "content": user_input,\
            }]
        },
        goto=active_agent
    )

def agent(state) -> Command[Literal["agent", "another_agent", "human"]]:
    # The condition for routing/halting can be anything, e.g. LLM tool call / structured output, etc.
    goto = get_next_agent(...)  # 'agent' / 'another_agent'
    if goto:
        return Command(goto=goto, update={"my_state_key": "my_state_value"})
    else:
        return Command(goto="human") # Go to human node

```

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/multi-agent-multi-turn-convo/\#setup "Permanent link")

First, let's install the required packages

```md-code__content
%%capture --no-stderr
%pip install -U langgraph langchain-anthropic

```

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("ANTHROPIC_API_KEY")

```

```md-code__content
ANTHROPIC_API_KEY:  ········

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Define agents [¶](https://langchain-ai.github.io/langgraph/how-tos/multi-agent-multi-turn-convo/\#define-agents "Permanent link")

In this example, we will build a team of travel assistant agents that can communicate with each other via handoffs.

We will create 2 agents:

- `travel_advisor`: can help with travel destination recommendations. Can ask `hotel_advisor` for help.
- `hotel_advisor`: can help with hotel recommendations. Can ask `travel_advisor` for help.

We will be using prebuilt [`create_react_agent`](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent "<code class=\"doc-symbol doc-symbol-heading doc-symbol-function\"></code>            <span class=\"doc doc-object-name doc-function-name\">create_react_agent</span>") for the agents - each agent will have tools specific to its area of expertise as well as a special [tool for handoffs](https://langchain-ai.github.io/langgraph/how-tos/agent-handoffs#implementing-handoffs-using-tools) to another agent.

First, let's define the tools we'll be using:

API Reference: [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [InjectedToolCallId](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.base.InjectedToolCallId.html) \| [InjectedState](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.InjectedState)

```md-code__content
import random
from typing import Annotated, Literal

from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState

@tool
def get_travel_recommendations():
    """Get recommendation for travel destinations"""
    return random.choice(["aruba", "turks and caicos"])

@tool
def get_hotel_recommendations(location: Literal["aruba", "turks and caicos"]):
    """Get hotel recommendations for a given destination."""
    return {
        "aruba": [\
            "The Ritz-Carlton, Aruba (Palm Beach)"\
            "Bucuti & Tara Beach Resort (Eagle Beach)"\
        ],
        "turks and caicos": ["Grace Bay Club", "COMO Parrot Cay"],
    }[location]

def make_handoff_tool(*, agent_name: str):
    """Create a tool that can return handoff via a Command"""
    tool_name = f"transfer_to_{agent_name}"

    @tool(tool_name)
    def handoff_to_agent(
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        """Ask another agent for help."""
        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": tool_name,
            "tool_call_id": tool_call_id,
        }
        return Command(
            # navigate to another agent node in the PARENT graph
            goto=agent_name,
            graph=Command.PARENT,
            # This is the state update that the agent `agent_name` will see when it is invoked.
            # We're passing agent's FULL internal message history AND adding a tool message to make sure
            # the resulting chat history is valid.
            update={"messages": state["messages"] + [tool_message]},
        )

    return handoff_to_agent

```

Let's now create our agents using the the prebuilt [`create_react_agent`](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent "<code class=\"doc-symbol doc-symbol-heading doc-symbol-function\"></code>            <span class=\"doc doc-object-name doc-function-name\">create_react_agent</span>"). We'll also define a dedicated `human` node with an [`interrupt`](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.interrupt "<code class=\"doc-symbol doc-symbol-heading doc-symbol-function\"></code>            <span class=\"doc doc-object-name doc-function-name\">interrupt</span>") \-\- we will route to this node after the final response from the agents. Note that to do so we're wrapping each agent invocation in a separate node function that returns `Command(goto="human", ...)`.

API Reference: [ChatAnthropic](https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) \| [InjectedState](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.InjectedState) \| [Command](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Command) \| [interrupt](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.interrupt) \| [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver)

```md-code__content
from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver

model = ChatAnthropic(model="claude-3-5-sonnet-latest")

# Define travel advisor tools and ReAct agent
travel_advisor_tools = [\
    get_travel_recommendations,\
    make_handoff_tool(agent_name="hotel_advisor"),\
]
travel_advisor = create_react_agent(
    model,
    travel_advisor_tools,
    prompt=(
        "You are a general travel expert that can recommend travel destinations (e.g. countries, cities, etc). "
        "If you need hotel recommendations, ask 'hotel_advisor' for help. "
        "You MUST include human-readable response before transferring to another agent."
    ),
)

def call_travel_advisor(
    state: MessagesState,
) -> Command[Literal["hotel_advisor", "human"]]:
    # You can also add additional logic like changing the input to the agent / output from the agent, etc.
    # NOTE: we're invoking the ReAct agent with the full history of messages in the state
    response = travel_advisor.invoke(state)
    return Command(update=response, goto="human")

# Define hotel advisor tools and ReAct agent
hotel_advisor_tools = [\
    get_hotel_recommendations,\
    make_handoff_tool(agent_name="travel_advisor"),\
]
hotel_advisor = create_react_agent(
    model,
    hotel_advisor_tools,
    prompt=(
        "You are a hotel expert that can provide hotel recommendations for a given destination. "
        "If you need help picking travel destinations, ask 'travel_advisor' for help."
        "You MUST include human-readable response before transferring to another agent."
    ),
)

def call_hotel_advisor(
    state: MessagesState,
) -> Command[Literal["travel_advisor", "human"]]:
    response = hotel_advisor.invoke(state)
    return Command(update=response, goto="human")

def human_node(
    state: MessagesState, config
) -> Command[Literal["hotel_advisor", "travel_advisor", "human"]]:
    """A node for collecting user input."""

    user_input = interrupt(value="Ready for user input.")

    # identify the last active agent
    # (the last active node before returning to human)
    langgraph_triggers = config["metadata"]["langgraph_triggers"]
    if len(langgraph_triggers) != 1:
        raise AssertionError("Expected exactly 1 trigger in human node")

    active_agent = langgraph_triggers[0].split(":")[1]

    return Command(
        update={
            "messages": [\
                {\
                    "role": "human",\
                    "content": user_input,\
                }\
            ]
        },
        goto=active_agent,
    )

builder = StateGraph(MessagesState)
builder.add_node("travel_advisor", call_travel_advisor)
builder.add_node("hotel_advisor", call_hotel_advisor)

# This adds a node to collect human input, which will route
# back to the active agent.
builder.add_node("human", human_node)

# We'll always start with a general travel advisor.
builder.add_edge(START, "travel_advisor")

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

```

```md-code__content
from IPython.display import display, Image

display(Image(graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

## Test multi-turn conversation [¶](https://langchain-ai.github.io/langgraph/how-tos/multi-agent-multi-turn-convo/\#test-multi-turn-conversation "Permanent link")

Let's test a multi turn conversation with this application.

```md-code__content
import uuid

thread_config = {"configurable": {"thread_id": uuid.uuid4()}}

inputs = [\
    # 1st round of conversation,\
    {\
        "messages": [\
            {"role": "user", "content": "i wanna go somewhere warm in the caribbean"}\
        ]\
    },\
    # Since we're using `interrupt`, we'll need to resume using the Command primitive.\
    # 2nd round of conversation,\
    Command(\
        resume="could you recommend a nice hotel in one of the areas and tell me which area it is."\
    ),\
    # 3rd round of conversation,\
    Command(\
        resume="i like the first one. could you recommend something to do near the hotel?"\
    ),\
]

for idx, user_input in enumerate(inputs):
    print()
    print(f"--- Conversation Turn {idx + 1} ---")
    print()
    print(f"User: {user_input}")
    print()
    for update in graph.stream(
        user_input,
        config=thread_config,
        stream_mode="updates",
    ):
        for node_id, value in update.items():
            if isinstance(value, dict) and value.get("messages", []):
                last_message = value["messages"][-1]
                if isinstance(last_message, dict) or last_message.type != "ai":
                    continue
                print(f"{node_id}: {last_message.content}")

```

```md-code__content
--- Conversation Turn 1 ---

User: {'messages': [{'role': 'user', 'content': 'i wanna go somewhere warm in the caribbean'}]}

travel_advisor: Based on the recommendations, I suggest considering Aruba! It's a fantastic Caribbean destination known for its perfect warm weather year-round, with average temperatures around 82°F (28°C). Aruba is famous for its pristine white-sand beaches, crystal-clear waters, and constant cooling trade winds.

Some highlights of Aruba include:
1. Beautiful Eagle Beach and Palm Beach
2. Excellent snorkeling and diving opportunities
3. Vibrant culture and dining scene
4. Consistent sunny weather (it's outside the hurricane belt!)
5. Great shopping and nightlife in Oranjestad

Would you like me to help you explore more specific aspects of visiting Aruba? Or if you're interested in finding a hotel there, I can connect you with our hotel advisor who can provide detailed accommodation recommendations.

--- Conversation Turn 2 ---

User: Command(resume='could you recommend a nice hotel in one of the areas and tell me which area it is.')

hotel_advisor: Based on the recommendations, I can suggest two excellent options in different areas:

1. The Ritz-Carlton, Aruba - Located in Palm Beach
This luxury resort is situated in the bustling Palm Beach area, known for its high-rise hotels and vibrant atmosphere. The Ritz offers world-class amenities, including a luxurious spa, multiple restaurants, and a casino. The location is perfect if you want to be close to shopping, dining, and nightlife.

2. Bucuti & Tara Beach Resort - Located in Eagle Beach
This adults-only boutique resort is situated on the stunning Eagle Beach, which is wider and generally quieter than Palm Beach. It's perfect for those seeking a more peaceful, romantic atmosphere. The resort is known for its exceptional service and sustainability practices.

Would you like more specific information about either of these hotels or their locations?

--- Conversation Turn 3 ---

User: Command(resume='i like the first one. could you recommend something to do near the hotel?')

travel_advisor: Near The Ritz-Carlton in Palm Beach, there are several excellent activities you can enjoy:

1. Palm Beach Strip - Right outside the hotel, you can walk along this vibrant strip featuring:
   - High-end shopping at luxury boutiques
   - Various restaurants and bars
   - The Paseo Herencia Shopping & Entertainment Center

2. Water Activities (within walking distance):
   - Snorkeling at the artificial reef
   - Parasailing
   - Jet ski rentals
   - Catamaran sailing trips
   - Paddleboarding

3. Nearby Attractions:
   - Bubali Bird Sanctuary (5-minute drive)
   - Butterfly Farm (10-minute walk)
   - California Lighthouse (short drive)
   - Visit the famous Stellaris Casino (located within the Ritz-Carlton)

4. Local Culture:
   - Visit the nearby fishing pier
   - Take a short trip to local craft markets
   - Evening sunset watching on the beach

Would you like more specific information about any of these activities? I can also recommend some specific restaurants or shopping venues in the area!

```

## Comments

giscus

#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/3750)

❤️1

#### [1 comment](https://github.com/langchain-ai/langgraph/discussions/3750)

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@RamziRebai](https://avatars.githubusercontent.com/u/92611463?u=184c101b1a6d3d7bfb8e1f320f277c04dc766508&v=4)RamziRebai](https://github.com/RamziRebai) [Mar 8](https://github.com/langchain-ai/langgraph/discussions/3750#discussioncomment-12436755)

I appreciate the detailed explanation and implementation of multi-turn conversations in a multi-agent application using the LangGraph functional API. The structured approach you outlined with interrupt is insightful for managing dynamic agent interactions.

However, I wanted to share an alternative approach that achieves the same functionalities—handling multi-turn interactions and routing back to the active agent—without requiring interrupt. Instead, I use a global state management system that keeps track of the active agent for each conversation thread, ensuring smooth handovers between agents.

Below is a shortened version of my solution:

```notranslate
global_store = {}

def return_state(user_id: str, default_state: dict) -> dict:
    """
    Returns the state associated with user_id from the global_store.
    If not present, initializes it with a copy of default_state.
    Using .copy() with setdefault ensures that a new default dictionary is created for every new user_id.
    This way, the global_store correctly maintains separate states for each user without risk of cross-contamination of data.
    """
    return global_store.setdefault(user_id, default_state.copy())

@entrypoint(checkpointer=memory_within_thread)
def workflow(messages: list[BaseMessage], *, previous: list[BaseMessage], config: RunnableConfig):

    if previous is not None:
        messages = add_messages(previous, messages)

    user_id = config['configurable']['thread_id']
    current_state = return_state(user_id, {})

    last_active_agent = current_state.get("agent", travel_advisor_agent_task)

    while True:
        last_active_agent = current_state.get("agent", travel_advisor_agent_task)
        llm_response = last_active_agent(messages).result()
        messages = add_messages(messages, llm_response)

        ai_msg = next(m for m in reversed(messages) if isinstance(m, AIMessage))

        if ai_msg.tool_calls == []:
            break
        else:
            # Update the active agent based on the last tool call.
            last_tool = ai_msg.tool_calls[-1]
            if last_tool['name'] == 'route_to_travel_advisor_agent':
                current_state['agent'] = travel_advisor_agent_task
            elif last_tool['name'] == 'route_to_hotel_recommendations_agent':
                current_state['agent'] = hotel_recommendations_agent_task

        current_state = return_state(config['configurable']['thread_id'], current_state)

    return entrypoint.final(value=llm_response[-1], save=messages)

```

I would love to hear your thoughts on this approach. Do you see any potential limitations or areas for improvement compared to using interrupt? Looking forward to your feedback!

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fmulti-agent-multi-turn-convo%2F)