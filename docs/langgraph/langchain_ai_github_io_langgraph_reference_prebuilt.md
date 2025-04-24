[Skip to content](https://langchain-ai.github.io/langgraph/reference/prebuilt/#prebuilt)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/reference/prebuilt.md "Edit this page")

# Prebuilt [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#prebuilt "Permanent link")

Functions:

- **`create_react_agent`**
–



Creates a graph that works with a chat model that utilizes tool calling.


## `` create\_react\_agent [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.chat_agent_executor.create_react_agent "Permanent link")

```md-code__content
create_react_agent(
    model: Union[str, LanguageModelLike],
    tools: Union[\
        Sequence[Union[BaseTool, Callable]], ToolNode\
    ],
    *,
    prompt: Optional[Prompt] = None,
    response_format: Optional[\
        Union[\
            StructuredResponseSchema,\
            tuple[str, StructuredResponseSchema],\
        ]\
    ] = None,
    pre_model_hook: Optional[RunnableLike] = None,
    state_schema: Optional[StateSchemaType] = None,
    config_schema: Optional[Type[Any]] = None,
    checkpointer: Optional[Checkpointer] = None,
    store: Optional[BaseStore] = None,
    interrupt_before: Optional[list[str]] = None,
    interrupt_after: Optional[list[str]] = None,
    debug: bool = False,
    version: Literal["v1", "v2"] = "v1",
    name: Optional[str] = None
) -> CompiledGraph

```

Creates a graph that works with a chat model that utilizes tool calling.

Parameters:

- **`model`**
( `Union[str, LanguageModelLike]`)
–



The `LangChain` chat model that supports tool calling.

- **`tools`**
( `Union[Sequence[Union[BaseTool, Callable]], ToolNode]`)
–



A list of tools or a ToolNode instance.
If an empty list is provided, the agent will consist of a single LLM node without tool calling.

- **`prompt`**
( `Optional[Prompt]`, default:
`None`
)
–



An optional prompt for the LLM. Can take a few different forms:



- str: This is converted to a SystemMessage and added to the beginning of the list of messages in state\["messages"\].
- SystemMessage: this is added to the beginning of the list of messages in state\["messages"\].
- Callable: This function should take in full graph state and the output is then passed to the language model.
- Runnable: This runnable should take in full graph state and the output is then passed to the language model.

- **`response_format`**
( `Optional[Union[StructuredResponseSchema, tuple[str, StructuredResponseSchema]]]`, default:
`None`
)
–



An optional schema for the final agent output.



If provided, output will be formatted to match the given schema and returned in the 'structured\_response' state key.
If not provided, `structured_response` will not be present in the output state.
Can be passed in as:





```
- an OpenAI function/tool schema,
- a JSON Schema,
- a TypedDict class,
- or a Pydantic class.
- a tuple (prompt, schema), where schema is one of the above.
    The prompt will be used together with the model that is being used to generate the structured response.

```

Important

`response_format` requires the model to support `.with_structured_output`

Note

The graph will make a separate call to the LLM to generate the structured response after the agent loop is finished.
This is not the only strategy to get structured responses, see more options in [this guide](https://langchain-ai.github.io/langgraph/how-tos/react-agent-structured-output/).

- **`pre_model_hook`**
( `Optional[RunnableLike]`, default:
`None`
)
–



An optional node to add before the `agent` node (i.e., the node that calls the LLM).
Useful for managing long message histories (e.g., message trimming, summarization, etc.).
Pre-model hook must be a callable or a runnable that takes in current graph state and returns a state update in the form of






```md-code__content
# At least one of `messages` or `llm_input_messages` MUST be provided
{
      # If provided, will UPDATE the `messages` in the state
      "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), ...],
      # If provided, will be used as the input to the LLM,
      # and will NOT UPDATE `messages` in the state
      "llm_input_messages": [...],
      # Any other state keys that need to be propagated
      ...
}

```











Important



At least one of `messages` or `llm_input_messages` MUST be provided and will be used as an input to the `agent` node.
The rest of the keys will be added to the graph state.







Warning



If you are returning `messages` in the pre-model hook, you should OVERWRITE the `messages` key by doing the following:





```md-code__content
{
      "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages]
      ...
}

```

- **`state_schema`**
( `Optional[StateSchemaType]`, default:
`None`
)
–



An optional state schema that defines graph state.
Must have `messages` and `remaining_steps` keys.
Defaults to `AgentState` that defines those two keys.

- **`config_schema`**
( `Optional[Type[Any]]`, default:
`None`
)
–



An optional schema for configuration.
Use this to expose configurable parameters via agent.config\_specs.

- **`checkpointer`**
( `Optional[Checkpointer]`, default:
`None`
)
–



An optional checkpoint saver object. This is used for persisting
the state of the graph (e.g., as chat memory) for a single thread (e.g., a single conversation).

- **`store`**
( `Optional[BaseStore]`, default:
`None`
)
–



An optional store object. This is used for persisting data
across multiple threads (e.g., multiple conversations / users).

- **`interrupt_before`**
( `Optional[list[str]]`, default:
`None`
)
–



An optional list of node names to interrupt before.
Should be one of the following: "agent", "tools".
This is useful if you want to add a user confirmation or other interrupt before taking an action.

- **`interrupt_after`**
( `Optional[list[str]]`, default:
`None`
)
–



An optional list of node names to interrupt after.
Should be one of the following: "agent", "tools".
This is useful if you want to return directly or run additional processing on an output.

- **`debug`**
( `bool`, default:
`False`
)
–



A flag indicating whether to enable debug mode.

- **`version`**
( `Literal['v1', 'v2']`, default:
`'v1'`
)
–



Determines the version of the graph to create.
Can be one of:



- `"v1"`: The tool node processes a single message. All tool
calls in the message are executed in parallel within the tool node.
- `"v2"`: The tool node processes a tool call.
Tool calls are distributed across multiple instances of the tool
node using the [Send](https://langchain-ai.github.io/langgraph/concepts/low_level/#send)
API.

- **`name`**
( `Optional[str]`, default:
`None`
)
–



An optional name for the CompiledStateGraph.
This name will be automatically used when adding ReAct agent graph to another graph as a subgraph node -
particularly useful for building multi-agent systems.


Returns:

- `CompiledGraph`
–



A compiled LangChain runnable that can be used for chat interactions.


The resulting graph looks like this:

The "agent" node calls the language model with the messages list (after applying the messages modifier).
If the resulting AIMessage contains `tool_calls`, the graph will then call the ["tools"](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.ToolNode "<code class=\"doc-symbol doc-symbol-heading doc-symbol-class\"></code>            <span class=\"doc doc-object-name doc-class-name\">ToolNode</span>").
The "tools" node executes the tools (1 tool per `tool_call`) and adds the responses to the messages list
as `ToolMessage` objects. The agent node then calls the language model again.
The process repeats until no more `tool_calls` are present in the response.
The agent then returns the full list of messages as a dictionary containing the key "messages".

Examples:

Use with a simple tool:

```md-code__content
>>> from langchain_openai import ChatOpenAI
>>> from langgraph.prebuilt import create_react_agent

... def check_weather(location: str) -> str:
...     '''Return the weather forecast for the specified location.'''
...     return f"It's always sunny in {location}"
>>>
>>> tools = [check_weather]
>>> model = ChatOpenAI(model="gpt-4o")
>>> graph = create_react_agent(model, tools=tools)
>>> inputs = {"messages": [("user", "what is the weather in sf")]}
>>> for s in graph.stream(inputs, stream_mode="values"):
...     message = s["messages"][-1]
...     if isinstance(message, tuple):
...         print(message)
...     else:
...         message.pretty_print()
('user', 'what is the weather in sf')
================================== Ai Message ==================================
Tool Calls:
check_weather (call_LUzFvKJRuaWQPeXvBOzwhQOu)
Call ID: call_LUzFvKJRuaWQPeXvBOzwhQOu
Args:
    location: San Francisco
================================= Tool Message =================================
Name: check_weather
It's always sunny in San Francisco
================================== Ai Message ==================================
The weather in San Francisco is sunny.

```

Add a system prompt for the LLM:

```md-code__content
>>> system_prompt = "You are a helpful bot named Fred."
>>> graph = create_react_agent(model, tools, prompt=system_prompt)
>>> inputs = {"messages": [("user", "What's your name? And what's the weather in SF?")]}
>>> for s in graph.stream(inputs, stream_mode="values"):
...     message = s["messages"][-1]
...     if isinstance(message, tuple):
...         print(message)
...     else:
...         message.pretty_print()
('user', "What's your name? And what's the weather in SF?")
================================== Ai Message ==================================
Hi, my name is Fred. Let me check the weather in San Francisco for you.
Tool Calls:
check_weather (call_lqhj4O0hXYkW9eknB4S41EXk)
Call ID: call_lqhj4O0hXYkW9eknB4S41EXk
Args:
    location: San Francisco
================================= Tool Message =================================
Name: check_weather
It's always sunny in San Francisco
================================== Ai Message ==================================
The weather in San Francisco is currently sunny. If you need any more details or have other questions, feel free to ask!

```

Add a more complex prompt for the LLM:

```md-code__content
>>> from langchain_core.prompts import ChatPromptTemplate
>>> prompt = ChatPromptTemplate.from_messages([\
...     ("system", "You are a helpful bot named Fred."),\
...     ("placeholder", "{messages}"),\
...     ("user", "Remember, always be polite!"),\
... ])
>>>
>>> graph = create_react_agent(model, tools, prompt=prompt)
>>> inputs = {"messages": [("user", "What's your name? And what's the weather in SF?")]}
>>> for s in graph.stream(inputs, stream_mode="values"):
...     message = s["messages"][-1]
...     if isinstance(message, tuple):
...         print(message)
...     else:
...         message.pretty_print()

```

Add complex prompt with custom graph state:

```md-code__content
>>> from typing_extensions import TypedDict
>>>
>>> from langgraph.managed import IsLastStep
>>> prompt = ChatPromptTemplate.from_messages(
...     [\
...         ("system", "Today is {today}"),\
...         ("placeholder", "{messages}"),\
...     ]
... )
>>>
>>> class CustomState(TypedDict):
...     today: str
...     messages: Annotated[list[BaseMessage], add_messages]
...     is_last_step: IsLastStep
>>>
>>> graph = create_react_agent(model, tools, state_schema=CustomState, prompt=prompt)
>>> inputs = {"messages": [("user", "What's today's date? And what's the weather in SF?")], "today": "July 16, 2004"}
>>> for s in graph.stream(inputs, stream_mode="values"):
...     message = s["messages"][-1]
...     if isinstance(message, tuple):
...         print(message)
...     else:
...         message.pretty_print()

```

Add thread-level "chat memory" to the graph:

```md-code__content
>>> from langgraph.checkpoint.memory import MemorySaver
>>> graph = create_react_agent(model, tools, checkpointer=MemorySaver())
>>> config = {"configurable": {"thread_id": "thread-1"}}
>>> def print_stream(graph, inputs, config):
...     for s in graph.stream(inputs, config, stream_mode="values"):
...         message = s["messages"][-1]
...         if isinstance(message, tuple):
...             print(message)
...         else:
...             message.pretty_print()
>>> inputs = {"messages": [("user", "What's the weather in SF?")]}
>>> print_stream(graph, inputs, config)
>>> inputs2 = {"messages": [("user", "Cool, so then should i go biking today?")]}
>>> print_stream(graph, inputs2, config)
('user', "What's the weather in SF?")
================================== Ai Message ==================================
Tool Calls:
check_weather (call_ChndaktJxpr6EMPEB5JfOFYc)
Call ID: call_ChndaktJxpr6EMPEB5JfOFYc
Args:
    location: San Francisco
================================= Tool Message =================================
Name: check_weather
It's always sunny in San Francisco
================================== Ai Message ==================================
The weather in San Francisco is sunny. Enjoy your day!
================================ Human Message =================================
Cool, so then should i go biking today?
================================== Ai Message ==================================
Since the weather in San Francisco is sunny, it sounds like a great day for biking! Enjoy your ride!

```

Add an interrupt to let the user confirm before taking an action:

```md-code__content
>>> graph = create_react_agent(
...     model, tools, interrupt_before=["tools"], checkpointer=MemorySaver()
>>> )
>>> config = {"configurable": {"thread_id": "thread-1"}}

>>> inputs = {"messages": [("user", "What's the weather in SF?")]}
>>> print_stream(graph, inputs, config)
>>> snapshot = graph.get_state(config)
>>> print("Next step: ", snapshot.next)
>>> print_stream(graph, None, config)

```

Add cross-thread memory to the graph:

```md-code__content
>>> from langgraph.prebuilt import InjectedStore
>>> from langgraph.store.base import BaseStore

>>> def save_memory(memory: str, *, config: RunnableConfig, store: Annotated[BaseStore, InjectedStore()]) -> str:
...     '''Save the given memory for the current user.'''
...     # This is a **tool** the model can use to save memories to storage
...     user_id = config.get("configurable", {}).get("user_id")
...     namespace = ("memories", user_id)
...     store.put(namespace, f"memory_{len(store.search(namespace))}", {"data": memory})
...     return f"Saved memory: {memory}"

>>> def prepare_model_inputs(state: AgentState, config: RunnableConfig, store: BaseStore):
...     # Retrieve user memories and add them to the system message
...     # This function is called **every time** the model is prompted. It converts the state to a prompt
...     user_id = config.get("configurable", {}).get("user_id")
...     namespace = ("memories", user_id)
...     memories = [m.value["data"] for m in store.search(namespace)]
...     system_msg = f"User memories: {', '.join(memories)}"
...     return [{"role": "system", "content": system_msg)] + state["messages"]

>>> from langgraph.checkpoint.memory import MemorySaver
>>> from langgraph.store.memory import InMemoryStore
>>> store = InMemoryStore()
>>> graph = create_react_agent(model, [save_memory], prompt=prepare_model_inputs, store=store, checkpointer=MemorySaver())
>>> config = {"configurable": {"thread_id": "thread-1", "user_id": "1"}}

>>> inputs = {"messages": [("user", "Hey I'm Will, how's it going?")]}
>>> print_stream(graph, inputs, config)
('user', "Hey I'm Will, how's it going?")
================================== Ai Message ==================================
Hello Will! It's nice to meet you. I'm doing well, thank you for asking. How are you doing today?

>>> inputs2 = {"messages": [("user", "I like to bike")]}
>>> print_stream(graph, inputs2, config)
================================ Human Message =================================
I like to bike
================================== Ai Message ==================================
That's great to hear, Will! Biking is an excellent hobby and form of exercise. It's a fun way to stay active and explore your surroundings. Do you have any favorite biking routes or trails you enjoy? Or perhaps you're into a specific type of biking, like mountain biking or road cycling?

>>> config = {"configurable": {"thread_id": "thread-2", "user_id": "1"}}
>>> inputs3 = {"messages": [("user", "Hi there! Remember me?")]}
>>> print_stream(graph, inputs3, config)
================================ Human Message =================================
Hi there! Remember me?
================================== Ai Message ==================================
User memories:
Hello! Of course, I remember you, Will! You mentioned earlier that you like to bike. It's great to hear from you again. How have you been? Have you been on any interesting bike rides lately?

```

Add a timeout for a given step:

```md-code__content
>>> import time
... def check_weather(location: str) -> str:
...     '''Return the weather forecast for the specified location.'''
...     time.sleep(2)
...     return f"It's always sunny in {location}"
>>>
>>> tools = [check_weather]
>>> graph = create_react_agent(model, tools)
>>> graph.step_timeout = 1 # Seconds
>>> for s in graph.stream({"messages": [("user", "what is the weather in sf")]}):
...     print(s)
TimeoutError: Timed out at step 2

```

Classes:

- **`ToolNode`**
–



A node that runs the tools called in the last AIMessage.

- **`InjectedState`**
–



Annotation for a Tool arg that is meant to be populated with the graph state.

- **`InjectedStore`**
–



Annotation for a Tool arg that is meant to be populated with LangGraph store.


Functions:

- **`tools_condition`**
–



Use in the conditional\_edge to route to the ToolNode if the last message


## `` ToolNode [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode "Permanent link")

Bases: `RunnableCallable`

A node that runs the tools called in the last AIMessage.

It can be used either in StateGraph with a "messages" state key (or a custom key passed via ToolNode's 'messages\_key').
If multiple tool calls are requested, they will be run in parallel. The output will be
a list of ToolMessages, one for each tool call.

Tool calls can also be passed directly as a list of `ToolCall` dicts.

Parameters:

- **`tools`**
( `Sequence[Union[BaseTool, Callable]]`)
–



A sequence of tools that can be invoked by the ToolNode.

- **`name`**
( `str`, default:
`'tools'`
)
–



The name of the ToolNode in the graph. Defaults to "tools".

- **`tags`**
( `Optional[list[str]]`, default:
`None`
)
–



Optional tags to associate with the node. Defaults to None.

- **`handle_tool_errors`**
( `Union[bool, str, Callable[..., str], tuple[type[Exception], ...]]`, default:
`True`
)
–



How to handle tool errors raised by tools inside the node. Defaults to True.
Must be one of the following:



- True: all errors will be caught and
a ToolMessage with a default error message (TOOL\_CALL\_ERROR\_TEMPLATE) will be returned.
- str: all errors will be caught and
a ToolMessage with the string value of 'handle\_tool\_errors' will be returned.
- tuple\[type\[Exception\], ...\]: exceptions in the tuple will be caught and
a ToolMessage with a default error message (TOOL\_CALL\_ERROR\_TEMPLATE) will be returned.
- Callable\[..., str\]: exceptions from the signature of the callable will be caught and
a ToolMessage with the string value of the result of the 'handle\_tool\_errors' callable will be returned.
- False: none of the errors raised by the tools will be caught

- **`messages_key`**
( `str`, default:
`'messages'`
)
–



The state key in the input that contains the list of messages.
The same key will be used for the output from the ToolNode.
Defaults to "messages".


The `ToolNode` is roughly analogous to:

```md-code__content
tools_by_name = {tool.name: tool for tool in tools}
def tool_node(state: dict):
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}

```

Tool calls can also be passed directly to a ToolNode. This can be useful when using
the Send API, e.g., in a conditional edge:

```md-code__content
def example_conditional_edge(state: dict) -> List[Send]:
    tool_calls = state["messages"][-1].tool_calls
    # If tools rely on state or store variables (whose values are not generated
    # directly by a model), you can inject them into the tool calls.
    tool_calls = [\
        tool_node.inject_tool_args(call, state, store)\
        for call in last_message.tool_calls\
    ]
    return [Send("tools", [tool_call]) for tool_call in tool_calls]

```

Important

- The input state can be one of the following:
  - A dict with a messages key containing a list of messages.
  - A list of messages.
  - A list of tool calls.
- If operating on a message list, the last message must be an `AIMessage` with
`tool_calls` populated.

Methods:

- **`inject_tool_args`**
–



Injects the state and store into the tool call.

- **`get_name`**
–



Get the name of the Runnable.

- **`get_input_schema`**
–



Get a pydantic model that can be used to validate input to the Runnable.

- **`get_input_jsonschema`**
–



Get a JSON schema that represents the input to the Runnable.

- **`get_output_schema`**
–



Get a pydantic model that can be used to validate output to the Runnable.

- **`get_output_jsonschema`**
–



Get a JSON schema that represents the output of the Runnable.

- **`config_schema`**
–



The type of config this Runnable accepts specified as a pydantic model.

- **`get_config_jsonschema`**
–



Get a JSON schema that represents the config of the Runnable.

- **`get_graph`**
–



Return a graph representation of this Runnable.

- **`get_prompts`**
–



Return a list of prompts used by this Runnable.

- **`__or__`**
–



Compose this Runnable with another object to create a RunnableSequence.

- **`__ror__`**
–



Compose this Runnable with another object to create a RunnableSequence.

- **`pipe`**
–



Compose this Runnable with Runnable-like objects to make a RunnableSequence.

- **`pick`**
–



Pick keys from the output dict of this Runnable.

- **`assign`**
–



Assigns new fields to the dict output of this Runnable.

- **`batch`**
–



Default implementation runs invoke in parallel using a thread pool executor.

- **`batch_as_completed`**
–



Run invoke in parallel on a list of inputs.

- **`abatch`**
–



Default implementation runs ainvoke in parallel using asyncio.gather.

- **`abatch_as_completed`**
–



Run ainvoke in parallel on a list of inputs.

- **`stream`**
–



Default implementation of stream, which calls invoke.

- **`astream`**
–



Default implementation of astream, which calls ainvoke.

- **`astream_log`**
–



Stream all output from a Runnable, as reported to the callback system.

- **`astream_events`**
–



Generate a stream of events.

- **`transform`**
–



Default implementation of transform, which buffers input and calls astream.

- **`atransform`**
–



Default implementation of atransform, which buffers input and calls astream.

- **`bind`**
–



Bind arguments to a Runnable, returning a new Runnable.

- **`with_config`**
–



Bind config to a Runnable, returning a new Runnable.

- **`with_listeners`**
–



Bind lifecycle listeners to a Runnable, returning a new Runnable.

- **`with_alisteners`**
–



Bind async lifecycle listeners to a Runnable, returning a new Runnable.

- **`with_types`**
–



Bind input and output types to a Runnable, returning a new Runnable.

- **`with_retry`**
–



Create a new Runnable that retries the original Runnable on exceptions.

- **`map`**
–



Return a new Runnable that maps a list of inputs to a list of outputs.

- **`with_fallbacks`**
–



Add fallbacks to a Runnable, returning a new Runnable.

- **`as_tool`**
–



Create a BaseTool from a Runnable.


Attributes:

- **`InputType`**
( `type[Input]`)
–



The type of input this Runnable accepts specified as a type annotation.

- **`OutputType`**
( `type[Output]`)
–



The type of output this Runnable produces specified as a type annotation.

- **`input_schema`**
( `type[BaseModel]`)
–



The type of input this Runnable accepts specified as a pydantic model.

- **`output_schema`**
( `type[BaseModel]`)
–



The type of output this Runnable produces specified as a pydantic model.

- **`config_specs`**
( `list[ConfigurableFieldSpec]`)
–



List configurable fields for this Runnable.


### `` InputType`property`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.InputType "Permanent link")

```md-code__content
InputType: type[Input]

```

The type of input this Runnable accepts specified as a type annotation.

### `` OutputType`property`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.OutputType "Permanent link")

```md-code__content
OutputType: type[Output]

```

The type of output this Runnable produces specified as a type annotation.

### `` input\_schema`property`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.input_schema "Permanent link")

```md-code__content
input_schema: type[BaseModel]

```

The type of input this Runnable accepts specified as a pydantic model.

### `` output\_schema`property`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.output_schema "Permanent link")

```md-code__content
output_schema: type[BaseModel]

```

The type of output this Runnable produces specified as a pydantic model.

### `` config\_specs`property`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.config_specs "Permanent link")

```md-code__content
config_specs: list[ConfigurableFieldSpec]

```

List configurable fields for this Runnable.

### `` inject\_tool\_args [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.inject_tool_args "Permanent link")

```md-code__content
inject_tool_args(
    tool_call: ToolCall,
    input: Union[\
        list[AnyMessage], dict[str, Any], BaseModel\
    ],
    store: Optional[BaseStore],
) -> ToolCall

```

Injects the state and store into the tool call.

Tool arguments with types annotated as `InjectedState` and `InjectedStore` are
ignored in tool schemas for generation purposes. This method injects them into
tool calls for tool invocation.

Parameters:

- **`tool_call`**
( `ToolCall`)
–



The tool call to inject state and store into.

- **`input`**
( `Union[list[AnyMessage], dict[str, Any], BaseModel]`)
–



The input state
to inject.

- **`store`**
( `Optional[BaseStore]`)
–



The store to inject.


Returns:

- **`ToolCall`** ( `ToolCall`
) –



The tool call with injected state and store.


### `` get\_name [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.get_name "Permanent link")

```md-code__content
get_name(
    suffix: Optional[str] = None,
    *,
    name: Optional[str] = None
) -> str

```

Get the name of the Runnable.

### `` get\_input\_schema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.get_input_schema "Permanent link")

```md-code__content
get_input_schema(
    config: Optional[RunnableConfig] = None,
) -> type[BaseModel]

```

Get a pydantic model that can be used to validate input to the Runnable.

Runnables that leverage the configurable\_fields and configurable\_alternatives
methods will have a dynamic input schema that depends on which
configuration the Runnable is invoked with.

This method allows to get an input schema for a specific configuration.

Parameters:

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



A config to use when generating the schema.


Returns:

- `type[BaseModel]`
–



A pydantic model that can be used to validate input.


### `` get\_input\_jsonschema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.get_input_jsonschema "Permanent link")

```md-code__content
get_input_jsonschema(
    config: Optional[RunnableConfig] = None,
) -> dict[str, Any]

```

Get a JSON schema that represents the input to the Runnable.

Parameters:

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



A config to use when generating the schema.


Returns:

- `dict[str, Any]`
–



A JSON schema that represents the input to the Runnable.


Example:

```
.. code-block:: python

    from langchain_core.runnables import RunnableLambda

    def add_one(x: int) -> int:
        return x + 1

    runnable = RunnableLambda(add_one)

    print(runnable.get_input_jsonschema())

```

.. versionadded:: 0.3.0

### `` get\_output\_schema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.get_output_schema "Permanent link")

```md-code__content
get_output_schema(
    config: Optional[RunnableConfig] = None,
) -> type[BaseModel]

```

Get a pydantic model that can be used to validate output to the Runnable.

Runnables that leverage the configurable\_fields and configurable\_alternatives
methods will have a dynamic output schema that depends on which
configuration the Runnable is invoked with.

This method allows to get an output schema for a specific configuration.

Parameters:

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



A config to use when generating the schema.


Returns:

- `type[BaseModel]`
–



A pydantic model that can be used to validate output.


### `` get\_output\_jsonschema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.get_output_jsonschema "Permanent link")

```md-code__content
get_output_jsonschema(
    config: Optional[RunnableConfig] = None,
) -> dict[str, Any]

```

Get a JSON schema that represents the output of the Runnable.

Parameters:

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



A config to use when generating the schema.


Returns:

- `dict[str, Any]`
–



A JSON schema that represents the output of the Runnable.


Example:

```
.. code-block:: python

    from langchain_core.runnables import RunnableLambda

    def add_one(x: int) -> int:
        return x + 1

    runnable = RunnableLambda(add_one)

    print(runnable.get_output_jsonschema())

```

.. versionadded:: 0.3.0

### `` config\_schema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.config_schema "Permanent link")

```md-code__content
config_schema(
    *, include: Optional[Sequence[str]] = None
) -> type[BaseModel]

```

The type of config this Runnable accepts specified as a pydantic model.

To mark a field as configurable, see the `configurable_fields`
and `configurable_alternatives` methods.

Parameters:

- **`include`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



A list of fields to include in the config schema.


Returns:

- `type[BaseModel]`
–



A pydantic model that can be used to validate config.


### `` get\_config\_jsonschema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.get_config_jsonschema "Permanent link")

```md-code__content
get_config_jsonschema(
    *, include: Optional[Sequence[str]] = None
) -> dict[str, Any]

```

Get a JSON schema that represents the config of the Runnable.

Parameters:

- **`include`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



A list of fields to include in the config schema.


Returns:

- `dict[str, Any]`
–



A JSON schema that represents the config of the Runnable.


.. versionadded:: 0.3.0

### `` get\_graph [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.get_graph "Permanent link")

```md-code__content
get_graph(config: Optional[RunnableConfig] = None) -> Graph

```

Return a graph representation of this Runnable.

### `` get\_prompts [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.get_prompts "Permanent link")

```md-code__content
get_prompts(
    config: Optional[RunnableConfig] = None,
) -> list[BasePromptTemplate]

```

Return a list of prompts used by this Runnable.

### ``\_\_or\_\_ [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.__or__ "Permanent link")

```md-code__content
__or__(
    other: Union[\
        Runnable[Any, Other],\
        Callable[[Any], Other],\
        Callable[[Iterator[Any]], Iterator[Other]],\
        Mapping[\
            str,\
            Union[\
                Runnable[Any, Other],\
                Callable[[Any], Other],\
                Any,\
            ],\
        ],\
    ],
) -> RunnableSerializable[Input, Other]

```

Compose this Runnable with another object to create a RunnableSequence.

### ``\_\_ror\_\_ [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.__ror__ "Permanent link")

```md-code__content
__ror__(
    other: Union[\
        Runnable[Other, Any],\
        Callable[[Other], Any],\
        Callable[[Iterator[Other]], Iterator[Any]],\
        Mapping[\
            str,\
            Union[\
                Runnable[Other, Any],\
                Callable[[Other], Any],\
                Any,\
            ],\
        ],\
    ],
) -> RunnableSerializable[Other, Output]

```

Compose this Runnable with another object to create a RunnableSequence.

### `` pipe [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.pipe "Permanent link")

```md-code__content
pipe(
    *others: Union[\
        Runnable[Any, Other], Callable[[Any], Other]\
    ],
    name: Optional[str] = None
) -> RunnableSerializable[Input, Other]

```

Compose this Runnable with Runnable-like objects to make a RunnableSequence.

Equivalent to `RunnableSequence(self, *others)` or `self | others[0] | ...`

Example

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda

def add_one(x: int) -> int:
    return x + 1

def mul_two(x: int) -> int:
    return x * 2

runnable_1 = RunnableLambda(add_one)
runnable_2 = RunnableLambda(mul_two)
sequence = runnable_1.pipe(runnable_2)
# Or equivalently:
# sequence = runnable_1 | runnable_2
# sequence = RunnableSequence(first=runnable_1, last=runnable_2)
sequence.invoke(1)
await sequence.ainvoke(1)
# -> 4

sequence.batch([1, 2, 3])
await sequence.abatch([1, 2, 3])
# -> [4, 6, 8]

```

### `` pick [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.pick "Permanent link")

```md-code__content
pick(
    keys: Union[str, list[str]],
) -> RunnableSerializable[Any, Any]

```

Pick keys from the output dict of this Runnable.

Pick single key

.. code-block:: python

```
import json

from langchain_core.runnables import RunnableLambda, RunnableMap

as_str = RunnableLambda(str)
as_json = RunnableLambda(json.loads)
chain = RunnableMap(str=as_str, json=as_json)

chain.invoke("[1, 2, 3]")
# -> {"str": "[1, 2, 3]", "json": [1, 2, 3]}

json_only_chain = chain.pick("json")
json_only_chain.invoke("[1, 2, 3]")
# -> [1, 2, 3]

```

Pick list of keys

.. code-block:: python

```
from typing import Any

import json

from langchain_core.runnables import RunnableLambda, RunnableMap

as_str = RunnableLambda(str)
as_json = RunnableLambda(json.loads)
def as_bytes(x: Any) -> bytes:
    return bytes(x, "utf-8")

chain = RunnableMap(
    str=as_str,
    json=as_json,
    bytes=RunnableLambda(as_bytes)
)

chain.invoke("[1, 2, 3]")
# -> {"str": "[1, 2, 3]", "json": [1, 2, 3], "bytes": b"[1, 2, 3]"}

json_and_bytes_chain = chain.pick(["json", "bytes"])
json_and_bytes_chain.invoke("[1, 2, 3]")
# -> {"json": [1, 2, 3], "bytes": b"[1, 2, 3]"}

```

### `` assign [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.assign "Permanent link")

```md-code__content
assign(
    **kwargs: Union[\
        Runnable[dict[str, Any], Any],\
        Callable[[dict[str, Any]], Any],\
        Mapping[\
            str,\
            Union[\
                Runnable[dict[str, Any], Any],\
                Callable[[dict[str, Any]], Any],\
            ],\
        ],\
    ],
) -> RunnableSerializable[Any, Any]

```

Assigns new fields to the dict output of this Runnable.

Returns a new Runnable.

.. code-block:: python

```
from langchain_community.llms.fake import FakeStreamingListLLM
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import SystemMessagePromptTemplate
from langchain_core.runnables import Runnable
from operator import itemgetter

prompt = (
    SystemMessagePromptTemplate.from_template("You are a nice assistant.")
    + "{question}"
)
llm = FakeStreamingListLLM(responses=["foo-lish"])

chain: Runnable = prompt | llm | {"str": StrOutputParser()}

chain_with_assign = chain.assign(hello=itemgetter("str") | llm)

print(chain_with_assign.input_schema.model_json_schema())
# {'title': 'PromptInput', 'type': 'object', 'properties':
{'question': {'title': 'Question', 'type': 'string'}}}
print(chain_with_assign.output_schema.model_json_schema())
# {'title': 'RunnableSequenceOutput', 'type': 'object', 'properties':
{'str': {'title': 'Str',
'type': 'string'}, 'hello': {'title': 'Hello', 'type': 'string'}}}

```

### `` batch [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.batch "Permanent link")

```md-code__content
batch(
    inputs: list[Input],
    config: Optional[\
        Union[RunnableConfig, list[RunnableConfig]]\
    ] = None,
    *,
    return_exceptions: bool = False,
    **kwargs: Optional[Any]
) -> list[Output]

```

Default implementation runs invoke in parallel using a thread pool executor.

The default implementation of batch works well for IO bound runnables.

Subclasses should override this method if they can batch more efficiently;
e.g., if the underlying Runnable uses an API which supports a batch mode.

### `` batch\_as\_completed [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.batch_as_completed "Permanent link")

```md-code__content
batch_as_completed(
    inputs: Sequence[Input],
    config: Optional[\
        Union[RunnableConfig, Sequence[RunnableConfig]]\
    ] = None,
    *,
    return_exceptions: bool = False,
    **kwargs: Optional[Any]
) -> Iterator[tuple[int, Union[Output, Exception]]]

```

Run invoke in parallel on a list of inputs.

Yields results as they complete.

### `` abatch`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.abatch "Permanent link")

```md-code__content
abatch(
    inputs: list[Input],
    config: Optional[\
        Union[RunnableConfig, list[RunnableConfig]]\
    ] = None,
    *,
    return_exceptions: bool = False,
    **kwargs: Optional[Any]
) -> list[Output]

```

Default implementation runs ainvoke in parallel using asyncio.gather.

The default implementation of batch works well for IO bound runnables.

Subclasses should override this method if they can batch more efficiently;
e.g., if the underlying Runnable uses an API which supports a batch mode.

Parameters:

- **`inputs`**
( `list[Input]`)
–



A list of inputs to the Runnable.

- **`config`**
( `Optional[Union[RunnableConfig, list[RunnableConfig]]]`, default:
`None`
)
–



A config to use when invoking the Runnable.
The config supports standard keys like 'tags', 'metadata' for tracing
purposes, 'max\_concurrency' for controlling how much work to do
in parallel, and other keys. Please refer to the RunnableConfig
for more details. Defaults to None.

- **`return_exceptions`**
( `bool`, default:
`False`
)
–



Whether to return exceptions instead of raising them.
Defaults to False.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Returns:

- `list[Output]`
–



A list of outputs from the Runnable.


### `` abatch\_as\_completed`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.abatch_as_completed "Permanent link")

```md-code__content
abatch_as_completed(
    inputs: Sequence[Input],
    config: Optional[\
        Union[RunnableConfig, Sequence[RunnableConfig]]\
    ] = None,
    *,
    return_exceptions: bool = False,
    **kwargs: Optional[Any]
) -> AsyncIterator[tuple[int, Union[Output, Exception]]]

```

Run ainvoke in parallel on a list of inputs.

Yields results as they complete.

Parameters:

- **`inputs`**
( `Sequence[Input]`)
–



A list of inputs to the Runnable.

- **`config`**
( `Optional[Union[RunnableConfig, Sequence[RunnableConfig]]]`, default:
`None`
)
–



A config to use when invoking the Runnable.
The config supports standard keys like 'tags', 'metadata' for tracing
purposes, 'max\_concurrency' for controlling how much work to do
in parallel, and other keys. Please refer to the RunnableConfig
for more details. Defaults to None. Defaults to None.

- **`return_exceptions`**
( `bool`, default:
`False`
)
–



Whether to return exceptions instead of raising them.
Defaults to False.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `AsyncIterator[tuple[int, Union[Output, Exception]]]`
–



A tuple of the index of the input and the output from the Runnable.


### `` stream [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.stream "Permanent link")

```md-code__content
stream(
    input: Input,
    config: Optional[RunnableConfig] = None,
    **kwargs: Optional[Any]
) -> Iterator[Output]

```

Default implementation of stream, which calls invoke.

Subclasses should override this method if they support streaming output.

Parameters:

- **`input`**
( `Input`)
–



The input to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable. Defaults to None.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `Output`
–



The output of the Runnable.


### `` astream`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.astream "Permanent link")

```md-code__content
astream(
    input: Input,
    config: Optional[RunnableConfig] = None,
    **kwargs: Optional[Any]
) -> AsyncIterator[Output]

```

Default implementation of astream, which calls ainvoke.

Subclasses should override this method if they support streaming output.

Parameters:

- **`input`**
( `Input`)
–



The input to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable. Defaults to None.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `AsyncIterator[Output]`
–



The output of the Runnable.


### `` astream\_log`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.astream_log "Permanent link")

```md-code__content
astream_log(
    input: Any,
    config: Optional[RunnableConfig] = None,
    *,
    diff: bool = True,
    with_streamed_output_list: bool = True,
    include_names: Optional[Sequence[str]] = None,
    include_types: Optional[Sequence[str]] = None,
    include_tags: Optional[Sequence[str]] = None,
    exclude_names: Optional[Sequence[str]] = None,
    exclude_types: Optional[Sequence[str]] = None,
    exclude_tags: Optional[Sequence[str]] = None,
    **kwargs: Any
) -> Union[\
    AsyncIterator[RunLogPatch], AsyncIterator[RunLog]\
]

```

Stream all output from a Runnable, as reported to the callback system.

This includes all inner runs of LLMs, Retrievers, Tools, etc.

Output is streamed as Log objects, which include a list of
Jsonpatch ops that describe how the state of the run has changed in each
step, and the final state of the run.

The Jsonpatch ops can be applied in order to construct state.

Parameters:

- **`input`**
( `Any`)
–



The input to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable.

- **`diff`**
( `bool`, default:
`True`
)
–



Whether to yield diffs between each step or the current state.

- **`with_streamed_output_list`**
( `bool`, default:
`True`
)
–



Whether to yield the streamed\_output list.

- **`include_names`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include logs with these names.

- **`include_types`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include logs with these types.

- **`include_tags`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include logs with these tags.

- **`exclude_names`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude logs with these names.

- **`exclude_types`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude logs with these types.

- **`exclude_tags`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude logs with these tags.

- **`kwargs`**
( `Any`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `Union[AsyncIterator[RunLogPatch], AsyncIterator[RunLog]]`
–



A RunLogPatch or RunLog object.


### `` astream\_events`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.astream_events "Permanent link")

```md-code__content
astream_events(
    input: Any,
    config: Optional[RunnableConfig] = None,
    *,
    version: Literal["v1", "v2"] = "v2",
    include_names: Optional[Sequence[str]] = None,
    include_types: Optional[Sequence[str]] = None,
    include_tags: Optional[Sequence[str]] = None,
    exclude_names: Optional[Sequence[str]] = None,
    exclude_types: Optional[Sequence[str]] = None,
    exclude_tags: Optional[Sequence[str]] = None,
    **kwargs: Any
) -> AsyncIterator[StreamEvent]

```

Generate a stream of events.

Use to create an iterator over StreamEvents that provide real-time information
about the progress of the Runnable, including StreamEvents from intermediate
results.

A StreamEvent is a dictionary with the following schema:

- `event`: **str** \- Event names are of the
format: on\_\[runnable\_type\]\_(start\|stream\|end).
- `name`: **str** \- The name of the Runnable that generated the event.
- `run_id`: **str** \- randomly generated ID associated with the given execution of
the Runnable that emitted the event.
A child Runnable that gets invoked as part of the execution of a
parent Runnable is assigned its own unique ID.
- `parent_ids`: **list\[str\]** \- The IDs of the parent runnables that
generated the event. The root Runnable will have an empty list.
The order of the parent IDs is from the root to the immediate parent.
Only available for v2 version of the API. The v1 version of the API
will return an empty list.
- `tags`: **Optional\[list\[str\]\]** \- The tags of the Runnable that generated
the event.
- `metadata`: **Optional\[dict\[str, Any\]\]** \- The metadata of the Runnable
that generated the event.
- `data`: **dict\[str, Any\]**

Below is a table that illustrates some events that might be emitted by various
chains. Metadata fields have been omitted from the table for brevity.
Chain definitions have been included after the table.

**ATTENTION** This reference table is for the V2 version of the schema.

+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| event \| name \| chunk \| input \| output \|
+======================+==================+=================================+===============================================+=================================================+
\| on\_chat\_model\_start \| \[model name\] \| \| {"messages": \[\[SystemMessage, HumanMessage\]\]} \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_chat\_model\_stream \| \[model name\] \| AIMessageChunk(content="hello") \| \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_chat\_model\_end \| \[model name\] \| \| {"messages": \[\[SystemMessage, HumanMessage\]\]} \| AIMessageChunk(content="hello world") \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_llm\_start \| \[model name\] \| \| {'input': 'hello'} \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_llm\_stream \| \[model name\] \| 'Hello' \| \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_llm\_end \| \[model name\] \| \| 'Hello human!' \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_chain\_start \| format\_docs \| \| \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_chain\_stream \| format\_docs \| "hello world!, goodbye world!" \| \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_chain\_end \| format\_docs \| \| \[Document(...)\] \| "hello world!, goodbye world!" \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_tool\_start \| some\_tool \| \| {"x": 1, "y": "2"} \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_tool\_end \| some\_tool \| \| \| {"x": 1, "y": "2"} \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_retriever\_start \| \[retriever name\] \| \| {"query": "hello"} \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_retriever\_end \| \[retriever name\] \| \| {"query": "hello"} \| \[Document(...), ..\] \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_prompt\_start \| \[template\_name\] \| \| {"question": "hello"} \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_prompt\_end \| \[template\_name\] \| \| {"question": "hello"} \| ChatPromptValue(messages: \[SystemMessage, ...\]) \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+

In addition to the standard events, users can also dispatch custom events (see example below).

Custom events will be only be surfaced with in the `v2` version of the API!

A custom event has following format:

+-----------+------+-----------------------------------------------------------------------------------------------------------+
\| Attribute \| Type \| Description \|
+===========+======+===========================================================================================================+
\| name \| str \| A user defined name for the event. \|
+-----------+------+-----------------------------------------------------------------------------------------------------------+
\| data \| Any \| The data associated with the event. This can be anything, though we suggest making it JSON serializable. \|
+-----------+------+-----------------------------------------------------------------------------------------------------------+

Here are declarations associated with the standard events shown above:

`format_docs`:

.. code-block:: python

```
def format_docs(docs: list[Document]) -> str:
    '''Format the docs.'''
    return ", ".join([doc.page_content for doc in docs])

format_docs = RunnableLambda(format_docs)

```

`some_tool`:

.. code-block:: python

```
@tool
def some_tool(x: int, y: str) -> dict:
    '''Some_tool.'''
    return {"x": x, "y": y}

```

`prompt`:

.. code-block:: python

```
template = ChatPromptTemplate.from_messages(
    [("system", "You are Cat Agent 007"), ("human", "{question}")]
).with_config({"run_name": "my_template", "tags": ["my_template"]})

```

Example:

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda

async def reverse(s: str) -> str:
    return s[::-1]

chain = RunnableLambda(func=reverse)

events = [\
    event async for event in chain.astream_events("hello", version="v2")\
]

# will produce the following events (run_id, and parent_ids
# has been omitted for brevity):
[\
    {\
        "data": {"input": "hello"},\
        "event": "on_chain_start",\
        "metadata": {},\
        "name": "reverse",\
        "tags": [],\
    },\
    {\
        "data": {"chunk": "olleh"},\
        "event": "on_chain_stream",\
        "metadata": {},\
        "name": "reverse",\
        "tags": [],\
    },\
    {\
        "data": {"output": "olleh"},\
        "event": "on_chain_end",\
        "metadata": {},\
        "name": "reverse",\
        "tags": [],\
    },\
]

```

Example: Dispatch Custom Event

.. code-block:: python

```
from langchain_core.callbacks.manager import (
    adispatch_custom_event,
)
from langchain_core.runnables import RunnableLambda, RunnableConfig
import asyncio

async def slow_thing(some_input: str, config: RunnableConfig) -> str:
    """Do something that takes a long time."""
    await asyncio.sleep(1) # Placeholder for some slow operation
    await adispatch_custom_event(
        "progress_event",
        {"message": "Finished step 1 of 3"},
        config=config # Must be included for python < 3.10
    )
    await asyncio.sleep(1) # Placeholder for some slow operation
    await adispatch_custom_event(
        "progress_event",
        {"message": "Finished step 2 of 3"},
        config=config # Must be included for python < 3.10
    )
    await asyncio.sleep(1) # Placeholder for some slow operation
    return "Done"

slow_thing = RunnableLambda(slow_thing)

async for event in slow_thing.astream_events("some_input", version="v2"):
    print(event)

```

Parameters:

- **`input`**
( `Any`)
–



The input to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable.

- **`version`**
( `Literal['v1', 'v2']`, default:
`'v2'`
)
–



The version of the schema to use either `v2` or `v1`.
Users should use `v2`.
`v1` is for backwards compatibility and will be deprecated
in 0.4.0.
No default will be assigned until the API is stabilized.
custom events will only be surfaced in `v2`.

- **`include_names`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include events from runnables with matching names.

- **`include_types`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include events from runnables with matching types.

- **`include_tags`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include events from runnables with matching tags.

- **`exclude_names`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude events from runnables with matching names.

- **`exclude_types`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude events from runnables with matching types.

- **`exclude_tags`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude events from runnables with matching tags.

- **`kwargs`**
( `Any`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.
These will be passed to astream\_log as this implementation
of astream\_events is built on top of astream\_log.


Yields:

- `AsyncIterator[StreamEvent]`
–



An async stream of StreamEvents.


Raises:

- `NotImplementedError`
–



If the version is not `v1` or `v2`.


### `` transform [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.transform "Permanent link")

```md-code__content
transform(
    input: Iterator[Input],
    config: Optional[RunnableConfig] = None,
    **kwargs: Optional[Any]
) -> Iterator[Output]

```

Default implementation of transform, which buffers input and calls astream.

Subclasses should override this method if they can start producing output while
input is still being generated.

Parameters:

- **`input`**
( `Iterator[Input]`)
–



An iterator of inputs to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable. Defaults to None.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `Output`
–



The output of the Runnable.


### `` atransform`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.atransform "Permanent link")

```md-code__content
atransform(
    input: AsyncIterator[Input],
    config: Optional[RunnableConfig] = None,
    **kwargs: Optional[Any]
) -> AsyncIterator[Output]

```

Default implementation of atransform, which buffers input and calls astream.

Subclasses should override this method if they can start producing output while
input is still being generated.

Parameters:

- **`input`**
( `AsyncIterator[Input]`)
–



An async iterator of inputs to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable. Defaults to None.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `AsyncIterator[Output]`
–



The output of the Runnable.


### `` bind [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.bind "Permanent link")

```md-code__content
bind(**kwargs: Any) -> Runnable[Input, Output]

```

Bind arguments to a Runnable, returning a new Runnable.

Useful when a Runnable in a chain requires an argument that is not
in the output of the previous Runnable or included in the user input.

Parameters:

- **`kwargs`**
( `Any`, default:
`{}`
)
–



The arguments to bind to the Runnable.


Returns:

- `Runnable[Input, Output]`
–



A new Runnable with the arguments bound.


Example:

.. code-block:: python

```
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser

llm = ChatOllama(model='llama2')

# Without bind.
chain = (
    llm
    | StrOutputParser()
)

chain.invoke("Repeat quoted words exactly: 'One two three four five.'")
# Output is 'One two three four five.'

# With bind.
chain = (
    llm.bind(stop=["three"])
    | StrOutputParser()
)

chain.invoke("Repeat quoted words exactly: 'One two three four five.'")
# Output is 'One two'

```

### `` with\_config [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.with_config "Permanent link")

```md-code__content
with_config(
    config: Optional[RunnableConfig] = None, **kwargs: Any
) -> Runnable[Input, Output]

```

Bind config to a Runnable, returning a new Runnable.

Parameters:

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to bind to the Runnable.

- **`kwargs`**
( `Any`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Returns:

- `Runnable[Input, Output]`
–



A new Runnable with the config bound.


### `` with\_listeners [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.with_listeners "Permanent link")

```md-code__content
with_listeners(
    *,
    on_start: Optional[\
        Union[\
            Callable[[Run], None],\
            Callable[[Run, RunnableConfig], None],\
        ]\
    ] = None,
    on_end: Optional[\
        Union[\
            Callable[[Run], None],\
            Callable[[Run, RunnableConfig], None],\
        ]\
    ] = None,
    on_error: Optional[\
        Union[\
            Callable[[Run], None],\
            Callable[[Run, RunnableConfig], None],\
        ]\
    ] = None
) -> Runnable[Input, Output]

```

Bind lifecycle listeners to a Runnable, returning a new Runnable.

on\_start: Called before the Runnable starts running, with the Run object.
on\_end: Called after the Runnable finishes running, with the Run object.
on\_error: Called if the Runnable throws an error, with the Run object.

The Run object contains information about the run, including its id,
type, input, output, error, start\_time, end\_time, and any tags or metadata
added to the run.

Parameters:

- **`on_start`**
( `Optional[Union[Callable[[Run], None], Callable[[Run, RunnableConfig], None]]]`, default:
`None`
)
–



Called before the Runnable starts running. Defaults to None.

- **`on_end`**
( `Optional[Union[Callable[[Run], None], Callable[[Run, RunnableConfig], None]]]`, default:
`None`
)
–



Called after the Runnable finishes running. Defaults to None.

- **`on_error`**
( `Optional[Union[Callable[[Run], None], Callable[[Run, RunnableConfig], None]]]`, default:
`None`
)
–



Called if the Runnable throws an error. Defaults to None.


Returns:

- `Runnable[Input, Output]`
–



A new Runnable with the listeners bound.


Example:

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda
from langchain_core.tracers.schemas import Run

import time

def test_runnable(time_to_sleep : int):
    time.sleep(time_to_sleep)

def fn_start(run_obj: Run):
    print("start_time:", run_obj.start_time)

def fn_end(run_obj: Run):
    print("end_time:", run_obj.end_time)

chain = RunnableLambda(test_runnable).with_listeners(
    on_start=fn_start,
    on_end=fn_end
)
chain.invoke(2)

```

### `` with\_alisteners [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.with_alisteners "Permanent link")

```md-code__content
with_alisteners(
    *,
    on_start: Optional[AsyncListener] = None,
    on_end: Optional[AsyncListener] = None,
    on_error: Optional[AsyncListener] = None
) -> Runnable[Input, Output]

```

Bind async lifecycle listeners to a Runnable, returning a new Runnable.

on\_start: Asynchronously called before the Runnable starts running.
on\_end: Asynchronously called after the Runnable finishes running.
on\_error: Asynchronously called if the Runnable throws an error.

The Run object contains information about the run, including its id,
type, input, output, error, start\_time, end\_time, and any tags or metadata
added to the run.

Parameters:

- **`on_start`**
( `Optional[AsyncListener]`, default:
`None`
)
–



Asynchronously called before the Runnable starts running.
Defaults to None.

- **`on_end`**
( `Optional[AsyncListener]`, default:
`None`
)
–



Asynchronously called after the Runnable finishes running.
Defaults to None.

- **`on_error`**
( `Optional[AsyncListener]`, default:
`None`
)
–



Asynchronously called if the Runnable throws an error.
Defaults to None.


Returns:

- `Runnable[Input, Output]`
–



A new Runnable with the listeners bound.


Example:

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda, Runnable
from datetime import datetime, timezone
import time
import asyncio

def format_t(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()

async def test_runnable(time_to_sleep : int):
    print(f"Runnable[{time_to_sleep}s]: starts at {format_t(time.time())}")
    await asyncio.sleep(time_to_sleep)
    print(f"Runnable[{time_to_sleep}s]: ends at {format_t(time.time())}")

async def fn_start(run_obj : Runnable):
    print(f"on start callback starts at {format_t(time.time())}")
    await asyncio.sleep(3)
    print(f"on start callback ends at {format_t(time.time())}")

async def fn_end(run_obj : Runnable):
    print(f"on end callback starts at {format_t(time.time())}")
    await asyncio.sleep(2)
    print(f"on end callback ends at {format_t(time.time())}")

runnable = RunnableLambda(test_runnable).with_alisteners(
    on_start=fn_start,
    on_end=fn_end
)
async def concurrent_runs():
    await asyncio.gather(runnable.ainvoke(2), runnable.ainvoke(3))

asyncio.run(concurrent_runs())
Result:
on start callback starts at 2025-03-01T07:05:22.875378+00:00
on start callback starts at 2025-03-01T07:05:22.875495+00:00
on start callback ends at 2025-03-01T07:05:25.878862+00:00
on start callback ends at 2025-03-01T07:05:25.878947+00:00
Runnable[2s]: starts at 2025-03-01T07:05:25.879392+00:00
Runnable[3s]: starts at 2025-03-01T07:05:25.879804+00:00
Runnable[2s]: ends at 2025-03-01T07:05:27.881998+00:00
on end callback starts at 2025-03-01T07:05:27.882360+00:00
Runnable[3s]: ends at 2025-03-01T07:05:28.881737+00:00
on end callback starts at 2025-03-01T07:05:28.882428+00:00
on end callback ends at 2025-03-01T07:05:29.883893+00:00
on end callback ends at 2025-03-01T07:05:30.884831+00:00

```

### `` with\_types [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.with_types "Permanent link")

```md-code__content
with_types(
    *,
    input_type: Optional[type[Input]] = None,
    output_type: Optional[type[Output]] = None
) -> Runnable[Input, Output]

```

Bind input and output types to a Runnable, returning a new Runnable.

Parameters:

- **`input_type`**
( `Optional[type[Input]]`, default:
`None`
)
–



The input type to bind to the Runnable. Defaults to None.

- **`output_type`**
( `Optional[type[Output]]`, default:
`None`
)
–



The output type to bind to the Runnable. Defaults to None.


Returns:

- `Runnable[Input, Output]`
–



A new Runnable with the types bound.


### `` with\_retry [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.with_retry "Permanent link")

```md-code__content
with_retry(
    *,
    retry_if_exception_type: tuple[\
        type[BaseException], ...\
    ] = (Exception,),
    wait_exponential_jitter: bool = True,
    exponential_jitter_params: Optional[\
        ExponentialJitterParams\
    ] = None,
    stop_after_attempt: int = 3
) -> Runnable[Input, Output]

```

Create a new Runnable that retries the original Runnable on exceptions.

Parameters:

- **`retry_if_exception_type`**
( `tuple[type[BaseException], ...]`, default:
`(Exception,)`
)
–



A tuple of exception types to retry on.
Defaults to (Exception,).

- **`wait_exponential_jitter`**
( `bool`, default:
`True`
)
–



Whether to add jitter to the wait
time between retries. Defaults to True.

- **`stop_after_attempt`**
( `int`, default:
`3`
)
–



The maximum number of attempts to make before
giving up. Defaults to 3.

- **`exponential_jitter_params`**
( `Optional[ExponentialJitterParams]`, default:
`None`
)
–



Parameters for
`tenacity.wait_exponential_jitter`. Namely: `initial`, `max`,
`exp_base`, and `jitter` (all float values).


Returns:

- `Runnable[Input, Output]`
–



A new Runnable that retries the original Runnable on exceptions.


Example:

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda

count = 0

def _lambda(x: int) -> None:
    global count
    count = count + 1
    if x == 1:
        raise ValueError("x is 1")
    else:
         pass

runnable = RunnableLambda(_lambda)
try:
    runnable.with_retry(
        stop_after_attempt=2,
        retry_if_exception_type=(ValueError,),
    ).invoke(1)
except ValueError:
    pass

assert (count == 2)

```

### `` map [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.map "Permanent link")

```md-code__content
map() -> Runnable[list[Input], list[Output]]

```

Return a new Runnable that maps a list of inputs to a list of outputs.

Calls invoke() with each input.

Returns:

- `Runnable[list[Input], list[Output]]`
–



A new Runnable that maps a list of inputs to a list of outputs.


Example:

```
.. code-block:: python

        from langchain_core.runnables import RunnableLambda

        def _lambda(x: int) -> int:
            return x + 1

        runnable = RunnableLambda(_lambda)
        print(runnable.map().invoke([1, 2, 3])) # [2, 3, 4]

```

### `` with\_fallbacks [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.with_fallbacks "Permanent link")

```md-code__content
with_fallbacks(
    fallbacks: Sequence[Runnable[Input, Output]],
    *,
    exceptions_to_handle: tuple[\
        type[BaseException], ...\
    ] = (Exception,),
    exception_key: Optional[str] = None
) -> RunnableWithFallbacks[Input, Output]

```

Add fallbacks to a Runnable, returning a new Runnable.

The new Runnable will try the original Runnable, and then each fallback
in order, upon failures.

Parameters:

- **`fallbacks`**
( `Sequence[Runnable[Input, Output]]`)
–



A sequence of runnables to try if the original Runnable fails.

- **`exceptions_to_handle`**
( `tuple[type[BaseException], ...]`, default:
`(Exception,)`
)
–



A tuple of exception types to handle.
Defaults to (Exception,).

- **`exception_key`**
( `Optional[str]`, default:
`None`
)
–



If string is specified then handled exceptions will be passed
to fallbacks as part of the input under the specified key. If None,
exceptions will not be passed to fallbacks. If used, the base Runnable
and its fallbacks must accept a dictionary as input. Defaults to None.


Returns:

- `RunnableWithFallbacks[Input, Output]`
–



A new Runnable that will try the original Runnable, and then each

- `RunnableWithFallbacks[Input, Output]`
–



fallback in order, upon failures.


Example:

```
.. code-block:: python

    from typing import Iterator

    from langchain_core.runnables import RunnableGenerator

    def _generate_immediate_error(input: Iterator) -> Iterator[str]:
        raise ValueError()
        yield ""

    def _generate(input: Iterator) -> Iterator[str]:
        yield from "foo bar"

    runnable = RunnableGenerator(_generate_immediate_error).with_fallbacks(
        [RunnableGenerator(_generate)]
        )
    print(''.join(runnable.stream({}))) #foo bar

```

Parameters:

- **`fallbacks`**
( `Sequence[Runnable[Input, Output]]`)
–



A sequence of runnables to try if the original Runnable fails.

- **`exceptions_to_handle`**
( `tuple[type[BaseException], ...]`, default:
`(Exception,)`
)
–



A tuple of exception types to handle.

- **`exception_key`**
( `Optional[str]`, default:
`None`
)
–



If string is specified then handled exceptions will be passed
to fallbacks as part of the input under the specified key. If None,
exceptions will not be passed to fallbacks. If used, the base Runnable
and its fallbacks must accept a dictionary as input.


Returns:

- `RunnableWithFallbacks[Input, Output]`
–



A new Runnable that will try the original Runnable, and then each

- `RunnableWithFallbacks[Input, Output]`
–



fallback in order, upon failures.


### `` as\_tool [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.ToolNode.as_tool "Permanent link")

```md-code__content
as_tool(
    args_schema: Optional[type[BaseModel]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    arg_types: Optional[dict[str, type]] = None
) -> BaseTool

```

Create a BaseTool from a Runnable.

`as_tool` will instantiate a BaseTool with a name, description, and
`args_schema` from a Runnable. Where possible, schemas are inferred
from `runnable.get_input_schema`. Alternatively (e.g., if the
Runnable takes a dict as input and the specific dict keys are not typed),
the schema can be specified directly with `args_schema`. You can also
pass `arg_types` to just specify the required arguments and their types.

Parameters:

- **`args_schema`**
( `Optional[type[BaseModel]]`, default:
`None`
)
–



The schema for the tool. Defaults to None.

- **`name`**
( `Optional[str]`, default:
`None`
)
–



The name of the tool. Defaults to None.

- **`description`**
( `Optional[str]`, default:
`None`
)
–



The description of the tool. Defaults to None.

- **`arg_types`**
( `Optional[dict[str, type]]`, default:
`None`
)
–



A dictionary of argument names to types. Defaults to None.


Returns:

- `BaseTool`
–



A BaseTool instance.


Typed dict input:

.. code-block:: python

```
from typing_extensions import TypedDict
from langchain_core.runnables import RunnableLambda

class Args(TypedDict):
    a: int
    b: list[int]

def f(x: Args) -> str:
    return str(x["a"] * max(x["b"]))

runnable = RunnableLambda(f)
as_tool = runnable.as_tool()
as_tool.invoke({"a": 3, "b": [1, 2]})

```

`dict` input, specifying schema via `args_schema`:

.. code-block:: python

```
from typing import Any
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableLambda

def f(x: dict[str, Any]) -> str:
    return str(x["a"] * max(x["b"]))

class FSchema(BaseModel):
    """Apply a function to an integer and list of integers."""

    a: int = Field(..., description="Integer")
    b: list[int] = Field(..., description="List of ints")

runnable = RunnableLambda(f)
as_tool = runnable.as_tool(FSchema)
as_tool.invoke({"a": 3, "b": [1, 2]})

```

`dict` input, specifying schema via `arg_types`:

.. code-block:: python

```
from typing import Any
from langchain_core.runnables import RunnableLambda

def f(x: dict[str, Any]) -> str:
    return str(x["a"] * max(x["b"]))

runnable = RunnableLambda(f)
as_tool = runnable.as_tool(arg_types={"a": int, "b": list[int]})
as_tool.invoke({"a": 3, "b": [1, 2]})

```

String input:

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda

def f(x: str) -> str:
    return x + "a"

def g(x: str) -> str:
    return x + "z"

runnable = RunnableLambda(f) | g
as_tool = runnable.as_tool()
as_tool.invoke("b")

```

.. versionadded:: 0.2.14

## `` InjectedState [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.InjectedState "Permanent link")

Bases: `InjectedToolArg`

Annotation for a Tool arg that is meant to be populated with the graph state.

Any Tool argument annotated with InjectedState will be hidden from a tool-calling
model, so that the model doesn't attempt to generate the argument. If using
ToolNode, the appropriate graph state field will be automatically injected into
the model-generated tool args.

Parameters:

- **`field`**
( `Optional[str]`, default:
`None`
)
–



The key from state to insert. If None, the entire state is expected to
be passed in.


Example

```md-code__content
from typing import List
from typing_extensions import Annotated, TypedDict

from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.tools import tool

from langgraph.prebuilt import InjectedState, ToolNode

class AgentState(TypedDict):
    messages: List[BaseMessage]
    foo: str

@tool
def state_tool(x: int, state: Annotated[dict, InjectedState]) -> str:
    '''Do something with state.'''
    if len(state["messages"]) > 2:
        return state["foo"] + str(x)
    else:
        return "not enough messages"

@tool
def foo_tool(x: int, foo: Annotated[str, InjectedState("foo")]) -> str:
    '''Do something else with state.'''
    return foo + str(x + 1)

node = ToolNode([state_tool, foo_tool])

tool_call1 = {"name": "state_tool", "args": {"x": 1}, "id": "1", "type": "tool_call"}
tool_call2 = {"name": "foo_tool", "args": {"x": 1}, "id": "2", "type": "tool_call"}
state = {
    "messages": [AIMessage("", tool_calls=[tool_call1, tool_call2])],
    "foo": "bar",
}
node.invoke(state)

```

```md-code__content
[\
    ToolMessage(content='not enough messages', name='state_tool', tool_call_id='1'),\
    ToolMessage(content='bar2', name='foo_tool', tool_call_id='2')\
]

```

## `` InjectedStore [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.InjectedStore "Permanent link")

Bases: `InjectedToolArg`

Annotation for a Tool arg that is meant to be populated with LangGraph store.

Any Tool argument annotated with InjectedStore will be hidden from a tool-calling
model, so that the model doesn't attempt to generate the argument. If using
ToolNode, the appropriate store field will be automatically injected into
the model-generated tool args. Note: if a graph is compiled with a store object,
the store will be automatically propagated to the tools with InjectedStore args
when using ToolNode.

Warning

`InjectedStore` annotation requires `langchain-core >= 0.3.8`

Example

```md-code__content
from typing import Any
from typing_extensions import Annotated

from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from langgraph.store.memory import InMemoryStore
from langgraph.prebuilt import InjectedStore, ToolNode

store = InMemoryStore()
store.put(("values",), "foo", {"bar": 2})

@tool
def store_tool(x: int, my_store: Annotated[Any, InjectedStore()]) -> str:
    '''Do something with store.'''
    stored_value = my_store.get(("values",), "foo").value["bar"]
    return stored_value + x

node = ToolNode([store_tool])

tool_call = {"name": "store_tool", "args": {"x": 1}, "id": "1", "type": "tool_call"}
state = {
    "messages": [AIMessage("", tool_calls=[tool_call])],
}

node.invoke(state, store=store)

```

```md-code__content
{
    "messages": [\
        ToolMessage(content='3', name='store_tool', tool_call_id='1'),\
    ]
}

```

## `` tools\_condition [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_node.tools_condition "Permanent link")

```md-code__content
tools_condition(
    state: Union[\
        list[AnyMessage], dict[str, Any], BaseModel\
    ],
    messages_key: str = "messages",
) -> Literal["tools", "__end__"]

```

Use in the conditional\_edge to route to the ToolNode if the last message

has tool calls. Otherwise, route to the end.

Parameters:

- **`state`**
( `Union[list[AnyMessage], dict[str, Any], BaseModel]`)
–



The state to check for
tool calls. Must have a list of messages (MessageGraph) or have the
"messages" key (StateGraph).


Returns:

- `Literal['tools', '__end__']`
–



The next node to route to.


Examples:

Create a custom ReAct-style agent with tools.

```md-code__content
>>> from langchain_anthropic import ChatAnthropic
>>> from langchain_core.tools import tool
...
>>> from langgraph.graph import StateGraph
>>> from langgraph.prebuilt import ToolNode, tools_condition
>>> from langgraph.graph.message import add_messages
...
>>> from typing import Annotated
>>> from typing_extensions import TypedDict
...
>>> @tool
>>> def divide(a: float, b: float) -> int:
...     """Return a / b."""
...     return a / b
...
>>> llm = ChatAnthropic(model="claude-3-haiku-20240307")
>>> tools = [divide]
...
>>> class State(TypedDict):
...     messages: Annotated[list, add_messages]
>>>
>>> graph_builder = StateGraph(State)
>>> graph_builder.add_node("tools", ToolNode(tools))
>>> graph_builder.add_node("chatbot", lambda state: {"messages":llm.bind_tools(tools).invoke(state['messages'])})
>>> graph_builder.add_edge("tools", "chatbot")
>>> graph_builder.add_conditional_edges(
...     "chatbot", tools_condition
... )
>>> graph_builder.set_entry_point("chatbot")
>>> graph = graph_builder.compile()
>>> graph.invoke({"messages": {"role": "user", "content": "What's 329993 divided by 13662?"}})

```

This module provides a ValidationNode class that can be used to validate tool calls
in a langchain graph. It applies a pydantic schema to tool\_calls in the models' outputs,
and returns a ToolMessage with the validated content. If the schema is not valid, it
returns a ToolMessage with the error message. The ValidationNode can be used in a
StateGraph with a "messages" key or in a MessageGraph. If multiple tool calls are
requested, they will be run in parallel.

Classes:

- **`ValidationNode`**
–



A node that validates all tools requests from the last AIMessage.


## `` ValidationNode [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode "Permanent link")

Bases: `RunnableCallable`

A node that validates all tools requests from the last AIMessage.

It can be used either in StateGraph with a "messages" key or in MessageGraph.

Note

This node does not actually **run** the tools, it only validates the tool calls,
which is useful for extraction and other use cases where you need to generate
structured output that conforms to a complex schema without losing the original
messages and tool IDs (for use in multi-turn conversations).

Parameters:

- **`schemas`**
( `Sequence[Union[BaseTool, Type[BaseModel], Callable]]`)
–



A list of schemas to validate the tool calls with. These can be
any of the following:
\- A pydantic BaseModel class
\- A BaseTool instance (the args\_schema will be used)
\- A function (a schema will be created from the function signature)

- **`format_error`**
( `Optional[Callable[[BaseException, ToolCall, Type[BaseModel]], str]]`, default:
`None`
)
–



A function that takes an exception, a ToolCall, and a schema
and returns a formatted error string. By default, it returns the
exception repr and a message to respond after fixing validation errors.

- **`name`**
( `str`, default:
`'validation'`
)
–



The name of the node.

- **`tags`**
( `Optional[list[str]]`, default:
`None`
)
–



A list of tags to add to the node.


Returns:

- `Union[Dict[str, List[ToolMessage]], Sequence[ToolMessage]]`
–



A list of ToolMessages with the validated content or error messages.


Examples:

Example usage for re-prompting the model to generate a valid response:

```md-code__content
>>> from typing import Literal, Annotated
>>> from typing_extensions import TypedDict
...
>>> from langchain_anthropic import ChatAnthropic
>>> from pydantic import BaseModel, field_validator
...
>>> from langgraph.graph import END, START, StateGraph
>>> from langgraph.prebuilt import ValidationNode
>>> from langgraph.graph.message import add_messages
...
...
>>> class SelectNumber(BaseModel):
...     a: int
...
...     @field_validator("a")
...     def a_must_be_meaningful(cls, v):
...         if v != 37:
...             raise ValueError("Only 37 is allowed")
...         return v
...
...
>>> builder = StateGraph(Annotated[list, add_messages])
>>> llm = ChatAnthropic(model="claude-3-5-haiku-latest").bind_tools([SelectNumber])
>>> builder.add_node("model", llm)
>>> builder.add_node("validation", ValidationNode([SelectNumber]))
>>> builder.add_edge(START, "model")
...
...
>>> def should_validate(state: list) -> Literal["validation", "__end__"]:
...     if state[-1].tool_calls:
...         return "validation"
...     return END
...
...
>>> builder.add_conditional_edges("model", should_validate)
...
...
>>> def should_reprompt(state: list) -> Literal["model", "__end__"]:
...     for msg in state[::-1]:
...         # None of the tool calls were errors
...         if msg.type == "ai":
...             return END
...         if msg.additional_kwargs.get("is_error"):
...             return "model"
...     return END
...
...
>>> builder.add_conditional_edges("validation", should_reprompt)
...
...
>>> graph = builder.compile()
>>> res = graph.invoke(("user", "Select a number, any number"))
>>> # Show the retry logic
>>> for msg in res:
...     msg.pretty_print()
================================ Human Message =================================
Select a number, any number
================================== Ai Message ==================================
[{'id': 'toolu_01JSjT9Pq8hGmTgmMPc6KnvM', 'input': {'a': 42}, 'name': 'SelectNumber', 'type': 'tool_use'}]
Tool Calls:
SelectNumber (toolu_01JSjT9Pq8hGmTgmMPc6KnvM)
Call ID: toolu_01JSjT9Pq8hGmTgmMPc6KnvM
Args:
    a: 42
================================= Tool Message =================================
Name: SelectNumber
ValidationError(model='SelectNumber', errors=[{'loc': ('a',), 'msg': 'Only 37 is allowed', 'type': 'value_error'}])
Respond after fixing all validation errors.
================================== Ai Message ==================================
[{'id': 'toolu_01PkxSVxNxc5wqwCPW1FiSmV', 'input': {'a': 37}, 'name': 'SelectNumber', 'type': 'tool_use'}]
Tool Calls:
SelectNumber (toolu_01PkxSVxNxc5wqwCPW1FiSmV)
Call ID: toolu_01PkxSVxNxc5wqwCPW1FiSmV
Args:
    a: 37
================================= Tool Message =================================
Name: SelectNumber
{"a": 37}

```

Methods:

- **`get_name`**
–



Get the name of the Runnable.

- **`get_input_schema`**
–



Get a pydantic model that can be used to validate input to the Runnable.

- **`get_input_jsonschema`**
–



Get a JSON schema that represents the input to the Runnable.

- **`get_output_schema`**
–



Get a pydantic model that can be used to validate output to the Runnable.

- **`get_output_jsonschema`**
–



Get a JSON schema that represents the output of the Runnable.

- **`config_schema`**
–



The type of config this Runnable accepts specified as a pydantic model.

- **`get_config_jsonschema`**
–



Get a JSON schema that represents the config of the Runnable.

- **`get_graph`**
–



Return a graph representation of this Runnable.

- **`get_prompts`**
–



Return a list of prompts used by this Runnable.

- **`__or__`**
–



Compose this Runnable with another object to create a RunnableSequence.

- **`__ror__`**
–



Compose this Runnable with another object to create a RunnableSequence.

- **`pipe`**
–



Compose this Runnable with Runnable-like objects to make a RunnableSequence.

- **`pick`**
–



Pick keys from the output dict of this Runnable.

- **`assign`**
–



Assigns new fields to the dict output of this Runnable.

- **`batch`**
–



Default implementation runs invoke in parallel using a thread pool executor.

- **`batch_as_completed`**
–



Run invoke in parallel on a list of inputs.

- **`abatch`**
–



Default implementation runs ainvoke in parallel using asyncio.gather.

- **`abatch_as_completed`**
–



Run ainvoke in parallel on a list of inputs.

- **`stream`**
–



Default implementation of stream, which calls invoke.

- **`astream`**
–



Default implementation of astream, which calls ainvoke.

- **`astream_log`**
–



Stream all output from a Runnable, as reported to the callback system.

- **`astream_events`**
–



Generate a stream of events.

- **`transform`**
–



Default implementation of transform, which buffers input and calls astream.

- **`atransform`**
–



Default implementation of atransform, which buffers input and calls astream.

- **`bind`**
–



Bind arguments to a Runnable, returning a new Runnable.

- **`with_config`**
–



Bind config to a Runnable, returning a new Runnable.

- **`with_listeners`**
–



Bind lifecycle listeners to a Runnable, returning a new Runnable.

- **`with_alisteners`**
–



Bind async lifecycle listeners to a Runnable, returning a new Runnable.

- **`with_types`**
–



Bind input and output types to a Runnable, returning a new Runnable.

- **`with_retry`**
–



Create a new Runnable that retries the original Runnable on exceptions.

- **`map`**
–



Return a new Runnable that maps a list of inputs to a list of outputs.

- **`with_fallbacks`**
–



Add fallbacks to a Runnable, returning a new Runnable.

- **`as_tool`**
–



Create a BaseTool from a Runnable.


Attributes:

- **`InputType`**
( `type[Input]`)
–



The type of input this Runnable accepts specified as a type annotation.

- **`OutputType`**
( `type[Output]`)
–



The type of output this Runnable produces specified as a type annotation.

- **`input_schema`**
( `type[BaseModel]`)
–



The type of input this Runnable accepts specified as a pydantic model.

- **`output_schema`**
( `type[BaseModel]`)
–



The type of output this Runnable produces specified as a pydantic model.

- **`config_specs`**
( `list[ConfigurableFieldSpec]`)
–



List configurable fields for this Runnable.


### `` InputType`property`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.InputType "Permanent link")

```md-code__content
InputType: type[Input]

```

The type of input this Runnable accepts specified as a type annotation.

### `` OutputType`property`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.OutputType "Permanent link")

```md-code__content
OutputType: type[Output]

```

The type of output this Runnable produces specified as a type annotation.

### `` input\_schema`property`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.input_schema "Permanent link")

```md-code__content
input_schema: type[BaseModel]

```

The type of input this Runnable accepts specified as a pydantic model.

### `` output\_schema`property`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.output_schema "Permanent link")

```md-code__content
output_schema: type[BaseModel]

```

The type of output this Runnable produces specified as a pydantic model.

### `` config\_specs`property`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.config_specs "Permanent link")

```md-code__content
config_specs: list[ConfigurableFieldSpec]

```

List configurable fields for this Runnable.

### `` get\_name [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.get_name "Permanent link")

```md-code__content
get_name(
    suffix: Optional[str] = None,
    *,
    name: Optional[str] = None
) -> str

```

Get the name of the Runnable.

### `` get\_input\_schema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.get_input_schema "Permanent link")

```md-code__content
get_input_schema(
    config: Optional[RunnableConfig] = None,
) -> type[BaseModel]

```

Get a pydantic model that can be used to validate input to the Runnable.

Runnables that leverage the configurable\_fields and configurable\_alternatives
methods will have a dynamic input schema that depends on which
configuration the Runnable is invoked with.

This method allows to get an input schema for a specific configuration.

Parameters:

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



A config to use when generating the schema.


Returns:

- `type[BaseModel]`
–



A pydantic model that can be used to validate input.


### `` get\_input\_jsonschema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.get_input_jsonschema "Permanent link")

```md-code__content
get_input_jsonschema(
    config: Optional[RunnableConfig] = None,
) -> dict[str, Any]

```

Get a JSON schema that represents the input to the Runnable.

Parameters:

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



A config to use when generating the schema.


Returns:

- `dict[str, Any]`
–



A JSON schema that represents the input to the Runnable.


Example:

```
.. code-block:: python

    from langchain_core.runnables import RunnableLambda

    def add_one(x: int) -> int:
        return x + 1

    runnable = RunnableLambda(add_one)

    print(runnable.get_input_jsonschema())

```

.. versionadded:: 0.3.0

### `` get\_output\_schema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.get_output_schema "Permanent link")

```md-code__content
get_output_schema(
    config: Optional[RunnableConfig] = None,
) -> type[BaseModel]

```

Get a pydantic model that can be used to validate output to the Runnable.

Runnables that leverage the configurable\_fields and configurable\_alternatives
methods will have a dynamic output schema that depends on which
configuration the Runnable is invoked with.

This method allows to get an output schema for a specific configuration.

Parameters:

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



A config to use when generating the schema.


Returns:

- `type[BaseModel]`
–



A pydantic model that can be used to validate output.


### `` get\_output\_jsonschema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.get_output_jsonschema "Permanent link")

```md-code__content
get_output_jsonschema(
    config: Optional[RunnableConfig] = None,
) -> dict[str, Any]

```

Get a JSON schema that represents the output of the Runnable.

Parameters:

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



A config to use when generating the schema.


Returns:

- `dict[str, Any]`
–



A JSON schema that represents the output of the Runnable.


Example:

```
.. code-block:: python

    from langchain_core.runnables import RunnableLambda

    def add_one(x: int) -> int:
        return x + 1

    runnable = RunnableLambda(add_one)

    print(runnable.get_output_jsonschema())

```

.. versionadded:: 0.3.0

### `` config\_schema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.config_schema "Permanent link")

```md-code__content
config_schema(
    *, include: Optional[Sequence[str]] = None
) -> type[BaseModel]

```

The type of config this Runnable accepts specified as a pydantic model.

To mark a field as configurable, see the `configurable_fields`
and `configurable_alternatives` methods.

Parameters:

- **`include`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



A list of fields to include in the config schema.


Returns:

- `type[BaseModel]`
–



A pydantic model that can be used to validate config.


### `` get\_config\_jsonschema [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.get_config_jsonschema "Permanent link")

```md-code__content
get_config_jsonschema(
    *, include: Optional[Sequence[str]] = None
) -> dict[str, Any]

```

Get a JSON schema that represents the config of the Runnable.

Parameters:

- **`include`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



A list of fields to include in the config schema.


Returns:

- `dict[str, Any]`
–



A JSON schema that represents the config of the Runnable.


.. versionadded:: 0.3.0

### `` get\_graph [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.get_graph "Permanent link")

```md-code__content
get_graph(config: Optional[RunnableConfig] = None) -> Graph

```

Return a graph representation of this Runnable.

### `` get\_prompts [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.get_prompts "Permanent link")

```md-code__content
get_prompts(
    config: Optional[RunnableConfig] = None,
) -> list[BasePromptTemplate]

```

Return a list of prompts used by this Runnable.

### ``\_\_or\_\_ [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.__or__ "Permanent link")

```md-code__content
__or__(
    other: Union[\
        Runnable[Any, Other],\
        Callable[[Any], Other],\
        Callable[[Iterator[Any]], Iterator[Other]],\
        Mapping[\
            str,\
            Union[\
                Runnable[Any, Other],\
                Callable[[Any], Other],\
                Any,\
            ],\
        ],\
    ],
) -> RunnableSerializable[Input, Other]

```

Compose this Runnable with another object to create a RunnableSequence.

### ``\_\_ror\_\_ [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.__ror__ "Permanent link")

```md-code__content
__ror__(
    other: Union[\
        Runnable[Other, Any],\
        Callable[[Other], Any],\
        Callable[[Iterator[Other]], Iterator[Any]],\
        Mapping[\
            str,\
            Union[\
                Runnable[Other, Any],\
                Callable[[Other], Any],\
                Any,\
            ],\
        ],\
    ],
) -> RunnableSerializable[Other, Output]

```

Compose this Runnable with another object to create a RunnableSequence.

### `` pipe [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.pipe "Permanent link")

```md-code__content
pipe(
    *others: Union[\
        Runnable[Any, Other], Callable[[Any], Other]\
    ],
    name: Optional[str] = None
) -> RunnableSerializable[Input, Other]

```

Compose this Runnable with Runnable-like objects to make a RunnableSequence.

Equivalent to `RunnableSequence(self, *others)` or `self | others[0] | ...`

Example

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda

def add_one(x: int) -> int:
    return x + 1

def mul_two(x: int) -> int:
    return x * 2

runnable_1 = RunnableLambda(add_one)
runnable_2 = RunnableLambda(mul_two)
sequence = runnable_1.pipe(runnable_2)
# Or equivalently:
# sequence = runnable_1 | runnable_2
# sequence = RunnableSequence(first=runnable_1, last=runnable_2)
sequence.invoke(1)
await sequence.ainvoke(1)
# -> 4

sequence.batch([1, 2, 3])
await sequence.abatch([1, 2, 3])
# -> [4, 6, 8]

```

### `` pick [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.pick "Permanent link")

```md-code__content
pick(
    keys: Union[str, list[str]],
) -> RunnableSerializable[Any, Any]

```

Pick keys from the output dict of this Runnable.

Pick single key

.. code-block:: python

```
import json

from langchain_core.runnables import RunnableLambda, RunnableMap

as_str = RunnableLambda(str)
as_json = RunnableLambda(json.loads)
chain = RunnableMap(str=as_str, json=as_json)

chain.invoke("[1, 2, 3]")
# -> {"str": "[1, 2, 3]", "json": [1, 2, 3]}

json_only_chain = chain.pick("json")
json_only_chain.invoke("[1, 2, 3]")
# -> [1, 2, 3]

```

Pick list of keys

.. code-block:: python

```
from typing import Any

import json

from langchain_core.runnables import RunnableLambda, RunnableMap

as_str = RunnableLambda(str)
as_json = RunnableLambda(json.loads)
def as_bytes(x: Any) -> bytes:
    return bytes(x, "utf-8")

chain = RunnableMap(
    str=as_str,
    json=as_json,
    bytes=RunnableLambda(as_bytes)
)

chain.invoke("[1, 2, 3]")
# -> {"str": "[1, 2, 3]", "json": [1, 2, 3], "bytes": b"[1, 2, 3]"}

json_and_bytes_chain = chain.pick(["json", "bytes"])
json_and_bytes_chain.invoke("[1, 2, 3]")
# -> {"json": [1, 2, 3], "bytes": b"[1, 2, 3]"}

```

### `` assign [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.assign "Permanent link")

```md-code__content
assign(
    **kwargs: Union[\
        Runnable[dict[str, Any], Any],\
        Callable[[dict[str, Any]], Any],\
        Mapping[\
            str,\
            Union[\
                Runnable[dict[str, Any], Any],\
                Callable[[dict[str, Any]], Any],\
            ],\
        ],\
    ],
) -> RunnableSerializable[Any, Any]

```

Assigns new fields to the dict output of this Runnable.

Returns a new Runnable.

.. code-block:: python

```
from langchain_community.llms.fake import FakeStreamingListLLM
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import SystemMessagePromptTemplate
from langchain_core.runnables import Runnable
from operator import itemgetter

prompt = (
    SystemMessagePromptTemplate.from_template("You are a nice assistant.")
    + "{question}"
)
llm = FakeStreamingListLLM(responses=["foo-lish"])

chain: Runnable = prompt | llm | {"str": StrOutputParser()}

chain_with_assign = chain.assign(hello=itemgetter("str") | llm)

print(chain_with_assign.input_schema.model_json_schema())
# {'title': 'PromptInput', 'type': 'object', 'properties':
{'question': {'title': 'Question', 'type': 'string'}}}
print(chain_with_assign.output_schema.model_json_schema())
# {'title': 'RunnableSequenceOutput', 'type': 'object', 'properties':
{'str': {'title': 'Str',
'type': 'string'}, 'hello': {'title': 'Hello', 'type': 'string'}}}

```

### `` batch [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.batch "Permanent link")

```md-code__content
batch(
    inputs: list[Input],
    config: Optional[\
        Union[RunnableConfig, list[RunnableConfig]]\
    ] = None,
    *,
    return_exceptions: bool = False,
    **kwargs: Optional[Any]
) -> list[Output]

```

Default implementation runs invoke in parallel using a thread pool executor.

The default implementation of batch works well for IO bound runnables.

Subclasses should override this method if they can batch more efficiently;
e.g., if the underlying Runnable uses an API which supports a batch mode.

### `` batch\_as\_completed [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.batch_as_completed "Permanent link")

```md-code__content
batch_as_completed(
    inputs: Sequence[Input],
    config: Optional[\
        Union[RunnableConfig, Sequence[RunnableConfig]]\
    ] = None,
    *,
    return_exceptions: bool = False,
    **kwargs: Optional[Any]
) -> Iterator[tuple[int, Union[Output, Exception]]]

```

Run invoke in parallel on a list of inputs.

Yields results as they complete.

### `` abatch`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.abatch "Permanent link")

