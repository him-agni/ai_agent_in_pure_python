"""The Agents SDK party tricks: handoffs and guardrails.

A triage agent routes work to specialists, and an input guardrail
blocks destructive requests before the main agent ever sees them.
"""

import asyncio

from pydantic import BaseModel

from agent import MODEL, list_files, read_file, run_command, write_file

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    Runner,
    input_guardrail,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# GEMINI_API_KEY is loaded and checked when agent.py is imported above


# -------- guardrail: a tiny agent that screens every request first --------

class SafetyCheck(BaseModel):
    is_destructive: bool
    reasoning: str


guardrail_agent = Agent(
    name="Safety check",
    instructions=(
        "Decide if the request asks to delete files, wipe folders, "
        "or run destructive shell commands. Refactoring existing code is fine."
    ),
    output_type=SafetyCheck,
    model=MODEL,
)


@input_guardrail
async def block_destructive(ctx, agent, user_input) -> GuardrailFunctionOutput:
    check = await Runner.run(guardrail_agent, user_input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=check.final_output,
        tripwire_triggered=check.final_output.is_destructive,
    )


# -------- two specialists and a triage agent that hands off between them --------


coder = Agent(
    name="Coder",
    handoff_description="Writes, edits, and runs code.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n\n"
        "You are the Coder. The request has already been routed to you, so do the work "
        "yourself now. Do not announce a transfer or hand it to anyone else. "
        "Complete the coding task with your tools, then summarize what you did."
    ),
    model=MODEL,
    tools=[list_files, read_file, write_file, run_command],
)

explainer = Agent(
    name="Explainer",
    handoff_description="Explains the codebase without changing anything.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n\n"
        "You are the Explainer. The request has already been routed to you, so answer it "
        "yourself now. Do not announce a transfer or hand it to anyone else. "
        "Answer questions about the code. Read files as needed. Never write or run anything."
    ),
    model=MODEL,
    tools=[list_files, read_file],
)

triage = Agent(
    name="Triage",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n\n"
        "Route the user. Hand off build/edit/run requests to the Coder. "
        "Hand off questions about the code to the Explainer."
    ),
    model=MODEL,
    handoffs=[coder, explainer],
    input_guardrails=[block_destructive],
)


async def main():
    print("Triage agent ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break
        try:
            result = await Runner.run(triage, user_input)
            print(f"\n[{result.last_agent.name}]: {result.final_output}")
        except InputGuardrailTripwireTriggered:
            print("\n[guardrail]: Blocked. That request looked destructive.")


if __name__ == "__main__":
    asyncio.run(main())
