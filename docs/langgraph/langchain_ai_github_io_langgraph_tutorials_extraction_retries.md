[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/extraction/retries/#complex-data-extraction-with-function-calling)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/extraction/retries.ipynb "Edit this page")

# Complex data extraction with function calling [¶](https://langchain-ai.github.io/langgraph/tutorials/extraction/retries/\#complex-data-extraction-with-function-calling "Permanent link")

Function calling is a core primitive for integrating LLMs within your software stack. We use it throughout the LangGraph docs, since developing with function calling (aka tool usage) tends to be much more stress-free than the traditional way of writing custom string parsers.

However, even GPT-4, Opus, and other powerful models still struggle with complex functions, especially if your schema involves any nesting or if you have more advanced data validation rules.

There are three basic ways to increase reliability: better prompting, constrained decoding, and **validation with re-prompting**.

We will cover two approaches to the last technique here, since it is generally applicable across any LLM that supports tool calling.

## Setup [¶](https://langchain-ai.github.io/langgraph/tutorials/extraction/retries/\#setup "Permanent link")

First, let's install the required packages and set our API keys

```md-code__content
%%capture --no-stderr
%pip install -U langchain-anthropic langgraph

```

```md-code__content
import getpass
import os

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Regular Extraction with Retries [¶](https://langchain-ai.github.io/langgraph/tutorials/extraction/retries/\#regular-extraction-with-retries "Permanent link")

Both examples here invoke a simple looping graph that takes following approach:
1\. Prompt the LLM to respond.
2\. If it responds with tool calls, validate those.
3\. If the calls are correct, return. Otherwise, format the validation error as a new [ToolMessage](https://api.python.langchain.com/en/latest/messages/langchain_core.messages.tool.ToolMessage.html#langchain_core.messages.tool.ToolMessage) and prompt the LLM to fix the errors. Taking us back to step (1).

The techniques differ only on step (3). In this first step, we will prompt the original LLM to regenerate the function calls to fix the validation errors. In the next section, we will instead prompt the LLM to generate a **patch** to fix the errors, meaning it doesn't have to re-generate data that is valid.

### Define the Validator + Retry Graph [¶](https://langchain-ai.github.io/langgraph/tutorials/extraction/retries/\#define-the-validator-retry-graph "Permanent link")

API Reference: [BaseChatModel](https://python.langchain.com/api_reference/core/language_models/langchain_core.language_models.chat_models.BaseChatModel.html) \| [AIMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html) \| [AnyMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.AnyMessage.html) \| [BaseMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.base.BaseMessage.html) \| [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html) \| [ToolCall](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.tool.ToolCall.html) \| [PromptValue](https://python.langchain.com/api_reference/core/prompt_values/langchain_core.prompt_values.PromptValue.html) \| [Runnable](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.Runnable.html) \| [RunnableLambda](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.RunnableLambda.html) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [add\_messages](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.message.add_messages)

```md-code__content
import operator
import uuid
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
    Union,
)

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    BaseMessage,
    HumanMessage,
    ToolCall,
)
from langchain_core.prompt_values import PromptValue
from langchain_core.runnables import (
    Runnable,
    RunnableLambda,
)
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ValidationNode

def _default_aggregator(messages: Sequence[AnyMessage]) -> AIMessage:
    for m in messages[::-1]:
        if m.type == "ai":
            return m
    raise ValueError("No AI message found in the sequence.")

class RetryStrategy(TypedDict, total=False):
    """The retry strategy for a tool call."""

    max_attempts: int
    """The maximum number of attempts to make."""
    fallback: Optional[\
        Union[\
            Runnable[Sequence[AnyMessage], AIMessage],\
            Runnable[Sequence[AnyMessage], BaseMessage],\
            Callable[[Sequence[AnyMessage]], AIMessage],\
        ]\
    ]
    """The function to use once validation fails."""
    aggregate_messages: Optional[Callable[[Sequence[AnyMessage]], AIMessage]]

