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

from schemas import IntentResult, CodeResult, TestResult

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

INTENT_SYSTEM_PROMPT = """You classify a user's message for a coding \
assistant pipeline. Decide which of two situations applies:

- "generate": the user describes a problem and wants code written for it. \
No existing code was provided (or only a trivial snippet that isn't \
really "their" solution).
- "debug": the user has pasted their own code and wants it reviewed, \
explained, fixed, or tested. This applies even if they didn't explicitly \
say "fix this" - e.g. "what's wrong with this", "why doesn't this work", \
"review my code", or just pasting code with a question, all count as \
"debug".

Also extract a clear problem statement (inferred if needed), the user's \
code verbatim (if intent is "debug", else empty), and the language.
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


# --- Agent functions -----------------------------------------------------

def detect_intent(user_input: str, model: str = "gpt-4o-mini") -> IntentResult:
    llm = get_llm(model, temperature=0.0).with_structured_output(IntentResult)
    return llm.invoke([
        SystemMessage(content=INTENT_SYSTEM_PROMPT),
        HumanMessage(content=user_input),
    ])


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
