[Skip to content](https://langchain-ai.github.io/langgraph/how-tos/visualization/#how-to-visualize-your-graph)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/how-tos/visualization.ipynb "Edit this page")

# How to visualize your graph [¶](https://langchain-ai.github.io/langgraph/how-tos/visualization/\#how-to-visualize-your-graph "Permanent link")

This guide walks through how to visualize the graphs you create. This works with ANY [Graph](https://langchain-ai.github.io/langgraph/reference/graphs/).

## Setup [¶](https://langchain-ai.github.io/langgraph/how-tos/visualization/\#setup "Permanent link")

First, let's install the required packages

```md-code__content
%%capture --no-stderr
%pip install -U langgraph

```

## Set up Graph [¶](https://langchain-ai.github.io/langgraph/how-tos/visualization/\#set-up-graph "Permanent link")

You can visualize any arbitrary [Graph](https://langchain-ai.github.io/langgraph/reference/graphs/), including [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph). Let's have some fun by drawing fractals :).

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [add\_messages](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.message.add_messages)

```md-code__content
import random
from typing import Annotated, Literal

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

class MyNode:
    def __init__(self, name: str):
        self.name = name

    def __call__(self, state: State):
        return {"messages": [("assistant", f"Called node {self.name}")]}

def route(state) -> Literal["entry_node", "__end__"]:
    if len(state["messages"]) > 10:
        return "__end__"
    return "entry_node"

def add_fractal_nodes(builder, current_node, level, max_level):
    if level > max_level:
        return

    # Number of nodes to create at this level
    num_nodes = random.randint(1, 3)  # Adjust randomness as needed
    for i in range(num_nodes):
        nm = ["A", "B", "C"][i]
        node_name = f"node_{current_node}_{nm}"
        builder.add_node(node_name, MyNode(node_name))
        builder.add_edge(current_node, node_name)

        # Recursively add more nodes
        r = random.random()
        if r > 0.2 and level + 1 < max_level:
            add_fractal_nodes(builder, node_name, level + 1, max_level)
        elif r > 0.05:
            builder.add_conditional_edges(node_name, route, node_name)
        else:
            # End
            builder.add_edge(node_name, "__end__")

def build_fractal_graph(max_level: int):
    builder = StateGraph(State)
    entry_point = "entry_node"
    builder.add_node(entry_point, MyNode(entry_point))
    builder.add_edge(START, entry_point)

    add_fractal_nodes(builder, entry_point, 1, max_level)

    # Optional: set a finish point if required
    builder.add_edge(entry_point, END)  # or any specific node

    return builder.compile()

app = build_fractal_graph(3)

```

## Mermaid [¶](https://langchain-ai.github.io/langgraph/how-tos/visualization/\#mermaid "Permanent link")

We can also convert a graph class into Mermaid syntax.

```md-code__content
print(app.get_graph().draw_mermaid())

```

```md-code__content
%%{init: {'flowchart': {'curve': 'linear'}}}%%
graph TD;
    __start__([<p>__start__</p>]):::first
    entry_node(entry_node)
    node_entry_node_A(node_entry_node_A)
    node_entry_node_B(node_entry_node_B)
    node_node_entry_node_B_A(node_node_entry_node_B_A)
    node_node_entry_node_B_B(node_node_entry_node_B_B)
    node_node_entry_node_B_C(node_node_entry_node_B_C)
    __end__([<p>__end__</p>]):::last
    __start__ --> entry_node;
    entry_node --> __end__;
    entry_node --> node_entry_node_A;
    entry_node --> node_entry_node_B;
    node_entry_node_B --> node_node_entry_node_B_A;
    node_entry_node_B --> node_node_entry_node_B_B;
    node_entry_node_B --> node_node_entry_node_B_C;
    node_entry_node_A -.-> entry_node;
    node_entry_node_A -.-> __end__;
    node_node_entry_node_B_A -.-> entry_node;
    node_node_entry_node_B_A -.-> __end__;
    node_node_entry_node_B_B -.-> entry_node;
    node_node_entry_node_B_B -.-> __end__;
    node_node_entry_node_B_C -.-> entry_node;
    node_node_entry_node_B_C -.-> __end__;
    classDef default fill:#f2f0ff,line-height:1.2
    classDef first fill-opacity:0
    classDef last fill:#bfb6fc

```

## PNG [¶](https://langchain-ai.github.io/langgraph/how-tos/visualization/\#png "Permanent link")

If preferred, we could render the Graph into a `.png`. Here we could use three options:

- Using Mermaid.ink API (does not require additional packages)
- Using Mermaid + Pyppeteer (requires `pip install pyppeteer`)
- Using graphviz (which requires `pip install graphviz`)

### Using Mermaid.Ink [¶](https://langchain-ai.github.io/langgraph/how-tos/visualization/\#using-mermaidink "Permanent link")

By default, `draw_mermaid_png()` uses Mermaid.Ink's API to generate the diagram.

API Reference: [CurveStyle](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.graph.CurveStyle.html) \| [MermaidDrawMethod](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.graph.MermaidDrawMethod.html) \| [NodeStyles](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.graph.NodeStyles.html)

```md-code__content
from IPython.display import Image, display
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles

display(
    Image(
        app.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.API,
        )
    )
)

```

![](<Base64-Image-Removed>)

### Using Mermaid + Pyppeteer [¶](https://langchain-ai.github.io/langgraph/how-tos/visualization/\#using-mermaid-pyppeteer "Permanent link")

```md-code__content
%%capture --no-stderr
%pip install --quiet pyppeteer
%pip install --quiet nest_asyncio

```

```md-code__content
import nest_asyncio

nest_asyncio.apply()  # Required for Jupyter Notebook to run async functions

display(
    Image(
        app.get_graph().draw_mermaid_png(
            curve_style=CurveStyle.LINEAR,
            node_colors=NodeStyles(first="#ffdfba", last="#baffc9", default="#fad7de"),
            wrap_label_n_words=9,
            output_file_path=None,
            draw_method=MermaidDrawMethod.PYPPETEER,
            background_color="white",
            padding=10,
        )
    )
)

```

![](<Base64-Image-Removed>)

### Using Graphviz [¶](https://langchain-ai.github.io/langgraph/how-tos/visualization/\#using-graphviz "Permanent link")

```md-code__content
%%capture --no-stderr
%pip install pygraphviz

```

```md-code__content
try:
    display(Image(app.get_graph().draw_png()))
except ImportError:
    print(
        "You likely need to install dependencies for pygraphviz, see more here https://github.com/pygraphviz/pygraphviz/blob/main/INSTALL.txt"
    )

```

![](<Base64-Image-Removed>)

## Comments

giscus

#### [2 reactions](https://github.com/langchain-ai/langgraph/discussions/570)

👍2

#### [11 comments](https://github.com/langchain-ai/langgraph/discussions/570)

#### ·

#### 15 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@Pao10](https://avatars.githubusercontent.com/u/20927104?v=4)Pao10](https://github.com/Pao10) [Jun 2, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9638381)

When I want to draw my graph, I get only a "pregel" node instead of all my nodes. Can you help me on this ?

1

4 replies

[![@hwchase17](https://avatars.githubusercontent.com/u/11986836?u=f4c4f21a82b2af6c9f91e1f1d99ea40062f7a101&v=4)](https://github.com/hwchase17)

[hwchase17](https://github.com/hwchase17) [Jun 2, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9639224)

Contributor

Can you provide more information on what your graph looks like?

[![@Pao10](https://avatars.githubusercontent.com/u/20927104?v=4)](https://github.com/Pao10)

[Pao10](https://github.com/Pao10) [Jun 4, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9661261)

Hi thank you :

it displays only three bubbles :

LangraphInput --> Pregel --> LangGraphOutput

[![@Pao10](https://avatars.githubusercontent.com/u/20927104?v=4)](https://github.com/Pao10)

[Pao10](https://github.com/Pao10) [Jun 13, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9767433)

Hi, any idea what I am doing wrong ?

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Jun 13, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9768017)

Contributor

[Could you please share code](https://stackoverflow.com/help/minimal-reproducible-example) to make it possible to help?

[![@jackiezhangcn](https://avatars.githubusercontent.com/u/13310512?v=4)jackiezhangcn](https://github.com/jackiezhangcn) [Jun 6, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9686930)

tried every method, but all failed with: <IPython.core.display.Image object>,

1

3 replies

[![@Jaid844](https://avatars.githubusercontent.com/u/112820053?u=b35ffddc9527dccae75e42533f86853bc7cdd438&v=4)](https://github.com/Jaid844)

[Jaid844](https://github.com/Jaid844) [Jun 9, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9717774)

are you trying in jupyter notebook

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Jun 13, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9768025)

Contributor

Ya IPython renders in jupyter. If you want to see it otherwise you'd write it out as a PNG

[![@lmc0521](https://avatars.githubusercontent.com/u/47588907?v=4)](https://github.com/lmc0521)

[lmc0521](https://github.com/lmc0521) [Aug 11, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-10301221)

If I want to use Pycharm to display my graph, how could I do it?

👍1

[![@LordO54](https://avatars.githubusercontent.com/u/119976077?v=4)LordO54](https://github.com/LordO54) [Jun 8, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9713461)

How can I deploy a agent made with this?

1

1 reply

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Jun 13, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9768021)

Contributor

edited

If you're looking for a hosted solution, [we're planning to launch a managed option](https://github.com/langchain-ai/langgraph-example) soon ( [docs](https://langchain-ai.github.io/langgraph/cloud/))

Also plan to publish reference checkpointers.

[![@hodgesz](https://avatars.githubusercontent.com/u/1764965?v=4)hodgesz](https://github.com/hodgesz) [Jun 15, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9781699)

Do the dotted lines indicate asynchronous and solid synchronous?

1

3 replies

[![@hodgesz](https://avatars.githubusercontent.com/u/1764965?v=4)](https://github.com/hodgesz)

[hodgesz](https://github.com/hodgesz) [Jun 18, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9810286)

anyone?

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Jun 19, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9820984)

Contributor

They represent conditional edges. Async/Sync/Stream/etc. is less a property of the graph than it is the method you invoke it

😄1

[![@hodgesz](https://avatars.githubusercontent.com/u/1764965?v=4)](https://github.com/hodgesz)

[hodgesz](https://github.com/hodgesz) [Jun 19, 2024](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-9821026)

Really appreciate it!

[![@qingzhengar](https://avatars.githubusercontent.com/u/145352698?u=f1e229bf749f3ff4ac7573df1fee6f5c4608dbc2&v=4)qingzhengar](https://github.com/qingzhengar) [Jan 27](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-11975077)

some of my nodes are not showed in the generated graph. Some of the generated edges are not correct.

My graph works as expected, just the generated graph is not correct.

1

0 replies

[![@ESJavadex](https://avatars.githubusercontent.com/u/11579714?u=fb8ea61848aee3cfda1296e2962ac2065c3f4a34&v=4)ESJavadex](https://github.com/ESJavadex) [Feb 4](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-12054187)

Is there any way to show the tools that a model has binded?

1

👍2

1 reply

[![@Superskyyy](https://avatars.githubusercontent.com/u/26076517?u=6457805af06994e063da75ffcb09e055494408d0&v=4)](https://github.com/Superskyyy)

[Superskyyy](https://github.com/Superskyyy) [Feb 24](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-12296350)

I don't think currently there's a way, other than binding the tools to nodes manually as a state transition.

❤️1

[![@AndreiSolodinTR](https://avatars.githubusercontent.com/u/57628536?v=4)AndreiSolodinTR](https://github.com/AndreiSolodinTR) [Feb 27](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-12342033)

edited

Hello, in our application we add a bunch of nodes to StateGraph and then construct the edges with a subset of them. These graphs can then be used as subgraphs in a larger graph. This works fine. However, if we try to visualize the entire graph, we get ValueError: Could not extend subgraph 'Y' due to missing entrypoint. The root cause appears to be the way the entry point for a subgraph is determined. Basically the algorithm does a set difference of nodes and edge targets and if there is > 1 node left, it errors out. Note, that this is not the case for the main graph: you can have extra nodes and visualization works just fine. I guess my question is if this could be a candidate for a bugfix or enhancement? The subgraph algorithm could simply be changed to do a set difference of edge sources and targets. Here's the code snippet to reproduce the issue:

from langgraph.graph import StateGraph

from langgraph.graph import START, END

class TestNode:

"""A simple test node class."""

```notranslate
def __init__(self, name):
    self.name = name

def __call__(self, *args, **kwargs):
    input = args[0]
    return f"Processed {input} in {self.name}"

```

def test\_langgraph\_graph\_extends():

"""Test that the graph extension works as expected."""

subgraph = StateGraph(state\_schema=str)

subgraph.add\_node("A", TestNode("A"))

subgraph.add\_node("B", TestNode("B"))

subgraph.add\_node("C", TestNode("C"))

subgraph.add\_edge(START, "A")

subgraph.add\_edge("A", "B")

subgraph.add\_edge("B", END)

```notranslate
graph = StateGraph(state_schema=str)
graph.add_node("X", TestNode("X"))
graph.add_node("Y", subgraph.compile())
graph.add_node("Z", TestNode("Z"))
graph.add_edge(START, "X")
graph.add_edge("X", "Y")
graph.add_edge("Y", "Z")
graph.add_edge("Z", END)

graph.compile().get_graph(xray=True)

```

2

1 reply

[![@AndreiSolodinTR](https://avatars.githubusercontent.com/u/57628536?v=4)](https://github.com/AndreiSolodinTR)

[AndreiSolodinTR](https://github.com/AndreiSolodinTR) [Feb 27](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-12342272)

I saw the reply in a different thread, sorry for duplicate posts.

[![@rajandevkota98](https://avatars.githubusercontent.com/u/34398821?u=c1e210d0775c893b3ba622c36adf46101be3c1db&v=4)rajandevkota98](https://github.com/rajandevkota98) [Mar 10](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-12444012)

Whenever I am trying to visualize the graph, I get this error: ---------------------------------------------------------------------------

TimeoutError Traceback (most recent call last)

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/urllib3/connectionpool.py:536, in HTTPConnectionPool.\_make\_request(self, conn, method, url, body, headers, retries, timeout, chunked, response\_conn, preload\_content, decode\_content, enforce\_content\_length)

535 try:

--\> 536 response = conn.getresponse()

537 except (BaseSSLError, OSError) as e:

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/urllib3/connection.py:507, in HTTPConnection.getresponse(self)

506 # Get the response from http.client.HTTPConnection

--\> 507 httplib\_response = super().getresponse()

509 try:

File ~/miniconda3/envs/exo/lib/python3.12/http/client.py:1411, in HTTPConnection.getresponse(self)

1410 try:

-\> 1411 response.begin()

1412 except ConnectionError:

File ~/miniconda3/envs/exo/lib/python3.12/http/client.py:324, in HTTPResponse.begin(self)

323 while True:

--\> 324 version, status, reason = self.\_read\_status()

325 if status != CONTINUE:

File ~/miniconda3/envs/exo/lib/python3.12/http/client.py:285, in HTTPResponse.\_read\_status(self)

284 def \_read\_status(self):

--\> 285 line = str(self.fp.readline(\_MAXLINE + 1), "iso-8859-1")

286 if len(line) > \_MAXLINE:

File ~/miniconda3/envs/exo/lib/python3.12/socket.py:707, in SocketIO.readinto(self, b)

706 try:

--\> 707 return self.\_sock.recv\_into(b)

708 except timeout:

File ~/miniconda3/envs/exo/lib/python3.12/ssl.py:1249, in SSLSocket.recv\_into(self, buffer, nbytes, flags)

1246 raise ValueError(

1247 "non-zero flags not allowed in calls to recv\_into() on %s" %

1248 self. **class**)

-\> 1249 return self.read(nbytes, buffer)

1250 else:

File ~/miniconda3/envs/exo/lib/python3.12/ssl.py:1105, in SSLSocket.read(self, len, buffer)

1104 if buffer is not None:

-\> 1105 return self.\_sslobj.read(len, buffer)

1106 else:

TimeoutError: The read operation timed out

The above exception was the direct cause of the following exception:

ReadTimeoutError Traceback (most recent call last)

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/requests/adapters.py:667, in HTTPAdapter.send(self, request, stream, timeout, verify, cert, proxies)

666 try:

--\> 667 resp = conn.urlopen(

668 method=request.method,

669 url=url,

670 body=request.body,

671 headers=request.headers,

672 redirect=False,

673 assert\_same\_host=False,

674 preload\_content=False,

675 decode\_content=False,

676 retries=self.max\_retries,

677 timeout=timeout,

678 chunked=chunked,

679 )

681 except (ProtocolError, OSError) as err:

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/urllib3/connectionpool.py:843, in HTTPConnectionPool.urlopen(self, method, url, body, headers, retries, redirect, assert\_same\_host, timeout, pool\_timeout, release\_conn, chunked, body\_pos, preload\_content, decode\_content, \*\*response\_kw)

841 new\_e = ProtocolError("Connection aborted.", new\_e)

--\> 843 retries = retries.increment(

844 method, url, error=new\_e, \_pool=self, \_stacktrace=sys.exc\_info()\[2\]

845 )

846 retries.sleep()

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/urllib3/util/retry.py:474, in Retry.increment(self, method, url, response, error, \_pool, \_stacktrace)

473 if read is False or method is None or not self.\_is\_method\_retryable(method):

--\> 474 raise reraise(type(error), error, \_stacktrace)

475 elif read is not None:

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/urllib3/util/util.py:39, in reraise(tp, value, tb)

38 raise value.with\_traceback(tb)

---\> 39 raise value

40 finally:

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/urllib3/connectionpool.py:789, in HTTPConnectionPool.urlopen(self, method, url, body, headers, retries, redirect, assert\_same\_host, timeout, pool\_timeout, release\_conn, chunked, body\_pos, preload\_content, decode\_content, \*\*response\_kw)

788 # Make the request on the HTTPConnection object

--\> 789 response = self.\_make\_request(

790 conn,

791 method,

792 url,

793 timeout=timeout\_obj,

794 body=body,

795 headers=headers,

796 chunked=chunked,

797 retries=retries,

798 response\_conn=response\_conn,

799 preload\_content=preload\_content,

800 decode\_content=decode\_content,

801 \*\*response\_kw,

802 )

804 # Everything went great!

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/urllib3/connectionpool.py:538, in HTTPConnectionPool.\_make\_request(self, conn, method, url, body, headers, retries, timeout, chunked, response\_conn, preload\_content, decode\_content, enforce\_content\_length)

537 except (BaseSSLError, OSError) as e:

--\> 538 self.\_raise\_timeout(err=e, url=url, timeout\_value=read\_timeout)

539 raise

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/urllib3/connectionpool.py:369, in HTTPConnectionPool.\_raise\_timeout(self, err, url, timeout\_value)

368 if isinstance(err, SocketTimeout):

--\> 369 raise ReadTimeoutError(

370 self, url, f"Read timed out. (read timeout={timeout\_value})"

371 ) from err

373 # See the above comment about EAGAIN in Python 3.

ReadTimeoutError: HTTPSConnectionPool(host='mermaid.ink', port=443): Read timed out. (read timeout=10)

During handling of the above exception, another exception occurred:

ReadTimeout Traceback (most recent call last)

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/IPython/core/formatters.py:1036, in MimeBundleFormatter. **call**(self, obj, include, exclude)

1033 method = get\_real\_method(obj, self.print\_method)

1035 if method is not None:

-\> 1036 return method(include=include, exclude=exclude)

1037 return None

1038 else:

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/langgraph/graph/graph.py:641, in CompiledGraph. _repr\_mimebundle_(self, \*\*kwargs)

637 def _repr\_mimebundle_(self, \*\*kwargs: Any) -> dict\[str, Any\]:

638 """Mime bundle used by Jupyter to display the graph"""

639 return {

640 "text/plain": repr(self),

--\> 641 "image/png": self.get\_graph().draw\_mermaid\_png(),

642 }

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/langchain\_core/runnables/graph.py:630, in Graph.draw\_mermaid\_png(self, curve\_style, node\_colors, wrap\_label\_n\_words, output\_file\_path, draw\_method, background\_color, padding)

623 from langchain\_core.runnables.graph\_mermaid import draw\_mermaid\_png

625 mermaid\_syntax = self.draw\_mermaid(

626 curve\_style=curve\_style,

627 node\_colors=node\_colors,

628 wrap\_label\_n\_words=wrap\_label\_n\_words,

629 )

--\> 630 return draw\_mermaid\_png(

631 mermaid\_syntax=mermaid\_syntax,

632 output\_file\_path=output\_file\_path,

633 draw\_method=draw\_method,

634 background\_color=background\_color,

635 padding=padding,

636 )

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/langchain\_core/runnables/graph\_mermaid.py:214, in draw\_mermaid\_png(mermaid\_syntax, output\_file\_path, draw\_method, background\_color, padding)

208 img\_bytes = asyncio.run(

209 \_render\_mermaid\_using\_pyppeteer(

210 mermaid\_syntax, output\_file\_path, background\_color, padding

211 )

212 )

213 elif draw\_method == MermaidDrawMethod.API:

--\> 214 img\_bytes = \_render\_mermaid\_using\_api(

215 mermaid\_syntax, output\_file\_path, background\_color

216 )

217 else:

218 supported\_methods = ", ".join(\[m.value for m in MermaidDrawMethod\])

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/langchain\_core/runnables/graph\_mermaid.py:336, in \_render\_mermaid\_using\_api(mermaid\_syntax, output\_file\_path, background\_color, file\_type)

330 background\_color = f"!{background\_color}"

332 image\_url = (

333 f" [https://mermaid.ink/img/{mermaid\_syntax\_encoded}](https://mermaid.ink/img/%7Bmermaid_syntax_encoded%7D)"

334 f"?type={file\_type}&bgColor={background\_color}"

335 )

--\> 336 response = requests.get(image\_url, timeout=10)

337 if response.status\_code == 200:

338 img\_bytes = response.content

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/requests/api.py:73, in get(url, params, \*\*kwargs)

62 def get(url, params=None, \*\*kwargs):

63 r"""Sends a GET request.

64

65 :param url: URL for the new :class: `Request` object.

(...)

70 :rtype: requests.Response

71 """

---\> 73 return request("get", url, params=params, \*\*kwargs)

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/requests/api.py:59, in request(method, url, \*\*kwargs)

55 # By using the 'with' statement we are sure the session is closed, thus we

56 # avoid leaving sockets open which can trigger a ResourceWarning in some

57 # cases, and look like a memory leak in others.

58 with sessions.Session() as session:

---\> 59 return session.request(method=method, url=url, \*\*kwargs)

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/requests/sessions.py:589, in Session.request(self, method, url, params, data, headers, cookies, files, auth, timeout, allow\_redirects, proxies, hooks, stream, verify, cert, json)

584 send\_kwargs = {

585 "timeout": timeout,

586 "allow\_redirects": allow\_redirects,

587 }

588 send\_kwargs.update(settings)

--\> 589 resp = self.send(prep, \*\*send\_kwargs)

591 return resp

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/requests/sessions.py:703, in Session.send(self, request, \*\*kwargs)

700 start = preferred\_clock()

702 # Send the request

--\> 703 r = adapter.send(request, \*\*kwargs)

705 # Total elapsed time of the request (approximately)

706 elapsed = preferred\_clock() - start

File ~/miniconda3/envs/exo/lib/python3.12/site-packages/requests/adapters.py:713, in HTTPAdapter.send(self, request, stream, timeout, verify, cert, proxies)

711 raise SSLError(e, request=request)

712 elif isinstance(e, ReadTimeoutError):

--\> 713 raise ReadTimeout(e, request=request)

714 elif isinstance(e, \_InvalidHeader):

715 raise InvalidHeader(e, request=request)

ReadTimeout: HTTPSConnectionPool(host='mermaid.ink', port=443): Read timed out. (read timeout=10)

7

1 reply

[![@mohamadlakkis](https://avatars.githubusercontent.com/u/74541089?u=367992eb7df04d4a8da0fb78741caf769294d7b9&v=4)](https://github.com/mohamadlakkis)

[mohamadlakkis](https://github.com/mohamadlakkis) [18 days ago](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-12738654)

I faced the same problem, but I had asynchronous nodes in my graph. If that is the case for you, you could use this:

import nest\_asyncio

from langchain\_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles

nest\_asyncio.apply() # Required for Jupyter Notebook to run async functions

display(

Image(

graph.get\_graph().draw\_mermaid\_png(

curve\_style=CurveStyle.BASIS,

node\_colors=NodeStyles(first="#64784", last="#baffc9", default="#fad7de"),

output\_file\_path="./graph.png",

draw\_method=MermaidDrawMethod.PYPPETEER,

background\_color="white",

padding=1,

)

)

)

[![@khteh](https://avatars.githubusercontent.com/u/3871483?u=8434f4d49eefb670c9cd64152fad5e6c504fc459&v=4)khteh](https://github.com/khteh) [Mar 10](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-12446792)

It doesn't work with python module code: [https://stackoverflow.com/questions/79493962/ipython-display-does-not-show-any-image-at-all-but-ipython-core-display-image-o](https://stackoverflow.com/questions/79493962/ipython-display-does-not-show-any-image-at-all-but-ipython-core-display-image-o)

1

1 reply

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [21 days ago](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-12706972)

Contributor

THen draw ascii or draw to png.

[![@sandeepbhutani304](https://avatars.githubusercontent.com/u/4421756?u=86dde50440749d848899820700dd8ac9cea5aef6&v=4)sandeepbhutani304](https://github.com/sandeepbhutani304) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-12705141)

This is good.. How can we change the yellow color to some fancy..

Dont want to use mermaid, as we are offline...

3

0 replies

[![@kdyzm](https://avatars.githubusercontent.com/u/12097910?u=d41ef4687e4d9935d5a05a97ee222ead81c00938&v=4)kdyzm](https://github.com/kdyzm) [2 days ago](https://github.com/langchain-ai/langgraph/discussions/570#discussioncomment-12907063)

The display method didn't work, and it only output "<IPython.core.display.Image object>" in the console.

I'm using Pycharm 2020.3.5.

How to solve this problem?

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fhow-tos%2Fvisualization%2F)