```md-code__content
abatch(
    inputs: list[Input],
    config: Optional[\
        Union[RunnableConfig, list[RunnableConfig]]\
    ] = None,
    *,
    return_exceptions: bool = False,
    **kwargs: Optional[Any]
) -> list[Output]

```

Default implementation runs ainvoke in parallel using asyncio.gather.

The default implementation of batch works well for IO bound runnables.

Subclasses should override this method if they can batch more efficiently;
e.g., if the underlying Runnable uses an API which supports a batch mode.

Parameters:

- **`inputs`**
( `list[Input]`)
–



A list of inputs to the Runnable.

- **`config`**
( `Optional[Union[RunnableConfig, list[RunnableConfig]]]`, default:
`None`
)
–



A config to use when invoking the Runnable.
The config supports standard keys like 'tags', 'metadata' for tracing
purposes, 'max\_concurrency' for controlling how much work to do
in parallel, and other keys. Please refer to the RunnableConfig
for more details. Defaults to None.

- **`return_exceptions`**
( `bool`, default:
`False`
)
–



Whether to return exceptions instead of raising them.
Defaults to False.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Returns:

- `list[Output]`
–



A list of outputs from the Runnable.


### `` abatch\_as\_completed`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.abatch_as_completed "Permanent link")

```md-code__content
abatch_as_completed(
    inputs: Sequence[Input],
    config: Optional[\
        Union[RunnableConfig, Sequence[RunnableConfig]]\
    ] = None,
    *,
    return_exceptions: bool = False,
    **kwargs: Optional[Any]
) -> AsyncIterator[tuple[int, Union[Output, Exception]]]

```

