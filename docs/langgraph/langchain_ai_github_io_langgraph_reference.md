[Skip to content](https://langchain-ai.github.io/langgraph/reference/#reference)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/reference/index.md "Edit this page")

# Reference [¶](https://langchain-ai.github.io/langgraph/reference/\#reference "Permanent link")

Welcome to the LangGraph API reference! This reference provides detailed information about the LangGraph API, including classes, methods, and other components.

If you are new to LangGraph, we recommend starting with the [Quick Start](https://langchain-ai.github.io/langgraph/tutorials/introduction/) in the Tutorials section.

## Comments

giscus

#### [0 reactions](https://github.com/langchain-ai/langgraph/discussions/1908)

#### [5 comments](https://github.com/langchain-ai/langgraph/discussions/1908)

#### ·

#### 7 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@bramburn](https://avatars.githubusercontent.com/u/11090413?u=f14e710b399e47dc17130c04ad57962b97e67524&v=4)bramburn](https://github.com/bramburn) [Feb 1](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12027511)

Thanks 🙏🙏

Please elaborate on the reason for the use of the memory

1

2 replies

[![@Adi-Senku69](https://avatars.githubusercontent.com/u/108868478?u=4b3364a2eb88e3bf54d87648223a1b027d368e6c&v=4)](https://github.com/Adi-Senku69)

[Adi-Senku69](https://github.com/Adi-Senku69) [Feb 6](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12080189)

So, without memory, the state re-writes itself whenever we return a state. This goes against the purpose of using interrupts where we require some Human in the loop and just want to update the state and move on to the next node. Therefore, in the examples the memory is used.

[![@Adi-Senku69](https://avatars.githubusercontent.com/u/108868478?u=4b3364a2eb88e3bf54d87648223a1b027d368e6c&v=4)](https://github.com/Adi-Senku69)

[Adi-Senku69](https://github.com/Adi-Senku69) [Feb 6](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12080257)

If you try without checkpointer, the events of the graph are not stored, and resuming will not be possible.

[![@phuonglv-ltv](https://avatars.githubusercontent.com/u/148533275?v=4)phuonglv-ltv](https://github.com/phuonglv-ltv) [Feb 23](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12292568)

What is the most convenient way to send a confirmation request to the UI for user approval when Interrupt stops execution?

1. Use try...except to catch GraphInterrupt, then send the information to the UI via RESTful API, WebSocket, etc.
2. Send the information to the UI before calling interrupt() using a RESTful API, WebSocket, etc.

Are there any other ways to achieve this besides these two methods?

1

👍1

2 replies

[![@junbo2001](https://avatars.githubusercontent.com/u/50980865?u=4a506a974acdc6c03321d345dd5dd328b47c56be&v=4)](https://github.com/junbo2001)

[junbo2001](https://github.com/junbo2001) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12698460)

你这个问题解决了吗？我也在实现这个场景，断点之后不知道怎么把信息返回给ui前端，能参考一下你现在的解决方式吗？

[![@Adi-Senku69](https://avatars.githubusercontent.com/u/108868478?u=4b3364a2eb88e3bf54d87648223a1b027d368e6c&v=4)](https://github.com/Adi-Senku69)

[Adi-Senku69](https://github.com/Adi-Senku69) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12700272)

Use the RemoteGraph in frontend or python/Javascript sdk. Assuming you are using the langgraph server

[![@mouadenna](https://avatars.githubusercontent.com/u/90518486?u=5d5ce112249751c73dab1187ceefbdbd0c4af321&v=4)mouadenna](https://github.com/mouadenna) [23 days ago](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12682987)

why should use `Interrupt` and not end the workflow asking for something until the human interact?

1

1 reply

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [23 days ago](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12688822)

Contributor

Interrupt **does** end the workflow until the human (or other external caller) interacts.

Or is the question is about when to interrupt() a graph execution vs. designing the graph to go to `__end__` (alternatively, not have any remaining tasks to execute)? In that case, both work! interrupt() is convenient because it lets you write code as it should operate and insert an opportunity for human intervention inline, without having to re-architect the graph to accommodate it.

👍1

[![@TaisukeIto](https://avatars.githubusercontent.com/u/56746159?v=4)TaisukeIto](https://github.com/TaisukeIto) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12700063)

Are they changing the specifications of LangGraph so frequently that the “human in the loop” program doesn’t run at all? Please provide a basic program that actually works.

1

2 replies

[![@Adi-Senku69](https://avatars.githubusercontent.com/u/108868478?u=4b3364a2eb88e3bf54d87648223a1b027d368e6c&v=4)](https://github.com/Adi-Senku69)

[Adi-Senku69](https://github.com/Adi-Senku69) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12700250)

Human in the loop works just fine, it depends on how your running your graph.

Let's assume you have created a CompiledGraph object then the graph stops where you have specified. You must check the next node which is set for execution in this case ( This is the case for Subgraphs). If you are using a normal graph then you'll get an output dictionary with the key **interrupt**. If you have created a langgraph server, then you must manually check the state at a given checkpoint for the next node set to execute. If you are using RemoteGraph then this will raise GraphInterrupt exception and then you can use the try and except block in python to catch it

[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)

[hinthornw](https://github.com/hinthornw) [22 days ago](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12704668)

Contributor

[@TaisukeIto](https://github.com/TaisukeIto) we haven't changed the functions, and the example runs in CI. What are you running into?

[![@SalmonSung](https://avatars.githubusercontent.com/u/148196990?u=f2fd149ffd9672449a4b9ef1ae3b0a704a16634a&v=4)SalmonSung](https://github.com/SalmonSung) [yesterday](https://github.com/langchain-ai/langgraph/discussions/1908#discussioncomment-12926892)

Hi everyone, what’s the best way to handle send and command when there are too many simultaneous requests?

```
def router(state: SectionState):
  return Command(goto=[\
Send("some_node", {"placeholder": s})\
  for s in state["some_list"]\
])
```

In this case, if some\_list contains too many items, my API key could become overloaded due to the high number of simultaneous requests.

1

0 replies

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Freference%2F)