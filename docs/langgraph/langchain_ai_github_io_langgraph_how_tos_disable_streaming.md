[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/disable-streaming/#how-to-disable-streaming-for-models-that-dont-support-it)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/disable-streaming.ipynb "Edit this page")

# How to disable streaming for models that don't support it [¶](https://langchain-ai.github.io/langgraph/how-tos/disable-streaming/\#how-to-disable-streaming-for-models-that-dont-support-it "Permanent link")

Prerequisites

This guide assumes familiarity with the following:


- [streaming](https://python.langchain.com/docs/concepts/#streaming)
- [Chat Models](https://python.langchain.com/docs/concepts/#chat-models/)

Some chat models, including the new O1 models from OpenAI (depending on when you're reading this), do not support streaming. This can lead to issues when using the [astream\_events API](https://python.langchain.com/docs/concepts/#astream_events), as it calls models in streaming mode, expecting streaming to function properly.

In this guide, we’ll show you how to disable streaming for models that don’t support it, ensuring they they're never called in streaming mode, even when invoked through the astream\_events API.

API Reference: [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END)

```md-code__content
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END

llm = ChatOpenAI(model="o1-preview", temperature=1)

graph_builder = StateGraph(MessagesState)

def chatbot(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

```

```md-code__content
from IPython.display import Image, display

display(Image(graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

## Without disabling streaming [¶](https://langchain-ai.github.io/langgraph/how-tos/disable-streaming/\#without-disabling-streaming "Permanent link")

Now that we've defined our graph, let's try to call `astream_events` without disabling streaming. This should throw an error because the `o1` model does not support streaming natively:

```md-code__content
input = {"messages": {"role": "user", "content": "how many r's are in strawberry?"}}
try:
    async for event in graph.astream_events(input, version="v2"):
        if event["event"] == "on_chat_model_end":
            print(event["data"]["output"].content, end="", flush=True)
except:
    print("Streaming not supported!")

```

```md-code__content
Streaming not supported!

```

An error occurred as we expected, luckily there is an easy fix!

## Disabling streaming [¶](https://langchain-ai.github.io/langgraph/how-tos/disable-streaming/\#disabling-streaming "Permanent link")

Now without making any changes to our graph, let's set the [disable\_streaming](https://python.langchain.com/api_reference/core/language_models/langchain_core.language_models.chat_models.BaseChatModel.html#langchain_core.language_models.chat_models.BaseChatModel.disable_streaming) parameter on our model to be `True` which will solve the problem:

```md-code__content
llm = ChatOpenAI(model="o1-preview", temperature=1, disable_streaming=True)

graph_builder = StateGraph(MessagesState)

def chatbot(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

```

And now, rerunning with the same input, we should see no errors:

```md-code__content
input = {"messages": {"role": "user", "content": "how many r's are in strawberry?"}}
async for event in graph.astream_events(input, version="v2"):
    if event["event"] == "on_chat_model_end":
        print(event["data"]["output"].content, end="", flush=True)

```

```md-code__content
There are three "r"s in the word "strawberry".

```

## Comments

giscus

#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/3769)

👍1

#### [0 comments](https://github.com/langchain-ai/langgraph/discussions/3769)

_– powered by [giscus](https://giscus.app/)_

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fdisable-streaming%2F)