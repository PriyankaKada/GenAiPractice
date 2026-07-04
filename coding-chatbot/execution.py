"""
execution.py

Runs generated test suites against generated code. Pure subprocess/file
logic - no LLM calls here.
"""

import subprocess
import sys
from pathlib import Path

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


def ensure_pytest():
    try:
        import pytest  # noqa: F401
    except ImportError:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest", "--break-system-packages"],
            check=True,
        )


def run_python_tests(test_path: Path):
    ensure_pytest()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_path.name, "-v"],
        capture_output=True, text=True,
        cwd=str(test_path.parent),
    )
    output = result.stdout + ("\n" + result.stderr if result.stderr else "")
    return result.returncode == 0, output


def run_node_tests(test_path: Path):
    node = subprocess.run(["node", "--version"], capture_output=True, text=True)
    if node.returncode != 0:
        return None, "Node.js not found on this system - cannot auto-run JS tests."
    result = subprocess.run(
        ["node", test_path.name], capture_output=True, text=True,
        cwd=str(test_path.parent),
    )
    output = result.stdout + ("\n" + result.stderr if result.stderr else "")
    return result.returncode == 0, output


def run_tests(language: str, code_path: Path, test_path: Path):
    """Returns (passed: bool|None, output: str). None = execution unsupported."""
    lang = language.strip().lower()
    if lang == "python":
        return run_python_tests(test_path)
    if lang in ("javascript", "typescript"):
        return run_node_tests(test_path)

    msg = (
        f"Automatic execution isn't set up for {language} yet. "
        f"Code saved at {code_path} and tests saved at {test_path} - "
        f"you can compile/run them manually."
    )
    return None, msg
