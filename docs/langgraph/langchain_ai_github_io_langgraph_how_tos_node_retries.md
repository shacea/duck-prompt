[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/node-retries/#how-to-add-node-retry-policies)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/node-retries.ipynb "Edit this page")

# How to add node retry policies [¶](https://langchain-ai.github.io/langgraph/how-tos/node-retries/\#how-to-add-node-retry-policies "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [LangGraph Glossary](https://langchain-ai.github.io/langgraph/concepts/low_level/)

There are many use cases where you may wish for your node to have a custom retry policy, for example if you are calling an API, querying a database, or calling an LLM, etc.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/node-retries/\#setup "Permanent link")

First, let's install the required packages and set our API keys

```md-code__content
%%capture --no-stderr
%pip install -U langgraph langchain_anthropic langchain_community

```

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("ANTHROPIC_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


In order to configure the retry policy, you have to pass the `retry` parameter to the [add\_node](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph.add_node). The `retry` parameter takes in a `RetryPolicy` named tuple object. Below we instantiate a `RetryPolicy` object with the default parameters:

```md-code__content
from langgraph.pregel import RetryPolicy

RetryPolicy()

```

```md-code__content
RetryPolicy(initial_interval=0.5, backoff_factor=2.0, max_interval=128.0, max_attempts=3, jitter=True, retry_on=<function default_retry_on at 0x78b964b89940>)

```

By default, the `retry_on` parameter uses the `default_retry_on` function, which retries on any exception except for the following:

- `ValueError`
- `TypeError`
- `ArithmeticError`
- `ImportError`
- `LookupError`
- `NameError`
- `SyntaxError`
- `RuntimeError`
- `ReferenceError`
- `StopIteration`
- `StopAsyncIteration`
- `OSError`

In addition, for exceptions from popular http request libraries such as `requests` and `httpx` it only retries on 5xx status codes.

## Passing a retry policy to a node [¶](https://langchain-ai.github.io/langgraph/how-tos/node-retries/\#passing-a-retry-policy-to-a-node "Permanent link")

Lastly, we can pass `RetryPolicy` objects when we call the [add\_node](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph.add_node) function. In the example below we pass two different retry policies to each of our nodes:

API Reference: [ChatAnthropic](https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html) \| [BaseMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.base.BaseMessage.html) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [SQLDatabase](https://python.langchain.com/api_reference/community/utilities/langchain_community.utilities.sql_database.SQLDatabase.html) \| [AIMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html)

```md-code__content
import operator
import sqlite3
from typing import Annotated, Sequence
from typing_extensions import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage

from langgraph.graph import END, StateGraph, START
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import AIMessage

db = SQLDatabase.from_uri("sqlite:///:memory:")

model = ChatAnthropic(model_name="claude-2.1")

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

def query_database(state):
    query_result = db.run("SELECT * FROM Artist LIMIT 10;")
    return {"messages": [AIMessage(content=query_result)]}

def call_model(state):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

# Define a new graph
builder = StateGraph(AgentState)
builder.add_node(
    "query_database",
    query_database,
    retry=RetryPolicy(retry_on=sqlite3.OperationalError),
)
builder.add_node("model", call_model, retry=RetryPolicy(max_attempts=5))
builder.add_edge(START, "model")
builder.add_edge("model", "query_database")
builder.add_edge("query_database", END)

graph = builder.compile()

```

## Comments

giscus

#### [7 reactions](https://github.com/langchain-ai/langgraph/discussions/1175)

👍1❤️6

#### [7 comments](https://github.com/langchain-ai/langgraph/discussions/1175)

#### ·

#### 5 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@michaelozery](https://avatars.githubusercontent.com/u/41621093?u=eaefca80dd7ae71d50ccbec8f46372f1e5f4220c&v=4)michaelozery](https://github.com/michaelozery) [Jul 31, 2024](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-10199811)

Thank you!

fyi there is a typo in the 3rd line: policty

1

1 reply

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Jul 31, 2024](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-10202438)

Collaborator

thanks for reporting -- fixed!

[![@niklasmartin](https://avatars.githubusercontent.com/u/55481472?u=5b344e30c6ce615854e06fd5863176344415e8ec&v=4)niklasmartin](https://github.com/niklasmartin) [Sep 2, 2024](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-10518271)

Contributor

Can I add the error message to the messages in the state? For example, if I get Pydantic Validation Error, it would be nice to add the message to the state, so the llm knows what to do better.

2

👍1

1 reply

[![@muralov](https://avatars.githubusercontent.com/u/13185122?u=6443cf5e6d6f801813a858213c7ca84597bc30d7&v=4)](https://github.com/muralov)

[muralov](https://github.com/muralov) [Feb 4](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-12050925)

we need this feature too.

[![@djprawns](https://avatars.githubusercontent.com/u/3663330?u=35367c8a7be62f945e489c43d25e5481f1f616f7&v=4)djprawns](https://github.com/djprawns) [Nov 14, 2024](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-11260760)

What if i have a JSONDecodeError? That inherits ValueError, and would be excluded. How could I retry on such an error?

1

3 replies

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Nov 14, 2024](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-11260926)

Collaborator

you can set `retry_on`, see more here [https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.RetryPolicy.retry\_on](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.RetryPolicy.retry_on)

[![@djprawns](https://avatars.githubusercontent.com/u/3663330?u=35367c8a7be62f945e489c43d25e5481f1f616f7&v=4)](https://github.com/djprawns)

[djprawns](https://github.com/djprawns) [Nov 14, 2024](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-11261001)

[@vbarda](https://github.com/vbarda) , but JSONDecodeError is a subclass of ValueError. That would be excluded.

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Nov 15, 2024](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-11273552)

Collaborator

that's only true for the default `retry_on`, but if you override it you can explicitly control what's being retried.

[![@reach-will](https://avatars.githubusercontent.com/u/101368213?v=4)reach-will](https://github.com/reach-will) [Nov 25, 2024](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-11368182)

Is using time travel/forking off graph states with errors with retry policies overkill? I believe that would lead to a lot of retries, increasing load and maybe leading to more issues instead, so I would like to know what would be the recommended approach overall, given I still see rewind/time travel mentioned in the documentation quite a bit (specifically when talking about human-in-the-loop).

1

0 replies

[![@antoinegar](https://avatars.githubusercontent.com/u/188879296?u=61bc3119dbb7fcecf4eaf5cf3348a30b0799edf3&v=4)antoinegar](https://github.com/antoinegar) [Feb 21](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-12274868)

It seems the documentation is wrong.

It indicates that only httpx 5xx errors yield a retry:

"In addition, for exceptions from popular http request libraries such as requests and httpx it only retries on 5xx status codes."

But the implementation of the default\_retry\_on returns `True` by default.

See httpx error hierachy:

- HTTPError


x RequestError

  - TransportError
    - TimeoutException


      · ConnectTimeout


      · ReadTimeout


      · WriteTimeout


      · PoolTimeout
    - NetworkError


      · ConnectError


      · ReadError


      · WriteError


      · CloseError
    - ProtocolError


      · LocalProtocolError


      · RemoteProtocolError
    - ProxyError
    - UnsupportedProtocol
  - DecodingError
  - TooManyRedirects


    x HTTPStatusError
- InvalidURL
- CookieConflict
- StreamError


x StreamConsumed


x StreamClosed


x ResponseNotRead


x RequestNotRead

1

0 replies

[![@QuinRiva](https://avatars.githubusercontent.com/u/6433951?u=782040227f1a3d115d36d35a0ceb19c233e54e8c&v=4)QuinRiva](https://github.com/QuinRiva) [Mar 17](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-12520656)

Is it possible to have a node with multiple retry policies? For example, when the node executes there are could be multiple error states that require different handling:

1. Resources exhausted - retry 10 times with a high back-off
2. Response content was empty or invalid - retry once immediately

Is this achievable using the retry policy, or should I just create an error handling node?

1

0 replies

[![@baahujain](https://avatars.githubusercontent.com/u/32643003?v=4)baahujain](https://github.com/baahujain) [12 days ago](https://github.com/langchain-ai/langgraph/discussions/1175#discussioncomment-12811078)

If all the retry attempts fail, then the graph execution stop immediately. How can I ensure that execution moves to another node for graceful stop of the graph?

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fnode-retries%2F)