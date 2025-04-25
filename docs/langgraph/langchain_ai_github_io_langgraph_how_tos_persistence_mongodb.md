[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb/#how-to-use-mongodb-checkpointer-for-persistence)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/persistence_mongodb.ipynb "Edit this page")

# How to use MongoDB checkpointer for persistence [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb/\#how-to-use-mongodb-checkpointer-for-persistence "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [MongoDB](https://www.mongodb.com/)

When creating LangGraph agents, you can also set them up so that they persist their state. This allows you to do things like interact with an agent multiple times and have it remember previous interactions.

This reference implementation shows how to use MongoDB as the backend for persisting checkpoint state using the `langgraph-checkpoint-mongodb` library.

For demonstration purposes we add persistence to a [prebuilt ReAct agent](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/).

In general, you can add a checkpointer to any custom graph that you build like this:

```md-code__content
from langgraph.graph import StateGraph

builder = StateGraph(...)
# ... define the graph
checkpointer = # mongodb checkpointer (see examples below)
graph = builder.compile(checkpointer=checkpointer)
...

```

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb/\#setup "Permanent link")

To use the MongoDB checkpointer, you will need a MongoDB cluster. Follow [this guide](https://www.mongodb.com/docs/guides/atlas/cluster/) to create a cluster if you don't already have one.

Next, let's install the required packages and set our API keys

```md-code__content
%%capture --no-stderr
%pip install -U pymongo langgraph langgraph-checkpoint-mongodb

```

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")

```

```md-code__content
OPENAI_API_KEY:  ········

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Define model and tools for the graph [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb/\#define-model-and-tools-for-the-graph "Permanent link")

API Reference: [tool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

```md-code__content
from typing import Literal

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

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

## MongoDB checkpointer usage [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb/\#mongodb-checkpointer-usage "Permanent link")

### With a connection string [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb/\#with-a-connection-string "Permanent link")

This creates a connection to MongoDB directly using the connection string of your cluster. This is ideal for use in scripts, one-off operations and short-lived applications.

```md-code__content
from langgraph.checkpoint.mongodb import MongoDBSaver

MONGODB_URI = "localhost:27017"  # replace this with your connection string

with MongoDBSaver.from_conn_string(MONGODB_URI) as checkpointer:
    graph = create_react_agent(model, tools=tools, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "1"}}
    response = graph.invoke(
        {"messages": [("human", "what's the weather in sf")]}, config
    )

```

```md-code__content
response

```

```md-code__content
{'messages': [HumanMessage(content="what's the weather in sf", additional_kwargs={}, response_metadata={}, id='729afd6a-fdc0-4192-a255-1dac065c79b2'),\
  AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_YqaO8oU3BhGmIz9VHTxqGyyN', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_39a40c96a0', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-b45c0c12-c68e-4392-92dd-5d325d0a9f60-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_YqaO8oU3BhGmIz9VHTxqGyyN', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}),\
  ToolMessage(content="It's always sunny in sf", name='get_weather', id='0c72eb29-490b-44df-898f-8454c314eac1', tool_call_id='call_YqaO8oU3BhGmIz9VHTxqGyyN'),\
  AIMessage(content='The weather in San Francisco is always sunny!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_818c284075', 'finish_reason': 'stop', 'logprobs': None}, id='run-33f54c91-0ba9-48b7-9b25-5a972bbdeea9-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}

```

### Using the MongoDB client [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb/\#using-the-mongodb-client "Permanent link")

This creates a connection to MongoDB using the MongoDB client. This is ideal for long-running applications since it allows you to reuse the client instance for multiple database operations without needing to reinitialize the connection each time.

```md-code__content
from pymongo import MongoClient

mongodb_client = MongoClient(MONGODB_URI)

checkpointer = MongoDBSaver(mongodb_client)
graph = create_react_agent(model, tools=tools, checkpointer=checkpointer)
config = {"configurable": {"thread_id": "2"}}
response = graph.invoke({"messages": [("user", "What's the weather in sf?")]}, config)

```

```md-code__content
response

```

```md-code__content
{'messages': [HumanMessage(content="What's the weather in sf?", additional_kwargs={}, response_metadata={}, id='4ce68bee-a843-4b08-9c02-7a0e3b010110'),\
  AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_MvGxq9IU9wvW9mfYKSALHtGu', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_6fc10e10eb', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-9712c5a4-376c-4812-a0c4-1b522334a59d-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_MvGxq9IU9wvW9mfYKSALHtGu', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}),\
  ToolMessage(content="It's always sunny in sf", name='get_weather', id='b4eed38d-bcaf-4497-ad08-f21ccd6a8c30', tool_call_id='call_MvGxq9IU9wvW9mfYKSALHtGu'),\
  AIMessage(content='The weather in San Francisco is always sunny!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_6fc10e10eb', 'finish_reason': 'stop', 'logprobs': None}, id='run-c6c4ad75-89ef-4b4f-9ca4-bd52ccb0729b-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}

```

```md-code__content
# Retrieve the latest checkpoint for the given thread ID
# To retrieve a specific checkpoint, pass the checkpoint_id in the config
checkpointer.get_tuple(config)

```

```md-code__content
CheckpointTuple(config={'configurable': {'thread_id': '2', 'checkpoint_ns': '', 'checkpoint_id': '1efb8c75-9262-68b4-8003-1ac1ef198757'}}, checkpoint={'v': 1, 'ts': '2024-12-12T20:26:20.545003+00:00', 'id': '1efb8c75-9262-68b4-8003-1ac1ef198757', 'channel_values': {'messages': [HumanMessage(content="What's the weather in sf?", additional_kwargs={}, response_metadata={}, id='4ce68bee-a843-4b08-9c02-7a0e3b010110'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_MvGxq9IU9wvW9mfYKSALHtGu', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_6fc10e10eb', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-9712c5a4-376c-4812-a0c4-1b522334a59d-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_MvGxq9IU9wvW9mfYKSALHtGu', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}), ToolMessage(content="It's always sunny in sf", name='get_weather', id='b4eed38d-bcaf-4497-ad08-f21ccd6a8c30', tool_call_id='call_MvGxq9IU9wvW9mfYKSALHtGu'), AIMessage(content='The weather in San Francisco is always sunny!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_6fc10e10eb', 'finish_reason': 'stop', 'logprobs': None}, id='run-c6c4ad75-89ef-4b4f-9ca4-bd52ccb0729b-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})], 'agent': 'agent'}, 'channel_versions': {'__start__': 2, 'messages': 5, 'start:agent': 3, 'agent': 5, 'branch:agent:should_continue:tools': 4, 'tools': 5}, 'versions_seen': {'__input__': {}, '__start__': {'__start__': 1}, 'agent': {'start:agent': 2, 'tools': 4}, 'tools': {'branch:agent:should_continue:tools': 3}}, 'pending_sends': []}, metadata={'source': 'loop', 'writes': {'agent': {'messages': [AIMessage(content='The weather in San Francisco is always sunny!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_6fc10e10eb', 'finish_reason': 'stop', 'logprobs': None}, id='run-c6c4ad75-89ef-4b4f-9ca4-bd52ccb0729b-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}}, 'thread_id': '2', 'step': 3, 'parents': {}}, parent_config={'configurable': {'thread_id': '2', 'checkpoint_ns': '', 'checkpoint_id': '1efb8c75-8d89-6ffe-8002-84a4312c4fed'}}, pending_writes=[])

```

```md-code__content
# Remember to close the connection after you're done
mongodb_client.close()

```

### Using an async connection [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb/\#using-an-async-connection "Permanent link")

This creates a short-lived asynchronous connection to MongoDB.

Async connections allow non-blocking database operations. This means other parts of your application can continue running while waiting for database operations to complete. It's particularly useful in high-concurrency scenarios or when dealing with I/O-bound operations.

```md-code__content
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

async with AsyncMongoDBSaver.from_conn_string(MONGODB_URI) as checkpointer:
    graph = create_react_agent(model, tools=tools, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "3"}}
    response = await graph.ainvoke(
        {"messages": [("user", "What's the weather in sf?")]}, config
    )

```

```md-code__content
response

```

```md-code__content
{'messages': [HumanMessage(content="What's the weather in sf?", additional_kwargs={}, response_metadata={}, id='fed70fe6-1b2e-4481-9bfc-063df3b587dc'),\
  AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_miRiF3vPQv98wlDHl6CeRxBy', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_6fc10e10eb', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-7f2d5153-973e-4a9e-8b71-a77625c342cf-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_miRiF3vPQv98wlDHl6CeRxBy', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}),\
  ToolMessage(content="It's always sunny in sf", name='get_weather', id='49035e8e-8aee-4d9d-88ab-9a1bc10ecbd3', tool_call_id='call_miRiF3vPQv98wlDHl6CeRxBy'),\
  AIMessage(content='The weather in San Francisco is always sunny!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_6fc10e10eb', 'finish_reason': 'stop', 'logprobs': None}, id='run-9403d502-391e-4407-99fd-eec8ed184e50-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}

```

### Using the async MongoDB client [¶](https://langchain-ai.github.io/langgraph/how-tos/persistence_mongodb/\#using-the-async-mongodb-client "Permanent link")

This routes connections to MongoDB through an asynchronous MongoDB client.

```md-code__content
from pymongo import AsyncMongoClient

async_mongodb_client = AsyncMongoClient(MONGODB_URI)

checkpointer = AsyncMongoDBSaver(async_mongodb_client)
graph = create_react_agent(model, tools=tools, checkpointer=checkpointer)
config = {"configurable": {"thread_id": "4"}}
response = await graph.ainvoke(
    {"messages": [("user", "What's the weather in sf?")]}, config
)

```

```md-code__content
response

```

```md-code__content
{'messages': [HumanMessage(content="What's the weather in sf?", additional_kwargs={}, response_metadata={}, id='58282e2b-4cc1-40a1-8e65-420a2177bbd6'),\
  AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_SJFViVHl1tYTZDoZkNN3ePhJ', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_bba3c8e70b', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-131af8c1-d388-4d7f-9137-da59ebd5fefd-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_SJFViVHl1tYTZDoZkNN3ePhJ', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}),\
  ToolMessage(content="It's always sunny in sf", name='get_weather', id='6090a56f-177b-4d3f-b16a-9c05f23800e3', tool_call_id='call_SJFViVHl1tYTZDoZkNN3ePhJ'),\
  AIMessage(content='The weather in San Francisco is always sunny!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_6fc10e10eb', 'finish_reason': 'stop', 'logprobs': None}, id='run-6ff5ddf5-6e13-4126-8df9-81c8638355fc-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}

```

```md-code__content
# Retrieve the latest checkpoint for the given thread ID
# To retrieve a specific checkpoint, pass the checkpoint_id in the config
latest_checkpoint = await checkpointer.aget_tuple(config)
print(latest_checkpoint)

```

```md-code__content
CheckpointTuple(config={'configurable': {'thread_id': '4', 'checkpoint_ns': '', 'checkpoint_id': '1efb8c76-21f4-6d10-8003-9496e1754e93'}}, checkpoint={'v': 1, 'ts': '2024-12-12T20:26:35.599560+00:00', 'id': '1efb8c76-21f4-6d10-8003-9496e1754e93', 'channel_values': {'messages': [HumanMessage(content="What's the weather in sf?", additional_kwargs={}, response_metadata={}, id='58282e2b-4cc1-40a1-8e65-420a2177bbd6'), AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_SJFViVHl1tYTZDoZkNN3ePhJ', 'function': {'arguments': '{"city":"sf"}', 'name': 'get_weather'}, 'type': 'function'}], 'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 14, 'prompt_tokens': 57, 'total_tokens': 71, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_bba3c8e70b', 'finish_reason': 'tool_calls', 'logprobs': None}, id='run-131af8c1-d388-4d7f-9137-da59ebd5fefd-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'sf'}, 'id': 'call_SJFViVHl1tYTZDoZkNN3ePhJ', 'type': 'tool_call'}], usage_metadata={'input_tokens': 57, 'output_tokens': 14, 'total_tokens': 71, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}), ToolMessage(content="It's always sunny in sf", name='get_weather', id='6090a56f-177b-4d3f-b16a-9c05f23800e3', tool_call_id='call_SJFViVHl1tYTZDoZkNN3ePhJ'), AIMessage(content='The weather in San Francisco is always sunny!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_6fc10e10eb', 'finish_reason': 'stop', 'logprobs': None}, id='run-6ff5ddf5-6e13-4126-8df9-81c8638355fc-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})], 'agent': 'agent'}, 'channel_versions': {'__start__': 2, 'messages': 5, 'start:agent': 3, 'agent': 5, 'branch:agent:should_continue:tools': 4, 'tools': 5}, 'versions_seen': {'__input__': {}, '__start__': {'__start__': 1}, 'agent': {'start:agent': 2, 'tools': 4}, 'tools': {'branch:agent:should_continue:tools': 3}}, 'pending_sends': []}, metadata={'source': 'loop', 'writes': {'agent': {'messages': [AIMessage(content='The weather in San Francisco is always sunny!', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 10, 'prompt_tokens': 84, 'total_tokens': 94, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_6fc10e10eb', 'finish_reason': 'stop', 'logprobs': None}, id='run-6ff5ddf5-6e13-4126-8df9-81c8638355fc-0', usage_metadata={'input_tokens': 84, 'output_tokens': 10, 'total_tokens': 94, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})]}}, 'thread_id': '4', 'step': 3, 'parents': {}}, parent_config={'configurable': {'thread_id': '4', 'checkpoint_ns': '', 'checkpoint_id': '1efb8c76-1c6c-6474-8002-9c2595cd481c'}}, pending_writes=[])

```

```md-code__content
# Remember to close the connection after you're done
await async_mongodb_client.close()

```

## Comments

giscus

#### [6 reactions](https://github.com/langchain-ai/langgraph/discussions/1054)

❤️6

#### [16 comments](https://github.com/langchain-ai/langgraph/discussions/1054)

#### ·

#### 18 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)HoangNguyen689](https://github.com/HoangNguyen689) [Jul 18, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10079697)

Sometimes, I see that you use `checkpoint_id` for the `thread_ts`, sometimes you use `checkpoint_ts` for the `thread_ts`. Which value should be use?

1

5 replies

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Jul 18, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10090085)

Collaborator

[@HoangNguyen689](https://github.com/HoangNguyen689) you should use `checkpoint_id`, `thread_ts` is a legacy name

👍3

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)](https://github.com/HoangNguyen689)

[HoangNguyen689](https://github.com/HoangNguyen689) [Jul 19, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10094087)

[@vbarda](https://github.com/vbarda)

We are moving from AgentExecutor to LangGraph.

In AgentExecutor, we use DynamoDB for persistent memory through chat\_history content.

We pass the chat\_history to the prompt as a placeholder.

When using LangGraph, we defined a DynamoDBSaver to implement the checkpointer.

That checkpointer go well, when printing it, i can see the chat history in the channel\_values\["messages"\].

However, the LLM agent doesn't have any knowledge about conversation history.

We already followed the above instruction and also read the blog about PostreSQL and MongoDB.

Is the conversation history in the checkpointer consumed automatically by the agent node?

❤️1

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)](https://github.com/HoangNguyen689)

[HoangNguyen689](https://github.com/HoangNguyen689) [Jul 19, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10094168)

figure it out. Just passing all the state\["messages"\] that should be fine

👍1

[![@AlcebiadesFilho](https://avatars.githubusercontent.com/u/78539159?u=d5915a088f6b312ea44681760a5cc44051d6ca02&v=4)](https://github.com/AlcebiadesFilho)

[AlcebiadesFilho](https://github.com/AlcebiadesFilho) [Dec 3, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11452946)

[@HoangNguyen689](https://github.com/HoangNguyen689)

you can show how you do that ? Im stay with the same problem

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)](https://github.com/HoangNguyen689)

[HoangNguyen689](https://github.com/HoangNguyen689) [Dec 10, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11522403)

[@AlcebiadesFilho](https://github.com/AlcebiadesFilho)

Sorry for late response. Which problem did you face?

In my case, State store the messages variable, which store all the conversation history.

```
class State(TypedDict):
    today_date: str

    messages: Annotated[list[AnyMessage], add_messages]
```

After that, you can define the model/assistant like below:

```
    def call_assistant(self, state: State) -> dict[str, list[BaseMessage]]:
        model_runnable = self.prompt | self.llm.bind_tools(
            self.tools, parallel_tool_calls=False
        )

        response = model_runnable.invoke(
            {
                "messages": state["messages"],
            }
        )

        return {"messages": [response]}
```

And finally, you just need to pass the user input

```
res = app.invoke(
                {
                    "messages": user_input,
                    "today_date": today_date,
                },
            )
```

[![@roboticsocialism](https://avatars.githubusercontent.com/u/147677847?v=4)roboticsocialism](https://github.com/roboticsocialism) [Jul 19, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10093789)

I cannot find the module in the latest current version 0.1.9

1

1 reply

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Jul 22, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10109393)

Collaborator

[@roboticsocialism](https://github.com/roboticsocialism) there is no module for this in the library, this is just a reference implementation

[![@guilledt](https://avatars.githubusercontent.com/u/65425245?v=4)guilledt](https://github.com/guilledt) [Jul 24, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10136740)

Hi! How can I limit the number of previous messages in the memory, so that not all messages are remembered!

1

👀3

2 replies

[![@Mr-Frk](https://avatars.githubusercontent.com/u/68559129?u=efcf1e796a5e06778f822750a74facc260b81e49&v=4)](https://github.com/Mr-Frk)

[Mr-Frk](https://github.com/Mr-Frk) [Oct 23, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11027158)

I got same issue. Does anyone know the solution?

👍1

[![@mihailtd](https://avatars.githubusercontent.com/u/7993468?u=9f13c0a9d53ff62fefb1911671f0b3c5857cfba6&v=4)](https://github.com/mihailtd)

[mihailtd](https://github.com/mihailtd) [Nov 19, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11311429)

Any solution to this? just change the thread ID?

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)HoangNguyen689](https://github.com/HoangNguyen689) [Jul 25, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10145581)

I believe that this example is outdated.

As I see, the langgraph also has put\_writes method.

What purposes the `writes` is used for?

1

1 reply

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Aug 9, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10289674)

Collaborator

We just updated the example to have all of the necessary methods. `writes` refer to intermediate writes from successful nodes, so that if one of the nodes running in parallel with others fails and we restart execution from the failure point, we don't re-run the ones that already succeeded. hope this helps!

[![@xuejuhui](https://avatars.githubusercontent.com/u/32085550?v=4)xuejuhui](https://github.com/xuejuhui) [Jul 25, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10153869)

when using Asynchronous implementation of mongodb, it error out in the new version of langgraph, works in 0.1.9

AsyncBackgroundExecutor.exit(self, exc\_type, exc\_value, traceback)

152 for task in self.tasks:

153 try:

--\> 154 task.result()

155 except asyncio.CancelledError:

156 pass

NotImplementedError: This method was added in langgraph 0.1.7. Please update your checkpoint saver to implement it.

1

1 reply

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Aug 9, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10289681)

Collaborator

We just updated the guide to have all of the necessary methods

[![@LordO54](https://avatars.githubusercontent.com/u/119976077?v=4)LordO54](https://github.com/LordO54) [Aug 1, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10206458)

how do I stream this?

config = {"configurable": {"thread\_id": "2"}}

inputs = {"question": "me gustaria saber que consideraciones nutricionales necesito tener a la hora de bajar de peso","sessionid":"006", "userdata":userdata,}

async for event in app\_memo.astream\_events(input=inputs, version="v2", config=config):

kind = event\["event"\]

tags = event.get("tags", \[\])

if kind == "on\_chat\_model\_stream" and "tool\_llm" in tags:

data = event\["data"\]\["chunk"\].content

if data:

\# Empty content in the context of OpenAI or Anthropic usually means

\# that the model is asking for a tool to be invoked.

\# So we only print non-empty content

print(data, end="")

File c:\\Users\\PC\\anaconda3\\envs\\myenv\\Lib\\site-packages\\langgraph\\pregel\_ _init_\_.py:1098, in Pregel.astream(self, input, config, stream\_mode, output\_keys, input\_keys, interrupt\_before, interrupt\_after, debug)

1095 processes = {\*\*self.nodes}

1096 # get checkpoint from saver, or create an empty one

...

(...)

141 ),

142 )

TypeError: 'async for' requires an object with **aiter** method, got Cursor

1

0 replies

[![@RichmondAlake](https://avatars.githubusercontent.com/u/16384755?v=4)RichmondAlake](https://github.com/RichmondAlake) [Aug 7, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10269180)

Replace: langgraph.serde.jsonplus import JsonPlusSerializer

With: from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

1

❤️1

1 reply

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Aug 9, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10289685)

Collaborator

We just updated the guide, thanks for flagging!

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)vbarda](https://github.com/vbarda) [Aug 9, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10289688)

Collaborator

Hi all! The guide has been updated with the correct implementtions of `.put_writes` and `.aput_writes`

1

0 replies

[![@parokshsaxena](https://avatars.githubusercontent.com/u/3033105?v=4)parokshsaxena](https://github.com/parokshsaxena) [Sep 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10610535)

Thanks for providing this implementation! This is super helpful.

One problem I am facing is even if I am setting the `checkpoint_ns`, I am always getting `checkpoint_ns` as '' while debugging in `aput` function.

My config is

config = {"configurable": {"thread\_id": "2", "checkpoint\_ns": "test"}}

Am I missing anything?

1

1 reply

[![@parokshsaxena](https://avatars.githubusercontent.com/u/3033105?v=4)](https://github.com/parokshsaxena)

[parokshsaxena](https://github.com/parokshsaxena) [Sep 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10610551)

One observation. while debugging `config` received in `aput` function, I see in `metadata` it has correct value of checkpoint\_ns but in configurable it's empty. Although while calling I am setting it in `configurable` parameter as specified in this doc

[![@Taha0229](https://avatars.githubusercontent.com/u/113607983?v=4)Taha0229](https://github.com/Taha0229) [Sep 14, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10646072)

Hi,

I have implemented a graph with mongodb checkpointer in my FastAPI, but following this example, every time a request comes in, a new context is created for the checkpointer and a graph object is also instantiated which compiles the graph with the checkpointer. Following this the graph is invoked. Is this the only way to do it? I cannot compile a graph beforehand, because mongodb context is required which is passed as the checkpointer and within that context I need to invoke the graph. So to invoke the graph on every incoming request I first create a context then compile the graph by making an object (of my graph class) and then invoking it.

1

1 reply

[![@theofficialvedantjoshi](https://avatars.githubusercontent.com/u/76871277?u=899312b3757a11cdb82b89c3196acaffaf50dc66&v=4)](https://github.com/theofficialvedantjoshi)

[theofficialvedantjoshi](https://github.com/theofficialvedantjoshi) [Sep 20, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-10704428)

Contributor

You do not need to initiate a new graph object everytime.

Create a class Workflow and inside it define a stategraph and a checkpointer object of type MongoDBSaver.

Create a self.app = stategraph.compile(checkpointer=self.checkpointer).

In your code create a workflow object and invoke workflow.app with specific state data and config.

The db keeps updating in the back and is not reset.

If this doesnt help you elaborate on your issue.

[![@my23701](https://avatars.githubusercontent.com/u/65496483?v=4)my23701](https://github.com/my23701) [Nov 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11213153)

I am getting this error does anyone faced the same problem?

psycopg.Not SupportedError: the feature 'Connection.pipeline()" is not available: the client libpq version (imported from system libraries) is 13.11; the feature requires libpq version 14.0 or newer

1

1 reply

[![@my23701](https://avatars.githubusercontent.com/u/65496483?v=4)](https://github.com/my23701)

[my23701](https://github.com/my23701) [Nov 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11213166)

Sorry, this was wrong blog you guys can ignore it, its for Postgres implementation.

[![@cris-m](https://avatars.githubusercontent.com/u/29815096?u=4b55bcd0d0e557e3cc2a483bfd427627d7e52493&v=4)cris-m](https://github.com/cris-m) [Nov 15, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11266350)

I am having issue using `MongoDBSaver` in `langgraph`. I am getting `AttributeError: '_GeneratorContextManager' object has no attribute 'get_next_version'`

```
checkpointer = MongoDBSaver.from_conn_info(
    host="localhost", port=27017, db_name="checkpoints"
)
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=[],
    interrupt_after=[],
)
graph.name = "Agent"
```

1

2 replies

[![@bhat-abhishek](https://avatars.githubusercontent.com/u/86356896?v=4)](https://github.com/bhat-abhishek)

[bhat-abhishek](https://github.com/bhat-abhishek) [Nov 18, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11291069)

Even I am getting the same error

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Nov 18, 2024](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11292344)

Collaborator

that's because you need to use it as a context manager

```
with MongoDB.from_conn_info(...) as checkpointer:
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=[],
        interrupt_after=[],
    )
    graph.invoke(...)
```

👍2

[![@gokpm](https://avatars.githubusercontent.com/u/25360621?v=4)gokpm](https://github.com/gokpm) [Jan 22](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11911014)

What indexes should be created in MongoDB to support the queries this driver would use?

1

1 reply

[![@gokpm](https://avatars.githubusercontent.com/u/25360621?v=4)](https://github.com/gokpm)

[gokpm](https://github.com/gokpm) [Jan 22](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11911061)

Also, which field to add the TTL index in case older records should be removed?

[![@pranaykoppula](https://avatars.githubusercontent.com/u/58975464?v=4)pranaykoppula](https://github.com/pranaykoppula) [Jan 27](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-11966563)

Although I'm trying to use thread level persistence, the model seems to remember details from conversation in different threads. Am I doing it wring?

> class CustomState(TypedDict):
>
> user\_context: str
>
> humanReadableDate:str
>
> messages: Annotated\[list\[BaseMessage\], add\_messages\]
>
> is\_last\_step: IsLastStep

> memory = MongoDBSaver(client=mongo\_client,db\_name="user\_conversations")
>
> agent = create\_react\_agent(llm, tools, state\_schema=CustomState, state\_modifier=prompt, checkpointer=memory)
>
> response=agent.invoke(inputs,config={'configurable':{'thread\_id':session\_id}})

1

0 replies

[![@PigsyAK](https://avatars.githubusercontent.com/u/122603246?u=c21a8c1cee032b9af6e76587ba19ddf37890c678&v=4)PigsyAK](https://github.com/PigsyAK) [Mar 14](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-12495419)

### With a connection string

In my case:

```
MONGODB_URI = "mongodb://user:PasswOrd@localhost:27017/"  # replace this with your connection string
```

1

1 reply

[![@ThangQT2606](https://avatars.githubusercontent.com/u/134129739?u=82405ddf331bd40621af65273b3501b2a9232e6a&v=4)](https://github.com/ThangQT2606)

[ThangQT2606](https://github.com/ThangQT2606) [15 days ago](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-12772931)

what if i want to use both user\_id and thread\_id? thanks for help

[![@ThangQT2606](https://avatars.githubusercontent.com/u/134129739?u=82405ddf331bd40621af65273b3501b2a9232e6a&v=4)ThangQT2606](https://github.com/ThangQT2606) [15 days ago](https://github.com/langchain-ai/langgraph/discussions/1054#discussioncomment-12772937)

what if i want to use both user\_id and thread\_id? thanks for help

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fpersistence_mongodb%2F)