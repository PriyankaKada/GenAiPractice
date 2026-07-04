"""
schemas.py

Pydantic models used with LangChain's `.with_structured_output()` so each
agent returns a validated typed object instead of hand-parsed JSON.
"""

from typing import Literal
from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    """Output of the intent-detection agent."""
    intent: Literal["generate", "debug"] = Field(
        description=(
            "'generate' if the user described a problem and wants NEW code "
            "written. 'debug' if the user pasted their own existing code "
            "and wants it reviewed, explained, fixed, or tested - this "
            "includes questions like 'what's wrong with this' or 'review "
            "my code', even without the word 'fix'."
        )
    )
    problem_statement: str = Field(
        description="A clear, self-contained description of what the code "
                    "should do, inferred from context if not stated explicitly."
    )
    code: str = Field(
        default="",
        description="The user's original code verbatim, if intent is 'debug'. "
                    "Empty string if intent is 'generate'."
    )
    language: str = Field(
        description="The programming language, detected from the code or "
                    "the user's wording. Default to 'Python' if unclear."
    )


class CodeResult(BaseModel):
    """Output of the coding agent (both fresh generation and fixes)."""
    language: str = Field(description="Human-readable language name, e.g. 'Python', 'Java'.")
    code: str = Field(description="The complete, runnable source code.")
    explanation: str = Field(description="A short (2-4 sentence) explanation of the approach.")


class TestResult(BaseModel):
    """Output of the test-generation agent."""
    test_code: str = Field(description="The complete, runnable test suite.")
    explanation: str = Field(description="A short (2-4 sentence) explanation of test coverage.")
