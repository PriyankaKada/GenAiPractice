#!/usr/bin/env python3
"""
pipeline_agent.py

Full pipeline: problem statement -> generated code -> generated tests -> run tests.

Steps:
  1. coding_agent.run_agent()      -> generates code for the problem, detects language.
  2. test_case_agent.generate_...  -> generates a test suite for that code.
  3. Both are written to disk (solution.<ext> and test_solution.<ext>).
  4. The test suite is actually executed, and the pass/fail result is
     printed back to you.

Execution support:
  - Python: run via pytest (auto-installed if missing).
  - JavaScript/Node: run via Node's built-in `assert` + node, or npx jest
    if a jest test file is detected.
  - Other languages: code + tests are still generated and saved, but
    automatic execution is not wired up yet (compiler/runtime setup
    varies too much to assume) - you'll get clear instructions instead.

Usage:
    python pipeline_agent.py "Write a function to check if a number is prime, in Python"

Requires:
    pip install openai python-dotenv --break-system-packages
    (pytest is auto-installed on demand for Python execution)
"""

import subprocess
import sys
from pathlib import Path

from coding_agent import run_agent, pretty_print
from test_case_agent import generate_test_cases


# Internal-only mapping (not LLM-generated) used purely to decide how to
# save/execute files. Extend as you add more execution backends.
LANGUAGE_EXT = {
    "python": "py",
    "javascript": "js",
    "typescript": "ts",
    "java": "java",
    "c++": "cpp", "cpp": "cpp",
    "c": "c",
    "go": "go",
    "rust": "rs",
}

WORK_DIR = Path("./agent_run")


def ensure_pytest():
    try:
        import pytest  # noqa: F401
    except ImportError:
        pretty_print("pytest not found, installing it now...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest", "--break-system-packages"],
            check=True,
        )


def run_python_tests(code_path: Path, test_path: Path):
    ensure_pytest()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_path.name, "-v"],
        capture_output=True, text=True,
        cwd=str(test_path.parent),
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    output = result.stdout + ("\n" + result.stderr if result.stderr else "")
    return result.returncode == 0, output


def run_node_tests(code_path: Path, test_path: Path):
    node = subprocess.run(["node", "--version"], capture_output=True, text=True)
    if node.returncode != 0:
        msg = "Node.js not found on this system - cannot auto-run JS tests."
        pretty_print(msg)
        return None, msg
    result = subprocess.run(
        ["node", test_path.name], capture_output=True, text=True,
        cwd=str(test_path.parent),
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    output = result.stdout + ("\n" + result.stderr if result.stderr else "")
    return result.returncode == 0, output


def run_tests(language: str, code_path: Path, test_path: Path):
    lang = language.strip().lower()
    if lang == "python":
        return run_python_tests(code_path, test_path)
    if lang in ("javascript", "typescript"):
        return run_node_tests(code_path, test_path)

    msg = (
        f"Automatic execution isn't set up for {language} yet. "
        f"Code saved at {code_path} and tests saved at {test_path} - "
        f"you can compile/run them manually."
    )
    pretty_print(msg)
    return None, msg


def pipeline(problem_prompt: str, model: str = "gpt-4o-mini"):
    # 1. Generate code
    code_resp = run_agent(problem_prompt, model)
    language = code_resp.get("language", "Python")
    code = code_resp.get("code", "")

    print("\n" + "=" * 60 + "\n")

    # 2. Generate tests for that code
    test_resp = generate_test_cases(problem_prompt, language, code, model)
    explanation = test_resp.get("explanation", "")
    test_code = test_resp.get("test_code", "")

    pretty_print("Test coverage:", explanation)
    print("\nGenerated test code:\n")
    print(test_code)

    # 3. Save both files
    ext = LANGUAGE_EXT.get(language.strip().lower(), "txt")
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    code_path = WORK_DIR / f"solution.{ext}"
    test_path = WORK_DIR / f"test_solution.{ext}"

    code_path.write_text(code, encoding="utf-8")
    test_path.write_text(test_code, encoding="utf-8")

    print("\n" + "=" * 60 + "\n")
    pretty_print(f"Saved code to {code_path} and tests to {test_path}. Running tests now...")
    print()

    # 4. Run the tests
    passed, _output = run_tests(language, code_path, test_path)

    print()
    if passed is True:
        pretty_print("Result: ALL TESTS PASSED.")
    elif passed is False:
        pretty_print("Result: TESTS FAILED. See output above for details.")
    # passed is None -> unsupported language, message already printed above

    return code_resp, test_resp, passed


if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Describe the coding problem: ").strip()

    pipeline(prompt)
