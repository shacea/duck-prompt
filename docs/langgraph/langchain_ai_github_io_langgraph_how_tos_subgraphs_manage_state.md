[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/#how-to-view-and-update-state-in-subgraphs)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/subgraphs-manage-state.ipynb "Edit this page")

# How to view and update state in subgraphs [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/\#how-to-view-and-update-state-in-subgraphs "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [Subgraphs](https://langchain-ai.github.io/langgraph/concepts/low_level/#subgraphs)
- [Human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- [State](https://langchain-ai.github.io/langgraph/concepts/low_level/#state)

Once you add [persistence](https://langchain-ai.github.io/langgraph/how-tos/subgraph-persistence), you can easily view and update the state of the subgraph at any point in time. This enables a lot of the human-in-the-loop interaction patterns:

- You can surface a state during an interrupt to a user to let them accept an action.
- You can rewind the subgraph to reproduce or avoid issues.
- You can modify the state to let the user better control its actions.

This guide shows how you can do this.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/\#setup "Permanent link")

First, let's install the required packages

```md-code__content
%%capture --no-stderr
%pip install -U langgraph

```

Next, we need to set API keys for OpenAI (the LLM we will use):

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


## Define subgraph [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/\#define-subgraph "Permanent link")

First, let's set up our subgraph. For this, we will create a simple graph that can get the weather for a specific city. We will compile this graph with a [breakpoint](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/breakpoints/) before the `weather_node`:

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html)

```md-code__content
from langgraph.graph import StateGraph, END, START, MessagesState
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

@tool
def get_weather(city: str):
    """Get the weather for a specific city"""
    return f"It's sunny in {city}!"

raw_model = ChatOpenAI(model="gpt-4o")
model = raw_model.with_structured_output(get_weather)

class SubGraphState(MessagesState):
    city: str

def model_node(state: SubGraphState):
    result = model.invoke(state["messages"])
    return {"city": result["city"]}

def weather_node(state: SubGraphState):
    result = get_weather.invoke({"city": state["city"]})
    return {"messages": [{"role": "assistant", "content": result}]}

subgraph = StateGraph(SubGraphState)
subgraph.add_node(model_node)
subgraph.add_node(weather_node)
subgraph.add_edge(START, "model_node")
subgraph.add_edge("model_node", "weather_node")
subgraph.add_edge("weather_node", END)
subgraph = subgraph.compile(interrupt_before=["weather_node"])

```

## Define parent graph [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/\#define-parent-graph "Permanent link")

We can now setup the overall graph. This graph will first route to the subgraph if it needs to get the weather, otherwise it will route to a normal LLM.

API Reference: [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver)

```md-code__content
from typing import Literal
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

class RouterState(MessagesState):
    route: Literal["weather", "other"]

class Router(TypedDict):
    route: Literal["weather", "other"]

router_model = raw_model.with_structured_output(Router)

def router_node(state: RouterState):
    system_message = "Classify the incoming query as either about weather or not."
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    route = router_model.invoke(messages)
    return {"route": route["route"]}

def normal_llm_node(state: RouterState):
    response = raw_model.invoke(state["messages"])
    return {"messages": [response]}

def route_after_prediction(
    state: RouterState,
) -> Literal["weather_graph", "normal_llm_node"]:
    if state["route"] == "weather":
        return "weather_graph"
    else:
        return "normal_llm_node"

graph = StateGraph(RouterState)
graph.add_node(router_node)
graph.add_node(normal_llm_node)
graph.add_node("weather_graph", subgraph)
graph.add_edge(START, "router_node")
graph.add_conditional_edges("router_node", route_after_prediction)
graph.add_edge("normal_llm_node", END)
graph.add_edge("weather_graph", END)
graph = graph.compile(checkpointer=memory)

```

```md-code__content
from IPython.display import Image, display

# Setting xray to 1 will show the internal structure of the nested graph
display(Image(graph.get_graph(xray=1).draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

Let's test this out with a normal query to make sure it works as intended!

```md-code__content
config = {"configurable": {"thread_id": "1"}}
inputs = {"messages": [{"role": "user", "content": "hi!"}]}
for update in graph.stream(inputs, config=config, stream_mode="updates"):
    print(update)

```

```md-code__content
{'router_node': {'route': 'other'}}
{'normal_llm_node': {'messages': [AIMessage(content='Hello! How can I assist you today?', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 9, 'prompt_tokens': 9, 'total_tokens': 18, 'completion_tokens_details': {'reasoning_tokens': 0}}, 'model_name': 'gpt-3.5-turbo-0125', 'system_fingerprint': None, 'finish_reason': 'stop', 'logprobs': None}, id='run-35de4577-2117-40e4-ab3b-cd2ac6e27b4c-0', usage_metadata={'input_tokens': 9, 'output_tokens': 9, 'total_tokens': 18})]}}

```

Great! We didn't ask about the weather, so we got a normal response from the LLM.

## Resuming from breakpoints [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/\#resuming-from-breakpoints "Permanent link")

Let's now look at what happens with breakpoints. Let's invoke it with a query that should get routed to the weather subgraph where we have the interrupt node.

```md-code__content
config = {"configurable": {"thread_id": "2"}}
inputs = {"messages": [{"role": "user", "content": "what's the weather in sf"}]}
for update in graph.stream(inputs, config=config, stream_mode="updates"):
    print(update)

```

```md-code__content
{'router_node': {'route': 'weather'}}

```

Note that the graph stream doesn't include subgraph events. If we want to stream subgraph events, we can pass `subgraphs=True` and get back subgraph events like so:

```md-code__content
config = {"configurable": {"thread_id": "3"}}
inputs = {"messages": [{"role": "user", "content": "what's the weather in sf"}]}
for update in graph.stream(inputs, config=config, stream_mode="values", subgraphs=True):
    print(update)

```

```md-code__content
((), {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc')]})
((), {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc')], 'route': 'weather'})
(('weather_graph:0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20',), {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc')]})
(('weather_graph:0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20',), {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc')], 'city': 'San Francisco'})

```

If we get the state now, we can see that it's paused on `weather_graph`

```md-code__content
state = graph.get_state(config)
state.next

```

```md-code__content
('weather_graph',)

```

If we look at the pending tasks for our current state, we can see that we have one task named `weather_graph`, which corresponds to the subgraph task.

```md-code__content
state.tasks

```

```md-code__content
(PregelTask(id='0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20', name='weather_graph', path=('__pregel_pull', 'weather_graph'), error=None, interrupts=(), state={'configurable': {'thread_id': '3', 'checkpoint_ns': 'weather_graph:0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20'}}),)

```

However since we got the state using the config of the parent graph, we don't have access to the subgraph state. If you look at the `state` value of the `PregelTask` above you will note that it is simply the configuration of the parent graph. If we want to actually populate the subgraph state, we can pass in `subgraphs=True` to `get_state` like so:

```md-code__content
state = graph.get_state(config, subgraphs=True)
state.tasks[0]

```

```md-code__content
PregelTask(id='0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20', name='weather_graph', path=('__pregel_pull', 'weather_graph'), error=None, interrupts=(), state=StateSnapshot(values={'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc')], 'city': 'San Francisco'}, next=('weather_node',), config={'configurable': {'thread_id': '3', 'checkpoint_ns': 'weather_graph:0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20', 'checkpoint_id': '1ef75ee0-d9c3-6242-8001-440e7a3fb19f', 'checkpoint_map': {'': '1ef75ee0-d4e8-6ede-8001-2542067239ef', 'weather_graph:0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20': '1ef75ee0-d9c3-6242-8001-440e7a3fb19f'}}}, metadata={'source': 'loop', 'writes': {'model_node': {'city': 'San Francisco'}}, 'step': 1, 'parents': {'': '1ef75ee0-d4e8-6ede-8001-2542067239ef'}}, created_at='2024-09-18T18:44:36.278105+00:00', parent_config={'configurable': {'thread_id': '3', 'checkpoint_ns': 'weather_graph:0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20', 'checkpoint_id': '1ef75ee0-d4ef-6dec-8000-5d5724f3ef73'}}, tasks=(PregelTask(id='26f4384a-41d7-5ca9-cb94-4001de62e8aa', name='weather_node', path=('__pregel_pull', 'weather_node'), error=None, interrupts=(), state=None),)))

```

Now we have access to the subgraph state! If you look at the `state` value of the `PregelTask` you can see that it has all the information we need, like the next node ( `weather_node`) and the current state values (e.g. `city`).

To resume execution, we can just invoke the outer graph as normal:

```md-code__content
for update in graph.stream(None, config=config, stream_mode="values", subgraphs=True):
    print(update)

```

```md-code__content
((), {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc')], 'route': 'weather'})
(('weather_graph:0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20',), {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc')], 'city': 'San Francisco'})
(('weather_graph:0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20',), {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc'), AIMessage(content="It's sunny in San Francisco!", additional_kwargs={}, response_metadata={}, id='c996ce37-438c-44f4-9e60-5aed8bcdae8a')], 'city': 'San Francisco'})
((), {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc'), AIMessage(content="It's sunny in San Francisco!", additional_kwargs={}, response_metadata={}, id='c996ce37-438c-44f4-9e60-5aed8bcdae8a')], 'route': 'weather'})

```

### Resuming from specific subgraph node [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/\#resuming-from-specific-subgraph-node "Permanent link")

In the example above, we were replaying from the outer graph - which automatically replayed the subgraph from whatever state it was in previously (paused before the `weather_node` in our case), but it is also possible to replay from inside a subgraph. In order to do so, we need to get the configuration from the exact subgraph state that we want to replay from.

We can do this by exploring the state history of the subgraph, and selecting the state before `model_node` \- which we can do by filtering on the `.next` parameter.

To get the state history of the subgraph, we need to first pass in

```md-code__content
parent_graph_state_before_subgraph = next(
    h for h in graph.get_state_history(config) if h.next == ("weather_graph",)
)

```

```md-code__content
subgraph_state_before_model_node = next(
    h
    for h in graph.get_state_history(parent_graph_state_before_subgraph.tasks[0].state)
    if h.next == ("model_node",)
)

# This pattern can be extended no matter how many levels deep
# subsubgraph_stat_history = next(h for h in graph.get_state_history(subgraph_state_before_model_node.tasks[0].state) if h.next == ('my_subsubgraph_node',))

```

We can confirm that we have gotten the correct state by comparing the `.next` parameter of the `subgraph_state_before_model_node`.

```md-code__content
subgraph_state_before_model_node.next

```

```md-code__content
('model_node',)

```

Perfect! We have gotten the correct state snaphshot, and we can now resume from the `model_node` inside of our subgraph:

```md-code__content
for value in graph.stream(
    None,
    config=subgraph_state_before_model_node.config,
    stream_mode="values",
    subgraphs=True,
):
    print(value)

```

```md-code__content
((), {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc')], 'route': 'weather'})
(('weather_graph:0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20',), {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc')]})
(('weather_graph:0c47aeb3-6f4d-5e68-ccf4-42bd48e8ef20',), {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='108eb27a-2cbf-48d2-a6e7-6e07e82eafbc')], 'city': 'San Francisco'})

```

Great, this subsection has shown how you can replay from any node, no matter how deeply nested it is inside your graph - a powerful tool for testing how deterministic your agent is.

## Modifying state [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/\#modifying-state "Permanent link")

### Update the state of a subgraph [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/\#update-the-state-of-a-subgraph "Permanent link")

What if we want to modify the state of a subgraph? We can do this similarly to how we [update the state of normal graphs](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/), just being careful to pass in the config of the subgraph to `update_state`.

```md-code__content
config = {"configurable": {"thread_id": "4"}}
inputs = {"messages": [{"role": "user", "content": "what's the weather in sf"}]}
for update in graph.stream(inputs, config=config, stream_mode="updates"):
    print(update)

```

```md-code__content
{'router_node': {'route': 'weather'}}

```

```md-code__content
state = graph.get_state(config, subgraphs=True)
state.values["messages"]

```

```md-code__content
[HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='05ee2159-3b25-4d6c-97d6-82beda3cabd4')]

```

In order to update the state of the **inner** graph, we need to pass the config for the **inner** graph, which we can get by accessing calling `state.tasks[0].state.config` \- since we interrupted inside the subgraph, the state of the task is just the state of the subgraph.

```md-code__content
graph.update_state(state.tasks[0].state.config, {"city": "la"})

```

```md-code__content
{'configurable': {'thread_id': '4',
  'checkpoint_ns': 'weather_graph:67f32ef7-aee0-8a20-0eb0-eeea0fd6de6e',
  'checkpoint_id': '1ef75e5a-0b00-6bc0-8002-5726e210fef4',
  'checkpoint_map': {'': '1ef75e59-1b13-6ffe-8001-0844ae748fd5',
   'weather_graph:67f32ef7-aee0-8a20-0eb0-eeea0fd6de6e': '1ef75e5a-0b00-6bc0-8002-5726e210fef4'}}}

```

We can now resume streaming the outer graph (which will resume the subgraph!) and check that we updated our search to use LA instead of SF.

```md-code__content
for update in graph.stream(None, config=config, stream_mode="updates", subgraphs=True):
    print(update)

```

```md-code__content
(('weather_graph:9e512e8e-bac5-5412-babe-fe5c12a47cc2',), {'weather_node': {'messages': [{'role': 'assistant', 'content': "It's sunny in la!"}]}})
((), {'weather_graph': {'messages': [HumanMessage(content="what's the weather in sf", id='35e331c6-eb47-483c-a63c-585877b12f5d'), AIMessage(content="It's sunny in la!", id='c3d6b224-9642-4b21-94d5-eef8dc3f2cc9')]}})

```

Fantastic! The AI responded with "It's sunny in LA!" as we expected.

### Acting as a subgraph node [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/\#acting-as-a-subgraph-node "Permanent link")

Another way we could update the state is by acting as the `weather_node` ourselves instead of editing the state before `weather_node` is ran as we did above. We can do this by passing the subgraph config and also the `as_node` argument, which allows us to update the state as if we are the node we specify. Thus by setting an interrupt before the `weather_node` and then using the update state function as the `weather_node`, the graph itself never calls `weather_node` directly but instead we decide what the output of `weather_node` should be.

```md-code__content
config = {"configurable": {"thread_id": "14"}}
inputs = {"messages": [{"role": "user", "content": "what's the weather in sf"}]}
for update in graph.stream(
    inputs, config=config, stream_mode="updates", subgraphs=True
):
    print(update)
# Graph execution should stop before the weather node
print("interrupted!")

state = graph.get_state(config, subgraphs=True)

# We update the state by passing in the message we want returned from the weather node, and make sure to use as_node
graph.update_state(
    state.tasks[0].state.config,
    {"messages": [{"role": "assistant", "content": "rainy"}]},
    as_node="weather_node",
)
for update in graph.stream(None, config=config, stream_mode="updates", subgraphs=True):
    print(update)

print(graph.get_state(config).values["messages"])

```

```md-code__content
((), {'router_node': {'route': 'weather'}})
(('weather_graph:c7eb1fc7-efab-b0e3-12ed-8586f37bc7a2',), {'model_node': {'city': 'San Francisco'}})
interrupted!
((), {'weather_graph': {'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='ad694c4e-8aac-4e1f-b5ca-790c60c1775b'), AIMessage(content='rainy', additional_kwargs={}, response_metadata={}, id='98a73aaf-3524-482a-9d07-971407df0389')]}})
[HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='ad694c4e-8aac-4e1f-b5ca-790c60c1775b'), AIMessage(content='rainy', additional_kwargs={}, response_metadata={}, id='98a73aaf-3524-482a-9d07-971407df0389')]

```

Perfect! The AI responded with the message we passed in ourselves.

### Acting as the entire subgraph [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/\#acting-as-the-entire-subgraph "Permanent link")

Lastly, we could also update the graph just acting as the **entire** subgraph. This is similar to the case above but instead of acting as just the `weather_node` we are acting as the entire subgraph. This is done by passing in the normal graph config as well as the `as_node` argument, where we specify the we are acting as the entire subgraph node.

```md-code__content
config = {"configurable": {"thread_id": "8"}}
inputs = {"messages": [{"role": "user", "content": "what's the weather in sf"}]}
for update in graph.stream(
    inputs, config=config, stream_mode="updates", subgraphs=True
):
    print(update)
# Graph execution should stop before the weather node
print("interrupted!")

# We update the state by passing in the message we want returned from the weather graph, making sure to use as_node
# Note that we don't need to pass in the subgraph config, since we aren't updating the state inside the subgraph
graph.update_state(
    config,
    {"messages": [{"role": "assistant", "content": "rainy"}]},
    as_node="weather_graph",
)
for update in graph.stream(None, config=config, stream_mode="updates"):
    print(update)

print(graph.get_state(config).values["messages"])

```

```md-code__content
((), {'router_node': {'route': 'weather'}})
(('weather_graph:53ab3fb1-23e8-5de0-acc6-9fb904fd4dc4',), {'model_node': {'city': 'San Francisco'}})
interrupted!
[HumanMessage(content="what's the weather in sf", id='64b1b683-778b-4623-b783-4a8f81322ec8'), AIMessage(content='rainy', id='c1d1a2f3-c117-41e9-8c1f-8fb0a02a3b70')]

```

Again, the AI responded with "rainy" as we expected.

## Double nested subgraphs [¶](https://langchain-ai.github.io/langgraph/how-tos/subgraphs-manage-state/\#double-nested-subgraphs "Permanent link")

This same functionality continues to work no matter the level of nesting. Here is an example of doing the same things with a double nested subgraph (although any level of nesting will work). We add another router on top of our already defined graphs.

API Reference: [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver)

```md-code__content
from typing import Literal
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

class RouterState(MessagesState):
    route: Literal["weather", "other"]

class Router(TypedDict):
    route: Literal["weather", "other"]

router_model = raw_model.with_structured_output(Router)

def router_node(state: RouterState):
    system_message = "Classify the incoming query as either about weather or not."
    messages = [{"role": "system", "content": system_message}] + state["messages"]
    route = router_model.invoke(messages)
    return {"route": route["route"]}

def normal_llm_node(state: RouterState):
    response = raw_model.invoke(state["messages"])
    return {"messages": [response]}

def route_after_prediction(
    state: RouterState,
) -> Literal["weather_graph", "normal_llm_node"]:
    if state["route"] == "weather":
        return "weather_graph"
    else:
        return "normal_llm_node"

graph = StateGraph(RouterState)
graph.add_node(router_node)
graph.add_node(normal_llm_node)
graph.add_node("weather_graph", subgraph)
graph.add_edge(START, "router_node")
graph.add_conditional_edges("router_node", route_after_prediction)
graph.add_edge("normal_llm_node", END)
graph.add_edge("weather_graph", END)
graph = graph.compile()

```

API Reference: [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver)

```md-code__content
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

class GrandfatherState(MessagesState):
    to_continue: bool

def router_node(state: GrandfatherState):
    # Dummy logic that will always continue
    return {"to_continue": True}

def route_after_prediction(state: GrandfatherState):
    if state["to_continue"]:
        return "graph"
    else:
        return END

grandparent_graph = StateGraph(GrandfatherState)
grandparent_graph.add_node(router_node)
grandparent_graph.add_node("graph", graph)
grandparent_graph.add_edge(START, "router_node")
grandparent_graph.add_conditional_edges(
    "router_node", route_after_prediction, ["graph", END]
)
grandparent_graph.add_edge("graph", END)
grandparent_graph = grandparent_graph.compile(checkpointer=MemorySaver())

```

```md-code__content
from IPython.display import Image, display

# Setting xray to 1 will show the internal structure of the nested graph
display(Image(grandparent_graph.get_graph(xray=2).draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

If we run until the interrupt, we can now see that there are snapshots of the state of all three graphs

```md-code__content
config = {"configurable": {"thread_id": "2"}}
inputs = {"messages": [{"role": "user", "content": "what's the weather in sf"}]}
for update in grandparent_graph.stream(
    inputs, config=config, stream_mode="updates", subgraphs=True
):
    print(update)

```

```md-code__content
((), {'router_node': {'to_continue': True}})
(('graph:e18ecd45-5dfb-53b0-bcb7-db793924e9a8',), {'router_node': {'route': 'weather'}})
(('graph:e18ecd45-5dfb-53b0-bcb7-db793924e9a8', 'weather_graph:12bd3069-de24-5bc6-b4f1-f39527605781'), {'model_node': {'city': 'San Francisco'}})

```

```md-code__content
state = grandparent_graph.get_state(config, subgraphs=True)
print("Grandparent State:")
print(state.values)
print("---------------")
print("Parent Graph State:")
print(state.tasks[0].state.values)
print("---------------")
print("Subgraph State:")
print(state.tasks[0].state.tasks[0].state.values)

```

```md-code__content
Grandparent State:
{'messages': [HumanMessage(content="what's the weather in sf", id='3bb28060-3d30-49a7-9f84-c90b6ada7848')], 'to_continue': True}
---------------
Parent Graph State:
{'messages': [HumanMessage(content="what's the weather in sf", id='3bb28060-3d30-49a7-9f84-c90b6ada7848')], 'route': 'weather'}
---------------
Subgraph State:
{'messages': [HumanMessage(content="what's the weather in sf", id='3bb28060-3d30-49a7-9f84-c90b6ada7848')], 'city': 'San Francisco'}

```

We can now continue, acting as the node three levels down

```md-code__content
grandparent_graph_state = state
parent_graph_state = grandparent_graph_state.tasks[0].state
subgraph_state = parent_graph_state.tasks[0].state
grandparent_graph.update_state(
    subgraph_state.config,
    {"messages": [{"role": "assistant", "content": "rainy"}]},
    as_node="weather_node",
)
for update in grandparent_graph.stream(
    None, config=config, stream_mode="updates", subgraphs=True
):
    print(update)

print(grandparent_graph.get_state(config).values["messages"])

```

```md-code__content
(('graph:e18ecd45-5dfb-53b0-bcb7-db793924e9a8',), {'weather_graph': {'messages': [HumanMessage(content="what's the weather in sf", id='3bb28060-3d30-49a7-9f84-c90b6ada7848'), AIMessage(content='rainy', id='be926b59-c647-4355-88fd-a429b9e2b420')]}})
((), {'graph': {'messages': [HumanMessage(content="what's the weather in sf", id='3bb28060-3d30-49a7-9f84-c90b6ada7848'), AIMessage(content='rainy', id='be926b59-c647-4355-88fd-a429b9e2b420')]}})
[HumanMessage(content="what's the weather in sf", id='3bb28060-3d30-49a7-9f84-c90b6ada7848'), AIMessage(content='rainy', id='be926b59-c647-4355-88fd-a429b9e2b420')]

```

As in the cases above, we can see that the AI responds with "rainy" as we expect.

We can explore the state history to see how the state of the grandparent graph was updated at each step.

```md-code__content
for state in grandparent_graph.get_state_history(config):
    print(state)
    print("-----")

```

```md-code__content
StateSnapshot(values={'messages': [HumanMessage(content="what's the weather in sf", id='5ff89e4d-8255-4d23-8b55-01633c112720'), AIMessage(content='rainy', id='7c80f847-248d-4b8f-8238-633ed757b353')], 'to_continue': True}, next=(), config={'configurable': {'thread_id': '2', 'checkpoint_ns': '', 'checkpoint_id': '1ef66f40-7a2c-6f9e-8002-a37a61b26709'}}, metadata={'source': 'loop', 'writes': {'graph': {'messages': [HumanMessage(content="what's the weather in sf", id='5ff89e4d-8255-4d23-8b55-01633c112720'), AIMessage(content='rainy', id='7c80f847-248d-4b8f-8238-633ed757b353')]}}, 'step': 2, 'parents': {}}, created_at='2024-08-30T17:19:35.793847+00:00', parent_config={'configurable': {'thread_id': '2', 'checkpoint_ns': '', 'checkpoint_id': '1ef66f3f-f312-6338-8001-766acddc781e'}}, tasks=())
-----
StateSnapshot(values={'messages': [HumanMessage(content="what's the weather in sf", id='5ff89e4d-8255-4d23-8b55-01633c112720')], 'to_continue': True}, next=('graph',), config={'configurable': {'thread_id': '2', 'checkpoint_ns': '', 'checkpoint_id': '1ef66f3f-f312-6338-8001-766acddc781e'}}, metadata={'source': 'loop', 'writes': {'router_node': {'to_continue': True}}, 'step': 1, 'parents': {}}, created_at='2024-08-30T17:19:21.627097+00:00', parent_config={'configurable': {'thread_id': '2', 'checkpoint_ns': '', 'checkpoint_id': '1ef66f3f-f303-61d0-8000-1945c8a74e9e'}}, tasks=(PregelTask(id='b59fe96f-fdce-5afe-aa58-bd2876a0d592', name='graph', error=None, interrupts=(), state={'configurable': {'thread_id': '2', 'checkpoint_ns': 'graph:b59fe96f-fdce-5afe-aa58-bd2876a0d592'}}),))
-----
StateSnapshot(values={'messages': [HumanMessage(content="what's the weather in sf", id='5ff89e4d-8255-4d23-8b55-01633c112720')]}, next=('router_node',), config={'configurable': {'thread_id': '2', 'checkpoint_ns': '', 'checkpoint_id': '1ef66f3f-f303-61d0-8000-1945c8a74e9e'}}, metadata={'source': 'loop', 'writes': None, 'step': 0, 'parents': {}}, created_at='2024-08-30T17:19:21.620923+00:00', parent_config={'configurable': {'thread_id': '2', 'checkpoint_ns': '', 'checkpoint_id': '1ef66f3f-f2f9-6d6a-bfff-c8b76e5b2462'}}, tasks=(PregelTask(id='e3d4a97a-f4ca-5260-801e-e65b02907825', name='router_node', error=None, interrupts=(), state=None),))
-----
StateSnapshot(values={'messages': []}, next=('__start__',), config={'configurable': {'thread_id': '2', 'checkpoint_ns': '', 'checkpoint_id': '1ef66f3f-f2f9-6d6a-bfff-c8b76e5b2462'}}, metadata={'source': 'input', 'writes': {'messages': [{'role': 'user', 'content': "what's the weather in sf"}]}, 'step': -1, 'parents': {}}, created_at='2024-08-30T17:19:21.617127+00:00', parent_config=None, tasks=(PregelTask(id='f0538638-b794-58fc-a406-980d2fea28a1', name='__start__', error=None, interrupts=(), state=None),))
-----

```

## Comments

giscus

#### [2 reactions](https://github.com/langchain-ai/langgraph/discussions/1728)

👍2

#### [15 comments](https://github.com/langchain-ai/langgraph/discussions/1728)

#### ·

#### 17 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@apoorvkk](https://avatars.githubusercontent.com/u/33816630?u=cc1fa561eeab52753e8068558db76470e15bac38&v=4)apoorvkk](https://github.com/apoorvkk) [Sep 16, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-10659179)

Is it possible to replay from a node within a subggraph like shown here for top level nodes? [https://langchain-ai.github.io/langgraph/how-tos/human\_in\_the\_loop/time-travel/#replay-a-state](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/#replay-a-state)

1

5 replies

[![@apoorvkk](https://avatars.githubusercontent.com/u/33816630?u=cc1fa561eeab52753e8068558db76470e15bac38&v=4)](https://github.com/apoorvkk)

[apoorvkk](https://github.com/apoorvkk) [Sep 16, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-10659734)

In addition, is it possible to replay between two different sessions?

[![@isahers1](https://avatars.githubusercontent.com/u/78627776?u=7fd9922950b898ab502666f2cea155cf0200fe5f&v=4)](https://github.com/isahers1)

[isahers1](https://github.com/isahers1) [Sep 18, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-10686001)

Contributor

I am not 100% sure what you mean by replay between two different sessions - but replaying from a node inside a subgraph is possible, we just added a PR to add this information to the docs: [#1759](https://github.com/langchain-ai/langgraph/pull/1759)

[![@apoorvkk](https://avatars.githubusercontent.com/u/33816630?u=cc1fa561eeab52753e8068558db76470e15bac38&v=4)](https://github.com/apoorvkk)

[apoorvkk](https://github.com/apoorvkk) [Sep 19, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-10691120)

ah perfect, your PR helped significantly! The second question was more to do with replaying between different script runs but that was easily solvable with external persistence like sqlite saver

[![@sivaTwks010928](https://avatars.githubusercontent.com/u/178696152?v=4)](https://github.com/sivaTwks010928)

[sivaTwks010928](https://github.com/sivaTwks010928) [11 days ago](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-12821317)

[@isahers1](https://github.com/isahers1)

Let’s say I’m using interrupt from langgraph.types inside some nodes of a subgraph. I have two subgraphs, both of which contain nodes that use interrupt, and I’ve combined them into a parent graph (each subgraph is compiled into a node in the parent graph).

Now, suppose I want to "travel back in time" — meaning I want the user to be able to select a checkpoint to return to, and then resume execution from that point, potentially following a different path than the original one.

How can I implement this kind of behavior, especially considering that the subgraphs are already compiled into the parent graph?

[![@sivaTwks010928](https://avatars.githubusercontent.com/u/178696152?v=4)](https://github.com/sivaTwks010928)

[sivaTwks010928](https://github.com/sivaTwks010928) [11 days ago](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-12821638)

[@apoorvkk](https://github.com/apoorvkk) can you help me? did you find the answer for your question in that PR?

[![@wangxinzhang](https://avatars.githubusercontent.com/u/9651225?v=4)wangxinzhang](https://github.com/wangxinzhang) [Sep 19, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-10689386)

Does the subgraph have to be pre-compiled to support being suspended and resumed，Can the subgraph as a node method support it?

1

👍1

1 reply

[![@ChatGPD](https://avatars.githubusercontent.com/u/133729112?v=4)](https://github.com/ChatGPD)

[ChatGPD](https://github.com/ChatGPD) [Dec 6, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11482107)

So far as I tested, a node method will not be able to get the subgraph state and config. I tried to use checkpointer to get last config but don't work out.

[![@gssci](https://avatars.githubusercontent.com/u/9202765?u=0704ddc407fe221f68382727d757750b568858da&v=4)gssci](https://github.com/gssci) [Sep 20, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-10704453)

Shouldn't there be a way to set a max\_recursion limit to subgraphs?

1

0 replies

[![@LiuXinke75](https://avatars.githubusercontent.com/u/155616168?v=4)LiuXinke75](https://github.com/LiuXinke75) [Sep 24, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-10735639)

## I encountered the following error. How can I fix it?

TypeError Traceback (most recent call last)

Cell In\[25\], line 1

----\> 1 state = graph.get\_state(config, subgraphs=True)

2 state.values\['messages'\]

TypeError: Pregel.get\_state() got an unexpected keyword argument 'subgraphs'

1

2 replies

[![@matteociccozzi-ah](https://avatars.githubusercontent.com/u/144736047?u=92a1e8167b9f9c328573f3af4eee029ce2049655&v=4)](https://github.com/matteociccozzi-ah)

[matteociccozzi-ah](https://github.com/matteociccozzi-ah) [Oct 8, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-10881838)

I'm also getting the same error

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Oct 8, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-10885574)

Collaborator

which langgraph version are you using? i would recommend updating to the latest

[![@jhachirag7](https://avatars.githubusercontent.com/u/70481022?v=4)jhachirag7](https://github.com/jhachirag7) [Oct 19, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-10989897)

below is the latest graph response:

```notranslate
(('GenerateKeywordsIdeas:b458982c-c182-854a-44a9-f0bcdecba8e8',), {'generator': {'messages': [AIMessage(content=[{'type': 'text', 'text': "Certainly! I'll follow the steps you've outlined to find seed keywords for neoleads.com. Let's begin with scraping the website content and then use the search tools to expand on the keywords.\n\nStep 1: Let's use the scraping tool to extract data from neoleads.com.", 'index': 0}, {'type': 'tool_use', 'id': 'toolu_bdrk_01Fzc3TnbAfxkwwbvVBVNMn6', 'name': 'apify_website_content_crawler', 'input': {}, 'index': 1, 'partial_json': '{"query": "https://neoleads.com"}'}], additional_kwargs={}, response_metadata={'stop_reason': 'tool_use', 'stop_sequence': None}, id='run-3f3f97fa-11a1-48d7-b8f7-57bb9bf94ecd-0', tool_calls=[{'name': 'apify_website_content_crawler', 'args': {'query': 'https://neoleads.com'}, 'id': 'toolu_bdrk_01Fzc3TnbAfxkwwbvVBVNMn6', 'type': 'tool_call'}], usage_metadata={'input_tokens': 1709, 'output_tokens': 115, 'total_tokens': 1824})], 'sender': 'generator', 'limit': 0, 'generation': AIMessage(content=[{'type': 'text', 'text': "Certainly! I'll follow the steps you've outlined to find seed keywords for neoleads.com. Let's begin with scraping the website content and then use the search tools to expand on the keywords.\n\nStep 1: Let's use the scraping tool to extract data from neoleads.com.", 'index': 0}, {'type': 'tool_use', 'id': 'toolu_bdrk_01Fzc3TnbAfxkwwbvVBVNMn6', 'name': 'apify_website_content_crawler', 'input': {}, 'index': 1, 'partial_json': '{"query": "https://neoleads.com"}'}], additional_kwargs={}, response_metadata={'stop_reason': 'tool_use', 'stop_sequence': None}, id='run-3f3f97fa-11a1-48d7-b8f7-57bb9bf94ecd-0', tool_calls=[{'name': 'apify_website_content_crawler', 'args': {'query': 'https://neoleads.com'}, 'id': 'toolu_bdrk_01Fzc3TnbAfxkwwbvVBVNMn6', 'type': 'tool_call'}], usage_metadata={'input_tokens': 1709, 'output_tokens': 115, 'total_tokens': 1824})}}))

```

And when i am getting graph state, in tasks i didn't get subgraph tasks even though i have mentioned subgraphs to True:

```notranslate
StateSnapshot(values={'messages': [HumanMessage(content='find seed keywords for neoleads.com', additional_kwargs={}, response_metadata={}, id='1590f929-1b02-4fbf-8bc1-4c490ac1c3f8')], 'next': 'GenerateKeywordsIdeas', 'steps': "Step 1: Use the scraping tool to extract data from neoleads.com.\nStep 2: Analyze the extracted data to identify potential seed keywords related to the website's content and services.\nStep 3: Use Google Search, Bing Search, and YouTube Search tools to find related keywords and searches based on the identified seed keywords.\nStep 4: Compile a comprehensive list of seed keywords and related searches relevant to neoleads.com."}, next=('GenerateKeywordsIdeas',), config={'configurable': {'thread_id': 'gwZPugyWbAA008weA5ZT', 'checkpoint_ns': '', 'checkpoint_id': '1ef8df14-2442-6a18-8001-ed017ce3e52a'}}, metadata={'step': 1, 'source': 'loop', 'writes': {'supervisor': {'next': 'GenerateKeywordsIdeas', 'steps': "Step 1: Use the scraping tool to extract data from neoleads.com.\nStep 2: Analyze the extracted data to identify potential seed keywords related to the website's content and services.\nStep 3: Use Google Search, Bing Search, and YouTube Search tools to find related keywords and searches based on the identified seed keywords.\nStep 4: Compile a comprehensive list of seed keywords and related searches relevant to neoleads.com."}}, 'parents': {}}, created_at='2024-10-19T08:08:01.017277+00:00', parent_config={'configurable': {'thread_id': 'gwZPugyWbAA008weA5ZT', 'checkpoint_ns': '', 'checkpoint_id': '1ef8df13-f1ef-6b51-8000-9e465076db1d'}}, tasks=(PregelTask(id='b458982c-c182-854a-44a9-f0bcdecba8e8', name='GenerateKeywordsIdeas', path=('__pregel_pull', 'GenerateKeywordsIdeas'), error=None, interrupts=(), state=None, result=None),))

```

code:

```notranslate
def run(self, input_message: str):
        self.compile()
        with ConnectionPool(
            conninfo=self.DB_URI,
            kwargs=self.connection_kwargs,
        ) as pool:
            checkpointer = PostgresSaver(pool)
            # memory = MemorySaver()
            # checkpointer.setup()
            print(self.config)
            graph = self.workflow.compile(checkpointer = checkpointer, interrupt_before=["human_feedback"])
            # print(graph.get_graph().draw_mermaid())
            self.config['recursion_limit'] = 150
            self.config['callbacks'] = self.callbacks
            # self.config["configurable"] = {"thread_id": "1"}
            for s in graph.stream({"messages": [HumanMessage(content=input_message)],"user_feedback": "No Feedback till now, so continue your work",},
                                  config=self.config,subgraphs=True):
                print(s)
                # if "__end__" not in s:
                #     print(s)
                #     if "FINISH" in s:
                #         self.final_response = s["FINISH"]['messages'][-1].content
                #     print("----")
            print(graph.get_state(self.config, subgraphs=True))

```

1

0 replies

[![@cocoza4](https://avatars.githubusercontent.com/u/2470948?u=1ca63e39c8e1ddbbb3d3c3bfee49d31d46cbff28&v=4)cocoza4](https://github.com/cocoza4) [Oct 24, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11036901)

For, double nested subgraphs, let's say we have the following routes

```notranslate
class RouterState(MessagesState):
    route: Literal["weather", "sql", "other"]

class Router(TypedDict):
    route: Literal["weather", "sq", "other"]

```

How can we implement a graph such that it supports question that requires multiple routes e.g. both weather and other route. For example, questions like what is the weather in SF and show me 3 countries with highest sales.

1

0 replies

[![@atanudasgupta](https://avatars.githubusercontent.com/u/8434765?u=e64130922b224173095bd3e31698e753281f6019&v=4)atanudasgupta](https://github.com/atanudasgupta) [Oct 27, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11065324)

How to display subgraphs within graphs, IPython.display does not show subgraphs the way you would want to visualise/

1

2 replies

[![@ficzusistvan](https://avatars.githubusercontent.com/u/3605610?u=9c142ea8385e9399a826540328c5f1782f6f57c1&v=4)](https://github.com/ficzusistvan)

[ficzusistvan](https://github.com/ficzusistvan) [Oct 28, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11075252)

I have the same question.

[![@jhachirag7](https://avatars.githubusercontent.com/u/70481022?v=4)](https://github.com/jhachirag7)

[jhachirag7](https://github.com/jhachirag7) [Oct 29, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11083361)

graph.get\_graph(xray=True).draw\_mermaid()

use this you will get code that starts with graph TD;

paste that code in mermaid.live website

👍1

[![@ClaireJL](https://avatars.githubusercontent.com/u/14009994?u=67df64c8066facdfc10ed77d7484e0bfc012fcb1&v=4)ClaireJL](https://github.com/ClaireJL) [Oct 29, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11083213)

Is there a way to stack & restore a subgraph's private state history? I'm developing a multi-agent system, where each agent is defined as a subgraph. A subgraph can be visited multiple times during a session, and I want it to keep all of its own state memory. In the earlier Langgraph version I tried to customize a "SubgraphStateManager" and use it as a context object in parent state. Since `context` is no longer supported in later versions, I'm wondering if there's any easy way for me to do this.

2

0 replies

[![@lixxvsky](https://avatars.githubusercontent.com/u/15372795?v=4)lixxvsky](https://github.com/lixxvsky) [Oct 30, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11098631)

For the second case "Add a node function that invokes the subgraph"

If we set parameter config when invoke subgraph,

```notranslate
response = subgraph.invoke({"bar": state["foo"]}, config={"configurable": {"thread_id": "1233"}})

```

Parent graph fails to steam the events of subgraph. The output will be

```notranslate
((), {'node_1': {'foo': 'hi! foo'}})
((), {'node_2': {'foo': 'hi! foobaz'}})

```

May I know is there a way to stream subgraph when set config parameter when invoking subgraph?

2

3 replies

[![@atanudasgupta](https://avatars.githubusercontent.com/u/8434765?u=e64130922b224173095bd3e31698e753281f6019&v=4)](https://github.com/atanudasgupta)

[atanudasgupta](https://github.com/atanudasgupta) [Oct 30, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11098799)

While streaming. Use subgraphs=True, in graph.stream()

[![@lixxvsky](https://avatars.githubusercontent.com/u/15372795?v=4)](https://github.com/lixxvsky)

[lixxvsky](https://github.com/lixxvsky) [Oct 31, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11106548)

Hi atanudasgupta, I add `subgraphs=True`, but it still cannot stream subgraph when `config` is added in subgraph.invoke() function

```notranslate
    for chunk in graph.stream({"foo": "foo"}, subgraphs=True):
        print(chunk)

```

I use the sample code shown in _Add a node function that invokes the subgraph_ for test, the only one difference is just adding `config` in subgraph.invoke() function.

[![@atanudasgupta](https://avatars.githubusercontent.com/u/8434765?u=e64130922b224173095bd3e31698e753281f6019&v=4)](https://github.com/atanudasgupta)

[atanudasgupta](https://github.com/atanudasgupta) [Oct 31, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11108794)

you need to use as follows, with config.

for chunk in graph.stream({"foo": "foo"}, config=config, subgraphs=True):

print(chunk)

## see the output below.

((), {'node\_1': {'foo': 'hi! foo'}})

(('node\_2:a143cd80-3d42-40c1-02a8-99add744ed8b',), {'subgraph\_node\_1': {'baz': 'baz'}})

(('node\_2:a143cd80-3d42-40c1-02a8-99add744ed8b',), {'subgraph\_node\_2': {'bar': 'hi! foobaz'}})

((), {'node\_2': {'foo': 'hi! foobaz'}})

[![@youdar](https://avatars.githubusercontent.com/u/4286525?u=ee8b31f0fbdc92e8d2eb0fb84e2f2c0eb9d26a69&v=4)youdar](https://github.com/youdar) [Nov 9, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11194163)

Hi.

How to create edges between a subgraph and the parent graph?

When creating an edge from parent to the subgraph, the subgraph need to be compiled first.

When creating an edge from the subgraph back to the parent, the parent needs to be compiled first.

So this method does not appear to work, since it a circular logic.

I assume that going to END in the subgraph, keeps us in the subgraph, state changes to the START if the subgraph.

If I want to convert [Customer support bot](https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support/#assistants) to a graph implementation,

how to I leave the flight reservation subgraph and go back to the main assistant parent graph?

Any advice/thoughts ?

thank you

1

1 reply

[![@youdar](https://avatars.githubusercontent.com/u/4286525?u=ee8b31f0fbdc92e8d2eb0fb84e2f2c0eb9d26a69&v=4)](https://github.com/youdar)

[youdar](https://github.com/youdar) [Nov 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11217981)

Looking at the code above it looks like when the interaction get to `subgraph_node_2` it automatically goes back to the parent `start` .

Or maybe I am not understanding it correctly...

It looks to me like the one of the main points of using subgraphs architecture is to allow to remain in the subgraph until routed beck to the parent, avoiding always going to the parent `start` automatically.

[![@weatherman85](https://avatars.githubusercontent.com/u/65472530?v=4)weatherman85](https://github.com/weatherman85) [Nov 16, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11277815)

I was trying to get this to work where there are two subgraphs running in parallel with a breakpoint in one of them. It always throws a GraphInterrupt error though. Using the latest lang graph. Can’t share the code since it’s at work.

1

0 replies

[![@atanudasgupta](https://avatars.githubusercontent.com/u/8434765?u=e64130922b224173095bd3e31698e753281f6019&v=4)atanudasgupta](https://github.com/atanudasgupta) [Nov 16, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11277954)

Use add interrupt

Yahoo Mail: Search, Organize, Conquer

On Sat, Nov 16, 2024 at 7:43 PM, \*\*\*@\*\*\*.\*\*\*> wrote:

I was trying to get this to work where there are two subgraphs running in parallel with a breakpoint in one of them. It always throws a GraphInterrupt error though. Using the latest lang graph. Can’t share the code since it’s at work.

—
Reply to this email directly, view it on GitHub, or unsubscribe.
You are receiving this because you commented.Message ID: \*\*\*@\*\*\*.\*\*\*>

1

1 reply

[![@weatherman85](https://avatars.githubusercontent.com/u/65472530?v=4)](https://github.com/weatherman85)

[weatherman85](https://github.com/weatherman85) [Nov 16, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11277966)

I have an interrupt in the one subgraph. Does it need to go into the primary graph somewhere?

[![@padamson](https://avatars.githubusercontent.com/u/5460406?u=a5e6a257f3f8dec64a38e732b5a481fa9f51d8dd&v=4)padamson](https://github.com/padamson) [Dec 29, 2024](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11690222)

Is it possible to interrupt after a subgraph node by passing "interrupt\_after" to CompiledGraph.stream()? This would be useful for testing, but it seems like it's not possible since the subgraph namespace includes a dynamic runtime UID (subgraph:UID.node\_name).

1

0 replies

[![@vigneshmj1997](https://avatars.githubusercontent.com/u/33595829?u=d0ee173f2ceb7074923d3ffbd63ca56493081977&v=4)vigneshmj1997](https://github.com/vigneshmj1997) [Jan 6](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-11745487)

Wont it be a better design if langgraph its self knows where to continue from, irrespective of graph being a subgraph or parent graph ..?

1

0 replies

[![@david101-hunter](https://avatars.githubusercontent.com/u/156736296?u=a733d3a1912f21d6300c34761c577ecf305107f7&v=4)david101-hunter](https://github.com/david101-hunter) [8 days ago](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-12848874)

Hi

I'm in `To get the state history of the subgraph, we need to first pass in` stage

after run

```notranslate
parent_graph_state_before_subgraph = next(
    h
    for h in graph.get_state_history(config)
    if h.next == ("weather_graph",)
)

subgraph_state_before_model_node = next(
    h
    for h in graph.get_state_history(parent_graph_state_before_subgraph.tasks[0].state)
    if h.next == ("model_node",)
)

```

it raise

```notranslate
Traceback (most recent call last):
  File "../view-and-update-state-graph.py", line 155, in <module>
    parent_graph_state_before_subgraph = next(
                                         ^^^^^
StopIteration

```

1

2 replies

[![@sivaTwks010928](https://avatars.githubusercontent.com/u/178696152?v=4)](https://github.com/sivaTwks010928)

[sivaTwks010928](https://github.com/sivaTwks010928) [8 days ago](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-12850472)

edited

```notranslate
class SubgraphState(TypedDict):
    foo: str
    bar: str

def subgraph_node_1(state: SubgraphState):
    return {"bar": "subgraph_node_1:bar"}

def subgraph_node_2(state: SubgraphState):
    return {"foo": state["foo"] + " + subgraph_node_2(" + state["bar"] + ")"}

def subgraph_node_3(state: SubgraphState):
    return {"bar": state["bar"] + " + subgraph_node_3"}

def subgraph_node_4(state: SubgraphState):
    return {"foo": state["foo"] + " + subgraph_node_4 FINAL"}

subgraph_builder = StateGraph(SubgraphState)
subgraph_builder.add_node("subgraph_node_1", subgraph_node_1)
subgraph_builder.add_node("subgraph_node_2", subgraph_node_2)
subgraph_builder.add_node("subgraph_node_3", subgraph_node_3)
subgraph_builder.add_node("subgraph_node_4", subgraph_node_4)

subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph_builder.add_edge("subgraph_node_1", "subgraph_node_2")
subgraph_builder.add_edge("subgraph_node_2", "subgraph_node_3")
subgraph_builder.add_edge("subgraph_node_3", "subgraph_node_4")

subgraph = subgraph_builder.compile(checkpointer=True)

class ParentState(TypedDict):
    foo: str

def node_1(state: ParentState):
    return {"foo": "parent_node_1(" + state["foo"] + ")"}

builder = StateGraph(ParentState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", subgraph)

builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_1", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "1"}}

print("\n--- Streamed Updates ---")

for event in graph.stream({"foo": "foo"}, config=config, stream_mode="updates", subgraphs=True):
    for key, value in event[1].items():
        print(key, value)

print("\n--- Final Parent Graph State ---")
pprint(graph.get_state(config).values)

print("\n--- Parent Graph State History ---")
snapshots_parent = graph.get_state_history(config=config)

state_with_subgraph = [s for s in snapshots_parent if s.next == ('node_2',)][0]
subgraph_config =state_with_subgraph.tasks[0].state

subgraph_state_histories = graph.get_state_history(config=subgraph_config)

subgraph_histories = []
for h in subgraph_state_histories:
    subgraph_histories.append(h)

```

I have tried this, but I got subgraph\_state\_histories as empty list... do u have any idea?

[![@sivaTwks010928](https://avatars.githubusercontent.com/u/178696152?v=4)](https://github.com/sivaTwks010928)

[sivaTwks010928](https://github.com/sivaTwks010928) [8 days ago](https://github.com/langchain-ai/langgraph/discussions/1728#discussioncomment-12850621)

anyone have any idea why we can't get the subgraph state history?

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fsubgraphs-manage-state%2F)