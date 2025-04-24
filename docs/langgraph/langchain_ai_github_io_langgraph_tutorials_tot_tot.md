[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/tot/tot/#tree-of-thoughts)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/tot/tot.ipynb "Edit this page")

# Tree of Thoughts [¶](https://langchain-ai.github.io/langgraph/tutorials/tot/tot/\#tree-of-thoughts "Permanent link")

[Tree of Thoughts](https://arxiv.org/abs/2305.10601) (ToT), by Yao, et. al, is a general LLM agent search algorithm that combines reflection/evaluation and simple search (in this case BFS, though you can apply DFS or other algorithms if you'd like).

![LATS diagram](https://langchain-ai.github.io/langgraph/tutorials/tot/img/tot.png)

It has three main steps:

1. Expand: generate 1 or more candidate solutions to the problem.
2. Score: measure the quality of the responses.
3. Prune: retain the top K best candidates

Then return to "Expand" if no solution is found (or if the solution is of insufficient quality).

## Prerequisites [¶](https://langchain-ai.github.io/langgraph/tutorials/tot/tot/\#prerequisites "Permanent link")

We'll install the tutorial's dependent packages and set our API key for the LLM provider of choice.

```md-code__content
%%capture --no-stderr
%pip install -U langgraph langchain-openai

```

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")
# To visualize the algorithm
trace = True
if trace:
    _set_env("LANGSMITH_API_KEY")
    os.environ["LANGSMITH_PROJECT"] = "ToT Tutorial"

```

## Task Definition [¶](https://langchain-ai.github.io/langgraph/tutorials/tot/tot/\#task-definition "Permanent link")

Our agent will try to play the "Game of 24". Given 4 numbers, it must generate a math equation that uses each of these numbers exactly one time to evaluate to a value of `24`.

```md-code__content
import operator
from typing import List, Literal, Union, NamedTuple, Optional
from pydantic import BaseModel, Field

OperatorType = Literal["+", "-", "*", "/"]
TokenType = Union[float, OperatorType]

## We use these schemas to prompt the LLM to generate equations that evaluate to 24.

class Equation(BaseModel):
    """The formula combining the provided numbers to reach the target of 24."""

    tokens: List[TokenType] = Field(
        description="The stack of tokens and operators in reverse-polish notation. Example: [3, 4, '+', -1, '*'] would evaluate to (3 + 4) * -1 = -7.",
    )

    def compute(self) -> float:
        op_funcs = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
        }
        stack = []
        for token in self.tokens:
            if isinstance(token, float):
                stack.append(token)
            else:
                b, a = stack.pop(), stack.pop()
                stack.append(op_funcs[token](a, b))

        return stack[0]

class GuessEquations(BaseModel):
    """Submit multiple equations as guesses."""

    reasoning: str = Field(
        description="The reasoning behind the submitted guesses. Explain how you arrived at these equations."
    )

    equations: List[Equation] = Field(
        description="The list of equations to submit as guesses."
    )

## These objects will represent a single "candidate" (or scored candidate) within our agent's state.
# You can update the candidate object to match your own task.

class Candidate(NamedTuple):
    candidate: Equation
    score: Optional[float] = None
    feedback: Optional[str] = None

    def __str__(self):
        try:
            computed = self.candidate.compute()
        except Exception as e:
            computed = f"Invalid equation: {self.candidate.tokens}; Error: {repr(e)}"

        return f"Equation({self.candidate.tokens}) = {computed} (Reward: {self.score})"

class ScoredCandidate(Candidate):
    candidate: Equation
    score: float
    feedback: str

```

#### Fetch data [¶](https://langchain-ai.github.io/langgraph/tutorials/tot/tot/\#fetch-data "Permanent link")

We'll use an example from the [Game of 24](https://github.com/princeton-nlp/tree-of-thought-llm) dataset.

```md-code__content
import requests
import csv

csv_data = requests.get(
    "https://storage.googleapis.com/benchmarks-artifacts/game-of-24/24.csv"
).content.decode("utf-8")
# Get just the Puzzles column (column index 1)
puzzles = [row[1].strip() for row in csv.reader(csv_data.splitlines()[1:])]

print(f"Example puzzles: {puzzles[:3]}")

```

```md-code__content
Example puzzles: ['1 1 4 6', '1 1 11 11', '1 1 3 8']

```

## Expander [¶](https://langchain-ai.github.io/langgraph/tutorials/tot/tot/\#expander "Permanent link")

The "tree of thoughts" algorithm is relatively generic. The primary two task-specific components are the **expander** and the **scorer**.
The expander (the augmented LLM) tries to generate 1 or more solutions to the problem. On subsequent attempts, it is given a seed/candidate value from
the previous search.

You can update this section to match your own task requirements. The expander can be arbitrarily complex. All that's required is that it accepts the problem and an optional previous attempt (or attempts) and returns a new result.

API Reference: [ChatPromptTemplate](https://python.langchain.com/api_reference/core/prompts/langchain_core.prompts.chat.ChatPromptTemplate.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html)

```md-code__content
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_messages(
    [\
        (\
            "system",\
            "You are playing the Game of 24. Using the provide numbers, create an equation that evaluates to 24.\n"\
            "Submit exactly {k} guesses for this round.",\
        ),\
        ("user", "Solve the 24 game for these numbers: {problem}.{candidate}"),\
    ],
).partial(candidate="")
llm = ChatOpenAI(model="gpt-4o-mini")

bound_llm = llm.with_structured_output(GuessEquations)
solver = prompt | bound_llm

```

# Scorer [¶](https://langchain-ai.github.io/langgraph/tutorials/tot/tot/\#scorer "Permanent link")

In this game, the scorer is easy. We need to assert two things:

1. The LLM has generated a valid equation using each number exactly one time.
2. The equation evaluates to 24.

You can update this function to match your own task requirements.

```md-code__content
def compute_score(problem: str, candidate: Candidate) -> ScoredCandidate:
    numbers = list(map(int, problem.split()))
    # Check that the candidate equation uses all 4 numbers exactly once
    used_numbers = [\
        token for token in candidate.candidate.tokens if isinstance(token, float)\
    ]
    if sorted(used_numbers) != sorted(numbers):
        score = 0
        feedback = "The equation must use all 4 numbers exactly once."
        return ScoredCandidate(
            candidate=candidate.candidate, score=score, feedback=feedback
        )
    try:
        result = candidate.candidate.compute()
        score = 1 / (1 + abs(24 - result))
        feedback = f"Result: {result}"
    except Exception as e:
        score = 0
        feedback = f"Invalid equation. Error: {repr(e)}"
    return ScoredCandidate(
        candidate=candidate.candidate, score=score, feedback=feedback
    )

```

## Graph [¶](https://langchain-ai.github.io/langgraph/tutorials/tot/tot/\#graph "Permanent link")

Now it's time to create our graph.

API Reference: [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [RunnableConfig](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.config.RunnableConfig.html) \| [Send](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Send) \| [MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver)

```md-code__content
import operator
from typing import Optional, Dict, Any
from typing_extensions import Annotated, TypedDict
from langgraph.graph import StateGraph

from langchain_core.runnables import RunnableConfig
from langgraph.constants import Send
from langgraph.checkpoint.memory import MemorySaver

def update_candidates(
    existing: Optional[list] = None,
    updates: Optional[Union[list, Literal["clear"]]] = None,
) -> List[str]:
    if existing is None:
        existing = []
    if updates is None:
        return existing
    if updates == "clear":
        return []
    # Concatenate the lists
    return existing + updates

class ToTState(TypedDict):
    problem: str
    candidates: Annotated[List[Candidate], update_candidates]
    scored_candidates: Annotated[List[ScoredCandidate], update_candidates]
    depth: Annotated[int, operator.add]

class Configuration(TypedDict, total=False):
    max_depth: int
    threshold: float
    k: int
    beam_size: int

def _ensure_configurable(config: RunnableConfig) -> Configuration:
    """Get params that configure the search algorithm."""
    configurable = config.get("configurable", {})
    return {
        **configurable,
        "max_depth": configurable.get("max_depth", 10),
        "threshold": config.get("threshold", 0.9),
        "k": configurable.get("k", 5),
        "beam_size": configurable.get("beam_size", 3),
    }

class ExpansionState(ToTState):
    seed: Optional[Candidate]

def expand(state: ExpansionState, *, config: RunnableConfig) -> Dict[str, List[str]]:
    """Generate the next state."""
    configurable = _ensure_configurable(config)
    if not state.get("seed"):
        candidate_str = ""
    else:
        candidate_str = "\n\n" + str(state["seed"])
    try:
        equation_submission = solver.invoke(
            {
                "problem": state["problem"],
                "candidate": candidate_str,
                "k": configurable["k"],
            },
            config=config,
        )
    except Exception:
        return {"candidates": []}
    new_candidates = [\
        Candidate(candidate=equation) for equation in equation_submission.equations\
    ]
    return {"candidates": new_candidates}

def score(state: ToTState) -> Dict[str, List[float]]:
    """Evaluate the candidate generations."""
    candidates = state["candidates"]
    scored = []
    for candidate in candidates:
        scored.append(compute_score(state["problem"], candidate))
    return {"scored_candidates": scored, "candidates": "clear"}

def prune(
    state: ToTState, *, config: RunnableConfig
) -> Dict[str, List[Dict[str, Any]]]:
    scored_candidates = state["scored_candidates"]
    beam_size = _ensure_configurable(config)["beam_size"]
    organized = sorted(
        scored_candidates, key=lambda candidate: candidate[1], reverse=True
    )
    pruned = organized[:beam_size]
    return {
        # Update the starting point for the next iteration
        "candidates": pruned,
        # Clear the old memory
        "scored_candidates": "clear",
        # Increment the depth by 1
        "depth": 1,
    }

def should_terminate(
    state: ToTState, config: RunnableConfig
) -> Union[Literal["__end__"], Send]:
    configurable = _ensure_configurable(config)
    solved = state["candidates"][0].score >= configurable["threshold"]
    if solved or state["depth"] >= configurable["max_depth"]:
        return "__end__"
    return [\
        Send("expand", {**state, "somevalseed": candidate})\
        for candidate in state["candidates"]\
    ]

# Create the graph
builder = StateGraph(state_schema=ToTState, config_schema=Configuration)

# Add nodes
builder.add_node(expand)
builder.add_node(score)
builder.add_node(prune)

# Add edges
builder.add_edge("expand", "score")
builder.add_edge("score", "prune")
builder.add_conditional_edges("prune", should_terminate, path_map=["expand", "__end__"])

# Set entry point
builder.add_edge("__start__", "expand")

# Compile the graph
graph = builder.compile(checkpointer=MemorySaver())

```

```md-code__content
from IPython.display import Image, display

display(Image(graph.get_graph().draw_mermaid_png()))

```

![](<Base64-Image-Removed>)

## Run [¶](https://langchain-ai.github.io/langgraph/tutorials/tot/tot/\#run "Permanent link")

Now let's try it on one of the puzzles!

```md-code__content
config = {
    "configurable": {
        "thread_id": "test_1",
        "depth": 10,
    }
}
for step in graph.stream({"problem": puzzles[42]}, config):
    print(step)

```

```md-code__content
{'expand': {'candidates': [Candidate(candidate=Equation(tokens=[12.0, 5.0, '/', 7.0, '*']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[12.0, 1.0, '+', 5.0, '*']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[12.0, 7.0, '*', 1.0, '/']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[5.0, 7.0, '*', 1.0, '*']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[7.0, 5.0, '*', 12.0, '/']), score=None, feedback=None)]}}
{'score': {'candidates': 'clear', 'scored_candidates': [ScoredCandidate(candidate=Equation(tokens=[12.0, 5.0, '/', 7.0, '*']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[12.0, 1.0, '+', 5.0, '*']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[12.0, 7.0, '*', 1.0, '/']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[5.0, 7.0, '*', 1.0, '*']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[7.0, 5.0, '*', 12.0, '/']), score=0, feedback='The equation must use all 4 numbers exactly once.')]}}
{'prune': {'candidates': [ScoredCandidate(candidate=Equation(tokens=[12.0, 5.0, '/', 7.0, '*']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[12.0, 1.0, '+', 5.0, '*']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[12.0, 7.0, '*', 1.0, '/']), score=0, feedback='The equation must use all 4 numbers exactly once.')], 'scored_candidates': 'clear', 'depth': 1}}
{'expand': {'candidates': [Candidate(candidate=Equation(tokens=[12.0, 5.0, '-', 1.0, '*']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[1.0, 7.0, '*', 5.0, '+']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[12.0, 1.0, '+', 5.0, '*']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[7.0, 5.0, '*', 1.0, '-']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[12.0, 1.0, '*', 5.0, '-']), score=None, feedback=None)]}}
{'expand': {'candidates': []}}
{'expand': {'candidates': [Candidate(candidate=Equation(tokens=[5.0, 7.0, '*', 12.0, '-']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[1.0, 5.0, 7.0, '*', 12.0, '-', '+']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[12.0, 1.0, '*', 5.0, 7.0, '/']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[12.0, 5.0, '*', 7.0, '/', 1.0, '-']), score=None, feedback=None), Candidate(candidate=Equation(tokens=[5.0, 7.0, '*', 1.0, '-', 12.0, '+']), score=None, feedback=None)]}}
{'score': {'candidates': 'clear', 'scored_candidates': [ScoredCandidate(candidate=Equation(tokens=[12.0, 5.0, '/', 7.0, '*']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[12.0, 1.0, '+', 5.0, '*']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[12.0, 7.0, '*', 1.0, '/']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[5.0, 7.0, '*', 12.0, '-']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[1.0, 5.0, 7.0, '*', 12.0, '-', '+']), score=1.0, feedback='Result: 24.0'), ScoredCandidate(candidate=Equation(tokens=[12.0, 1.0, '*', 5.0, 7.0, '/']), score=0.07692307692307693, feedback='Result: 12.0'), ScoredCandidate(candidate=Equation(tokens=[12.0, 5.0, '*', 7.0, '/', 1.0, '-']), score=0.05737704918032786, feedback='Result: 7.571428571428571'), ScoredCandidate(candidate=Equation(tokens=[5.0, 7.0, '*', 1.0, '-', 12.0, '+']), score=0.043478260869565216, feedback='Result: 46.0'), ScoredCandidate(candidate=Equation(tokens=[12.0, 5.0, '-', 1.0, '*']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[1.0, 7.0, '*', 5.0, '+']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[12.0, 1.0, '+', 5.0, '*']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[7.0, 5.0, '*', 1.0, '-']), score=0, feedback='The equation must use all 4 numbers exactly once.'), ScoredCandidate(candidate=Equation(tokens=[12.0, 1.0, '*', 5.0, '-']), score=0, feedback='The equation must use all 4 numbers exactly once.')]}}
{'prune': {'candidates': [ScoredCandidate(candidate=Equation(tokens=[1.0, 5.0, 7.0, '*', 12.0, '-', '+']), score=1.0, feedback='Result: 24.0'), ScoredCandidate(candidate=Equation(tokens=[12.0, 1.0, '*', 5.0, 7.0, '/']), score=0.07692307692307693, feedback='Result: 12.0'), ScoredCandidate(candidate=Equation(tokens=[12.0, 5.0, '*', 7.0, '/', 1.0, '-']), score=0.05737704918032786, feedback='Result: 7.571428571428571')], 'scored_candidates': 'clear', 'depth': 1}}

```

```md-code__content
final_state = graph.get_state(config)
winning_solution = final_state.values["candidates"][0]
search_depth = final_state.values["depth"]
if winning_solution[1] == 1:
    print(f"Found a winning solution in {search_depth} steps: {winning_solution}")
else:
    print(
        f"Failed to find a winning solution in {search_depth} steps. Best guess: {winning_solution}"
    )

```

```md-code__content
Found a winning solution in 2 steps: [Equation(tokens=[1.0, 5.0, 7.0, '*', 12.0, '-', '+']), 1.0, 'Result: 24.0']

```

## Comments

giscus

#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/2856)

👍1

#### [1 comment](https://github.com/langchain-ai/langgraph/discussions/2856)

#### ·

#### 4 replies

_– powered by [giscus](https://giscus.app/)_

- Oldest
- Newest

[![@pg2455](https://avatars.githubusercontent.com/u/6943817?u=27ffc15d1661ec54f00915c879d1c30b337d91a2&v=4)pg2455](https://github.com/pg2455) [Dec 22, 2024](https://github.com/langchain-ai/langgraph/discussions/2856#discussioncomment-11644793)

Hi,

I think should\_terminate should send the key as 'seed' rather than 'somevalseed' as expected by `ExpansionState`. Is that correct?

Also, can you please explain how the output of `expand` aggregates it's output before `score` is called? Is there a hidden wait that doesn't allow calling `score` before all `expand` s are executed? Are all `exapnd` s executed asynchronously?

1

4 replies

[![@ayush9096](https://avatars.githubusercontent.com/u/35530090?v=4)](https://github.com/ayush9096)

[ayush9096](https://github.com/ayush9096) [Dec 26, 2024](https://github.com/langchain-ai/langgraph/discussions/2856#discussioncomment-11665719)

+1, to the above question.

[![@ayush9096](https://avatars.githubusercontent.com/u/35530090?v=4)](https://github.com/ayush9096)

[ayush9096](https://github.com/ayush9096) [Dec 26, 2024](https://github.com/langchain-ai/langgraph/discussions/2856#discussioncomment-11665761)

Based on the execution steps, it is performing BFS traversal with `expand` waiting for all `Sends` to be executed before moving to `Score` node. How can I configure it to not wait and perform some sort of DFS traversal ?

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)](https://github.com/HoangNguyen689)

[HoangNguyen689](https://github.com/HoangNguyen689) [Jan 16](https://github.com/langchain-ai/langgraph/discussions/2856#discussioncomment-11857005)

Yeah, I think {"seed": candidate} is the right implementation.

> Also, can you please explain how the output of expand aggregates it's output before score is called?

[langgraph/libs/langgraph/langgraph/types.py](https://github.com/langchain-ai/langgraph/blob/adff439d4e64b28f5a54d5809f5b34f4f416d862/libs/langgraph/langgraph/types.py#L177)

Line 177
in
[adff439](https://github.com/)

|     |     |
| --- | --- |
|  | classSend: |

The `Send` function is used for "map-reduce" like and aggregate before execute the next action in graph.

👍1

[![@HoangNguyen689](https://avatars.githubusercontent.com/u/40779936?u=13a36fc6ac5e34554d530c548d2113eaf9ab6674&v=4)](https://github.com/HoangNguyen689)

[HoangNguyen689](https://github.com/HoangNguyen689) [Jan 16](https://github.com/langchain-ai/langgraph/discussions/2856#discussioncomment-11857013)

```notranslate
One such example is a "map-reduce" workflow where your graph invokes
    the same node multiple times in parallel with different states,
    before aggregating the results back into the main graph's state.

```

WritePreview

[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")

[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Ftot%2Ftot%2F)