[Skip to content](https://langchain-ai.github.io/langgraph/agents/models/#models)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/agents/models.md "Edit this page")

# Models [¶](https://langchain-ai.github.io/langgraph/agents/models/\#models "Permanent link")

This page describes how to configure the chat model used by an agent.

## Tool calling support [¶](https://langchain-ai.github.io/langgraph/agents/models/\#tool-calling-support "Permanent link")

To enable tool-calling agents, the underlying LLM must support [tool calling](https://python.langchain.com/docs/concepts/tool_calling/).

Compatible models can be found in the [LangChain integrations directory](https://python.langchain.com/docs/integrations/chat/).

## Specifying a model by name [¶](https://langchain-ai.github.io/langgraph/agents/models/\#specifying-a-model-by-name "Permanent link")

You can configure an agent with a model name string:

API Reference: [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

```md-code__content
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    # other parameters
)

```

## Using `init_chat_model` [¶](https://langchain-ai.github.io/langgraph/agents/models/\#using-init_chat_model "Permanent link")

The [`init_chat_model`](https://python.langchain.com/docs/how_to/chat_models_universal_init/) utility simplifies model initialization with configurable parameters:

API Reference: [init\_chat\_model](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html)

```md-code__content
from langchain.chat_models import init_chat_model

model = init_chat_model(
    "anthropic:claude-3-7-sonnet-latest",
    temperature=0,
    max_tokens=2048
)

```

Refer to the [API reference](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html) for advanced options.

## Using provider-specific LLMs [¶](https://langchain-ai.github.io/langgraph/agents/models/\#using-provider-specific-llms "Permanent link")

If a model provider is not available via `init_chat_model`, you can instantiate the provider's model class directly. The model must implement the [BaseChatModel interface](https://python.langchain.com/api_reference/core/language_models/langchain_core.language_models.chat_models.BaseChatModel.html) and support tool calling:

API Reference: [ChatAnthropic](https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html) \| [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

```md-code__content
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

model = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    temperature=0,
    max_tokens=2048
)

agent = create_react_agent(
    model=model,
    # other parameters
)

```

Illustrative example

The example above uses `ChatAnthropic`, which is already supported by `init_chat_model`. This pattern is shown to illustrate how to manually instantiate a model not available through init\_chat\_model.

## Additional resources [¶](https://langchain-ai.github.io/langgraph/agents/models/\#additional-resources "Permanent link")

- [Model integration directory](https://python.langchain.com/docs/integrations/chat/)
- [Universal initialization with `init_chat_model`](https://python.langchain.com/docs/how_to/chat_models_universal_init/)

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fagents%2Fmodels%2F)