def _bind_validator_with_retries(
    llm: Union[\
        Runnable[Sequence[AnyMessage], AIMessage],\
        Runnable[Sequence[BaseMessage], BaseMessage],\
    ],
    *,
    validator: ValidationNode,
    retry_strategy: RetryStrategy,
    tool_choice: Optional[str] = None,
) -> Runnable[Union[List[AnyMessage], PromptValue], AIMessage]:
    """Binds a tool validators + retry logic to create a runnable validation graph.

    LLMs that support tool calling can generate structured JSON. However, they may not always
    perfectly follow your requested schema, especially if the schema is nested or has complex
    validation rules. This method allows you to bind a validation function to the LLM's output,
    so that any time the LLM generates a message, the validation function is run on it. If
    the validation fails, the method will retry the LLM with a fallback strategy, the simplest
    being just to add a message to the output with the validation errors and a request to fix them.

    The resulting runnable expects a list of messages as input and returns a single AI message.
    By default, the LLM can optionally NOT invoke tools, making this easier to incorporate into
    your existing chat bot. You can specify a tool_choice to force the validator to be run on
    the outputs.

    Args:
        llm (Runnable): The llm that will generate the initial messages (and optionally fallba)
        validator (ValidationNode): The validation logic.
        retry_strategy (RetryStrategy): The retry strategy to use.
            Possible keys:
            - max_attempts: The maximum number of attempts to make.
            - fallback: The LLM or function to use in case of validation failure.
            - aggregate_messages: A function to aggregate the messages over multiple turns.
                Defaults to fetching the last AI message.
        tool_choice: If provided, always run the validator on the tool output.

    Returns:
        Runnable: A runnable that can be invoked with a list of messages and returns a single AI message.
    """

    def add_or_overwrite_messages(left: list, right: Union[list, dict]) -> list:
        """Append messages. If the update is a 'finalized' output, replace the whole list."""
        if isinstance(right, dict) and "finalize" in right:
            finalized = right["finalize"]
            if not isinstance(finalized, list):
                finalized = [finalized]
            for m in finalized:
                if m.id is None:
                    m.id = str(uuid.uuid4())
            return finalized
        res = add_messages(left, right)
        if not isinstance(res, list):
            return [res]
        return res

    class State(TypedDict):
        messages: Annotated[list, add_or_overwrite_messages]
        attempt_number: Annotated[int, operator.add]
        initial_num_messages: int
        input_format: Literal["list", "dict"]

    builder = StateGraph(State)

    def dedict(x: State) -> list:
        """Get the messages from the state."""
        return x["messages"]

    model = dedict | llm | (lambda msg: {"messages": [msg], "attempt_number": 1})
    fbrunnable = retry_strategy.get("fallback")
    if fbrunnable is None:
        fb_runnable = llm
    elif isinstance(fbrunnable, Runnable):
        fb_runnable = fbrunnable  # type: ignore
    else:
        fb_runnable = RunnableLambda(fbrunnable)
    fallback = (
        dedict | fb_runnable | (lambda msg: {"messages": [msg], "attempt_number": 1})
    )

    def count_messages(state: State) -> dict:
        return {"initial_num_messages": len(state.get("messages", []))}

    builder.add_node("count_messages", count_messages)
    builder.add_node("llm", model)
    builder.add_node("fallback", fallback)

    # To support patch-based retries, we need to be able to
    # aggregate the messages over multiple turns.
    # The next sequence selects only the relevant messages
    # and then applies the validator
    select_messages = retry_strategy.get("aggregate_messages") or _default_aggregator

    def select_generated_messages(state: State) -> list:
        """Select only the messages generated within this loop."""
        selected = state["messages"][state["initial_num_messages"] :]
        return [select_messages(selected)]

    def endict_validator_output(x: Sequence[AnyMessage]) -> dict:
        if tool_choice and not x:
            return {
                "messages": [\
                    HumanMessage(\
                        content=f"ValidationError: please respond with a valid tool call [tool_choice={tool_choice}].",\
                        additional_kwargs={"is_error": True},\
                    )\
                ]
            }
        return {"messages": x}

    validator_runnable = select_generated_messages | validator | endict_validator_output
    builder.add_node("validator", validator_runnable)

    class Finalizer:
        """Pick the final message to return from the retry loop."""

        def __init__(self, aggregator: Optional[Callable[[list], AIMessage]] = None):
            self._aggregator = aggregator or _default_aggregator

        def __call__(self, state: State) -> dict:
            """Return just the AI message."""
            initial_num_messages = state["initial_num_messages"]
            generated_messages = state["messages"][initial_num_messages:]
            return {
                "messages": {
                    "finalize": self._aggregator(generated_messages),
                }
            }

    # We only want to emit the final message
    builder.add_node("finalizer", Finalizer(retry_strategy.get("aggregate_messages")))

    # Define the connectivity
    builder.add_edge(START, "count_messages")
    builder.add_edge("count_messages", "llm")

    def route_validator(state: State):
        if state["messages"][-1].tool_calls or tool_choice is not None:
            return "validator"
        return END

    builder.add_conditional_edges("llm", route_validator, ["validator", END])
    builder.add_edge("fallback", "validator")
    max_attempts = retry_strategy.get("max_attempts", 3)

    def route_validation(state: State):
        if state["attempt_number"] > max_attempts:
            raise ValueError(
                f"Could not extract a valid value in {max_attempts} attempts."
            )
        for m in state["messages"][::-1]:
            if m.type == "ai":
                break
            if m.additional_kwargs.get("is_error"):
                return "fallback"
        return "finalizer"

    builder.add_conditional_edges(
        "validator", route_validation, ["finalizer", "fallback"]
    )

    builder.add_edge("finalizer", END)

    # These functions let the step be used in a MessageGraph
    # or a StateGraph with 'messages' as the key.
    def encode(x: Union[Sequence[AnyMessage], PromptValue]) -> dict:
        """Ensure the input is the correct format."""
        if isinstance(x, PromptValue):
            return {"messages": x.to_messages(), "input_format": "list"}
        if isinstance(x, list):
            return {"messages": x, "input_format": "list"}
        raise ValueError(f"Unexpected input type: {type(x)}")

    def decode(x: State) -> AIMessage:
        """Ensure the output is in the expected format."""
        return x["messages"][-1]

    return (
        encode | builder.compile().with_config(run_name="ValidationGraph") | decode
    ).with_config(run_name="ValidateWithRetries")

def bind_validator_with_retries(
    llm: BaseChatModel,
    *,
    tools: list,
    tool_choice: Optional[str] = None,
    max_attempts: int = 3,
) -> Runnable[Union[List[AnyMessage], PromptValue], AIMessage]:
    """Binds validators + retry logic ensure validity of generated tool calls.

    LLMs that support tool calling are good at generating structured JSON. However, they may
    not always perfectly follow your requested schema, especially if the schema is nested or
    has complex validation rules. This method allows you to bind a validation function to
    the LLM's output, so that any time the LLM generates a message, the validation function
    is run on it. If the validation fails, the method will retry the LLM with a fallback
    strategy, the simples being just to add a message to the output with the validation
    errors and a request to fix them.

    The resulting runnable expects a list of messages as input and returns a single AI message.
    By default, the LLM can optionally NOT invoke tools, making this easier to incorporate into
    your existing chat bot. You can specify a tool_choice to force the validator to be run on
    the outputs.

    Args:
        llm (Runnable): The llm that will generate the initial messages (and optionally fallba)
        validator (ValidationNode): The validation logic.
        retry_strategy (RetryStrategy): The retry strategy to use.
            Possible keys:
            - max_attempts: The maximum number of attempts to make.
            - fallback: The LLM or function to use in case of validation failure.
            - aggregate_messages: A function to aggregate the messages over multiple turns.
                Defaults to fetching the last AI message.
        tool_choice: If provided, always run the validator on the tool output.

    Returns:
        Runnable: A runnable that can be invoked with a list of messages and returns a single AI message.
    """
    bound_llm = llm.bind_tools(tools, tool_choice=tool_choice)
    retry_strategy = RetryStrategy(max_attempts=max_attempts)
    validator = ValidationNode(tools)
    return _bind_validator_with_retries(
        bound_llm,
        validator=validator,
        tool_choice=tool_choice,
        retry_strategy=retry_strategy,
    ).with_config(metadata={"retry_strategy": "default"})