Run ainvoke in parallel on a list of inputs.

Yields results as they complete.

Parameters:

- **`inputs`**
( `Sequence[Input]`)
–



A list of inputs to the Runnable.

- **`config`**
( `Optional[Union[RunnableConfig, Sequence[RunnableConfig]]]`, default:
`None`
)
–



A config to use when invoking the Runnable.
The config supports standard keys like 'tags', 'metadata' for tracing
purposes, 'max\_concurrency' for controlling how much work to do
in parallel, and other keys. Please refer to the RunnableConfig
for more details. Defaults to None. Defaults to None.

- **`return_exceptions`**
( `bool`, default:
`False`
)
–



Whether to return exceptions instead of raising them.
Defaults to False.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `AsyncIterator[tuple[int, Union[Output, Exception]]]`
–



A tuple of the index of the input and the output from the Runnable.


### `` stream [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.stream "Permanent link")

```md-code__content
stream(
    input: Input,
    config: Optional[RunnableConfig] = None,
    **kwargs: Optional[Any]
) -> Iterator[Output]

```

Default implementation of stream, which calls invoke.

Subclasses should override this method if they support streaming output.

Parameters:

- **`input`**
( `Input`)
–



The input to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable. Defaults to None.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `Output`
–



The output of the Runnable.


### `` astream`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.astream "Permanent link")

