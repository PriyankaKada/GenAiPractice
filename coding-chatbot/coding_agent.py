#!/usr/bin/env python3
"""
coding_agent.py

An agent that:
  1. Loads your OpenAI API key from a .env file.
  2. Takes a problem statement (with or without an explicit language).
  3. Asks the LLM to detect the target programming language and
     generate a solution.
  4. Pretty-prints the language + explanation, prints the code, and
     saves the code to a file with the correct extension.

Usage:
    python coding_agent.py
    python coding_agent.py "Write a function to reverse a linked list in Java"

Requires:
    pip install openai python-dotenv --break-system-packages
"""

import os
import sys
import json
import textwrap

from dotenv import load_dotenv
from openai import OpenAI


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

ENV_PATH = "/Users/dineshjadhav/Desktop/genai-course/openai_key.env"  # <- adjust if needed

load_dotenv(ENV_PATH, override=True)

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    api_key = api_key.strip()

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY not found! "
        "Make sure your .env file has: OPENAI_API_KEY=sk-..."
    )

client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = """You are a coding agent. The user will give you a problem \
statement written in natural language. Your job:

1. Determine which programming language the user wants the solution in.
   - If a language is explicitly named, use that one.
   - If it's only hinted at (framework names, syntax, file extension), \
infer it from context.
   - If no language is specified or implied at all, default to Python.
2. Write a complete, correct, well-commented solution to the problem in \
that language. The code will be saved as a standalone file called \
"solution" (with the right extension) and imported by a separate test \
file, so:
   - Python: just define the function(s) normally at module level.
   - JavaScript: export function(s) via `module.exports = { ... }`.
   - Java: put the solution in a public class named `Solution`.
3. Briefly explain your solution (2-4 sentences).

Respond with ONLY a single JSON object, no markdown fences, no extra text, \
matching exactly this schema:

{
  "language": "<human readable name, e.g. 'Python', 'Java'>",
  "code": "<the complete source code as a single string, with real \\n newlines>",
  "explanation": "<short explanation of the approach>"
}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pretty_print(*args):
    text = " ".join(str(arg) for arg in args)
    try:
        print(textwrap.fill(text, width=80))
    except Exception:
        print(text)  # fallback to normal print if text isn't a plain string


def call_llm(problem_prompt: str, model: str = "gpt-4o-mini",
             feedback: str = None, test_code: str = None) -> dict:
    """Calls the LLM and returns a parsed dict: language, code, explanation.

    If `feedback` (e.g. a failing test run's output) and optionally the
    `test_code` it failed against are provided, the model is asked to fix
    the previous attempt while keeping the same function name/signature
    so the existing tests still apply.
    """
    user_content = problem_prompt
    if feedback:
        user_content += (
            "\n\nA previous attempt at this problem failed when run against "
            "tests. Fix the code so it passes. Keep the same function/class "
            "name and signature so the existing tests still apply.\n\n"
            f"Test failure output:\n{feedback}"
        )
    if test_code:
        user_content += f"\n\nThe tests it must pass:\n{test_code}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(f"Model did not return valid JSON:\n{raw}")


def run_agent(problem_prompt: str, model: str = "gpt-4o-mini"):
    resp = call_llm(problem_prompt, model)

    language = resp.get("language", "Unknown")
    code = resp.get("code", "")
    explanation = resp.get("explanation", "")

    pretty_print("Detected language:", language)
    pretty_print("Explanation:", explanation)

    print("\nGenerated code:\n")
    print(code)

    return resp


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Describe the coding problem: ").strip()

    run_agent(prompt)
