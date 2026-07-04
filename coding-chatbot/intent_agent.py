#!/usr/bin/env python3
"""
intent_agent.py

An agent whose only job is to look at the user's raw input and decide:

  - "generate": the user gave a problem statement and wants NEW code
                written for it.
  - "debug":    the user already pasted their own code (with or without
                a problem statement) and wants it checked/fixed - so the
                orchestrator should skip code generation and go straight
                to testing/fixing THEIR code.

It also extracts the pieces the orchestrator needs either way: a clean
problem statement, the user's code (if any), and the language.
"""

import sys
import json

from coding_agent import client


INTENT_SYSTEM_PROMPT = """You classify a user's message for a coding \
assistant pipeline. Decide which of two situations applies:

- "generate": the user describes a problem and wants code written for \
it. No existing code was provided (or only a trivial snippet that isn't \
really "their" solution).
- "debug": the user has pasted their own code (a function, script, etc.) \
and wants it reviewed, explained, fixed, or tested. This applies even if \
they didn't explicitly say "fix this" - e.g. "what's wrong with this", \
"why doesn't this work", "review my code", or just pasting code with a \
question, all count as "debug".

Also extract:
- "problem_statement": a clear, self-contained description of what the \
code is supposed to do (infer this from context/comments/function names \
if the user didn't state it explicitly).
- "code": the user's original code, exactly as given, if intent is \
"debug". Empty string if intent is "generate".
- "language": the programming language, detected from the code or from \
what the user said. If genuinely unclear, default to "Python".

Respond with ONLY a single JSON object, no markdown fences, no extra \
text, matching exactly this schema:

{
  "intent": "generate" | "debug",
  "problem_statement": "<string>",
  "code": "<string, empty if intent is generate>",
  "language": "<string>"
}
"""


def detect_intent(user_input: str, model: str = "gpt-4o-mini") -> dict:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    raw = response.choices[0].message.content
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(f"Model did not return valid JSON:\n{raw}")

    # Safety defaults in case the model omits a field.
    result.setdefault("intent", "generate")
    result.setdefault("problem_statement", user_input)
    result.setdefault("code", "")
    result.setdefault("language", "Python")
    return result
