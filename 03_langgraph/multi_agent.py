"""The LangGraph party trick: a multi-agent graph you can actually see.

A triage node reads the request and picks a route. Each specialist is the
agent loop from agent.py, compiled and dropped in as a single node.
The reviewer can send work back to the coder, so the graph has a real cycle.

    START -> triage -> explainer -> END
                    -> coder -> reviewer -> END
                          ^          |
                          +----------+   (changes requested)
"""

import os
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()  # reads GEMINI_API_KEY from the .env file in the project root
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set. Add it to the .env file in the project root.")

import agent as base

MAX_REVISIONS = 2


# -------- shared state: the messages list plus the routing fields --------

class State(MessagesState):
    route: str        # set by triage: "coder" or "explainer"
    approved: bool    # set by the reviewer
    revisions: int    # how many times the reviewer sent work back


# -------- a specialist = the agent loop from agent.py with its own prompt and tools --------

def make_specialist(name: str, system_prompt: str, tools: list):
    model = init_chat_model(base.MODEL, api_key=GEMINI_API_KEY).bind_tools(tools)

    def agent_node(state: MessagesState):
        reply = model.invoke([SystemMessage(system_prompt)] + state["messages"])
        for call in reply.tool_calls:
            first_arg = str(next(iter(call["args"].values()), "")).splitlines()[0][:60]
            print(f"  [{name}] {call['name']}({first_arg})")
        return {"messages": [reply]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", base.tool_node)  # same tool executor as agent.py
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", base.should_continue, ["tools", END])
    builder.add_edge("tools", "agent")
    return builder.compile()  # a compiled graph can be used as a node in another graph


coder = make_specialist(
    "coder",
    base.SYSTEM_PROMPT + " If you receive reviewer feedback, fix exactly what it asks for.",
    [base.list_files, base.read_file, base.write_file, base.run_command],
)

explainer = make_specialist(
    "explainer",
    "You explain the codebase. Read files as needed and answer the question. Never write or run anything.",
    [base.list_files, base.read_file],
)


# -------- triage: a structured-output call that decides the route --------

class Route(BaseModel):
    agent: Literal["coder", "explainer"]
    reason: str


triage_model = init_chat_model(base.MODEL, api_key=GEMINI_API_KEY).with_structured_output(Route, method="function_calling")


def triage_node(state: State):
    decision = triage_model.invoke([
        SystemMessage(
            "Route the user's latest request. coder: anything that builds, edits, or runs code. "
            "explainer: questions about the code that change nothing."
        ),
        *state["messages"],
    ])
    print(f"  [triage] -> {decision.agent} ({decision.reason})")
    return {"route": decision.agent, "approved": False, "revisions": 0}


def pick_specialist(state: State):
    return state["route"]


# -------- reviewer: checks the coder's work and can loop it back --------

class Review(BaseModel):
    approved: bool
    feedback: str


reviewer_model = init_chat_model(base.MODEL, api_key=GEMINI_API_KEY).with_structured_output(Review, method="function_calling")


def reviewer_node(state: State):
    review = reviewer_model.invoke([
        SystemMessage(
            "You are the code reviewer. Look at what the coder just did in this conversation: "
            "the files it wrote and the commands it ran. Approve if the work meets the user's "
            "request and has no obvious bugs. Otherwise reject with short, specific feedback."
        ),
        *state["messages"],
    ])
    if review.approved or state["revisions"] >= MAX_REVISIONS:
        print("  [reviewer] approved" if review.approved else "  [reviewer] out of revisions, shipping as is")
        return {"approved": True}
    print(f"  [reviewer] changes requested: {review.feedback}")
    return {
        "approved": False,
        "revisions": state["revisions"] + 1,
        "messages": [HumanMessage(f"Reviewer feedback: {review.feedback}")],
    }


def after_review(state: State):
    return END if state["approved"] else "coder"


# -------- the graph: triage fans out, the reviewer loops back --------

def build_graph(checkpointer=None):
    builder = StateGraph(State)
    builder.add_node("triage", triage_node)
    builder.add_node("coder", coder)
    builder.add_node("explainer", explainer)
    builder.add_node("reviewer", reviewer_node)
    builder.add_edge(START, "triage")
    builder.add_conditional_edges("triage", pick_specialist, ["coder", "explainer"])
    builder.add_edge("explainer", END)
    builder.add_edge("coder", "reviewer")
    builder.add_conditional_edges("reviewer", after_review, ["coder", END])
    return builder.compile(checkpointer=checkpointer)


def main():
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "chat"}}

    print("Multi-agent graph ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break
        state = graph.invoke({"messages": [{"role": "user", "content": user_input}]}, config)
        print(f"\n[{state['route']}]: {state['messages'][-1].text}")


if __name__ == "__main__":
    main()
