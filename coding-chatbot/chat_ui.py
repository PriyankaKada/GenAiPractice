#!/usr/bin/env python3
"""
chat_ui.py

Gradio UI for the Agentic Coding Assistant.

Run:
    python chat_ui.py

Then open:
    http://127.0.0.1:7860
"""

import gradio as gr

from graph_orchestrator import orchestrate


def chat(message, history):
    """
    Handles a single chat message.
    """

    result = orchestrate(message)

    # Handle blocked / non-coding requests
    if result.get("response"):
        return result["response"]

    language = result.get("language", "").lower()

    attempts = result.get("attempts", [])

    attempts_summary = ""
    for attempt in attempts:
        status = "✅ Passed" if attempt["passed"] else "❌ Failed"
        attempts_summary += (
            f"- Attempt {attempt['attempt']}: {status}\n"
        )

        response = f"""
            # 🤖 Agentic Coding Assistant

            ### Intent
            **{result['intent']}** 


            ### Language
            **{result['language']}**

            ### Attempts Used
            **{result['attempts_used']}**

            ---

            ## Test Execution Summary

            {attempts_summary if attempts_summary else "No test execution."}

            ---

            ## Generated Code

            ```{language}
                {result['final_code']}
            ```

            ---

            ## Generated Test Suite

            ```{language}
                {result['test_code']}
            ```

            ---

            ## Test Explanation

            {result.get("test_explanation", "")}
            """

        return response

demo = gr.ChatInterface(
    fn=chat,
    title="🚀 Agentic Coding Assistant",
    description="Generate code, debug code, generate tests and validate them.",
    type="messages",
)

if __name__ == "__main__":
    demo.launch()