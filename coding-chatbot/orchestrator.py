#!/usr/bin/env python3
"""
orchestrator.py

The orchestrator coordinates two agents:
  - coding_agent      -> generates/regenerates the solution code
  - test_case_agent   -> generates the test suite

Workflow:
  1. coding_agent generates code for the problem statement (attempt 1).
  2. test_case_agent generates a test suite ONCE, based on that first
     attempt (the tests stay fixed across retries so the "spec" doesn't
     move - only the code changes).
  3. The tests are executed against the code.
  4. If they pass -> done, return success.
  5. If they fail -> feed the failure output + the fixed test suite back
     to coding_agent, ask it to regenerate the code, and re-run the same
     tests. This repeats for a MAXIMUM of 3 total attempts (not more).
  6. Whether it ultimately passes or not, a full attempt-by-attempt log
     is returned so callers (e.g. the FastAPI layer) can inspect what
     happened at each step.

This module has no CLI/print dependency on the terminal - it's designed
to be called from other Python code (like a FastAPI endpoint) and
returns a plain dict, but also exposes a __main__ block for manual runs.
"""

import sys
from pathlib import Path
from typing import Optional

import coding_agent
import test_case_agent
import pipeline_agent
import intent_agent

MAX_ATTEMPTS = 3
WORK_DIR = Path("./agent_run")


def orchestrate(user_input: str, model: str = "gpt-4o-mini") -> dict:
    """
    Runs the full agent loop and returns a structured result:

    {
        "intent": "generate" | "debug",
        "success": bool,
        "attempts_used": int,
        "language": str,
        "final_code": str,
        "test_code": str,
        "attempts": [
            {"attempt": 1, "passed": bool | None, "output": str, "code": str},
            ...
        ]
    }

    Routing:
      - intent == "generate": coding_agent writes fresh code for the
        problem statement (original behavior).
      - intent == "debug": the user's own code is used as-is for attempt
        1 - coding_agent is skipped for the first attempt, and the
        orchestrator goes straight to test generation + execution. If
        the user's code fails the tests, coding_agent is then used only
        to FIX it (still bounded by MAX_ATTEMPTS), not to rewrite it
        from scratch.
    """
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    attempts_log = []

    # --- Step 0: figure out what the user actually wants ---
    intent_resp = intent_agent.detect_intent(user_input, model)
    intent = intent_resp["intent"]
    problem_prompt = intent_resp["problem_statement"]
    language = intent_resp["language"]

    # --- Attempt 1: get the starting code, either from the user or fresh ---
    if intent == "debug" and intent_resp.get("code"):
        code = intent_resp["code"]
    else:
        intent = "generate"  # normalize: no usable code was actually given
        code_resp = coding_agent.call_llm(problem_prompt, model)
        language = code_resp.get("language", language)
        code = code_resp.get("code", "")

    # --- Generate the test suite once, from this starting code ---
    test_resp = test_case_agent.generate_test_cases(problem_prompt, language, code, model)
    test_code = test_resp.get("test_code", "")
    test_explanation = test_resp.get("explanation", "")

    ext = pipeline_agent.LANGUAGE_EXT.get(language.strip().lower(), "txt")
    code_path = WORK_DIR / f"solution.{ext}"
    test_path = WORK_DIR / f"test_solution.{ext}"

    passed = None
    output = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        code_path.write_text(code, encoding="utf-8")
        test_path.write_text(test_code, encoding="utf-8")

        passed, output = pipeline_agent.run_tests(language, code_path, test_path)

        attempts_log.append({
            "attempt": attempt,
            "passed": passed,
            "output": output,
            "code": code,
        })

        # Stop conditions: tests passed, execution unsupported for this
        # language (passed is None), or we've used all attempts.
        if passed is True or passed is None or attempt == MAX_ATTEMPTS:
            break

        # --- Fix/regenerate code using the failure as feedback ---
        # Same call whether intent was "generate" or "debug" - the
        # feedback+test_code framing already tells coding_agent to FIX
        # the existing code rather than start over.
        code_resp = coding_agent.call_llm(
            problem_prompt, model, feedback=output, test_code=test_code
        )
        code = code_resp.get("code", code)

    return {
        "intent": intent,
        "success": bool(passed),
        "attempts_used": len(attempts_log),
        "language": language,
        "final_code": attempts_log[-1]["code"],
        "test_code": test_code,
        "test_explanation": test_explanation,
        "attempts": attempts_log,
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Describe the coding problem: ").strip()

    result = orchestrate(prompt)

    print("\n" + "=" * 60)
    print(f"Intent: {result['intent']}")
    print(f"Language: {result['language']}")
    print(f"Attempts used: {result['attempts_used']} / {MAX_ATTEMPTS}")
    print(f"Success: {result['success']}")
    print("=" * 60 + "\n")
    print("Final code:\n")
    print(result["final_code"])
    print("\nTest code:\n")
    print(result["test_code"])
