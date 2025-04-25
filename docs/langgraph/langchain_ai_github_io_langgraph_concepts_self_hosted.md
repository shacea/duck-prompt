[Skip to content](https://langchain-ai.github.io/langgraph/concepts/self_hosted/#self-hosted)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/self_hosted.md "Edit this page")

# Self-Hosted [¶](https://langchain-ai.github.io/langgraph/concepts/self_hosted/\#self-hosted "Permanent link")

Note

- [LangGraph Platform](https://langchain-ai.github.io/langgraph/concepts/langgraph_platform/)
- [Deployment Options](https://langchain-ai.github.io/langgraph/concepts/deployment_options/)

## Versions [¶](https://langchain-ai.github.io/langgraph/concepts/self_hosted/\#versions "Permanent link")

There are two versions of the self-hosted deployment: [Self-Hosted Data Plane](https://langchain-ai.github.io/langgraph/concepts/deployment_options/#self-hosted-data-plane) and [Self-Hosted Control Plane](https://langchain-ai.github.io/langgraph/concepts/deployment_options/#self-hosted-control-plane).

### Self-Hosted Data Plane [¶](https://langchain-ai.github.io/langgraph/concepts/self_hosted/\#self-hosted-data-plane "Permanent link")

The [Self-Hosted Data Plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_self_hosted_data_plane/) deployment option is a "hybrid" model for deployment where we manage the [control plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_control_plane/) in our cloud and you manage the [data plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_data_plane/) in your cloud. This option provides a way to securely manage your data plane infrastructure, while offloading control plane management to us.

When using the Self-Hosted Data Plane version, you authenticate with a [LangSmith](https://smith.langchain.com/) API key.

### Self-Hosted Control Plane [¶](https://langchain-ai.github.io/langgraph/concepts/self_hosted/\#self-hosted-control-plane "Permanent link")

The [Self-Hosted Control Plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_self_hosted_control_plane/) deployment option is a fully self-hosted model for deployment where you manage the [control plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_control_plane/) and [data plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_data_plane/) in your cloud. This option give you full control and responsibility of the control plane and data plane infrastructure.

## Requirements [¶](https://langchain-ai.github.io/langgraph/concepts/self_hosted/\#requirements "Permanent link")

- You use `langgraph-cli` and/or [LangGraph Studio](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/) app to test graph locally.
- You use `langgraph build` command to build image.

## How it works [¶](https://langchain-ai.github.io/langgraph/concepts/self_hosted/\#how-it-works "Permanent link")

- Deploy Redis and Postgres instances on your own infrastructure.
- Build the docker image for [LangGraph Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/) using the [LangGraph CLI](https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/).
- Deploy a web server that will run the docker image and pass in the necessary environment variables.

Note

The LangGraph Platform Deployments view is optionally available for Self-Hosted LangGraph deployments. With one click, self-hosted LangGraph deployments can be deployed in the same Kubernetes cluster where a self-hosted LangSmith instance is deployed.

For step-by-step instructions, see [How to set up a self-hosted deployment of LangGraph](https://langchain-ai.github.io/langgraph/how-tos/deploy-self-hosted/).

## Helm Chart [¶](https://langchain-ai.github.io/langgraph/concepts/self_hosted/\#helm-chart "Permanent link")

If you would like to deploy LangGraph Cloud on Kubernetes, you can use this [Helm chart](https://github.com/langchain-ai/helm/blob/main/charts/langgraph-cloud/README.md).

## Related [¶](https://langchain-ai.github.io/langgraph/concepts/self_hosted/\#related "Permanent link")

- [How to set up a self-hosted deployment of LangGraph](https://langchain-ai.github.io/langgraph/how-tos/deploy-self-hosted/).

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Fself_hosted%2F)