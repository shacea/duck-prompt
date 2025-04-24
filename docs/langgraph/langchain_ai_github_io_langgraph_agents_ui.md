[Skip to content](https://langchain-ai.github.io/langgraph/agents/ui/#ui)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/agents/ui.md "Edit this page")

# UI [¶](https://langchain-ai.github.io/langgraph/agents/ui/\#ui "Permanent link")

You can use a prebuilt chat UI for interacting with any LangGraph agent through the [Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui). Using the [deployed version](https://agentchat.vercel.app/) is the quickest way to get started, and allows you to interact with both local and deployed graphs.

## Run agent in UI [¶](https://langchain-ai.github.io/langgraph/agents/ui/\#run-agent-in-ui "Permanent link")

First, set up LangGraph API server [locally](https://langchain-ai.github.io/langgraph/agents/deployment/#launch-langgraph-server-locally) or deploy your agent on [LangGraph Cloud](https://langchain-ai.github.io/langgraph/cloud/quick_start/).

Then, navigate to [Agent Chat UI](https://agentchat.vercel.app/), or clone the repository and [run the dev server locally](https://github.com/langchain-ai/agent-chat-ui?tab=readme-ov-file#setup):

Tip

UI has out-of-box support for rendering tool calls, and tool result messages. To customize what messages are shown, see the [Hiding Messages in the Chat](https://github.com/langchain-ai/agent-chat-ui?tab=readme-ov-file#hiding-messages-in-the-chat) section in the Agent Chat UI documentation.

## Add human-in-the-loop [¶](https://langchain-ai.github.io/langgraph/agents/ui/\#add-human-in-the-loop "Permanent link")

Agent Chat UI has full support for [human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/) workflows. To try it out, replace the agent code in `src/agent/graph.py` (from the [deployment](https://langchain-ai.github.io/langgraph/agents/deployment/) guide) with this [agent implementation](https://langchain-ai.github.io/langgraph/agents/human-in-the-loop/#using-with-agent-inbox):

Important

Agent Chat UI works best if your LangGraph agent interrupts using the [`HumanInterrupt` schema](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.interrupt.HumanInterrupt "<code class=\"doc-symbol doc-symbol-heading doc-symbol-class\"></code>            <span class=\"doc doc-object-name doc-class-name\">HumanInterrupt</span>"). If you do not use that schema, the Agent Chat UI will be able to render the input passed to the `interrupt` function, but it will not have full support for resuming your graph.

## Generative UI [¶](https://langchain-ai.github.io/langgraph/agents/ui/\#generative-ui "Permanent link")

You can also use generative UI in the Agent Chat UI.

Generative UI allows you to define [React](https://react.dev/) components, and push them to the UI from the LangGraph server. For more documentation on building generative UI LangGraph agents, read [these docs](https://langchain-ai.github.io/langgraph/cloud/how-tos/generative_ui_react/).

## Comments

giscus

#### 0 reactions

#### 0 comments

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fagents%2Fui%2F)