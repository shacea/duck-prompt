[Skip to content](https://langchain-ai.github.io/langgraph/reference/errors/#errors)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/reference/errors.md "Edit this page")

# Errors [¶](https://langchain-ai.github.io/langgraph/reference/errors/\#errors "Permanent link")

Classes:

- **`GraphRecursionError`**
–



Raised when the graph has exhausted the maximum number of steps.

- **`InvalidUpdateError`**
–



Raised when attempting to update a channel with an invalid set of updates.

- **`GraphInterrupt`**
–



Raised when a subgraph is interrupted, suppressed by the root graph.

- **`NodeInterrupt`**
–



Raised by a node to interrupt execution.

- **`GraphDelegate`**
–



Raised when a graph is delegated (for distributed mode).

- **`EmptyInputError`**
–



Raised when graph receives an empty input.

- **`TaskNotFound`**
–



Raised when the executor is unable to find a task (for distributed mode).

- **`CheckpointNotLatest`**
–



Raised when the checkpoint is not the latest version (for distributed mode).


## `` GraphRecursionError [¶](https://langchain-ai.github.io/langgraph/reference/errors/\#langgraph.errors.GraphRecursionError "Permanent link")

Bases: `RecursionError`

Raised when the graph has exhausted the maximum number of steps.

This prevents infinite loops. To increase the maximum number of steps,
run your graph with a config specifying a higher `recursion_limit`.

Troubleshooting Guides:

- [GRAPH\_RECURSION\_LIMIT](https://python.langchain.com/docs/troubleshooting/errors/GRAPH_RECURSION_LIMIT)

Examples:

```
graph = builder.compile()
graph.invoke(
    {"messages": [("user", "Hello, world!")]},
    # The config is the second positional argument
    {"recursion_limit": 1000},
)

```

## `` InvalidUpdateError [¶](https://langchain-ai.github.io/langgraph/reference/errors/\#langgraph.errors.InvalidUpdateError "Permanent link")

Bases: `Exception`

Raised when attempting to update a channel with an invalid set of updates.

Troubleshooting Guides:

- [INVALID\_CONCURRENT\_GRAPH\_UPDATE](https://python.langchain.com/docs/troubleshooting/errors/INVALID_CONCURRENT_GRAPH_UPDATE)
- [INVALID\_GRAPH\_NODE\_RETURN\_VALUE](https://python.langchain.com/docs/troubleshooting/errors/INVALID_GRAPH_NODE_RETURN_VALUE)

## `` GraphInterrupt [¶](https://langchain-ai.github.io/langgraph/reference/errors/\#langgraph.errors.GraphInterrupt "Permanent link")

Bases: `GraphBubbleUp`

Raised when a subgraph is interrupted, suppressed by the root graph.
Never raised directly, or surfaced to the user.

## `` NodeInterrupt [¶](https://langchain-ai.github.io/langgraph/reference/errors/\#langgraph.errors.NodeInterrupt "Permanent link")

Bases: `GraphInterrupt`

Raised by a node to interrupt execution.

## `` GraphDelegate [¶](https://langchain-ai.github.io/langgraph/reference/errors/\#langgraph.errors.GraphDelegate "Permanent link")

Bases: `GraphBubbleUp`

Raised when a graph is delegated (for distributed mode).

## `` EmptyInputError [¶](https://langchain-ai.github.io/langgraph/reference/errors/\#langgraph.errors.EmptyInputError "Permanent link")

Bases: `Exception`

Raised when graph receives an empty input.

## `` TaskNotFound [¶](https://langchain-ai.github.io/langgraph/reference/errors/\#langgraph.errors.TaskNotFound "Permanent link")

Bases: `Exception`

Raised when the executor is unable to find a task (for distributed mode).

## `` CheckpointNotLatest [¶](https://langchain-ai.github.io/langgraph/reference/errors/\#langgraph.errors.CheckpointNotLatest "Permanent link")

Bases: `Exception`

Raised when the checkpoint is not the latest version (for distributed mode).

## Comments

giscus

#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/530)

#### [3 comments](https://github.com/langchain-ai/langgraph/discussions/530)

#### ·

#### 1 reply

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@sriharsha0806](https://avatars.githubusercontent.com/u/6563096?u=7bc60bb8aab913245b19199447bc6c6421f6ab30&v=4)sriharsha0806](https://github.com/sriharsha0806) [May 24, 2024](https://github.com/langchain-ai/langgraph/discussions/530#discussioncomment-9545011)

Is there an example tutorial on how to use InvalidUpdateError?

1

1 reply

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [May 24, 2024](https://github.com/langchain-ai/langgraph/discussions/530#discussioncomment-9545022)

Contributor

Oh not yet! What would you want the tutorial to teach?

[![@DimonHo](https://avatars.githubusercontent.com/u/3371641?u=8fd1276fb51d56f65612107160491f1486dee6d0&v=4)DimonHo](https://github.com/DimonHo) [Aug 20, 2024](https://github.com/langchain-ai/langgraph/discussions/530#discussioncomment-10390030)

If the recursion\_limit is set too high, it may result in excessive retry attempts when tool calls fail, leading to unnecessary token consumption. What suggestions do you have to address this issue?

1

0 replies

[![@TejParmar10](https://avatars.githubusercontent.com/u/64017555?v=4)TejParmar10](https://github.com/TejParmar10) [Oct 29, 2024](https://github.com/langchain-ai/langgraph/discussions/530#discussioncomment-11086389)

So I am using a local model with the help of ollama which is llama3.2:latest I am getting this error:

'ollama' has no object attribute 'bind\_tools'

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Freference%2Ferrors%2F)