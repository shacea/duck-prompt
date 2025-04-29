[Skip to content](https://langchain-ai.github.io/langgraph/concepts/template_applications/?q=#template-applications)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/template_applications.md "Edit this page")

# Template Applications [¶](https://langchain-ai.github.io/langgraph/concepts/template_applications/?q=\#template-applications "Permanent link")

Templates are open source reference applications designed to help you get started quickly when building with LangGraph. They provide working examples of common agentic workflows that can be customized to your needs.

You can create an application from a template using the LangGraph CLI.

Requirements

- Python >= 3.11
- [LangGraph CLI](https://langchain-ai.github.io/langgraph/cloud/reference/cli/): Requires langchain-cli\[inmem\] >= 0.1.58

## Install the LangGraph CLI [¶](https://langchain-ai.github.io/langgraph/concepts/template_applications/?q=\#install-the-langgraph-cli "Permanent link")

```md-code__content
pip install "langgraph-cli[inmem]" --upgrade

```

## Available Templates [¶](https://langchain-ai.github.io/langgraph/concepts/template_applications/?q=\#available-templates "Permanent link")

| Template | Description | Python | JS/TS |
| --- | --- | --- | --- |
| **New LangGraph Project** | A simple, minimal chatbot with memory. | [Repo](https://github.com/langchain-ai/new-langgraph-project) | [Repo](https://github.com/langchain-ai/new-langgraphjs-project) |
| **ReAct Agent** | A simple agent that can be flexibly extended to many tools. | [Repo](https://github.com/langchain-ai/react-agent) | [Repo](https://github.com/langchain-ai/react-agent-js) |
| **Memory Agent** | A ReAct-style agent with an additional tool to store memories for use across threads. | [Repo](https://github.com/langchain-ai/memory-agent) | [Repo](https://github.com/langchain-ai/memory-agent-js) |
| **Retrieval Agent** | An agent that includes a retrieval-based question-answering system. | [Repo](https://github.com/langchain-ai/retrieval-agent-template) | [Repo](https://github.com/langchain-ai/retrieval-agent-template-js) |
| **Data-Enrichment Agent** | An agent that performs web searches and organizes its findings into a structured format. | [Repo](https://github.com/langchain-ai/data-enrichment) | [Repo](https://github.com/langchain-ai/data-enrichment-js) |

## 🌱 Create a LangGraph App [¶](https://langchain-ai.github.io/langgraph/concepts/template_applications/?q=\#create-a-langgraph-app "Permanent link")

To create a new app from a template, use the `langgraph new` command.

```md-code__content
langgraph new

```

## Next Steps [¶](https://langchain-ai.github.io/langgraph/concepts/template_applications/?q=\#next-steps "Permanent link")

Review the `README.md` file in the root of your new LangGraph app for more information about the template and how to customize it.

After configuring the app properly and adding your API keys, you can start the app using the LangGraph CLI:

```md-code__content
langgraph dev

```

See the following guides for more information on how to deploy your app:

- **[Launch Local LangGraph Server](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/)**: This quick start guide shows how to start a LangGraph Server locally for the **ReAct Agent** template. The steps are similar for other templates.
- **[Deploy to LangGraph Cloud](https://langchain-ai.github.io/langgraph/cloud/quick_start/)**: Deploy your LangGraph app using LangGraph Cloud.

### LangGraph Framework [¶](https://langchain-ai.github.io/langgraph/concepts/template_applications/?q=\#langgraph-framework "Permanent link")

- **[LangGraph Concepts](https://langchain-ai.github.io/langgraph/concepts/)**: Learn the foundational concepts of LangGraph.
- **[LangGraph How-to Guides](https://langchain-ai.github.io/langgraph/how-tos/)**: Guides for common tasks with LangGraph.

### 📚 Learn More about LangGraph Platform [¶](https://langchain-ai.github.io/langgraph/concepts/template_applications/?q=\#learn-more-about-langgraph-platform "Permanent link")

Expand your knowledge with these resources:

- **[LangGraph Platform Concepts](https://langchain-ai.github.io/langgraph/concepts/#langgraph-platform)**: Understand the foundational concepts of the LangGraph Platform.
- **[LangGraph Platform How-to Guides](https://langchain-ai.github.io/langgraph/how-tos/#langgraph-platform)**: Discover step-by-step guides to build and deploy applications.

## Comments

giscus

#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/3752)

#### [1 comment](https://github.com/langchain-ai/langgraph/discussions/3752)

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@arady2](https://avatars.githubusercontent.com/u/191402803?v=4)arady2](https://github.com/arady2) [Mar 8](https://github.com/langchain-ai/langgraph/discussions/3752#discussioncomment-12437171)

I must say I am very impressed and thankful for the great work and direction shown by your platform; I have been looking for this mindset where tech and ai becomes enablers and optimized in this way. All yours if needed to support. All the best!

1

🚀1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Ftemplate_applications%2F%3Fq%3D)