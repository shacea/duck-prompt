[Skip to content](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/#human-in-the-loop)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/v0-human-in-the-loop.md "Edit this page")

# Human-in-the-loop [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#human-in-the-loop "Permanent link")

Use the `interrupt` function instead.

As of LangGraph 0.2.57, the recommended way to set breakpoints is using the [`interrupt` function](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.interrupt "<code class=\"doc-symbol doc-symbol-heading doc-symbol-function\"></code>            <span class=\"doc doc-object-name doc-function-name\">interrupt</span>") as it simplifies **human-in-the-loop** patterns.

Please see the revised [human-in-the-loop guide](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/) for the latest version that uses the `interrupt` function.

Human-in-the-loop (or "on-the-loop") enhances agent capabilities through several common user interaction patterns.

Common interaction patterns include:

(1) `Approval` \- We can interrupt our agent, surface the current state to a user, and allow the user to accept an action.

(2) `Editing` \- We can interrupt our agent, surface the current state to a user, and allow the user to edit the agent state.

(3) `Input` \- We can explicitly create a graph node to collect human input and pass that input directly to the agent state.

Use-cases for these interaction patterns include:

(1) `Reviewing tool calls` \- We can interrupt an agent to review and edit the results of tool calls.

(2) `Time Travel` \- We can manually re-play and / or fork past actions of an agent.

## Persistence [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#persistence "Permanent link")

All of these interaction patterns are enabled by LangGraph's built-in [persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/) layer, which will write a checkpoint of the graph state at each step. Persistence allows the graph to stop so that a human can review and / or edit the current state of the graph and then resume with the human's input.

### Breakpoints [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#breakpoints "Permanent link")

Adding a [breakpoint](https://langchain-ai.github.io/langgraph/concepts/breakpoints/) a specific location in the graph flow is one way to enable human-in-the-loop. In this case, the developer knows _where_ in the workflow human input is needed and simply places a breakpoint prior to or following that particular graph node.

Here, we compile our graph with a checkpointer and a breakpoint at the node we want to interrupt before, `step_for_human_in_the_loop`. We then perform one of the above interaction patterns, which will create a new checkpoint if a human edits the graph state. The new checkpoint is saved to the `thread` and we can resume the graph execution from there by passing in `None` as the input.

```md-code__content
# Compile our graph with a checkpointer and a breakpoint before "step_for_human_in_the_loop"
graph = builder.compile(checkpointer=checkpointer, interrupt_before=["step_for_human_in_the_loop"])

# Run the graph up to the breakpoint
thread_config = {"configurable": {"thread_id": "1"}}
for event in graph.stream(inputs, thread_config, stream_mode="values"):
    print(event)

# Perform some action that requires human in the loop

# Continue the graph execution from the current checkpoint
for event in graph.stream(None, thread_config, stream_mode="values"):
    print(event)

```

### Dynamic Breakpoints [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#dynamic-breakpoints "Permanent link")

Alternatively, the developer can define some _condition_ that must be met for a breakpoint to be triggered. This concept of [dynamic breakpoints](https://langchain-ai.github.io/langgraph/concepts/breakpoints/) is useful when the developer wants to halt the graph under _a particular condition_. This uses a `NodeInterrupt`, which is a special type of exception that can be raised from within a node based upon some condition. As an example, we can define a dynamic breakpoint that triggers when the `input` is longer than 5 characters.

```md-code__content
def my_node(state: State) -> State:
    if len(state['input']) > 5:
        raise NodeInterrupt(f"Received input that is longer than 5 characters: {state['input']}")
    return state

```

Let's assume we run the graph with an input that triggers the dynamic breakpoint and then attempt to resume the graph execution simply by passing in `None` for the input.

```md-code__content
# Attempt to continue the graph execution with no change to state after we hit the dynamic breakpoint
for event in graph.stream(None, thread_config, stream_mode="values"):
    print(event)

```

The graph will _interrupt_ again because this node will be _re-run_ with the same graph state. We need to change the graph state such that the condition that triggers the dynamic breakpoint is no longer met. So, we can simply edit the graph state to an input that meets the condition of our dynamic breakpoint (< 5 characters) and re-run the node.

```md-code__content
# Update the state to pass the dynamic breakpoint
graph.update_state(config=thread_config, values={"input": "foo"})
for event in graph.stream(None, thread_config, stream_mode="values"):
    print(event)

```

Alternatively, what if we want to keep our current input and skip the node ( `my_node`) that performs the check? To do this, we can simply perform the graph update with `as_node="my_node"` and pass in `None` for the values. This will make no update the graph state, but run the update as `my_node`, effectively skipping the node and bypassing the dynamic breakpoint.

```md-code__content
# This update will skip the node `my_node` altogether
graph.update_state(config=thread_config, values=None, as_node="my_node")
for event in graph.stream(None, thread_config, stream_mode="values"):
    print(event)

```

See [our guide](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/dynamic_breakpoints/) for a detailed how-to on doing this!

## Interaction Patterns [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#interaction-patterns "Permanent link")

### Approval [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#approval "Permanent link")

![](https://langchain-ai.github.io/langgraph/concepts/img/human_in_the_loop/approval.png)

Sometimes we want to approve certain steps in our agent's execution.

We can interrupt our agent at a [breakpoint](https://langchain-ai.github.io/langgraph/concepts/breakpoints/) prior to the step that we want to approve.

This is generally recommend for sensitive actions (e.g., using external APIs or writing to a database).

With persistence, we can surface the current agent state as well as the next step to a user for review and approval.

If approved, the graph resumes execution from the last saved checkpoint, which is saved to the `thread`:

```md-code__content
# Compile our graph with a checkpointer and a breakpoint before the step to approve
graph = builder.compile(checkpointer=checkpointer, interrupt_before=["node_2"])

# Run the graph up to the breakpoint
for event in graph.stream(inputs, thread, stream_mode="values"):
    print(event)

# ... Get human approval ...

# If approved, continue the graph execution from the last saved checkpoint
for event in graph.stream(None, thread, stream_mode="values"):
    print(event)

```

See [our guide](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/breakpoints/) for a detailed how-to on doing this!

### Editing [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#editing "Permanent link")

![](https://langchain-ai.github.io/langgraph/concepts/img/human_in_the_loop/edit_graph_state.png)

Sometimes we want to review and edit the agent's state.

As with approval, we can interrupt our agent at a [breakpoint](https://langchain-ai.github.io/langgraph/concepts/breakpoints/) prior to the step we want to check.

We can surface the current state to a user and allow the user to edit the agent state.

This can, for example, be used to correct the agent if it made a mistake (e.g., see the section on tool calling below).

We can edit the graph state by forking the current checkpoint, which is saved to the `thread`.

We can then proceed with the graph from our forked checkpoint as done before.

```md-code__content
# Compile our graph with a checkpointer and a breakpoint before the step to review
graph = builder.compile(checkpointer=checkpointer, interrupt_before=["node_2"])

# Run the graph up to the breakpoint
for event in graph.stream(inputs, thread, stream_mode="values"):
    print(event)

# Review the state, decide to edit it, and create a forked checkpoint with the new state
graph.update_state(thread, {"state": "new state"})

# Continue the graph execution from the forked checkpoint
for event in graph.stream(None, thread, stream_mode="values"):
    print(event)

```

See [this guide](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/edit-graph-state/) for a detailed how-to on doing this!

### Input [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#input "Permanent link")

![](https://langchain-ai.github.io/langgraph/concepts/img/human_in_the_loop/wait_for_input.png)

Sometimes we want to explicitly get human input at a particular step in the graph.

We can create a graph node designated for this (e.g., `human_input` in our example diagram).

As with approval and editing, we can interrupt our agent at a [breakpoint](https://langchain-ai.github.io/langgraph/concepts/breakpoints/) prior to this node.

We can then perform a state update that includes the human input, just as we did with editing state.

But, we add one thing:

We can use `as_node=human_input` with the state update to specify that the state update _should be treated as a node_.

The is subtle, but important:

With editing, the user makes a decision about whether or not to edit the graph state.

With input, we explicitly define a node in our graph for collecting human input!

The state update with the human input then runs _as this node_.

```md-code__content
# Compile our graph with a checkpointer and a breakpoint before the step to to collect human input
graph = builder.compile(checkpointer=checkpointer, interrupt_before=["human_input"])

# Run the graph up to the breakpoint
for event in graph.stream(inputs, thread, stream_mode="values"):
    print(event)

# Update the state with the user input as if it was the human_input node
graph.update_state(thread, {"user_input": user_input}, as_node="human_input")

# Continue the graph execution from the checkpoint created by the human_input node
for event in graph.stream(None, thread, stream_mode="values"):
    print(event)

```

See [this guide](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/wait-user-input/) for a detailed how-to on doing this!

## Use-cases [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#use-cases "Permanent link")

### Reviewing Tool Calls [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#reviewing-tool-calls "Permanent link")

Some user interaction patterns combine the above ideas.

For example, many agents use [tool calling](https://python.langchain.com/docs/how_to/tool_calling/) to make decisions.

Tool calling presents a challenge because the agent must get two things right:

(1) The name of the tool to call

(2) The arguments to pass to the tool

Even if the tool call is correct, we may also want to apply discretion:

(3) The tool call may be a sensitive operation that we want to approve

With these points in mind, we can combine the above ideas to create a human-in-the-loop review of a tool call.

```md-code__content
# Compile our graph with a checkpointer and a breakpoint before the step to to review the tool call from the LLM
graph = builder.compile(checkpointer=checkpointer, interrupt_before=["human_review"])

# Run the graph up to the breakpoint
for event in graph.stream(inputs, thread, stream_mode="values"):
    print(event)

# Review the tool call and update it, if needed, as the human_review node
graph.update_state(thread, {"tool_call": "updated tool call"}, as_node="human_review")

# Otherwise, approve the tool call and proceed with the graph execution with no edits

# Continue the graph execution from either:
# (1) the forked checkpoint created by human_review or
# (2) the checkpoint saved when the tool call was originally made (no edits in human_review)
for event in graph.stream(None, thread, stream_mode="values"):
    print(event)

```

See [this guide](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/review-tool-calls/) for a detailed how-to on doing this!

### Time Travel [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#time-travel "Permanent link")

When working with agents, we often want closely examine their decision making process:

(1) Even when they arrive a desired final result, the reasoning that led to that result is often important to examine.

(2) When agents make mistakes, it is often valuable to understand why.

(3) In either of the above cases, it is useful to manually explore alternative decision making paths.

Collectively, we call these debugging concepts `time-travel` and they are composed of `replaying` and `forking`.

#### Replaying [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#replaying "Permanent link")

![](https://langchain-ai.github.io/langgraph/concepts/img/human_in_the_loop/replay.png)

Sometimes we want to simply replay past actions of an agent.

Above, we showed the case of executing an agent from the current state (or checkpoint) of the graph.

We by simply passing in `None` for the input with a `thread`.

```md-code__content
thread = {"configurable": {"thread_id": "1"}}
for event in graph.stream(None, thread, stream_mode="values"):
    print(event)

```

Now, we can modify this to replay past actions from a _specific_ checkpoint by passing in the checkpoint ID.

To get a specific checkpoint ID, we can easily get all of the checkpoints in the thread and filter to the one we want.

```md-code__content
all_checkpoints = []
for state in app.get_state_history(thread):
    all_checkpoints.append(state)

```

Each checkpoint has a unique ID, which we can use to replay from a specific checkpoint.

Assume from reviewing the checkpoints that we want to replay from one, `xxx`.

We just pass in the checkpoint ID when we run the graph.

```md-code__content
config = {'configurable': {'thread_id': '1', 'checkpoint_id': 'xxx'}}
for event in graph.stream(None, config, stream_mode="values"):
    print(event)

```

Importantly, the graph knows which checkpoints have been previously executed.

So, it will re-play any previously executed nodes rather than re-executing them.

See [this additional conceptual guide](https://langchain-ai.github.io/langgraph/concepts/persistence/#replay) for related context on replaying.

See see [this guide](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/) for a detailed how-to on doing time-travel!

#### Forking [¶](https://langchain-ai.github.io/langgraph/concepts/v0-human-in-the-loop/\#forking "Permanent link")

![](https://langchain-ai.github.io/langgraph/concepts/img/human_in_the_loop/forking.png)

Sometimes we want to fork past actions of an agent, and explore different paths through the graph.

`Editing`, as discussed above, is _exactly_ how we do this for the _current_ state of the graph!

But, what if we want to fork _past_ states of the graph?

For example, let's say we want to edit a particular checkpoint, `xxx`.

We pass this `checkpoint_id` when we update the state of the graph.

```md-code__content
config = {"configurable": {"thread_id": "1", "checkpoint_id": "xxx"}}
graph.update_state(config, {"state": "updated state"}, )

```

This creates a new forked checkpoint, `xxx-fork`, which we can then run the graph from.

```md-code__content
config = {'configurable': {'thread_id': '1', 'checkpoint_id': 'xxx-fork'}}
for event in graph.stream(None, config, stream_mode="values"):
    print(event)

```

See [this additional conceptual guide](https://langchain-ai.github.io/langgraph/concepts/persistence/#update-state) for related context on forking.

See [this guide](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/) for a detailed how-to on doing time-travel!

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Fv0-human-in-the-loop%2F)