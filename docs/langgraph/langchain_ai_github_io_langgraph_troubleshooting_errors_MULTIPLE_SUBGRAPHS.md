[Skip to content](https://langchain-ai.github.io/langgraph/troubleshooting/errors/MULTIPLE_SUBGRAPHS/#multiple_subgraphs)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/troubleshooting/errors/MULTIPLE_SUBGRAPHS.md "Edit this page")

# MULTIPLE\_SUBGRAPHS [¶](https://langchain-ai.github.io/langgraph/troubleshooting/errors/MULTIPLE_SUBGRAPHS/\#multiple_subgraphs "Permanent link")

You are calling subgraphs multiple times within a single LangGraph node with checkpointing enabled for each subgraph.

This is currently not allowed due to internal restrictions on how checkpoint namespacing for subgraphs works.

## Troubleshooting [¶](https://langchain-ai.github.io/langgraph/troubleshooting/errors/MULTIPLE_SUBGRAPHS/\#troubleshooting "Permanent link")

The following may help resolve this error:

- If you don't need to interrupt/resume from a subgraph, pass `checkpointer=False` when compiling it like this: `.compile(checkpointer=False)`
- Don't imperatively call graphs multiple times in the same node, and instead use the [`Send`](https://langchain-ai.github.io/langgraph/concepts/low_level/#send) API.

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftroubleshooting%2Ferrors%2FMULTIPLE_SUBGRAPHS%2F)