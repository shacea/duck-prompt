[Skip to content](https://langchain-ai.github.io/langgraph/troubleshooting/errors/GRAPH_RECURSION_LIMIT/#graph_recursion_limit)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/troubleshooting/errors/GRAPH_RECURSION_LIMIT.md "Edit this page")

# GRAPH\_RECURSION\_LIMIT [¶](https://langchain-ai.github.io/langgraph/troubleshooting/errors/GRAPH_RECURSION_LIMIT/\#graph_recursion_limit "Permanent link")

Your LangGraph [`StateGraph`](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) reached the maximum number of steps before hitting a stop condition.
This is often due to an infinite loop caused by code like the example below:

```md-code__content
class State(TypedDict):
    some_key: str

builder = StateGraph(State)
builder.add_node("a", ...)
builder.add_node("b", ...)
builder.add_edge("a", "b")
builder.add_edge("b", "a")
...

graph = builder.compile()

```

However, complex graphs may hit the default limit naturally.

## Troubleshooting [¶](https://langchain-ai.github.io/langgraph/troubleshooting/errors/GRAPH_RECURSION_LIMIT/\#troubleshooting "Permanent link")

- If you are not expecting your graph to go through many iterations, you likely have a cycle. Check your logic for infinite loops.
- If you have a complex graph, you can pass in a higher `recursion_limit` value into your `config` object when invoking your graph like this:

```md-code__content
graph.invoke({...}, {"recursion_limit": 100})

```

## Comments

giscus

#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/3122)

#### [1 comment](https://github.com/langchain-ai/langgraph/discussions/3122)

#### ·

#### 1 reply

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@afurgal](https://avatars.githubusercontent.com/u/6023214?u=8666e3eef40864c9e2e93b126a32d496178e75db&v=4)afurgal](https://github.com/afurgal) [Jan 21](https://github.com/langchain-ai/langgraph/discussions/3122#discussioncomment-11904844)

What is recommended if we have a long running mostly autonomous agent - say it's running for a week and doing multiple tasks a day, each running many nodes and/or node loops? Just pick an arbitrarily large number like 999999999, or something else?

2

👍1👀3

1 reply

[![@dlaliberte](https://avatars.githubusercontent.com/u/570125?v=4)](https://github.com/dlaliberte)

[dlaliberte](https://github.com/dlaliberte) [Jan 21](https://github.com/langchain-ai/langgraph/discussions/3122#discussioncomment-11905112)

I have a similar question. In my case, the agent is a chat system, which may run an indefinitely long time. Typically, a human will be involved, thus naturally limiting the number of interactions to a finite high number. But an agent might be interacting with other agents, each one continuing their independent conversations with other agents indefinitely. I want to be able to turn off this recursion limit, and take responsibility for detecting non-productive infinite loops myself.

❤️1

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftroubleshooting%2Ferrors%2FGRAPH_RECURSION_LIMIT%2F)