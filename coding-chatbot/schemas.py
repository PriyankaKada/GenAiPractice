"""
schemas.py

Pydantic models used with LangChain's `.with_structured_output()` so each
agent returns a validated typed object instead of hand-parsed JSON.
"""

from typing import Literal
from pydantic import BaseModel, Field


from typing import Literal
from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    """Output of the intent-detection agent."""

    intent: Literal["generate", "debug", "non_coding"] = Field(
        description=(
            "'generate' if the user wants new code to be written. "
            "'debug' if the user provides existing code and wants it "
            "reviewed, explained, fixed, optimized, or tested. "
            "'non_coding' if the request is unrelated to software "
            "development or programming."
        )
    )

    problem_statement: str = Field(
        default="",
        description=(
            "A clear, self-contained programming problem. "
            "Leave empty for non_coding requests."
        ),
    )

    code: str = Field(
        default="",
        description=(
            "The user's original source code exactly as provided. "
            "Only populated when intent is 'debug'."
        ),
    )

    language: str = Field(
        default="",
        description=(
            "Programming language of the request or supplied code. "
            "Leave empty for non_coding requests."
        ),
    )

    response: str = Field(
        default="",
        description=(
            "Only populated when intent is 'non_coding'. "
            "Contains a polite message explaining that the assistant "
            "is a coding agent and cannot answer non-programming questions."
        ),
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


class GuardrailResult(BaseModel):
    """Output of the guardrail agent."""

    status: Literal["safe", "unsafe"] = Field(
        description="Whether the coding request is safe to execute."
    )

    reason: str = Field(
        description="Short explanation for the safety decision."
    )