[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/#how-to-add-custom-authentication)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/auth/custom_auth.md "Edit this page")

# How to add custom authentication [¶](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/\#how-to-add-custom-authentication "Permanent link")

Prerequisites

This guide assumes familiarity with the following concepts:

- [**Authentication & Access Control**](https://langchain-ai.github.io/langgraph/concepts/auth/)
- [**LangGraph Platform**](https://langchain-ai.github.io/langgraph/concepts/#langgraph-platform)

For a more guided walkthrough, see [**setting up custom authentication**](https://langchain-ai.github.io/langgraph/tutorials/auth/getting_started/) tutorial.

Support by deployment type

Custom auth is supported for all deployments in the **managed LangGraph Cloud**, as well as **Enterprise** self-hosted plans. It is not supported for **Lite** self-hosted plans.

This guide shows how to add custom authentication to your LangGraph Platform application. This guide applies to both LangGraph Cloud, BYOC, and self-hosted deployments. It does not apply to isolated usage of the LangGraph open source library in your own custom server.

## 1\. Implement authentication [¶](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/\#1-implement-authentication "Permanent link")

```md-code__content
from langgraph_sdk import Auth

my_auth = Auth()

@my_auth.authenticate
async def authenticate(authorization: str) -> str:
    token = authorization.split(" ", 1)[-1] # "Bearer <token>"
    try:
        # Verify token with your auth provider
        user_id = await verify_token(token)
        return user_id
    except Exception:
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Invalid token"
        )

# Add authorization rules to actually control access to resources
@my_auth.on
async def add_owner(
    ctx: Auth.types.AuthContext,
    value: dict,
):
    """Add owner to resource metadata and filter by owner."""
    filters = {"owner": ctx.user.identity}
    metadata = value.setdefault("metadata", {})
    metadata.update(filters)
    return filters

# Assumes you organize information in store like (user_id, resource_type, resource_id)
@my_auth.on.store()
async def authorize_store(ctx: Auth.types.AuthContext, value: dict):
    namespace: tuple = value["namespace"]
    assert namespace[0] == ctx.user.identity, "Not authorized"

```

## 2\. Update configuration [¶](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/\#2-update-configuration "Permanent link")

In your `langgraph.json`, add the path to your auth file:

```md-code__content
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./agent.py:graph"
  },
  "env": ".env",
  "auth": {
    "path": "./auth.py:my_auth"
  }
}

```

## 3\. Connect from the client [¶](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/\#3-connect-from-the-client "Permanent link")

Once you've set up authentication in your server, requests must include the the required authorization information based on your chosen scheme.
Assuming you are using JWT token authentication, you could access your deployments using any of the following methods:

[Python Client](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/#__tabbed_1_1)[Python RemoteGraph](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/#__tabbed_1_2)[JavaScript Client](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/#__tabbed_1_3)[JavaScript RemoteGraph](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/#__tabbed_1_4)[CURL](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/#__tabbed_1_5)

```md-code__content
from langgraph_sdk import get_client

my_token = "your-token" # In practice, you would generate a signed token with your auth provider
client = get_client(
    url="http://localhost:2024",
    headers={"Authorization": f"Bearer {my_token}"}
)
threads = await client.threads.search()

```

```md-code__content
from langgraph.pregel.remote import RemoteGraph

my_token = "your-token" # In practice, you would generate a signed token with your auth provider
remote_graph = RemoteGraph(
    "agent",
    url="http://localhost:2024",
    headers={"Authorization": f"Bearer {my_token}"}
)
threads = await remote_graph.ainvoke(...)

```

```md-code__content
import { Client } from "@langchain/langgraph-sdk";

const my_token = "your-token"; // In practice, you would generate a signed token with your auth provider
const client = new Client({
  apiUrl: "http://localhost:2024",
  headers: { Authorization: `Bearer ${my_token}` },
});
const threads = await client.threads.search();

```

```md-code__content
import { RemoteGraph } from "@langchain/langgraph/remote";

const my_token = "your-token"; // In practice, you would generate a signed token with your auth provider
const remoteGraph = new RemoteGraph({
  graphId: "agent",
  url: "http://localhost:2024",
  headers: { Authorization: `Bearer ${my_token}` },
});
const threads = await remoteGraph.invoke(...);

```

```md-code__content
curl -H "Authorization: Bearer ${your-token}" http://localhost:2024/threads

```

## Comments

giscus

#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/3196)

#### [1 comment](https://github.com/langchain-ai/langgraph/discussions/3196)

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@ARadovski](https://avatars.githubusercontent.com/u/26825950?u=c480c152eddca0532eb6ff16fce2d08e9dc68e63&v=4)ARadovski](https://github.com/ARadovski) [Jan 24](https://github.com/langchain-ai/langgraph/discussions/3196#discussioncomment-11943963)

In part 3 above the connector from JavaScript Client example has an error - with current with @langchain/langgraph-sdk 0.0.36 it should be

const client = new Client({

apiUrl: " [http://localhost:2024](http://localhost:2024/)",

defaultHeaders: { Authorization: `Bearer ${my_token}` },

});

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fauth%2Fcustom_auth%2F)