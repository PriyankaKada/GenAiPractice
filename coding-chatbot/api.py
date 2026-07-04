#!/usr/bin/env python3
"""
FastAPI wrapper around the LangGraph coding orchestrator.
"""

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph_orchestrator import orchestrate, MAX_ATTEMPTS

app = FastAPI(
    title="Agentic Code Generation & Testing API",
    description=(
        "Generates or debugs code, creates tests, executes them, "
        f"and retries up to {MAX_ATTEMPTS} times."
    ),
    version="1.1.0",
)


# ---------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------

class SolveRequest(BaseModel):
    problem: str = Field(
        ...,
        description=(
            "Either a programming problem or existing code to debug."
        ),
    )
    model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use.",
    )


# ---------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------

class AttemptResult(BaseModel):
    attempt: int
    passed: Optional[bool]
    output: str
    code: str


class SolveResponse(BaseModel):
    intent: str
    success: bool

    # Populated for blocked/non-coding requests
    response: Optional[str] = None

    attempts_used: int
    max_attempts: int

    language: str
    final_code: str
    test_code: str
    test_explanation: str

    attempts: List[AttemptResult]


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest):

    if not req.problem.strip():
        raise HTTPException(
            status_code=400,
            detail="`problem` cannot be empty.",
        )

    try:
        result = orchestrate(req.problem, req.model)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    return SolveResponse(
        intent=result.get("intent", ""),
        success=result.get("success", False),

        response=result.get("response"),

        attempts_used=result.get("attempts_used", 0),
        max_attempts=MAX_ATTEMPTS,

        language=result.get("language", ""),
        final_code=result.get("final_code", ""),
        test_code=result.get("test_code", ""),
        test_explanation=result.get("test_explanation", ""),

        attempts=[
            AttemptResult(**attempt)
            for attempt in result.get("attempts", [])
        ],
    )