```md-code__content
astream(
    input: Input,
    config: Optional[RunnableConfig] = None,
    **kwargs: Optional[Any]
) -> AsyncIterator[Output]

```

Default implementation of astream, which calls ainvoke.

Subclasses should override this method if they support streaming output.

Parameters:

- **`input`**
( `Input`)
–



The input to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable. Defaults to None.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `AsyncIterator[Output]`
–



The output of the Runnable.


### `` astream\_log`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.astream_log "Permanent link")

```md-code__content
astream_log(
    input: Any,
    config: Optional[RunnableConfig] = None,
    *,
    diff: bool = True,
    with_streamed_output_list: bool = True,
    include_names: Optional[Sequence[str]] = None,
    include_types: Optional[Sequence[str]] = None,
    include_tags: Optional[Sequence[str]] = None,
    exclude_names: Optional[Sequence[str]] = None,
    exclude_types: Optional[Sequence[str]] = None,
    exclude_tags: Optional[Sequence[str]] = None,
    **kwargs: Any
) -> Union[\
    AsyncIterator[RunLogPatch], AsyncIterator[RunLog]\
]

```

Stream all output from a Runnable, as reported to the callback system.

This includes all inner runs of LLMs, Retrievers, Tools, etc.

Output is streamed as Log objects, which include a list of
Jsonpatch ops that describe how the state of the run has changed in each
step, and the final state of the run.

