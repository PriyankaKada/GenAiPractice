#!/usr/bin/env python3
"""
test_case_agent.py

An agent that generates test cases for code produced by coding_agent.py.

Workflow:
  1. Take a problem statement + the language + the generated code.
  2. Ask the LLM to write a runnable test suite (using the standard
     testing convention for that language, e.g. pytest for Python,
     JUnit for Java, Jest for JavaScript, etc.).
  3. Pretty-print an explanation of the test coverage, then print the
     test code.

Can be used standalone, or chained with coding_agent.run_agent() to go
straight from "problem statement" -> "code" -> "tests" in one run.

Usage:
    python test_case_agent.py "Write a function to check if a number is prime, in Python"

Requires:
    pip install openai python-dotenv --break-system-packages
"""

import sys
import json

# Reuse the already-configured client, pretty_print, and code-generation
# agent from coding_agent.py so API key loading isn't duplicated.
from coding_agent import client, pretty_print, run_agent


TEST_SYSTEM_PROMPT = """You are a test-writing agent. The user will give you:
  - A problem statement
  - The programming language of the solution
  - The solution code itself

Your job:
1. Write a runnable test suite for the given code, using the standard/idiomatic \
testing convention for that language (e.g. pytest for Python, JUnit for Java, \
Jest/Mocha for JavaScript, Go's built-in "testing" package for Go, etc.).
2. Cover: typical/expected cases, edge cases (empty input, zero, negative \
numbers, boundaries, etc. as relevant), and at least one invalid-input case \
if the problem allows for it.
3. IMPORTANT: the solution code will be saved in a file called "solution" \
with the appropriate extension for the language, in the SAME directory as \
the test file. Import/require it accordingly:
   - Python: `from solution import <function_name>`
   - JavaScript: `const { <function_name> } = require('./solution');` \
(assume the solution exports its function(s) via module.exports)
   - Java: assume the class in solution.java is called `Solution`.
   Do not redefine the function in the test file - import/require it.
4. Briefly explain what the test suite covers (2-4 sentences).

Respond with ONLY a single JSON object, no markdown fences, no extra text, \
matching exactly this schema:

{
  "test_code": "<the complete test suite as a single string, with real \\n newlines>",
  "explanation": "<short explanation of what is covered and why>"
}
"""


def generate_test_cases(problem_prompt: str, language: str, code: str,
                         model: str = "gpt-4o-mini") -> dict:
    """Calls the LLM to generate a test suite for the given code."""
    user_content = (
        f"Problem statement:\n{problem_prompt}\n\n"
        f"Language: {language}\n\n"
        f"Solution code:\n{code}"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": TEST_SYSTEM_PROMPT},
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


def run_test_agent(problem_prompt: str, language: str, code: str,
                    model: str = "gpt-4o-mini") -> dict:
    resp = generate_test_cases(problem_prompt, language, code, model)

    explanation = resp.get("explanation", "")
    test_code = resp.get("test_code", "")

    pretty_print("Test coverage:", explanation)
    print("\nGenerated test code:\n")
    print(test_code)

    return resp


def solve_and_test(problem_prompt: str, model: str = "gpt-4o-mini"):
    """Chains coding_agent -> test_case_agent: problem -> code -> tests."""
    code_resp = run_agent(problem_prompt, model)
    print("\n" + "=" * 60 + "\n")
    test_resp = run_test_agent(
        problem_prompt,
        code_resp.get("language", "Python"),
        code_resp.get("code", ""),
        model,
    )
    return code_resp, test_resp


if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Describe the coding problem: ").strip()

    solve_and_test(prompt)
