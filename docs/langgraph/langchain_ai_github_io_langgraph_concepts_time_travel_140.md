[Skip to content](https://langchain-ai.github.io/langgraph/concepts/time-travel/?q=#time-travel)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/time-travel.md "Edit this page")

# Time Travel ⏱️ [¶](https://langchain-ai.github.io/langgraph/concepts/time-travel/?q=\#time-travel "Permanent link")

Prerequisites

This guide assumes that you are familiar with LangGraph's checkpoints and states. If not, please review the [persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/) concept first.

When working with non-deterministic systems that make model-based decisions (e.g., agents powered by LLMs), it can be useful to examine their decision-making process in detail:

1. 🤔 **Understand Reasoning**: Analyze the steps that led to a successful result.
2. 🐞 **Debug Mistakes**: Identify where and why errors occurred.
3. 🔍 **Explore Alternatives**: Test different paths to uncover better solutions.

We call these debugging techniques **Time Travel**, composed of two key actions: [**Replaying**](https://langchain-ai.github.io/langgraph/concepts/time-travel/?q=#replaying) 🔁 and [**Forking**](https://langchain-ai.github.io/langgraph/concepts/time-travel/?q=#forking) 🔀 .

## Replaying [¶](https://langchain-ai.github.io/langgraph/concepts/time-travel/?q=\#replaying "Permanent link")

![](https://langchain-ai.github.io/langgraph/concepts/img/human_in_the_loop/replay.png)

Replaying allows us to revisit and reproduce an agent's past actions, up to and including a specific step (checkpoint).

To replay actions before a specific checkpoint, start by retrieving all checkpoints for the thread:

```md-code__content
all_checkpoints = []
for state in graph.get_state_history(thread):
    all_checkpoints.append(state)

```

Each checkpoint has a unique ID. After identifying the desired checkpoint, for instance, `xyz`, include its ID in the configuration:

```md-code__content
config = {'configurable': {'thread_id': '1', 'checkpoint_id': 'xyz'}}
for event in graph.stream(None, config, stream_mode="values"):
    print(event)

```

The graph replays previously executed steps _before_ the provided `checkpoint_id` and executes the steps _after_ `checkpoint_id` (i.e., a new fork), even if they have been executed previously.

## Forking [¶](https://langchain-ai.github.io/langgraph/concepts/time-travel/?q=\#forking "Permanent link")

![](https://langchain-ai.github.io/langgraph/concepts/img/human_in_the_loop/forking.png)

Forking allows you to revisit an agent's past actions and explore alternative paths within the graph.

To edit a specific checkpoint, such as `xyz`, provide its `checkpoint_id` when updating the graph's state:

```md-code__content
config = {"configurable": {"thread_id": "1", "checkpoint_id": "xyz"}}
graph.update_state(config, {"state": "updated state"})

```

This creates a new forked checkpoint, xyz-fork, from which you can continue running the graph:

```md-code__content
config = {'configurable': {'thread_id': '1', 'checkpoint_id': 'xyz-fork'}}
for event in graph.stream(None, config, stream_mode="values"):
    print(event)

```

## Additional Resources 📚 [¶](https://langchain-ai.github.io/langgraph/concepts/time-travel/?q=\#additional-resources "Permanent link")

- [**Conceptual Guide: Persistence**](https://langchain-ai.github.io/langgraph/concepts/persistence/#replay): Read the persistence guide for more context on replaying.
- [**How to View and Update Past Graph State**](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/): Step-by-step instructions for working with graph state that demonstrate the **replay** and **fork** actions.

## Comments

giscus

#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/4261)

#### [1 comment](https://github.com/langchain-ai/langgraph/discussions/4261)

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@sivaTwks010928](https://avatars.githubusercontent.com/u/178696152?v=4)sivaTwks010928](https://github.com/sivaTwks010928) [10 days ago](https://github.com/langchain-ai/langgraph/discussions/4261#discussioncomment-12823748)

Let’s say I’m using interrupt from langgraph.types inside some nodes of a subgraph. I have two subgraphs, both of which contain nodes that use interrupt, and I’ve combined them into a parent graph (each subgraph is compiled into a node in the parent graph).

Now, suppose I want to "travel back in time" — meaning I want the user to be able to select a checkpoint to return to, and then resume execution from that point, potentially following a different path than the original one.

How can I implement this kind of behavior, especially considering that the subgraphs are already compiled into the parent graph?

1

👍1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Ftime-travel%2F%3Fq%3D)