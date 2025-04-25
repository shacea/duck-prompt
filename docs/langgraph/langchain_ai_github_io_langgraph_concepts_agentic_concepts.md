[Skip to content](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/#agent-architectures)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/agentic_concepts.md "Edit this page")

# Agent architectures [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#agent-architectures "Permanent link")

Many LLM applications implement a particular control flow of steps before and / or after LLM calls. As an example, [RAG](https://github.com/langchain-ai/rag-from-scratch) performs retrieval of documents relevant to a user question, and passes those documents to an LLM in order to ground the model's response in the provided document context.

Instead of hard-coding a fixed control flow, we sometimes want LLM systems that can pick their own control flow to solve more complex problems! This is one definition of an [agent](https://blog.langchain.dev/what-is-an-agent/): _an agent is a system that uses an LLM to decide the control flow of an application._ There are many ways that an LLM can control application:

- An LLM can route between two potential paths
- An LLM can decide which of many tools to call
- An LLM can decide whether the generated answer is sufficient or more work is needed

As a result, there are many different types of [agent architectures](https://blog.langchain.dev/what-is-a-cognitive-architecture/), which give an LLM varying levels of control.

![Agent Types](https://langchain-ai.github.io/langgraph/concepts/img/agent_types.png)

## Router [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#router "Permanent link")

A router allows an LLM to select a single step from a specified set of options. This is an agent architecture that exhibits a relatively limited level of control because the LLM usually focuses on making a single decision and produces a specific output from a limited set of pre-defined options. Routers typically employ a few different concepts to achieve this.

### Structured Output [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#structured-output "Permanent link")

Structured outputs with LLMs work by providing a specific format or schema that the LLM should follow in its response. This is similar to tool calling, but more general. While tool calling typically involves selecting and using predefined functions, structured outputs can be used for any type of formatted response. Common methods to achieve structured outputs include:

1. Prompt engineering: Instructing the LLM to respond in a specific format via the system prompt.
2. Output parsers: Using post-processing to extract structured data from LLM responses.
3. Tool calling: Leveraging built-in tool calling capabilities of some LLMs to generate structured outputs.

Structured outputs are crucial for routing as they ensure the LLM's decision can be reliably interpreted and acted upon by the system. Learn more about [structured outputs in this how-to guide](https://python.langchain.com/docs/how_to/structured_output/).

## Tool calling agent [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#tool-calling-agent "Permanent link")

While a router allows an LLM to make a single decision, more complex agent architectures expand the LLM's control in two key ways:

1. Multi-step decision making: The LLM can make a series of decisions, one after another, instead of just one.
2. Tool access: The LLM can choose from and use a variety of tools to accomplish tasks.

[ReAct](https://arxiv.org/abs/2210.03629) is a popular general purpose agent architecture that combines these expansions, integrating three core concepts.

1. `Tool calling`: Allowing the LLM to select and use various tools as needed.
2. `Memory`: Enabling the agent to retain and use information from previous steps.
3. `Planning`: Empowering the LLM to create and follow multi-step plans to achieve goals.

This architecture allows for more complex and flexible agent behaviors, going beyond simple routing to enable dynamic problem-solving with multiple steps. You can use it with [`create_react_agent`](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent "<code class=\"doc-symbol doc-symbol-heading doc-symbol-function\"></code>            <span class=\"doc doc-object-name doc-function-name\">create_react_agent</span>").

### Tool calling [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#tool-calling "Permanent link")

Tools are useful whenever you want an agent to interact with external systems. External systems (e.g., APIs) often require a particular input schema or payload, rather than natural language. When we bind an API, for example, as a tool, we give the model awareness of the required input schema. The model will choose to call a tool based upon the natural language input from the user and it will return an output that adheres to the tool's required schema.

[Many LLM providers support tool calling](https://python.langchain.com/docs/integrations/chat/) and [tool calling interface](https://blog.langchain.dev/improving-core-tool-interfaces-and-docs-in-langchain/) in LangChain is simple: you can simply pass any Python `function` into `ChatModel.bind_tools(function)`.

![Tools](https://langchain-ai.github.io/langgraph/concepts/img/tool_call.png)

### Memory [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#memory "Permanent link")

Memory is crucial for agents, enabling them to retain and utilize information across multiple steps of problem-solving. It operates on different scales:

1. Short-term memory: Allows the agent to access information acquired during earlier steps in a sequence.
2. Long-term memory: Enables the agent to recall information from previous interactions, such as past messages in a conversation.

LangGraph provides full control over memory implementation:

- [`State`](https://langchain-ai.github.io/langgraph/concepts/low_level/#state): User-defined schema specifying the exact structure of memory to retain.
- [`Checkpointers`](https://langchain-ai.github.io/langgraph/concepts/persistence/): Mechanism to store state at every step across different interactions.

This flexible approach allows you to tailor the memory system to your specific agent architecture needs. For a practical guide on adding memory to your graph, see [this tutorial](https://langchain-ai.github.io/langgraph/how-tos/persistence/).

Effective memory management enhances an agent's ability to maintain context, learn from past experiences, and make more informed decisions over time.

### Planning [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#planning "Permanent link")

In the ReAct architecture, an LLM is called repeatedly in a while-loop. At each step the agent decides which tools to call, and what the inputs to those tools should be. Those tools are then executed, and the outputs are fed back into the LLM as observations. The while-loop terminates when the agent decides it has enough information to solve the user request and it is not worth calling any more tools.

### ReAct implementation [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#react-implementation "Permanent link")

There are several differences between [this](https://arxiv.org/abs/2210.03629) paper and the pre-built [`create_react_agent`](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent "<code class=\"doc-symbol doc-symbol-heading doc-symbol-function\"></code>            <span class=\"doc doc-object-name doc-function-name\">create_react_agent</span>") implementation:

- First, we use [tool-calling](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/#tool-calling) to have LLMs call tools, whereas the paper used prompting + parsing of raw output. This is because tool calling did not exist when the paper was written, but is generally better and more reliable.
- Second, we use messages to prompt the LLM, whereas the paper used string formatting. This is because at the time of writing, LLMs didn't even expose a message-based interface, whereas now that's the only interface they expose.
- Third, the paper required all inputs to the tools to be a single string. This was largely due to LLMs not being super capable at the time, and only really being able to generate a single input. Our implementation allows for using tools that require multiple inputs.
- Fourth, the paper only looks at calling a single tool at the time, largely due to limitations in LLMs performance at the time. Our implementation allows for calling multiple tools at a time.
- Finally, the paper asked the LLM to explicitly generate a "Thought" step before deciding which tools to call. This is the "Reasoning" part of "ReAct". Our implementation does not do this by default, largely because LLMs have gotten much better and that is not as necessary. Of course, if you wish to prompt it do so, you certainly can.

## Custom agent architectures [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#custom-agent-architectures "Permanent link")

While routers and tool-calling agents (like ReAct) are common, [customizing agent architectures](https://blog.langchain.dev/why-you-should-outsource-your-agentic-infrastructure-but-own-your-cognitive-architecture/) often leads to better performance for specific tasks. LangGraph offers several powerful features for building tailored agent systems:

### Human-in-the-loop [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#human-in-the-loop "Permanent link")

Human involvement can significantly enhance agent reliability, especially for sensitive tasks. This can involve:

- Approving specific actions
- Providing feedback to update the agent's state
- Offering guidance in complex decision-making processes

Human-in-the-loop patterns are crucial when full automation isn't feasible or desirable. Learn more in our [human-in-the-loop guide](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/).

### Parallelization [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#parallelization "Permanent link")

Parallel processing is vital for efficient multi-agent systems and complex tasks. LangGraph supports parallelization through its [Send](https://langchain-ai.github.io/langgraph/concepts/low_level/#send) API, enabling:

- Concurrent processing of multiple states
- Implementation of map-reduce-like operations
- Efficient handling of independent subtasks

For practical implementation, see our [map-reduce tutorial](https://langchain-ai.github.io/langgraph/how-tos/map-reduce/).

### Subgraphs [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#subgraphs "Permanent link")

[Subgraphs](https://langchain-ai.github.io/langgraph/concepts/low_level/#subgraphs) are essential for managing complex agent architectures, particularly in [multi-agent systems](https://langchain-ai.github.io/langgraph/concepts/multi_agent/). They allow:

- Isolated state management for individual agents
- Hierarchical organization of agent teams
- Controlled communication between agents and the main system

Subgraphs communicate with the parent graph through overlapping keys in the state schema. This enables flexible, modular agent design. For implementation details, refer to our [subgraph how-to guide](https://langchain-ai.github.io/langgraph/how-tos/subgraph/).

### Reflection [¶](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/\#reflection "Permanent link")

Reflection mechanisms can significantly improve agent reliability by:

1. Evaluating task completion and correctness
2. Providing feedback for iterative improvement
3. Enabling self-correction and learning

While often LLM-based, reflection can also use deterministic methods. For instance, in coding tasks, compilation errors can serve as feedback. This approach is demonstrated in [this video using LangGraph for self-corrective code generation](https://www.youtube.com/watch?v=MvNdgmM7uyc).

By leveraging these features, LangGraph enables the creation of sophisticated, task-specific agent architectures that can handle complex workflows, collaborate effectively, and continuously improve their performance.

## Comments

giscus

#### [9 reactions](https://github.com/langchain-ai/langgraph/discussions/1018)

👍8❤️1

#### [4 comments](https://github.com/langchain-ai/langgraph/discussions/1018)

#### ·

#### 7 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@Pythonista7](https://avatars.githubusercontent.com/u/36104244?u=1ac6ba4051e99094406e1bd812475c123ef8481a&v=4)Pythonista7](https://github.com/Pythonista7) [Jul 14, 2024](https://github.com/langchain-ai/langgraph/discussions/1018#discussioncomment-10045038)

How can i use Structured Outputs with the builtin ReAct agent? since it takes in a model and not LlmLike , i cant really add `llm.with_structured_output()` , was just running some experiments and im sure this is possible by defining a custom graph with a node having a runnable to create structured outputs. But would be nice to have it at an agent output level as well with the builtin agent :)

1

5 replies

[![@hwchase17](https://avatars.githubusercontent.com/u/11986836?u=f4c4f21a82b2af6c9f91e1f1d99ea40062f7a101&v=4)](https://github.com/hwchase17)

[hwchase17](https://github.com/hwchase17) [Jul 15, 2024](https://github.com/langchain-ai/langgraph/discussions/1018#discussioncomment-10046412)

Contributor

with the built in ReAct agent you cant. What you would you want/expect? To be able to specify a schema and then the agent would alway return that schema?

😄1

[![@Pythonista7](https://avatars.githubusercontent.com/u/36104244?u=1ac6ba4051e99094406e1bd812475c123ef8481a&v=4)](https://github.com/Pythonista7)

[Pythonista7](https://github.com/Pythonista7) [Jul 16, 2024](https://github.com/langchain-ai/langgraph/discussions/1018#discussioncomment-10063348)

[@hwchase17](https://github.com/hwchase17) Yes was pretty much trying to do exactly that

```
graph = create_react_agent(model=llm,tools=self.tools,messages_modifier=prompt) | RunnableLambda(
            lambda data: {"text": str(data["messages"][-1].content)}
        ) | parser_chain
```

And had a `parser_chain` using the `PydanticOutputParser` to get the structured output.

[![@lukajose](https://avatars.githubusercontent.com/u/37333424?u=8ac09c221b3993b9505578c161d2dcd4a850cfcf&v=4)](https://github.com/lukajose)

[lukajose](https://github.com/lukajose) [Oct 21, 2024](https://github.com/langchain-ai/langgraph/discussions/1018#discussioncomment-10999346)

I was trying to do the same, did you find a solution?

[![@yunhzou](https://avatars.githubusercontent.com/u/59716776?u=93b776e7590f859cceba6b34d3aa937438cfe6c8&v=4)](https://github.com/yunhzou)

[yunhzou](https://github.com/yunhzou) [Nov 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1018#discussioncomment-11219273)

You can use structured output to generate

class ReACT(BaseModel):

thought: str = Field(description="One thought process.Each thought is only one sentence and should have a objective, you must follow this rule")

action: str = Field(description="An action should be taken to achieve the thought, only one action is allowed. Describe the action in one sentence, best to include the action name you proposed")

terminate: bool = Field(description="When the target has been achieved or the question has been answered, set this to True, otherwise False")

and connect an executor agent(REACT agent or openai tool agent) that equip with tools to look at action description at each step and call the tools if the action can be solved with tools equipped.

👍1

[![@yunhzou](https://avatars.githubusercontent.com/u/59716776?u=93b776e7590f859cceba6b34d3aa937438cfe6c8&v=4)](https://github.com/yunhzou)

[yunhzou](https://github.com/yunhzou) [Nov 11, 2024](https://github.com/langchain-ai/langgraph/discussions/1018#discussioncomment-11219283)

This implementation lead to something like this.

Assistant: : I need to check the current weather in San Francisco.,

: perform a web search for current weather in San Francisco.,

: False

Assistant: : The current weather in San Francisco is sunny. However, if you're a Gemini, you might want to be cautious! 😈

Assistant: : The current weather in San Francisco is sunny.,

: No action is required.,

: True

[![@ashantanu](https://avatars.githubusercontent.com/u/14858985?u=8a09fd313f96b28b53d810fd96a447108c736840&v=4)ashantanu](https://github.com/ashantanu) [Aug 4, 2024](https://github.com/langchain-ai/langgraph/discussions/1018#discussioncomment-10236745)

what can we do for caching?

langchain had LLMCaching but that doesn't seem to be working for me.

1

1 reply

[![@rlancemartin](https://avatars.githubusercontent.com/u/122662504?u=e88c472fba16a74332c550cc9707fd015738a0da&v=4)](https://github.com/rlancemartin)

[rlancemartin](https://github.com/rlancemartin) [Sep 24, 2024](https://github.com/langchain-ai/langgraph/discussions/1018#discussioncomment-10744629)

Contributor

Have a look at persistence documentation:

[https://langchain-ai.github.io/langgraph/concepts/persistence/#persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/#persistence)

[![@yadgire7](https://avatars.githubusercontent.com/u/47882001?u=4c14b35f94a49ec92a7309653c8cff68c2713df0&v=4)yadgire7](https://github.com/yadgire7) [Aug 19, 2024](https://github.com/langchain-ai/langgraph/discussions/1018#discussioncomment-10387963)

Can I create an agent using LlamaCpp and bind tools to it?

1

1 reply

[![@rlancemartin](https://avatars.githubusercontent.com/u/122662504?u=e88c472fba16a74332c550cc9707fd015738a0da&v=4)](https://github.com/rlancemartin)

[rlancemartin](https://github.com/rlancemartin) [Sep 24, 2024](https://github.com/langchain-ai/langgraph/discussions/1018#discussioncomment-10744626)

Contributor

Yes, see here:

[https://www.youtube.com/watch?v=rsDlu-9UP00](https://www.youtube.com/watch?v=rsDlu-9UP00)

And here:

[https://python.langchain.com/docs/integrations/chat/llamacpp/](https://python.langchain.com/docs/integrations/chat/llamacpp/)

If you want to use LlamaCpp tool calling w/ LangChain integration.

You can also use LlamaCpp directly w/o LangChain, as LangGraph does not require you to use LangChain.

Here is an example graph using Ollama (rather than LlamaCpp) to show how local llms + LangGraph can work:

[https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph\_rag\_agent\_llama3\_local.ipynb](https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph_rag_agent_llama3_local.ipynb)

[![@WesGBrooks](https://avatars.githubusercontent.com/u/2110932?u=cee9eda6d45b2ffdeb3d970507e2df49fc83c75b&v=4)WesGBrooks](https://github.com/WesGBrooks) [Oct 21, 2024](https://github.com/langchain-ai/langgraph/discussions/1018#discussioncomment-11009394)

LOVE the new memory capabilities. For chatbot use-cases, is there anything coming out sometime soon to be able to manage conversation flow across multiple messages with the user? Let's say there's 5 questions you want the user to work through with the agent. Are there any paradigms you've seen for effective graph controller design to manage the flow of the conversation across multiple graph instantiations? i.e. Google's DialogFlow [describes the flow of the conversation something like this](https://cloud.google.com/dialogflow/cx/docs/basics#flow).

I've been exploring a "conversation flow manager" which keeps track of the state of the conversation via a field in the graph state, but it seems like there has to be a better way to manage conversation state \[not just graph run state\] reliably. Am I missing a useful paradigm with the current tools to do this effectively?

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Fagentic_concepts%2F)