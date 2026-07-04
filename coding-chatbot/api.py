#!/usr/bin/env python3
"""
api.py

FastAPI wrapper around the orchestrator, so the whole agentic pipeline
(generate code -> generate tests -> run tests -> retry up to 3x on
failure) is available over HTTP.

Run it:
    pip install fastapi uvicorn --break-system-packages
    uvicorn api:app --reload --port 8000

Then call it:
    curl -X POST http://localhost:8000/solve \\
        -H "Content-Type: application/json" \\
        -d '{"problem": "Write a function to check if a number is prime, in Python"}'

Docs (interactive):
    http://localhost:8000/docs
"""

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph_orchestrator import orchestrate, MAX_ATTEMPTS

app = FastAPI(
    title="Agentic Code Generation & Testing API",
    description=(
        "Given a problem statement, an orchestrator coordinates a coding "
        "agent and a test-generation agent, runs the tests, and retries "
        f"(regenerating the code) up to {MAX_ATTEMPTS} times if tests fail."
    ),
    version="1.0.0",
)


class SolveRequest(BaseModel):
    problem: str = Field(
        ...,
        description=(
            "Either a problem statement to generate code for, OR your own "
            "code (with or without an explanation) that you want checked, "
            "debugged, and tested. The orchestrator detects which one this "
            "is automatically."
        ),
    )
    model: str = Field("gpt-4o-mini", description="The OpenAI model to use.")


class AttemptResult(BaseModel):
    attempt: int
    passed: Optional[bool]
    output: str
    code: str


class SolveResponse(BaseModel):
    intent: str
    success: bool
    attempts_used: int
    max_attempts: int
    language: str
    final_code: str
    test_code: str
    test_explanation: str
    attempts: List[AttemptResult]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest):
    if not req.problem.strip():
        raise HTTPException(status_code=400, detail="`problem` cannot be empty.")

    try:
        result = orchestrate(req.problem, req.model)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return SolveResponse(
        intent=result["intent"],
        success=result["success"],
        attempts_used=result["attempts_used"],
        max_attempts=MAX_ATTEMPTS,
        language=result["language"],
        final_code=result["final_code"],
        test_code=result["test_code"],
        test_explanation=result.get("test_explanation", ""),
        attempts=result["attempts"],
    )
