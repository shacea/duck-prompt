[Skip to content](https://langchain-ai.github.io/langgraph/concepts/langgraph_cloud/#cloud-saas-beta)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/langgraph_cloud.md "Edit this page")

# Cloud SaaS (Beta) [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_cloud/\#cloud-saas-beta "Permanent link")

To deploy a [LangGraph Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/), follow the how-to guide for [how to deploy to Cloud SaaS](https://langchain-ai.github.io/langgraph/cloud/deployment/cloud/).

## Overview [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_cloud/\#overview "Permanent link")

The Cloud SaaS deployment option is a fully managed model for deployment where we manage the [control plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_control_plane/) and [data plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_data_plane/) in our cloud.

|  | [Control Plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_control_plane/) | [Data Plane](https://langchain-ai.github.io/langgraph/concepts/langgraph_data_plane/) |
| --- | --- | --- |
| **What is it?** | - Control Plane UI for creating deployments and revisions<br>- Control Plane APIs for creating deployments and revisions | - Data plane "listener" for reconciling deployments with control plane state<br>- LangGraph Servers<br>- Postgres, Redis, etc |
| **Where is it hosted?** | LangChain's cloud | LangChain's cloud |
| **Who provisions and manages it?** | LangChain | LangChain |

## Architecture [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_cloud/\#architecture "Permanent link")

![Cloud SaaS](https://langchain-ai.github.io/langgraph/concepts/img/self_hosted_control_plane_architecture.png)

## Comments

giscus

#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/2587)

#### [3 comments](https://github.com/langchain-ai/langgraph/discussions/2587)

#### ·

#### 2 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@RVCA212](https://avatars.githubusercontent.com/u/112829052?u=3b98aa2cc36693bbfee9d289b9c07e9de3e12717&v=4)RVCA212](https://github.com/RVCA212) [Jan 17](https://github.com/langchain-ai/langgraph/discussions/2587#discussioncomment-11868842)

Is it possible to turn off langsmith tracing at runtime for projects deployed on Langgraph Cloud?

I tried setting:\`\`\`

os.environ\["LANGCHAIN\_TRACING\_V2"\] = "false"

LANGCHAIN\_TRACING\_V2 = "false"

```notranslate
but the runs are still being traced. I'm wondering if there's any way around this?

```

1

0 replies

[![@ahgoos](https://avatars.githubusercontent.com/u/30512230?u=f91d6b57619018dcca1c5792d33e16705f81f714&v=4)ahgoos](https://github.com/ahgoos) [Jan 18](https://github.com/langchain-ai/langgraph/discussions/2587#discussioncomment-11878071)

Is there a way to configure a custom url for Langgraph Cloud deployments? I scoured Langsmith for a configuration option but couldn't find one, could be a good addition as a field in the langgraph.json conf file

1

1 reply

[![@andrewnguonly](https://avatars.githubusercontent.com/u/7654246?u=b8599019655adaada3cdc3c3006798df42c44494&v=4)](https://github.com/andrewnguonly)

[andrewnguonly](https://github.com/andrewnguonly) [Jan 27](https://github.com/langchain-ai/langgraph/discussions/2587#discussioncomment-11977284)

Contributor

At the moment, LangGraph Cloud SaaS deployments do not support custom URLs.

[![@kihumban](https://avatars.githubusercontent.com/u/3886280?u=be226484faecf404d51ca99675a0da24224e37d0&v=4)kihumban](https://github.com/kihumban) [Feb 17](https://github.com/langchain-ai/langgraph/discussions/2587#discussioncomment-12229735)

I recently got on the Cloud SaaS plan.

However, after deploying my application, I’ve encountered an issue when integrating it with a deployed frontend application. Previously, I hosted the backend API locally using a Docker container, and everything worked (and still works) as expected.

Here’s what I’ve observed:

\-\- I can successfully connect to the backend server via Notebook and CLI.

\-\- The app also functions correctly in LangGraph Studio.

\-\- However, when accessing the application from any browser-based connection—including my local development environment, a Vercel-hosted app, or even the LangGraph Platform API Client—I consistently receive an HTTP 403: "Missing authentication headers" error.

I’ve ensured that the x-api-key header is included and set to the correct API key. I’ve also verified that the API key is valid, as it works without issue in Notebook, CLI, and Studio environments.

Despite researching and posting on several forums, I haven’t been able to resolve this issue. Could you please advise on any additional authentication details or configuration steps required to enable the server to work with a deployed frontend application?

1

👍1

1 reply

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [6 days ago](https://github.com/langchain-ai/langgraph/discussions/2587#discussioncomment-12881051)

Contributor

Hi Kihumban,

Given that you are successfully connecting to it from notebook/cli/studio/curl commands, it seems the server deployment is healthy and that something is happening in your browser app that makes it so this header is not actually sent over.

An additional comment is that langsmith API key auth shouldn't be used from client-side/browser applications since that would expose the private key to the user. You'd want to set up custom auth if you want to directly interface with the backend. ( [https://langchain-ai.github.io/langgraph/tutorials/auth/getting\_started/](https://langchain-ai.github.io/langgraph/tutorials/auth/getting_started/))

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Flanggraph_cloud%2F)