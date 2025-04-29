[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/auth/openapi_security/#how-to-document-api-authentication-in-openapi)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/auth/openapi_security.md "Edit this page")

# How to document API authentication in OpenAPI [¶](https://langchain-ai.github.io/langgraph/how-tos/auth/openapi_security/\#how-to-document-api-authentication-in-openapi "Permanent link")

This guide shows how to customize the OpenAPI security schema for your LangGraph Platform API documentation. A well-documented security schema helps API consumers understand how to authenticate with your API and even enables automatic client generation. See the [Authentication & Access Control conceptual guide](https://langchain-ai.github.io/langgraph/concepts/auth/) for more details about LangGraph's authentication system.

Implementation vs Documentation

This guide only covers how to document your security requirements in OpenAPI. To implement the actual authentication logic, see [How to add custom authentication](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/).

This guide applies to all LangGraph Platform deployments (Cloud, BYOC, and self-hosted). It does not apply to usage of the LangGraph open source library if you are not using LangGraph Platform.

## Default Schema [¶](https://langchain-ai.github.io/langgraph/how-tos/auth/openapi_security/\#default-schema "Permanent link")

The default security scheme varies by deployment type:

[LangGraph Cloud](https://langchain-ai.github.io/langgraph/how-tos/auth/openapi_security/#__tabbed_1_1)

By default, LangGraph Cloud requires a LangSmith API key in the `x-api-key` header:

```md-code__content
components:
  securitySchemes:
    apiKeyAuth:
      type: apiKey
      in: header
      name: x-api-key
security:
  - apiKeyAuth: []

```

When using one of the LangGraph SDK's, this can be inferred from environment variables.

[Self-hosted](https://langchain-ai.github.io/langgraph/how-tos/auth/openapi_security/#__tabbed_2_1)

By default, self-hosted deployments have no security scheme. This means they are to be deployed only on a secured network or with authentication. To add custom authentication, see [How to add custom authentication](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/).

## Custom Security Schema [¶](https://langchain-ai.github.io/langgraph/how-tos/auth/openapi_security/\#custom-security-schema "Permanent link")

To customize the security schema in your OpenAPI documentation, add an `openapi` field to your `auth` configuration in `langgraph.json`. Remember that this only updates the API documentation - you must also implement the corresponding authentication logic as shown in [How to add custom authentication](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/).

Note that LangGraph Platform does not provide authentication endpoints - you'll need to handle user authentication in your client application and pass the resulting credentials to the LangGraph API.

[OAuth2 with Bearer Token](https://langchain-ai.github.io/langgraph/how-tos/auth/openapi_security/#__tabbed_3_1)[API Key](https://langchain-ai.github.io/langgraph/how-tos/auth/openapi_security/#__tabbed_3_2)

```md-code__content
{
  "auth": {
    "path": "./auth.py:my_auth",  // Implement auth logic here
    "openapi": {
      "securitySchemes": {
        "OAuth2": {
          "type": "oauth2",
          "flows": {
            "implicit": {
              "authorizationUrl": "https://your-auth-server.com/oauth/authorize",
              "scopes": {
                "me": "Read information about the current user",
                "threads": "Access to create and manage threads"
              }
            }
          }
        }
      },
      "security": [\
        {"OAuth2": ["me", "threads"]}\
      ]
    }
  }
}

```

```md-code__content
{
  "auth": {
    "path": "./auth.py:my_auth",  // Implement auth logic here
    "openapi": {
      "securitySchemes": {
        "apiKeyAuth": {
          "type": "apiKey",
          "in": "header",
          "name": "X-API-Key"
        }
      },
      "security": [\
        {"apiKeyAuth": []}\
      ]
    }
  }
}

```

## Testing [¶](https://langchain-ai.github.io/langgraph/how-tos/auth/openapi_security/\#testing "Permanent link")

After updating your configuration:

1. Deploy your application
2. Visit `/docs` to see the updated OpenAPI documentation
3. Try out the endpoints using credentials from your authentication server (make sure you've implemented the authentication logic first)

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fauth%2Fopenapi_security%2F)