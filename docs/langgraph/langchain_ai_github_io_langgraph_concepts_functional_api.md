[Skip to content](https://langchain-ai.github.io/langgraph/concepts/functional_api/#functional-api)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/concepts/functional_api.md "Edit this page")

# Functional API [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#functional-api "Permanent link")

## Overview [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#overview "Permanent link")

The **Functional API** allows you to add LangGraph's key features -- [persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/), [memory](https://langchain-ai.github.io/langgraph/concepts/memory/), [human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/), and [streaming](https://langchain-ai.github.io/langgraph/concepts/streaming/) — to your applications with minimal changes to your existing code.

It is designed to integrate these features into existing code that may use standard language primitives for branching and control flow, such as `if` statements, `for` loops, and function calls. Unlike many data orchestration frameworks that require restructuring code into an explicit pipeline or DAG, the Functional API allows you to incorporate these capabilities without enforcing a rigid execution model.

The Functional API uses two key building blocks:

- **`@entrypoint`** – Marks a function as the starting point of a workflow, encapsulating logic and managing execution flow, including handling long-running tasks and interrupts.
- **`@task`** – Represents a discrete unit of work, such as an API call or data processing step, that can be executed asynchronously within an entrypoint. Tasks return a future-like object that can be awaited or resolved synchronously.

This provides a minimal abstraction for building workflows with state management and streaming.

Tip

For users who prefer a more declarative approach, LangGraph's [Graph API](https://langchain-ai.github.io/langgraph/concepts/low_level/) allows you to define workflows using a Graph paradigm. Both APIs share the same underlying runtime, so you can use them together in the same application.
Please see the [Functional API vs. Graph API](https://langchain-ai.github.io/langgraph/concepts/functional_api/#functional-api-vs-graph-api) section for a comparison of the two paradigms.

## Example [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#example "Permanent link")

Below we demonstrate a simple application that writes an essay and [interrupts](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/) to request human review.

API Reference: [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver) \| [entrypoint](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.entrypoint) \| [task](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.task) \| [interrupt](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.interrupt)

```md-code__content
from langgraph.checkpoint.memory import MemorySaver
from langgraph.func import entrypoint, task
from langgraph.types import interrupt

@task
def write_essay(topic: str) -> str:
    """Write an essay about the given topic."""
    time.sleep(1) # A placeholder for a long-running task.
    return f"An essay about topic: {topic}"

@entrypoint(checkpointer=MemorySaver())
def workflow(topic: str) -> dict:
    """A simple workflow that writes an essay and asks for a review."""
    essay = write_essay("cat").result()
    is_approved = interrupt({
        # Any json-serializable payload provided to interrupt as argument.
        # It will be surfaced on the client side as an Interrupt when streaming data
        # from the workflow.
        "essay": essay, # The essay we want reviewed.
        # We can add any additional information that we need.
        # For example, introduce a key called "action" with some instructions.
        "action": "Please approve/reject the essay",
    })

    return {
        "essay": essay, # The essay that was generated
        "is_approved": is_approved, # Response from HIL
    }

```

Detailed Explanation

This workflow will write an essay about the topic "cat" and then pause to get a review from a human. The workflow can be interrupted for an indefinite amount of time until a review is provided.

When the workflow is resumed, it executes from the very start, but because the result of the `write_essay` task was already saved, the task result will be loaded from the checkpoint instead of being recomputed.

```md-code__content
import time
import uuid

from langgraph.func import entrypoint, task
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver

@task
def write_essay(topic: str) -> str:
    """Write an essay about the given topic."""
    time.sleep(1) # This is a placeholder for a long-running task.
    return f"An essay about topic: {topic}"

@entrypoint(checkpointer=MemorySaver())
def workflow(topic: str) -> dict:
    """A simple workflow that writes an essay and asks for a review."""
    essay = write_essay("cat").result()
    is_approved = interrupt({
        # Any json-serializable payload provided to interrupt as argument.
        # It will be surfaced on the client side as an Interrupt when streaming data
        # from the workflow.
        "essay": essay, # The essay we want reviewed.
        # We can add any additional information that we need.
        # For example, introduce a key called "action" with some instructions.
        "action": "Please approve/reject the essay",
    })

    return {
        "essay": essay, # The essay that was generated
        "is_approved": is_approved, # Response from HIL
    }

thread_id = str(uuid.uuid4())

config = {
    "configurable": {
        "thread_id": thread_id
    }
}

for item in workflow.stream("cat", config):
    print(item)

```

```md-code__content
{'write_essay': 'An essay about topic: cat'}
{'__interrupt__': (Interrupt(value={'essay': 'An essay about topic: cat', 'action': 'Please approve/reject the essay'}, resumable=True, ns=['workflow:f7b8508b-21c0-8b4c-5958-4e8de74d2684'], when='during'),)}

```

An essay has been written and is ready for review. Once the review is provided, we can resume the workflow:

```md-code__content
from langgraph.types import Command

# Get review from a user (e.g., via a UI)
# In this case, we're using a bool, but this can be any json-serializable value.
human_review = True

for item in workflow.stream(Command(resume=human_review), config):
    print(item)

```

```md-code__content
{'workflow': {'essay': 'An essay about topic: cat', 'is_approved': False}}

```

The workflow has been completed and the review has been added to the essay.

## Entrypoint [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#entrypoint "Permanent link")

The [`@entrypoint`](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.entrypoint "<code class=\"doc-symbol doc-symbol-heading doc-symbol-class\"></code>            <span class=\"doc doc-object-name doc-class-name\">entrypoint</span>") decorator can be used to create a workflow from a function. It encapsulates workflow logic and manages execution flow, including handling _long-running tasks_ and [interrupts](https://langchain-ai.github.io/langgraph/concepts/low_level/#interrupt).

### Definition [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#definition "Permanent link")

An **entrypoint** is defined by decorating a function with the `@entrypoint` decorator.

The function **must accept a single positional argument**, which serves as the workflow input. If you need to pass multiple pieces of data, use a dictionary as the input type for the first argument.

Decorating a function with an `entrypoint` produces a [`Pregel`](https://langchain-ai.github.io/langgraph/reference/pregel/#langgraph.pregel.Pregel.stream "<code class=\"doc-symbol doc-symbol-heading doc-symbol-method\"></code>            <span class=\"doc doc-object-name doc-function-name\">stream</span>") instance which helps to manage the execution of the workflow (e.g., handles streaming, resumption, and checkpointing).

You will usually want to pass a **checkpointer** to the `@entrypoint` decorator to enable persistence and use features like **human-in-the-loop**.

[Sync](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_1_1)[Async](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_1_2)

```md-code__content
from langgraph.func import entrypoint

@entrypoint(checkpointer=checkpointer)
def my_workflow(some_input: dict) -> int:
    # some logic that may involve long-running tasks like API calls,
    # and may be interrupted for human-in-the-loop.
    ...
    return result

```

```md-code__content
from langgraph.func import entrypoint

@entrypoint(checkpointer=checkpointer)
async def my_workflow(some_input: dict) -> int:
    # some logic that may involve long-running tasks like API calls,
    # and may be interrupted for human-in-the-loop
    ...
    return result

```

Serialization

The **inputs** and **outputs** of entrypoints must be JSON-serializable to support checkpointing. Please see the [serialization](https://langchain-ai.github.io/langgraph/concepts/functional_api/#serialization) section for more details.

### Injectable Parameters [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#injectable-parameters "Permanent link")

When declaring an `entrypoint`, you can request access to additional parameters that will be injected automatically at run time. These parameters include:

| Parameter | Description |
| --- | --- |
| **previous** | Access the the state associated with the previous `checkpoint` for the given thread. See [state management](https://langchain-ai.github.io/langgraph/concepts/functional_api/#state-management). |
| **store** | An instance of [BaseStore](https://langchain-ai.github.io/langgraph/reference/store/#langgraph.store.base.BaseStore "<code class=\"doc-symbol doc-symbol-heading doc-symbol-class\"></code>            <span class=\"doc doc-object-name doc-class-name\">BaseStore</span>"). Useful for [long-term memory](https://langchain-ai.github.io/langgraph/concepts/functional_api/#long-term-memory). |
| **writer** | For streaming custom data, to write custom data to the `custom` stream. Useful for [streaming custom data](https://langchain-ai.github.io/langgraph/concepts/functional_api/#streaming-custom-data). |
| **config** | For accessing run time configuration. See [RunnableConfig](https://python.langchain.com/docs/concepts/runnables/#runnableconfig) for information. |

Important

Declare the parameters with the appropriate name and type annotation.

Requesting Injectable Parameters

```md-code__content
from langchain_core.runnables import RunnableConfig
from langgraph.func import entrypoint
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore

in_memory_store = InMemoryStore(...)  # An instance of InMemoryStore for long-term memory

@entrypoint(
    checkpointer=checkpointer,  # Specify the checkpointer
    store=in_memory_store  # Specify the store
)
def my_workflow(
    some_input: dict,  # The input (e.g., passed via `invoke`)
    *,
    previous: Any = None, # For short-term memory
    store: BaseStore,  # For long-term memory
    writer: StreamWriter,  # For streaming custom data
    config: RunnableConfig  # For accessing the configuration passed to the entrypoint
) -> ...:

```

### Executing [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#executing "Permanent link")

Using the [`@entrypoint`](https://langchain-ai.github.io/langgraph/concepts/functional_api/#entrypoint) yields a [`Pregel`](https://langchain-ai.github.io/langgraph/reference/pregel/#langgraph.pregel.Pregel.stream "<code class=\"doc-symbol doc-symbol-heading doc-symbol-method\"></code>            <span class=\"doc doc-object-name doc-function-name\">stream</span>") object that can be executed using the `invoke`, `ainvoke`, `stream`, and `astream` methods.

[Invoke](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_2_1)[Async Invoke](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_2_2)[Stream](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_2_3)[Async Stream](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_2_4)

```md-code__content
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
my_workflow.invoke(some_input, config)  # Wait for the result synchronously

```

```md-code__content
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
await my_workflow.ainvoke(some_input, config)  # Await result asynchronously

```

```md-code__content
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}

for chunk in my_workflow.stream(some_input, config):
    print(chunk)

```

```md-code__content
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}

async for chunk in my_workflow.astream(some_input, config):
    print(chunk)

```

### Resuming [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#resuming "Permanent link")

Resuming an execution after an [interrupt](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.interrupt "<code class=\"doc-symbol doc-symbol-heading doc-symbol-function\"></code>            <span class=\"doc doc-object-name doc-function-name\">interrupt</span>") can be done by passing a **resume** value to the [Command](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Command "<code class=\"doc-symbol doc-symbol-heading doc-symbol-class\"></code>            <span class=\"doc doc-object-name doc-class-name\">Command</span>     <span class=\"doc doc-labels\">       <small class=\"doc doc-label doc-label-dataclass\"><code>dataclass</code></small>   </span>") primitive.

[Invoke](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_3_1)[Async Invoke](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_3_2)[Stream](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_3_3)[Async Stream](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_3_4)

```md-code__content
from langgraph.types import Command

config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}

my_workflow.invoke(Command(resume=some_resume_value), config)

```

```md-code__content
from langgraph.types import Command

config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}

await my_workflow.ainvoke(Command(resume=some_resume_value), config)

```

```md-code__content
from langgraph.types import Command

config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}

for chunk in my_workflow.stream(Command(resume=some_resume_value), config):
    print(chunk)

```

```md-code__content
from langgraph.types import Command

config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}

async for chunk in my_workflow.astream(Command(resume=some_resume_value), config):
    print(chunk)

```

**Resuming after an error**

To resume after an error, run the `entrypoint` with a `None` and the same **thread id** (config).

This assumes that the underlying **error** has been resolved and execution can proceed successfully.

[Invoke](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_4_1)[Async Invoke](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_4_2)[Stream](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_4_3)[Async Stream](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_4_4)

```md-code__content
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}

my_workflow.invoke(None, config)

```

```md-code__content
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}

await my_workflow.ainvoke(None, config)

```

```md-code__content
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}

for chunk in my_workflow.stream(None, config):
    print(chunk)

```

```md-code__content
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}

async for chunk in my_workflow.astream(None, config):
    print(chunk)

```

### State Management [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#state-management "Permanent link")

When an `entrypoint` is defined with a `checkpointer`, it stores information between successive invocations on the same **thread id** in [checkpoints](https://langchain-ai.github.io/langgraph/concepts/persistence/#checkpoints).

This allows accessing the state from the previous invocation using the `previous` parameter.

By default, the `previous` parameter is the return value of the previous invocation.

```md-code__content
@entrypoint(checkpointer=checkpointer)
def my_workflow(number: int, *, previous: Any = None) -> int:
    previous = previous or 0
    return number + previous

config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}

my_workflow.invoke(1, config)  # 1 (previous was None)
my_workflow.invoke(2, config)  # 3 (previous was 1 from the previous invocation)

```

#### `entrypoint.final` [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#entrypointfinal "Permanent link")

[entrypoint.final](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.entrypoint.final "<code class=\"doc-symbol doc-symbol-heading doc-symbol-class\"></code>            <span class=\"doc doc-object-name doc-class-name\">final</span>     <span class=\"doc doc-labels\">       <small class=\"doc doc-label doc-label-dataclass\"><code>dataclass</code></small>   </span>") is a special primitive that can be returned from an entrypoint and allows **decoupling** the value that is **saved in the checkpoint** from the **return value of the entrypoint**.

The first value is the return value of the entrypoint, and the second value is the value that will be saved in the checkpoint. The type annotation is `entrypoint.final[return_type, save_type]`.

```md-code__content
@entrypoint(checkpointer=checkpointer)
def my_workflow(number: int, *, previous: Any = None) -> entrypoint.final[int, int]:
    previous = previous or 0
    # This will return the previous value to the caller, saving
    # 2 * number to the checkpoint, which will be used in the next invocation
    # for the `previous` parameter.
    return entrypoint.final(value=previous, save=2 * number)

config = {
    "configurable": {
        "thread_id": "1"
    }
}

my_workflow.invoke(3, config)  # 0 (previous was None)
my_workflow.invoke(1, config)  # 6 (previous was 3 * 2 from the previous invocation)

```

## Task [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#task "Permanent link")

A **task** represents a discrete unit of work, such as an API call or data processing step. It has two key characteristics:

- **Asynchronous Execution**: Tasks are designed to be executed asynchronously, allowing multiple operations to run concurrently without blocking.
- **Checkpointing**: Task results are saved to a checkpoint, enabling resumption of the workflow from the last saved state. (See [persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/) for more details).

### Definition [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#definition_1 "Permanent link")

Tasks are defined using the `@task` decorator, which wraps a regular Python function.

API Reference: [task](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.task)

```md-code__content
from langgraph.func import task

@task()
def slow_computation(input_value):
    # Simulate a long-running operation
    ...
    return result

```

Serialization

The **outputs** of tasks must be JSON-serializable to support checkpointing.

### Execution [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#execution "Permanent link")

**Tasks** can only be called from within an **entrypoint**, another **task**, or a [state graph node](https://langchain-ai.github.io/langgraph/concepts/low_level/#nodes).

Tasks _cannot_ be called directly from the main application code.

When you call a **task**, it returns _immediately_ with a future object. A future is a placeholder for a result that will be available later.

To obtain the result of a **task**, you can either wait for it synchronously (using `result()`) or await it asynchronously (using `await`).

[Synchronous Invocation](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_5_1)[Asynchronous Invocation](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_5_2)

```md-code__content
@entrypoint(checkpointer=checkpointer)
def my_workflow(some_input: int) -> int:
    future = slow_computation(some_input)
    return future.result()  # Wait for the result synchronously

```

```md-code__content
@entrypoint(checkpointer=checkpointer)
async def my_workflow(some_input: int) -> int:
    return await slow_computation(some_input)  # Await result asynchronously

```

## When to use a task [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#when-to-use-a-task "Permanent link")

**Tasks** are useful in the following scenarios:

- **Checkpointing**: When you need to save the result of a long-running operation to a checkpoint, so you don't need to recompute it when resuming the workflow.
- **Human-in-the-loop**: If you're building a workflow that requires human intervention, you MUST use **tasks** to encapsulate any randomness (e.g., API calls) to ensure that the workflow can be resumed correctly. See the [determinism](https://langchain-ai.github.io/langgraph/concepts/functional_api/#determinism) section for more details.
- **Parallel Execution**: For I/O-bound tasks, **tasks** enable parallel execution, allowing multiple operations to run concurrently without blocking (e.g., calling multiple APIs).
- **Observability**: Wrapping operations in **tasks** provides a way to track the progress of the workflow and monitor the execution of individual operations using [LangSmith](https://docs.smith.langchain.com/).
- **Retryable Work**: When work needs to be retried to handle failures or inconsistencies, **tasks** provide a way to encapsulate and manage the retry logic.

## Serialization [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#serialization "Permanent link")

There are two key aspects to serialization in LangGraph:

1. `@entrypoint` inputs and outputs must be JSON-serializable.
2. `@task` outputs must be JSON-serializable.

These requirements are necessary for enabling checkpointing and workflow resumption. Use python primitives
like dictionaries, lists, strings, numbers, and booleans to ensure that your inputs and outputs are serializable.

Serialization ensures that workflow state, such as task results and intermediate values, can be reliably saved and restored. This is critical for enabling human-in-the-loop interactions, fault tolerance, and parallel execution.

Providing non-serializable inputs or outputs will result in a runtime error when a workflow is configured with a checkpointer.

## Determinism [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#determinism "Permanent link")

To utilize features like **human-in-the-loop**, any randomness should be encapsulated inside of **tasks**. This guarantees that when execution is halted (e.g., for human in the loop) and then resumed, it will follow the same _sequence of steps_, even if **task** results are non-deterministic.

LangGraph achieves this behavior by persisting **task** and [**subgraph**](https://langchain-ai.github.io/langgraph/concepts/low_level/#subgraphs) results as they execute. A well-designed workflow ensures that resuming execution follows the _same sequence of steps_, allowing previously computed results to be retrieved correctly without having to re-execute them. This is particularly useful for long-running **tasks** or **tasks** with non-deterministic results, as it avoids repeating previously done work and allows resuming from essentially the same

While different runs of a workflow can produce different results, resuming a **specific** run should always follow the same sequence of recorded steps. This allows LangGraph to efficiently look up **task** and **subgraph** results that were executed prior to the graph being interrupted and avoid recomputing them.

## Idempotency [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#idempotency "Permanent link")

Idempotency ensures that running the same operation multiple times produces the same result. This helps prevent duplicate API calls and redundant processing if a step is rerun due to a failure. Always place API calls inside **tasks** functions for checkpointing, and design them to be idempotent in case of re-execution. Re-execution can occur if a **task** starts, but does not complete successfully. Then, if the workflow is resumed, the **task** will run again. Use idempotency keys or verify existing results to avoid duplication.

## Functional API vs. Graph API [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#functional-api-vs-graph-api "Permanent link")

The **Functional API** and the [Graph APIs (StateGraph)](https://langchain-ai.github.io/langgraph/concepts/low_level/#stategraph) provide two different paradigms to create applications with LangGraph. Here are some key differences:

- **Control flow**: The Functional API does not require thinking about graph structure. You can use standard Python constructs to define workflows. This will usually trim the amount of code you need to write.
- **State management**: The **GraphAPI** requires declaring a [**State**](https://langchain-ai.github.io/langgraph/concepts/low_level/#state) and may require defining [**reducers**](https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers) to manage updates to the graph state. `@entrypoint` and `@tasks` do not require explicit state management as their state is scoped to the function and is not shared across functions.
- **Checkpointing**: Both APIs generate and use checkpoints. In the **Graph API** a new checkpoint is generated after every [superstep](https://langchain-ai.github.io/langgraph/concepts/low_level/). In the **Functional API**, when tasks are executed, their results are saved to an existing checkpoint associated with the given entrypoint instead of creating a new checkpoint.
- **Visualization**: The Graph API makes it easy to visualize the workflow as a graph which can be useful for debugging, understanding the workflow, and sharing with others. The Functional API does not support visualization as the graph is dynamically generated during runtime.

## Common Pitfalls [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#common-pitfalls "Permanent link")

### Handling side effects [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#handling-side-effects "Permanent link")

Encapsulate side effects (e.g., writing to a file, sending an email) in tasks to ensure they are not executed multiple times when resuming a workflow.

[Incorrect](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_6_1)[Correct](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_6_2)

In this example, a side effect (writing to a file) is directly included in the workflow, so it will be executed a second time when resuming the workflow.

```md-code__content
@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    # This code will be executed a second time when resuming the workflow.
    # Which is likely not what you want.
    with open("output.txt", "w") as f:
        f.write("Side effect executed")
    value = interrupt("question")
    return value

```

In this example, the side effect is encapsulated in a task, ensuring consistent execution upon resumption.

```md-code__content
from langgraph.func import task

@task
def write_to_file():
    with open("output.txt", "w") as f:
        f.write("Side effect executed")

@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    # The side effect is now encapsulated in a task.
    write_to_file().result()
    value = interrupt("question")
    return value

```

### Non-deterministic control flow [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#non-deterministic-control-flow "Permanent link")

Operations that might give different results each time (like getting current time or random numbers) should be encapsulated in tasks to ensure that on resume, the same result is returned.

- In a task: Get random number (5) → interrupt → resume → (returns 5 again) → ...
- Not in a task: Get random number (5) → interrupt → resume → get new random number (7) → ...

This is especially important when using **human-in-the-loop** workflows with multiple interrupts calls. LangGraph keeps a list
of resume values for each task/entrypoint. When an interrupt is encountered, it's matched with the corresponding resume value.
This matching is strictly **index-based**, so the order of the resume values should match the order of the interrupts.

If order of execution is not maintained when resuming, one `interrupt` call may be matched with the wrong `resume` value, leading to incorrect results.

Please read the section on [determinism](https://langchain-ai.github.io/langgraph/concepts/functional_api/#determinism) for more details.

[Incorrect](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_7_1)[Correct](https://langchain-ai.github.io/langgraph/concepts/functional_api/#__tabbed_7_2)

In this example, the workflow uses the current time to determine which task to execute. This is non-deterministic because the result of the workflow depends on the time at which it is executed.

```md-code__content
from langgraph.func import entrypoint

@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    t0 = inputs["t0"]
    t1 = time.time()

    delta_t = t1 - t0

    if delta_t > 1:
        result = slow_task(1).result()
        value = interrupt("question")
    else:
        result = slow_task(2).result()
        value = interrupt("question")

    return {
        "result": result,
        "value": value
    }

```

In this example, the workflow uses the input `t0` to determine which task to execute. This is deterministic because the result of the workflow depends only on the input.

```md-code__content
import time

from langgraph.func import task

@task
def get_time() -> float:
    return time.time()

@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    t0 = inputs["t0"]
    t1 = get_time().result()

    delta_t = t1 - t0

    if delta_t > 1:
        result = slow_task(1).result()
        value = interrupt("question")
    else:
        result = slow_task(2).result()
        value = interrupt("question")

    return {
        "result": result,
        "value": value
    }

```

## Patterns [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#patterns "Permanent link")

Below are a few simple patterns that show examples of **how to** use the **Functional API**.

When defining an `entrypoint`, input is restricted to the first argument of the function. To pass multiple inputs, you can use a dictionary.

```md-code__content
@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    value = inputs["value"]
    another_value = inputs["another_value"]
    ...

my_workflow.invoke({"value": 1, "another_value": 2})

```

### Parallel execution [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#parallel-execution "Permanent link")

Tasks can be executed in parallel by invoking them concurrently and waiting for the results. This is useful for improving performance in IO bound tasks (e.g., calling APIs for LLMs).

```md-code__content
@task
def add_one(number: int) -> int:
    return number + 1

@entrypoint(checkpointer=checkpointer)
def graph(numbers: list[int]) -> list[str]:
    futures = [add_one(i) for i in numbers]
    return [f.result() for f in futures]

```

### Calling subgraphs [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#calling-subgraphs "Permanent link")

The **Functional API** and the [**Graph API**](https://langchain-ai.github.io/langgraph/concepts/low_level/) can be used together in the same application as they share the same underlying runtime.

API Reference: [entrypoint](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.entrypoint) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph)

```md-code__content
from langgraph.func import entrypoint
from langgraph.graph import StateGraph

builder = StateGraph()
...
some_graph = builder.compile()

@entrypoint()
def some_workflow(some_input: dict) -> int:
    # Call a graph defined using the graph API
    result_1 = some_graph.invoke(...)
    # Call another graph defined using the graph API
    result_2 = another_graph.invoke(...)
    return {
        "result_1": result_1,
        "result_2": result_2
    }

```

### Calling other entrypoints [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#calling-other-entrypoints "Permanent link")

You can call other **entrypoints** from within an **entrypoint** or a **task**.

```md-code__content
@entrypoint() # Will automatically use the checkpointer from the parent entrypoint
def some_other_workflow(inputs: dict) -> int:
    return inputs["value"]

@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    value = some_other_workflow.invoke({"value": 1})
    return value

```

### Streaming custom data [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#streaming-custom-data "Permanent link")

You can stream custom data from an **entrypoint** by using the `StreamWriter` type. This allows you to write custom data to the `custom` stream.

API Reference: [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver) \| [entrypoint](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.entrypoint) \| [task](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.task) \| [StreamWriter](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.StreamWriter)

```md-code__content
from langgraph.checkpoint.memory import MemorySaver
from langgraph.func import entrypoint, task
from langgraph.types import StreamWriter

@task
def add_one(x):
    return x + 1

@task
def add_two(x):
    return x + 2

checkpointer = MemorySaver()

@entrypoint(checkpointer=checkpointer)
def main(inputs, writer: StreamWriter) -> int:
    """A simple workflow that adds one and two to a number."""
    writer("hello") # Write some data to the `custom` stream
    add_one(inputs['number']).result() # Will write data to the `updates` stream
    writer("world") # Write some more data to the `custom` stream
    add_two(inputs['number']).result() # Will write data to the `updates` stream
    return 5

config = {
    "configurable": {
        "thread_id": "1"
    }
}

for chunk in main.stream({"number": 1}, stream_mode=["custom", "updates"], config=config):
    print(chunk)

```

```md-code__content
('updates', {'add_one': 2})
('updates', {'add_two': 3})
('custom', 'hello')
('custom', 'world')
('updates', {'main': 5})

```

Important

The `writer` parameter is automatically injected at run time. It will only be injected if the
parameter name appears in the function signature with that _exact_ name.

### Retry policy [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#retry-policy "Permanent link")

API Reference: [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver) \| [entrypoint](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.entrypoint) \| [task](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.task) \| [RetryPolicy](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.RetryPolicy)

```md-code__content
from langgraph.checkpoint.memory import MemorySaver
from langgraph.func import entrypoint, task
from langgraph.types import RetryPolicy

attempts = 0

# Let's configure the RetryPolicy to retry on ValueError.
# The default RetryPolicy is optimized for retrying specific network errors.
retry_policy = RetryPolicy(retry_on=ValueError)

@task(retry=retry_policy)
def get_info():
    global attempts
    attempts += 1

    if attempts < 2:
        raise ValueError('Failure')
    return "OK"

checkpointer = MemorySaver()

@entrypoint(checkpointer=checkpointer)
def main(inputs, writer):
    return get_info().result()

config = {
    "configurable": {
        "thread_id": "1"
    }
}

main.invoke({'any_input': 'foobar'}, config=config)

```

```md-code__content
'OK'

```

### Resuming after an error [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#resuming-after-an-error "Permanent link")

API Reference: [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver) \| [entrypoint](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.entrypoint) \| [task](https://langchain-ai.github.io/langgraph/reference/func/#langgraph.func.task) \| [StreamWriter](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.StreamWriter)

```md-code__content
import time
from langgraph.checkpoint.memory import MemorySaver
from langgraph.func import entrypoint, task
from langgraph.types import StreamWriter

# This variable is just used for demonstration purposes to simulate a network failure.
# It's not something you will have in your actual code.
attempts = 0

@task()
def get_info():
    """
    Simulates a task that fails once before succeeding.
    Raises an exception on the first attempt, then returns "OK" on subsequent tries.
    """
    global attempts
    attempts += 1

    if attempts < 2:
        raise ValueError("Failure")  # Simulate a failure on the first attempt
    return "OK"

# Initialize an in-memory checkpointer for persistence
checkpointer = MemorySaver()

@task
def slow_task():
    """
    Simulates a slow-running task by introducing a 1-second delay.
    """
    time.sleep(1)
    return "Ran slow task."

@entrypoint(checkpointer=checkpointer)
def main(inputs, writer: StreamWriter):
    """
    Main workflow function that runs the slow_task and get_info tasks sequentially.

    Parameters:
    - inputs: Dictionary containing workflow input values.
    - writer: StreamWriter for streaming custom data.

    The workflow first executes `slow_task` and then attempts to execute `get_info`,
    which will fail on the first invocation.
    """
    slow_task_result = slow_task().result()  # Blocking call to slow_task
    get_info().result()  # Exception will be raised here on the first attempt
    return slow_task_result

# Workflow execution configuration with a unique thread identifier
config = {
    "configurable": {
        "thread_id": "1"  # Unique identifier to track workflow execution
    }
}

# This invocation will take ~1 second due to the slow_task execution
try:
    # First invocation will raise an exception due to the `get_info` task failing
    main.invoke({'any_input': 'foobar'}, config=config)
except ValueError:
    pass  # Handle the failure gracefully

```

When we resume execution, we won't need to re-run the `slow_task` as its result is already saved in the checkpoint.

```md-code__content
main.invoke(None, config=config)

```

```md-code__content
'Ran slow task.'

```

### Human-in-the-loop [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#human-in-the-loop "Permanent link")

The functional API supports [human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/) workflows using the `interrupt` function and the `Command` primitive.

Please see the following examples for more details:

- [How to wait for user input (Functional API)](https://langchain-ai.github.io/langgraph/how-tos/wait-user-input-functional/): Shows how to implement a simple human-in-the-loop workflow using the functional API.
- [How to review tool calls (Functional API)](https://langchain-ai.github.io/langgraph/how-tos/review-tool-calls-functional/): Guide demonstrates how to implement human-in-the-loop workflows in a ReAct agent using the LangGraph Functional API.

### Short-term memory [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#short-term-memory "Permanent link")

[State management](https://langchain-ai.github.io/langgraph/concepts/functional_api/#state-management) using the **previous** parameter and optionally using the `entrypoint.final` primitive can be used to implement [short term memory](https://langchain-ai.github.io/langgraph/concepts/memory/).

Please see the following how-to guides for more details:

- [How to add thread-level persistence (functional API)](https://langchain-ai.github.io/langgraph/how-tos/persistence-functional/): Shows how to add thread-level persistence to a functional API workflow and implements a simple chatbot.

### Long-term memory [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#long-term-memory "Permanent link")

[long-term memory](https://langchain-ai.github.io/langgraph/concepts/memory/#long-term-memory) allows storing information across different **thread ids**. This could be useful for learning information
about a given user in one conversation and using it in another.

Please see the following how-to guides for more details:

- [How to add cross-thread persistence (functional API)](https://langchain-ai.github.io/langgraph/how-tos/cross-thread-persistence-functional/): Shows how to add cross-thread persistence to a functional API workflow and implements a simple chatbot.

### Workflows [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#workflows "Permanent link")

- [Workflows and agent](https://langchain-ai.github.io/langgraph/tutorials/workflows/) guide for more examples of how to build workflows using the Functional API.

### Agents [¶](https://langchain-ai.github.io/langgraph/concepts/functional_api/\#agents "Permanent link")

- [How to create a React agent from scratch (Functional API)](https://langchain-ai.github.io/langgraph/how-tos/react-agent-from-scratch-functional/): Shows how to create a simple React agent from scratch using the functional API.
- [How to build a multi-agent network](https://langchain-ai.github.io/langgraph/how-tos/multi-agent-network-functional/): Shows how to build a multi-agent network using the functional API.
- [How to add multi-turn conversation in a multi-agent application (functional API)](https://langchain-ai.github.io/langgraph/how-tos/multi-agent-multi-turn-convo-functional/): allow an end-user to engage in a multi-turn conversation with one or more agents.

## Comments

giscus

#### [2 reactions](https://github.com/langchain-ai/langgraph/discussions/3323)

🎉1🚀1

#### [1 comment](https://github.com/langchain-ai/langgraph/discussions/3323)

#### ·

#### 4 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@donatoaz](https://avatars.githubusercontent.com/u/127527?v=4)donatoaz](https://github.com/donatoaz) [Feb 5](https://github.com/langchain-ai/langgraph/discussions/3323#discussioncomment-12070433)

I am getting a `None` returned by interrupt when I `invoke` my entrypoint, whereas if I `stream` my entrypoint I get a correct result...

```notranslate
@entrypoint(checkpointer=MemorySaver())
def agent(messages: list[BaseMessage]):
    # we will do an initial call to the llm, maybe the user's initial message contains all necessary info
    llm_response = call_llm(messages).result()

    while True:
        # we will iterate until we have a tool call
        if not llm_response.tool_calls:
            messages = add_messages(messages, llm_response)
            clarification = interrupt({"follow_up": llm_response})
            # call llm again with the clarification
            messages = add_messages(messages, clarification)
            llm_response = call_llm(messages).result()
            # loop ...
        else:
            # oh, there is finally a tool call!
            tool_result_futures = [\
                call_tool(tool_call) for tool_call in llm_response.tool_calls\
            ]
            tool_results = [fut.result() for fut in tool_result_futures]

            messages = add_messages(messages, [llm_response, *tool_results])
            break

    return messages

if __name__ == "__main__":
    thread_id = "123"
    config = {"configurable": {"thread_id": thread_id}}

    msgs = [\
        ("user", "I need help with my account"),\
    ]

    new_state = agent.invoke(msgs, config=config)
    print(f"{new_state=}")

```

Prints `new_state=None`

Whereas

```notranslate
    ...

    for chunk in agent.stream(msgs, config=config):
        print(chunk)
        print("\n")

```

Gives me interrupt result...

```notranslate
{'call_llm': AIMessage(content="Certainly! I'd be happy to help you with your account...", additional_kwargs={}, response_metadata={'ResponseMetadata': {'RequestId': '1d257fd3-3823-41c3-a7fb-a4d4b4838a56', 'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Wed, 05 Feb 2025 13:28:39 GMT', 'content-type': 'application/json', 'content-length': '676', 'connection': 'keep-alive', 'x-amzn-requestid': '1d257fd3-3823-41c3-a7fb-a4d4b4838a56'}, 'RetryAttempts': 0}, 'stopReason': 'end_turn', 'metrics': {'latencyMs': [3079]}}, id='run-a730263b-8e3d-4e29-ba7c-dc9213572e5d-0', usage_metadata={'input_tokens': 582, 'output_tokens': 118, 'total_tokens': 700})}

{'__interrupt__': (Interrupt(value={'follow_up': AIMessage(content="Certainly! I'd be happy to help you with your account...", additional_kwargs={}, response_metadata={'ResponseMetadata': {'RequestId': '1d257fd3-3823-41c3-a7fb-a4d4b4838a56', 'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Wed, 05 Feb 2025 13:28:39 GMT', 'content-type': 'application/json', 'content-length': '676', 'connection': 'keep-alive', 'x-amzn-requestid': '1d257fd3-3823-41c3-a7fb-a4d4b4838a56'}, 'RetryAttempts': 0}, 'stopReason': 'end_turn', 'metrics': {'latencyMs': [3079]}}, id='run-a730263b-8e3d-4e29-ba7c-dc9213572e5d-0', usage_metadata={'input_tokens': 582, 'output_tokens': 118, 'total_tokens': 700})}, resumable=True, ns=['agent:469edd7a-e8ea-e92c-dabc-c0bee21c62db'], when='during'),)}

```

1

4 replies

[![@donatoaz](https://avatars.githubusercontent.com/u/127527?v=4)](https://github.com/donatoaz)

[donatoaz](https://github.com/donatoaz) [Feb 5](https://github.com/langchain-ai/langgraph/discussions/3323#discussioncomment-12070444)

```notranslate
langchain-core==0.3.33
langchain-community==0.3.9
langchain-aws==0.2.9
langgraph==0.2.69

```

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Feb 5](https://github.com/langchain-ai/langgraph/discussions/3323#discussioncomment-12070484)

Collaborator

[@donatoaz](https://github.com/donatoaz) this is the expected behavior at the moment -- we're thinking about ways to improve this devx. this is actually not limited to the functional API, StateGraph API has the same behavior. for now i would recommend relying on `.stream()` to surface the interrupt information

👍1

[![@donatoaz](https://avatars.githubusercontent.com/u/127527?v=4)](https://github.com/donatoaz)

[donatoaz](https://github.com/donatoaz) [Feb 5](https://github.com/langchain-ai/langgraph/discussions/3323#discussioncomment-12070670)

Ok, cool, thanks for the heads up... I might have missed it on the docs

[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)

[vbarda](https://github.com/vbarda) [Feb 6](https://github.com/langchain-ai/langgraph/discussions/3323#discussioncomment-12076436)

Collaborator

another thing you can do is inspect the state via `agent.get_state(config)` \-\- you should have information about interrupts contained in the returned `StateSnapshot` as well (under `tasks`)

👍1

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Fconcepts%2Ffunctional_api%2F)