[Skip to content](https://langchain-ai.github.io/langgraph/concepts/high_level/#why-langgraph)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/high_level.md "Edit this page")

# Why LangGraph? [¶](https://langchain-ai.github.io/langgraph/concepts/high_level/\#why-langgraph "Permanent link")

## LLM applications [¶](https://langchain-ai.github.io/langgraph/concepts/high_level/\#llm-applications "Permanent link")

LLMs make it possible to embed intelligence into a new class of applications. There are many patterns for building applications that use LLMs. Workflows have scaffolding of predefined code paths around LLM calls. LLMs can direct the control flow through these predefined code paths, which some consider to be an "agentic system". In other cases, it's possible to remove this scaffolding, creating autonomous agents that can [plan](https://huyenchip.com/2025/01/07/agents.html), take actions via [tool calls](https://python.langchain.com/docs/concepts/tool_calling/), and directly respond [to the feedback from their own actions](https://research.google/blog/react-synergizing-reasoning-and-acting-in-language-models/) with further actions.

![Agent Workflow](https://langchain-ai.github.io/langgraph/concepts/img/agent_workflow.png)

## What LangGraph provides [¶](https://langchain-ai.github.io/langgraph/concepts/high_level/\#what-langgraph-provides "Permanent link")

LangGraph provides low-level supporting infrastructure that sits underneath _any_ workflow or agent. It does not abstract prompts or architecture, and provides three central benefits:

### Persistence [¶](https://langchain-ai.github.io/langgraph/concepts/high_level/\#persistence "Permanent link")

LangGraph has a [persistence layer](https://langchain-ai.github.io/langgraph/concepts/persistence/), which offers a number of benefits:

- [Memory](https://langchain-ai.github.io/langgraph/concepts/memory/): LangGraph persists arbitrary aspects of your application's state, supporting memory of conversations and other updates within and across user interactions;
- [Human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/): Because state is checkpointed, execution can be interrupted and resumed, allowing for decisions, validation, and corrections via human input.

### Streaming [¶](https://langchain-ai.github.io/langgraph/concepts/high_level/\#streaming "Permanent link")

LangGraph also provides support for [streaming](https://langchain-ai.github.io/langgraph/how-tos/#streaming) workflow / agent state to the user (or developer) over the course of execution. LangGraph supports streaming of both events ( [such as feedback from a tool call](https://langchain-ai.github.io/langgraph/how-tos/streaming/#updates)) and [tokens from LLM calls](https://langchain-ai.github.io/langgraph/how-tos/streaming-tokens/) embedded in an application.

### Debugging and Deployment [¶](https://langchain-ai.github.io/langgraph/concepts/high_level/\#debugging-and-deployment "Permanent link")

LangGraph provides an easy onramp for testing, debugging, and deploying applications via [LangGraph Platform](https://langchain-ai.github.io/langgraph/concepts/langgraph_platform/). This includes [Studio](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/), an IDE that enables visualization, interaction, and debugging of workflows or agents. This also includes numerous [options](https://langchain-ai.github.io/langgraph/tutorials/deployment/) for deployment.

## Comments

giscus

#### [11 reactions](https://github.com/langchain-ai/langgraph/discussions/933)

👍6🎉2❤️2👀1

#### [3 comments](https://github.com/langchain-ai/langgraph/discussions/933)

#### ·

#### 3 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@Rohianon](https://avatars.githubusercontent.com/u/41194018?u=8c81461d1acb685b9fa82a5f755ea3979ac15fec&v=4)Rohianon](https://github.com/Rohianon) [Jul 16, 2024](https://github.com/langchain-ai/langgraph/discussions/933#discussioncomment-10063108)

Hey.. how do i stream messages in real-time using langgraph and fastapi over to a client side built on react?

1

👍4

3 replies

[![@shivmohith](https://avatars.githubusercontent.com/u/25202910?u=d4cdce69b7842ced822def582100f25cbce1b863&v=4)](https://github.com/shivmohith)

[shivmohith](https://github.com/shivmohith) [Aug 23, 2024](https://github.com/langchain-ai/langgraph/discussions/933#discussioncomment-10426787)

Not sure if it works but came across this - [https://github.com/JoshuaC215/agent-service-toolkit/blob/fb513eb09d8ce3be724e86c60e5013a77388f8d1/service/service.py#L132](https://github.com/JoshuaC215/agent-service-toolkit/blob/fb513eb09d8ce3be724e86c60e5013a77388f8d1/service/service.py#L132)

[![@shiv248](https://avatars.githubusercontent.com/u/15200155?u=8dfb018067d48386774a67898ec47d8ab97c7a03&v=4)](https://github.com/shiv248)

[shiv248](https://github.com/shiv248) [Oct 3, 2024](https://github.com/langchain-ai/langgraph/discussions/933#discussioncomment-10827242)

you can use websockets, like this project [here](https://github.com/shiv248/LangGraphPy-x-ReactJS/blob/main/graph.py).

🚀1

[![@johnsonfamily1234](https://avatars.githubusercontent.com/u/65795972?u=f1989fce2c3b039eb2dcef905779dffedc5ed512&v=4)](https://github.com/johnsonfamily1234)

[johnsonfamily1234](https://github.com/johnsonfamily1234) [Nov 2, 2024](https://github.com/langchain-ai/langgraph/discussions/933#discussioncomment-11131533)

Can do this with SSE. On the FastAPI side use starlette EventSourceResponse. On the React side use @microsoft/fetch-event-source.

👍1

[![@WesGBrooks](https://avatars.githubusercontent.com/u/2110932?u=cee9eda6d45b2ffdeb3d970507e2df49fc83c75b&v=4)WesGBrooks](https://github.com/WesGBrooks) [Aug 28, 2024](https://github.com/langchain-ai/langgraph/discussions/933#discussioncomment-10476668)

Something that I think I missed reading through this that would have been VERY helpful from the onset (assuming I'm thinking about this correctly):

\-\- LangGraph processes 1 message per graph run/cycle. The point of the framework is to manage the next steps that happen beyond each user's message.

\-\- LangGraph's state persists between messages, or between graph cycles. This is the reason for the checkpointer/thread system, to manage & update state between graph runs/cycles. Each graph run/cycle can also update the graph mid-run/cycle.

As simple as it sounds, this was an assumption that I completely missed reading the docs again early on and caused a lot of headache getting started.

1

👍1

0 replies

[![@MR-GREEN1337](https://avatars.githubusercontent.com/u/94931434?u=37ce42cfee6e934500a9506ea4eb30d67923248a&v=4)MR-GREEN1337](https://github.com/MR-GREEN1337) [Sep 24, 2024](https://github.com/langchain-ai/langgraph/discussions/933#discussioncomment-10732780)

I want to take compiled graph, pickle it and send to S3, but it doesn't work

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Fhigh_level%2F)