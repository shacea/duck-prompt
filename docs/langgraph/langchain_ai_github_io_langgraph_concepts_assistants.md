[Skip to content](https://langchain-ai.github.io/langgraph/concepts/assistants/#assistants)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/assistants.md "Edit this page")

# Assistants [¶](https://langchain-ai.github.io/langgraph/concepts/assistants/\#assistants "Permanent link")

Prerequisites

- [LangGraph Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/)

When building agents, it is fairly common to make rapid changes that _do not_ alter the graph logic. For example, simply changing prompts or the LLM selection can have significant impacts on the behavior of the agents. Assistants offer an easy way to make and save these types of changes to agent configuration. This can have at least two use-cases:

- Assistants give developers a quick and easy way to modify and version agents for experimentation.
- Assistants can be modified via LangGraph Studio, offering a no-code way to configure agents (e.g., for business users).

Assistants build off the concept of ["configuration"](https://langchain-ai.github.io/langgraph/concepts/low_level/#configuration).
While ["configuration"](https://langchain-ai.github.io/langgraph/concepts/low_level/#configuration) is available in the open source LangGraph library as well, assistants are only present in [LangGraph Platform](https://langchain-ai.github.io/langgraph/concepts/langgraph_platform/).
This is because Assistants are tightly coupled to your deployed graph, and so we can only make them available when we are also deploying the graphs.

## Configuring Assistants [¶](https://langchain-ai.github.io/langgraph/concepts/assistants/\#configuring-assistants "Permanent link")

In practice, an assistant is just an _instance_ of a graph with a specific configuration. Because of this, multiple assistants can reference the same graph but can contain different configurations, such as prompts, models, and other graph configuration options. The LangGraph Cloud API provides several endpoints for creating and managing assistants. See the [API reference](https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref.html) and [this how-to](https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/) for more details on how to create assistants.

## Versioning Assistants [¶](https://langchain-ai.github.io/langgraph/concepts/assistants/\#versioning-assistants "Permanent link")

Once you've created an assistant, you can save and version it to track changes to the configuration over time. You can think about this at three levels:

1) The graph lays out the general agent application logic
2) The agent configuration options represent parameters that can be changed
3) Assistant versions save and track specific settings of the agent configuration options

For example, let's imagine you have a general writing agent. You have created a general graph architecture that works well for writing. However, there are different types of writing, e.g. blogs vs tweets. In order to get the best performance on each use case, you need to make some minor changes to the models and prompts used. In this setup, you could create an assistant for each use case - one for blog writing and one for tweeting. These would share the same graph structure, but they may use different models and different prompts. Read [this how-to](https://langchain-ai.github.io/langgraph/cloud/how-tos/assistant_versioning/) to learn how you can use assistant versioning through both the [Studio](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/) and the SDK.

![assistant versions](https://langchain-ai.github.io/langgraph/concepts/img/assistants.png)

## Resources [¶](https://langchain-ai.github.io/langgraph/concepts/assistants/\#resources "Permanent link")

For more information on assistants, see the following resources:

- [Assistants how-to guides](https://langchain-ai.github.io/langgraph/how-tos/#assistants)

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Fassistants%2F)