[Skip to content](https://langchain-ai.github.io/langgraph/concepts/langgraph_self_hosted_data_plane/?q=#self-hosted-data-plane-beta)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/langgraph_self_hosted_data_plane.md "Edit this page")

# Self-Hosted Data Plane (Beta) [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_self_hosted_data_plane/?q=\#self-hosted-data-plane-beta "Permanent link")

To deploy a [LangGraph Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/), follow the how-to guide for [how to deploy the Self-Hosted Data Plane](https://langchain-ai.github.io/langgraph/cloud/deployment/self_hosted_data_plane/).

## Overview [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_self_hosted_data_plane/?q=\#overview "Permanent link")

LangGraph Platform's Self-Hosted Data Plane deployment option is a "hybrid" model for deployemnt where we manage the [control plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_control_plane/) in our cloud and you manage the [data plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_data_plane/) in your cloud.

|  | [Control Plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_control_plane/) | [Data Plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_data_plane/) |
| --- | --- | --- |
| **What is it?** | - Control Plane UI for creating deployments and revisions<br>- Control Plane APIs for creating deployments and revisions | - Data plane "listener" for reconciling deployments with control plane state<br>- LangGraph Servers<br>- Postgres, Redis, etc |
| **Where is it hosted?** | LangChain's cloud | Your cloud |
| **Who provisions and manages it?** | LangChain | You |

## Architecture [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_self_hosted_data_plane/?q=\#architecture "Permanent link")

![Self-Hosted Data Plane Architecture](https://langchain-ai.github.io/langgraph/concepts/img/self_hosted_data_plane_architecture.png)

## Compute Platforms [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_self_hosted_data_plane/?q=\#compute-platforms "Permanent link")

### Kubernetes [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_self_hosted_data_plane/?q=\#kubernetes "Permanent link")

The Self-Hosted Data Plane deployment option supports deploying data plane infrastructure to any Kubernetes cluster.

### Amazon ECS [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_self_hosted_data_plane/?q=\#amazon-ecs "Permanent link")

Coming soon...

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Flanggraph_self_hosted_data_plane%2F%3Fq%3D)