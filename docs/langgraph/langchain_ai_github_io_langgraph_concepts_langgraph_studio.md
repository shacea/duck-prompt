[Skip to content](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/#langgraph-studio)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/langgraph_studio.md "Edit this page")

# LangGraph Studio [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#langgraph-studio "Permanent link")

Prerequisites

- [LangGraph Platform](https://langchain-ai.github.io/langgraph/concepts/langgraph_platform/)
- [LangGraph Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/)

LangGraph Studio offers a new way to develop LLM applications by providing a specialized agent IDE that enables visualization, interaction, and debugging of complex agentic applications.

With visual graphs and the ability to edit state, you can better understand agent workflows and iterate faster. LangGraph Studio integrates with LangSmith allowing you to collaborate with teammates to debug failure modes.

![](https://langchain-ai.github.io/langgraph/concepts/img/lg_studio.png)

## Features [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#features "Permanent link")

The key features of LangGraph Studio are:

- Visualize your graphs
- Test your graph by running it from the UI
- Debug your agent by [modifying its state and rerunning](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- Create and manage [assistants](https://langchain-ai.github.io/langgraph/concepts/assistants/)
- View and manage [threads](https://langchain-ai.github.io/langgraph/concepts/persistence/#threads)
- View and manage [long term memory](https://langchain-ai.github.io/langgraph/concepts/memory/)
- Add node input/outputs to [LangSmith](https://smith.langchain.com/) datasets for testing

## Getting started [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#getting-started "Permanent link")

There are two ways to connect your LangGraph app with the studio:

### Deployed Application [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#deployed-application "Permanent link")

If you have deployed your LangGraph application on LangGraph Platform, you can access the studio as part of that deployment. To do so, navigate to the deployment in LangGraph Platform within the LangSmith UI and click the "LangGraph Studio" button.

### Local Development Server [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#local-development-server "Permanent link")

If you have a LangGraph application that is [running locally in-memory](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/), you can connect it to LangGraph Studio in the browser within LangSmith.

By default, starting the local server with `langgraph dev` will run the server at `http://127.0.0.1:2024` and automatically open Studio in your browser. However, you can also manually connect to Studio by either:

1. In LangGraph Platform, clicking the "LangGraph Studio" button and entering the server URL in the dialog that appears.

or

1. Navigating to the URL in your browser:

```md-code__content
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

```

## Related [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#related "Permanent link")

For more information please see the following:

- [LangGraph Studio how-to guides](https://langchain-ai.github.io/langgraph/how-tos/#langgraph-studio)
- [LangGraph CLI Documentation](https://langchain-ai.github.io/langgraph/cloud/reference/cli/)

## LangGraph Studio FAQs [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#langgraph-studio-faqs "Permanent link")

### Why is my project failing to start? [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#why-is-my-project-failing-to-start "Permanent link")

A project may fail to start if the configuration file is defined incorrectly, or if required environment variables are missing. See [here](https://langchain-ai.github.io/langgraph/cloud/reference/cli/#configuration-file) for how your configuration file should be defined.

### How does interrupt work? [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#how-does-interrupt-work "Permanent link")

When you select the `Interrupts` dropdown and select a node to interrupt the graph will pause execution before and after (unless the node goes straight to `END`) that node has run. This means that you will be able to both edit the state before the node is ran and the state after the node has ran. This is intended to allow developers more fine-grained control over the behavior of a node and make it easier to observe how the node is behaving. You will not be able to edit the state after the node has ran if the node is the final node in the graph.

For more information on interrupts and human in the loop, see [here](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/).

### Why are extra edges showing up in my graph? [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#why-are-extra-edges-showing-up-in-my-graph "Permanent link")

If you don't define your conditional edges carefully, you might notice extra edges appearing in your graph. This is because without proper definition, LangGraph Studio assumes the conditional edge could access all other nodes. In order for this to not be the case, you need to be explicit about how you define the nodes the conditional edge routes to. There are two ways you can do this:

#### Solution 1: Include a path map [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#solution-1-include-a-path-map "Permanent link")

The first way to solve this is to add path maps to your conditional edges. A path map is just a dictionary or array that maps the possible outputs of your router function with the names of the nodes that each output corresponds to. The path map is passed as the third argument to the `add_conditional_edges` function like so:

[Python](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/#__tabbed_1_1)[Javascript](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/#__tabbed_1_2)

```md-code__content
graph.add_conditional_edges("node_a", routing_function, {True: "node_b", False: "node_c"})

```

```md-code__content
graph.addConditionalEdges("node_a", routingFunction, { true: "node_b", false: "node_c" });

```

In this case, the routing function returns either True or False, which map to `node_b` and `node_c` respectively.

#### Solution 2: Update the typing of the router (Python only) [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#solution-2-update-the-typing-of-the-router-python-only "Permanent link")

Instead of passing a path map, you can also be explicit about the typing of your routing function by specifying the nodes it can map to using the `Literal` python definition. Here is an example of how to define a routing function in that way:

```md-code__content
def routing_function(state: GraphState) -> Literal["node_b","node_c"]:
    if state['some_condition'] == True:
        return "node_b"
    else:
        return "node_c"

```

### Studio Desktop FAQs [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#studio-desktop-faqs "Permanent link")

Deprecation Warning

In order to support a wider range of platforms and users, we now recommend following the above instructions to connect to LangGraph Studio using the development server instead of the desktop app.

The LangGraph Studio Desktop App is a standalone application that allows you to connect to your LangGraph application and visualize and interact with your graph. It is available for MacOS only and requires Docker to be installed.

#### Why is my project failing to start? [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#why-is-my-project-failing-to-start_1 "Permanent link")

In addition to the reasons listed above, for the desktop app there are a few more reasons that your project might fail to start:

Note

LangGraph Studio Desktop automatically populates `LANGCHAIN_*` environment variables for license verification and tracing, regardless of the contents of the `.env` file. All other environment variables defined in `.env` will be read as normal.

##### Docker issues [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#docker-issues "Permanent link")

LangGraph Studio (desktop) requires Docker Desktop version 4.24 or higher. Please make sure you have a version of Docker installed that satisfies that requirement and also make sure you have the Docker Desktop app up and running before trying to use LangGraph Studio. In addition, make sure you have docker-compose updated to version 2.22.0 or higher.

##### Incorrect data region [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#incorrect-data-region "Permanent link")

If you receive a license verification error when attempting to start the LangGraph Server, you may be logged into the incorrect LangSmith data region. Ensure that you're logged into the correct LangSmith data region and ensure that the LangSmith account has access to LangGraph platform.

1. In the top right-hand corner, click the user icon and select `Logout`.
2. At the login screen, click the `Data Region` dropdown menu and select the appropriate data region. Then click `Login to LangSmith`.

### How do I reload the app? [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#how-do-i-reload-the-app "Permanent link")

If you would like to reload the app, don't use Command+R as you might normally do. Instead, close and reopen the app for a full refresh.

### How does automatic rebuilding work? [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#how-does-automatic-rebuilding-work "Permanent link")

One of the key features of LangGraph Studio is that it automatically rebuilds your image when you change the source code. This allows for a super fast development and testing cycle which makes it easy to iterate on your graph. There are two different ways that LangGraph rebuilds your image: either by editing the image or completely rebuilding it.

#### Rebuilds from source code changes [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#rebuilds-from-source-code-changes "Permanent link")

If you modified the source code only (no configuration or dependency changes!) then the image does not require a full rebuild, and LangGraph Studio will only update the relevant parts. The UI status in the bottom left will switch from `Online` to `Stopping` temporarily while the image gets edited. The logs will be shown as this process is happening, and after the image has been edited the status will change back to `Online` and you will be able to run your graph with the modified code!

#### Rebuilds from configuration or dependency changes [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#rebuilds-from-configuration-or-dependency-changes "Permanent link")

If you edit your graph configuration file ( `langgraph.json`) or the dependencies (either `pyproject.toml` or `requirements.txt`) then the entire image will be rebuilt. This will cause the UI to switch away from the graph view and start showing the logs of the new image building process. This can take a minute or two, and once it is done your updated image will be ready to use!

### Why is my graph taking so long to startup? [¶](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/\#why-is-my-graph-taking-so-long-to-startup "Permanent link")

The LangGraph Studio interacts with a local LangGraph API server. To stay aligned with ongoing updates, the LangGraph API requires regular rebuilding. As a result, you may occasionally experience slight delays when starting up your project.

## Comments

giscus

#### [2 reactions](https://github.com/langchain-ai/langgraph/discussions/2389)

👍1🚀1

#### [4 comments](https://github.com/langchain-ai/langgraph/discussions/2389)

#### ·

#### 1 reply

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@sanjeed5](https://avatars.githubusercontent.com/u/40694326?v=4)sanjeed5](https://github.com/sanjeed5) [Nov 11, 2024](https://github.com/langchain-ai/langgraph/discussions/2389#discussioncomment-11218159)

cool stuff

1

0 replies

[![@Fancyfoot](https://avatars.githubusercontent.com/u/34892276?u=81f9c08d1b8dc7a11d2a8c189460ff0b7a323a2d&v=4)Fancyfoot](https://github.com/Fancyfoot) [Nov 12, 2024](https://github.com/langchain-ai/langgraph/discussions/2389#discussioncomment-11229877)

Awesome Guys

1

0 replies

[![@avfranco-br](https://avatars.githubusercontent.com/u/20467839?u=5c3ec3af04b6f428ec7db760a0881e90b2267761&v=4)avfranco-br](https://github.com/avfranco-br) [Dec 20, 2024](https://github.com/langchain-ai/langgraph/discussions/2389#discussioncomment-11630864)

Hi, great stuff! However, I haven't been able to fix an issue that's causing my application not start with Langgraph Studio. I am using requirements.txt and all modules successfully imported., Langgraph Studios is installed on the same project environment. Any help will be very appreciated. Many thanks.

Failed to start project ea4all

error \| Traceback (most recent call last):

File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 693, in lifespan

async with self.lifespan\_context(app) as maybe\_state:

File "/usr/local/lib/python3.11/contextlib.py", line 210, in **aenter**

return await anext(self.gen)

^^^^^^^^^^^^^^^^^^^^^

File "/api/langgraph\_api/lifespan.py", line 30, in lifespan

File "/api/langgraph\_api/graph.py", line 257, in collect\_graphs\_from\_env

File "/usr/local/lib/python3.11/site-packages/langchain\_core/runnables/config.py", line 588, in run\_in\_executor

return await asyncio.get\_running\_loop().run\_in\_executor(

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "/usr/local/lib/python3.11/concurrent/futures/thread.py", line 58, in run

result = self.fn(\*self.args, \*\*self.kwargs)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "/usr/local/lib/python3.11/site-packages/langchain\_core/runnables/config.py", line 579, in wrapper

return func(\*args, \*\*kwargs)

^^^^^^^^^^^^^^^^^^^^^

File "/api/langgraph\_api/graph.py", line 295, in \_graph\_from\_spec

File "", line 940, in exec\_module

File "", line 241, in \_call\_with\_frames\_removed

File "/deps/\_\_outer\_ea4all/src/src/apm\_graph/graph.py", line 25, in

from langchain.hub import pull

ModuleNotFoundError: No module named 'langchain'

Could not import python module for graph:

GraphSpec(id='apm\_qna', path='/deps/\_\_outer\_ea4all/src/src/apm\_graph/graph.py', module=None, variable='graph', config=None)

error \| Application startup failed. Exiting.

1

1 reply

[![@shiblyanastas](https://avatars.githubusercontent.com/u/141586897?u=0cb932574d04b89f9af2f6159312609353dc9a25&v=4)](https://github.com/shiblyanastas)

[shiblyanastas](https://github.com/shiblyanastas) [Mar 1](https://github.com/langchain-ai/langgraph/discussions/2389#discussioncomment-12362133)

[@avfranco-br](https://github.com/avfranco-br), Did you fix the problem? if yes, I appreciate very much if you tell us what was the problem! Thanks in advance!

[![@verbadi](https://avatars.githubusercontent.com/u/187024670?v=4)verbadi](https://github.com/verbadi) [21 days ago](https://github.com/langchain-ai/langgraph/discussions/2389#discussioncomment-12713352)

How can I define the node types for conditional edges which return a sequence of Send Objects?

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Flanggraph_studio%2F)