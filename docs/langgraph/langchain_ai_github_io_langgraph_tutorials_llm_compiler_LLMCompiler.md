[Skip to content](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/#llmcompiler)

[Edit this page](https://github.com/langchain-ai/langgraph/edit/main/docs/docs/tutorials/llm-compiler/LLMCompiler.ipynb "Edit this page")

# LLMCompiler [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#llmcompiler "Permanent link")

This notebook shows how to implement [LLMCompiler, by Kim, et. al](https://arxiv.org/abs/2312.04511) in LangGraph.

LLMCompiler is an agent architecture designed to **speed up** the execution of agentic tasks by eagerly-executed tasks within a DAG. It also saves costs on redundant token usage by reducing the number of calls to the LLM. Below is an overview of its computational graph:

![LLMCompiler Graph](<Base64-Image-Removed>)

It has 3 main components:

1. Planner: stream a DAG of tasks.
2. Task Fetching Unit: schedules and executes the tasks as soon as they are executable
3. Joiner: Responds to the user or triggers a second plan

This notebook walks through each component and shows how to wire them together using LangGraph. The end result will leave a trace [like the following](https://smith.langchain.com/public/218c2677-c719-4147-b0e9-7bc3b5bb2623/r).

## Setup [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#setup "Permanent link")

First, let's install the required packages and set our API keys

```md-code__content
%%capture --no-stderr
%pip install -U --quiet langchain_openai langsmith langgraph langchain numexpr

```

```md-code__content
import getpass
import os

def _get_pass(var: str):
    if var not in os.environ:
        os.environ[var] = getpass.getpass(f"{var}: ")

_get_pass("OPENAI_API_KEY")

```

Set up [LangSmith](https://smith.langchain.com/) for LangGraph development

Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started [here](https://docs.smith.langchain.com/).


## Helper Files [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#helper-files "Permanent link")

### Math Tools [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#math-tools "Permanent link")

Place the following code in a file called `math_tools.py` and ensure that you can import it into this notebook.

Show/Hide Math Tools

```md-code__content
    import math
    import re
    from typing import List, Optional

    import numexpr
    from langchain.chains.openai_functions import create_structured_output_runnable
    from langchain_core.messages import SystemMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.runnables import RunnableConfig
    from langchain_core.tools import StructuredTool
    from langchain_openai import ChatOpenAI
    from pydantic import BaseModel, Field

    _MATH_DESCRIPTION = (
        "math(problem: str, context: Optional[list[str]]) -> float:\n"
        " - Solves the provided math problem.\n"
        ' - `problem` can be either a simple math problem (e.g. "1 + 3") or a word problem (e.g. "how many apples are there if there are 3 apples and 2 apples").\n'
        " - You cannot calculate multiple expressions in one call. For instance, `math('1 + 3, 2 + 4')` does not work. "
        "If you need to calculate multiple expressions, you need to call them separately like `math('1 + 3')` and then `math('2 + 4')`\n"
        " - Minimize the number of `math` actions as much as possible. For instance, instead of calling "
        '2. math("what is the 10% of $1") and then call 3. math("$1 + $2"), '
        'you MUST call 2. math("what is the 110% of $1") instead, which will reduce the number of math actions.\n'
        # Context specific rules below
        " - You can optionally provide a list of strings as `context` to help the agent solve the problem. "
        "If there are multiple contexts you need to answer the question, you can provide them as a list of strings.\n"
        " - `math` action will not see the output of the previous actions unless you provide it as `context`. "
        "You MUST provide the output of the previous actions as `context` if you need to do math on it.\n"
        " - You MUST NEVER provide `search` type action's outputs as a variable in the `problem` argument. "
        "This is because `search` returns a text blob that contains the information about the entity, not a number or value. "
        "Therefore, when you need to provide an output of `search` action, you MUST provide it as a `context` argument to `math` action. "
        'For example, 1. search("Barack Obama") and then 2. math("age of $1") is NEVER allowed. '
        'Use 2. math("age of Barack Obama", context=["$1"]) instead.\n'
        " - When you ask a question about `context`, specify the units. "
        'For instance, "what is xx in height?" or "what is xx in millions?" instead of "what is xx?"\n'
    )

    _SYSTEM_PROMPT = """Translate a math problem into a expression that can be executed using Python's numexpr library. Use the output of running this code to answer the question.

    Question: ${{Question with math problem.}}

${{single line mathematical expression that solves the problem}}

    ...numexpr.evaluate(text)...

${{Output of running the code}}

    Answer: ${{Answer}}

    Begin.

    Question: What is 37593 * 67?
    ExecuteCode({{code: "37593 * 67"}})
    ...numexpr.evaluate("37593 * 67")...

2518731

    Answer: 2518731

    Question: 37593^(1/5)
    ExecuteCode({{code: "37593**(1/5)"}})
    ...numexpr.evaluate("37593**(1/5)")...

8.222831614237718

    Answer: 8.222831614237718
    """

    _ADDITIONAL_CONTEXT_PROMPT = """The following additional context is provided from other functions.\
        Use it to substitute into any ${{#}} variables or other words in the problem.\
        \n\n${context}\n\nNote that context variables are not defined in code yet.\
    You must extract the relevant numbers and directly put them in code."""

    class ExecuteCode(BaseModel):
        """The input to the numexpr.evaluate() function."""

        reasoning: str = Field(
            ...,
            description="The reasoning behind the code expression, including how context is included, if applicable.",
        )

        code: str = Field(
            ...,
            description="The simple code expression to execute by numexpr.evaluate().",
        )

    def _evaluate_expression(expression: str) -> str:
        try:
            local_dict = {"pi": math.pi, "e": math.e}
            output = str(
                numexpr.evaluate(
                    expression.strip(),
                    global_dict={},  # restrict access to globals
                    local_dict=local_dict,  # add common mathematical functions
                )
            )
        except Exception as e:
            raise ValueError(
                f'Failed to evaluate "{expression}". Raised error: {repr(e)}.'
                " Please try again with a valid numerical expression"
            )

        # Remove any leading and trailing brackets from the output
        return re.sub(r"^\[|\]$", "", output)

    def get_math_tool(llm: ChatOpenAI):
        prompt = ChatPromptTemplate.from_messages(
            [\
                ("system", _SYSTEM_PROMPT),\
                ("user", "{problem}"),\
                MessagesPlaceholder(variable_name="context", optional=True),\
            ]
        )
        extractor = prompt | llm.with_structured_output(ExecuteCode)

        def calculate_expression(
            problem: str,
            context: Optional[List[str]] = None,
            config: Optional[RunnableConfig] = None,
        ):
            chain_input = {"problem": problem}
            if context:
                context_str = "\n".join(context)
                if context_str.strip():
                    context_str = _ADDITIONAL_CONTEXT_PROMPT.format(
                        context=context_str.strip()
                    )
                    chain_input["context"] = [SystemMessage(content=context_str)]
            code_model = extractor.invoke(chain_input, config)
            try:
                return _evaluate_expression(code_model.code)
            except Exception as e:
                return repr(e)

        return StructuredTool.from_function(
            name="math",
            func=calculate_expression,
            description=_MATH_DESCRIPTION,
        )

```

### Output Parser [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#output-parser "Permanent link")

Show/Hide Output Parser

```
    import ast
    import re
    from typing import (
        Any,
        Dict,
        Iterator,
        List,
        Optional,
        Sequence,
        Tuple,
        Union,
    )

    from langchain_core.exceptions import OutputParserException
    from langchain_core.messages import BaseMessage
    from langchain_core.output_parsers.transform import BaseTransformOutputParser
    from langchain_core.runnables import RunnableConfig
    from langchain_core.tools import BaseTool
    from typing_extensions import TypedDict

    THOUGHT_PATTERN = r"Thought: ([^\n]*)"
    ACTION_PATTERN = r"\n*(\d+)\. (\w+)\((.*)\)(\s*#\w+\n)?"
    # $1 or ${1} -> 1
    ID_PATTERN = r"\$\{?(\d+)\}?"
    END_OF_PLAN = ""

    ### Helper functions

    def _ast_parse(arg: str) -> Any:
        try:
            return ast.literal_eval(arg)
        except:  # noqa
            return arg

    def _parse_llm_compiler_action_args(args: str, tool: Union[str, BaseTool]) -> list[Any]:
        """Parse arguments from a string."""
        if args == "":
            return ()
        if isinstance(tool, str):
            return ()
        extracted_args = {}
        tool_key = None
        prev_idx = None
        for key in tool.args.keys():
            # Split if present
            if f"{key}=" in args:
                idx = args.index(f"{key}=")
                if prev_idx is not None:
                    extracted_args[tool_key] = _ast_parse(
                        args[prev_idx:idx].strip().rstrip(",")
                    )
                args = args.split(f"{key}=", 1)[1]
                tool_key = key
                prev_idx = 0
        if prev_idx is not None:
            extracted_args[tool_key] = _ast_parse(
                args[prev_idx:].strip().rstrip(",").rstrip(")")
            )
        return extracted_args

    def default_dependency_rule(idx, args: str):
        matches = re.findall(ID_PATTERN, args)
        numbers = [int(match) for match in matches]
        return idx in numbers

    def _get_dependencies_from_graph(
        idx: int, tool_name: str, args: Dict[str, Any]
    ) -> dict[str, list[str]]:
        """Get dependencies from a graph."""
        if tool_name == "join":
            return list(range(1, idx))
        return [i for i in range(1, idx) if default_dependency_rule(i, str(args))]

    class Task(TypedDict):
        idx: int
        tool: BaseTool
        args: list
        dependencies: Dict[str, list]
        thought: Optional[str]

    def instantiate_task(
        tools: Sequence[BaseTool],
        idx: int,
        tool_name: str,
        args: Union[str, Any],
        thought: Optional[str] = None,
    ) -> Task:
        if tool_name == "join":
            tool = "join"
        else:
            try:
                tool = tools[[tool.name for tool in tools].index(tool_name)]
            except ValueError as e:
                raise OutputParserException(f"Tool {tool_name} not found.") from e
        tool_args = _parse_llm_compiler_action_args(args, tool)
        dependencies = _get_dependencies_from_graph(idx, tool_name, tool_args)

        return Task(
            idx=idx,
            tool=tool,
            args=tool_args,
            dependencies=dependencies,
            thought=thought,
        )

    class LLMCompilerPlanParser(BaseTransformOutputParser[dict], extra="allow"):
        """Planning output parser."""

        tools: List[BaseTool]

        def _transform(self, input: Iterator[Union[str, BaseMessage]]) -> Iterator[Task]:
            texts = []
            # TODO: Cleanup tuple state tracking here.
            thought = None
            for chunk in input:
                # Assume input is str. TODO: support vision/other formats
                text = chunk if isinstance(chunk, str) else str(chunk.content)
                for task, thought in self.ingest_token(text, texts, thought):
                    yield task
            # Final possible task
            if texts:
                task, _ = self._parse_task("".join(texts), thought)
                if task:
                    yield task

        def parse(self, text: str) -> List[Task]:
            return list(self._transform([text]))

        def stream(
            self,
            input: str | BaseMessage,
            config: RunnableConfig | None = None,
            **kwargs: Any | None,
        ) -> Iterator[Task]:
            yield from self.transform([input], config, **kwargs)

        def ingest_token(
            self, token: str, buffer: List[str], thought: Optional[str]
        ) -> Iterator[Tuple[Optional[Task], str]]:
            buffer.append(token)
            if "\n" in token:
                buffer_ = "".join(buffer).split("\n")
                suffix = buffer_[-1]
                for line in buffer_[:-1]:
                    task, thought = self._parse_task(line, thought)
                    if task:
                        yield task, thought
                buffer.clear()
                buffer.append(suffix)

        def _parse_task(self, line: str, thought: Optional[str] = None):
            task = None
            if match := re.match(THOUGHT_PATTERN, line):
                # Optionally, action can be preceded by a thought
                thought = match.group(1)
            elif match := re.match(ACTION_PATTERN, line):
                # if action is parsed, return the task, and clear the buffer
                idx, tool_name, args, _ = match.groups()
                idx = int(idx)
                task = instantiate_task(
                    tools=self.tools,
                    idx=idx,
                    tool_name=tool_name,
                    args=args,
                    thought=thought,
                )
                thought = None
            # Else it is just dropped
            return task, thought

```

## Define Tools [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#define-tools "Permanent link")

We'll first define the tools for the agent to use in our demo. We'll give it the class search engine + calculator combo.

If you don't want to sign up for tavily, you can replace it with the free [DuckDuckGo](https://python.langchain.com/docs/integrations/tools/ddg/).

API Reference: [TavilySearchResults](https://python.langchain.com/api_reference/community/tools/langchain_community.tools.tavily_search.tool.TavilySearchResults.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html)

```md-code__content
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from math_tools import get_math_tool

_get_pass("TAVILY_API_KEY")

calculate = get_math_tool(ChatOpenAI(model="gpt-4-turbo-preview"))
search = TavilySearchResults(
    max_results=1,
    description='tavily_search_results_json(query="the search query") - a search engine.',
)

tools = [search, calculate]

```

```md-code__content
calculate.invoke(
    {
        "problem": "What's the temp of sf + 5?",
        "context": ["Thet empreature of sf is 32 degrees"],
    }
)

```

```md-code__content
'37'

```

## Planner [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#planner "Permanent link")

Largely adapted from [the original source code](https://github.com/SqueezeAILab/LLMCompiler/blob/main/src/llm_compiler/output_parser.py), the planner accepts the input question and generates a task list to execute.

If it is provided with a previous plan, it is instructed to re-plan, which is useful if, upon completion of the first batch of tasks, the agent must take more actions.

The code below composes constructs the prompt template for the planner and composes it with LLM and output parser, defined in `output_parser.py`. The output parser processes a task list in the following form:

```md-code__content
1. tool_1(arg1="arg1", arg2=3.5, ...)
Thought: I then want to find out Y by using tool_2
2. tool_2(arg1="", arg2="${1}")'
3. join()<END_OF_PLAN>"

```

The "Thought" lines are optional. The `${#}` placeholders are variables. These are used to route tool (task) outputs to other tools.

API Reference: [BaseChatModel](https://python.langchain.com/api_reference/core/language_models/langchain_core.language_models.chat_models.BaseChatModel.html) \| [BaseMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.base.BaseMessage.html) \| [FunctionMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.function.FunctionMessage.html) \| [HumanMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.human.HumanMessage.html) \| [SystemMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.system.SystemMessage.html) \| [ChatPromptTemplate](https://python.langchain.com/api_reference/core/prompts/langchain_core.prompts.chat.ChatPromptTemplate.html) \| [RunnableBranch](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.branch.RunnableBranch.html) \| [BaseTool](https://python.langchain.com/api_reference/core/tools/langchain_core.tools.base.BaseTool.html) \| [ChatOpenAI](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html)

```md-code__content
from typing import Sequence

from langchain import hub
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from output_parser import LLMCompilerPlanParser, Task

prompt = hub.pull("wfh/llm-compiler")
print(prompt.pretty_print())

```

```md-code__content
================================[1m System Message [0m================================\
\
Given a user query, create a plan to solve it with the utmost parallelizability. Each plan should comprise an action from the following [33;1m[1;3m{num_tools}[0m types:\
[33;1m[1;3m{tool_descriptions}[0m\
[33;1m[1;3m{num_tools}[0m. join(): Collects and combines results from prior actions.\
\
 - An LLM agent is called upon invoking join() to either finalize the user query or wait until the plans are executed.\
 - join should always be the last action in the plan, and will be called in two scenarios:\
   (a) if the answer can be determined by gathering the outputs from tasks to generate the final response.\
   (b) if the answer cannot be determined in the planning phase before you execute the plans. Guidelines:\
 - Each action described above contains input/output types and description.\
    - You must strictly adhere to the input and output types for each action.\
    - The action descriptions contain the guidelines. You MUST strictly follow those guidelines when you use the actions.\
 - Each action in the plan should strictly be one of the above types. Follow the Python conventions for each action.\
 - Each action MUST have a unique ID, which is strictly increasing.\
 - Inputs for actions can either be constants or outputs from preceding actions. In the latter case, use the format $id to denote the ID of the previous action whose output will be the input.\
 - Always call join as the last action in the plan. Say '<END_OF_PLAN>' after you call join\
 - Ensure the plan maximizes parallelizability.\
 - Only use the provided action types. If a query cannot be addressed using these, invoke the join action for the next steps.\
 - Never introduce new actions other than the ones provided.\
\
=============================[1m Messages Placeholder [0m=============================\
\
[33;1m[1;3m{messages}[0m\
\
================================[1m System Message [0m================================\
\
Remember, ONLY respond with the task list in the correct format! E.g.:\
idx. tool(arg_name=args)\
None\
\
```\
\
```md-code__content\
def create_planner(\
    llm: BaseChatModel, tools: Sequence[BaseTool], base_prompt: ChatPromptTemplate\
):\
    tool_descriptions = "\n".join(\
        f"{i+1}. {tool.description}\n"\
        for i, tool in enumerate(\
            tools\
        )  # +1 to offset the 0 starting index, we want it count normally from 1.\
    )\
    planner_prompt = base_prompt.partial(\
        replan="",\
        num_tools=len(tools)\
        + 1,  # Add one because we're adding the join() tool at the end.\
        tool_descriptions=tool_descriptions,\
    )\
    replanner_prompt = base_prompt.partial(\
        replan=' - You are given "Previous Plan" which is the plan that the previous agent created along with the execution results '\
        "(given as Observation) of each plan and a general thought (given as Thought) about the executed results."\
        'You MUST use these information to create the next plan under "Current Plan".\n'\
        ' - When starting the Current Plan, you should start with "Thought" that outlines the strategy for the next plan.\n'\
        " - In the Current Plan, you should NEVER repeat the actions that are already executed in the Previous Plan.\n"\
        " - You must continue the task index from the end of the previous one. Do not repeat task indices.",\
        num_tools=len(tools) + 1,\
        tool_descriptions=tool_descriptions,\
    )\
\
    def should_replan(state: list):\
        # Context is passed as a system message\
        return isinstance(state[-1], SystemMessage)\
\
    def wrap_messages(state: list):\
        return {"messages": state}\
\
    def wrap_and_get_last_index(state: list):\
        next_task = 0\
        for message in state[::-1]:\
            if isinstance(message, FunctionMessage):\
                next_task = message.additional_kwargs["idx"] + 1\
                break\
        state[-1].content = state[-1].content + f" - Begin counting at : {next_task}"\
        return {"messages": state}\
\
    return (\
        RunnableBranch(\
            (should_replan, wrap_and_get_last_index | replanner_prompt),\
            wrap_messages | planner_prompt,\
        )\
        | llm\
        | LLMCompilerPlanParser(tools=tools)\
    )\
\
```\
\
```md-code__content\
llm = ChatOpenAI(model="gpt-4-turbo-preview")\
# This is the primary "agent" in our application\
planner = create_planner(llm, tools, prompt)\
\
```\
\
```md-code__content\
example_question = "What's the temperature in SF raised to the 3rd power?"\
\
for task in planner.stream([HumanMessage(content=example_question)]):\
    print(task["tool"], task["args"])\
    print("---")\
\
```\
\
```md-code__content\
description='tavily_search_results_json(query="the search query") - a search engine.' max_results=1 api_wrapper=TavilySearchAPIWrapper(tavily_api_key=SecretStr('**********')) {'query': 'current temperature in San Francisco'}\
---\
name='math' description='math(problem: str, context: Optional[list[str]]) -> float:\n - Solves the provided math problem.\n - `problem` can be either a simple math problem (e.g. "1 + 3") or a word problem (e.g. "how many apples are there if there are 3 apples and 2 apples").\n - You cannot calculate multiple expressions in one call. For instance, `math(\'1 + 3, 2 + 4\')` does not work. If you need to calculate multiple expressions, you need to call them separately like `math(\'1 + 3\')` and then `math(\'2 + 4\')`\n - Minimize the number of `math` actions as much as possible. For instance, instead of calling 2. math("what is the 10% of $1") and then call 3. math("$1 + $2"), you MUST call 2. math("what is the 110% of $1") instead, which will reduce the number of math actions.\n - You can optionally provide a list of strings as `context` to help the agent solve the problem. If there are multiple contexts you need to answer the question, you can provide them as a list of strings.\n - `math` action will not see the output of the previous actions unless you provide it as `context`. You MUST provide the output of the previous actions as `context` if you need to do math on it.\n - You MUST NEVER provide `search` type action\'s outputs as a variable in the `problem` argument. This is because `search` returns a text blob that contains the information about the entity, not a number or value. Therefore, when you need to provide an output of `search` action, you MUST provide it as a `context` argument to `math` action. For example, 1. search("Barack Obama") and then 2. math("age of $1") is NEVER allowed. Use 2. math("age of Barack Obama", context=["$1"]) instead.\n - When you ask a question about `context`, specify the units. For instance, "what is xx in height?" or "what is xx in millions?" instead of "what is xx?"' args_schema=<class 'langchain_core.utils.pydantic.math'> func=<function get_math_tool.<locals>.calculate_expression at 0x11bed0fe0> {'problem': 'x ** 3', 'context': ['$1']}\
---\
join ()\
---\
\
```\
\
## Task Fetching Unit [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#task-fetching-unit "Permanent link")\
\
This component schedules the tasks. It receives a stream of tools of the following format:\
\
```md-code__content\
{\
    tool: BaseTool,\
    dependencies: number[],\
}\
\
```\
\
The basic idea is to begin executing tools as soon as their dependencies are met. This is done through multi-threading. We will combine the task fetching unit and executor below:\
\
![diagram](<Base64-Image-Removed>)\
\
API Reference: [chain](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.chain.html)\
\
```md-code__content\
import re\
import time\
from concurrent.futures import ThreadPoolExecutor, wait\
from typing import Any, Dict, Iterable, List, Union\
\
from langchain_core.runnables import (\
    chain as as_runnable,\
)\
from typing_extensions import TypedDict\
\
def _get_observations(messages: List[BaseMessage]) -> Dict[int, Any]:\
    # Get all previous tool responses\
    results = {}\
    for message in messages[::-1]:\
        if isinstance(message, FunctionMessage):\
            results[int(message.additional_kwargs["idx"])] = message.content\
    return results\
\
class SchedulerInput(TypedDict):\
    messages: List[BaseMessage]\
    tasks: Iterable[Task]\
\
def _execute_task(task, observations, config):\
    tool_to_use = task["tool"]\
    if isinstance(tool_to_use, str):\
        return tool_to_use\
    args = task["args"]\
    try:\
        if isinstance(args, str):\
            resolved_args = _resolve_arg(args, observations)\
        elif isinstance(args, dict):\
            resolved_args = {\
                key: _resolve_arg(val, observations) for key, val in args.items()\
            }\
        else:\
            # This will likely fail\
            resolved_args = args\
    except Exception as e:\
        return (\
            f"ERROR(Failed to call {tool_to_use.name} with args {args}.)"\
            f" Args could not be resolved. Error: {repr(e)}"\
        )\
    try:\
        return tool_to_use.invoke(resolved_args, config)\
    except Exception as e:\
        return (\
            f"ERROR(Failed to call {tool_to_use.name} with args {args}."\
            + f" Args resolved to {resolved_args}. Error: {repr(e)})"\
        )\
\
def _resolve_arg(arg: Union[str, Any], observations: Dict[int, Any]):\
    # $1 or ${1} -> 1\
    ID_PATTERN = r"\$\{?(\d+)\}?"\
\
    def replace_match(match):\
        # If the string is ${123}, match.group(0) is ${123}, and match.group(1) is 123.\
\
        # Return the match group, in this case the index, from the string. This is the index\
        # number we get back.\
        idx = int(match.group(1))\
        return str(observations.get(idx, match.group(0)))\
\
    # For dependencies on other tasks\
    if isinstance(arg, str):\
        return re.sub(ID_PATTERN, replace_match, arg)\
    elif isinstance(arg, list):\
        return [_resolve_arg(a, observations) for a in arg]\
    else:\
        return str(arg)\
\
@as_runnable\
def schedule_task(task_inputs, config):\
    task: Task = task_inputs["task"]\
    observations: Dict[int, Any] = task_inputs["observations"]\
    try:\
        observation = _execute_task(task, observations, config)\
    except Exception:\
        import traceback\
\
        observation = traceback.format_exception()  # repr(e) +\
    observations[task["idx"]] = observation\
\
def schedule_pending_task(\
    task: Task, observations: Dict[int, Any], retry_after: float = 0.2\
):\
    while True:\
        deps = task["dependencies"]\
        if deps and (any([dep not in observations for dep in deps])):\
            # Dependencies not yet satisfied\
            time.sleep(retry_after)\
            continue\
        schedule_task.invoke({"task": task, "observations": observations})\
        break\
\
@as_runnable\
def schedule_tasks(scheduler_input: SchedulerInput) -> List[FunctionMessage]:\
    """Group the tasks into a DAG schedule."""\
    # For streaming, we are making a few simplifying assumption:\
    # 1. The LLM does not create cyclic dependencies\
    # 2. That the LLM will not generate tasks with future deps\
    # If this ceases to be a good assumption, you can either\
    # adjust to do a proper topological sort (not-stream)\
    # or use a more complicated data structure\
    tasks = scheduler_input["tasks"]\
    args_for_tasks = {}\
    messages = scheduler_input["messages"]\
    # If we are re-planning, we may have calls that depend on previous\
    # plans. Start with those.\
    observations = _get_observations(messages)\
    task_names = {}\
    originals = set(observations)\
    # ^^ We assume each task inserts a different key above to\
    # avoid race conditions...\
    futures = []\
    retry_after = 0.25  # Retry every quarter second\
    with ThreadPoolExecutor() as executor:\
        for task in tasks:\
            deps = task["dependencies"]\
            task_names[task["idx"]] = (\
                task["tool"] if isinstance(task["tool"], str) else task["tool"].name\
            )\
            args_for_tasks[task["idx"]] = task["args"]\
            if (\
                # Depends on other tasks\
                deps and (any([dep not in observations for dep in deps]))\
            ):\
                futures.append(\
                    executor.submit(\
                        schedule_pending_task, task, observations, retry_after\
                    )\
                )\
            else:\
                # No deps or all deps satisfied\
                # can schedule now\
                schedule_task.invoke(dict(task=task, observations=observations))\
                # futures.append(executor.submit(schedule_task.invoke, dict(task=task, observations=observations)))\
\
        # All tasks have been submitted or enqueued\
        # Wait for them to complete\
        wait(futures)\
    # Convert observations to new tool messages to add to the state\
    new_observations = {\
        k: (task_names[k], args_for_tasks[k], observations[k])\
        for k in sorted(observations.keys() - originals)\
    }\
    tool_messages = [\
        FunctionMessage(\
            name=name,\
            content=str(obs),\
            additional_kwargs={"idx": k, "args": task_args},\
            tool_call_id=k,\
        )\
        for k, (name, task_args, obs) in new_observations.items()\
    ]\
    return tool_messages\
\
```\
\
```md-code__content\
import itertools\
\
@as_runnable\
def plan_and_schedule(state):\
    messages = state["messages"]\
    tasks = planner.stream(messages)\
    # Begin executing the planner immediately\
    try:\
        tasks = itertools.chain([next(tasks)], tasks)\
    except StopIteration:\
        # Handle the case where tasks is empty.\
        tasks = iter([])\
    scheduled_tasks = schedule_tasks.invoke(\
        {\
            "messages": messages,\
            "tasks": tasks,\
        }\
    )\
    return {"messages": scheduled_tasks}\
\
```\
\
### Example Plan [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#example-plan "Permanent link")\
\
We still haven't introduced any cycles in our computation graph, so this is all easily expressed in LCEL.\
\
```md-code__content\
tool_messages = plan_and_schedule.invoke(\
    {"messages": [HumanMessage(content=example_question)]}\
)["messages"]\
\
```\
\
```md-code__content\
tool_messages\
\
```\
\
```md-code__content\
[FunctionMessage(content="[{'url': 'https://www.accuweather.com/en/us/san-francisco/94103/current-weather/347629', 'content': 'Get the latest weather information for San Francisco, CA, including temperature, wind, humidity, pressure, and UV index. See hourly, daily, and monthly forecasts, as ...'}]", additional_kwargs={'idx': 1, 'args': {'query': 'current temperature in San Francisco'}}, response_metadata={}, name='tavily_search_results_json', tool_call_id=1),\
 FunctionMessage(content='ValueError(\'Failed to evaluate "No specific value for \\\'x\\\' provided.". Raised error: SyntaxError(\\\'invalid syntax\\\', (\\\'<expr>\\\', 1, 4, "No specific value for \\\'x\\\' provided.", 1, 12)). Please try again with a valid numerical expression\')', additional_kwargs={'idx': 2, 'args': {'problem': 'x^3', 'context': ['$1']}}, response_metadata={}, name='math', tool_call_id=2),\
 FunctionMessage(content='join', additional_kwargs={'idx': 3, 'args': ()}, response_metadata={}, name='join', tool_call_id=3)]\
\
```\
\
## Joiner [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#joiner "Permanent link")\
\
So now we have the planning and initial execution done. We need a component to process these outputs and either:\
\
1. Respond with the correct answer.\
2. Loop with a new plan.\
\
The paper refers to this as the "joiner". It's another LLM call. We are using function calling to improve parsing reliability.\
\
Using Pydantic with LangChain\
\
This notebook uses Pydantic v2 `BaseModel`, which requires `langchain-core >= 0.3`. Using `langchain-core < 0.3` will result in errors due to mixing of Pydantic v1 and v2 `BaseModels`.\
\
\
API Reference: [AIMessage](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html)\
\
```md-code__content\
from langchain_core.messages import AIMessage\
\
from pydantic import BaseModel, Field\
\
class FinalResponse(BaseModel):\
    """The final response/answer."""\
\
    response: str\
\
class Replan(BaseModel):\
    feedback: str = Field(\
        description="Analysis of the previous attempts and recommendations on what needs to be fixed."\
    )\
\
class JoinOutputs(BaseModel):\
    """Decide whether to replan or whether you can return the final response."""\
\
    thought: str = Field(\
        description="The chain of thought reasoning for the selected action"\
    )\
    action: Union[FinalResponse, Replan]\
\
joiner_prompt = hub.pull("wfh/llm-compiler-joiner").partial(\
    examples=""\
)  # You can optionally add examples\
llm = ChatOpenAI(model="gpt-4-turbo-preview")\
\
runnable = joiner_prompt | llm.with_structured_output(\
    JoinOutputs, method="function_calling"\
)\
\
```\
\
We will select only the most recent messages in the state, and format the output to be more useful for\
the planner, should the agent need to loop.\
\
```md-code__content\
def _parse_joiner_output(decision: JoinOutputs) -> List[BaseMessage]:\
    response = [AIMessage(content=f"Thought: {decision.thought}")]\
    if isinstance(decision.action, Replan):\
        return {\
            "messages": response\
            + [\
                SystemMessage(\
                    content=f"Context from last attempt: {decision.action.feedback}"\
                )\
            ]\
        }\
    else:\
        return {"messages": response + [AIMessage(content=decision.action.response)]}\
\
def select_recent_messages(state) -> dict:\
    messages = state["messages"]\
    selected = []\
    for msg in messages[::-1]:\
        selected.append(msg)\
        if isinstance(msg, HumanMessage):\
            break\
    return {"messages": selected[::-1]}\
\
joiner = select_recent_messages | runnable | _parse_joiner_output\
\
```\
\
```md-code__content\
input_messages = [HumanMessage(content=example_question)] + tool_messages\
\
```\
\
```md-code__content\
joiner.invoke({"messages": input_messages})\
\
```\
\
```md-code__content\
{'messages': [AIMessage(content='Thought: Since the temperature in San Francisco was not provided, I cannot calculate its value raised to the 3rd power. The search result did not include specific temperature information, and the subsequent action to calculate the power raised the error due to lack of numerical input.', additional_kwargs={}, response_metadata={}),\
  SystemMessage(content="Context from last attempt: To answer the user's question, we need the current temperature in San Francisco. Please include a step to find the current temperature in San Francisco and then calculate its value raised to the 3rd power.", additional_kwargs={}, response_metadata={})]}\
\
```\
\
## Compose using LangGraph [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#compose-using-langgraph "Permanent link")\
\
We'll define the agent as a stateful graph, with the main nodes being:\
\
1. Plan and execute (the DAG from the first step above)\
2. Join: determine if we should finish or replan\
3. Recontextualize: update the graph state based on the output from the joiner\
\
API Reference: [END](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.END) \| [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) \| [START](https://langchain-ai.github.io/langgraph/reference/constants/#langgraph.constants.START) \| [add\_messages](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.message.add_messages)\
\
```md-code__content\
from langgraph.graph import END, StateGraph, START\
from langgraph.graph.message import add_messages\
from typing import Annotated\
\
class State(TypedDict):\
    messages: Annotated[list, add_messages]\
\
graph_builder = StateGraph(State)\
\
# 1.  Define vertices\
# We defined plan_and_schedule above already\
# Assign each node to a state variable to update\
graph_builder.add_node("plan_and_schedule", plan_and_schedule)\
graph_builder.add_node("join", joiner)\
\
## Define edges\
graph_builder.add_edge("plan_and_schedule", "join")\
\
### This condition determines looping logic\
\
def should_continue(state):\
    messages = state["messages"]\
    if isinstance(messages[-1], AIMessage):\
        return END\
    return "plan_and_schedule"\
\
graph_builder.add_conditional_edges(\
    "join",\
    # Next, we pass in the function that will determine which node is called next.\
    should_continue,\
)\
graph_builder.add_edge(START, "plan_and_schedule")\
chain = graph_builder.compile()\
\
```\
\
### Simple question [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#simple-question "Permanent link")\
\
Let's ask a simple question of the agent.\
\
```md-code__content\
for step in chain.stream(\
    {"messages": [HumanMessage(content="What's the GDP of New York?")]}\
):\
    print(step)\
    print("---")\
\
```\
\
```md-code__content\
{'plan_and_schedule': {'messages': [FunctionMessage(content="[{'url': 'https://www.investopedia.com/articles/investing/011516/new-yorks-economy-6-industries-driving-gdp-growth.asp', 'content': 'The manufacturing sector is a leader in railroad rolling stock, as many of the earliest railroads were financed or founded in New York; garments, as New York City is the fashion capital of the U.S.; elevator parts; glass; and many other products.\\n Educational Services\\nThough not typically thought of as a leading industry, the educational sector in New York nonetheless has a substantial impact on the state and its residents, and in attracting new talent that eventually enters the New York business scene. New York has seen a large uptick in college attendees, both young and old, over the 21st century, and an increasing number of new employees in other New York sectors were educated in the state. New York City is the leading job hub for banking, finance, and communication in the U.S. New York is also a major manufacturing center and shipping port, and it has a thriving technological sector.\\n The state of New York has the third-largest economy in the United States with a gross domestic product (GDP) of $1.7 trillion, trailing only Texas and California.'}]", additional_kwargs={'idx': 1, 'args': {'query': 'GDP of New York'}}, response_metadata={}, name='tavily_search_results_json', tool_call_id=1)]}}\
---\
{'join': {'messages': [AIMessage(content='Thought: The search result provides the specific information requested. It states that the state of New York has the third-largest economy in the United States with a GDP of $1.7 trillion.', additional_kwargs={}, response_metadata={}, id='63af07a6-f931-43e9-8fdc-4f2b8c7b7663'), AIMessage(content='The GDP of New York is $1.7 trillion.', additional_kwargs={}, response_metadata={}, id='7cfc50e6-e041-4985-a5f4-ebf2e097826e')]}}\
---\
\
```\
\
```md-code__content\
# Final answer\
print(step["join"]["messages"][-1].content)\
\
```\
\
```md-code__content\
The GDP of New York is $1.7 trillion.\
\
```\
\
### Multi-hop question [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#multi-hop-question "Permanent link")\
\
This question requires that the agent perform multiple searches.\
\
```md-code__content\
steps = chain.stream(\
    {\
        "messages": [\
            HumanMessage(\
                content="What's the oldest parrot alive, and how much longer is that than the average?"\
            )\
        ]\
    },\
    {\
        "recursion_limit": 100,\
    },\
)\
for step in steps:\
    print(step)\
    print("---")\
\
```\
\
```md-code__content\
{'plan_and_schedule': {'messages': [FunctionMessage(content='[{\'url\': \'https://en.wikipedia.org/wiki/Cookie_(cockatoo)\', \'content\': \'He was one of the longest-lived birds on record[4] and was recognised by the Guinness World Records as the oldest living parrot in the world.[5]\\nThe next-oldest pink cockatoo to be found in a zoological setting was a 31-year-old female bird located at Paradise Wildlife Sanctuary, England.[3] Information published by the World Parrot Trust states longevity for Cookie\\\'s species in captivity is on average 40–60 years.[6]\\nLife[edit]\\nCookie was Brookfield Zoo\\\'s oldest resident and the last surviving member of the animal collection from the time of the zoo\\\'s opening in 1934, having arrived from Taronga Zoo of Sydney, New South Wales, Australia, in the same year and judged to be one year old at the time.[7]\\nIn the 1950s an attempt was made to introduce Cookie to a female pink cockatoo, but Cookie rejected her as "she was not nice to him".[8]\\n In 2007, Cookie was diagnosed with, and placed on medication and nutritional supplements for, osteoarthritis and osteoporosis\\xa0– medical conditions which occur commonly in aging animals and humans alike,[7] although it is believed that the latter may also have been brought on as a result of being fed a seed-only diet for the first 40 years of his life, in the years before the dietary requirements of his species were fully understood.[9]\\nCookie was "retired" from exhibition at the zoo in 2009 (following a few months of weekend-only appearances) in order to preserve his health, after it was noticed by staff that his appetite, demeanor and stress levels improved markedly when not on public display. age.[11] A memorial at the zoo was unveiled in September 2017.[12]\\nIn 2020, Cookie became the subject of a poetry collection by Barbara Gregorich entitled Cookie the Cockatoo: Everything Changes.[13]\\nSee also[edit]\\nReferences[edit]\\nExternal links[edit] He was believed to be the oldest member of his species alive in captivity, at the age of 82 in June 2015,[1]\[2] having significantly exceeded the average lifespan for his kind.[3] He was moved to a permanent residence in the keepers\\\' office of the zoo\\\'s Perching Bird House, although he made occasional appearances for special events, such as his birthday celebration, which was held each June.[3]\'}]', additional_kwargs={'idx': 1, 'args': {'query': 'oldest parrot alive'}}, response_metadata={}, name='tavily_search_results_json', tool_call_id=1), FunctionMessage(content="[{'url': 'https://www.birdzilla.com/learn/how-long-do-parrots-live/', 'content': 'In captivity, they can easily live to be ten or even 18 years of age. In general, most wild parrot species live only half the numbers of years they would live in captivity. For example, adopted African Gray Parrots might live to be 60, whereas wild birds have an average lifespan of 30 or 40 at the very most.'}]", additional_kwargs={'idx': 2, 'args': {'query': 'average lifespan of a parrot'}}, response_metadata={}, name='tavily_search_results_json', tool_call_id=2), FunctionMessage(content='join', additional_kwargs={'idx': 3, 'args': ()}, response_metadata={}, name='join', tool_call_id=3)]}}\
---\
{'join': {'messages': [AIMessage(content="Thought: The information from Wikipedia about Cookie, the cockatoo, indicates that he was recognized as the oldest living parrot, reaching the age of 82. This significantly exceeds the average lifespan for his species, which is noted to be 40-60 years in captivity. The information from Birdzilla provides a more general perspective on parrot lifespans, indicating that, in captivity, parrots can easily live to be ten or even 18 years of age, with some species like the African Gray Parrot potentially living up to 60 years. However, it does not provide a specific average lifespan for all parrot species, making it challenging to provide a precise comparison for Cookie's age beyond his species' average lifespan.", additional_kwargs={}, response_metadata={}, id='f00a464e-c273-42b9-8d1b-edd27bde8687'), AIMessage(content="Cookie the cockatoo was recognized as the oldest living parrot, reaching the age of 82, which is significantly beyond the average lifespan for his species, noted to be between 40-60 years in captivity. While general information for parrots suggests varying lifespans with some capable of living up to 60 years in captivity, Cookie's age far exceeded these averages, highlighting his exceptional longevity.", additional_kwargs={}, response_metadata={}, id='dc62a826-5528-446e-8797-6854abdeb94c')]}}\
---\
\
```\
\
```md-code__content\
# Final answer\
print(step["join"]["messages"][-1].content)\
\
```\
\
```md-code__content\
Cookie the cockatoo was recognized as the oldest living parrot, reaching the age of 82, which is significantly beyond the average lifespan for his species, noted to be between 40-60 years in captivity. While general information for parrots suggests varying lifespans with some capable of living up to 60 years in captivity, Cookie's age far exceeded these averages, highlighting his exceptional longevity.\
\
```\
\
### Multi-step math [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#multi-step-math "Permanent link")\
\
```md-code__content\
for step in chain.stream(\
    {\
        "messages": [\
            HumanMessage(\
                content="What's ((3*(4+5)/0.5)+3245) + 8? What's 32/4.23? What's the sum of those two values?"\
            )\
        ]\
    }\
):\
    print(step)\
\
```\
\
```md-code__content\
{'plan_and_schedule': {'messages': [FunctionMessage(content='3307.0', additional_kwargs={'idx': 1, 'args': {'problem': '((3*(4+5)/0.5)+3245) + 8'}}, response_metadata={}, name='math', tool_call_id=1), FunctionMessage(content='7.565011820330969', additional_kwargs={'idx': 2, 'args': {'problem': '32/4.23'}}, response_metadata={}, name='math', tool_call_id=2), FunctionMessage(content='join', additional_kwargs={'idx': 3, 'args': ()}, response_metadata={}, name='join', tool_call_id=3)]}}\
{'join': {'messages': [AIMessage(content="Thought: The calculations for both the expressions provided by the user have been successfully completed, with the results being 3307.0 for the first expression and 7.565011820330969 for the second. Therefore, we have all the necessary information to answer the user's question.", additional_kwargs={}, response_metadata={}, id='2dd394b3-468a-4abc-b7d2-02f7b803a8b6'), AIMessage(content='The result of the first calculation ((3*(4+5)/0.5)+3245) + 8 is 3307.0, and the result of the second calculation (32/4.23) is approximately 7.57. The sum of those two values is 3307.0 + 7.57 = approximately 3314.57.', additional_kwargs={}, response_metadata={}, id='83eb8e01-7a0a-4f79-8475-fad5bc83e645')]}}\
\
```\
\
```md-code__content\
# Final answer\
print(step["join"]["messages"][-1].content)\
\
```\
\
```md-code__content\
The result of the first calculation ((3*(4+5)/0.5)+3245) + 8 is 3307.0, and the result of the second calculation (32/4.23) is approximately 7.57. The sum of those two values is 3307.0 + 7.57 = approximately 3314.57.\
\
```\
\
### Complex Replanning Example [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#complex-replanning-example "Permanent link")\
\
This question is likely to prompt the Replan functionality, but it may need to be run multiple times to see this in action.\
\
```md-code__content\
for step in chain.stream(\
    {\
        "messages": [\
            HumanMessage(\
                content="Find the current temperature in Tokyo, then, respond with a flashcard summarizing this information"\
            )\
        ]\
    }\
):\
    print(step)\
\
```\
\
```md-code__content\
{'plan_and_schedule': {'messages': [FunctionMessage(content="[{'url': 'https://www.timeanddate.com/weather/japan/tokyo/ext', 'content': 'Tokyo 14 Day Extended Forecast. Weather Today Weather Hourly 14 Day Forecast Yesterday/Past Weather Climate (Averages) Currently: 84 °F. Partly sunny. (Weather station: Tokyo, Japan). See more current weather.'}]", additional_kwargs={'idx': 1, 'args': {'query': 'current temperature in Tokyo'}}, response_metadata={}, name='tavily_search_results_json', tool_call_id=1), FunctionMessage(content='join', additional_kwargs={'idx': 2, 'args': ()}, response_metadata={}, name='join', tool_call_id=2)]}}\
{'join': {'messages': [AIMessage(content='Thought: The extracted information provides the current temperature in Tokyo, which is 84 °F and describes the weather as partly sunny. This information is sufficient to create a flashcard summary for the user.', additional_kwargs={}, response_metadata={}, id='e9a1af40-ca06-4eb8-b4bb-24429cf8c689'), AIMessage(content='**Flashcard: Current Temperature in Tokyo**\n\n- **Temperature:** 84 °F\n- **Weather Conditions:** Partly sunny\n\n*Note: This information is based on the latest available data and may change.*', additional_kwargs={}, response_metadata={}, id='92bb42bc-e9b9-4b98-8936-8f74ff111504')]}}\
\
```\
\
## Conclusion [¶](https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/\#conclusion "Permanent link")\
\
Congrats on building your first LLMCompiler agent! I'll leave you with some known limitations to the implementation above:\
\
1. The planner output parsing format is fragile if your function requires more than 1 or 2 arguments. We could make it more robust by using streaming tool calling.\
2. Variable substitution is fragile in the example above. It could be made more robust by using a fine-tuned model and a more robust syntax (using e.g., Lark or a tool calling schema)\
3. The state can grow quite long if you require multiple re-planning runs. To handle, you could add a message compressor once you go above a certain token limit.\
\
## Comments\
\
giscus\
\
#### [1 reaction](https://github.com/langchain-ai/langgraph/discussions/742)\
\
👍1\
\
#### [4 comments](https://github.com/langchain-ai/langgraph/discussions/742)\
\
#### ·\
\
#### 1 reply\
\
_– powered by [giscus](https://giscus.app/)_\
\
- Oldest\
- Newest\
\
[![@atacankural](https://avatars.githubusercontent.com/u/61664490?u=c9fe661da79321af15aea1a33c32802511315d1a&v=4)atacankural](https://github.com/atacankural) [Jun 21, 2024](https://github.com/langchain-ai/langgraph/discussions/742#discussioncomment-9840697)\
\
Thanks for the nice project!\
\
Hi I get an error on part 2:\
\
AttributeError: 'TavilySearchResults' object has no attribute 'func'\
\
Could you please help me?\
\
1\
\
0 replies\
\
[![@dopc](https://avatars.githubusercontent.com/u/29026534?u=a6ad1ea4ae0ddf4727405323d8fd0be597a728d4&v=4)dopc](https://github.com/dopc) [Jul 26, 2024](https://github.com/langchain-ai/langgraph/discussions/742#discussioncomment-10159753)\
\
Hey!\
\
I am trying to use [PlayWright browser tools](https://python.langchain.com/v0.1/docs/integrations/toolkits/playwright/) with this LLMCompiler implementation.\
\
However,\
\
1. with `create_async_playwright_browser`, I got the error below:\
\
`ValueError('Synchronous browser not provided to navigate_browser')`\
\
\
Here is a [related issue](https://github.com/langchain-ai/langchain/issues/3903) with this error,\
2. with `create_sync_playwright_browser`, I got the error below:\
\
`error('cannot switch to a different thread')`\
\
\
Here is a [related issue](https://github.com/microsoft/playwright-python/issues/1422) with this error.\
\
Can you please help me?\
\
1\
\
0 replies\
\
[![@crazyyanchao](https://avatars.githubusercontent.com/u/19403898?u=653236a54c30bcaf89100a4eb3f6684c97be8664&v=4)crazyyanchao](https://github.com/crazyyanchao) [Aug 5, 2024](https://github.com/langchain-ai/langgraph/discussions/742#discussioncomment-10238217)\
\
[This is a complete implementation of LLMCompiler](https://github.com/crazyyanchao/llmcompiler), which has been verified for use in enterprise applications, welcome to use it and raise an issue!\
\
1\
\
👍2\
\
1 reply\
\
[![@wuyanghui](https://avatars.githubusercontent.com/u/50493454?v=4)](https://github.com/wuyanghui)\
\
[wuyanghui](https://github.com/wuyanghui) [Sep 12, 2024](https://github.com/langchain-ai/langgraph/discussions/742#discussioncomment-10623799)\
\
Does this support AzureOpenAI?\
\
[![@pazevedo-hyland](https://avatars.githubusercontent.com/u/185094512?v=4)pazevedo-hyland](https://github.com/pazevedo-hyland) [Dec 16, 2024](https://github.com/langchain-ai/langgraph/discussions/742#discussioncomment-11578713)\
\
Is this example up to date with the latest Chat Models from langchain?\
\
```\
for task in planner.stream([HumanMessage(content=example_question)]):\
    print(task["tool"], task["args"])\
    print("---")\
```\
\
ValueError: System message must be at beginning of message list.\
\
1\
\
0 replies\
\
WritePreview\
\
[Styling with Markdown is supported](https://guides.github.com/features/mastering-markdown/ "Styling with Markdown is supported")\
\
[Sign in with GitHub](https://giscus.app/api/oauth/authorize?redirect_uri=https%3A%2F%2Flangchain-ai.github.io%2Flanggraph%2Ftutorials%2Fllm-compiler%2FLLMCompiler%2F)