The Jsonpatch ops can be applied in order to construct state.

Parameters:

- **`input`**
( `Any`)
–



The input to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable.

- **`diff`**
( `bool`, default:
`True`
)
–



Whether to yield diffs between each step or the current state.

- **`with_streamed_output_list`**
( `bool`, default:
`True`
)
–



Whether to yield the streamed\_output list.

- **`include_names`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include logs with these names.

- **`include_types`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include logs with these types.

- **`include_tags`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include logs with these tags.

- **`exclude_names`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude logs with these names.

- **`exclude_types`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude logs with these types.

- **`exclude_tags`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude logs with these tags.

- **`kwargs`**
( `Any`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `Union[AsyncIterator[RunLogPatch], AsyncIterator[RunLog]]`
–



A RunLogPatch or RunLog object.


### `` astream\_events`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.astream_events "Permanent link")

```md-code__content
astream_events(
    input: Any,
    config: Optional[RunnableConfig] = None,
    *,
    version: Literal["v1", "v2"] = "v2",
    include_names: Optional[Sequence[str]] = None,
    include_types: Optional[Sequence[str]] = None,
    include_tags: Optional[Sequence[str]] = None,
    exclude_names: Optional[Sequence[str]] = None,
    exclude_types: Optional[Sequence[str]] = None,
    exclude_tags: Optional[Sequence[str]] = None,
    **kwargs: Any
) -> AsyncIterator[StreamEvent]

```

Generate a stream of events.

Use to create an iterator over StreamEvents that provide real-time information
about the progress of the Runnable, including StreamEvents from intermediate
results.

A StreamEvent is a dictionary with the following schema:

- `event`: **str** \- Event names are of the
format: on\_\[runnable\_type\]\_(start\|stream\|end).
- `name`: **str** \- The name of the Runnable that generated the event.
- `run_id`: **str** \- randomly generated ID associated with the given execution of
the Runnable that emitted the event.
A child Runnable that gets invoked as part of the execution of a
parent Runnable is assigned its own unique ID.
- `parent_ids`: **list\[str\]** \- The IDs of the parent runnables that
generated the event. The root Runnable will have an empty list.
The order of the parent IDs is from the root to the immediate parent.
Only available for v2 version of the API. The v1 version of the API
will return an empty list.
- `tags`: **Optional\[list\[str\]\]** \- The tags of the Runnable that generated
the event.
- `metadata`: **Optional\[dict\[str, Any\]\]** \- The metadata of the Runnable
that generated the event.
- `data`: **dict\[str, Any\]**

Below is a table that illustrates some events that might be emitted by various
chains. Metadata fields have been omitted from the table for brevity.
Chain definitions have been included after the table.

**ATTENTION** This reference table is for the V2 version of the schema.

+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| event \| name \| chunk \| input \| output \|
+======================+==================+=================================+===============================================+=================================================+
\| on\_chat\_model\_start \| \[model name\] \| \| {"messages": \[\[SystemMessage, HumanMessage\]\]} \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_chat\_model\_stream \| \[model name\] \| AIMessageChunk(content="hello") \| \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_chat\_model\_end \| \[model name\] \| \| {"messages": \[\[SystemMessage, HumanMessage\]\]} \| AIMessageChunk(content="hello world") \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_llm\_start \| \[model name\] \| \| {'input': 'hello'} \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_llm\_stream \| \[model name\] \| 'Hello' \| \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_llm\_end \| \[model name\] \| \| 'Hello human!' \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_chain\_start \| format\_docs \| \| \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_chain\_stream \| format\_docs \| "hello world!, goodbye world!" \| \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_chain\_end \| format\_docs \| \| \[Document(...)\] \| "hello world!, goodbye world!" \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_tool\_start \| some\_tool \| \| {"x": 1, "y": "2"} \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_tool\_end \| some\_tool \| \| \| {"x": 1, "y": "2"} \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_retriever\_start \| \[retriever name\] \| \| {"query": "hello"} \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_retriever\_end \| \[retriever name\] \| \| {"query": "hello"} \| \[Document(...), ..\] \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_prompt\_start \| \[template\_name\] \| \| {"question": "hello"} \| \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+
\| on\_prompt\_end \| \[template\_name\] \| \| {"question": "hello"} \| ChatPromptValue(messages: \[SystemMessage, ...\]) \|
+----------------------+------------------+---------------------------------+-----------------------------------------------+-------------------------------------------------+

In addition to the standard events, users can also dispatch custom events (see example below).

Custom events will be only be surfaced with in the `v2` version of the API!

A custom event has following format:

+-----------+------+-----------------------------------------------------------------------------------------------------------+
\| Attribute \| Type \| Description \|
+===========+======+===========================================================================================================+
\| name \| str \| A user defined name for the event. \|
+-----------+------+-----------------------------------------------------------------------------------------------------------+
\| data \| Any \| The data associated with the event. This can be anything, though we suggest making it JSON serializable. \|
+-----------+------+-----------------------------------------------------------------------------------------------------------+

Here are declarations associated with the standard events shown above:

`format_docs`:

.. code-block:: python

```
def format_docs(docs: list[Document]) -> str:
    '''Format the docs.'''
    return ", ".join([doc.page_content for doc in docs])

format_docs = RunnableLambda(format_docs)

```

`some_tool`:

.. code-block:: python

```
@tool
def some_tool(x: int, y: str) -> dict:
    '''Some_tool.'''
    return {"x": x, "y": y}

```

`prompt`:

.. code-block:: python

```
template = ChatPromptTemplate.from_messages(
    [("system", "You are Cat Agent 007"), ("human", "{question}")]
).with_config({"run_name": "my_template", "tags": ["my_template"]})

```

Example:

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda

async def reverse(s: str) -> str:
    return s[::-1]

chain = RunnableLambda(func=reverse)

events = [\
    event async for event in chain.astream_events("hello", version="v2")\
]

# will produce the following events (run_id, and parent_ids
# has been omitted for brevity):
[\
    {\
        "data": {"input": "hello"},\
        "event": "on_chain_start",\
        "metadata": {},\
        "name": "reverse",\
        "tags": [],\
    },\
    {\
        "data": {"chunk": "olleh"},\
        "event": "on_chain_stream",\
        "metadata": {},\
        "name": "reverse",\
        "tags": [],\
    },\
    {\
        "data": {"output": "olleh"},\
        "event": "on_chain_end",\
        "metadata": {},\
        "name": "reverse",\
        "tags": [],\
    },\
]

```

Example: Dispatch Custom Event

.. code-block:: python

```
from langchain_core.callbacks.manager import (
    adispatch_custom_event,
)
from langchain_core.runnables import RunnableLambda, RunnableConfig
import asyncio

async def slow_thing(some_input: str, config: RunnableConfig) -> str:
    """Do something that takes a long time."""
    await asyncio.sleep(1) # Placeholder for some slow operation
    await adispatch_custom_event(
        "progress_event",
        {"message": "Finished step 1 of 3"},
        config=config # Must be included for python < 3.10
    )
    await asyncio.sleep(1) # Placeholder for some slow operation
    await adispatch_custom_event(
        "progress_event",
        {"message": "Finished step 2 of 3"},
        config=config # Must be included for python < 3.10
    )
    await asyncio.sleep(1) # Placeholder for some slow operation
    return "Done"

slow_thing = RunnableLambda(slow_thing)

async for event in slow_thing.astream_events("some_input", version="v2"):
    print(event)

```

Parameters:

- **`input`**
( `Any`)
–



The input to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable.

- **`version`**
( `Literal['v1', 'v2']`, default:
`'v2'`
)
–



The version of the schema to use either `v2` or `v1`.
Users should use `v2`.
`v1` is for backwards compatibility and will be deprecated
in 0.4.0.
No default will be assigned until the API is stabilized.
custom events will only be surfaced in `v2`.

- **`include_names`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include events from runnables with matching names.

- **`include_types`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include events from runnables with matching types.

- **`include_tags`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Only include events from runnables with matching tags.

- **`exclude_names`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude events from runnables with matching names.

- **`exclude_types`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude events from runnables with matching types.

- **`exclude_tags`**
( `Optional[Sequence[str]]`, default:
`None`
)
–



Exclude events from runnables with matching tags.

- **`kwargs`**
( `Any`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.
These will be passed to astream\_log as this implementation
of astream\_events is built on top of astream\_log.


Yields:

- `AsyncIterator[StreamEvent]`
–



An async stream of StreamEvents.


Raises:

- `NotImplementedError`
–



If the version is not `v1` or `v2`.


### `` transform [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.transform "Permanent link")

```md-code__content
transform(
    input: Iterator[Input],
    config: Optional[RunnableConfig] = None,
    **kwargs: Optional[Any]
) -> Iterator[Output]

```

Default implementation of transform, which buffers input and calls astream.

Subclasses should override this method if they can start producing output while
input is still being generated.

Parameters:

- **`input`**
( `Iterator[Input]`)
–



An iterator of inputs to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable. Defaults to None.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `Output`
–



The output of the Runnable.


### `` atransform`async`[¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.atransform "Permanent link")

```md-code__content
atransform(
    input: AsyncIterator[Input],
    config: Optional[RunnableConfig] = None,
    **kwargs: Optional[Any]
) -> AsyncIterator[Output]

```

Default implementation of atransform, which buffers input and calls astream.

Subclasses should override this method if they can start producing output while
input is still being generated.

Parameters:

- **`input`**
( `AsyncIterator[Input]`)
–



An async iterator of inputs to the Runnable.

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to use for the Runnable. Defaults to None.

- **`kwargs`**
( `Optional[Any]`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Yields:

- `AsyncIterator[Output]`
–



The output of the Runnable.


### `` bind [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.bind "Permanent link")

```md-code__content
bind(**kwargs: Any) -> Runnable[Input, Output]

```

Bind arguments to a Runnable, returning a new Runnable.

Useful when a Runnable in a chain requires an argument that is not
in the output of the previous Runnable or included in the user input.

Parameters:

- **`kwargs`**
( `Any`, default:
`{}`
)
–



The arguments to bind to the Runnable.


Returns:

- `Runnable[Input, Output]`
–



A new Runnable with the arguments bound.


Example:

.. code-block:: python

```
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser

llm = ChatOllama(model='llama2')

# Without bind.
chain = (
    llm
    | StrOutputParser()
)

chain.invoke("Repeat quoted words exactly: 'One two three four five.'")
# Output is 'One two three four five.'

# With bind.
chain = (
    llm.bind(stop=["three"])
    | StrOutputParser()
)

chain.invoke("Repeat quoted words exactly: 'One two three four five.'")
# Output is 'One two'

```

### `` with\_config [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.with_config "Permanent link")

```md-code__content
with_config(
    config: Optional[RunnableConfig] = None, **kwargs: Any
) -> Runnable[Input, Output]

```

Bind config to a Runnable, returning a new Runnable.

Parameters:

- **`config`**
( `Optional[RunnableConfig]`, default:
`None`
)
–



The config to bind to the Runnable.

- **`kwargs`**
( `Any`, default:
`{}`
)
–



Additional keyword arguments to pass to the Runnable.


Returns:

- `Runnable[Input, Output]`
–



A new Runnable with the config bound.


### `` with\_listeners [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.with_listeners "Permanent link")

```md-code__content
with_listeners(
    *,
    on_start: Optional[\
        Union[\
            Callable[[Run], None],\
            Callable[[Run, RunnableConfig], None],\
        ]\
    ] = None,
    on_end: Optional[\
        Union[\
            Callable[[Run], None],\
            Callable[[Run, RunnableConfig], None],\
        ]\
    ] = None,
    on_error: Optional[\
        Union[\
            Callable[[Run], None],\
            Callable[[Run, RunnableConfig], None],\
        ]\
    ] = None
) -> Runnable[Input, Output]

```

Bind lifecycle listeners to a Runnable, returning a new Runnable.

on\_start: Called before the Runnable starts running, with the Run object.
on\_end: Called after the Runnable finishes running, with the Run object.
on\_error: Called if the Runnable throws an error, with the Run object.

The Run object contains information about the run, including its id,
type, input, output, error, start\_time, end\_time, and any tags or metadata
added to the run.

Parameters:

- **`on_start`**
( `Optional[Union[Callable[[Run], None], Callable[[Run, RunnableConfig], None]]]`, default:
`None`
)
–



Called before the Runnable starts running. Defaults to None.

- **`on_end`**
( `Optional[Union[Callable[[Run], None], Callable[[Run, RunnableConfig], None]]]`, default:
`None`
)
–



Called after the Runnable finishes running. Defaults to None.

- **`on_error`**
( `Optional[Union[Callable[[Run], None], Callable[[Run, RunnableConfig], None]]]`, default:
`None`
)
–



Called if the Runnable throws an error. Defaults to None.


Returns:

- `Runnable[Input, Output]`
–



A new Runnable with the listeners bound.


Example:

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda
from langchain_core.tracers.schemas import Run

import time

def test_runnable(time_to_sleep : int):
    time.sleep(time_to_sleep)

def fn_start(run_obj: Run):
    print("start_time:", run_obj.start_time)

def fn_end(run_obj: Run):
    print("end_time:", run_obj.end_time)

chain = RunnableLambda(test_runnable).with_listeners(
    on_start=fn_start,
    on_end=fn_end
)
chain.invoke(2)

```

### `` with\_alisteners [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.with_alisteners "Permanent link")

```md-code__content
with_alisteners(
    *,
    on_start: Optional[AsyncListener] = None,
    on_end: Optional[AsyncListener] = None,
    on_error: Optional[AsyncListener] = None
) -> Runnable[Input, Output]

```

Bind async lifecycle listeners to a Runnable, returning a new Runnable.

on\_start: Asynchronously called before the Runnable starts running.
on\_end: Asynchronously called after the Runnable finishes running.
on\_error: Asynchronously called if the Runnable throws an error.

The Run object contains information about the run, including its id,
type, input, output, error, start\_time, end\_time, and any tags or metadata
added to the run.

Parameters:

- **`on_start`**
( `Optional[AsyncListener]`, default:
`None`
)
–



Asynchronously called before the Runnable starts running.
Defaults to None.

- **`on_end`**
( `Optional[AsyncListener]`, default:
`None`
)
–



Asynchronously called after the Runnable finishes running.
Defaults to None.

- **`on_error`**
( `Optional[AsyncListener]`, default:
`None`
)
–



Asynchronously called if the Runnable throws an error.
Defaults to None.


Returns:

- `Runnable[Input, Output]`
–



A new Runnable with the listeners bound.


Example:

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda, Runnable
from datetime import datetime, timezone
import time
import asyncio

def format_t(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()

async def test_runnable(time_to_sleep : int):
    print(f"Runnable[{time_to_sleep}s]: starts at {format_t(time.time())}")
    await asyncio.sleep(time_to_sleep)
    print(f"Runnable[{time_to_sleep}s]: ends at {format_t(time.time())}")

async def fn_start(run_obj : Runnable):
    print(f"on start callback starts at {format_t(time.time())}")
    await asyncio.sleep(3)
    print(f"on start callback ends at {format_t(time.time())}")

async def fn_end(run_obj : Runnable):
    print(f"on end callback starts at {format_t(time.time())}")
    await asyncio.sleep(2)
    print(f"on end callback ends at {format_t(time.time())}")

runnable = RunnableLambda(test_runnable).with_alisteners(
    on_start=fn_start,
    on_end=fn_end
)
async def concurrent_runs():
    await asyncio.gather(runnable.ainvoke(2), runnable.ainvoke(3))

asyncio.run(concurrent_runs())
Result:
on start callback starts at 2025-03-01T07:05:22.875378+00:00
on start callback starts at 2025-03-01T07:05:22.875495+00:00
on start callback ends at 2025-03-01T07:05:25.878862+00:00
on start callback ends at 2025-03-01T07:05:25.878947+00:00
Runnable[2s]: starts at 2025-03-01T07:05:25.879392+00:00
Runnable[3s]: starts at 2025-03-01T07:05:25.879804+00:00
Runnable[2s]: ends at 2025-03-01T07:05:27.881998+00:00
on end callback starts at 2025-03-01T07:05:27.882360+00:00
Runnable[3s]: ends at 2025-03-01T07:05:28.881737+00:00
on end callback starts at 2025-03-01T07:05:28.882428+00:00
on end callback ends at 2025-03-01T07:05:29.883893+00:00
on end callback ends at 2025-03-01T07:05:30.884831+00:00

```

### `` with\_types [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.with_types "Permanent link")

```md-code__content
with_types(
    *,
    input_type: Optional[type[Input]] = None,
    output_type: Optional[type[Output]] = None
) -> Runnable[Input, Output]

```

Bind input and output types to a Runnable, returning a new Runnable.

Parameters:

- **`input_type`**
( `Optional[type[Input]]`, default:
`None`
)
–



The input type to bind to the Runnable. Defaults to None.

- **`output_type`**
( `Optional[type[Output]]`, default:
`None`
)
–



The output type to bind to the Runnable. Defaults to None.


Returns:

- `Runnable[Input, Output]`
–



A new Runnable with the types bound.


### `` with\_retry [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.with_retry "Permanent link")

```md-code__content
with_retry(
    *,
    retry_if_exception_type: tuple[\
        type[BaseException], ...\
    ] = (Exception,),
    wait_exponential_jitter: bool = True,
    exponential_jitter_params: Optional[\
        ExponentialJitterParams\
    ] = None,
    stop_after_attempt: int = 3
) -> Runnable[Input, Output]

```

Create a new Runnable that retries the original Runnable on exceptions.

Parameters:

- **`retry_if_exception_type`**
( `tuple[type[BaseException], ...]`, default:
`(Exception,)`
)
–



A tuple of exception types to retry on.
Defaults to (Exception,).

- **`wait_exponential_jitter`**
( `bool`, default:
`True`
)
–



Whether to add jitter to the wait
time between retries. Defaults to True.

- **`stop_after_attempt`**
( `int`, default:
`3`
)
–



The maximum number of attempts to make before
giving up. Defaults to 3.

- **`exponential_jitter_params`**
( `Optional[ExponentialJitterParams]`, default:
`None`
)
–



Parameters for
`tenacity.wait_exponential_jitter`. Namely: `initial`, `max`,
`exp_base`, and `jitter` (all float values).


Returns:

- `Runnable[Input, Output]`
–



A new Runnable that retries the original Runnable on exceptions.


Example:

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda

count = 0

def _lambda(x: int) -> None:
    global count
    count = count + 1
    if x == 1:
        raise ValueError("x is 1")
    else:
         pass

runnable = RunnableLambda(_lambda)
try:
    runnable.with_retry(
        stop_after_attempt=2,
        retry_if_exception_type=(ValueError,),
    ).invoke(1)
except ValueError:
    pass

assert (count == 2)

```

### `` map [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.map "Permanent link")

```md-code__content
map() -> Runnable[list[Input], list[Output]]

```

Return a new Runnable that maps a list of inputs to a list of outputs.

Calls invoke() with each input.

Returns:

- `Runnable[list[Input], list[Output]]`
–



A new Runnable that maps a list of inputs to a list of outputs.


Example:

```
.. code-block:: python

        from langchain_core.runnables import RunnableLambda

        def _lambda(x: int) -> int:
            return x + 1

        runnable = RunnableLambda(_lambda)
        print(runnable.map().invoke([1, 2, 3])) # [2, 3, 4]

```

### `` with\_fallbacks [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.with_fallbacks "Permanent link")

```md-code__content
with_fallbacks(
    fallbacks: Sequence[Runnable[Input, Output]],
    *,
    exceptions_to_handle: tuple[\
        type[BaseException], ...\
    ] = (Exception,),
    exception_key: Optional[str] = None
) -> RunnableWithFallbacks[Input, Output]

```

Add fallbacks to a Runnable, returning a new Runnable.

The new Runnable will try the original Runnable, and then each fallback
in order, upon failures.

Parameters:

- **`fallbacks`**
( `Sequence[Runnable[Input, Output]]`)
–



A sequence of runnables to try if the original Runnable fails.

- **`exceptions_to_handle`**
( `tuple[type[BaseException], ...]`, default:
`(Exception,)`
)
–



A tuple of exception types to handle.
Defaults to (Exception,).

- **`exception_key`**
( `Optional[str]`, default:
`None`
)
–



If string is specified then handled exceptions will be passed
to fallbacks as part of the input under the specified key. If None,
exceptions will not be passed to fallbacks. If used, the base Runnable
and its fallbacks must accept a dictionary as input. Defaults to None.


Returns:

- `RunnableWithFallbacks[Input, Output]`
–



A new Runnable that will try the original Runnable, and then each

- `RunnableWithFallbacks[Input, Output]`
–



fallback in order, upon failures.


Example:

```
.. code-block:: python

    from typing import Iterator

    from langchain_core.runnables import RunnableGenerator

    def _generate_immediate_error(input: Iterator) -> Iterator[str]:
        raise ValueError()
        yield ""

    def _generate(input: Iterator) -> Iterator[str]:
        yield from "foo bar"

    runnable = RunnableGenerator(_generate_immediate_error).with_fallbacks(
        [RunnableGenerator(_generate)]
        )
    print(''.join(runnable.stream({}))) #foo bar

```

Parameters:

- **`fallbacks`**
( `Sequence[Runnable[Input, Output]]`)
–



A sequence of runnables to try if the original Runnable fails.

- **`exceptions_to_handle`**
( `tuple[type[BaseException], ...]`, default:
`(Exception,)`
)
–



A tuple of exception types to handle.

- **`exception_key`**
( `Optional[str]`, default:
`None`
)
–



If string is specified then handled exceptions will be passed
to fallbacks as part of the input under the specified key. If None,
exceptions will not be passed to fallbacks. If used, the base Runnable
and its fallbacks must accept a dictionary as input.


Returns:

- `RunnableWithFallbacks[Input, Output]`
–



A new Runnable that will try the original Runnable, and then each

- `RunnableWithFallbacks[Input, Output]`
–



fallback in order, upon failures.


### `` as\_tool [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.tool_validator.ValidationNode.as_tool "Permanent link")

```md-code__content
as_tool(
    args_schema: Optional[type[BaseModel]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    arg_types: Optional[dict[str, type]] = None
) -> BaseTool

```

Create a BaseTool from a Runnable.

`as_tool` will instantiate a BaseTool with a name, description, and
`args_schema` from a Runnable. Where possible, schemas are inferred
from `runnable.get_input_schema`. Alternatively (e.g., if the
Runnable takes a dict as input and the specific dict keys are not typed),
the schema can be specified directly with `args_schema`. You can also
pass `arg_types` to just specify the required arguments and their types.

Parameters:

- **`args_schema`**
( `Optional[type[BaseModel]]`, default:
`None`
)
–



The schema for the tool. Defaults to None.

- **`name`**
( `Optional[str]`, default:
`None`
)
–



The name of the tool. Defaults to None.

- **`description`**
( `Optional[str]`, default:
`None`
)
–



The description of the tool. Defaults to None.

- **`arg_types`**
( `Optional[dict[str, type]]`, default:
`None`
)
–



A dictionary of argument names to types. Defaults to None.


Returns:

- `BaseTool`
–



A BaseTool instance.


Typed dict input:

.. code-block:: python

```
from typing_extensions import TypedDict
from langchain_core.runnables import RunnableLambda

class Args(TypedDict):
    a: int
    b: list[int]

def f(x: Args) -> str:
    return str(x["a"] * max(x["b"]))

runnable = RunnableLambda(f)
as_tool = runnable.as_tool()
as_tool.invoke({"a": 3, "b": [1, 2]})

```

`dict` input, specifying schema via `args_schema`:

.. code-block:: python

```
from typing import Any
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableLambda

def f(x: dict[str, Any]) -> str:
    return str(x["a"] * max(x["b"]))

class FSchema(BaseModel):
    """Apply a function to an integer and list of integers."""

    a: int = Field(..., description="Integer")
    b: list[int] = Field(..., description="List of ints")

runnable = RunnableLambda(f)
as_tool = runnable.as_tool(FSchema)
as_tool.invoke({"a": 3, "b": [1, 2]})

```

`dict` input, specifying schema via `arg_types`:

.. code-block:: python

```
from typing import Any
from langchain_core.runnables import RunnableLambda

def f(x: dict[str, Any]) -> str:
    return str(x["a"] * max(x["b"]))

runnable = RunnableLambda(f)
as_tool = runnable.as_tool(arg_types={"a": int, "b": list[int]})
as_tool.invoke({"a": 3, "b": [1, 2]})

```

String input:

.. code-block:: python

```
from langchain_core.runnables import RunnableLambda

def f(x: str) -> str:
    return x + "a"

def g(x: str) -> str:
    return x + "z"

runnable = RunnableLambda(f) | g
as_tool = runnable.as_tool()
as_tool.invoke("b")

```

.. versionadded:: 0.2.14

Classes:

- **`HumanInterruptConfig`**
–



Configuration that defines what actions are allowed for a human interrupt.

- **`ActionRequest`**
–



Represents a request for human action within the graph execution.

- **`HumanInterrupt`**
–



Represents an interrupt triggered by the graph that requires human intervention.

- **`HumanResponse`**
–



The response provided by a human to an interrupt, which is returned when graph execution resumes.


## `` HumanInterruptConfig [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.interrupt.HumanInterruptConfig "Permanent link")

Bases: `TypedDict`

Configuration that defines what actions are allowed for a human interrupt.

This controls the available interaction options when the graph is paused for human input.

Attributes:

- **`allow_ignore`**
( `bool`)
–



Whether the human can choose to ignore/skip the current step

- **`allow_respond`**
( `bool`)
–



Whether the human can provide a text response/feedback

- **`allow_edit`**
( `bool`)
–



Whether the human can edit the provided content/state

- **`allow_accept`**
( `bool`)
–



Whether the human can accept/approve the current state


## `` ActionRequest [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.interrupt.ActionRequest "Permanent link")

Bases: `TypedDict`

Represents a request for human action within the graph execution.

Contains the action type and any associated arguments needed for the action.

Attributes:

- **`action`**
( `str`)
–



The type or name of action being requested (e.g., "Approve XYZ action")

- **`args`**
( `dict`)
–



Key-value pairs of arguments needed for the action


## `` HumanInterrupt [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.interrupt.HumanInterrupt "Permanent link")

Bases: `TypedDict`

Represents an interrupt triggered by the graph that requires human intervention.

This is passed to the `interrupt` function when execution is paused for human input.

Attributes:

- **`action_request`**
( `ActionRequest`)
–



The specific action being requested from the human

- **`config`**
( `HumanInterruptConfig`)
–



Configuration defining what actions are allowed

- **`description`**
( `Optional[str]`)
–



Optional detailed description of what input is needed


Example

```md-code__content
# Extract a tool call from the state and create an interrupt request
request = HumanInterrupt(
    action_request=ActionRequest(
        action="run_command",  # The action being requested
        args={"command": "ls", "args": ["-l"]}  # Arguments for the action
    ),
    config=HumanInterruptConfig(
        allow_ignore=True,    # Allow skipping this step
        allow_respond=True,   # Allow text feedback
        allow_edit=False,     # Don't allow editing
        allow_accept=True     # Allow direct acceptance
    ),
    description="Please review the command before execution"
)
# Send the interrupt request and get the response
response = interrupt([request])[0]

```

## `` HumanResponse [¶](https://langchain-ai.github.io/langgraph/reference/prebuilt/\#langgraph.prebuilt.interrupt.HumanResponse "Permanent link")

Bases: `TypedDict`

The response provided by a human to an interrupt, which is returned when graph execution resumes.

Attributes:

- **`type`**
( `Literal['accept', 'ignore', 'response', 'edit']`)
–



The type of response:
\- "accept": Approves the current state without changes
\- "ignore": Skips/ignores the current step
\- "response": Provides text feedback or instructions
\- "edit": Modifies the current state/content

- **`arg`**
( `Literal['accept', 'ignore', 'response', 'edit']`)
–



The response payload:
\- None: For ignore/accept actions
\- str: For text responses
\- ActionRequest: For edit actions with updated content


## Comments

giscus

#### [9 reactions](https://github.com/langchain-ai/langgraph/discussions/517)

👍7🚀2

#### [10 comments](https://github.com/langchain-ai/langgraph/discussions/517)

#### ·

#### 9 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@woodswift](https://avatars.githubusercontent.com/u/15988956?u=091d00f8d0f0b3e323f27f6495a877000e15b361&v=4)woodswift](https://github.com/woodswift) [Jul 16, 2024](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-10065190)

Could you please provide a better solution to use the pre-defined prompt by create\_react\_agent() interface? For example, as shown below, the variable `prompt` is a global variable, and it is used internally by the function modify\_messages(). It does not follow the best practice of programming. One potential solution is to move prompt inside the function. However, it might limit the reuse ability of the function. Any advice?

```notranslate
>>> from langchain_core.prompts import ChatPromptTemplate
>>> prompt = ChatPromptTemplate.from_messages([\
...     ("system", "You are a helpful bot named Fred."),\
...     ("placeholder", "{messages}"),\
...     ("user", "Remember, always be polite!"),\
... ])
>>> def modify_messages(messages: list):
...     # You can do more complex modifications here
...     return prompt.invoke({"messages": messages})
>>>
>>> graph = create_react_agent(model, tools, messages_modifier=modify_messages)

```

1

1 reply

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Feb 7](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-12098679)

Contributor

1. It's not something that's mutated so it's not bad to have outside
2. You can namespace it if you want
3. You can use a class instead if you want
4. You can use a function instead if you watn.
5. You can use closures if you want.

[![@SvenDuve](https://avatars.githubusercontent.com/u/10611906?u=b9759e8c8ac068c28a727c1d70800fba279dfce5&v=4)SvenDuve](https://github.com/SvenDuve) [Oct 29, 2024](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-11086440)

Just in case somebody else is confused, the following example won't work like this:

```notranslate
>>> from typing import TypedDict
>>> prompt = ChatPromptTemplate.from_messages(
...     [\
...         ("system", "Today is {today}"),\
...         ("placeholder", "{messages}"),\
...     ]
... )
>>>
>>> class CustomState(TypedDict):
...     today: str
...     messages: Annotated[list[BaseMessage], add_messages]
...     is_last_step: str
>>>
>>> graph = create_react_agent(model, tools, state_schema=CustomState, state_modifier=prompt)
>>> inputs = {"messages": [("user", "What's today's date? And what's the weather in SF?")], "today": "July 16, 2004"}
>>> for s in graph.stream(inputs, stream_mode="values"):
...     message = s["messages"][-1]
...     if isinstance(message, tuple):
...         print(message)
...     else:
...         message.pretty_print()

```

you would have to pass the `is_last_step=False`:

```notranslate
inputs = {"messages": [("user", "What's today's date? And what's the weather in SF?")], "today": "July 16, 2004", "is_last_step":False}

```

1

1 reply

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Mar 5](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-12402355)

Collaborator

you shouldn't need to specify `is_last_step` at all -- you need to subclass your graph state to use custom state schema:

```
from langgraph.prebuilt.chat_agent_executor import AgentState

class CustomState(AgentState):
    today: str
```

[![@sepety](https://avatars.githubusercontent.com/u/120281248?v=4)sepety](https://github.com/sepety) [Nov 14, 2024](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-11250281)

good day!! please help me solve such a simple problem (but I'm confused in the code and don't see any acceptable examples or instructions) - I want to make an agent with the rag\_tool tool that will take the kottext from my pinecone index. what methods should I use, maybe there are examples of such a simple agent? I would be extremely grateful!!

1

1 reply

[![@Heiden133](https://avatars.githubusercontent.com/u/102782285?v=4)](https://github.com/Heiden133)

[Heiden133](https://github.com/Heiden133) [Dec 3, 2024](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-11447132)

You can use Pinecone vector store as a retriever and append it to tools.

[https://python.langchain.com/api\_reference/pinecone/vectorstores/langchain\_pinecone.vectorstores.PineconeVectorStore.html#langchain\_pinecone.vectorstores.PineconeVectorStore](https://python.langchain.com/api_reference/pinecone/vectorstores/langchain_pinecone.vectorstores.PineconeVectorStore.html#langchain_pinecone.vectorstores.PineconeVectorStore)

[![@jimmyn88](https://avatars.githubusercontent.com/u/177209061?v=4)jimmyn88](https://github.com/jimmyn88) [Dec 19, 2024](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-11616386)

Hi,

Is it possibile to get a structured output from a ReAct Agent?

At the moment this is my output:

```
{
  "action": "search",
  "action_input": "what is the temperature in SF"
}'''
```

1

👍2

3 replies

[![@jimmyn88](https://avatars.githubusercontent.com/u/177209061?v=4)](https://github.com/jimmyn88)

[jimmyn88](https://github.com/jimmyn88) [Dec 19, 2024](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-11616401)

At the moment this is my output:

'''JSON

{

"action": "search",

"action\_input": "what is the temperature in SF"

}'''

[![@Hamza5](https://avatars.githubusercontent.com/u/7011111?v=4)](https://github.com/Hamza5)

[Hamza5](https://github.com/Hamza5) [Feb 11](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-12143937)

There is already a tutorial on this:

[How to return structured output from a ReAct agent](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-structured-output/)

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Mar 5](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-12402364)

Collaborator

and you can also pass `response_format` to `create_react_agent`

[![@amandafanny](https://avatars.githubusercontent.com/u/54808661?u=a68800acb68332b76841539bc70ca59893695e66&v=4)amandafanny](https://github.com/amandafanny) [Dec 30, 2024](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-11695671)

the code in ValidationNode can't run well.

```notranslate
File ~/miniconda3/lib/python3.12/site-packages/langgraph/pregel/__init__.py:1929, in Pregel.invoke(self, input, config, stream_mode, output_keys, interrupt_before, interrupt_after, debug, **kwargs)
   1927 else:
   1928     chunks = []
-> 1929 for chunk in self.stream(
   1930     input,
   1931     config,
   1932     stream_mode=stream_mode,
   1933     output_keys=output_keys,
   1934     interrupt_before=interrupt_before,
   1935     interrupt_after=interrupt_after,
   1936     debug=debug,
   1937     **kwargs,
   1938 ):
   1939     if stream_mode == "values":
   1940         latest = chunk
...
--> 643     raise InvalidUpdateError(msg)

InvalidUpdateError: Expected dict, got ('user', 'Select a number, any number')

```

1

😕1

1 reply

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Mar 5](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-12402334)

Collaborator

how are you invoking it?

[![@agdev](https://avatars.githubusercontent.com/u/3872949?v=4)agdev](https://github.com/agdev) [Jan 3](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-11725466)

When using Groq

The code below does not work in ends up in loop.

==============Code===================

> > > from langchain\_core.prompts import ChatPromptTemplate
> > >
> > > prompt = ChatPromptTemplate.from\_messages(\[\
> > >\
> > > ... ("system", "You are a helpful bot named Fred."),\
> > >\
> > > ... ("placeholder", "{messages}"),\
> > >\
> > > ... ("user", "Remember, always be polite!"),\
> > >\
> > > ... \])
> > >
> > > def format\_for\_model(state: AgentState):
> > >
> > > ... # You can do more complex modifications here
> > >
> > > ... return prompt.invoke({"messages": state\["messages"\]})
> > >
> > > graph = create\_react\_agent(model, tools, state\_modifier=format\_for\_model)
> > >
> > > inputs = {"messages": \[("user", "What's your name? And what's the weather in SF?")\]}
> > >
> > > for s in graph.stream(inputs, stream\_mode="values"):
> > >
> > > ... message = s\["messages"\]\[-1\]
> > >
> > > ... if isinstance(message, tuple):
> > >
> > > ... print(message)
> > >
> > > ... else:
> > >
> > > ... message.pretty\_print()
> > >
> > > ==============End of code ==============

1

👀1

0 replies

[![@ashwanthkumar1007](https://avatars.githubusercontent.com/u/67331617?u=452af930304523dc5da25ee571e33b637cf00384&v=4)ashwanthkumar1007](https://github.com/ashwanthkumar1007) [Feb 13](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-12190211)

Is it possible to connect multiple databases to a create\_react\_agent and make the LLM query from these multiple databases to find the final result?

connection\_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={DRIVER\_NAME}"

engine = create\_engine(connection\_string)

db = SQLDatabase(engine)

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

toolkit.get\_tools()

agent\_executor = create\_react\_agent(

llm, toolkit.get\_tools(), state\_modifier=system\_message

)

1

😕1

0 replies

[![@tiaan720](https://avatars.githubusercontent.com/u/157584945?v=4)tiaan720](https://github.com/tiaan720) [Feb 20](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-12261367)

Good day, we had code that relied on the state\_modifier. Since this feature is now removed. How can we still achieve the same state modification?

1

1 reply

[![@eyurtsev](https://avatars.githubusercontent.com/u/3205522?v=4)](https://github.com/eyurtsev)

[eyurtsev](https://github.com/eyurtsev) [Feb 26](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-12329044)

Collaborator

The feature has not been removed. It's been renamed, although the old parameter name will continue to work. If you're on a new version rename the parameter to `prompt`. Please consult the API reference: [https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat\_agent\_executor.create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

[![@n1tz53](https://avatars.githubusercontent.com/u/6022791?v=4)n1tz53](https://github.com/n1tz53) [Mar 25](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-12615037)

Is it possible to see default prompt of create\_react\_agent, also can we pass graph nodes which are another react agent instead of tools ? PS: I want to create multiagent where i want my supervisor node to be a ReAct agent.

1

0 replies

[![@smuniharish](https://avatars.githubusercontent.com/u/59732397?u=a2ea73ce3c78f1b00653254516f1fa45391c442e&v=4)smuniharish](https://github.com/smuniharish) [10 days ago](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-12825672)

TypeError: create\_react\_agent() got an unexpected keyword argument 'prompt'

addition\_expert = create\_react\_agent(

model,

\[add, make\_handoff\_tool(agent\_name="multiplication\_expert")\],

prompt="You are an addition expert, you can ask the multiplication expert for help with multiplication.",

)

multiplication\_expert = create\_react\_agent(

model,

\[multiply, make\_handoff\_tool(agent\_name="addition\_expert")\],

prompt="You are a multiplication expert, you can ask an addition expert for help with addition.",

)

builder = StateGraph(MessagesState)

builder.add\_node("addition\_expert", addition\_expert)

builder.add\_node("multiplication\_expert", multiplication\_expert)

builder.add\_edge(START, "addition\_expert")

graph = builder.compile()

I am getting the error

TypeError: create\_react\_agent() got an unexpected keyword argument 'prompt'

How to resolve this issue?

i am using the langgraph version 0.2.60 and langchain 0.3.7

1

1 reply

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [10 days ago](https://github.com/langchain-ai/langgraph/discussions/517#discussioncomment-12833252)

Collaborator

update to the latest version of `langgraph`

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Freference%2Fprebuilt%2F)