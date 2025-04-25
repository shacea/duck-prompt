[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/#how-to-use-postgres-checkpointer-for-persistence)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/persistence_postgres.ipynb "Edit this page")

# How to use Postgres checkpointer for persistence [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/\#how-to-use-postgres-checkpointer-for-persistence "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [Postgresql](https://www.postgresql.org/about/)

Not needed for LangGraph API users

If you're using the LangGraph API, you needn't manually implement a checkpointer. The API automatically handles checkpointing for you. This guide is relevant when implementing LangGraph in your own custom server.

When creating LangGraph agents, you can also set them up so that they persist their state. This allows you to do things like interact with an agent multiple times and have it remember previous interactions.

This how-to guide shows how to use `Postgres` as the backend for persisting checkpoint state using the [`langgraph-checkpoint-postgres`](https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-postgres) library.

For demonstration purposes we add persistence to the [pre-built create react agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent).

In general, you can add a checkpointer to any custom graph that you build like this:

```md-code__content
from langgraph.graph import StateGraph

builder = StateGraph(....)
# ... define the graph
checkpointer = # postgres checkpointer (see examples below)
graph = builder.compile(checkpointer=checkpointer)
...

```

Setup

You need to run `.setup()` once on your checkpointer to initialize the database before you can use it.

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/\#setup "Permanent link")

You will need access to a postgres instance. There are many resources online that can help
you set up a postgres instance.

Next, let's install the required packages and set our API keys

```md-code__content
%%capture --no-stderr
%pip install -U psycopg psycopg-pool langgraph langgraph-checkpoint-postgres

```

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


## Define model and tools for the graph [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/\#define-model-and-tools-for-the-graph "Permanent link")

API Reference: [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) \| [PostgresSaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.postgres.PostgresSaver) \| [AsyncPostgresSaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.postgres.aio.AsyncPostgresSaver)

```md-code__content
from typing import Literal

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

@tool
def get_weather(city: Literal["nyc", "sf"]):
    """Use this to get weather information."""
    if city == "nyc":
        return "It might be cloudy in nyc"
    elif city == "sf":
        return "It's always sunny in sf"
    else:
        raise AssertionError("Unknown city")

tools = [get_weather]
model = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

```

## Use sync connection [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/\#use-sync-connection "Permanent link")

This sets up a synchronous connection to the database.

Synchronous connections execute operations in a blocking manner, meaning each operation waits for completion before moving to the next one. The `DB_URI` is the database connection URI, with the protocol used for connecting to a PostgreSQL database, authentication, and host where database is running. The connection\_kwargs dictionary defines additional parameters for the database connection.

```md-code__content
DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"

```

```md-code__content
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

```

### With a connection pool [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/\#with-a-connection-pool "Permanent link")

This manages a pool of reusable database connections:
\- Advantages: Efficient resource utilization, improved performance for frequent connections
\- Best for: Applications with many short-lived database operations

```md-code__content
from psycopg_pool import ConnectionPool

with ConnectionPool(
    # Example configuration
    conninfo=DB_URI,
    max_size=20,
    kwargs=connection_kwargs,
) as pool:
    checkpointer = PostgresSaver(pool)

    # NOTE: you need to call .setup() the first time you're using your checkpointer
    checkpointer.setup()

    graph = create_react_agent(model, tools=tools, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "1"}}
    res = graph.invoke({"messages": [("human", "what's the weather in sf")]}, config)
    checkpoint = checkpointer.get(config)

```

```md-code__content
res

```

```md-code__content
{'messages': [HumanMessage(content="what's the weather in sf", id='735b7deb-b0fe-4ad5-8920-2a3c69bbe9f7'),\
  AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_lJHMDYgfgRdiEAGfFsEhqqKV', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-c56b3e04-08a9-4a59-b3f5-ee52d0ef0656-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_lJHMDYgfgRdiEAGfFsEhqqKV', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71}),\
  ToolMessage(content="It's always sunny in sf", name='get_weather', id='0644bf7b-4d1b-4ebe-afa1-d2169ccce582', tool_call_id='call_lJHMDYgfgRdiEAGfFsEhqqKV'),\
  AIMessage(content='The weather in San Francisco is always sunny!', response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'stop', 'logprobs': None}, id='run-1ed9b8d0-9b50-4b87-b3a2-9860f51e9fd1-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94})]}

```

```md-code__content
checkpoint

```

```md-code__content
{'v': 1,
 'id': '1ef559b7-3b19-6ce8-8003-18d0f60634be',
 'ts': '2024-08-08T15:32:42.108605+00:00',
 'current_tasks': {},
 'pending_sends': [],
 'versions_seen': {'agent': {'tools': '00000000000000000000000000000004.022986cd20ae85c77ea298a383f69ba8',
   'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'},
  'tools': {'branch:agent:should_continue:tools': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af'},
  '__input__': {},
  '__start__': {'__start__': '00000000000000000000000000000001.ab89befb52cc0e91e106ef7f500ea033'}},
 'channel_versions': {'agent': '00000000000000000000000000000005.065d90dd7f7cd091f0233855210bb2af',
  'tools': '00000000000000000000000000000005.',
  'messages': '00000000000000000000000000000005.b9adc75836c78af94af1d6811340dd13',
  '__start__': '00000000000000000000000000000002.',
  'start:agent': '00000000000000000000000000000003.',
  'branch:agent:should_continue:tools': '00000000000000000000000000000004.'},
 'channel_values': {'agent': 'agent',
  'messages': [HumanMessage(content="what's the weather in sf", id='735b7deb-b0fe-4ad5-8920-2a3c69bbe9f7'),\
   AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_lJHMDYgfgRdiEAGfFsEhqqKV', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-c56b3e04-08a9-4a59-b3f5-ee52d0ef0656-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_lJHMDYgfgRdiEAGfFsEhqqKV', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71}),\
   ToolMessage(content="It's always sunny in sf", name='get_weather', id='0644bf7b-4d1b-4ebe-afa1-d2169ccce582', tool_call_id='call_lJHMDYgfgRdiEAGfFsEhqqKV'),\
   AIMessage(content='The weather in San Francisco is always sunny!', response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'stop', 'logprobs': None}, id='run-1ed9b8d0-9b50-4b87-b3a2-9860f51e9fd1-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94})]}}

```

### With a connection [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/\#with-a-connection "Permanent link")

This creates a single, dedicated connection to the database:
\- Advantages: Simple to use, suitable for longer transactions
\- Best for: Applications with fewer, longer-lived database operations

```md-code__content
from psycopg import Connection

with Connection.connect(DB_URI, **connection_kwargs) as conn:
    checkpointer = PostgresSaver(conn)
    # NOTE: you need to call .setup() the first time you're using your checkpointer
    # checkpointer.setup()
    graph = create_react_agent(model, tools=tools, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "2"}}
    res = graph.invoke({"messages": [("human", "what's the weather in sf")]}, config)

    checkpoint_tuple = checkpointer.get_tuple(config)

```

```md-code__content
checkpoint_tuple

```

```md-code__content
CheckpointTuple(config={'configurable': {'thread_id': '2', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-4650-6bfc-8003-1c5488f19318'}}, checkpoint={'v': 1, 'id': '1ef559b7-4650-6bfc-8003-1c5488f19318', 'ts': '2024-08-08T15:32:43.284551+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'agent': {'tools': '00000000000000000000000000000004.022986cd20ae85c77ea298a383f69ba8', 'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'}, 'tools': {'branch:agent:should_continue:tools': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af'}, '__input__': {}, '__start__': {'__start__': '00000000000000000000000000000001.ab89befb52cc0e91e106ef7f500ea033'}}, 'channel_versions': {'agent': '00000000000000000000000000000005.065d90dd7f7cd091f0233855210bb2af', 'tools': '00000000000000000000000000000005.', 'messages': '00000000000000000000000000000005.af9f229d2c4e14f4866eb37f72ec39f6', '__start__': '00000000000000000000000000000002.', 'start:agent': '00000000000000000000000000000003.', 'branch:agent:should_continue:tools': '00000000000000000000000000000004.'}, 'channel_values': {'agent': 'agent', 'messages': [HumanMessage(content="what's the weather in sf", id='7a14f96c-2d88-454f-9520-0e0287a4abbb'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_NcL4dBTYu4kSPGMKdxztdpjN', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-39adbf2c-36ef-40f6-9cad-8e1f8167fc19-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_NcL4dBTYu4kSPGMKdxztdpjN', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71}), ToolMessage(content="It's always sunny in sf", name='get_weather', id='c9f82354-3225-40a8-bf54-81f3e199043b', tool_call_id='call_NcL4dBTYu4kSPGMKdxztdpjN'), AIMessage(content='The weather in San Francisco is always sunny!', response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'stop', 'logprobs': None}, id='run-83888be3-d681-42ca-ad67-e2f5ee8550de-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94})]}}, metadata={'step': 3, 'source': 'loop', 'writes': {'agent': {'messages': [AIMessage(content='The weather in San Francisco is always sunny!', response_metadata={'logprobs': None, 'model_name': 'gpt-4o-mini-2024-07-18', 'token_usage': {'total_tokens': 94, 'prompt_tokens': 84, 'completion_tokens': 10}, 'finish_reason': 'stop', 'system_fingerprint': 'fp_48196bc67a'}, id='run-83888be3-d681-42ca-ad67-e2f5ee8550de-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94})]}}}, parent_config={'configurable': {'thread_id': '2', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-4087-681a-8002-88a5738f76f1'}}, pending_writes=[])

```

### With a connection string [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/\#with-a-connection-string "Permanent link")

This creates a connection based on a connection string:
\- Advantages: Simplicity, encapsulates connection details
\- Best for: Quick setup or when connection details are provided as a string

```md-code__content
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    graph = create_react_agent(model, tools=tools, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "3"}}
    res = graph.invoke({"messages": [("human", "what's the weather in sf")]}, config)

    checkpoint_tuples = list(checkpointer.list(config))

```

```md-code__content
checkpoint_tuples

```

```md-code__content
[CheckpointTuple(config={'configurable': {'thread_id': '3', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-5024-6476-8003-cf0a750e6b37'}}, checkpoint={'v': 1, 'id': '1ef559b7-5024-6476-8003-cf0a750e6b37', 'ts': '2024-08-08T15:32:44.314900+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'agent': {'tools': '00000000000000000000000000000004.022986cd20ae85c77ea298a383f69ba8', 'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'}, 'tools': {'branch:agent:should_continue:tools': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af'}, '__input__': {}, '__start__': {'__start__': '00000000000000000000000000000001.ab89befb52cc0e91e106ef7f500ea033'}}, 'channel_versions': {'agent': '00000000000000000000000000000005.065d90dd7f7cd091f0233855210bb2af', 'tools': '00000000000000000000000000000005.', 'messages': '00000000000000000000000000000005.3f8b8d9923575b911e17157008ab75ac', '__start__': '00000000000000000000000000000002.', 'start:agent': '00000000000000000000000000000003.', 'branch:agent:should_continue:tools': '00000000000000000000000000000004.'}, 'channel_values': {'agent': 'agent', 'messages': [HumanMessage(content="what's the weather in sf", id='5bf79d15-6332-4bf5-89bd-ee192b31ed84'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_9y3q1BiwW7zGh2gk2faInTRk', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_507c9469a1', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-2958adc7-f6a4-415d-ade1-5ee77e0b9276-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_9y3q1BiwW7zGh2gk2faInTRk', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71}), ToolMessage(content="It's always sunny in sf", name='get_weather', id='cac4f90a-dc3e-4bfa-940f-1c630289a583', tool_call_id='call_9y3q1BiwW7zGh2gk2faInTRk'), AIMessage(content='The weather in San Francisco is always sunny!', response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'stop', 'logprobs': None}, id='run-97d3fb7a-3d2e-4090-84f4-dafdfe44553f-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94})]}}, metadata={'step': 3, 'source': 'loop', 'writes': {'agent': {'messages': [AIMessage(content='The weather in San Francisco is always sunny!', response_metadata={'logprobs': None, 'model_name': 'gpt-4o-mini-2024-07-18', 'token_usage': {'total_tokens': 94, 'prompt_tokens': 84, 'completion_tokens': 10}, 'finish_reason': 'stop', 'system_fingerprint': 'fp_48196bc67a'}, id='run-97d3fb7a-3d2e-4090-84f4-dafdfe44553f-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94})]}}}, parent_config={'configurable': {'thread_id': '3', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-4b3d-6430-8002-b5c99d2eb4db'}}, pending_writes=None),\
 CheckpointTuple(config={'configurable': {'thread_id': '3', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-4b3d-6430-8002-b5c99d2eb4db'}}, checkpoint={'v': 1, 'id': '1ef559b7-4b3d-6430-8002-b5c99d2eb4db', 'ts': '2024-08-08T15:32:43.800857+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'agent': {'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'}, 'tools': {'branch:agent:should_continue:tools': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af'}, '__input__': {}, '__start__': {'__start__': '00000000000000000000000000000001.ab89befb52cc0e91e106ef7f500ea033'}}, 'channel_versions': {'agent': '00000000000000000000000000000004.', 'tools': '00000000000000000000000000000004.022986cd20ae85c77ea298a383f69ba8', 'messages': '00000000000000000000000000000004.1195f50946feaedb0bae1fdbfadc806b', '__start__': '00000000000000000000000000000002.', 'start:agent': '00000000000000000000000000000003.', 'branch:agent:should_continue:tools': '00000000000000000000000000000004.'}, 'channel_values': {'tools': 'tools', 'messages': [HumanMessage(content="what's the weather in sf", id='5bf79d15-6332-4bf5-89bd-ee192b31ed84'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_9y3q1BiwW7zGh2gk2faInTRk', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_507c9469a1', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-2958adc7-f6a4-415d-ade1-5ee77e0b9276-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_9y3q1BiwW7zGh2gk2faInTRk', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71}), ToolMessage(content="It's always sunny in sf", name='get_weather', id='cac4f90a-dc3e-4bfa-940f-1c630289a583', tool_call_id='call_9y3q1BiwW7zGh2gk2faInTRk')]}}, metadata={'step': 2, 'source': 'loop', 'writes': {'tools': {'messages': [ToolMessage(content="It's always sunny in sf", name='get_weather', id='cac4f90a-dc3e-4bfa-940f-1c630289a583', tool_call_id='call_9y3q1BiwW7zGh2gk2faInTRk')]}}}, parent_config={'configurable': {'thread_id': '3', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-4b30-6078-8001-eaf8c9bd8844'}}, pending_writes=None),\
 CheckpointTuple(config={'configurable': {'thread_id': '3', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-4b30-6078-8001-eaf8c9bd8844'}}, checkpoint={'v': 1, 'id': '1ef559b7-4b30-6078-8001-eaf8c9bd8844', 'ts': '2024-08-08T15:32:43.795440+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'agent': {'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'}, '__input__': {}, '__start__': {'__start__': '00000000000000000000000000000001.ab89befb52cc0e91e106ef7f500ea033'}}, 'channel_versions': {'agent': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af', 'messages': '00000000000000000000000000000003.bab5fb3a70876f600f5f2fd46945ce5f', '__start__': '00000000000000000000000000000002.', 'start:agent': '00000000000000000000000000000003.', 'branch:agent:should_continue:tools': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af'}, 'channel_values': {'agent': 'agent', 'messages': [HumanMessage(content="what's the weather in sf", id='5bf79d15-6332-4bf5-89bd-ee192b31ed84'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_9y3q1BiwW7zGh2gk2faInTRk', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_507c9469a1', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-2958adc7-f6a4-415d-ade1-5ee77e0b9276-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_9y3q1BiwW7zGh2gk2faInTRk', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71})], 'branch:agent:should_continue:tools': 'agent'}}, metadata={'step': 1, 'source': 'loop', 'writes': {'agent': {'messages': [AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_9y3q1BiwW7zGh2gk2faInTRk', 'type': 'function', 'function': {'name': 'get_weather', 'arguments': '{"city":"sf"}'}}]}, response_metadata={'logprobs': None, 'model_name': 'gpt-4o-mini-2024-07-18', 'token_usage': {'total_tokens': 71, 'prompt_tokens': 57, 'completion_tokens': 14}, 'finish_reason': 'tool_calls', 'system_fingerprint': 'fp_507c9469a1'}, id='run-2958adc7-f6a4-415d-ade1-5ee77e0b9276-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_9y3q1BiwW7zGh2gk2faInTRk', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71})]}}}, parent_config={'configurable': {'thread_id': '3', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-46d7-6116-8000-8976b7c89a2f'}}, pending_writes=None),\
 CheckpointTuple(config={'configurable': {'thread_id': '3', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-46d7-6116-8000-8976b7c89a2f'}}, checkpoint={'v': 1, 'id': '1ef559b7-46d7-6116-8000-8976b7c89a2f', 'ts': '2024-08-08T15:32:43.339573+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'__input__': {}, '__start__': {'__start__': '00000000000000000000000000000001.ab89befb52cc0e91e106ef7f500ea033'}}, 'channel_versions': {'messages': '00000000000000000000000000000002.ba0c90d32863686481f7fe5eab9ecdf0', '__start__': '00000000000000000000000000000002.', 'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'}, 'channel_values': {'messages': [HumanMessage(content="what's the weather in sf", id='5bf79d15-6332-4bf5-89bd-ee192b31ed84')], 'start:agent': '__start__'}}, metadata={'step': 0, 'source': 'loop', 'writes': None}, parent_config={'configurable': {'thread_id': '3', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-46ce-6c64-bfff-ef7fe2663573'}}, pending_writes=None),\
 CheckpointTuple(config={'configurable': {'thread_id': '3', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-46ce-6c64-bfff-ef7fe2663573'}}, checkpoint={'v': 1, 'id': '1ef559b7-46ce-6c64-bfff-ef7fe2663573', 'ts': '2024-08-08T15:32:43.336188+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'__input__': {}}, 'channel_versions': {'__start__': '00000000000000000000000000000001.ab89befb52cc0e91e106ef7f500ea033'}, 'channel_values': {'__start__': {'messages': [['human', "what's the weather in sf"]]}}}, metadata={'step': -1, 'source': 'input', 'writes': {'messages': [['human', "what's the weather in sf"]]}}, parent_config=None, pending_writes=None)]

```

## Use async connection [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/\#use-async-connection "Permanent link")

This sets up an asynchronous connection to the database.

Async connections allow non-blocking database operations. This means other parts of your application can continue running while waiting for database operations to complete. It's particularly useful in high-concurrency scenarios or when dealing with I/O-bound operations.

### With a connection pool [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/\#with-a-connection-pool_1 "Permanent link")

```md-code__content
from psycopg_pool import AsyncConnectionPool

async with AsyncConnectionPool(
    # Example configuration
    conninfo=DB_URI,
    max_size=20,
    kwargs=connection_kwargs,
) as pool:
    checkpointer = AsyncPostgresSaver(pool)

    # NOTE: you need to call .setup() the first time you're using your checkpointer
    await checkpointer.setup()

    graph = create_react_agent(model, tools=tools, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "4"}}
    res = await graph.ainvoke(
        {"messages": [("human", "what's the weather in nyc")]}, config
    )

    checkpoint = await checkpointer.aget(config)

```

```md-code__content
checkpoint

```

```md-code__content
{'v': 1,
 'id': '1ef559b7-5cc9-6460-8003-8655824c0944',
 'ts': '2024-08-08T15:32:45.640793+00:00',
 'current_tasks': {},
 'pending_sends': [],
 'versions_seen': {'agent': {'tools': '00000000000000000000000000000004.022986cd20ae85c77ea298a383f69ba8',
   'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'},
  'tools': {'branch:agent:should_continue:tools': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af'},
  '__input__': {},
  '__start__': {'__start__': '00000000000000000000000000000001.0e148ae3debe753278387e84f786e863'}},
 'channel_versions': {'agent': '00000000000000000000000000000005.065d90dd7f7cd091f0233855210bb2af',
  'tools': '00000000000000000000000000000005.',
  'messages': '00000000000000000000000000000005.d869fc7231619df0db74feed624efe41',
  '__start__': '00000000000000000000000000000002.',
  'start:agent': '00000000000000000000000000000003.',
  'branch:agent:should_continue:tools': '00000000000000000000000000000004.'},
 'channel_values': {'agent': 'agent',
  'messages': [HumanMessage(content="what's the weather in nyc", id='d883b8a0-99de-486d-91a2-bcfa7f25dc05'),\
   AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_H6TAYfyd6AnaCrkQGs6Q2fVp', 'function': {'arguments': '{"city":"nyc"}', 'name': 'get_weather'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 15, 'prompt_tokens': 58, 'total_tokens': 73}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-6f542f84-ad73-444c-8ef7-b5ea75a2e09b-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'nyc'}, 'id': 'call_H6TAYfyd6AnaCrkQGs6Q2fVp', 'type': 'tool_call'}], usage_metadata={'input_tokens': 58, 'output_tokens': 15, 'total_tokens': 73}),\
   ToolMessage(content='It might be cloudy in nyc', name='get_weather', id='c0e52254-77a4-4ea9-a2b7-61dd2d65ec68', tool_call_id='call_H6TAYfyd6AnaCrkQGs6Q2fVp'),\
   AIMessage(content='The weather in NYC might be cloudy.', response_metadata={'token_usage': {'completion_tokens': 9, 'prompt_tokens': 88, 'total_tokens': 97}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'stop', 'logprobs': None}, id='run-977140d4-7582-40c3-b2b6-31b542c430a3-0', usage_metadata={'input_tokens': 88, 'output_tokens': 9, 'total_tokens': 97})]}}

```

### With a connection [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/\#with-a-connection_1 "Permanent link")

```md-code__content
from psycopg import AsyncConnection

async with await AsyncConnection.connect(DB_URI, **connection_kwargs) as conn:
    checkpointer = AsyncPostgresSaver(conn)
    graph = create_react_agent(model, tools=tools, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "5"}}
    res = await graph.ainvoke(
        {"messages": [("human", "what's the weather in nyc")]}, config
    )
    checkpoint_tuple = await checkpointer.aget_tuple(config)

```

```md-code__content
checkpoint_tuple

```

```md-code__content
CheckpointTuple(config={'configurable': {'thread_id': '5', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-65b4-60ca-8003-1ef4b620559a'}}, checkpoint={'v': 1, 'id': '1ef559b7-65b4-60ca-8003-1ef4b620559a', 'ts': '2024-08-08T15:32:46.575814+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'agent': {'tools': '00000000000000000000000000000004.022986cd20ae85c77ea298a383f69ba8', 'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'}, 'tools': {'branch:agent:should_continue:tools': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af'}, '__input__': {}, '__start__': {'__start__': '00000000000000000000000000000001.0e148ae3debe753278387e84f786e863'}}, 'channel_versions': {'agent': '00000000000000000000000000000005.065d90dd7f7cd091f0233855210bb2af', 'tools': '00000000000000000000000000000005.', 'messages': '00000000000000000000000000000005.1557a6006d58f736d5cb2dd5c5f10111', '__start__': '00000000000000000000000000000002.', 'start:agent': '00000000000000000000000000000003.', 'branch:agent:should_continue:tools': '00000000000000000000000000000004.'}, 'channel_values': {'agent': 'agent', 'messages': [HumanMessage(content="what's the weather in nyc", id='935e7732-b288-49bd-9ec2-1f7610cc38cb'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_94KtjtPmsiaj7T8yXvL7Ef31', 'function': {'arguments': '{"city":"nyc"}', 'name': 'get_weather'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 15, 'prompt_tokens': 58, 'total_tokens': 73}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-790c929a-7982-49e7-af67-2cbe4a86373b-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'nyc'}, 'id': 'call_94KtjtPmsiaj7T8yXvL7Ef31', 'type': 'tool_call'}], usage_metadata={'input_tokens': 58, 'output_tokens': 15, 'total_tokens': 73}), ToolMessage(content='It might be cloudy in nyc', name='get_weather', id='b2dc1073-abc4-4492-8982-434a7e32e445', tool_call_id='call_94KtjtPmsiaj7T8yXvL7Ef31'), AIMessage(content='The weather in NYC might be cloudy.', response_metadata={'token_usage': {'completion_tokens': 9, 'prompt_tokens': 88, 'total_tokens': 97}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'stop', 'logprobs': None}, id='run-7e8a7f16-d8e1-457a-89f3-192102396449-0', usage_metadata={'input_tokens': 88, 'output_tokens': 9, 'total_tokens': 97})]}}, metadata={'step': 3, 'source': 'loop', 'writes': {'agent': {'messages': [AIMessage(content='The weather in NYC might be cloudy.', response_metadata={'logprobs': None, 'model_name': 'gpt-4o-mini-2024-07-18', 'token_usage': {'total_tokens': 97, 'prompt_tokens': 88, 'completion_tokens': 9}, 'finish_reason': 'stop', 'system_fingerprint': 'fp_48196bc67a'}, id='run-7e8a7f16-d8e1-457a-89f3-192102396449-0', usage_metadata={'input_tokens': 88, 'output_tokens': 9, 'total_tokens': 97})]}}}, parent_config={'configurable': {'thread_id': '5', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-62ae-6128-8002-c04af82bcd41'}}, pending_writes=[])

```

### With a connection string [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/\#with-a-connection-string_1 "Permanent link")

```md-code__content
async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
    graph = create_react_agent(model, tools=tools, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "6"}}
    res = await graph.ainvoke(
        {"messages": [("human", "what's the weather in nyc")]}, config
    )
    checkpoint_tuples = [c async for c in checkpointer.alist(config)]

```

```md-code__content
checkpoint_tuples

```

```md-code__content
[CheckpointTuple(config={'configurable': {'thread_id': '6', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-723c-67de-8003-63bd4eab35af'}}, checkpoint={'v': 1, 'id': '1ef559b7-723c-67de-8003-63bd4eab35af', 'ts': '2024-08-08T15:32:47.890003+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'agent': {'tools': '00000000000000000000000000000004.022986cd20ae85c77ea298a383f69ba8', 'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'}, 'tools': {'branch:agent:should_continue:tools': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af'}, '__input__': {}, '__start__': {'__start__': '00000000000000000000000000000001.0e148ae3debe753278387e84f786e863'}}, 'channel_versions': {'agent': '00000000000000000000000000000005.065d90dd7f7cd091f0233855210bb2af', 'tools': '00000000000000000000000000000005.', 'messages': '00000000000000000000000000000005.b6fe2a26011590cfe8fd6a39151a9e92', '__start__': '00000000000000000000000000000002.', 'start:agent': '00000000000000000000000000000003.', 'branch:agent:should_continue:tools': '00000000000000000000000000000004.'}, 'channel_values': {'agent': 'agent', 'messages': [HumanMessage(content="what's the weather in nyc", id='977ddb90-9991-44cb-9f73-361c6dd21396'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_QIFCuh4zfP9owpjToycJiZf7', 'function': {'arguments': '{"city":"nyc"}', 'name': 'get_weather'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 15, 'prompt_tokens': 58, 'total_tokens': 73}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-47b10c48-4db3-46d8-b4fa-e021818e01c5-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'nyc'}, 'id': 'call_QIFCuh4zfP9owpjToycJiZf7', 'type': 'tool_call'}], usage_metadata={'input_tokens': 58, 'output_tokens': 15, 'total_tokens': 73}), ToolMessage(content='It might be cloudy in nyc', name='get_weather', id='798c520f-4f9a-4f6d-a389-da721eb4d4ce', tool_call_id='call_QIFCuh4zfP9owpjToycJiZf7'), AIMessage(content='The weather in NYC might be cloudy.', response_metadata={'token_usage': {'completion_tokens': 9, 'prompt_tokens': 88, 'total_tokens': 97}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'stop', 'logprobs': None}, id='run-4a34e05d-8bcf-41ad-adc3-715919fde64c-0', usage_metadata={'input_tokens': 88, 'output_tokens': 9, 'total_tokens': 97})]}}, metadata={'step': 3, 'source': 'loop', 'writes': {'agent': {'messages': [AIMessage(content='The weather in NYC might be cloudy.', response_metadata={'logprobs': None, 'model_name': 'gpt-4o-mini-2024-07-18', 'token_usage': {'total_tokens': 97, 'prompt_tokens': 88, 'completion_tokens': 9}, 'finish_reason': 'stop', 'system_fingerprint': 'fp_48196bc67a'}, id='run-4a34e05d-8bcf-41ad-adc3-715919fde64c-0', usage_metadata={'input_tokens': 88, 'output_tokens': 9, 'total_tokens': 97})]}}}, parent_config={'configurable': {'thread_id': '6', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-6bf5-63c6-8002-ed990dbbc96e'}}, pending_writes=None),\
 CheckpointTuple(config={'configurable': {'thread_id': '6', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-6bf5-63c6-8002-ed990dbbc96e'}}, checkpoint={'v': 1, 'id': '1ef559b7-6bf5-63c6-8002-ed990dbbc96e', 'ts': '2024-08-08T15:32:47.231667+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'agent': {'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'}, 'tools': {'branch:agent:should_continue:tools': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af'}, '__input__': {}, '__start__': {'__start__': '00000000000000000000000000000001.0e148ae3debe753278387e84f786e863'}}, 'channel_versions': {'agent': '00000000000000000000000000000004.', 'tools': '00000000000000000000000000000004.022986cd20ae85c77ea298a383f69ba8', 'messages': '00000000000000000000000000000004.c9074f2a41f05486b5efb86353dc75c0', '__start__': '00000000000000000000000000000002.', 'start:agent': '00000000000000000000000000000003.', 'branch:agent:should_continue:tools': '00000000000000000000000000000004.'}, 'channel_values': {'tools': 'tools', 'messages': [HumanMessage(content="what's the weather in nyc", id='977ddb90-9991-44cb-9f73-361c6dd21396'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_QIFCuh4zfP9owpjToycJiZf7', 'function': {'arguments': '{"city":"nyc"}', 'name': 'get_weather'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 15, 'prompt_tokens': 58, 'total_tokens': 73}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-47b10c48-4db3-46d8-b4fa-e021818e01c5-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'nyc'}, 'id': 'call_QIFCuh4zfP9owpjToycJiZf7', 'type': 'tool_call'}], usage_metadata={'input_tokens': 58, 'output_tokens': 15, 'total_tokens': 73}), ToolMessage(content='It might be cloudy in nyc', name='get_weather', id='798c520f-4f9a-4f6d-a389-da721eb4d4ce', tool_call_id='call_QIFCuh4zfP9owpjToycJiZf7')]}}, metadata={'step': 2, 'source': 'loop', 'writes': {'tools': {'messages': [ToolMessage(content='It might be cloudy in nyc', name='get_weather', id='798c520f-4f9a-4f6d-a389-da721eb4d4ce', tool_call_id='call_QIFCuh4zfP9owpjToycJiZf7')]}}}, parent_config={'configurable': {'thread_id': '6', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-6be0-6926-8001-1a8ce73baf9e'}}, pending_writes=None),\
 CheckpointTuple(config={'configurable': {'thread_id': '6', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-6be0-6926-8001-1a8ce73baf9e'}}, checkpoint={'v': 1, 'id': '1ef559b7-6be0-6926-8001-1a8ce73baf9e', 'ts': '2024-08-08T15:32:47.223198+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'agent': {'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'}, '__input__': {}, '__start__': {'__start__': '00000000000000000000000000000001.0e148ae3debe753278387e84f786e863'}}, 'channel_versions': {'agent': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af', 'messages': '00000000000000000000000000000003.097b5407d709b297591f1ef5d50c8368', '__start__': '00000000000000000000000000000002.', 'start:agent': '00000000000000000000000000000003.', 'branch:agent:should_continue:tools': '00000000000000000000000000000003.065d90dd7f7cd091f0233855210bb2af'}, 'channel_values': {'agent': 'agent', 'messages': [HumanMessage(content="what's the weather in nyc", id='977ddb90-9991-44cb-9f73-361c6dd21396'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_QIFCuh4zfP9owpjToycJiZf7', 'function': {'arguments': '{"city":"nyc"}', 'name': 'get_weather'}, 'type': 'function'}]}, response_metadata={'token_usage': {'completion_tokens': 15, 'prompt_tokens': 58, 'total_tokens': 73}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_48196bc67a', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-47b10c48-4db3-46d8-b4fa-e021818e01c5-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'nyc'}, 'id': 'call_QIFCuh4zfP9owpjToycJiZf7', 'type': 'tool_call'}], usage_metadata={'input_tokens': 58, 'output_tokens': 15, 'total_tokens': 73})], 'branch:agent:should_continue:tools': 'agent'}}, metadata={'step': 1, 'source': 'loop', 'writes': {'agent': {'messages': [AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_QIFCuh4zfP9owpjToycJiZf7', 'type': 'function', 'function': {'name': 'get_weather', 'arguments': '{"city":"nyc"}'}}]}, response_metadata={'logprobs': None, 'model_name': 'gpt-4o-mini-2024-07-18', 'token_usage': {'total_tokens': 73, 'prompt_tokens': 58, 'completion_tokens': 15}, 'finish_reason': 'tool_calls', 'system_fingerprint': 'fp_48196bc67a'}, id='run-47b10c48-4db3-46d8-b4fa-e021818e01c5-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'nyc'}, 'id': 'call_QIFCuh4zfP9owpjToycJiZf7', 'type': 'tool_call'}], usage_metadata={'input_tokens': 58, 'output_tokens': 15, 'total_tokens': 73})]}}}, parent_config={'configurable': {'thread_id': '6', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-663d-60b4-8000-10a8922bffbf'}}, pending_writes=None),\
 CheckpointTuple(config={'configurable': {'thread_id': '6', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-663d-60b4-8000-10a8922bffbf'}}, checkpoint={'v': 1, 'id': '1ef559b7-663d-60b4-8000-10a8922bffbf', 'ts': '2024-08-08T15:32:46.631935+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'__input__': {}, '__start__': {'__start__': '00000000000000000000000000000001.0e148ae3debe753278387e84f786e863'}}, 'channel_versions': {'messages': '00000000000000000000000000000002.2a79db8da664e437bdb25ea804457ca7', '__start__': '00000000000000000000000000000002.', 'start:agent': '00000000000000000000000000000002.d6f25946c3108fc12f27abbcf9b4cedc'}, 'channel_values': {'messages': [HumanMessage(content="what's the weather in nyc", id='977ddb90-9991-44cb-9f73-361c6dd21396')], 'start:agent': '__start__'}}, metadata={'step': 0, 'source': 'loop', 'writes': None}, parent_config={'configurable': {'thread_id': '6', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-6637-6d4e-bfff-6cecf690c3cb'}}, pending_writes=None),\
 CheckpointTuple(config={'configurable': {'thread_id': '6', 'checkpoint_ns': '', 'checkpoint_id': '1ef559b7-6637-6d4e-bfff-6cecf690c3cb'}}, checkpoint={'v': 1, 'id': '1ef559b7-6637-6d4e-bfff-6cecf690c3cb', 'ts': '2024-08-08T15:32:46.629806+00:00', 'current_tasks': {}, 'pending_sends': [], 'versions_seen': {'__input__': {}}, 'channel_versions': {'__start__': '00000000000000000000000000000001.0e148ae3debe753278387e84f786e863'}, 'channel_values': {'__start__': {'messages': [['human', "what's the weather in nyc"]]}}}, metadata={'step': -1, 'source': 'input', 'writes': {'messages': [['human', "what's the weather in nyc"]]}}, parent_config=None, pending_writes=None)]

```

## Comments

giscus

#### [10 reactions](https://github.com/langchain-ai/langgraph/discussions/894)

👍8👎1❤️1

#### [49 comments](https://github.com/langchain-ai/langgraph/discussions/894)

#### ·

#### 49+ replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@vaibhavp4](https://avatars.githubusercontent.com/u/4822281?v=4)vaibhavp4](https://github.com/vaibhavp4) [Jul 3, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-9944315)

How do I pass config and recursion limit together while streaming the graph? Currently, I'm getting this error - TypeError: Pregel.stream() takes from 2 to 3 positional arguments but 4 were given

1

1 reply

[![@nathan-vo810](https://avatars.githubusercontent.com/u/14048514?u=11a0760beb88894a1b60cf6aa15ef537f9808eac&v=4)](https://github.com/nathan-vo810)

[nathan-vo810](https://github.com/nathan-vo810) [Jul 4, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-9958710)

This can be done by adding the recursion\_limit key in the config:

```notranslate
config = {"configurable": {"thread_id": "2"}, "recursion_limit": 10}
for event in app.stream(
    {"messages": [input_message]},
    config,
    stream_mode="values",
):
    event["messages"][-1].pretty_print()

```

👍3

[![@dangchinh25](https://avatars.githubusercontent.com/u/35798337?u=21de1a54171be4f17e0348aa5b516180615384c5&v=4)dangchinh25](https://github.com/dangchinh25) [Jul 6, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-9972605)

Can you also update this guide but for JS version, and maybe a seperate general guide to explain in detail how to create a custom checkpointer and each component a checkpointer should have? I feel like this is a really important feature to bring LangGraph to production and there should be more guidance for it.

2

2 replies

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Jul 12, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10034494)

Collaborator

[@dangchinh25](https://github.com/dangchinh25) we've added a JS how-to guide here [https://langchain-ai.github.io/langgraphjs/how-tos/persistence-postgres/](https://langchain-ai.github.io/langgraphjs/how-tos/persistence-postgres/)

👍1

[![@dangchinh25](https://avatars.githubusercontent.com/u/35798337?u=21de1a54171be4f17e0348aa5b516180615384c5&v=4)](https://github.com/dangchinh25)

[dangchinh25](https://github.com/dangchinh25) [Sep 14, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10644005)

can we update this, the guide seem to have been deleted

[![@PI-rampi](https://avatars.githubusercontent.com/u/158999759?v=4)PI-rampi](https://github.com/PI-rampi) [Jul 8, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-9986592)

Please add a specific section on accessing and modifying the state variables of nodes from outside the node functions.

1

1 reply

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Jul 8, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-9992093)

Contributor

You mean like this? [https://langchain-ai.github.io/langgraph/how-tos/human\_in\_the\_loop/edit-graph-state/](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/edit-graph-state/)

[![@PI-rampi](https://avatars.githubusercontent.com/u/158999759?v=4)PI-rampi](https://github.com/PI-rampi) [Jul 9, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-9994306)

William

Thanks for the reply, this is not exactly what I am looking for. Consider a simple scenario that an attribute in the state object has to be modified.

I have a state object and want to modify a string parameter and set it to a value , for e.g. plan attribute . A simple document to modify state attributes with examples will be useful.

class AgentState(TypedDict):
task: str
plan: str
draft: str
critique: str
content: List\[str\]
revision\_number: int
max\_revisions: int

workflow = StateGraph(AgentState)

rampi

[…](https://giscus.app/en/widget?origin=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fpersistence_postgres%2F&session=&theme=preferred_color_scheme&reactionsEnabled=1&emitMetadata=0&inputPosition=bottom&repo=langchain-ai%2Flanggraph&repoId=R_kgDOKFU0lQ&category=Discussions&categoryId=DIC_kwDOKFU0lc4CfZgA&strict=0&description=Build+reliable%2C+stateful+AI+systems%2C+without+giving+up+control&backLink=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fpersistence_postgres%2F&term=langgraph%2Fhow-tos%2Fpersistence_postgres%2F#)

\\_\\_\\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
From: William FH \*\*\*@\*\*\*.\*\*\*>
Sent: 09 July 2024 03:47
To: langchain-ai/langgraph \*\*\*@\*\*\*.\*\*\*>
Cc: Ramprasad \*\*\*@\*\*\*.\*\*\*>; Comment \*\*\*@\*\*\*.\*\*\*>
Subject: Re: \[langchain-ai/langgraph\] langgraph/how-tos/persistence\_postgres/ (Discussion [#894](https://github.com/langchain-ai/langgraph/discussions/894))

You mean like this? [https://langchain-ai.github.io/langgraph/how-tos/human\_in\_the\_loop/edit-graph-state/<https://eu-central-1.protection.sophos.com/?d=langchain-ai.github.io&u=aHR0cHM6Ly9sYW5nY2hhaW4tYWkuZ2l0aHViLmlvL2xhbmdncmFwaC9ob3ctdG9zL2h1bWFuX2luX3RoZV9sb29wL2VkaXQtZ3JhcGgtc3RhdGUv&i=NWY1NzY4MDNhOGI2OTAwZWFlOGRmNDI2&t=QkNXVHhueXB5K0FEKzQ2eFNNSEpXelZJTCtEbCs5VGdscllybnBqZThGdz0=&h=afb31f07d9264eedb4c62fc9d0a21266&s=AVNPUEhUT0NFTkNSWVBUSVY6K0T94M0wPyDMzKN9BocAHrXlbSFJ3THbbw-AzQ3TEw](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/edit-graph-state/%3Chttps://eu-central-1.protection.sophos.com/?d=langchain-ai.github.io&u=aHR0cHM6Ly9sYW5nY2hhaW4tYWkuZ2l0aHViLmlvL2xhbmdncmFwaC9ob3ctdG9zL2h1bWFuX2luX3RoZV9sb29wL2VkaXQtZ3JhcGgtc3RhdGUv&i=NWY1NzY4MDNhOGI2OTAwZWFlOGRmNDI2&t=QkNXVHhueXB5K0FEKzQ2eFNNSEpXelZJTCtEbCs5VGdscllybnBqZThGdz0=&h=afb31f07d9264eedb4c62fc9d0a21266&s=AVNPUEhUT0NFTkNSWVBUSVY6K0T94M0wPyDMzKN9BocAHrXlbSFJ3THbbw-AzQ3TEw) >

—
Reply to this email directly, view it on GitHub< [https://eu-central-1.protection.sophos.com/?d=github.com&u=aHR0cHM6Ly9naXRodWIuY29tL2xhbmdjaGFpbi1haS9sYW5nZ3JhcGgvZGlzY3Vzc2lvbnMvODk0I2Rpc2N1c3Npb25jb21tZW50LTk5OTIwOTM=&i=NWY1NzY4MDNhOGI2OTAwZWFlOGRmNDI2&t=V0pKTnpNS3A2clF5NG54MUJYeStraGNLOHoxcVZBRklqU3dQV0xMbGF5RT0=&h=afb31f07d9264eedb4c62fc9d0a21266&s=AVNPUEhUT0NFTkNSWVBUSVY6K0T94M0wPyDMzKN9BocAHrXlbSFJ3THbbw-AzQ3TEw](https://eu-central-1.protection.sophos.com/?d=github.com&u=aHR0cHM6Ly9naXRodWIuY29tL2xhbmdjaGFpbi1haS9sYW5nZ3JhcGgvZGlzY3Vzc2lvbnMvODk0I2Rpc2N1c3Npb25jb21tZW50LTk5OTIwOTM=&i=NWY1NzY4MDNhOGI2OTAwZWFlOGRmNDI2&t=V0pKTnpNS3A2clF5NG54MUJYeStraGNLOHoxcVZBRklqU3dQV0xMbGF5RT0=&h=afb31f07d9264eedb4c62fc9d0a21266&s=AVNPUEhUT0NFTkNSWVBUSVY6K0T94M0wPyDMzKN9BocAHrXlbSFJ3THbbw-AzQ3TEw) >, or unsubscribe< [https://eu-central-1.protection.sophos.com/?d=github.com&u=aHR0cHM6Ly9naXRodWIuY29tL25vdGlmaWNhdGlvbnMvdW5zdWJzY3JpYmUtYXV0aC9CRjVDSlQyVkNRUFJLTFFMWTZDVkdLVFpMTUZZSEFWQ05GU002QUFBQUFCS0U0N1RENlZISTJEU01WUVdJWDNMTVY0M1NSREpPTlJYSzQzVE5GWFc0UTNQTlZXV0szVFVITTRUU09KU0dBNFRH&i=NWY1NzY4MDNhOGI2OTAwZWFlOGRmNDI2&t=SDdWRUxYR1o5RmROWXNnNWhrdktVWGVvZW9rOXY0eDBlbWdsWXdjcVZUST0=&h=afb31f07d9264eedb4c62fc9d0a21266&s=AVNPUEhUT0NFTkNSWVBUSVY6K0T94M0wPyDMzKN9BocAHrXlbSFJ3THbbw-AzQ3TEw](https://eu-central-1.protection.sophos.com/?d=github.com&u=aHR0cHM6Ly9naXRodWIuY29tL25vdGlmaWNhdGlvbnMvdW5zdWJzY3JpYmUtYXV0aC9CRjVDSlQyVkNRUFJLTFFMWTZDVkdLVFpMTUZZSEFWQ05GU002QUFBQUFCS0U0N1RENlZISTJEU01WUVdJWDNMTVY0M1NSREpPTlJYSzQzVE5GWFc0UTNQTlZXV0szVFVITTRUU09KU0dBNFRH&i=NWY1NzY4MDNhOGI2OTAwZWFlOGRmNDI2&t=SDdWRUxYR1o5RmROWXNnNWhrdktVWGVvZW9rOXY0eDBlbWdsWXdjcVZUST0=&h=afb31f07d9264eedb4c62fc9d0a21266&s=AVNPUEhUT0NFTkNSWVBUSVY6K0T94M0wPyDMzKN9BocAHrXlbSFJ3THbbw-AzQ3TEw) >.
You are receiving this because you commented.Message ID: \*\*\*@\*\*\*.\*\*\*>

This E-MAIL message is a property of Premjiinvest and is intended for use only by the individual or entity to which it is addressed. The information contained may be confidential and privileged. If this is a forwarded message, the content of this E-MAIL may not have been sent with the authority of the company. If you have received this message by mistake, kindly notify the sender by return E-MAIL and delete this message. Premjiinvest will not be responsible for any viruses or defects or any forwarded attachments emanating either from within or outside. Premjiinvest reserves the right to monitor and review the content of all messages sent to or from Premjiinvest E-MAIL addresses. Messages sent to or from this e-mail address may be stored on the Premjiinvest E-MAIL system or elsewhere.

1

1 reply

[![@nathan-vo810](https://avatars.githubusercontent.com/u/14048514?u=11a0760beb88894a1b60cf6aa15ef537f9808eac&v=4)](https://github.com/nathan-vo810)

[nathan-vo810](https://github.com/nathan-vo810) [Jul 9, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-9995717)

You can modify the attribute by using a node and return the new value.

```notranslate
def modify_plan(state):
      current_plan = state['plan']
      new_plan = current_plan + " expired"
      return {'plan': new_plan}

workflow.add_node('modify_plan', modify_plan)
workflow.set_entry_point('modify_plan')
workflow.add_edge('modify_plan', END)

app = workflow.compile()

```

[![@merchana](https://avatars.githubusercontent.com/u/174720198?v=4)merchana](https://github.com/merchana) [Jul 11, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10020275)

Hello, How can I limit the memory, avoiding the graph to continuously have more history on its prompt?

E.g., by limiting to the last 10 messages

1

👍1

1 reply

[![@DLOVRIC2](https://avatars.githubusercontent.com/u/66421606?u=20b7137c45b4589868ae3d45cb84cdfc67268074&v=4)](https://github.com/DLOVRIC2)

[DLOVRIC2](https://github.com/DLOVRIC2) [Nov 9, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-11196042)

In my usecase I only need the latest 3 questions and answers from the agents, so I have a method something like this:

```
    def _get_conversation_history(self, checkpoint: Checkpoint | None) -> list[str]:
        """
        Extract and format conversation history from checkpoint.

        Args:
            checkpoint (dict): The checkpoint containing conversation state

        Returns:
            list[str]: Interleaved list of queries and responses, up to MAX_HISTORY_LENGTH
        """
        if not checkpoint:
            return []

        user_queries = checkpoint.get("channel_values", {}).get("query", [])
        agent_responses = checkpoint.get("channel_values", {}).get("response", [])

        # Create interleaved conversation history from recent interactions
        conversation_history = []
        for q, r in zip(user_queries[-self.MAX_HISTORY_LENGTH :], agent_responses[-self.MAX_HISTORY_LENGTH :]):
            conversation_history.extend([q, r])

        logger.info("Current conversation state:")
        logger.info(f"Latest queries: {user_queries[-self.MAX_HISTORY_LENGTH:]}")
        logger.info(f"Latest responses: {agent_responses[-self.MAX_HISTORY_LENGTH:]}")
        logger.info(f"Conversation history: {conversation_history}")

        return conversation_history
```

Note that in my state I have both 'query' and 'response' args that I use to store the ongoing conversation. Note that input arg is the checkpoint which can be retrieved from Postgres, Redis, MongoDB or any other. Hope that helps

👍1

[![@Brainsoft-Raxat](https://avatars.githubusercontent.com/u/53768667?u=6ee840f3f158b947832661f8c336ce392f2b8f01&v=4)Brainsoft-Raxat](https://github.com/Brainsoft-Raxat) [Jul 12, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10028263)

I am currently implementing a customer support bot and have been exploring the use of persistent memory to manage user interactions. My initial approach was to load the memory for a specific user from persistent storage, ensuring that all interactions from different users remain isolated. This seemed straightforward for maintaining user-specific contexts across sessions.

However, I am a bit confused about the specific utility of threads in this context. I understand that threads can provide additional granularity by keeping separate interactions within the same user session, but I am struggling to come up with concrete use cases where this granularity would be beneficial.

One example I am considering is within a single chat interaction. Even with persistent memory loaded through a checkpointer, it seems possible to add more granularity by using threads to manage multiple sub-interactions within a single user session. For instance, in a customer support bot scenario, a user might request multiple tasks, and these could be managed as separate threads within the same interaction.

My question is about the practical management of this granularity. How does the agent determine which thread to use at any given time within an ongoing interaction? Are there specific strategies or examples where combining both checkpointers and threads has proven particularly effective? I would greatly appreciate insights from those with more experience in this area.

2

1 reply

[![@lakshaytalkstomachines](https://avatars.githubusercontent.com/u/38259381?u=c32bd533ee3f00d899ec906c6878f3a5a4fd91d5&v=4)](https://github.com/lakshaytalkstomachines)

[lakshaytalkstomachines](https://github.com/lakshaytalkstomachines) [Jul 17, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10077513)

How are you maintining "This seemed straightforward for maintaining user-specific contexts across sessions." without threads? Have you implemented it yourself?

[![@emarco177](https://avatars.githubusercontent.com/u/44670213?u=c5c658fcb5e3ed1f88c159b5621f93fac020661d&v=4)emarco177](https://github.com/emarco177) [Jul 13, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10037350)

Any plans to add to the documentation an explanation of the "state' structure once its persisted?

e.g:

b'{"v": 1, "ts": "2024-07-13T05:59:18.599275+00:00", "id": "1ef40dd0-add3-62c2-8000-c6d57b7034eb", "channel\_values": {"input": "hello world", "start:step\_1": " **start**"}, "channel\_versions": {" **start**": 2, "input": 2, "start:step\_1": 2}, "versions\_seen": {" **start**": {" **start**": 1}, "step\_1": {}, "human\_feedback": {}, "step\_3": {}}, "pending\_sends": \[\]}'

To understand what each of those values here represent :)

2

👍4

1 reply

[![@lakshaytalkstomachines](https://avatars.githubusercontent.com/u/38259381?u=c32bd533ee3f00d899ec906c6878f3a5a4fd91d5&v=4)](https://github.com/lakshaytalkstomachines)

[lakshaytalkstomachines](https://github.com/lakshaytalkstomachines) [Jul 17, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10077518)

We need more documentation on "channels" data structure in langraph.

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)HoangNguyen689](https://github.com/HoangNguyen689) [Jul 18, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10079707)

Why we need the `writes` table?

2

1 reply

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Jul 25, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10152641)

Collaborator

see below!

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)HoangNguyen689](https://github.com/HoangNguyen689) [Jul 25, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10145598)

It should have docs about the way checkpointer work.

What purposes the `writes table` is used for?

1

5 replies

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)](https://github.com/HoangNguyen689)

[HoangNguyen689](https://github.com/HoangNguyen689) [Jul 25, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10146831)

cc: [@vbarda](https://github.com/vbarda)

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Jul 25, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10152637)

Collaborator

thanks for the feedback -- we'll be updating the documents on this to add more comments / explanations soon!

re: `writes` table / `checkpointer.put_writes` method -- it's needed for storing pending writes: if a node fails mid-execution, we store pending checkpoint writes from other successful nodes at that superstep, so that whenever we resume graph execution from that superstep we don't re-run the nodes that completed successfully previously. hope this helps!

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)](https://github.com/HoangNguyen689)

[HoangNguyen689](https://github.com/HoangNguyen689) [Jul 26, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10154488)

fyi: [https://github.com/langchain-ai/langgraph/discussions/1141](https://github.com/langchain-ai/langgraph/discussions/1141)

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)](https://github.com/HoangNguyen689)

[HoangNguyen689](https://github.com/HoangNguyen689) [Jul 26, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10154524)

[@vbarda](https://github.com/vbarda)

Thanks.

Which resources I have to prepare for the writes? Is it the same as `checkpoint` table?

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Jul 26, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10159688)

Collaborator

thanks for starting the discussion -- we're working on improving the docs / developer experience around checkpointers and will post an update soon.

re: your question -- it really depends on what kind of checkpointer you're implementing, there isn't really a requirement for creating a specific table. the checkpointer just needs to conform to this interface: [https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/checkpoint/base.py#L152](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/checkpoint/base.py#L152) and implement `.put`, `.put_writes`, `.get_tuple`, `.list` or their async versions if you need to run your graph asynchronously

if you use a SQL database, you can just use the same table schemas as the postgres tutorial (although you might have to adjust the field types since the ones in the tutorial are postgres-specific). see more built-in examples here:

[https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/checkpoint/sqlite.py#L64](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/checkpoint/sqlite.py#L64)

[https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/checkpoint/aiosqlite.py#L46](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/checkpoint/aiosqlite.py#L46)

👍2

[![@GaryFail](https://avatars.githubusercontent.com/u/52258531?u=848b4be2ca3c1fc68cab90d42fbe5a211fac6977&v=4)GaryFail](https://github.com/GaryFail) [Jul 30, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10187790)

I get this error from get\_tuple:

CheckpointTuple. **new**() got an unexpected keyword argument 'pending\_writes'

and sure enough it doesn't:

class CheckpointTuple(NamedTuple):

config: RunnableConfig

checkpoint: Checkpoint

metadata: CheckpointMetadata

parent\_config: Optional\[RunnableConfig\] = None

Anybody any ideas?

1

👀1

1 reply

[![@GaryFail](https://avatars.githubusercontent.com/u/52258531?u=848b4be2ca3c1fc68cab90d42fbe5a211fac6977&v=4)](https://github.com/GaryFail)

[GaryFail](https://github.com/GaryFail) [Aug 6, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10254918)

This does now have pending\_writes. I've tried to look back to see if it was updated or if it was a mistake on my behalf but I can't find where this has changed and can't find the file on the main branch so perhaps it's also since being refactored. One less thing to worry about though :-)

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)vbarda](https://github.com/vbarda) [Aug 8, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10277417)

Collaborator

Hi folks! We just released a new Postgres checkpointer library -- you can install it with `pip install langgraph-checkpoint-postgres`. [This how-to guide](https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/) has been updated to use the library directly. This release is part of the larger LangGraph v0.2 release -- see release notes here [https://github.com/langchain-ai/langgraph/releases/tag/0.2.0](https://github.com/langchain-ai/langgraph/releases/tag/0.2.0)

Please let me know if you run into any issues with the library!

1

15 replies

Show 10 previous replies

[![@sataycat](https://avatars.githubusercontent.com/u/29532686?u=ab7cfa5c12defb1dc18b60e137164f2b91cb8640&v=4)](https://github.com/sataycat)

[sataycat](https://github.com/sataycat) [Aug 24, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10438161)

Here's how I use the lifespan now. I find that compiling the graph per invocation is rather quick in practice, compared to waiting for the first messages to stream out

```
@asynccontextmanager
async def lifespan(app: FastAPI):
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
        "row_factory": dict_row,
    }
    async with AsyncConnectionPool(settings.DB_URI, kwargs=connection_kwargs) as pool:
        await pool.wait()  # optional
        yield {"pool": pool}

app = FastAPI(lifespan=lifespan)

# elsewhere

@router.post("/message")
async def message(request: Request):
    async with request.state.pool.connection() as conn:
        checkpointer = AsyncPostgresSaver(conn)
        graph = graph_builder.compile(checkpointer=checkpointer)
        async for event in graph.astream_events(input, config=config, version="v2"):
            # do your thing
            pass
```

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Aug 29, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10487889)

Collaborator

by the way, we added support for passing pool to PostgresSaver directly in `langgraph-checkpoint-postgres==1.0.4`

❤️1

[![@Gontna](https://avatars.githubusercontent.com/u/37012179?v=4)](https://github.com/Gontna)

[Gontna](https://github.com/Gontna) [Nov 3, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-11134968)

if i want to operate the database to complete some operations,such as view all conversation history. what should i do to get the pool that defined in lifespan

[![@danielemaasit](https://avatars.githubusercontent.com/u/53980892?v=4)](https://github.com/danielemaasit)

[danielemaasit](https://github.com/danielemaasit) [26 days ago](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12664144)

edited

> Thanks for pointing that out.
>
> I guess I'm now questioning my implementation. I have a FastAPI in front of this so when somebody calls an endpoint I invoke the graph for the given thread. What I wasn't planning on doing was to compile the graph each time the endpoint was hit, instead compile the graph once and use that throughout the lifetime of the application using a connection pool to pull the connections out of upon each request.
>
> Is there any guidance on whether what I am attempting to do is correct or am I way off the mark?

[@GaryFail](https://github.com/GaryFail) Did you ever get a response to this Question? Did you find a solution? If so, please share. I have tried implementing this for 10 straight hours and failed.

[![@GaryFail](https://avatars.githubusercontent.com/u/52258531?u=848b4be2ca3c1fc68cab90d42fbe5a211fac6977&v=4)](https://github.com/GaryFail)

[GaryFail](https://github.com/GaryFail) [25 days ago](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12665919)

edited

[@danielemaasit](https://github.com/danielemaasit) I'm not sure exactly which point it is you are asking for clarification on. However we don't compile the graph on each request and we use a database connection pool which is initialised in the FastAPI lifespan event.

we have a connection pool set up like this:

```notranslate
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
    "row_factory": dict_row,
}

database_connection_pool = AsyncConnectionPool(
    conninfo=os.environ["STATE_CONNECTION_STRING"],
    max_size=20,
    open=False,
    kwargs=connection_kwargs,
)

```

main.py is something along the lines of this:

```notranslate
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database_connection_pool.open()
    try:
        async with database_connection_pool.connection() as conn:
            await AsyncPostgresSaver(conn).setup()
    except Exception as e:
        logging.error(f"Error setting up database: {type(e).__name__} - {e}")
        raise
    yield
    await database_connection_pool.close()

```

The checkpointer then uses the connection pool:

```notranslate
def get_checkpointer() -> BaseCheckpointSaver:
    """
    Return an implementation of BaseCheckpointSaver to be passed to a graph to store state.
    """
    return AsyncPostgresSaver(database_connection_pool)

```

And that is used to compile the graph and we return the compiled graph whenever we want to use it:

```notranslate

saver = get_checkpointer()

graph = builder.compile(checkpointer=saver)

def get_graph() -> CompiledStateGraph:
    return graph

```

Just ensure you have the updates to the libraries etc.

[![@gbaian10](https://avatars.githubusercontent.com/u/34255899?u=05aba76f1912a56538c8a5141f8135d0e3b1e1bd&v=4)gbaian10](https://github.com/gbaian10) [Aug 16, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10357892)

Contributor

```
from psycopg_pool import AsyncConnectionPool

async with AsyncConnectionPool(
    # Example configuration
    conninfo=DB_URI,
    max_size=20,
    kwargs=connection_kwargs
) as pool, pool.connection() as conn:
    checkpointer = AsyncPostgresSaver(conn)

    # NOTE: you need to call .setup() the first time you're using your checkpointer
    # await checkpointer.setup()

    graph = create_react_agent(model, tools=tools, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "4"}}
    res = await graph.ainvoke(
        {"messages": [("human", "what's the weather in nyc")]}, config
    )

    checkpoint = await checkpointer.aget(config)
```

Regarding this piece of pool code, the pool has 20 connections available, but the code only takes one connection from the pool and assigns it to `AsyncPostgresSaver`.

Does this mean that an AsyncPostgresSaver will always have only one connection?

It seems that the pool's intended effect is not being utilized?

Additionally, I have a similar question to [@GaryFail](https://github.com/GaryFail): how exactly should I compile the graph and the checkpointer in the API?

1

👍2

5 replies

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Aug 19, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10387307)

Collaborator

great question. you can use something like FastAPI lifespan in the code snippet above to initialize the pool. we'll also look into passing the connection pool directly into the `PostgresSaver`!

👍1

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Aug 29, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10487887)

Collaborator

by the way, we added support for passing pool to PostgresSaver directly in `langgraph-checkpoint-postgres==1.0.4`

🚀2

[![@sutharzan-ch](https://avatars.githubusercontent.com/u/138161119?v=4)](https://github.com/sutharzan-ch)

[sutharzan-ch](https://github.com/sutharzan-ch) [Jan 4](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-11731108)

[@vbarda](https://github.com/vbarda) I am trying to figure out how to avoid compiling the graph each time I need to invoke it. Even if I pass the connection pool to PostgresSaver directly, I still have to create a checkpointer using a connection from the pool before compiling the graph. This means I end up compiling the graph for each Postgres DB thread. Is there a way to compile the graph once and reuse it across multiple invocations while still using the connection pool for database operations? Or am I misunderstanding the intended usage here?

[![@viplazylmht](https://avatars.githubusercontent.com/u/20496271?u=d275f7f3ee891fd203f75a07883b9dad2a705742&v=4)](https://github.com/viplazylmht)

[viplazylmht](https://github.com/viplazylmht) [Jan 21](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-11897609)

[@sutharzan-ch](https://github.com/sutharzan-ch) You can compile graph when initialize the app (it can be FastAPI lifespan or your singleton instance). Then you can reuse the complied one to handle requests.

[![@sutharzan-ch](https://avatars.githubusercontent.com/u/138161119?v=4)](https://github.com/sutharzan-ch)

[sutharzan-ch](https://github.com/sutharzan-ch) [Jan 21](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-11902098)

[@viplazylmht](https://github.com/viplazylmht) Thanks for the clarifications!

[![@vigneshmj1997](https://avatars.githubusercontent.com/u/33595829?u=d0ee173f2ceb7074923d3ffbd63ca56493081977&v=4)vigneshmj1997](https://github.com/vigneshmj1997) [Aug 29, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10484230)

Any idea on which implementation works the best for the production environment ..?

- is it best to compile the graph on every request
- or is it better to have a complied version and use that object on every request

2

3 replies

[![@GaryFail](https://avatars.githubusercontent.com/u/52258531?u=848b4be2ca3c1fc68cab90d42fbe5a211fac6977&v=4)](https://github.com/GaryFail)

[GaryFail](https://github.com/GaryFail) [Aug 29, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10491056)

I guess we need to know if the compiled graph object is thread safe.

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Aug 29, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10491365)

Collaborator

yes, compiled graph object is thread safe

[![@robocanic](https://avatars.githubusercontent.com/u/79916872?u=c17df81704f1ce9b0c09e2c2fc7185c490d53de4&v=4)](https://github.com/robocanic)

[robocanic](https://github.com/robocanic) [Sep 2, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10516717)

I think the second is better. There are usually several initialize steps before the graph can be complied. These steps may cost a long time. So in order to reduce the whole inference costs, I believe the single pattern is better.

[![@kvkenyon](https://avatars.githubusercontent.com/u/1572831?u=42c9fcdfe95fda63f1d7a9feca1d572bfab59d12&v=4)kvkenyon](https://github.com/kvkenyon) [Aug 30, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10501578)

Hey when I run my agent outside of LangGraph studio it's accessing the DB fine. I've even used ngrok to expose to TCP port. But from the langgraph studio docker container it won't connect. Any ideas?

1

👍1

0 replies

[![@jhachirag7](https://avatars.githubusercontent.com/u/70481022?v=4)jhachirag7](https://github.com/jhachirag7) [Oct 3, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10830347)

i am getting error on imports

`from langgraph.checkpoint.postgres import PostgresSaver`

error:

ImportError no pq wrapper available.

Attempts made:

- couldn't import psycopg 'c' implementation: No module named 'psycopg\_c'
- couldn't import psycopg 'binary' implementation: No module named 'psycopg\_binary'
- couldn't import psycopg 'python' implementation: expected str, bytes or os.PathLike object, not NoneType

1

2 replies

[![@jhachirag7](https://avatars.githubusercontent.com/u/70481022?v=4)](https://github.com/jhachirag7)

[jhachirag7](https://github.com/jhachirag7) [Oct 3, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-10830549)

got solved after installing pip install "psycopg\[binary,pool\]"

👍2

[![@DLOVRIC2](https://avatars.githubusercontent.com/u/66421606?u=20b7137c45b4589868ae3d45cb84cdfc67268074&v=4)](https://github.com/DLOVRIC2)

[DLOVRIC2](https://github.com/DLOVRIC2) [Oct 23, 2024](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-11033639)

thanks!

19 hidden itemsLoad more…

[![@headyin](https://avatars.githubusercontent.com/u/2319336?v=4)headyin](https://github.com/headyin) [Jan 15](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-11844598)

What’s the best way to do data retention for the Postgres checkpoint save? I want to make sure the data is deleted after 30 days from the Postgres DB.

2

2 replies

[![@wfjt](https://avatars.githubusercontent.com/u/16338335?u=d1d9aa77415aa2a47be9f297a61b49806ba99ea8&v=4)](https://github.com/wfjt)

[wfjt](https://github.com/wfjt) [Jan 16](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-11849026)

`pg_cron` extension maybe?

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)](https://github.com/HoangNguyen689)

[HoangNguyen689](https://github.com/HoangNguyen689) [Jan 16](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-11857358)

you can do that with cron job and check the timestamp field

[![@my23701](https://avatars.githubusercontent.com/u/65496483?v=4)my23701](https://github.com/my23701) [Jan 20](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-11888130)

How can i get the rephrased question on the basis of user\_history from the response, any callbacks or technique to do that?

1

0 replies

[![@itogaston](https://avatars.githubusercontent.com/u/78599574?u=2d9259ce001cf6b30e1b2b10d13d66026b55b8ed&v=4)itogaston](https://github.com/itogaston) [Feb 4](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12051862)

Hi! I'm using the PostgresSaver to persist our conversations. The agent is connected to a frontend that retrieves the list of previous messages from the checkpoint associated with each conversation. Currently, we are storing all the messages in the state.

We're considering using message trimming or deletion to ensure that our conversation fits within the model's window size. However, this approach would modify the state and, in turn, change how the user sees their conversation history.

Questions:

- Are we using the checkpoint state correctly to persist user conversations, or should we implement a separate persistence mechanism (e.g., another table) to store the full conversation history without interfering with state management?
- Is it acceptable to store all messages within the checkpoint state, or could this lead to performance issues or unintended side effects as the conversation grows?
- Are there recommended patterns or best practices for integrating checkpoint management with conversation history in a RAG application?

More info can be found [here](https://github.com/langchain-ai/langchain/discussions/29574)

1

0 replies

[![@joelbolz](https://avatars.githubusercontent.com/u/67657428?v=4)joelbolz](https://github.com/joelbolz) [Feb 5](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12072808)

Hello everyone!

I am currently building an application and wanted to implement persistent memory using the async approach of the postgresmemorysaver. It works as expected, no hassle at all.

However, after prototyping with a simple graph (chatnode powered by ChatAgent + ToolNode), we now want to build a multi agent system. To get into that, Ive created a simple Agent Team (Supervisor, + 2 Worker Nodes with create\_react\_agent() Agents). When using the in-RAM MemorySaver() on the outer graph, it works absolutely fine. The Supervisor works and the Workers do their work and are able to recall the previous messages.

When trying to use the AsyncPostgresSaver however (meaning I literally just gave the outer graph that one instead of the MemorySaver), the supervisor fires, but after that nothing happens. No Worker is fired, nor do I get any Errors or Exceptions of any kind.

Anyone got an Idea what the problem is here?

Ive also tried giving the workers the same memory object as checkpointers, to no avail.

Any and all help is greatly appreciated!

For simplicity, all relevant code is shown together below:

```
async def build_testteam_graph() -> StateGraph:
    from langchain_core.messages import HumanMessage
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent
    from langchain_core.tools import tool

    from typing import List, Optional, Literal, TypedDict
    from langchain_core.language_models.chat_models import BaseChatModel

    from langgraph.graph import StateGraph, MessagesState, START, END
    from langgraph.types import Command
    global pool
    async with pool.connection() as conn:
        # Initialize persistent chat memory
        memory = AsyncPostgresSaver(conn)

        await memory.setup()
        class State(MessagesState):
            next: str

        def make_supervisor_node(llm: BaseChatModel, members: list[str]) -> str:
            options = ["FINISH"] + members
            print(options)
            system_prompt = (
                "You are a supervisor tasked with completing the task from the User below. As the first step, you will assign a task to analyze the request and then based on the returned workplan, assign the next workers from"
                f" one of the following workers: {members}. They can write Poems,or analyze user requests accordingly. They will fullfill their task and respond with their"
                " respond with the worker to act next. Each worker will perform a"
                " results and status. When you think the task is completely fullfilled,"
                " respond with FINISH."
            )

            class Router(TypedDict):
                """Worker to route to next. If no workers needed, route to FINISH."""

                next: Literal[*options]

            def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
                """An LLM-based router."""
                messages = [\
                    {"role": "system", "content": system_prompt},\
                ] + state["messages"]
                response = llm.with_structured_output(Router).invoke(messages)
                goto = response["next"]
                if goto == "FINISH":
                    goto = END

                return Command(goto=goto, update={"next": goto})

            return supervisor_node

        @tool
        def create_poem() -> str:
            """Use this to return the poem. There is only one poem, it is always the same."""
            return "ich mag mein haus, das sieht gut aus und in ihm wohnt ne' maus!"

        llm = ChatOpenAI(model="gpt-4o", streaming=True, stream_usage=True)

        create_poem_agent = create_react_agent(llm, tools=[create_poem], state_modifier="Your task is to create a poem! After that you are done, do not create anything else!", checkpointer=memory)
        def create_poem_node(state: State) -> Command[Literal["supervisor"]]:
            result = create_poem_agent.invoke(state)
            return Command(
                update={
                    "messages": [\
                        HumanMessage(content=result["messages"][-1].content, name="poem_creator")\
                    ]
                },
                # We want our workers to ALWAYS "report back" to the supervisor when done
                goto="supervisor",
            )

        @tool
        def analyze_request(list_of_steps: List) -> str:
            """Use this tool to pack the request into a list of tuples of required steps with instructuions and the respective worker from these: [poem_creator, DKR_Searcher].! After that you are done, do not create anything else!"""
            return list_of_steps

        analyze_request_agent = create_react_agent(llm, tools=[analyze_request], state_modifier=f"Your task is to analyze the request and put it into a list of tuples of required steps with instructuions and the respective worker from these: [poem_creator].! After that you are done, do not create anything else!", checkpointer=memory)
        def analyze_request_node(state: State) -> Command[Literal["supervisor"]]:
            result = analyze_request_agent.invoke(state)
            return Command(
                update={
                    "messages": [\
                        HumanMessage(content=result["messages"][-1].content, name="request_analyzer")\
                    ]
                },
                goto="supervisor",
            )
        supervisor_node = make_supervisor_node(llm, ["poem_creator", "request_analyzer"])

        builder = StateGraph(State)
        builder.add_edge(START, "supervisor")
        builder.add_node("supervisor", supervisor_node)
        builder.add_node("poem_creator", create_poem_node)
        builder.add_node("request_analyzer", analyze_request_node)
        graph = builder.compile(checkpointer=memory)

        from PIL import Image
        import io
        im = Image.open(io.BytesIO(graph.get_graph().draw_mermaid_png()))
        im.show()

        return graph
```

1

1 reply

[![@joelbolz](https://avatars.githubusercontent.com/u/67657428?v=4)](https://github.com/joelbolz)

[joelbolz](https://github.com/joelbolz) [Feb 5](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12073052)

Ok I have tried out the synchronous PostgresSaver and with that it works, however only when using stream (compared to graph.astream that we used before).

Am I overlooking something here?

[![@jhachirag7](https://avatars.githubusercontent.com/u/70481022?v=4)jhachirag7](https://github.com/jhachirag7) [Feb 7](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12090121)

currently i have been getting this below error

```notranslate
  File "d:\NeolenSearchtool\multi-agent\ai-agents\api\agent_api\src\langgraph_agent.py", line 281, in _get_checkpoints
    return checkpointer.get(configdb)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "d:\NeolenSearchtool\multi-agent\ai-agents\env\Lib\site-packages\langgraph\checkpoint\base\__init__.py", line 236, in get
    if value := self.get_tuple(config):
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "d:\NeolenSearchtool\multi-agent\ai-agents\env\Lib\site-packages\langgraph\checkpoint\postgres\__init__.py", line 219, in get_tuple
    cur.execute(
  File "d:\NeolenSearchtool\multi-agent\ai-agents\env\Lib\site-packages\psycopg\cursor.py", line 97, in execute
    raise ex.with_traceback(None)
psycopg.errors.UndefinedColumn: column cw.task_path does not exist
LINE 27: ...array_agg(array[cw.type::bytea, cw.blob] order by cw.task_pa...

```

```notranslate
def _get_checkpoints(self, configdb: dict):
        """
        Retrieve database checkpoints with connection pooling.

        Args:
            configdb: Configuration dictionary

        Returns:
            Checkpoint data
        """
        with ConnectionPool(conninfo=self.db_uri, kwargs=self.connection_kwargs) as pool:
            checkpointer = PostgresSaver(pool)
            return checkpointer.get(configdb)

```

1

0 replies

[![@kunal646](https://avatars.githubusercontent.com/u/63719336?u=b71e73ee8b262081bc958bd0e830571ac70ba282&v=4)kunal646](https://github.com/kunal646) [Feb 15](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12212025)

If a graph have thread level persistence , then for the chatbot agent do I still need to pass previous messages every time? What’s the best way to manage memory without unnecessary repetition?

1

1 reply

[![@ritik7jain](https://avatars.githubusercontent.com/u/59771357?u=ddf34f7daa487d03d0127c3ed64ee2a0464bb90a&v=4)](https://github.com/ritik7jain)

[ritik7jain](https://github.com/ritik7jain) [Mar 19](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12548531)

I guess yes, i am too passing previous message each time a conv. history, you have to parse state snapshot and create history

[![@Don-peter-joseph](https://avatars.githubusercontent.com/u/63770464?v=4)Don-peter-joseph](https://github.com/Don-peter-joseph) [Mar 11](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12463244)

InvalidSchemaName: no schema has been selected to create in

LINE 1: CREATE TABLE IF NOT EXISTS checkpoint\_migrations

how to mention the schema

1

2 replies

[![@ritik7jain](https://avatars.githubusercontent.com/u/59771357?u=ddf34f7daa487d03d0127c3ed64ee2a0464bb90a&v=4)](https://github.com/ritik7jain)

[ritik7jain](https://github.com/ritik7jain) [Mar 19](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12548513)

have you found any solution to use specific schema instead of public

[![@ritik7jain](https://avatars.githubusercontent.com/u/59771357?u=ddf34f7daa487d03d0127c3ed64ee2a0464bb90a&v=4)](https://github.com/ritik7jain)

[ritik7jain](https://github.com/ritik7jain) [Mar 19](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12548848)

```notranslate
db_uri_with_schema = f"{DB_URI}?options=-csearch_path%3D{schema}"
with PostgresSaver.from_conn_string(db_uri_with_schema) as checkpointer:

```

This resolved issue for me

[![@ritik7jain](https://avatars.githubusercontent.com/u/59771357?u=ddf34f7daa487d03d0127c3ed64ee2a0464bb90a&v=4)ritik7jain](https://github.com/ritik7jain) [Mar 19](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12548651)

Is there any way to clear postgress table, once one chat session end

1

0 replies

[![@mail2chethankarur](https://avatars.githubusercontent.com/u/50777362?u=0d59440fc667cfc2bfaa4759ed0b6b441fef5b83&v=4)mail2chethankarur](https://github.com/mail2chethankarur) [Mar 19](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12551842)

Hi, I am using AsyncConnectionPool just like how it is shown in the documentation above.

But for some reason, it works only for first two times with one thread\_id. If I hit the endpoint for the third time on, it throws an error (put below). Basically, it is just terminating the connection with Postgres without any specific reason.

I'm building an agentic framework which contains subgraphs as nodes in the `main_graph`

```notranslate
 config = {"configurable": {"thread_id": session_id}}
from psycopg_pool import AsyncConnectionPool

        async with AsyncConnectionPool(
            conninfo=DB_URI,
            max_size=20,
            kwargs=connection_kwargs,
        ) as pool:
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()

            compiled_main = main_graph.compile(checkpointer=checkpointer)

            async for event in compiled_main.astream_events(
                initial_state, config, version="v2"
            ):
                    <rest of code>

```

Error:

\| psycopg.OperationalError: sending prepared query failed: server closed the connection unexpectedly

\| This probably means the server terminated abnormally

\| before or while processing the request.

> 📝 **title**
>
> >
>
> \> \- l'm using langgraph version 0.3.16 and in the subgraphs, I have added `(checkpointer=True)`

1

👍1

0 replies

[![@Trapti04](https://avatars.githubusercontent.com/u/36842908?u=2cc620eb410a848b90ab23b38b3b5d6cdb8196d2&v=4)Trapti04](https://github.com/Trapti04) [Mar 23](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12593869)

I am facing an issue with AsyncPostgresSaver when any state key in my State has a NaN value.. the default implementation does not handle conversion of state data which maybe NaN during serailization input postgresql. what is the best way to make this work. I am on langgraph version 0.3.5. and langgraph-checkpoint-postgres==2.0.15. generally the error occurs when one of my Sub Agents is raising a GrpahInterrupt for user info, I think the checkpointer tries to serailize in db what is currently in State and this exception is raised.

I have tried this-> but does not work :

lass CustomJsonPlusSerializer(JsonPlusSerializer):

"""Custom serializer that handles NaN values and rounds numeric values"""

```notranslate
def default(self, obj):
    """Handle NaN values and round numeric values during serialization"""
    try:
        if pd.isna(obj):
            return None
        if isinstance(obj, (np.number, float, int)):
            return float(round(obj, 2))
        if isinstance(obj, dict):
            return {k: self._default(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._default(item) for item in obj]
        return super()._default(obj)
    except Exception as e:
        self.logger.error(f"Error in _default: {str(e)}")
        raise

def encode(self, obj: Any) -> str:
    """Ensures serialization allows NaN values by using orjson options"""
    return orjson.dumps(
        obj,
        option=orjson.OPT_NAIVE_UTC | orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_ALLOW_NAN
    ).decode("utf-8")

```

1

2 replies

[![@Trapti04](https://avatars.githubusercontent.com/u/36842908?u=2cc620eb410a848b90ab23b38b3b5d6cdb8196d2&v=4)](https://github.com/Trapti04)

[Trapti04](https://github.com/Trapti04) [Mar 23](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12593929)

error I encounter File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/langgraph/checkpoint/postgres/aio.py", line 345, in \_cursor

conn.pipeline(),

^^^^^^^^^^^^^^^

File "/Users/traptikalra/.pyenv/versions/3.12.8/lib/python3.12/contextlib.py", line 217, in **aexit**

await anext(self.gen)

File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/psycopg/connection\_async.py", line 416, in pipeline

async with pipeline:

^^^^^^^^

File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/psycopg/\_pipeline.py", line 266, in **aexit**

raise exc2.with\_traceback(None)

psycopg.errors.InvalidTextRepresentation: invalid input syntax for type json

DETAIL: Token "NaN" is invalid.

CONTEXT: JSON data, line 1: ...3786, 43690.320158519615, 44859.282252098456, NaN...

unnamed portal parameter $6 = '...'

During task with name 'analyst' and id '38f96f06-c667-edff-9ef7-3672a0fabbcc'

[![@Trapti04](https://avatars.githubusercontent.com/u/36842908?u=2cc620eb410a848b90ab23b38b3b5d6cdb8196d2&v=4)](https://github.com/Trapti04)

[Trapti04](https://github.com/Trapti04) [Mar 24](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12601067)

then I decided to write a custom Serde from SerializerProtocol

class NaNSafeSerializer(SerializerProtocol):

"""Custom serializer that converts NaN, Infinity, and -Infinity to None for JSON compatibility."""

```notranslate
        @staticmethod
        def serialize(obj) -> str:
            """Convert object to JSON string, replacing NaN with None."""
            def replace_nan(val):
                if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                    return None  # Convert NaN, Infinity, -Infinity to JSON null
                return val

            # Recursively replace NaN in lists/dictionaries
            def clean_data(data):
                if isinstance(data, dict):
                    return {k: clean_data(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [clean_data(v) for v in data]
                return replace_nan(data)

            safe_obj = clean_data(obj)
            return json.dumps(safe_obj)

        @staticmethod
        def deserialize(data: str):
            """Convert JSON string back to object, handling NaN conversion."""
            if not data:  # Handle empty data case
                return {}

            parsed_data = json.loads(data)

            # Ensure returned object is iterable (dict, list, or at least an empty dict)
            if parsed_data is None:
                return {}  # Return an empty dict instead of None

            def replace_none(val):
                if val is None:
                    return np.nan  # Optionally convert back to NaN
                return val

            #parsed_data = json.loads(data)
            if isinstance(parsed_data, list):
                return [replace_none(v) for v in parsed_data]
            elif isinstance(parsed_data, dict):
                return {k: replace_none(v) for k, v in parsed_data.items()}
            return replace_none(parsed_data)

```

But I am getting another issue. please suggest what is to be done and if I can show you this issue, it will be great. this is the error here File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/langgraph/utils/runnable.py", line 583, in ainvoke

input = await step.ainvoke(input, config, \*\*kwargs)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/langgraph/pregel/ **init**.py", line 2420, in ainvoke

async for chunk in self.astream(

File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/langgraph/pregel/ **init**.py", line 2258, in astream

async with AsyncPregelLoop(

^^^^^^^^^^^^^^^^

File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/langgraph/pregel/loop.py", line 1109, in **aexit**

return await exit\_task

^^^^^^^^^^^^^^^

File "/Users/traptikalra/.pyenv/versions/3.12.8/lib/python3.12/contextlib.py", line 754, in **aexit**

raise exc\_details\[1\]

File "/Users/traptikalra/.pyenv/versions/3.12.8/lib/python3.12/contextlib.py", line 737, in **aexit**

cb\_suppress = await cb(\*exc\_details)

^^^^^^^^^^^^^^^^^^^^^^

File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/langgraph/pregel/executor.py", line 206, in **aexit**

raise exc

File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/langgraph/pregel/loop.py", line 1023, in \_checkpointer\_put\_after\_previous

await prev

File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/langgraph/pregel/loop.py", line 1025, in \_checkpointer\_put\_after\_previous

await cast(BaseCheckpointSaver, self.checkpointer).aput(

File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/langgraph/checkpoint/postgres/aio.py", line 263, in aput

await asyncio.to\_thread(

File "/Users/traptikalra/.pyenv/versions/3.12.8/lib/python3.12/asyncio/threads.py", line 25, in to\_thread

return await loop.run\_in\_executor(None, func\_call)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "/Users/traptikalra/.pyenv/versions/3.12.8/lib/python3.12/concurrent/futures/thread.py", line 59, in run

result = self.fn(\*self.args, \*\*self.kwargs)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "/Users/traptikalra/backend-ai/AnalyticsAI/chat\_ai\_service/agent\_service/.agentvenv/lib/python3.12/site-packages/langgraph/checkpoint/postgres/base.py", line 191, in \_dump\_blobs

(

TypeError: Value after \* must be an iterable, not NoneType

[![@WangXL1024](https://avatars.githubusercontent.com/u/200537839?v=4)WangXL1024](https://github.com/WangXL1024) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12695199)

When I execute the code for the "With a connection pool" and "With a connection" sections, the following error occurs:

PS C:\\01\_Work\\01\_Project\\MyPYProject\\LangGraph\\Persistence> python .\\use\_Postgres\_checkpointer\_for\_persistence.py

Traceback (most recent call last):

File "C:\\01\_Work\\01\_Project\\MyPYProject\\LangGraph\\Persistence\\use\_Postgres\_checkpointer\_for\_persistence.py", line 5, in

from langgraph.prebuilt import create\_react\_agent

File "C:\\01\_Work\\04\_Soft\\01\_Programs\\Python312\\Lib\\site-packages\\langgraph\\prebuilt\_ _init_\_.py", line 3, in

from langgraph.prebuilt.chat\_agent\_executor import create\_react\_agent

File "C:\\01\_Work\\04\_Soft\\01\_Programs\\Python312\\Lib\\site-packages\\langgraph\\prebuilt\\chat\_agent\_executor.py", line 33, in

from langgraph.graph import END, StateGraph

File "C:\\01\_Work\\04\_Soft\\01\_Programs\\Python312\\Lib\\site-packages\\langgraph\\graph\_ _init_\_.py", line 1, in

from langgraph.graph.graph import END, START, Graph

File "C:\\01\_Work\\04\_Soft\\01\_Programs\\Python312\\Lib\\site-packages\\langgraph\\graph\\graph.py", line 33, in

from langgraph.graph.branch import Branch

File "C:\\01\_Work\\04\_Soft\\01\_Programs\\Python312\\Lib\\site-packages\\langgraph\\graph\\branch.py", line 33, in

from langgraph.pregel.write import ChannelWrite

File "C:\\01\_Work\\04\_Soft\\01\_Programs\\Python312\\Lib\\site-packages\\langgraph\\pregel\_ _init_\_.py", line 93, in

from langgraph.pregel.checkpoint import create\_checkpoint

File "C:\\01\_Work\\04\_Soft\\01\_Programs\\Python312\\Lib\\site-packages\\langgraph\\pregel\\checkpoint.py", line 5, in

from langgraph.checkpoint.base import LATEST\_VERSION, Checkpoint

ImportError: cannot import name 'LATEST\_VERSION' from 'langgraph.checkpoint.base' (C:\\01\_Work\\04\_Soft\\01\_Programs\\Python312\\Lib\\site-packages\\langgraph\\checkpoint\\base\_ _init_\_.py)

1

1 reply

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12695703)

Contributor

edited

Hm i think you may have to upgrade your `langgraph-checkpoint` version. We may need to update the min-bound of langraph so that upgrading locally doesn't run into this issue. We will fix this in the next version so you don't have to manuall yupdaet the langgraph-checkpoint version

[![@yu-rovikov](https://avatars.githubusercontent.com/u/24842658?v=4)yu-rovikov](https://github.com/yu-rovikov) [19 days ago](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12734019)

Hi! I would like to have several `PostgresSaver` s for different services in my application. However, they would all dump the data into the same 4 tables:

checkpoint\_blobs

checkpoint\_migrations

checkpoint\_writes

checkpoints

Is this allowed? Do I need to worry about this? For example, do I need to ensure that different `PostgresSaver` s obtain different `thread_id` s?

1

0 replies

[![@rodpenna](https://avatars.githubusercontent.com/u/111186371?u=e4fe5a68b9e1f2fc54792165e2bd3950bf87377f&v=4)rodpenna](https://github.com/rodpenna) [16 days ago](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12770343)

I'm having a problem using AsyncConnectionPool and AsyncPostgresSaver together with FastAPI, when I make the request the error appears, I'm creating the pool during the lifespan and getting the checkpoint when the request is created.

AsyncCursorProxy.execute() got an unexpected keyword argument 'binary'

"fastapi>=0.115.12",

"langgraph>=0.3.26",

"langgraph-checkpoint-postgres>=2.0.19",

"langgraph-supervisor>=0.0.16",

"psutil>=7.0.0",

"psycopg-binary>=3.2.6",

"psycopg-pool>=3.2.6",

1

0 replies

[![@PovedaAqui](https://avatars.githubusercontent.com/u/9494679?u=112ef7fc2990fc0a83ccf2e26f71a7afad3c2dd5&v=4)PovedaAqui](https://github.com/PovedaAqui) [15 days ago](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12778806)

It has been painfully. Any example?

1

0 replies

[![@rajanskumarsoni](https://avatars.githubusercontent.com/u/10997744?u=c3fbfc0a9112b73171ddda6068a7c1fd6542364c&v=4)rajanskumarsoni](https://github.com/rajanskumarsoni) [21 minutes ago](https://github.com/langchain-ai/langgraph/discussions/894#discussioncomment-12940311)

got this error while executing above code:

ValueError: Asked to cache, but no cache found at `langchain.cache`.

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fpersistence_postgres%2F)