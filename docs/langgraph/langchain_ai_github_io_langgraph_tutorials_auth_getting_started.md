[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/auth/getting_started/#setting-up-custom-authentication-part-13)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/auth/getting_started.md "Edit this page")

# Setting up Custom Authentication (Part ⅓) [¶](https://langchain-ai.github.io/langgraph/tutorials/auth/getting_started/\#setting-up-custom-authentication-part-13 "Permanent link")

This is part 1 of our authentication series:

1. Basic Authentication (you are here) - Control who can access your bot
2. [Resource Authorization](https://langchain-ai.github.io/langgraph/tutorials/auth/resource_auth/) \- Let users have private conversations
3. [Production Auth](https://langchain-ai.github.io/langgraph/tutorials/auth/add_auth_server/) \- Add real user accounts and validate using OAuth2

Prerequisites

This guide assumes basic familiarity with the following concepts:

- [**Authentication & Access Control**](https://langchain-ai.github.io/langgraph/concepts/auth/)
- [**LangGraph Platform**](https://langchain-ai.github.io/langgraph/concepts/#langgraph-platform)

Python only

We currently only support custom authentication and authorization in Python deployments with `langgraph-api>=0.0.11`. Support for LangGraph.JS will be added soon.

Support by deployment type

Custom auth is supported for all deployments in the **managed LangGraph Cloud**, as well as **Enterprise** self-hosted plans. It is not supported for **Lite** self-hosted plans.

In this tutorial, we will build a chatbot that only lets specific users access it. We'll start with the LangGraph template and add token-based security step by step. By the end, you'll have a working chatbot that checks for valid tokens before allowing access.

## Setting up our project [¶](https://langchain-ai.github.io/langgraph/tutorials/auth/getting_started/\#setting-up-our-project "Permanent link")

First, let's create a new chatbot using the LangGraph starter template:

```md-code__content
pip install -U "langgraph-cli[inmem]"
langgraph new --template=new-langgraph-project-python custom-auth
cd custom-auth

```

The template gives us a placeholder LangGraph app. Let's try it out by installing the local dependencies and running the development server.

```md-code__content
pip install -e .
langgraph dev

```

If everything works, the server should start and open the studio in your browser.

> - 🚀 API: [http://127.0.0.1:2024](http://127.0.0.1:2024/)
> - 🎨 Studio UI: [https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)
> - 📚 API Docs: [http://127.0.0.1:2024/docs](http://127.0.0.1:2024/docs)
>
> This in-memory server is designed for development and testing.
> For production use, please use LangGraph Cloud.

The graph should run, and if you were to self-host this on the public internet, anyone could access it!

![No auth](https://langchain-ai.github.io/langgraph/tutorials/auth/img/no_auth.png)

Now that we've seen the base LangGraph app, let's add authentication to it!

Placeholder token

In part 1, we will start with a hard-coded token for illustration purposes.
We will get to a "production-ready" authentication scheme in part 3, after mastering the basics.

## Adding Authentication [¶](https://langchain-ai.github.io/langgraph/tutorials/auth/getting_started/\#adding-authentication "Permanent link")

The [`Auth`](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/#langgraph_sdk.auth.Auth) object lets you register an authentication function that the LangGraph platform will run on every request. This function receives each request and decides whether to accept or reject.

Create a new file `src/security/auth.py`. This is where our code will live to check if users are allowed to access our bot:

src/security/auth.py

```md-code__content
from langgraph_sdk import Auth

# This is our toy user database. Do not do this in production
VALID_TOKENS = {
    "user1-token": {"id": "user1", "name": "Alice"},
    "user2-token": {"id": "user2", "name": "Bob"},
}

# The "Auth" object is a container that LangGraph will use to mark our authentication function
auth = Auth()

# The `authenticate` decorator tells LangGraph to call this function as middleware
# for every request. This will determine whether the request is allowed or not
@auth.authenticate
async def get_current_user(authorization: str | None) -> Auth.types.MinimalUserDict:
    """Check if the user's token is valid."""
    assert authorization
    scheme, token = authorization.split()
    assert scheme.lower() == "bearer"
    # Check if token is valid
    if token not in VALID_TOKENS:
        raise Auth.exceptions.HTTPException(status_code=401, detail="Invalid token")

    # Return user info if valid
    user_data = VALID_TOKENS[token]
    return {
        "identity": user_data["id"],
    }

```

Notice that our [authentication](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/#langgraph_sdk.auth.Auth.authenticate) handler does two important things:

1. Checks if a valid token is provided in the request's [Authorization header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Authorization)
2. Returns the user's [identity](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/#langgraph_sdk.auth.types.MinimalUserDict)

Now tell LangGraph to use our authentication by adding the following to the [`langgraph.json`](https://langchain-ai.github.io/langgraph/cloud/reference/cli/#configuration-file) configuration:

langgraph.json

```md-code__content
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/agent/graph.py:graph"
  },
  "env": ".env",
  "auth": {
    "path": "src/security/auth.py:auth"
  }
}

```

## Testing Our "Secure" Bot [¶](https://langchain-ai.github.io/langgraph/tutorials/auth/getting_started/\#testing-our-secure-bot "Permanent link")

Let's start the server again to test everything out!

```md-code__content
langgraph dev --no-browser

```

Custom auth in the studio

If you didn't add the `--no-browser`, the studio UI will open in the browser. You may wonder, how is the studio able to still connect to our server? By default, we also permit access from the LangGraph studio, even when using custom auth. This makes it easier to develop and test your bot in the studio. You can remove this alternative authentication option by
setting `disable_studio_auth: "true"` in your auth configuration:

```md-code__content
{
    "auth": {
        "path": "src/security/auth.py:auth",
        "disable_studio_auth": "true"
    }
}

```

Now let's try to chat with our bot. If we've implemented authentication correctly, we should only be able to access the bot if we provide a valid token in the request header. Users will still, however, be able to access each other's resources until we add [resource authorization handlers](https://langchain-ai.github.io/langgraph/concepts/auth/#resource-specific-handlers) in the next section of our tutorial.

![Authentication, no authorization handlers](https://langchain-ai.github.io/langgraph/tutorials/auth/img/authentication.png)

Run the following code in a file or notebook:

```md-code__content
from langgraph_sdk import get_client

# Try without a token (should fail)
client = get_client(url="http://localhost:2024")
try:
    thread = await client.threads.create()
    print("❌ Should have failed without token!")
except Exception as e:
    print("✅ Correctly blocked access:", e)

# Try with a valid token
client = get_client(
    url="http://localhost:2024", headers={"Authorization": "Bearer user1-token"}
)

# Create a thread and chat
thread = await client.threads.create()
print(f"✅ Created thread as Alice: {thread['thread_id']}")

response = await client.runs.create(
    thread_id=thread["thread_id"],
    assistant_id="agent",
    input={"messages": [{"role": "user", "content": "Hello!"}]},
)
print("✅ Bot responded:")
print(response)

```

You should see that:

1. Without a valid token, we can't access the bot
2. With a valid token, we can create threads and chat

Congratulations! You've built a chatbot that only lets "authenticated" users access it. While this system doesn't (yet) implement a production-ready security scheme, we've learned the basic mechanics of how to control access to our bot. In the next tutorial, we'll learn how to give each user their own private conversations.

## What's Next? [¶](https://langchain-ai.github.io/langgraph/tutorials/auth/getting_started/\#whats-next "Permanent link")

Now that you can control who accesses your bot, you might want to:

1. Continue the tutorial by going to [Making Conversations Private (Part ⅔)](https://langchain-ai.github.io/langgraph/tutorials/auth/resource_auth/) to learn about resource authorization.
2. Read more about [authentication concepts](https://langchain-ai.github.io/langgraph/concepts/auth/).
3. Check out the [API reference](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/) for more authentication details.

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Fauth%2Fgetting_started%2F)