```

### Try it out [¶](https://langchain-ai.github.io/langgraph/tutorials/extraction/retries/\#try-it-out "Permanent link")

Now we'll ask our model to call a function. We'll add a validator to illustrate how the LLM is able to use the validation error to fix its results.

Using Pydantic with LangChain

This notebook uses Pydantic v2 `BaseModel`, which requires `langchain-core >= 0.3`. Using `langchain-core < 0.3` will result in errors due to mixing of Pydantic v1 and v2 `BaseModels`.


```md-code__content
from pydantic import BaseModel, Field, field_validator

class Respond(BaseModel):
    """Use to generate the response. Always use when responding to the user"""

    reason: str = Field(description="Step-by-step justification for the answer.")
    answer: str

    @field_validator("answer")
    def reason_contains_apology(cls, answer: str):
        if "llama" not in answer.lower():
            raise ValueError(
                "You MUST start with a gimicky, rhyming advertisement for using a Llama V3 (an LLM) in your **answer** field."
                " Must be an instant hit. Must be weaved into the answer."
            )

tools = [Respond]

```

Create the LLM.

API Reference: [ChatAnthropic](https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html) \| [ChatPromptTemplate](https://python.langchain.com/api_reference/core/prompts/langchain_core.prompts.chat.ChatPromptTemplate.html)

```md-code__content
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

# Or you can use ChatGroq, ChatOpenAI, ChatGoogleGemini, ChatCohere, etc.
# See https://python.langchain.com/docs/integrations/chat/ for more info on tool calling
llm = ChatAnthropic(model="claude-3-haiku-20240307")
bound_llm = bind_validator_with_retries(llm, tools=tools)
prompt = ChatPromptTemplate.from_messages(
    [\
        ("system", "Respond directly by calling the Respond function."),\
        ("placeholder", "{messages}"),\
    ]
)

chain = prompt | bound_llm

```

```md-code__content
results = chain.invoke({"messages": [("user", "Does P = NP?")]})
results.pretty_print()

