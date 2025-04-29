[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/#tutorials)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/index.md "Edit this page")

# Tutorials [¶](https://langchain-ai.github.io/langgraph/tutorials/\#tutorials "Permanent link")

New to LangGraph or LLM app development? Read this material to get up and running building your first applications.

## Get Started 🚀 [¶](https://langchain-ai.github.io/langgraph/tutorials/\#quick-start "Permanent link")

- [LangGraph Quickstart](https://langchain-ai.github.io/langgraph/tutorials/introduction/): Build a chatbot that can use tools and keep track of conversation history. Add human-in-the-loop capabilities and explore how time-travel works.
- [Common Workflows](https://langchain-ai.github.io/langgraph/tutorials/workflows/): Overview of the most common workflows using LLMs implemented with LangGraph.
- [LangGraph Server Quickstart](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/): Launch a LangGraph server locally and interact with it using REST API and LangGraph Studio Web UI.
- [LangGraph Template Quickstart](https://langchain-ai.github.io/langgraph/concepts/template_applications/): Start building with LangGraph Platform using a template application.
- [Deploy with LangGraph Cloud Quickstart](https://langchain-ai.github.io/langgraph/cloud/quick_start/): Deploy a LangGraph app using LangGraph Cloud.

## Use cases 🛠️ [¶](https://langchain-ai.github.io/langgraph/tutorials/\#use-cases "Permanent link")

Explore practical implementations tailored for specific scenarios:

### Chatbots [¶](https://langchain-ai.github.io/langgraph/tutorials/\#chatbots "Permanent link")

- [Customer Support](https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support/): Build a multi-functional support bot for flights, hotels, and car rentals.
- [Prompt Generation from User Requirements](https://langchain-ai.github.io/langgraph/tutorials/chatbots/information-gather-prompting/): Build an information gathering chatbot.
- [Code Assistant](https://langchain-ai.github.io/langgraph/tutorials/code_assistant/langgraph_code_assistant/): Build a code analysis and generation assistant.

### RAG [¶](https://langchain-ai.github.io/langgraph/tutorials/\#rag "Permanent link")

- [Agentic RAG](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/): Use an agent to figure out how to retrieve the most relevant information before using the retrieved information to answer the user's question.
- [Adaptive RAG](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/): Adaptive RAG is a strategy for RAG that unites (1) query analysis with (2) active / self-corrective RAG. Implementation of: [https://arxiv.org/abs/2403.14403](https://arxiv.org/abs/2403.14403)
  - For a version that uses a local LLM: [Adaptive RAG using local LLMs](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag_local/)
- [Corrective RAG](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/): Uses an LLM to grade the quality of the retrieved information from the given source, and if the quality is low, it will try to retrieve the information from another source. Implementation of: [https://arxiv.org/pdf/2401.15884.pdf](https://arxiv.org/pdf/2401.15884.pdf)
  - For a version that uses a local LLM: [Corrective RAG using local LLMs](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag_local/)
- [Self-RAG](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/): Self-RAG is a strategy for RAG that incorporates self-reflection / self-grading on retrieved documents and generations. Implementation of [https://arxiv.org/abs/2310.11511](https://arxiv.org/abs/2310.11511).
  - For a version that uses a local LLM: [Self-RAG using local LLMs](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag_local/)
- [SQL Agent](https://langchain-ai.github.io/langgraph/tutorials/sql-agent/): Build a SQL agent that can answer questions about a SQL database.

### Agent Architectures [¶](https://langchain-ai.github.io/langgraph/tutorials/\#agent-architectures "Permanent link")

#### Multi-Agent Systems [¶](https://langchain-ai.github.io/langgraph/tutorials/\#multi-agent-systems "Permanent link")

- [Network](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/): Enable two or more agents to collaborate on a task
- [Supervisor](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/): Use an LLM to orchestrate and delegate to individual agents
- [Hierarchical Teams](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/): Orchestrate nested teams of agents to solve problems

#### Planning Agents [¶](https://langchain-ai.github.io/langgraph/tutorials/\#planning-agents "Permanent link")

- [Plan-and-Execute](https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/): Implement a basic planning and execution agent
- [Reasoning without Observation](https://langchain-ai.github.io/langgraph/tutorials/rewoo/rewoo/): Reduce re-planning by saving observations as variables
- [LLMCompiler](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/): Stream and eagerly execute a DAG of tasks from a planner

#### Reflection & Critique [¶](https://langchain-ai.github.io/langgraph/tutorials/\#reflection-critique "Permanent link")

- [Basic Reflection](https://langchain-ai.github.io/langgraph/tutorials/reflection/reflection/): Prompt the agent to reflect on and revise its outputs
- [Reflexion](https://langchain-ai.github.io/langgraph/tutorials/reflexion/reflexion/): Critique missing and superfluous details to guide next steps
- [Tree of Thoughts](https://langchain-ai.github.io/langgraph/tutorials/tot/tot/): Search over candidate solutions to a problem using a scored tree
- [Language Agent Tree Search](https://langchain-ai.github.io/langgraph/tutorials/lats/lats/): Use reflection and rewards to drive a monte-carlo tree search over agents
- [Self-Discover Agent](https://langchain-ai.github.io/langgraph/tutorials/self-discover/self-discover/): Analyze an agent that learns about its own capabilities

### Evaluation [¶](https://langchain-ai.github.io/langgraph/tutorials/\#evaluation "Permanent link")

- [Agent-based](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/agent-simulation-evaluation/): Evaluate chatbots via simulated user interactions
- [In LangSmith](https://langchain-ai.github.io/langgraph/tutorials/chatbot-simulation-evaluation/langsmith-agent-simulation-evaluation/): Evaluate chatbots in LangSmith over a dialog dataset

### Experimental [¶](https://langchain-ai.github.io/langgraph/tutorials/\#experimental "Permanent link")

- [Web Research (STORM)](https://langchain-ai.github.io/langgraph/tutorials/storm/storm/): Generate Wikipedia-like articles via research and multi-perspective QA
- [TNT-LLM](https://langchain-ai.github.io/langgraph/tutorials/tnt-llm/tnt-llm/): Build rich, interpretable taxonomies of user intentand using the classification system developed by Microsoft for their Bing Copilot application.
- [Web Navigation](https://langchain-ai.github.io/langgraph/tutorials/web-navigation/web_voyager/): Build an agent that can navigate and interact with websites
- [Competitive Programming](https://langchain-ai.github.io/langgraph/tutorials/usaco/usaco/): Build an agent with few-shot "episodic memory" and human-in-the-loop collaboration to solve problems from the USA Computing Olympiad; adapted from the ["Can Language Models Solve Olympiad Programming?"](https://arxiv.org/abs/2404.10952v1) paper by Shi, Tang, Narasimhan, and Yao.
- [Complex data extraction](https://langchain-ai.github.io/langgraph/tutorials/extraction/retries/): Build an agent that can use function calling to do complex extraction tasks

## LangGraph Platform 🧱 [¶](https://langchain-ai.github.io/langgraph/tutorials/\#platform "Permanent link")

### Authentication & Access Control [¶](https://langchain-ai.github.io/langgraph/tutorials/\#authentication-access-control "Permanent link")

Add custom authentication and authorization to an existing LangGraph Platform deployment in the following three-part guide:

1. [Setting Up Custom Authentication](https://langchain-ai.github.io/langgraph/tutorials/auth/getting_started/): Implement OAuth2 authentication to authorize users on your deployment
2. [Resource Authorization](https://langchain-ai.github.io/langgraph/tutorials/auth/resource_auth/): Let users have private conversations
3. [Connecting an Authentication Provider](https://langchain-ai.github.io/langgraph/tutorials/auth/add_auth_server/): Add real user accounts and validate using OAuth2

## Comments

giscus

#### [16 reactions](https://github.com/langchain-ai/langgraph/discussions/3277)

👍11🎉3❤️1👀1

#### [5 comments](https://github.com/langchain-ai/langgraph/discussions/3277)

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@lamoboos223](https://avatars.githubusercontent.com/u/35597031?v=4)lamoboos223](https://github.com/lamoboos223) [Mar 8](https://github.com/langchain-ai/langgraph/discussions/3277#discussioncomment-12432533)

amazing writing! thanks for sharing <3

1

0 replies

[![@hussainzs](https://avatars.githubusercontent.com/u/104400478?u=9241344cceeec80b02de8d284898a7ae91579b19&v=4)hussainzs](https://github.com/hussainzs) [Mar 21](https://github.com/langchain-ai/langgraph/discussions/3277#discussioncomment-12578104)

This was helpful thank you! The links provided for each section were also super useful

2

0 replies

[![@ayuranjan](https://avatars.githubusercontent.com/u/31190040?u=5185fa1b8f901622d427645d7201d2bdcf6368a8&v=4)ayuranjan](https://github.com/ayuranjan) [16 days ago](https://github.com/langchain-ai/langgraph/discussions/3277#discussioncomment-12770243)

Great informative article.

2

0 replies

[![@tugbayatilla](https://avatars.githubusercontent.com/u/16705175?u=0d912a4d3a7ba0d452f7566cdc9e1613e9add0a3&v=4)tugbayatilla](https://github.com/tugbayatilla) [14 days ago](https://github.com/langchain-ai/langgraph/discussions/3277#discussioncomment-12790962)

cool

1

0 replies

[![@BDWiii](https://avatars.githubusercontent.com/u/167006865?u=55f15d8f3385c6b09dbf86f7f09d58080d46d785&v=4)BDWiii](https://github.com/BDWiii) [5 days ago](https://github.com/langchain-ai/langgraph/discussions/3277#discussioncomment-12883815)

beautiful

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2F)