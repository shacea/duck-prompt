[Skip to content](https://langchain-ai.github.io/langgraph/troubleshooting/errors/#error-reference)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/troubleshooting/errors/index.md "Edit this page")

# Error reference [¶](https://langchain-ai.github.io/langgraph/troubleshooting/errors/\#error-reference "Permanent link")

This page contains guides around resolving common errors you may find while building with LangGraph.
Errors referenced below will have an `lc_error_code` property corresponding to one of the below codes when they are thrown in code.

- [GRAPH\_RECURSION\_LIMIT](https://langchain-ai.github.io/langgraph/troubleshooting/errors/GRAPH_RECURSION_LIMIT/)
- [INVALID\_CONCURRENT\_GRAPH\_UPDATE](https://langchain-ai.github.io/langgraph/troubleshooting/errors/INVALID_CONCURRENT_GRAPH_UPDATE/)
- [INVALID\_GRAPH\_NODE\_RETURN\_VALUE](https://langchain-ai.github.io/langgraph/troubleshooting/errors/INVALID_GRAPH_NODE_RETURN_VALUE/)
- [MULTIPLE\_SUBGRAPHS](https://langchain-ai.github.io/langgraph/troubleshooting/errors/MULTIPLE_SUBGRAPHS/)
- [INVALID\_CHAT\_HISTORY](https://langchain-ai.github.io/langgraph/troubleshooting/errors/INVALID_CHAT_HISTORY/)

## LangGraph Platform [¶](https://langchain-ai.github.io/langgraph/troubleshooting/errors/\#langgraph-platform "Permanent link")

These guides provide troubleshooting information for errors that are specific to the LangGraph Platform.

- [INVALID\_LICENSE](https://langchain-ai.github.io/langgraph/troubleshooting/errors/INVALID_LICENSE/)
- [Studio Errors](https://langchain-ai.github.io/langgraph/troubleshooting/studio/)

## Comments

giscus

#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/3302)

👍1

#### [2 comments](https://github.com/langchain-ai/langgraph/discussions/3302)

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@MadhuSIT](https://avatars.githubusercontent.com/u/92384937?v=4)MadhuSIT](https://github.com/MadhuSIT) [Feb 13](https://github.com/langchain-ai/langgraph/discussions/3302#discussioncomment-12191292)

Hai, Could you include the below requirement in your next release.

While raising this error, you are making use of create error message function with error code. Could you please find out a way to propagate this error code along with error message?? So that it would be helpful to identify this particular exception under invalid update error.

Thank you!

1

0 replies

[![@sahil28032005](https://avatars.githubusercontent.com/u/112303894?u=fa4261b0729127d8e76f6887c0a71207dfc6eebe&v=4)sahil28032005](https://github.com/sahil28032005) [Feb 13](https://github.com/langchain-ai/langgraph/discussions/3302#discussioncomment-12192540)

Workflow Failed: TypeError: this.operator is not a function

at BinaryOperatorAggregate.update (D:\\Node js\\version control build service\\api-server-spinner\\node\_modules@langchain\\langgraph\\dist\\channels\\binop.cjs:57:35)

at \_applyWrites (D:\\Node js\\version control build service\\api-server-spinner\\node\_modules@langchain\\langgraph\\dist\\pregel\\algo.cjs:205:46)

at PregelLoop.tick (D:\\Node js\\version control build service\\api-server-spinner\\node\_modules@langchain\\langgraph\\dist\\pregel\\loop.cjs:454:67)

at CompiledStateGraph.\_runLoop (D:\\Node js\\version control build service\\api-server-spinner\\node\_modules@langchain\\langgraph\\dist\\pregel\\index.cjs:1010:31)

at process.processTicksAndRejections (node:internal/process/task\_queues:95:5)

at async createAndRunLoop (D:\\Node js\\version control build service\\api-server-spinner\\node\_modules@langchain\\langgraph\\dist\\pregel\\index.cjs:908:17)

web hook Worker is ready to process jobs.

deployment Worker is ready to process jobs.

Failed queue worker is ready to process jobs.

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftroubleshooting%2Ferrors%2F)