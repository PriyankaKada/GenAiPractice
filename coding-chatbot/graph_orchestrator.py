"""
graph_orchestrator.py

The orchestrator, rebuilt as a LangGraph StateGraph.

Graph shape:

    detect_intent
         |
         +--(debug, has code)----------------+
         |                                    |
    generate_code                             |
         |                                    |
         +------------------------------------+
                         |
                    generate_tests
                         |
                      run_tests  <---------------+
                         |                        |
              (passed / unsupported / maxed out)  |
                         |               (failed, attempts left)
                        END                       |
                                              fix_code
                                                   |
                                              run_tests (loop)

MAX_ATTEMPTS bounds the run_tests <-> fix_code loop at 3 total attempts.
"""

from pathlib import Path
from typing import Optional, TypedDict, List

from langgraph.graph import StateGraph, END

import agents
import execution

MAX_ATTEMPTS = 3
WORK_DIR = Path("./agent_run")


# --- Graph state -----------------------------------------------------

class AttemptRecord(TypedDict):
    attempt: int
    passed: Optional[bool]
    output: str
    code: str


class GraphState(TypedDict):
    user_input: str
    model: str

    intent: str
    problem_statement: str
    language: str
    code: str

    test_code: str
    test_explanation: str

    attempt: int
    passed: Optional[bool]
    output: str
    attempts_log: List[AttemptRecord]


# --- Nodes -----------------------------------------------------

def node_detect_intent(state: GraphState) -> dict:
    result = agents.detect_intent(state["user_input"], state["model"])
    update = {
        "intent": result.intent,
        "problem_statement": result.problem_statement,
        "language": result.language,
    }
    if result.intent == "debug" and result.code.strip():
        update["code"] = result.code
    else:
        update["intent"] = "generate"  # normalize: no usable code was given
    return update


def route_after_intent(state: GraphState) -> str:
    return "generate_tests" if state["intent"] == "debug" else "generate_code"


def node_generate_code(state: GraphState) -> dict:
    result = agents.generate_code(state["problem_statement"], state["model"])
    return {"language": result.language, "code": result.code}


def node_generate_tests(state: GraphState) -> dict:
    result = agents.generate_tests(
        state["problem_statement"], state["language"], state["code"], state["model"]
    )
    return {"test_code": result.test_code, "test_explanation": result.explanation}


def node_run_tests(state: GraphState) -> dict:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    ext = execution.LANGUAGE_EXT.get(state["language"].strip().lower(), "txt")
    code_path = WORK_DIR / f"solution.{ext}"
    test_path = WORK_DIR / f"test_solution.{ext}"

    code_path.write_text(state["code"], encoding="utf-8")
    test_path.write_text(state["test_code"], encoding="utf-8")

    passed, output = execution.run_tests(state["language"], code_path, test_path)

    attempt = state.get("attempt", 0) + 1
    log_entry: AttemptRecord = {
        "attempt": attempt, "passed": passed, "output": output, "code": state["code"],
    }
    attempts_log = state.get("attempts_log", []) + [log_entry]

    return {"attempt": attempt, "passed": passed, "output": output, "attempts_log": attempts_log}


def route_after_tests(state: GraphState) -> str:
    if state["passed"] is True:
        return "end"
    if state["passed"] is None:  # execution unsupported for this language
        return "end"
    if state["attempt"] >= MAX_ATTEMPTS:
        return "end"
    return "fix_code"


def node_fix_code(state: GraphState) -> dict:
    result = agents.generate_code(
        state["problem_statement"], state["model"],
        feedback=state["output"], test_code=state["test_code"],
    )
    return {"code": result.code}


# --- Build the graph -----------------------------------------------------

def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("detect_intent", node_detect_intent)
    graph.add_node("generate_code", node_generate_code)
    graph.add_node("generate_tests", node_generate_tests)
    graph.add_node("run_tests", node_run_tests)
    graph.add_node("fix_code", node_fix_code)

    graph.set_entry_point("detect_intent")

    graph.add_conditional_edges(
        "detect_intent", route_after_intent,
        {"generate_code": "generate_code", "generate_tests": "generate_tests"},
    )
    graph.add_edge("generate_code", "generate_tests")
    graph.add_edge("generate_tests", "run_tests")

    graph.add_conditional_edges(
        "run_tests", route_after_tests,
        {"end": END, "fix_code": "fix_code"},
    )
    graph.add_edge("fix_code", "run_tests")

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def print_graph():
    """Print the graph structure as ASCII (terminal) or return Mermaid source."""
    graph = get_graph()
    print(graph.get_graph().draw_ascii())


def get_mermaid():
    """Return Mermaid diagram source - paste into https://mermaid.live to view,
    or save to a .mermaid/.md file."""
    graph = get_graph()
    return graph.get_graph().draw_mermaid()


def orchestrate(user_input: str, model: str = "gpt-4o-mini") -> dict:
    graph = get_graph()
    final_state = graph.invoke({
        "user_input": user_input,
        "model": model,
        "attempt": 0,
        "attempts_log": [],
    })

    return {
        "intent": final_state["intent"],
        "success": bool(final_state["passed"]),
        "attempts_used": len(final_state["attempts_log"]),
        "language": final_state["language"],
        "final_code": final_state["attempts_log"][-1]["code"],
        "test_code": final_state["test_code"],
        "test_explanation": final_state.get("test_explanation", ""),
        "attempts": final_state["attempts_log"],
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--graph":
        print_graph()
        sys.exit(0)

    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Describe the coding problem (or paste code to debug): ").strip()

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
