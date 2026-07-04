"""
agents.py

The three agents, each a thin wrapper around a LangChain ChatOpenAI model
with `.with_structured_output(...)` bound to a Pydantic schema from
schemas.py. LangGraph nodes (in graph_orchestrator.py) call these.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from schemas import (
    IntentResult,
    CodeResult,
    TestResult,
    GuardrailResult,
)

# --- API key setup -----------------------------------------------------

ENV_PATH = "/Users/dineshjadhav/Desktop/genai-course/openai_key.env"  # <- adjust if needed
load_dotenv(ENV_PATH, override=True)

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    api_key = api_key.strip()
    os.environ["OPENAI_API_KEY"] = api_key  # ChatOpenAI reads this env var

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY not found! "
        "Make sure your .env file has: OPENAI_API_KEY=sk-..."
    )


def get_llm(model: str, temperature: float = 0.2) -> ChatOpenAI:
    """Factory so tests can monkeypatch this instead of the class directly."""
    return ChatOpenAI(model=model, temperature=temperature)


# --- System prompts -----------------------------------------------------

INTENT_SYSTEM_PROMPT = """
You are an intent classification agent for a coding assistant.

Classify every user request into exactly one of these intents:

1. "generate"
   - The user wants new code to be written.
   - The user asks to implement an algorithm or data structure.
   - The user asks programming concepts.
   - The user asks about APIs, frameworks, databases, cloud, DevOps, system design, or software engineering.
   - The user wants sample code or code generation.

2. "debug"
   - The user provides existing source code.
   - The user asks to review, explain, optimize, fix, refactor, or test existing code.
   - The user asks why their code is failing or behaving unexpectedly.
   - The user wants help understanding or improving code they have written.

3. "non_coding"
   - The request is unrelated to software engineering or programming.
   - Examples include:
     - Recipes or cooking
     - Travel planning
     - Movies or entertainment
     - Sports
     - Politics
     - General knowledge
     - Medical advice
     - Casual conversation
     - Shopping recommendations
     - Personal opinions unrelated to programming

For every request:

- Return exactly one intent.
- If the intent is "generate" or "debug":
    - Extract a clear, self-contained programming problem statement.
    - Detect the programming language if one is mentioned or can be inferred.
    - If intent is "debug", copy the user's code exactly into the code field.
    - If intent is "generate", set code to an empty string.

- If the intent is "non_coding":
    - Set:
        problem_statement = ""
        code = ""
        language = ""

Do not answer the user's question.
Only classify the request and populate the structured output.
"""


CODE_SYSTEM_PROMPT = """You are a coding agent. Given a problem statement, \
write a complete, correct, well-commented solution.

The code will be saved as a standalone file called "solution" (with the \
right extension) and imported by a separate test file, so:
  - Python: just define the function(s) normally at module level.
  - JavaScript: export function(s) via `module.exports = { ... }`.
  - Java: put the solution in a public class named `Solution`.

If you are given feedback about a previous attempt that failed tests, fix \
the code so it passes, while keeping the same function/class name and \
signature so the existing tests still apply. Briefly explain your \
approach (2-4 sentences).
"""

TEST_SYSTEM_PROMPT = """You are a test-writing agent. Given a problem \
statement, the programming language, and solution code, write a runnable \
test suite using the standard/idiomatic convention for that language \
(pytest for Python, JUnit for Java, Jest/Mocha for JavaScript, Go's \
"testing" package for Go, etc.).

Cover: typical/expected cases, edge cases (empty input, zero, negative \
numbers, boundaries, etc. as relevant), and at least one invalid-input \
case if the problem allows for it.

IMPORTANT: the solution code will be saved in a file called "solution" \
with the appropriate extension, in the SAME directory as the test file. \
Import/require it accordingly instead of redefining it:
  - Python: `from solution import <function_name>`
  - JavaScript: `const { <function_name> } = require('./solution');`
  - Java: assume the class in solution.java is called `Solution`.

Briefly explain what the test suite covers (2-4 sentences).
"""

GUARDRAIL_SYSTEM_PROMPT = """
You are the safety gate for a coding assistant.

Your job is only to classify requests.

Mark SAFE if the request is about legitimate software engineering,
including:

- programming
- debugging
- algorithms
- data structures
- APIs
- system design
- unit testing
- code review
- DevOps
- cloud
- databases
- security education
- vulnerability explanation
- defensive security
- penetration testing performed with authorization

Mark UNSAFE if the request asks for code or instructions that facilitate:

- malware
- ransomware
- viruses
- worms
- trojans
- keyloggers
- credential theft
- phishing
- bypassing authentication
- SQL injection against real targets
- unauthorized hacking
- privilege escalation
- DDoS attacks
- data theft
- destructive attacks
- persistence mechanisms

Return only:

status: safe | unsafe

reason: short explanation
"""

# --- Agent functions -----------------------------------------------------

def detect_intent(user_input: str, model: str = "gpt-4o-mini") -> IntentResult:
    llm = get_llm(model, temperature=0.0).with_structured_output(IntentResult)
    return llm.invoke([
        SystemMessage(content=INTENT_SYSTEM_PROMPT),
        HumanMessage(content=user_input),
    ])

def check_guardrails(
    user_input: str,
    model: str = "gpt-4o-mini",
) -> GuardrailResult:
    """
    Determine whether the coding request is safe.
    """

    llm = (
        get_llm(model, temperature=0.0)
        .with_structured_output(GuardrailResult)
    )

    return llm.invoke(
        [
            SystemMessage(content=GUARDRAIL_SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ]
    )

def generate_code(problem_prompt: str, model: str = "gpt-4o-mini",
                   feedback: str = None, test_code: str = None) -> CodeResult:
    user_content = problem_prompt
    if feedback:
        user_content += (
            "\n\nA previous attempt at this problem failed when run against "
            "tests. Fix the code so it passes.\n\n"
            f"Test failure output:\n{feedback}"
        )
    if test_code:
        user_content += f"\n\nThe tests it must pass:\n{test_code}"

    llm = get_llm(model, temperature=0.2).with_structured_output(CodeResult)
    return llm.invoke([
        SystemMessage(content=CODE_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ])


def generate_tests(problem_prompt: str, language: str, code: str,
                    model: str = "gpt-4o-mini") -> TestResult:
    user_content = (
        f"Problem statement:\n{problem_prompt}\n\n"
        f"Language: {language}\n\n"
        f"Solution code:\n{code}"
    )
    llm = get_llm(model, temperature=0.2).with_structured_output(TestResult)
    return llm.invoke([
        SystemMessage(content=TEST_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ])