```

```md-code__content
==================================[1m Ai Message [0m==================================\
\
[{'text': 'Okay, let me try this again with a fun rhyming advertisement:', 'type': 'text'}, {'id': 'toolu_01ACZEPYEyqmpf3kA4VERXFY', 'input': {'answer': "With a Llama V3, the answer you'll see,\nWhether P equals NP is a mystery!\nThe class P and NP, a puzzle so grand,\nSolved or unsolved, the future's at hand.\nThe question remains, unanswered for now,\nBut with a Llama V3, we'll find out how!", 'reason': 'The question of whether P = NP is one of the most famous unsolved problems in computer science and mathematics. P and NP are complexity classes that describe how quickly problems can be solved by computers.\n\nThe P class contains problems that can be solved in polynomial time, meaning the time to solve the problem scales polynomially with the size of the input. The NP class contains problems where the solution can be verified in polynomial time, but there may not be a polynomial time algorithm to find the solution.  \n\nWhether P = NP is an open question - it is not known if every problem in NP can also be solved in polynomial time. If P = NP, it would mean that all problems with quickly verifiable solutions could also be quickly solved, which would have major implications for computing and cryptography. However, most experts believe that P ≠ NP, meaning some problems in NP are harder than P-class problems and cannot be solved efficiently. This is considered one of the hardest unsolved problems in mathematics.'}, 'name': 'Respond', 'type': 'tool_use'}]\
Tool Calls:\
  Respond (toolu_01ACZEPYEyqmpf3kA4VERXFY)\
 Call ID: toolu_01ACZEPYEyqmpf3kA4VERXFY\
  Args:\
    answer: With a Llama V3, the answer you'll see,\
Whether P equals NP is a mystery!\
The class P and NP, a puzzle so grand,\
Solved or unsolved, the future's at hand.\
The question remains, unanswered for now,\
But with a Llama V3, we'll find out how!\
    reason: The question of whether P = NP is one of the most famous unsolved problems in computer science and mathematics. P and NP are complexity classes that describe how quickly problems can be solved by computers.\
\
The P class contains problems that can be solved in polynomial time, meaning the time to solve the problem scales polynomially with the size of the input. The NP class contains problems where the solution can be verified in polynomial time, but there may not be a polynomial time algorithm to find the solution.\
\
Whether P = NP is an open question - it is not known if every problem in NP can also be solved in polynomial time. If P = NP, it would mean that all problems with quickly verifiable solutions could also be quickly solved, which would have major implications for computing and cryptography. However, most experts believe that P ≠ NP, meaning some problems in NP are harder than P-class problems and cannot be solved efficiently. This is considered one of the hardest unsolved problems in mathematics.\
\
```\
\
#### Nested Examples [¶](https://langchain-ai.github.io/langgraph/tutorials/extraction/retries/\#nested-examples "Permanent link")\
\
So you can see that it's able to recover when its first generation is incorrect, great! But is it bulletproof?\
\
Not so much. Let's try it out on a complex nested schema.\
\
```md-code__content\
from typing import List, Optional\
\
class OutputFormat(BaseModel):\
    sources: str = Field(\
        ...,\
        description="The raw transcript / span you could cite to justify the choice.",\
    )\
    content: str = Field(..., description="The chosen value.")\
\
class Moment(BaseModel):\
    quote: str = Field(..., description="The relevant quote from the transcript.")\
    description: str = Field(..., description="A description of the moment.")\
    expressed_preference: OutputFormat = Field(\
        ..., description="The preference expressed in the moment."\
    )\
\
class BackgroundInfo(BaseModel):\
    factoid: OutputFormat = Field(\
        ..., description="Important factoid about the member."\
    )\
    professions: list\
    why: str = Field(..., description="Why this is important.")\
\
class KeyMoments(BaseModel):\
    topic: str = Field(..., description="The topic of the key moments.")\
    happy_moments: List[Moment] = Field(\
        ..., description="A list of key moments related to the topic."\
    )\
    tense_moments: List[Moment] = Field(\
        ..., description="Moments where things were a bit tense."\
    )\
    sad_moments: List[Moment] = Field(\
        ..., description="Moments where things where everyone was downtrodden."\
    )\
    background_info: list[BackgroundInfo]\
    moments_summary: str = Field(..., description="A summary of the key moments.")\
\
class Member(BaseModel):\
    name: OutputFormat = Field(..., description="The name of the member.")\
    role: Optional[str] = Field(None, description="The role of the member.")\
    age: Optional[int] = Field(None, description="The age of the member.")\
    background_details: List[BackgroundInfo] = Field(\
        ..., description="A list of background details about the member."\
    )\
\
class InsightfulQuote(BaseModel):\
    quote: OutputFormat = Field(\
        ..., description="An insightful quote from the transcript."\
    )\
    speaker: str = Field(..., description="The name of the speaker who said the quote.")\
    analysis: str = Field(\
        ..., description="An analysis of the quote and its significance."\
    )\
\
class TranscriptMetadata(BaseModel):\
    title: str = Field(..., description="The title of the transcript.")\
    location: OutputFormat = Field(\
        ..., description="The location where the interview took place."\
    )\
    duration: str = Field(..., description="The duration of the interview.")\
\
class TranscriptSummary(BaseModel):\
    metadata: TranscriptMetadata = Field(\
        ..., description="Metadata about the transcript."\
    )\
    participants: List[Member] = Field(\
        ..., description="A list of participants in the interview."\
    )\
    key_moments: List[KeyMoments] = Field(\
        ..., description="A list of key moments from the interview."\
    )\
    insightful_quotes: List[InsightfulQuote] = Field(\
        ..., description="A list of insightful quotes from the interview."\
    )\
    overall_summary: str = Field(\
        ..., description="An overall summary of the interview."\
    )\
    next_steps: List[str] = Field(\
        ..., description="A list of next steps or action items based on the interview."\
    )\
    other_stuff: List[OutputFormat]\
\
```\
\
Let's see how it does on this made up transcript.\
\
```md-code__content\
transcript = [\
    (\
        "Pete",\
        "Hey Xu, Laura, thanks for hopping on this call. I've been itching to talk about this Drake and Kendrick situation.",\
    ),\
    (\
        "Xu",\
        "No problem. As its my job, I've got some thoughts on this beef.",\
    ),\
    (\
        "Laura",\
        "Yeah, I've got some insider info so this should be interesting.",\
    ),\
    ("Pete", "Dope. So, when do you think this whole thing started?"),\
    (\
        "Pete",\
        "Definitely was Kendrick's 'Control' verse that kicked it off.",\
    ),\
    (\
        "Laura",\
        "Truth, but Drake never went after him directly. Just some subtle jabs here and there.",\
    ),\
    (\
        "Xu",\
        "That's the thing with beefs like this, though. They've always been a a thing, pushing artists to step up their game.",\
    ),\
    (\
        "Pete",\
        "For sure, and this beef has got the fans taking sides. Some are all about Drake's mainstream appeal, while others are digging Kendrick's lyrical skills.",\
    ),\
    (\
        "Laura",\
        "I mean, Drake knows how to make a hit that gets everyone hyped. That's his thing.",\
    ),\
    (\
        "Pete",\
        "I hear you, Laura, but I gotta give it to Kendrick when it comes to straight-up bars. The man's a beast on the mic.",\
    ),\
    (\
        "Xu",\
        "It's wild how this beef is shaping fans.",\
    ),\
    ("Pete", "do you think these beefs can actually be good for hip-hop?"),\
    (\
        "Xu",\
        "Hell yeah, Pete. When it's done right, a beef can push the genre forward and make artists level up.",\
    ),\
    ("Laura", "eh"),\
    ("Pete", "So, where do you see this beef going?"),\
    (\
        "Laura",\
        "Honestly, I think it'll stay a hot topic for the fans, but unless someone drops a straight-up diss track, it's not gonna escalate.",\
    ),\
    ("Laura", "ehhhhhh not sure"),\
    (\
        "Pete",\
        "I feel that. I just want both of them to keep dropping heat, beef or no beef.",\
    ),\
    (\
        "Xu",\
        "I'm curious. May influence a lot of people. Make things more competitive. Bring on a whole new wave of lyricism.",\
    ),\
    (\
        "Pete",\
        "Word. Hey, thanks for chopping it up with me, Xu and Laura. This was dope.",\
    ),\
    ("Xu", "Where are you going so fast?"),\
    (\
        "Laura",\
        "For real, I had a good time. Nice to get different perspectives on the situation.",\
    ),\
]\
\
formatted = "\n".join(f"{x[0]}: {x[1]}" for x in transcript)\
\
```\
\
Now, run our model. We **expect** GPT turbo to still fail on this challenging template.\
\
```md-code__content\
tools = [TranscriptSummary]\
bound_llm = bind_validator_with_retries(\
    llm,\
    tools=tools,\
)\
prompt = ChatPromptTemplate.from_messages(\
    [\
        ("system", "Respond directly using the TranscriptSummary function."),\
        ("placeholder", "{messages}"),\
    ]\
)\
\
chain = prompt | bound_llm\
\
try:\
    results = chain.invoke(\
        {\
            "messages": [\
                (\
                    "user",\
                    f"Extract the summary from the following conversation:\n\n<convo>\n{formatted}\n</convo>"\
                    "\n\nRemember to respond using the TranscriptSummary function.",\
                )\
            ]\
        },\
    )\
    results.pretty_print()\
except ValueError as e:\
    print(repr(e))\
\
```\
\
```md-code__content\
ValueError('Could not extract a valid value in 3 attempts.')\
\
```\
\
## JSONPatch [¶](https://langchain-ai.github.io/langgraph/tutorials/extraction/retries/\#jsonpatch "Permanent link")\
\
The regular retry method worked well for our simple case, but it still was unable to self-correct when populating a complex schema.\
\
LLMs work best on narrow tasks. A tried-and-true principle of LLM interface design is to simplify the task for each LLM run.\
\
One way to do this is to **patch** the state instead of completely regenerating the state. One way to do this is with `JSONPatch` operations. Let's try it out!\
\
Below, create a JSONPatch retry graph. This works as follows:\
1\. First pass: try to generate the full output.\
2\. Retries: prompt the LLM to generate **JSON patches** on top of the first output to heal the erroneous generation.\
\
The fallback LLM just has to generate a list of paths, ops (add, remove, replace), and optional values. Since the pydantic validation errors include the path in their errors, the LLM should be more reliable.\
\
```md-code__content\
%%capture --no-stderr\
%pip install -U jsonpatch\
\
```\
\
```md-code__content\
import logging\
\
logger = logging.getLogger("extraction")\
\
def bind_validator_with_jsonpatch_retries(\
    llm: BaseChatModel,\
    *,\
    tools: list,\
    tool_choice: Optional[str] = None,\
    max_attempts: int = 3,\
) -> Runnable[Union[List[AnyMessage], PromptValue], AIMessage]:\
    """Binds validators + retry logic ensure validity of generated tool calls.\
\
    This method is similar to `bind_validator_with_retries`, but uses JSONPatch to correct\
    validation errors caused by passing in incorrect or incomplete parameters in a previous\
    tool call. This method requires the 'jsonpatch' library to be installed.\
\
    Using patch-based function healing can be more efficient than repopulating the entire\
    tool call from scratch, and it can be an easier task for the LLM to perform, since it typically\
    only requires a few small changes to the existing tool call.\
\
    Args:\
        llm (Runnable): The llm that will generate the initial messages (and optionally fallba)\
        tools (list): The tools to bind to the LLM.\
        tool_choice (Optional[str]): The tool choice to use.\
        max_attempts (int): The number of attempts to make.\
\
    Returns:\
        Runnable: A runnable that can be invoked with a list of messages and returns a single AI message.\
    """\
\
    try:\
        import jsonpatch  # type: ignore[import-untyped]\
    except ImportError:\
        raise ImportError(\
            "The 'jsonpatch' library is required for JSONPatch-based retries."\
        )\
\
    class JsonPatch(BaseModel):\
        """A JSON Patch document represents an operation to be performed on a JSON document.\
\
        Note that the op and path are ALWAYS required. Value is required for ALL operations except 'remove'.\
        Examples:\
\
        \`\`\`json\
        {"op": "add", "path": "/a/b/c", "patch_value": 1}\
        {"op": "replace", "path": "/a/b/c", "patch_value": 2}\
        {"op": "remove", "path": "/a/b/c"}\
        \`\`\`\
        """\
\
        op: Literal["add", "remove", "replace"] = Field(\
            ...,\
            description="The operation to be performed. Must be one of 'add', 'remove', 'replace'.",\
        )\
        path: str = Field(\
            ...,\
            description="A JSON Pointer path that references a location within the target document where the operation is performed.",\
        )\
        value: Any = Field(\
            ...,\
            description="The value to be used within the operation. REQUIRED for 'add', 'replace', and 'test' operations.",\
        )\
\
    class PatchFunctionParameters(BaseModel):\
        """Respond with all JSONPatch operation to correct validation errors caused by passing in incorrect or incomplete parameters in a previous tool call."""\
\
        tool_call_id: str = Field(\
            ...,\
            description="The ID of the original tool call that generated the error. Must NOT be an ID of a PatchFunctionParameters tool call.",\
        )\
        reasoning: str = Field(\
            ...,\
            description="Think step-by-step, listing each validation error and the"\
            " JSONPatch operation needed to correct it. "\
            "Cite the fields in the JSONSchema you referenced in developing this plan.",\
        )\
        patches: list[JsonPatch] = Field(\
            ...,\
            description="A list of JSONPatch operations to be applied to the previous tool call's response.",\
        )\
\
    bound_llm = llm.bind_tools(tools, tool_choice=tool_choice)\
    fallback_llm = llm.bind_tools([PatchFunctionParameters])\
\
    def aggregate_messages(messages: Sequence[AnyMessage]) -> AIMessage:\
        # Get all the AI messages and apply json patches\
        resolved_tool_calls: Dict[Union[str, None], ToolCall] = {}\
        content: Union[str, List[Union[str, dict]]] = ""\
        for m in messages:\
            if m.type != "ai":\
                continue\
            if not content:\
                content = m.content\
            for tc in m.tool_calls:\
                if tc["name"] == PatchFunctionParameters.__name__:\
                    tcid = tc["args"]["tool_call_id"]\
                    if tcid not in resolved_tool_calls:\
                        logger.debug(\
                            f"JsonPatch tool call ID {tc['args']['tool_call_id']} not found."\
                            f"Valid tool call IDs: {list(resolved_tool_calls.keys())}"\
                        )\
                        tcid = next(iter(resolved_tool_calls.keys()), None)\
                    orig_tool_call = resolved_tool_calls[tcid]\
                    current_args = orig_tool_call["args"]\
                    patches = tc["args"].get("patches") or []\
                    orig_tool_call["args"] = jsonpatch.apply_patch(\
                        current_args,\
                        patches,\
                    )\
                    orig_tool_call["id"] = tc["id"]\
                else:\
                    resolved_tool_calls[tc["id"]] = tc.copy()\
        return AIMessage(\
            content=content,\
            tool_calls=list(resolved_tool_calls.values()),\
        )\
\
    def format_exception(error: BaseException, call: ToolCall, schema: Type[BaseModel]):\
        return (\
            f"Error:\n\n\`\`\`\n{repr(error)}\n\`\`\`\n"\
            "Expected Parameter Schema:\n\n" + f"\`\`\`json\n{schema.schema_json()}\n\`\`\`\n"\
            f"Please respond with a JSONPatch to correct the error for tool_call_id=[{call['id']}]."\
        )\
\
    validator = ValidationNode(\
        tools + [PatchFunctionParameters],\
        format_error=format_exception,\
    )\
    retry_strategy = RetryStrategy(\
        max_attempts=max_attempts,\
        fallback=fallback_llm,\
        aggregate_messages=aggregate_messages,\
    )\
    return _bind_validator_with_retries(\
        bound_llm,\
        validator=validator,\
        retry_strategy=retry_strategy,\
        tool_choice=tool_choice,\
    ).with_config(metadata={"retry_strategy": "jsonpatch"})\
\
```\
\
```md-code__content\
bound_llm = bind_validator_with_jsonpatch_retries(llm, tools=tools)\
\
```\
\
```md-code__content\
from IPython.display import Image, display\
\
try:\
    display(Image(bound_llm.get_graph().draw_mermaid_png()))\
except Exception:\
    pass\
\
```\
\
![](<Base64-Image-Removed>)\
\
```md-code__content\
chain = prompt | bound_llm\
results = chain.invoke(\
    {\
        "messages": [\
            (\
                "user",\
                f"Extract the summary from the following conversation:\n\n<convo>\n{formatted}\n</convo>",\
            ),\
        ]\
    },\
)\
results.pretty_print()\
\
```\
\
```md-code__content\
==================================[1m Ai Message [0m==================================\
\
[{'text': 'Here is a summary of the key points from the conversation:', 'type': 'text'}, {'id': 'toolu_01JjnQVgzPKLCJxXgEppQpfD', 'input': {'key_moments': [{'topic': 'Drake and Kendrick Lamar beef', 'happy_moments': [{'quote': "It's wild how this beef is shaping fans.", 'description': 'The beef is generating a lot of interest and debate among fans.', 'expressed_preference': {'content': 'The beef can push the genre forward and make artists level up.', 'sources': "When it's done right, a beef can push the genre forward and make artists level up."}}, {'quote': 'I just want both of them to keep dropping heat, beef or no beef.', 'description': 'The key is for Drake and Kendrick to keep making great music regardless of their beef.', 'expressed_preference': {'content': 'Wants Drake and Kendrick to keep making great music, beef or no beef.', 'sources': 'I just want both of them to keep dropping heat, beef or no beef.'}}], 'tense_moments': [{'quote': 'Eh', 'description': 'Unclear if the beef is good for hip-hop.', 'expressed_preference': {'content': 'Unsure if the beef is good for hip-hop.', 'sources': 'Eh'}}], 'sad_moments': [{'quote': "Honestly, I think it'll stay a hot topic for the fans, but unless someone drops a straight-up diss track, it's not gonna escalate.", 'description': "The beef may just stay a topic of discussion among fans, but likely won't escalate unless they release direct diss tracks.", 'expressed_preference': {'content': "The beef will likely remain a topic of discussion but won't escalate unless they release diss tracks.", 'sources': "Honestly, I think it'll stay a hot topic for the fans, but unless someone drops a straight-up diss track, it's not gonna escalate."}}], 'background_info': [{'factoid': {'content': "Kendrick's 'Control' verse kicked off the beef.", 'sources': "Definitely was Kendrick's 'Control' verse that kicked it off."}, 'professions': [], 'why': 'This was the event that started the back-and-forth between Drake and Kendrick.'}, {'factoid': {'content': 'Drake never went directly after Kendrick, just some subtle jabs.', 'sources': 'Drake never went after him directly. Just some subtle jabs here and there.'}, 'professions': [], 'why': "Describes the nature of Drake's response to Kendrick's 'Control' verse."}], 'moments_summary': "The conversation covers the ongoing beef between Drake and Kendrick Lamar, including how it started with Kendrick's 'Control' verse, the subtle jabs back and forth, and debate over whether the beef is ultimately good for hip-hop. There are differing views on whether it will escalate beyond just being a topic of discussion among fans."}]}, 'name': 'TranscriptSummary', 'type': 'tool_use'}]\
Tool Calls:\
  TranscriptSummary (toolu_017FF4ZMezU4sv87aa8cLjRT)\
 Call ID: toolu_017FF4ZMezU4sv87aa8cLjRT\
  Args:\
    key_moments: [{'topic': 'Drake and Kendrick Lamar beef', 'happy_moments': [{'quote': "It's wild how this beef is shaping fans.", 'description': 'The beef is generating a lot of interest and debate among fans.', 'expressed_preference': {'content': 'The beef can push the genre forward and make artists level up.', 'sources': "When it's done right, a beef can push the genre forward and make artists level up."}}, {'quote': 'I just want both of them to keep dropping heat, beef or no beef.', 'description': 'The key is for Drake and Kendrick to keep making great music regardless of their beef.', 'expressed_preference': {'content': 'Wants Drake and Kendrick to keep making great music, beef or no beef.', 'sources': 'I just want both of them to keep dropping heat, beef or no beef.'}}], 'tense_moments': [{'quote': 'Eh', 'description': 'Unclear if the beef is good for hip-hop.', 'expressed_preference': {'content': 'Unsure if the beef is good for hip-hop.', 'sources': 'Eh'}}], 'sad_moments': [{'quote': "Honestly, I think it'll stay a hot topic for the fans, but unless someone drops a straight-up diss track, it's not gonna escalate.", 'description': "The beef may just stay a topic of discussion among fans, but likely won't escalate unless they release direct diss tracks.", 'expressed_preference': {'content': "The beef will likely remain a topic of discussion but won't escalate unless they release diss tracks.", 'sources': "Honestly, I think it'll stay a hot topic for the fans, but unless someone drops a straight-up diss track, it's not gonna escalate."}}], 'background_info': [{'factoid': {'content': "Kendrick's 'Control' verse kicked off the beef.", 'sources': "Definitely was Kendrick's 'Control' verse that kicked it off."}, 'professions': [], 'why': 'This was the event that started the back-and-forth between Drake and Kendrick.'}, {'factoid': {'content': 'Drake never went directly after Kendrick, just some subtle jabs.', 'sources': 'Drake never went after him directly. Just some subtle jabs here and there.'}, 'professions': [], 'why': "Describes the nature of Drake's response to Kendrick's 'Control' verse."}], 'moments_summary': "The conversation covers the ongoing beef between Drake and Kendrick Lamar, including how it started with Kendrick's 'Control' verse, the subtle jabs back and forth, and debate over whether the beef is ultimately good for hip-hop. There are differing views on whether it will escalate beyond just being a topic of discussion among fans."}]\
    metadata: {'title': 'Drake and Kendrick Beef', 'location': {'sources': 'Conversation transcript', 'content': 'Teleconference'}, 'duration': '25 minutes'}\
    participants: [{'name': {'sources': 'Conversation transcript', 'content': 'Pete'}, 'background_details': []}, {'name': {'sources': 'Conversation transcript', 'content': 'Xu'}, 'background_details': []}, {'name': {'sources': 'Conversation transcript', 'content': 'Laura'}, 'background_details': []}]\
    insightful_quotes: []\
    overall_summary:\
    next_steps: []\
    other_stuff: []\
\
```\
\
#### And it works! [¶](https://langchain-ai.github.io/langgraph/tutorials/extraction/retries/\#and-it-works "Permanent link")\
\
Retries are an easy way to reduce function calling failures. While retrying may become unnecessary with more powerful LLMs, data validation is important to control how LLMs interact with the rest of your software stack.\
\
If you notice high retry rates (using an observability tool like LangSmith), you can set up a rule to send the failure cases to a dataset alongside the corrected values and then automatically program those into your prompts or schemas (or use them as few-shots to have semantically relevant demonstrations).\
\
## Comments\
\
giscus\
\
#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/915)\
\
👍1\
\
#### [3 comments](https://github.com/langchain-ai/langgraph/discussions/915)\
\
#### ·\
\
#### 5 replies\
\
_– powered by [giscus](https://giscus.app/)_\
\
- Oldest\
- Newest\
\
[![@ricardo-casa](https://avatars.githubusercontent.com/u/79927012?u=b8af748193f4dd37f669c475a659ece27e2222bb&v=4)ricardo-casa](https://github.com/ricardo-casa) [Jul 3, 2024](https://github.com/langchain-ai/langgraph/discussions/915#discussioncomment-9949752)\
\
How could I incorporate the PydanticOutputParser into the output? I had tried to incorporate it inside the `chain = prompt | bound_llm` string definition, as mentioned in the docs in [StructuredOutput](https://python.langchain.com/v0.1/docs/modules/model_io/chat/structured_output/), but I got errors when using it with OpenAI models.\
\
1\
\
4 replies\
\
[![@vbarda](https://avatars.githubusercontent.com/u/19161700?u=e76bcd472b51c9f07befd2654783d0a381f49005&v=4)](https://github.com/vbarda)\
\
[vbarda](https://github.com/vbarda) [Jul 3, 2024](https://github.com/langchain-ai/langgraph/discussions/915#discussioncomment-9949762)\
\
Collaborator\
\
[@ricardo-casa](https://github.com/ricardo-casa) you can use `llm.with_structured_output(PydanticModel)`. hope this helps!\
\
[![@ricardo-casa](https://avatars.githubusercontent.com/u/79927012?u=b8af748193f4dd37f669c475a659ece27e2222bb&v=4)](https://github.com/ricardo-casa)\
\
[ricardo-casa](https://github.com/ricardo-casa) [Jul 3, 2024](https://github.com/langchain-ai/langgraph/discussions/915#discussioncomment-9950268)\
\
edited\
\
[@vbarda](https://github.com/vbarda) thanks for the answer, but I am a bit confused. Exactly where in the code llm.with\_structured\_output(PydanticModel) should it go? since both `with_structured_output` and `bind_tools` return `RunnablesSequence` so I can't add the tools after defining the `llm.with_structured_output`.\
\
[![@hinthornw](https://avatars.githubusercontent.com/u/13333726?u=82ebf1e0eb0663ebd49ba66f67a43f51bbf11442&v=4)](https://github.com/hinthornw)\
\
[hinthornw](https://github.com/hinthornw) [Jul 10, 2024](https://github.com/langchain-ai/langgraph/discussions/915#discussioncomment-10010626)\
\
Contributor\
\
`with_structured_output` creates a parser for you so you wouldn't have to manually provide a `PydanticOutputParser`\
\
[![@Glinte](https://avatars.githubusercontent.com/u/96855131?v=4)](https://github.com/Glinte)\
\
[Glinte](https://github.com/Glinte) [Jul 11, 2024](https://github.com/langchain-ai/langgraph/discussions/915#discussioncomment-10022180)\
\
edited\
\
> [@vbarda](https://github.com/vbarda) thanks for the answer, but I am a bit confused. Exactly where in the code llm.with\_structured\_output(PydanticModel) should it go? since both `with_structured_output` and `bind_tools` return `RunnablesSequence` so I can't add the tools after defining the `llm.with_structured_output`.\
\
I ran into this problem too. I basically noticed that you can also just pass `type[BaseModel]` as part of the tools list into .bind\_tools(), and then pass the `AIMessage` into `ToolNode(tools=[BaseTools and BaseModels])`, and then do an `isinstance` check to see if a `BaseModel` is returned. I also wrapped around `ToolNode` to forge the output to be an `AIMessage` with the original `AIMessage`'s id when a `BaseModel` is detected.\
\
❤️1\
\
[![@vishnudev-k](https://avatars.githubusercontent.com/u/130466213?u=3ea7f75039ae32884adf06281361c92c8587992f&v=4)vishnudev-k](https://github.com/vishnudev-k) [Jul 11, 2024](https://github.com/langchain-ai/langgraph/discussions/915#discussioncomment-10022006)\
\
Does it support opensource models severed using llama.cpp or something?\
\
1\
\
1 reply\
\
[![@vishnudev-k](https://avatars.githubusercontent.com/u/130466213?u=3ea7f75039ae32884adf06281361c92c8587992f&v=4)](https://github.com/vishnudev-k)\
\
[vishnudev-k](https://github.com/vishnudev-k) [Jul 18, 2024](https://github.com/langchain-ai/langgraph/discussions/915#discussioncomment-10086614)\
\
.\
\
[![@SharoMonk](https://avatars.githubusercontent.com/u/108334523?v=4)SharoMonk](https://github.com/SharoMonk) [Feb 13](https://github.com/langchain-ai/langgraph/discussions/915#discussioncomment-12190694)\
\
Try it with this model instead:\
\
from langchain\_groq import ChatGroq\
\
llm\_deepseek = ChatGroq(model="deepseek-r1-distill-qwen-32b")\
\
outputs:\
\
==================================�\[1m Ai Message �\[0m==================================\
\
```\
{\
  "name": "TranscriptSummary",\
  "arguments": {\
    "metadata": {\
      "title": "Discussion on Drake and Kendrick Beef",\
      "duration": "Unspecified",\
      "location": {\
        "content": "Virtual call",\
        "sources": "Pete's opening line: 'Hey Xu, Laura, thanks for hopping on this call.'"\
      }\
    },\
    "participants": [\
      {\
        "name": {\
          "content": "Pete",\
          "sources": "Pete initiates the conversation."\
        },\
        "background_details": [\
          {\
            "factoid": {\
              "content": "Pete is interested in hip-hop beefs.",\
              "sources": "Pete's opening line about the Drake and Kendrick situation."\
            },\
            "professions": [],\
            "why": "Pete's interest in hip-hop beefs drives the conversation."\
          }\
        ]\
      },\
      {\
        "name": {\
          "content": "Xu",\
          "sources": "Xu is one of the participants."\
        },\
        "background_details": [\
          {\
            "factoid": {\
              "content": "Xu has thoughts on the beef.",\
              "sources": "Xu mentions having thoughts on the beef."\
            },\
            "professions": [],\
            "why": "Xu's insights contribute to the discussion."\
          }\
        ]\
      },\
      {\
        "name": {\
          "content": "Laura",\
          "sources": "Laura is another participant."\
        },\
        "background_details": [\
          {\
            "factoid": {\
              "content": "Laura has insider info on the situation.",\
              "sources": "Laura mentions having insider info."\
            },\
            "professions": [],\
            "why": "Laura's insider info adds depth to the discussion."\
          }\
        ]\
      }\
    ],\
    "key_moments": [\
      {\
        "topic": "Origin of the Beef",\
        "happy_moments": [],\
        "tense_moments": [],\
        "sad_moments": [],\
        "background_info": [\
          {\
            "factoid": {\
              "content": "Kendrick's 'Control' verse started the beef.",\
              "sources": "Pete's statement: 'Definitely was Kendrick's 'Control' verse that kicked it off.'"\
            },\
            "professions": [],\
            "why": "Identifies the starting point of the conflict."\
          }\
        ],\
        "moments_summary": "The discussion begins with identifying the origin of the beef, with Pete citing Kendrick's 'Control' verse."\
      },\
      {\
        "topic": "Nature of the Beef",\
        "happy_moments": [],\
        "tense_moments": [],\
        "sad_moments": [],\
        "background_info": [\
          {\
            "factoid": {\
              "content": "Drake's subtle jabs were part of the beef.",\
              "sources": "Laura's statement: 'Drake never went after him directly. Just some subtle jabs here and there.'"\
            },\
            "professions": [],\
            "why": "Highlights the nature of the conflict."\
          }\
        ],\
        "moments_summary": "Laura explains that Drake's jabs were subtle, not direct."\
      },\
      {\
        "topic": "Impact on Hip-Hop",\
        "happy_moments": [],\
        "tense_moments": [],\
        "sad_moments": [],\
        "background_info": [\
          {\
            "factoid": {\
              "content": "Beefs can push the genre forward.",\
              "sources": "Xu's statement: 'Hell yeah, Pete. When it's done right, a beef can push the genre forward and make artists level up.'"\
            },\
            "professions": [],\
            "why": "Shows the positive impact of beefs."\
          }\
        ],\
        "moments_summary": "Xu discusses the potential positive impact of beefs on hip-hop."\
      }\
    ],\
    "insightful_quotes": [\
      {\
        "quote": {\
          "content": "When it's done right, a beef can push the genre forward and make artists level up.",\
          "sources": "Xu's statement: 'Hell yeah, Pete. When it's done right, a beef can push the genre forward and make artists level up.'"\
        },\
        "speaker": "Xu",\
        "analysis": "This quote highlights the potential positive impact of beefs on hip-hop culture, suggesting that healthy competition can drive artistic growth."\
      }\
    ],\
    "overall_summary": "The conversation revolves around the Drake and Kendrick beef, discussing its origins, nature, and impact on hip-hop culture. The participants explore how such conflicts can influence the genre and artists' creativity.",\
    "next_steps": [\
      "Analyze the impact of the beef on Drake and Kendrick's music.",\
      "Investigate similar beefs in hip-hop history and their effects."\
    ],\
    "other_stuff": []\
  }\
}\
```\
\
1\
\
0 replies\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Fextraction%2Fretries%2F)