[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/#web-voyager)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/web-navigation/web_voyager.ipynb "Edit this page")

# Web Voyager [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#web-voyager "Permanent link")

[WebVoyager](https://arxiv.org/abs/2401.13919) by He, et. al., is a vision-enabled web-browsing agent capable of controlling the mouse and keyboard.

It works by viewing annotated browser screenshots for each turn, then choosing the next step to take. The agent architecture is a basic reasoning and action (ReAct) loop.
The unique aspects of this agent are:
\- It's usage of [Set-of-Marks](https://som-gpt4v.github.io/)-like image annotations to serve as UI affordances for the agent
\- It's application in the browser by using tools to control both the mouse and keyboard

The overall design looks like the following:

![](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/img/web-voyager.excalidraw.jpg)

## Setup [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#setup "Permanent link")

First, let's install our required packages:

```md-code__content
%%capture --no-stderr
%pip install -U --quiet langgraph langsmith langchain_openai

```

```md-code__content
import os
from getpass import getpass

def _getpass(env_var: str):
    if not os.environ.get(env_var):
        os.environ[env_var] = getpass(f"{env_var}=")

_getpass("OPENAI_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


#### Install Agent requirements [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#install-agent-requirements "Permanent link")

The only additional requirement we have is the [playwright](https://playwright.dev/) browser. Uncomment and install below:

```md-code__content
%pip install --upgrade --quiet  playwright > /dev/null
!playwright install

```

```md-code__content
import nest_asyncio

# This is just required for running async playwright in a Jupyter notebook
nest_asyncio.apply()

```

## Helper File [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#helper-file "Permanent link")

We will use some JS code for this tutorial, which you should place in a file called `mark_page.js` in the same directory as the notebook you are running this tutorial from.

Show/Hide JS Code

```
    const customCSS = `
        ::-webkit-scrollbar {
            width: 10px;
        }
        ::-webkit-scrollbar-track {
            background: #27272a;
        }
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 0.375rem;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    `;

    const styleTag = document.createElement("style");
    styleTag.textContent = customCSS;
    document.head.append(styleTag);

    let labels = [];

    function unmarkPage() {
    // Unmark page logic
    for (const label of labels) {
        document.body.removeChild(label);
    }
    labels = [];
    }

    function markPage() {
    unmarkPage();

    var bodyRect = document.body.getBoundingClientRect();

    var items = Array.prototype.slice
        .call(document.querySelectorAll("*"))
        .map(function (element) {
        var vw = Math.max(
            document.documentElement.clientWidth || 0,
            window.innerWidth || 0
        );
        var vh = Math.max(
            document.documentElement.clientHeight || 0,
            window.innerHeight || 0
        );
        var textualContent = element.textContent.trim().replace(/\s{2,}/g, " ");
        var elementType = element.tagName.toLowerCase();
        var ariaLabel = element.getAttribute("aria-label") || "";

        var rects = [...element.getClientRects()]
            .filter((bb) => {
            var center_x = bb.left + bb.width / 2;
            var center_y = bb.top + bb.height / 2;
            var elAtCenter = document.elementFromPoint(center_x, center_y);

            return elAtCenter === element || element.contains(elAtCenter);
            })
            .map((bb) => {
            const rect = {
                left: Math.max(0, bb.left),
                top: Math.max(0, bb.top),
                right: Math.min(vw, bb.right),
                bottom: Math.min(vh, bb.bottom),
            };
            return {
                ...rect,
                width: rect.right - rect.left,
                height: rect.bottom - rect.top,
            };
            });

        var area = rects.reduce((acc, rect) => acc + rect.width * rect.height, 0);

        return {
            element: element,
            include:
            element.tagName === "INPUT" ||
            element.tagName === "TEXTAREA" ||
            element.tagName === "SELECT" ||
            element.tagName === "BUTTON" ||
            element.tagName === "A" ||
            element.onclick != null ||
            window.getComputedStyle(element).cursor == "pointer" ||
            element.tagName === "IFRAME" ||
            element.tagName === "VIDEO",
            area,
            rects,
            text: textualContent,
            type: elementType,
            ariaLabel: ariaLabel,
        };
        })
        .filter((item) => item.include && item.area >= 20);

    // Only keep inner clickable items
    items = items.filter(
        (x) => !items.some((y) => x.element.contains(y.element) && !(x == y))
    );

    // Function to generate random colors
    function getRandomColor() {
        var letters = "0123456789ABCDEF";
        var color = "#";
        for (var i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    // Lets create a floating border on top of these elements that will always be visible
    items.forEach(function (item, index) {
        item.rects.forEach((bbox) => {
        newElement = document.createElement("div");
        var borderColor = getRandomColor();
        newElement.style.outline = `2px dashed ${borderColor}`;
        newElement.style.position = "fixed";
        newElement.style.left = bbox.left + "px";
        newElement.style.top = bbox.top + "px";
        newElement.style.width = bbox.width + "px";
        newElement.style.height = bbox.height + "px";
        newElement.style.pointerEvents = "none";
        newElement.style.boxSizing = "border-box";
        newElement.style.zIndex = 2147483647;
        // newElement.style.background = `${borderColor}80`;

        // Add floating label at the corner
        var label = document.createElement("span");
        label.textContent = index;
        label.style.position = "absolute";
        // These we can tweak if we want
        label.style.top = "-19px";
        label.style.left = "0px";
        label.style.background = borderColor;
        // label.style.background = "black";
        label.style.color = "white";
        label.style.padding = "2px 4px";
        label.style.fontSize = "12px";
        label.style.borderRadius = "2px";
        newElement.appendChild(label);

        document.body.appendChild(newElement);
        labels.push(newElement);
        // item.element.setAttribute("-ai-label", label.textContent);
        });
    });
    const coordinates = items.flatMap((item) =>
        item.rects.map(({ left, top, width, height }) => ({
        x: (left + left + width) / 2,
        y: (top + top + height) / 2,
        type: item.type,
        text: item.text,
        ariaLabel: item.ariaLabel,
        }))
    );
    return coordinates;
    }

```

## Define graph [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#define-graph "Permanent link")

### Define graph state [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#define-graph-state "Permanent link")

The state provides the inputs to each node in the graph.

In our case, the agent will track the webpage object (within the browser), annotated images + bounding boxes, the user's initial request, and the messages containing the agent scratchpad, system prompt, and other information.

API Reference: [BaseMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.base.BaseMessage.html) \| [SystemMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.system.SystemMessage.html)

```md-code__content
from typing import List, Optional
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from playwright.async_api import Page

class BBox(TypedDict):
    x: float
    y: float
    text: str
    type: str
    ariaLabel: str

class Prediction(TypedDict):
    action: str
    args: Optional[List[str]]

# This represents the state of the agent
# as it proceeds through execution
class AgentState(TypedDict):
    page: Page  # The Playwright web page lets us interact with the web environment
    input: str  # User request
    img: str  # b64 encoded screenshot
    bboxes: List[BBox]  # The bounding boxes from the browser annotation function
    prediction: Prediction  # The Agent's output
    # A system message (or messages) containing the intermediate steps
    scratchpad: List[BaseMessage]
    observation: str  # The most recent response from a tool

```

### Define tools [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#define-tools "Permanent link")

The agent has 6 simple tools:

1. Click (at labeled box)
2. Type
3. Scroll
4. Wait
5. Go back
6. Go to search engine (Google)

We define them below here as functions:

```md-code__content
import asyncio
import platform

async def click(state: AgentState):
    # - Click [Numerical_Label]
    page = state["page"]
    click_args = state["prediction"]["args"]
    if click_args is None or len(click_args) != 1:
        return f"Failed to click bounding box labeled as number {click_args}"
    bbox_id = click_args[0]
    bbox_id = int(bbox_id)
    try:
        bbox = state["bboxes"][bbox_id]
    except Exception:
        return f"Error: no bbox for : {bbox_id}"
    x, y = bbox["x"], bbox["y"]
    await page.mouse.click(x, y)
    # TODO: In the paper, they automatically parse any downloaded PDFs
    # We could add something similar here as well and generally
    # improve response format.
    return f"Clicked {bbox_id}"

async def type_text(state: AgentState):
    page = state["page"]
    type_args = state["prediction"]["args"]
    if type_args is None or len(type_args) != 2:
        return (
            f"Failed to type in element from bounding box labeled as number {type_args}"
        )
    bbox_id = type_args[0]
    bbox_id = int(bbox_id)
    bbox = state["bboxes"][bbox_id]
    x, y = bbox["x"], bbox["y"]
    text_content = type_args[1]
    await page.mouse.click(x, y)
    # Check if MacOS
    select_all = "Meta+A" if platform.system() == "Darwin" else "Control+A"
    await page.keyboard.press(select_all)
    await page.keyboard.press("Backspace")
    await page.keyboard.type(text_content)
    await page.keyboard.press("Enter")
    return f"Typed {text_content} and submitted"

async def scroll(state: AgentState):
    page = state["page"]
    scroll_args = state["prediction"]["args"]
    if scroll_args is None or len(scroll_args) != 2:
        return "Failed to scroll due to incorrect arguments."

    target, direction = scroll_args

    if target.upper() == "WINDOW":
        # Not sure the best value for this:
        scroll_amount = 500
        scroll_direction = (
            -scroll_amount if direction.lower() == "up" else scroll_amount
        )
        await page.evaluate(f"window.scrollBy(0, {scroll_direction})")
    else:
        # Scrolling within a specific element
        scroll_amount = 200
        target_id = int(target)
        bbox = state["bboxes"][target_id]
        x, y = bbox["x"], bbox["y"]
        scroll_direction = (
            -scroll_amount if direction.lower() == "up" else scroll_amount
        )
        await page.mouse.move(x, y)
        await page.mouse.wheel(0, scroll_direction)

    return f"Scrolled {direction} in {'window' if target.upper() == 'WINDOW' else 'element'}"

async def wait(state: AgentState):
    sleep_time = 5
    await asyncio.sleep(sleep_time)
    return f"Waited for {sleep_time}s."

async def go_back(state: AgentState):
    page = state["page"]
    await page.go_back()
    return f"Navigated back a page to {page.url}."

async def to_google(state: AgentState):
    page = state["page"]
    await page.goto("https://www.google.com/")
    return "Navigated to google.com."

```

### Define Agent [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#define-agent "Permanent link")

The agent is driven by a multi-modal model and decides the action to take for each step. It is composed of a few runnable objects:

1. A `mark_page` function to annotate the current page with bounding boxes
2. A prompt to hold the user question, annotated image, and agent scratchpad
3. GPT-4V to decide the next steps
4. Parsing logic to extract the action

Let's first define the annotation step:

#### Browser Annotations [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#browser-annotations "Permanent link")

This function annotates all buttons, inputs, text areas, etc. with numbered bounding boxes. GPT-4V then just has to refer to a bounding box
when taking actions, reducing the complexity of the overall task.

API Reference: [chain](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.chain.html)

```md-code__content
import base64

from langchain_core.runnables import chain as chain_decorator

# Some javascript we will run on each step
# to take a screenshot of the page, select the
# elements to annotate, and add bounding boxes
with open("mark_page.js") as f:
    mark_page_script = f.read()

@chain_decorator
async def mark_page(page):
    await page.evaluate(mark_page_script)
    for _ in range(10):
        try:
            bboxes = await page.evaluate("markPage()")
            break
        except Exception:
            # May be loading...
            asyncio.sleep(3)
    screenshot = await page.screenshot()
    # Ensure the bboxes don't follow us around
    await page.evaluate("unmarkPage()")
    return {
        "img": base64.b64encode(screenshot).decode(),
        "bboxes": bboxes,
    }

```

#### Agent definition [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#agent-definition "Permanent link")

Now we'll compose this function with the prompt, llm and output parser to complete our agent.

API Reference: [StrOutputParser](https://python.langchain.com/api_reference/core/output_parsers/langchain_core.output_parsers.string.StrOutputParser.html) \| [RunnablePassthrough](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.passthrough.RunnablePassthrough.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html)

```md-code__content
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

async def annotate(state):
    marked_page = await mark_page.with_retry().ainvoke(state["page"])
    return {**state, **marked_page}

def format_descriptions(state):
    labels = []
    for i, bbox in enumerate(state["bboxes"]):
        text = bbox.get("ariaLabel") or ""
        if not text.strip():
            text = bbox["text"]
        el_type = bbox.get("type")
        labels.append(f'{i} (<{el_type}/>): "{text}"')
    bbox_descriptions = "\nValid Bounding Boxes:\n" + "\n".join(labels)
    return {**state, "bbox_descriptions": bbox_descriptions}

def parse(text: str) -> dict:
    action_prefix = "Action: "
    if not text.strip().split("\n")[-1].startswith(action_prefix):
        return {"action": "retry", "args": f"Could not parse LLM Output: {text}"}
    action_block = text.strip().split("\n")[-1]

    action_str = action_block[len(action_prefix) :]
    split_output = action_str.split(" ", 1)
    if len(split_output) == 1:
        action, action_input = split_output[0], None
    else:
        action, action_input = split_output
    action = action.strip()
    if action_input is not None:
        action_input = [\
            inp.strip().strip("[]") for inp in action_input.strip().split(";")\
        ]
    return {"action": action, "args": action_input}

# Will need a later version of langchain to pull
# this image prompt template
prompt = hub.pull("wfh/web-voyager")

```

```md-code__content
llm = ChatOpenAI(model="gpt-4-vision-preview", max_tokens=4096)
agent = annotate | RunnablePassthrough.assign(
    prediction=format_descriptions | prompt | llm | StrOutputParser() | parse
)

```

## Compile the graph [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#compile-the-graph "Permanent link")

We've created most of the important logic. We have one more function to define that will help us update the graph state after a tool is called.

```md-code__content
import re

def update_scratchpad(state: AgentState):
    """After a tool is invoked, we want to update
    the scratchpad so the agent is aware of its previous steps"""
    old = state.get("scratchpad")
    if old:
        txt = old[0].content
        last_line = txt.rsplit("\n", 1)[-1]
        step = int(re.match(r"\d+", last_line).group()) + 1
    else:
        txt = "Previous action observations:\n"
        step = 1
    txt += f"\n{step}. {state['observation']}"

    return {**state, "scratchpad": [SystemMessage(content=txt)]}

```

Now we can compose everything into a graph:

API Reference: [RunnableLambda](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.RunnableLambda.html) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph)

```md-code__content
from langchain_core.runnables import RunnableLambda

from langgraph.graph import END, START, StateGraph

graph_builder = StateGraph(AgentState)

graph_builder.add_node("agent", agent)
graph_builder.add_edge(START, "agent")

graph_builder.add_node("update_scratchpad", update_scratchpad)
graph_builder.add_edge("update_scratchpad", "agent")

tools = {
    "Click": click,
    "Type": type_text,
    "Scroll": scroll,
    "Wait": wait,
    "GoBack": go_back,
    "Google": to_google,
}

for node_name, tool in tools.items():
    graph_builder.add_node(
        node_name,
        # The lambda ensures the function's string output is mapped to the "observation"
        # key in the AgentState
        RunnableLambda(tool) | (lambda observation: {"observation": observation}),
    )
    # Always return to the agent (by means of the update-scratchpad node)
    graph_builder.add_edge(node_name, "update_scratchpad")

def select_tool(state: AgentState):
    # Any time the agent completes, this function
    # is called to route the output to a tool or
    # to the end user.
    action = state["prediction"]["action"]
    if action == "ANSWER":
        return END
    if action == "retry":
        return "agent"
    return action

graph_builder.add_conditional_edges("agent", select_tool)

graph = graph_builder.compile()

```

## Use the graph [¶](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/\#use-the-graph "Permanent link")

Now that we've created the whole agent executor, we can run it on a few questions! We'll start our browser at "google.com" and then let it control the rest.

Below is a helper function to help print out the steps to the notebook (and display the intermediate screenshots).

```md-code__content
from IPython import display
from playwright.async_api import async_playwright

browser = await async_playwright().start()
# We will set headless=False so we can watch the agent navigate the web.
browser = await browser.chromium.launch(headless=False, args=None)
page = await browser.new_page()
_ = await page.goto("https://www.google.com")

async def call_agent(question: str, page, max_steps: int = 150):
    event_stream = graph.astream(
        {
            "page": page,
            "input": question,
            "scratchpad": [],
        },
        {
            "recursion_limit": max_steps,
        },
    )
    final_answer = None
    steps = []
    async for event in event_stream:
        # We'll display an event stream here
        if "agent" not in event:
            continue
        pred = event["agent"].get("prediction") or {}
        action = pred.get("action")
        action_input = pred.get("args")
        display.clear_output(wait=False)
        steps.append(f"{len(steps) + 1}. {action}: {action_input}")
        print("\n".join(steps))
        display.display(display.Image(base64.b64decode(event["agent"]["img"])))
        if "ANSWER" in action:
            final_answer = action_input[0]
            break
    return final_answer

```

```md-code__content
res = await call_agent("Could you explain the WebVoyager paper (on arxiv)?", page)
print(f"Final response: {res}")

```

```md-code__content
1. Type: ['7', 'WebVoyager paper arXiv']
2. Click: ['32']
3. Click: ['3']
4. ANSWER;: ['The "WebVoyager" paper discusses the development of an end-to-end web agent that leverages large multimodal models. The abstract highlights the importance of such agents in automating complex tasks on the web, which remains a challenging domain due to the heterogeneity in structure and the semantic gap between humans and machines. The paper proposes a solution that combines neural symbolic models and multimodal web environments, aiming to advance the capabilities of these agents to perform web browsing tasks effectively. Further details would require a more in-depth analysis of the paper\'s content beyond the abstract.']

```

![](<Base64-Image-Removed>)

```md-code__content
Final response: The "WebVoyager" paper discusses the development of an end-to-end web agent that leverages large multimodal models. The abstract highlights the importance of such agents in automating complex tasks on the web, which remains a challenging domain due to the heterogeneity in structure and the semantic gap between humans and machines. The paper proposes a solution that combines neural symbolic models and multimodal web environments, aiming to advance the capabilities of these agents to perform web browsing tasks effectively. Further details would require a more in-depth analysis of the paper's content beyond the abstract.

```

```md-code__content
res = await call_agent(
    "Please explain the today's XKCD comic for me. Why is it funny?", page
)
print(f"Final response: {res}")

```

```md-code__content
1. retry: Could not parse LLM Output: I'm sorry, but the image provided does not contain an XKCD comic. The image shows a page from a scientific paper titled "WebVoyager 2: Building an End-to-End Web Agent with Large Multimodal Models." If you provide the XKCD comic you're referring to, I'd be happy to explain the humor in it.
2. retry: Could not parse LLM Output: I'm sorry, but I cannot assist with that request.
3. Google: None
4. Type: ['6', 'xkcd.com']
5. Click: ['25']
6. ANSWER;: ['The XKCD comic titled "Relationship Advice" pokes fun at the sometimes exaggerated way people talk about the challenges of relationships. It starts with one character stating that relationships require constant work and are like a job, which is a common sentiment. However, the other character takes this comparison to an extreme, calling it a "grueling ordeal" and a "crushing burden," which humorously exaggerates the difficulties of maintaining a relationship. The punchline comes when, after this escalation, the second character insists they\'re fine and that it\'s all normal, which satirizes how people might downplay their struggles to appear in control or deny the extent of their challenges. The humor lies in the hyperbole and the relatable nature of discussing relationship difficulties, as well as the contrast between the characters\' statements and the insistence that everything is okay.']

```

![](<Base64-Image-Removed>)

```md-code__content
Final response: The XKCD comic titled "Relationship Advice" pokes fun at the sometimes exaggerated way people talk about the challenges of relationships. It starts with one character stating that relationships require constant work and are like a job, which is a common sentiment. However, the other character takes this comparison to an extreme, calling it a "grueling ordeal" and a "crushing burden," which humorously exaggerates the difficulties of maintaining a relationship. The punchline comes when, after this escalation, the second character insists they're fine and that it's all normal, which satirizes how people might downplay their struggles to appear in control or deny the extent of their challenges. The humor lies in the hyperbole and the relatable nature of discussing relationship difficulties, as well as the contrast between the characters' statements and the insistence that everything is okay.

```

```md-code__content
res = await call_agent("What are the latest blog posts from langchain?", page)
print(f"Final response: {res}")

```

```md-code__content
1. Google: None
2. Type: ['6', 'latest blog posts from langchain']
3. Click: ['27']
4. Click: ['14']
5. Click: ['0']
6. retry: Could not parse LLM Output: Thought: The latest blog posts from Langchain are displayed on the right side of the screen with titles and reading time. I will provide the titles of the featured blog posts as seen on the screen.

Action: ANSWER; The latest blog posts from Langchain are:
1. OpenGPTs - 7 min read
2. LangGraph: Multi-Agent Workflows - 6 min read
3. LangGraph - 7 min read
4. LangChain v0.1.0 - 10 min read
7. ANSWER;: ['The latest blog posts from Langchain are "OpenGPTs," "LangGraph: Multi-Agent Workflows," and "LangGraph."']

```

![](<Base64-Image-Removed>)

```md-code__content
Final response: The latest blog posts from Langchain are "OpenGPTs," "LangGraph: Multi-Agent Workflows," and "LangGraph."

```

```md-code__content
res = await call_agent(
    "Could you check google maps to see when i should leave to get to SFO by 7 o'clock? starting from SF downtown.",
    page,
)
print(f"Final response: {res}")

```

```md-code__content
1. Google: None
2. Type: ['6', 'Google Maps']
3. Click: ['0']
4. Click: ['0']
5. Wait: None
6. Click: ['22']
7. Click: ['0']
8. Click: ['2']
9. Type: ['0', 'San Francisco downtown to SFO']
10. Click: ['1']
11. Click: ['2']
12. Type: ['8', 'San Francisco International Airport SFO']
13. Click: ['14']
14. Click: ['28']
15. Scroll: ['WINDOW', 'up']
16. Scroll: ['WINDOW', 'up']
17. Click: ['10']
18. Click: ['28']
19. ANSWER;: ['To arrive at San Francisco International Airport (SFO) by 7:00 AM starting from downtown San Francisco, you should leave by 6:46 AM according to the current Google Maps information, which estimates a 44-minute travel time.']

```

![](<Base64-Image-Removed>)

```md-code__content
Final response: To arrive at San Francisco International Airport (SFO) by 7:00 AM starting from downtown San Francisco, you should leave by 6:46 AM according to the current Google Maps information, which estimates a 44-minute travel time.

```

## Comments

giscus

#### [3 reactions](https://github.com/langchain-ai/langgraph/discussions/627)

❤️1🚀2

#### [6 comments](https://github.com/langchain-ai/langgraph/discussions/627)

#### ·

#### 4 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@lukas90275](https://avatars.githubusercontent.com/u/13397133?v=4)lukas90275](https://github.com/lukas90275) [Jun 9, 2024](https://github.com/langchain-ai/langgraph/discussions/627#discussioncomment-9717666)

edited

Hi, I'm getting an error when running the notebook.The only change I made was replacing:

llm = ChatOpenAI(model="gpt-4-vision-preview", max\_tokens=4096)

with

```notranslate
os.environ["OPENAI_API_KEY"] = "NA"
llm = ChatOpenAI(
    model = "llava:7b",
    base_url = "http://localhost:11434/v1")

Llava 7b is an open source vision model which should work similarly [worse ofc] to gpt4 vision: https://ollama.com/blog/vision-models

I also didn't implement Langsmith Tracing, although that's optional.

However that gives the following error:
BadRequestError: Error code: 400 - {'error': {'message': 'json: cannot unmarshal array into Go struct field Message.messages.content of type string', 'type': 'invalid_request_error', 'param': None, 'code': None}}

Any ideas?

Here's the traceback btw:

---------------------------------------------------------------------------
BadRequestError                           Traceback (most recent call last)
Cell In[13], line 1
----> 1 res = await call_agent("Could you explain the WebVoyager paper (on arxiv)?", page)
      2 print(f"Final response: {res}")

Cell In[12], line 25
     23 final_answer = None
     24 steps = []
---> 25 async for event in event_stream:
     26     # We'll display an event stream here
     27     if "agent" not in event:
     28         continue

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langgraph/pregel/__init__.py:1292, in Pregel.astream(self, input, config, stream_mode, output_keys, input_keys, interrupt_before, interrupt_after, debug)
   1289         del fut, task
   1291 # panic on failure or timeout
-> 1292 _panic_or_proceed(done, inflight, step)
   1293 # don't keep futures around in memory longer than needed
   1294 del done, inflight, futures

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langgraph/pregel/__init__.py:1489, in _panic_or_proceed(done, inflight, step)
   1487             inflight.pop().cancel()
   1488         # raise the exception
-> 1489         raise exc
   1491 if inflight:
   1492     # if we got here means we timed out
   1493     while inflight:
   1494         # cancel all pending tasks

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/asyncio/tasks.py:277, in Task.__step(***failed resolving arguments***)
    273 try:
    274     if exc is None:
    275         # We use the `send` method directly, because coroutines
    276         # don't have `__iter__` and `__next__` methods.
--> 277         result = coro.send(None)
    278     else:
    279         result = coro.throw(exc)

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langgraph/pregel/retry.py:114, in arun_with_retry(task, retry_policy, stream)
    112         pass
    113 else:
--> 114     await task.proc.ainvoke(task.input, task.config)
    115 # if successful, end
    116 break

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langchain_core/runnables/base.py:2533, in RunnableSequence.ainvoke(self, input, config, **kwargs)
   2531             input = await step.ainvoke(input, config, **kwargs)
   2532         else:
-> 2533             input = await step.ainvoke(input, config)
   2534 # finish the root run
   2535 except BaseException as e:

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langchain_core/runnables/passthrough.py:497, in RunnableAssign.ainvoke(self, input, config, **kwargs)
    491 async def ainvoke(
    492     self,
    493     input: Dict[str, Any],
    494     config: Optional[RunnableConfig] = None,
    495     **kwargs: Any,
    496 ) -> Dict[str, Any]:
--> 497     return await self._acall_with_config(self._ainvoke, input, config, **kwargs)

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langchain_core/runnables/base.py:1646, in Runnable._acall_with_config(self, func, input, config, run_type, **kwargs)
   1642 coro = acall_func_with_variable_args(
   1643     func, input, config, run_manager, **kwargs
   1644 )
   1645 if accepts_context(asyncio.create_task):
-> 1646     output: Output = await asyncio.create_task(coro, context=context)  # type: ignore
   1647 else:
   1648     output = await coro

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/asyncio/futures.py:287, in Future.__await__(self)
    285 if not self.done():
    286     self._asyncio_future_blocking = True
--> 287     yield self  # This tells Task to wait for completion.
    288 if not self.done():
    289     raise RuntimeError("await wasn't used with future")

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/asyncio/tasks.py:349, in Task.__wakeup(self, future)
    347 def __wakeup(self, future):
    348     try:
--> 349         future.result()
    350     except BaseException as exc:
    351         # This may also be a cancellation.
    352         self.__step(exc)

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/asyncio/futures.py:203, in Future.result(self)
    201 self.__log_traceback = False
    202 if self._exception is not None:
--> 203     raise self._exception.with_traceback(self._exception_tb)
    204 return self._result

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/asyncio/tasks.py:277, in Task.__step(***failed resolving arguments***)
    273 try:
    274     if exc is None:
    275         # We use the `send` method directly, because coroutines
    276         # don't have `__iter__` and `__next__` methods.
--> 277         result = coro.send(None)
    278     else:
    279         result = coro.throw(exc)

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langchain_core/runnables/passthrough.py:484, in RunnableAssign._ainvoke(self, input, run_manager, config, **kwargs)
    471 async def _ainvoke(
    472     self,
    473     input: Dict[str, Any],
   (...)
    476     **kwargs: Any,
    477 ) -> Dict[str, Any]:
    478     assert isinstance(
    479         input, dict
    480     ), "The input to RunnablePassthrough.assign() must be a dict."
    482     return {
    483         **input,
--> 484         **await self.mapper.ainvoke(
    485             input,
    486             patch_config(config, callbacks=run_manager.get_child()),
    487             **kwargs,
    488         ),
    489     }

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langchain_core/runnables/base.py:3170, in RunnableParallel.ainvoke(self, input, config, **kwargs)
   3167 try:
   3168     # copy to avoid issues from the caller mutating the steps during invoke()
   3169     steps = dict(self.steps__)
-> 3170     results = await asyncio.gather(
   3171         *(
   3172             step.ainvoke(
   3173                 input,
   3174                 # mark each step as a child run
   3175                 patch_config(
   3176                     config, callbacks=run_manager.get_child(f"map:key:{key}")
   3177                 ),
   3178             )
   3179             for key, step in steps.items()
   3180         )
   3181     )
   3182     output = {key: value for key, value in zip(steps, results)}
   3183 # finish the root run

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/asyncio/tasks.py:349, in Task.__wakeup(self, future)
    347 def __wakeup(self, future):
    348     try:
--> 349         future.result()
    350     except BaseException as exc:
    351         # This may also be a cancellation.
    352         self.__step(exc)

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/asyncio/tasks.py:277, in Task.__step(***failed resolving arguments***)
    273 try:
    274     if exc is None:
    275         # We use the `send` method directly, because coroutines
    276         # don't have `__iter__` and `__next__` methods.
--> 277         result = coro.send(None)
    278     else:
    279         result = coro.throw(exc)

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langchain_core/runnables/base.py:2533, in RunnableSequence.ainvoke(self, input, config, **kwargs)
   2531             input = await step.ainvoke(input, config, **kwargs)
   2532         else:
-> 2533             input = await step.ainvoke(input, config)
   2534 # finish the root run
   2535 except BaseException as e:

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py:191, in BaseChatModel.ainvoke(self, input, config, stop, **kwargs)
    182 async def ainvoke(
    183     self,
    184     input: LanguageModelInput,
   (...)
    188     **kwargs: Any,
    189 ) -> BaseMessage:
    190     config = ensure_config(config)
--> 191     llm_result = await self.agenerate_prompt(
    192         [self._convert_input(input)],
    193         stop=stop,
    194         callbacks=config.get("callbacks"),
    195         tags=config.get("tags"),
    196         metadata=config.get("metadata"),
    197         run_name=config.get("run_name"),
    198         run_id=config.pop("run_id", None),
    199         **kwargs,
    200     )
    201     return cast(ChatGeneration, llm_result.generations[0][0]).message

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py:609, in BaseChatModel.agenerate_prompt(self, prompts, stop, callbacks, **kwargs)
    601 async def agenerate_prompt(
    602     self,
    603     prompts: List[PromptValue],
   (...)
    606     **kwargs: Any,
    607 ) -> LLMResult:
    608     prompt_messages = [p.to_messages() for p in prompts]
--> 609     return await self.agenerate(
    610         prompt_messages, stop=stop, callbacks=callbacks, **kwargs
    611     )

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py:569, in BaseChatModel.agenerate(self, messages, stop, callbacks, tags, metadata, run_name, run_id, **kwargs)
    556     if run_managers:
    557         await asyncio.gather(
    558             *[\
    559                 run_manager.on_llm_end(\
   (...)\
    567             ]
    568         )
--> 569     raise exceptions[0]
    570 flattened_outputs = [\
    571     LLMResult(generations=[res.generations], llm_output=res.llm_output)  # type: ignore[list-item, union-attr]\
    572     for res in results\
    573 ]
    574 llm_output = self._combine_llm_outputs([res.llm_output for res in results])  # type: ignore[union-attr]

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/asyncio/tasks.py:277, in Task.__step(***failed resolving arguments***)
    273 try:
    274     if exc is None:
    275         # We use the `send` method directly, because coroutines
    276         # don't have `__iter__` and `__next__` methods.
--> 277         result = coro.send(None)
    278     else:
    279         result = coro.throw(exc)

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py:754, in BaseChatModel._agenerate_with_cache(self, messages, stop, run_manager, **kwargs)
    752 else:
    753     if inspect.signature(self._agenerate).parameters.get("run_manager"):
--> 754         result = await self._agenerate(
    755             messages, stop=stop, run_manager=run_manager, **kwargs
    756         )
    757     else:
    758         result = await self._agenerate(messages, stop=stop, **kwargs)

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/langchain_openai/chat_models/base.py:657, in BaseChatOpenAI._agenerate(self, messages, stop, run_manager, **kwargs)
    655 message_dicts, params = self._create_message_dicts(messages, stop)
    656 params = {**params, **kwargs}
--> 657 response = await self.async_client.create(messages=message_dicts, **params)
    658 return self._create_chat_result(response)

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/openai/resources/chat/completions.py:1214, in AsyncCompletions.create(self, messages, model, frequency_penalty, function_call, functions, logit_bias, logprobs, max_tokens, n, parallel_tool_calls, presence_penalty, response_format, seed, stop, stream, stream_options, temperature, tool_choice, tools, top_logprobs, top_p, user, extra_headers, extra_query, extra_body, timeout)
   1181 @required_args(["messages", "model"], ["messages", "model", "stream"])
   1182 async def create(
   1183     self,
   (...)
   1212     timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
   1213 ) -> ChatCompletion | AsyncStream[ChatCompletionChunk]:
-> 1214     return await self._post(
   1215         "/chat/completions",
   1216         body=await async_maybe_transform(
   1217             {
   1218                 "messages": messages,
   1219                 "model": model,
   1220                 "frequency_penalty": frequency_penalty,
   1221                 "function_call": function_call,
   1222                 "functions": functions,
   1223                 "logit_bias": logit_bias,
   1224                 "logprobs": logprobs,
   1225                 "max_tokens": max_tokens,
   1226                 "n": n,
   1227                 "parallel_tool_calls": parallel_tool_calls,
   1228                 "presence_penalty": presence_penalty,
   1229                 "response_format": response_format,
   1230                 "seed": seed,
   1231                 "stop": stop,
   1232                 "stream": stream,
   1233                 "stream_options": stream_options,
   1234                 "temperature": temperature,
   1235                 "tool_choice": tool_choice,
   1236                 "tools": tools,
   1237                 "top_logprobs": top_logprobs,
   1238                 "top_p": top_p,
   1239                 "user": user,
   1240             },
   1241             completion_create_params.CompletionCreateParams,
   1242         ),
   1243         options=make_request_options(
   1244             extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
   1245         ),
   1246         cast_to=ChatCompletion,
   1247         stream=stream or False,
   1248         stream_cls=AsyncStream[ChatCompletionChunk],
   1249     )

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/openai/_base_client.py:1790, in AsyncAPIClient.post(self, path, cast_to, body, files, options, stream, stream_cls)
   1776 async def post(
   1777     self,
   1778     path: str,
   (...)
   1785     stream_cls: type[_AsyncStreamT] | None = None,
   1786 ) -> ResponseT | _AsyncStreamT:
   1787     opts = FinalRequestOptions.construct(
   1788         method="post", url=path, json_data=body, files=await async_to_httpx_files(files), **options
   1789     )
-> 1790     return await self.request(cast_to, opts, stream=stream, stream_cls=stream_cls)

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/openai/_base_client.py:1493, in AsyncAPIClient.request(self, cast_to, options, stream, stream_cls, remaining_retries)
   1484 async def request(
   1485     self,
   1486     cast_to: Type[ResponseT],
   (...)
   1491     remaining_retries: Optional[int] = None,
   1492 ) -> ResponseT | _AsyncStreamT:
-> 1493     return await self._request(
   1494         cast_to=cast_to,
   1495         options=options,
   1496         stream=stream,
   1497         stream_cls=stream_cls,
   1498         remaining_retries=remaining_retries,
   1499     )

File ~/Desktop/cs/FoodBank/.conda/lib/python3.11/site-packages/openai/_base_client.py:1584, in AsyncAPIClient._request(self, cast_to, options, stream, stream_cls, remaining_retries)
   1581         await err.response.aread()
   1583     log.debug("Re-raising status error")
-> 1584     raise self._make_status_error_from_response(err.response) from None
   1586 return await self._process_response(
   1587     cast_to=cast_to,
   1588     options=options,
   (...)
   1591     stream_cls=stream_cls,
   1592 )

BadRequestError: Error code: 400 - {'error': {'message': 'json: cannot unmarshal array into Go struct field Message.messages.content of type string', 'type': 'invalid_request_error', 'param': None, 'code': None}}

```

1

1 reply

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [Jun 10, 2024](https://github.com/langchain-ai/langgraph/discussions/627#discussioncomment-9728456)

Contributor

Hmm - i don't believe we create any go structs in the notebook - I haven't looked in depth + am less familiar with Ollama's internal APIs but seems like it may be returning a Go object via their API that then breaks when using the openai client?

[![@AnupamGaur](https://avatars.githubusercontent.com/u/86046454?v=4)AnupamGaur](https://github.com/AnupamGaur) [Nov 30, 2024](https://github.com/langchain-ai/langgraph/discussions/627#discussioncomment-11423640)

llm = ChatOpenAI(

model = "llava:7b",

base\_url = " [http://localhost:11434/v1](http://localhost:11434/v1)")

Hi [@lukas90275](https://github.com/lukas90275)

Are you sure you can use llava with OpenAI?

1

0 replies

[![@Santhosraj](https://avatars.githubusercontent.com/u/108875935?u=172d06a8dfec810bc8af8f7719cde40e8d1e8005&v=4)Santhosraj](https://github.com/Santhosraj) [Jan 23](https://github.com/langchain-ai/langgraph/discussions/627#discussioncomment-11931988)

Help !! I am getting a error at the last cell :

code :

from IPython import display

from playwright.async\_api import async\_playwright

browser = await async\_playwright().start()

# We will set headless=False so we can watch the agent navigate the web.

browser = await browser.chromium.launch(headless=False, args=None)

page = await browser.new\_page()

\_ = await page.goto(" [https://www.google.com](https://www.google.com/)")

async def call\_agent(question: str, page, max\_steps: int = 150):

event\_stream = graph.astream(

{

"page": page,

"input": question,

"scratchpad": \[\],

},

{

"recursion\_limit": max\_steps,

},

)

final\_answer = None

steps = \[\]

async for event in event\_stream:

\# We'll display an event stream here

if "agent" not in event:

continue

pred = event\["agent"\].get("prediction") or {}

action = pred.get("action")

action\_input = pred.get("args")

display.clear\_output(wait=False)

steps.append(f"{len(steps) + 1}. {action}: {action\_input}")

print("\\n".join(steps))

display.display(display.Image(base64.b64decode(event\["agent"\]\["img"\])))

if "ANSWER" in action:

final\_answer = action\_input\[0\]

break

return final\_answer

```notranslate
error:
NotImplementedError                       Traceback (most recent call last)

```

Cell In\[12\], line 4

1 from IPython import display

2 from playwright.async\_api import async\_playwright

----\> 4 browser = await async\_playwright().start()

5 # We will set headless=False so we can watch the agent navigate the web.

6 browser = await browser.chromium.launch(headless=False, args=None)

File d:\\2025\\Study\\Jan\\Langgraph\\lc-academy-env\\Lib\\site-packages\\playwright\\async\_api\_context\_manager.py:51, in PlaywrightContextManager.start(self)

50 async def start(self) -> AsyncPlaywright:

---\> 51 return await self. **aenter**()

File d:\\2025\\Study\\Jan\\Langgraph\\lc-academy-env\\Lib\\site-packages\\playwright\\async\_api\_context\_manager.py:46, in PlaywrightContextManager. **aenter**(self)

44 if not playwright\_future.done():

45 playwright\_future.cancel()

---\> 46 playwright = AsyncPlaywright(next(iter(done)).result())

47 playwright.stop = self. **aexit** # type: ignore

48 return playwright

File ~\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\asyncio\\futures.py:203, in Future.result(self)

[201](https://file+.vscode-resource.vscode-cdn.net/d%3A/2025/Study/Jan/Langgraph/browse_ai/~/AppData/Local/Programs/Python/Python311/Lib/asyncio/futures.py:201) self.\_\_log\_traceback = False

[202](https://file+.vscode-resource.vscode-cdn.net/d%3A/2025/Study/Jan/Langgraph/browse_ai/~/AppData/Local/Programs/Python/Python311/Lib/asyncio/futures.py:202) if self.\_exception is not None:

--\> [203](https://file+.vscode-resource.vscode-cdn.net/d%3A/2025/Study/Jan/Langgraph/browse_ai/~/AppData/Local/Programs/Python/Python311/Lib/asyncio/futures.py:203) raise self.\_exception.with\_traceback(self.\_exception\_tb)

[204](https://file+.vscode-resource.vscode-cdn.net/d%3A/2025/Study/Jan/Langgraph/browse_ai/~/AppData/Local/Programs/Python/Python311/Lib/asyncio/futures.py:204) return self.\_result

...

[501](https://file+.vscode-resource.vscode-cdn.net/d%3A/2025/Study/Jan/Langgraph/browse_ai/~/AppData/Local/Programs/Python/Python311/Lib/asyncio/base_events.py:501) extra=None, \*\*kwargs):

[502](https://file+.vscode-resource.vscode-cdn.net/d%3A/2025/Study/Jan/Langgraph/browse_ai/~/AppData/Local/Programs/Python/Python311/Lib/asyncio/base_events.py:502) """Create subprocess transport."""

--\> [503](https://file+.vscode-resource.vscode-cdn.net/d%3A/2025/Study/Jan/Langgraph/browse_ai/~/AppData/Local/Programs/Python/Python311/Lib/asyncio/base_events.py:503) raise NotImplementedError

NotImplementedError:

Output is truncated. View as a scrollable element or open in a text editor. Adjust cell output settings...

1

0 replies

[![@cplusplusgoddess](https://avatars.githubusercontent.com/u/936058?u=e4668a3a0a997dea59bf151864b6fa68916d7330&v=4)cplusplusgoddess](https://github.com/cplusplusgoddess) [Feb 3](https://github.com/langchain-ai/langgraph/discussions/627#discussioncomment-12047198)

I received the following warning: /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages/langsmith/client.py:253: LangSmithMissingAPIKeyWarning: API key must be provided when using hosted LangSmith API

and I received the following error when running the agent:

NotFoundError: Error code: 404 - {'error': {'message': 'The model `gpt-4-vision-preview` has been deprecated, learn more here: [https://platform.openai.com/docs/deprecations](https://platform.openai.com/docs/deprecations)', 'type': 'invalid\_request\_error', 'param': None, 'code': 'model\_not\_found'}}

Seems the model you have specified is no longer an option.

2

2 replies

[![@jaames-bentley](https://avatars.githubusercontent.com/u/175034501?u=1b1e7a2a62189cdabb612861d18982e30ba81354&v=4)](https://github.com/jaames-bentley)

[jaames-bentley](https://github.com/jaames-bentley) [Feb 5](https://github.com/langchain-ai/langgraph/discussions/627#discussioncomment-12072680)

Looks like it was replaced by gpt-4o: [tldraw/make-real-starter#30 (comment)](https://github.com/tldraw/make-real-starter/issues/30#issuecomment-2176697263)

👀1

[![@cplusplusgoddess](https://avatars.githubusercontent.com/u/936058?u=e4668a3a0a997dea59bf151864b6fa68916d7330&v=4)](https://github.com/cplusplusgoddess)

[cplusplusgoddess](https://github.com/cplusplusgoddess) [Feb 5](https://github.com/langchain-ai/langgraph/discussions/627#discussioncomment-12075130)

How the heck did you find this area? Thank you! 🤙

[![@thrive2025](https://avatars.githubusercontent.com/u/199578916?v=4)thrive2025](https://github.com/thrive2025) [Feb 20](https://github.com/langchain-ai/langgraph/discussions/627#discussioncomment-12259433)

Could someone help explain why it is necessary or reasonable to wrap the tool observation into a system message? Based on my understanding, we should keep the tool observation as tool message. The corresponding implementation is inside update\_scratchpad function.

1

0 replies

[![@AncoPetiteMer](https://avatars.githubusercontent.com/u/165894997?v=4)AncoPetiteMer](https://github.com/AncoPetiteMer) [Mar 8](https://github.com/langchain-ai/langgraph/discussions/627#discussioncomment-12435623)

When I use template with only minor modifications (deprecated model and headless=True) I always got a capcha and model seems to be unable to resolve it, does it seem normal ?

Thanks 🙂

Logs:

18\. retry: Could not parse LLM Output: I'm unable to assist with CAPTCHA verifications. Could you complete it and let me know the results?

19\. retry: Could not parse LLM Output: I'm unable to help with the CAPTCHA, but you can proceed to verify it by selecting the appropriate images manually. Once you've done that, let me know if you need further assistance with the WebVoyager paper.

20\. retry: Could not parse LLM Output: I'm unable to interact with CAPTCHAs, but you can complete it by selecting the images with a fire hydrant.

1

1 reply

[![@Kotesh9177](https://avatars.githubusercontent.com/u/196038281?v=4)](https://github.com/Kotesh9177)

[Kotesh9177](https://github.com/Kotesh9177) [Mar 16](https://github.com/langchain-ai/langgraph/discussions/627#discussioncomment-12513760)

I am facing the same issue

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Fweb-navigation%2Fweb_voyager%2F)