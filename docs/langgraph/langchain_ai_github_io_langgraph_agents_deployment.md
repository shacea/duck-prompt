[Skip to content](https://langchain-ai.github.io/langgraph/agents/deployment/#deployment)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/agents/deployment.md "Edit this page")

# Deployment [¶](https://langchain-ai.github.io/langgraph/agents/deployment/\#deployment "Permanent link")

To deploy your LangGraph agent, create and configure a LangGraph app. This setup supports both local development and production deployments.

Features:

- 🖥️ Local server for development
- 🧩 Studio Web UI for visual debugging
- ☁️ Cloud and 🔧 self-hosted deployment options
- 📊 LangSmith integration for tracing and observability

Requirements

- ✅ You **must** have a [LangSmith account](https://www.langchain.com/langsmith). You can sign up for **free** and get started with the free tier.

## Create a LangGraph app [¶](https://langchain-ai.github.io/langgraph/agents/deployment/\#create-a-langgraph-app "Permanent link")

```md-code__content
pip install -U "langgraph-cli[inmem]"
langgraph new path/to/your/app --template new-langgraph-project-python

```

This will create an empty LangGraph project. You can modify it by replacing the code in `src/agent/graph.py` with your agent code. For example:

API Reference: [create\_react\_agent](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)

```md-code__content
from langgraph.prebuilt import create_react_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

graph = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    prompt="You are a helpful assistant"
)

```

### Install dependencies [¶](https://langchain-ai.github.io/langgraph/agents/deployment/\#install-dependencies "Permanent link")

In the root of your new LangGraph app, install the dependencies in `edit` mode so your local changes are used by the server:

```md-code__content
pip install -e .

```

### Create an `.env` file [¶](https://langchain-ai.github.io/langgraph/agents/deployment/\#create-an-env-file "Permanent link")

You will find a `.env.example` in the root of your new LangGraph app. Create
a `.env` file in the root of your new LangGraph app and copy the contents of the `.env.example` file into it, filling in the necessary API keys:

```md-code__content
LANGSMITH_API_KEY=lsv2...
ANTHROPIC_API_KEY=sk-

```

## Launch LangGraph server locally [¶](https://langchain-ai.github.io/langgraph/agents/deployment/\#launch-langgraph-server-locally "Permanent link")

```md-code__content
langgraph dev

```

This will start up the LangGraph API server locally. If this runs successfully, you should see something like:

> Ready!
>
> - API: [http://localhost:2024](http://localhost:2024/)
>
> - Docs: [http://localhost:2024/docs](http://localhost:2024/docs)
>
> - LangGraph Studio Web UI: [https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)

See this [tutorial](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/) to learn more about running LangGraph app locally.

## LangGraph Studio Web UI [¶](https://langchain-ai.github.io/langgraph/agents/deployment/\#langgraph-studio-web-ui "Permanent link")

LangGraph Studio Web is a specialized UI that you can connect to LangGraph API server to enable visualization, interaction, and debugging of your application locally. Test your graph in the LangGraph Studio Web UI by visiting the URL provided in the output of the `langgraph dev` command.

> - LangGraph Studio Web UI: [https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)

## Deployment [¶](https://langchain-ai.github.io/langgraph/agents/deployment/\#deployment_1 "Permanent link")

Once your LangGraph app is running locally, you can deploy it using LangGraph Cloud or self-hosted options. Refer to the [deployment options guide](https://langchain-ai.github.io/langgraph/tutorials/deployment/) for detailed instructions on all supported deployment models.

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fagents%2Fdeployment%2F)