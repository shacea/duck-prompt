[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/#quickstart-launch-local-langgraph-server)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/langgraph-platform/local-server.md "Edit this page")

# Quickstart: Launch Local LangGraph Server [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#quickstart-launch-local-langgraph-server "Permanent link")

This is a quick start guide to help you get a LangGraph app up and running locally.

Requirements

- Python >= 3.11
- [LangGraph CLI](https://langchain-ai.github.io/langgraph/cloud/reference/cli/): Requires langchain-cli\[inmem\] >= 0.1.58

## Install the LangGraph CLI [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#install-the-langgraph-cli "Permanent link")

```md-code__content
pip install --upgrade "langgraph-cli[inmem]"

```

## 🌱 Create a LangGraph App [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#create-a-langgraph-app "Permanent link")

Create a new app from the `react-agent` template. This template is a simple agent that can be flexibly extended to many tools.

[Python Server](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/#__tabbed_1_1)[Node Server](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/#__tabbed_1_2)

```md-code__content
langgraph new path/to/your/app --template react-agent-python

```

```md-code__content
langgraph new path/to/your/app --template react-agent-js

```

Additional Templates

If you use `langgraph new` without specifying a template, you will be presented with an interactive menu that will allow you to choose from a list of available templates.

## Install Dependencies [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#install-dependencies "Permanent link")

In the root of your new LangGraph app, install the dependencies in `edit` mode so your local changes are used by the server:

```md-code__content
pip install -e .

```

## Create a `.env` file [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#create-a-env-file "Permanent link")

You will find a `.env.example` in the root of your new LangGraph app. Create
a `.env` file in the root of your new LangGraph app and copy the contents of the `.env.example` file into it, filling in the necessary API keys:

```md-code__content
LANGSMITH_API_KEY=lsv2...
TAVILY_API_KEY=tvly-...
ANTHROPIC_API_KEY=sk-
OPENAI_API_KEY=sk-...

```

Get API Keys

- **LANGSMITH\_API\_KEY**: Go to the [LangSmith Settings page](https://smith.langchain.com/settings). Then clck **Create API Key**.
- **ANTHROPIC\_API\_KEY**: Get an API key from [Anthropic](https://console.anthropic.com/).
- **OPENAI\_API\_KEY**: Get an API key from [OpenAI](https://openai.com/).
- **TAVILY\_API\_KEY**: Get an API key on the [Tavily website](https://app.tavily.com/).

## 🚀 Launch LangGraph Server [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#launch-langgraph-server "Permanent link")

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

In-Memory Mode

The `langgraph dev` command starts LangGraph Server in an in-memory mode. This mode is suitable for development and testing purposes. For production use, you should deploy LangGraph Server with access to a persistent storage backend.

If you want to test your application with a persistent storage backend, you can use the `langgraph up` command instead of `langgraph dev`. You will
need to have `docker` installed on your machine to use this command.

## LangGraph Studio Web UI [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#langgraph-studio-web-ui "Permanent link")

LangGraph Studio Web is a specialized UI that you can connect to LangGraph API server to enable visualization, interaction, and debugging of your application locally. Test your graph in the LangGraph Studio Web UI by visiting the URL provided in the output of the `langgraph dev` command.

> - LangGraph Studio Web UI: [https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)

Connecting to a server with a custom host/port

If you are running the LangGraph API server with a custom host / port, you can point the Studio Web UI at it by changing the `baseUrl` URL param. For example, if you are running your server on port 8000, you can change the above URL to the following:

```md-code__content
https://smith.langchain.com/studio/baseUrl=http://127.0.0.1:8000

```

Safari Compatibility

Currently, LangGraph Studio Web does not support Safari when running a server locally.

## Test the API [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#test-the-api "Permanent link")

[Python SDK (Async)](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/#__tabbed_2_1)[Python SDK (Sync)](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/#__tabbed_2_2)[Javascript SDK](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/#__tabbed_2_3)[Rest API](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/#__tabbed_2_4)

**Install the LangGraph Python SDK**

```md-code__content
pip install langgraph-sdk

```

**Send a message to the assistant (threadless run)**

```md-code__content
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")

async for chunk in client.runs.stream(
    None,  # Threadless run
    "agent", # Name of assistant. Defined in langgraph.json.
    input={
        "messages": [{\
            "role": "human",\
            "content": "What is LangGraph?",\
        }],
    },
    stream_mode="updates",
):
    print(f"Receiving new event of type: {chunk.event}...")
    print(chunk.data)
    print("\n\n")

```

**Install the LangGraph Python SDK**

```md-code__content
pip install langgraph-sdk

```

**Send a message to the assistant (threadless run)**

```md-code__content
from langgraph_sdk import get_sync_client

client = get_sync_client(url="http://localhost:2024")

for chunk in client.runs.stream(
    None,  # Threadless run
    "agent", # Name of assistant. Defined in langgraph.json.
    input={
        "messages": [{\
            "role": "human",\
            "content": "What is LangGraph?",\
        }],
    },
    stream_mode="updates",
):
    print(f"Receiving new event of type: {chunk.event}...")
    print(chunk.data)
    print("\n\n")

```

**Install the LangGraph JS SDK**

```md-code__content
npm install @langchain/langgraph-sdk

```

**Send a message to the assistant (threadless run)**

```md-code__content
const { Client } = await import("@langchain/langgraph-sdk");

// only set the apiUrl if you changed the default port when calling langgraph dev
const client = new Client({ apiUrl: "http://localhost:2024"});

const streamResponse = client.runs.stream(
    null, // Threadless run
    "agent", // Assistant ID
    {
        input: {
            "messages": [\
                { "role": "user", "content": "What is LangGraph?"}\
            ]
        },
        streamMode: "messages",
    }
);

for await (const chunk of streamResponse) {
    console.log(`Receiving new event of type: ${chunk.event}...`);
    console.log(JSON.stringify(chunk.data));
    console.log("\n\n");
}

```

```md-code__content
curl -s --request POST \
    --url "http://localhost:2024/runs/stream" \
    --header 'Content-Type: application/json' \
    --data "{
        \"assistant_id\": \"agent\",
        \"input\": {
            \"messages\": [\
                {\
                    \"role\": \"human\",\
                    \"content\": \"What is LangGraph?\"\
                }\
            ]
        },
        \"stream_mode\": \"updates\"
    }"

```

Auth

If you're connecting to a remote server, you will need to provide a LangSmith
API Key for authorization. Please see the API Reference for the clients
for more information.

## Next Steps [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#next-steps "Permanent link")

Now that you have a LangGraph app running locally, take your journey further by exploring deployment and advanced features:

### 🌐 Deploy to LangGraph Cloud [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#deploy-to-langgraph-cloud "Permanent link")

- **[LangGraph Cloud Quickstart](https://langchain-ai.github.io/langgraph/cloud/quick_start/)**: Deploy your LangGraph app using LangGraph Cloud.

### 📚 Learn More about LangGraph Platform [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#learn-more-about-langgraph-platform "Permanent link")

Expand your knowledge with these resources:

- **[LangGraph Platform Concepts](https://langchain-ai.github.io/langgraph/concepts/#langgraph-platform)**: Understand the foundational concepts of the LangGraph Platform.
- **[LangGraph Platform How-to Guides](https://langchain-ai.github.io/langgraph/how-tos/#langgraph-platform)**: Discover step-by-step guides to build and deploy applications.

### 🛠️ Developer References [¶](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/\#developer-references "Permanent link")

Access detailed documentation for development and API usage:

- **[LangGraph Server API Reference](https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref.html)**: Explore the LangGraph Server API documentation.
- **[Python SDK Reference](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/)**: Explore the Python SDK API Reference.
- **[JS/TS SDK Reference](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/js_ts_sdk_ref/)**: Explore the JS/TS SDK API Reference.

## Comments

giscus

#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/2527)

👍1

#### [21 comments](https://github.com/langchain-ai/langgraph/discussions/2527)

#### ·

#### 21 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@wm987](https://avatars.githubusercontent.com/u/6326065?u=7a9dedcab823e78fabebe0178fd48549718ec969&v=4)wm987](https://github.com/wm987) [Nov 25, 2024](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11368719)

I tried setting it up using the `agent` template by following the instructions here, but when I tried running `langgraph dev`, I got this error:

```notranslate
$ langgraph dev
INFO:langgraph_api.cli:

        Welcome to

╦  ┌─┐┌┐┌┌─┐╔═╗┬─┐┌─┐┌─┐┬ ┬
║  ├─┤││││ ┬║ ╦├┬┘├─┤├─┘├─┤
╩═╝┴ ┴┘└┘└─┘╚═╝┴└─┴ ┴┴  ┴ ┴

- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs

This in-memory server is designed for development and testing.
For production use, please use LangGraph Cloud.

2024-11-25T06:33:11.602737Z [info     ] Will watch for changes in these directories: ['C:\\Users\\William\\Documents\\GitHub\\ArchiLabs-AI-MonoRepo\\langgraph'] [uvicorn.error] api_variant=test
2024-11-25T06:33:11.603738Z [info     ] Uvicorn running on http://127.0.0.1:2024 (Press CTRL+C to quit) [uvicorn.error] api_variant=test color_message=Uvicorn running on %s://%s:%d (Press CTRL+C to quit)
2024-11-25T06:33:11.603738Z [info     ] Started reloader process [120400] using WatchFiles [uvicorn.error] api_variant=test color_message=Started reloader process [120400] using WatchFiles
2024-11-25T06:33:12.579357Z [info     ] Started server process [110076] [uvicorn.error] api_variant=test color_message=Started server process [%d]
2024-11-25T06:33:12.579357Z [info     ] Waiting for application startup. [uvicorn.error] api_variant=test
2024-11-25T06:33:12.663118Z [error    ] Traceback (most recent call last):
  File "C:\Python311\Lib\site-packages\starlette\routing.py", line 693, in lifespan
    async with self.lifespan_context(app) as maybe_state:
  File "C:\Python311\Lib\contextlib.py", line 204, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\site-packages\langgraph_api\lifespan.py", line 30, in lifespan
    await collect_graphs_from_env(True)
  File "C:\Python311\Lib\site-packages\langgraph_api\graph.py", line 230, in collect_graphs_from_env
    graph = await run_in_executor(None, _graph_from_spec, spec)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\site-packages\langchain_core\runnables\config.py", line 588, in run_in_executor
    return await asyncio.get_running_loop().run_in_executor(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\concurrent\futures\thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\site-packages\langchain_core\runnables\config.py", line 579, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\site-packages\langgraph_api\graph.py", line 271, in _graph_from_spec
    raise e
  File "C:\Python311\Lib\site-packages\langgraph_api\graph.py", line 268, in _graph_from_spec
    modspec.loader.exec_module(module)
  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "C:\Users\William\Documents\GitHub\ArchiLabs-AI-MonoRepo\langgraph\./src/agent/graph.py", line 11, in <module>
    from agent.configuration import Configuration
ModuleNotFoundError: No module named 'agent'
Could not import python module for graph: GraphSpec(id='agent', path='./src/agent/graph.py', module=None, variable='graph', config=None)
 [uvicorn.error] api_variant=test
2024-11-25T06:33:12.665766Z [error    ] Application startup failed. Exiting. [uvicorn.error] api_variant=test

```

Any idea why it's failing to find the module?

1

❤️1👀1

3 replies

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Nov 25, 2024](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11368727)

Contributor

Did you install the current module?

```notranslate
pip install .

```

[![@ujitkumar1](https://avatars.githubusercontent.com/u/110418072?u=3f391132df96928b81f8f45332ee4f529afd4d00&v=4)](https://github.com/ujitkumar1)

[ujitkumar1](https://github.com/ujitkumar1) [Jan 10](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11796019)

This issue might be caused by an incorrect Python path or because the required module has not been installed.

To set the Python path:

Run: `export PYTHONPATH=.` in the project's root directory.

To install the module:

Run: `pip install ."`

Also check if you are in the right path in the terminal

[![@viren-vii](https://avatars.githubusercontent.com/u/56278281?v=4)](https://github.com/viren-vii)

[viren-vii](https://github.com/viren-vii) [Jan 19](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11878879)

Contributor

I am getting same error even after installing the dependencies. It says

ModuleNotFoundError: No module named 'react\_agent'

[![@jakehemmerle](https://avatars.githubusercontent.com/u/8061957?u=66fbb605258b71526a9697f74c7dc8392155505b&v=4)jakehemmerle](https://github.com/jakehemmerle) [Nov 28, 2024](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11402280)

I'm having a situation where `langgraph dev` just hangs. It was working earlier today. I added a .env tried wiping the venv, reinstalling CLI, trying new templates, no luck. Using uv with project-independant venvs.

```notranslate
~/codebases/infra/asdf main* ❯ langgraph dev                                                         asdf
INFO:langgraph_api.cli:

        Welcome to

╦  ┌─┐┌┐┌┌─┐╔═╗┬─┐┌─┐┌─┐┬ ┬
║  ├─┤││││ ┬║ ╦├┬┘├─┤├─┘├─┤
╩═╝┴ ┴┘└┘└─┘╚═╝┴└─┴ ┴┴  ┴ ┴

- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs

This in-memory server is designed for development and testing.
For production use, please use LangGraph Cloud.

```

1

👀1

2 replies

[![@prasanjeevi](https://avatars.githubusercontent.com/u/12180381?u=228e0d37ec0f4e245503beb77d1ad1dc9de3eeee&v=4)](https://github.com/prasanjeevi)

[prasanjeevi](https://github.com/prasanjeevi) [Nov 28, 2024](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11402570)

Faced the same issue downgrading from langgraph-checkpoint==2.0.7 to langgraph-checkpoint==2.0.6 works for me

👀1

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Nov 28, 2024](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11403426)

Contributor

Do you still see the locking if you use `--no-browser`?

[![@jwj1342](https://avatars.githubusercontent.com/u/53201338?u=d5757178cbdc256b76117b7d0b4d3e5fca2034c9&v=4)jwj1342](https://github.com/jwj1342) [Dec 14, 2024](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11564602)

When using `langgraph dev`, I encountered the following error:

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "D:\ANACONDA\envs\LangSmith\Scripts\langgraph.exe\__main__.py", line 7, in <module>
  File "D:\ANACONDA\envs\LangSmith\Lib\site-packages\click\core.py", line 1157, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\ANACONDA\envs\LangSmith\Lib\site-packages\click\core.py", line 1078, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "D:\ANACONDA\envs\LangSmith\Lib\site-packages\click\core.py", line 1688, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\ANACONDA\envs\LangSmith\Lib\site-packages\click\core.py", line 1434, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\ANACONDA\envs\LangSmith\Lib\site-packages\click\core.py", line 783, in invoke
    return __callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\ANACONDA\envs\LangSmith\Lib\site-packages\langgraph_cli\analytics.py", line 96, in decorator
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "D:\ANACONDA\envs\LangSmith\Lib\site-packages\langgraph_cli\cli.py", line 608, in dev
    run_server(
  File "D:\ANACONDA\envs\LangSmith\Lib\site-packages\langgraph_api\cli.py", line 221, in run_server
    uvicorn.run(
TypeError: run() got an unexpected keyword argument 'auth'
```

This error occurs because the `uvicorn.run()` function does not accept an `auth` argument.

**Solution:**

To resolve this issue, modify the `run_server` function in the `cli.py` file by removing the ` **kwargs` argument from the `uvicorn.run()` call. After making this change, the program should function correctly.

1

1 reply

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Dec 14, 2024](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11567624)

Contributor

Hi [@jwj1342](https://github.com/jwj1342) could you upgrade to `0.1.63`? Apologies for the broken release!

[![@ATAKing1023](https://avatars.githubusercontent.com/u/26701496?u=a0bd6dd25995e1208290d56b9d95eaeb2e0abfc6&v=4)ATAKing1023](https://github.com/ATAKing1023) [Dec 25, 2024](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11662749)

Requirements:

LangGraph CLI: Requires langchain-cli\[inmem\] >= 0.1.58

but the latest version of langchain-cli in PyPI is 0.0.35.

1

0 replies

[![@Kashyab19](https://avatars.githubusercontent.com/u/22251972?u=8bd00abd6d81a6f40878e012af7b5daff8d5e039&v=4)Kashyab19](https://github.com/Kashyab19) [Jan 3](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11722373)

Hi, I followed all the steps mentioned in the documentation

Ran this step after creating an env file with contents:

`langgraph dev`

My Langgraph server is running but it does not show any of the threads in the file. Error:

> Failed to load assistants
>
> Please verify if the API server is running or accessible from the browser.
>
> TypeError: Failed to fetch

Am I missing something?

1

👍4

4 replies

[![@aileen5150](https://avatars.githubusercontent.com/u/7599711?v=4)](https://github.com/aileen5150)

[aileen5150](https://github.com/aileen5150) [Jan 3](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11723305)

I encountered a similar issue. Using the F12 developer tools, I observed that an HTTP request was made to my local service at http://{ip}:{port}/assistants/search, but a cross-origin resource sharing (CORS) error occurred. However, when testing the /assistants/search endpoint via http://{ip}:{port}/docs, the call succeeded. The only deviation from the official tutorial is that, instead of using localhost, I am using the server's IP address.

I resolved the issue by implementing a local proxy.

[![@BobMerkus](https://avatars.githubusercontent.com/u/23738320?u=5193798d57e7e887fb121101272718f4f120f56c&v=4)](https://github.com/BobMerkus)

[BobMerkus](https://github.com/BobMerkus) [Jan 23](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11929295)

In my case it was Brave browser blocking the requests; see [https://stackoverflow.com/a/73248929](https://stackoverflow.com/a/73248929)

❤️2

[![@m2f0](https://avatars.githubusercontent.com/u/2529850?u=aedb57694c1f4f8c7398a4ba6aa741cef3bb34cd&v=4)](https://github.com/m2f0)

[m2f0](https://github.com/m2f0) [Feb 2](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12031707)

Thanks [@BobMerkus](https://github.com/BobMerkus). I was in the same issue. Brave browser block cookies comunications.

[![@alibabadoufu](https://avatars.githubusercontent.com/u/47876361?u=2441a7c55155f813fc206afe0c8c0a6aa98e2ca5&v=4)](https://github.com/alibabadoufu)

[alibabadoufu](https://github.com/alibabadoufu) [Mar 17](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12523343)

> In my case it was Brave browser blocking the requests; see [https://stackoverflow.com/a/73248929](https://stackoverflow.com/a/73248929)

This one worked for me!

[![@martinobettucci](https://avatars.githubusercontent.com/u/19490374?u=5ae0113e9348bf2bc0851c804bc4b3ddbf84c1c4&v=4)martinobettucci](https://github.com/martinobettucci) [Jan 9](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11789454)

Mixed Content: The page at ' [https://smith.langchain.com/studio/thread?baseUrl=http%3A%2F%2F0.0.0.0%3A2024](https://smith.langchain.com/studio/thread?baseUrl=http%3A%2F%2F0.0.0.0%3A2024)' was loaded over HTTPS, but requested an insecure resource ' [http://0.0.0.0:2024/assistants/search](http://0.0.0.0:2024/assistants/search)'. This request has been blocked; the content must be served over HTTPS.

It is impossible to load a local resource from a an https resource which is also on another domain. This can't work

2

👍1

2 replies

[![@eyurtsev](https://avatars.githubusercontent.com/u/3205522?v=4)](https://github.com/eyurtsev)

[eyurtsev](https://github.com/eyurtsev) [Jan 20](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11885692)

Collaborator

Which web-browser are you using?

[![@martinobettucci](https://avatars.githubusercontent.com/u/19490374?u=5ae0113e9348bf2bc0851c804bc4b3ddbf84c1c4&v=4)](https://github.com/martinobettucci)

[martinobettucci](https://github.com/martinobettucci) [Mar 1](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12360810)

any browser, literally, tried with Chrome, Firefox, Brave, Opera and Safari.

If for any reason it works for someont is that the person have enabled unsafe cors either via one extension or via cli option.

This literally CAN'T WORK

[![@zaferfatihk](https://avatars.githubusercontent.com/u/112559468?v=4)zaferfatihk](https://github.com/zaferfatihk) [Jan 15](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11846113)

Guys come on. This doesn't work. You put a quickstart tutorial on one of the most hyped tools at the moment and you don't have time to fix it. Come on guys!!!

1

1 reply

[![@eyurtsev](https://avatars.githubusercontent.com/u/3205522?v=4)](https://github.com/eyurtsev)

[eyurtsev](https://github.com/eyurtsev) [Jan 20](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11885685)

Collaborator

Could you file an issue with an explanation of what doesn't work?

[![@xtbwqtq](https://avatars.githubusercontent.com/u/146714110?u=c34939f4e6363410681f9342eab4c37ed0a4c376&v=4)xtbwqtq](https://github.com/xtbwqtq) [Jan 16](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11850127)

What hook functions can be used to perform cleanup after langgraph-cli is shut down?

1

2 replies

[![@eyurtsev](https://avatars.githubusercontent.com/u/3205522?v=4)](https://github.com/eyurtsev)

[eyurtsev](https://github.com/eyurtsev) [Jan 20](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11885688)

Collaborator

What are you trying to achieve?

[![@xtbwqtq](https://avatars.githubusercontent.com/u/146714110?u=c34939f4e6363410681f9342eab4c37ed0a4c376&v=4)](https://github.com/xtbwqtq)

[xtbwqtq](https://github.com/xtbwqtq) [Feb 2](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12030705)

I think the end of the program is to recycle some resources, such as database connections.

[![@aymenja](https://avatars.githubusercontent.com/u/46452921?v=4)aymenja](https://github.com/aymenja) [Jan 28](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11984731)

Hey, I've followed all the steps of the process and after doing `langgraph dev` and opening the Studio, I'm getting `TypeError: Failed to Fetch` \- Could you help? Thank you

1

1 reply

[![@aymenja](https://avatars.githubusercontent.com/u/46452921?v=4)](https://github.com/aymenja)

[aymenja](https://github.com/aymenja) [Jan 28](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-11984985)

\[SOLVED\] Brave Browser was the culprit, removed shields. Thank you!

[![@haydeniw](https://avatars.githubusercontent.com/u/15167330?u=2d472fe5c7f09140dc62daac84d45a001b9de94f&v=4)haydeniw](https://github.com/haydeniw) [Feb 6](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12075877)

After running `langgraph dev` most of the time the website at `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024` successfully renders and runs. Occasionally for a fixed period of time it fails to load and eventually times out. I can see in the console that there's an error `Failed to load resource: the serve responded with a status of 403() from auth.langchain.com/auth/v1/user`

I see no correlation across the times that this happens versus not, but do know it persists for a while. I've tried clearing cookies as well and that did not do the trick.

I can see the langgraph server is up and I'm able to get responses from it from a python client. Any idea how to fix?

1

0 replies

[![@zbx12381](https://avatars.githubusercontent.com/u/54806110?v=4)zbx12381](https://github.com/zbx12381) [Feb 6](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12081782)

After running langgraph dev

INFO:langgraph\_api.cli:

```notranslate
    Welcome to

```

╦ ┌─┐┌┐┌┌─┐╔═╗┬─┐┌─┐┌─┐┬ ┬

║ ├─┤││││ ┬║ ╦├┬┘├─┤├─┘├─┤

╩═╝┴ ┴┘└┘└─┘╚═╝┴└─┴ ┴┴ ┴ ┴

- 🚀 API: [http://127.0.0.1:2024](http://127.0.0.1:2024/)
- 🎨 Studio UI: [https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)
- 📚 API Docs: [http://127.0.0.1:2024/docs](http://127.0.0.1:2024/docs)

This in-memory server is designed for development and testing.

For production use, please use LangGraph Cloud.

2025-02-06T13:05:57.151330Z \[info \] Will watch for changes in these directories: \['C:\\Users\\zbx\\path\\to\\your\\app'\] \[uvicorn.error\] api\_variant=local\_dev

2025-02-06T13:05:57.152330Z \[error \] \[WinError 10013\] 以一种访问权限不允许的方式做了一个访问套接字的尝试。 \[uvicorn.error\] api\_variant=local\_dev

what should i do

1

0 replies

[![@wyk-imarubbish](https://avatars.githubusercontent.com/u/142979167?v=4)wyk-imarubbish](https://github.com/wyk-imarubbish) [Feb 9](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12107076)

I followed the instructions above. I create a .env file and write my OPENAI\_API\_KEY and OPENAI\_API\_BASE, and then change the default model in configuration.py to 'openai/gpt-4-turbo-preview'.

But when i run `langgraph dev` and try to ask a question to the agent in web-ui, it says "BadRequestError("Error code: 400 - {'error': {'message': 'model not found gpt-4-turbo-preview', 'type': ''}}")".

Is it because the base-url? How to change the base-url then?

1

0 replies

[![@mizhazha](https://avatars.githubusercontent.com/u/6841406?u=60257fcfb0925cb87362e613ef3f18752cc0aa45&v=4)mizhazha](https://github.com/mizhazha) [Feb 11](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12149800)

Hi there is it possible to get this run with python 3.10? python 3.10 is the officially supported version in the company and our base image are using python 3.10.

1

0 replies

[![@justme409](https://avatars.githubusercontent.com/u/77142531?v=4)justme409](https://github.com/justme409) [Feb 13](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12183477)

GUYS GUYS GUYS! To fix the 'Failed to fetch'

Chrome > Settings > Privacy and Security > Site Settings > Additional content settings > Insecure content > Allowed to show insecure content > Add smith.langchain.com

1

👍1

2 replies

[![@chenjxpp](https://avatars.githubusercontent.com/u/164125038?v=4)](https://github.com/chenjxpp)

[chenjxpp](https://github.com/chenjxpp) [Feb 23](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12291835)

This work for me

❤️1

[![@martinobettucci](https://avatars.githubusercontent.com/u/19490374?u=5ae0113e9348bf2bc0851c804bc4b3ddbf84c1c4&v=4)](https://github.com/martinobettucci)

[martinobettucci](https://github.com/martinobettucci) [Mar 1](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12360821)

this is ridiculous, lower your browser security to make this software work...

[![@sagarmainkar](https://avatars.githubusercontent.com/u/5027785?v=4)sagarmainkar](https://github.com/sagarmainkar) [Feb 27](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12341746)

Team,

I was successfully using langgraph studio however, I am now getting a strange error

Attaching to langgraph-api-1, langgraph-postgres-1, langgraph-redis-1

1:C 27 Feb 2025 16:47:28.628 # oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo

1:C 27 Feb 2025 16:47:28.628 # Redis version=6.2.17, bits=64, commit=00000000, modified=0, pid=1, just started

1:C 27 Feb 2025 16:47:28.628 # Warning: no config file specified, using the default config. In order to specify a config file use redis-server /path/to/redis.conf

1:M 27 Feb 2025 16:47:28.629 \* monotonic clock: POSIX clock\_gettime

1:M 27 Feb 2025 16:47:28.631 \* Running mode=standalone, port=6379.

1:M 27 Feb 2025 16:47:28.631 # Server initialized

1:M 27 Feb 2025 16:47:28.633 \* Ready to accept connections

The files belonging to this database system will be owned by user "postgres".

This user must also own the server process.

langgraph-postgres-1 \|

The database cluster will be initialized with locale "en\_US.utf8".

The default database encoding has accordingly been set to "UTF8".

The default text search configuration will be set to "english".

langgraph-postgres-1 \|

Data page checksums are disabled.

langgraph-postgres-1 \|

fixing permissions on existing directory /var/lib/postgresql/data ... ok

\\rlanggraph-postgres-1 exited with code 1

Cleared all images containers and volumes but still error

1

0 replies

[![@martinobettucci](https://avatars.githubusercontent.com/u/19490374?u=5ae0113e9348bf2bc0851c804bc4b3ddbf84c1c4&v=4)martinobettucci](https://github.com/martinobettucci) [Mar 1](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12360853)

Create a proxy script with NGROK and set the API KEY in a file called `config.env`.

Run this script alongside your graph instance, OF COURSE YOU SHOULD LAUNCH BOTH THIS SCRIPT AND THE LANGRAPH STUDIO INSTANCE IN AN ISOLATED ENVIRONMENT.

Unfortunately the studio, the ways it work so far, is bad design because you're basically allowing the langsmith website to send and execute commands in your PC which is A MAJOR SECURITY FLAW (both in design and security): DO NOT EVER LET A REMOTE SERVER execute code on your pc, this is very basic security stuff.

My recommandation is execute the langgraph studio as a docker connected to a docker to docker network with this proxy.

```
from flask import Flask, request, make_response
import requests
from pyngrok import ngrok
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv("config.env")

app = Flask(__name__)

# Target base URL for proxying (backend you're proxying to)
PROXY_BASE_URL = "http://127.0.0.1:2024"  # Replace with your langhgraph docker URI

# Add CORS headers to allow everything
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'  # Allow all origins
    response.headers['Access-Control-Allow-Credentials'] = 'true'  # Allow credentials
    response.headers['Access-Control-Allow-Headers'] = '*'  # Allow all headers
    response.headers['Access-Control-Allow-Methods'] = '*'  # Allow all HTTP methods
    return response

# Handle all routes and proxy requests
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(path):
    # Handle preflight OPTIONS requests
    if request.method == 'OPTIONS':
        return add_cors_headers(make_response())

    # Build the proxied request to the target server
    target_url = f"{PROXY_BASE_URL}/{path}"
    try:
        response = requests.request(
            method=request.method,
            url=target_url,
            headers={key: value for key, value in request.headers.items() if key.lower() != 'host'},
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
        )

        # Build the response with proxied content and status
        flask_response = make_response(response.content, response.status_code)
        for key, value in response.headers.items():
            flask_response.headers[key] = value

        # Add CORS headers
        return add_cors_headers(flask_response)
    except requests.RequestException as e:
        return make_response(f"Error proxying request: {e}", 502)

# Handle favicon requests to avoid unnecessary errors
@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return an empty response with "No Content" status

if __name__ == '__main__':
    # Retrieve the ngrok authtoken from the .env file
    ngrok_authtoken = os.getenv("NGROK_AUTHTOKEN")

    # Authenticate ngrok with your authtoken
    ngrok.set_auth_token(ngrok_authtoken)

    # Start ngrok tunnel
    public_url = ngrok.connect(8123)
    print(f"ngrok tunnel: {public_url}")

    # Start Flask app
    app.run(host="0.0.0.0", port=8123)
```

Once lanched, open the NGROK url to validate the tunneling.

Use this tunnel as your local studio URL (instead of localhost).

Thank me later.

1

0 replies

[![@inetkachev](https://avatars.githubusercontent.com/u/15964681?u=646833f2587e87d959692e79cdb5c798fe363d86&v=4)inetkachev](https://github.com/inetkachev) [Mar 3](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12371446)

Don't have UI button to create new nodes.

1

0 replies

[![@Wave1art](https://avatars.githubusercontent.com/u/6087998?v=4)Wave1art](https://github.com/Wave1art) [Mar 4](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12382052)

edited

For anyone struggling with the CORS-blocks-langgraph-studio-from-accessing-a-locally-deployed-langgraph-server problem I've just posted a [slightly simper approach using nginx to reverse proxy](https://github.com/langchain-ai/langgraph/discussions/2460#discussioncomment-12381978) and add the missing Access-Control-XXXX headers needed for CORS to work in Chrome.

It's simpler in the sense that it:

- Doesn't require you to disable any security settings in Chrome
- Doesn't require additional services such as NGROK
- Runs locally on your machine, deployed as part of your Docker Compose
- is slightly fewer lines of code than other solutions (maybe!)

Ultimately it achieves a similar outcome to martinobettuchi's solution above, so choose whichever is more familiar or you prefer.

1

0 replies

[![@TsolakHarutyunyanP](https://avatars.githubusercontent.com/u/70896327?v=4)TsolakHarutyunyanP](https://github.com/TsolakHarutyunyanP) [Mar 25](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12612926)

Hi everyone

LangGraph project not loading after setup

After cloning the project and setting up the .env file, I tried to start the project, but the UI stays stuck on the "Starting new-langgraphjs-project" screen (as shown in the screenshot below). No TypeScript or JavaScript templates are being opened or rendered.

I see logs like:

bash

Copy

Edit

Starting metadata loop

Application startup complete.

HTTP Request: POST [https://api.smith.langchain.com/v1/metadata/submit](https://api.smith.langchain.com/v1/metadata/submit) "HTTP/1.1 204 No Content"

The status at the bottom shows:

● Starting Target port: 3000

Even though everything seems to be running, the app doesn't go past this loading screen.

Steps taken:

Cloned the repository.

Added a .env file with the correct values.

Ran the project using the provided instructions.

Expected behavior: A template (or the LangGraph builder) should open and allow me to build or view a graph.

Actual behavior: Just a loading screen — nothing else happens.

1

0 replies

[![@SunGaofeng](https://avatars.githubusercontent.com/u/26536764?u=542b113fa10fc6aa05d349312b8687e965fa3f9e&v=4)SunGaofeng](https://github.com/SunGaofeng) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12694797)

I've set up langgraph as the instruction, create app from template, cd to the app\_path, set API\_KEYs in .env, and then run `langgraph dev`. But when I open the link in web browser, it showed nothing.

I checked the log of the server program, just as following, which showed either 404 or 200 error. Is there anything wrong with my setup?

(1) when I open in web browser [http://localhost:2024/docs](http://localhost:2024/docs), the page is blank, and the server log is:

2025-04-02T01:26:56.991689Z \[info \] GET /docs 200 0ms \[langgraph\_api.server\] api\_variant=local\_dev latency\_ms=0 method=GET path=/docs

(2) [http://localhost:2024/](http://localhost:2024/), the page showed Not Found, and the server log is:

2025-04-02T01:31:50.626019Z \[info \] GET / 404 1ms \[langgraph\_api.server\] api\_variant=local\_dev latency\_ms=1 method=GET path=/ path\_params={}

(3) [https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024), and the server log is:

2025-04-02T01:31:20.686457Z \[info \] HTTP Request: POST [https://api.smith.langchain.com/v1/metadata/submit](https://api.smith.langchain.com/v1/metadata/submit) "HTTP/1.1 204 No Content" \[httpx\] api\_variant=local\_dev thread\_name=MainThread

2025-04-02T01:31:50.626019Z \[info \] GET / 404 1ms \[langgraph\_api.server\] api\_variant=local\_dev latency\_ms=1 method=GET path=/ path\_params={}

1

2 replies

[![@SunGaofeng](https://avatars.githubusercontent.com/u/26536764?u=542b113fa10fc6aa05d349312b8687e965fa3f9e&v=4)](https://github.com/SunGaofeng)

[SunGaofeng](https://github.com/SunGaofeng) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12694855)

when I open [https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024) in chrome, the web site showed:

Failed to load assistants

Please verify if the API server is running or accessible from the browser.

TypeError: Failed to fetch

[![@SunGaofeng](https://avatars.githubusercontent.com/u/26536764?u=542b113fa10fc6aa05d349312b8687e965fa3f9e&v=4)](https://github.com/SunGaofeng)

[SunGaofeng](https://github.com/SunGaofeng) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12694912)

if open [http://127.0.0.1:2024/ok](http://127.0.0.1:2024/ok), can get {"ok":true} in the brower. It seems that the server is ready? But why can't open [http://localhost:2024/docs](http://localhost:2024/docs) or [http://localhost:2024/](http://localhost:2024/)

[![@martin-mirantes](https://avatars.githubusercontent.com/u/55810484?v=4)martin-mirantes](https://github.com/martin-mirantes) [yesterday](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12925170)

Everything works fine except thread search:

```notranslate
INFO:langgraph_api.cli:

        Welcome to

╦  ┌─┐┌┐┌┌─┐╔═╗┬─┐┌─┐┌─┐┬ ┬
║  ├─┤││││ ┬║ ╦├┬┘├─┤├─┘├─┤
╩═╝┴ ┴┘└┘└─┘╚═╝┴└─┴ ┴┴  ┴ ┴

- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs

This in-memory server is designed for development and testing.
For production use, please use LangGraph Cloud.

2025-04-23T16:08:18.193731Z [info     ] Using langgraph_runtime_inmem  [langgraph_runtime] api_variant=local_dev thread_name=MainThread
2025-04-23T16:08:18.201829Z [info     ] Using auth of type=noop        [langgraph_api.auth.middleware] api_variant=local_dev thread_name=MainThread
2025-04-23T16:08:18.204031Z [info     ] Starting In-Memory runtime with langgraph-api=0.1.12 [langgraph_runtime_inmem.lifespan] api_variant=local_dev thread_name=asyncio_0 version=0.1.12
2025-04-23T16:08:18.543555Z [info     ] Registering graph with id 'chatbot' [langgraph_api.graph] api_variant=local_dev graph_id=chatbot thread_name=asyncio_0
2025-04-23T16:08:18.543967Z [info     ] Starting metadata loop         [langgraph_api.metadata] api_variant=local_dev thread_name=MainThread
2025-04-23T16:08:18.555563Z [info     ] Starting 1 background workers  [langgraph_runtime_inmem.queue] api_variant=local_dev thread_name=asyncio_0
2025-04-23T16:08:18.597538Z [info     ] Worker stats                   [langgraph_runtime_inmem.queue] active=0 api_variant=local_dev available=1 max=1 thread_name=asyncio_0
2025-04-23T16:08:18.838998Z [info     ] HTTP Request: POST https://api.smith.langchain.com/v1/metadata/submit "HTTP/1.1 204 No Content" [httpx] api_variant=local_dev thread_name=MainThread
2025-04-23T16:08:19.107530Z [info     ] Queue stats                    [langgraph_runtime_inmem.queue] api_variant=local_dev max_age_secs=None med_age_secs=None n_pending=0 n_running=0 thread_name=asyncio_0
2025-04-23T16:08:19.108012Z [info     ] Sweeped runs                   [langgraph_runtime_inmem.queue] api_variant=local_dev run_ids=[] thread_name=MainThread
Server started in 1.74s
2025-04-23T16:08:19.332740Z [info     ] Server started in 1.74s        [browser_opener] api_variant=local_dev message='Server started in 1.74s' thread_name='Thread-3 (_open_browser)'
🎨 Opening Studio in your browser...
2025-04-23T16:08:19.332886Z [info     ] 🎨 Opening Studio in your browser... [browser_opener] api_variant=local_dev message='🎨 Opening Studio in your browser...' thread_name='Thread-3 (_open_browser)'
URL: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024&organizationId=9315cbe7-b74d-4a9b-9393-f9ab629d310f
2025-04-23T16:08:19.333069Z [info     ] URL: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024&organizationId=9315cbe7-b74d-4a9b-9393-f9ab629d310f [browser_opener] api_variant=local_dev message='URL: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024&organizationId=9315cbe7-b74d-4a9b-9393-f9ab629d310f' thread_name='Thread-3 (_open_browser)'
2025-04-23T16:08:26.323221Z [info     ] Getting auth instance: None    [langgraph_api.auth.custom] api_variant=local_dev langgraph_auth=None thread_name=MainThread
2025-04-23T16:08:26.370509Z [error    ] Exception in ASGI application
 [uvicorn.error] api_variant=local_dev thread_name=MainThread
  + Exception Group Traceback (most recent call last):
  |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/_utils.py", line 76, in collapse_excgroups
  |     yield
  |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/middleware/base.py", line 177, in __call__
  |     async with anyio.create_task_group() as task_group:
  |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/anyio/_backends/_asyncio.py", line 772, in __aexit__
  |     raise BaseExceptionGroup(
  | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/uvicorn/protocols/http/h11_impl.py", line 403, in run_asgi
    |     result = await app(  # type: ignore[func-returns-value]
    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    |     return await self.app(scope, receive, send)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/applications.py", line 112, in __call__
    |     await self.middleware_stack(scope, receive, send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/middleware/errors.py", line 187, in __call__
    |     raise exc
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/middleware/errors.py", line 165, in __call__
    |     await self.app(scope, receive, _send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/middleware/base.py", line 176, in __call__
    |     with recv_stream, send_stream, collapse_excgroups():
    |   File "/usr/lib/python3.12/contextlib.py", line 158, in __exit__
    |     self.gen.throw(value)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/_utils.py", line 82, in collapse_excgroups
    |     raise exc
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/middleware/base.py", line 178, in __call__
    |     response = await self.dispatch_func(request, call_next)
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/langgraph_api/middleware/private_network.py", line 50, in dispatch
    |     response = await call_next(request)
    |                ^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/middleware/base.py", line 156, in call_next
    |     raise app_exc
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/middleware/base.py", line 141, in coro
    |     await self.app(scope, receive_or_disconnect, send_no_error)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/middleware/cors.py", line 93, in __call__
    |     await self.simple_response(scope, receive, send, request_headers=headers)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/middleware/cors.py", line 144, in simple_response
    |     await self.app(scope, receive, send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/langgraph_api/middleware/http_logger.py", line 65, in __call__
    |     raise exc
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/langgraph_api/middleware/http_logger.py", line 59, in __call__
    |     await self.app(scope, inner_receive, inner_send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
    |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    |     raise exc
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    |     await app(scope, receive, sender)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/routing.py", line 714, in __call__
    |     await self.middleware_stack(scope, receive, send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/routing.py", line 734, in app
    |     await route.handle(scope, receive, send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/routing.py", line 460, in handle
    |     await self.app(scope, receive, send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/langgraph_api/auth/middleware.py", line 49, in __call__
    |     return await super().__call__(scope, receive, send)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/middleware/authentication.py", line 48, in __call__
    |     await self.app(scope, receive, send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/routing.py", line 714, in __call__
    |     await self.middleware_stack(scope, receive, send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/routing.py", line 734, in app
    |     await route.handle(scope, receive, send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/langgraph_api/route.py", line 125, in handle
    |     return await super().handle(scope, receive, send)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/routing.py", line 288, in handle
    |     await self.app(scope, receive, send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/langgraph_api/route.py", line 38, in app
    |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    |     raise exc
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    |     await app(scope, receive, sender)
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/langgraph_api/route.py", line 33, in app
    |     response = await func(request)
    |                ^^^^^^^^^^^^^^^^^^^
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/langgraph_runtime_inmem/retry.py", line 27, in wrapper
    |     return await func(*args, **kwargs)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/home/martp/langchain-academy/lc-academy-env/lib/python3.12/site-packages/langgraph_api/api/threads.py", line 58, in search_threads
    |     iter, total = await Threads.search(
    |                         ^^^^^^^^^^^^^^^
    | TypeError: Threads.search() got an unexpected keyword argument 'sort_order'

```

1

1 reply

[![@ujitkumar1](https://avatars.githubusercontent.com/u/110418072?u=3f391132df96928b81f8f45332ee4f529afd4d00&v=4)](https://github.com/ujitkumar1)

[ujitkumar1](https://github.com/ujitkumar1) [5 hours ago](https://github.com/langchain-ai/langgraph/discussions/2527#discussioncomment-12938227)

Can you share which LangGraph version you're using?

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Flanggraph-platform%2Flocal-server%2F)