[Skip to content](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/#langgraph-cli)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/langgraph_cli.md "Edit this page")

# LangGraph CLI [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/\#langgraph-cli "Permanent link")

Prerequisites

- [LangGraph Platform](https://langchain-ai.github.io/langgraph/concepts/langgraph_platform/)
- [LangGraph Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/)

The LangGraph CLI is a multi-platform command-line tool for building and running the [LangGraph API server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/) locally. The resulting server includes all API endpoints for your graph's runs, threads, assistants, etc. as well as the other services required to run your agent, including a managed database for checkpointing and storage.

## Installation [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/\#installation "Permanent link")

The LangGraph CLI can be installed via Homebrew (on macOS) or pip:

[Homebrew](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/#__tabbed_1_1)[pip](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/#__tabbed_1_2)

```md-code__content
brew install langgraph-cli

```

```md-code__content
pip install langgraph-cli

```

## Commands [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/\#commands "Permanent link")

The CLI provides the following core functionality:

### `build` [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/\#build "Permanent link")

The `langgraph build` command builds a Docker image for the [LangGraph API server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/) that can be directly deployed.

### `dev` [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/\#dev "Permanent link")

New in version 0.1.55

The `langgraph dev` command was introduced in langgraph-cli version 0.1.55.

Python only

Currently, the CLI only supports Python >= 3.11.
JS support is coming soon.

The `langgraph dev` command starts a lightweight development server that requires no Docker installation. This server is ideal for rapid development and testing, with features like:

- Hot reloading: Changes to your code are automatically detected and reloaded
- Debugger support: Attach your IDE's debugger for line-by-line debugging
- In-memory state with local persistence: Server state is stored in memory for speed but persisted locally between restarts

To use this command, you need to install the CLI with the "inmem" extra:

```md-code__content
pip install -U "langgraph-cli[inmem]"

```

**Note**: This command is intended for local development and testing only. It is not recommended for production use. Since it does not use Docker, we recommend using virtual environments to manage your project's dependencies.

### `up` [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/\#up "Permanent link")

The `langgraph up` command starts an instance of the [LangGraph API server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/) locally in a docker container. This requires the docker server to be running locally. It also requires a LangSmith API key for local development or a license key for production use.

The server includes all API endpoints for your graph's runs, threads, assistants, etc. as well as the other services required to run your agent, including a managed database for checkpointing and storage.

### `dockerfile` [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/\#dockerfile "Permanent link")

The `langgraph dockerfile` command generates a [Dockerfile](https://docs.docker.com/reference/dockerfile/) that can be used to build images for and deploy instances of the [LangGraph API server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/). This is useful if you want to further customize the dockerfile or deploy in a more custom way.

Updating your langgraph.json file

The `langgraph dockerfile` command translates all the configuration in your `langgraph.json` file into Dockerfile commands. When using this command, you will have to re-run it whenever you update your `langgraph.json` file. Otherwise, your changes will not be reflected when you build or run the dockerfile.

## Related [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/\#related "Permanent link")

- [LangGraph CLI API Reference](https://langchain-ai.github.io/langgraph/cloud/reference/cli/)

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Flanggraph_cli%2F)