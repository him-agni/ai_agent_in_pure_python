"""Level 3: LangGraph. The agent is a graph you draw yourself: nodes, edges, and state."""

import os
import subprocess

from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, ToolMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from dotenv import load_dotenv

load_dotenv()  # reads GEMINI_API_KEY from the .env file in the project root
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set. Add it to the .env file in the project root.")

MODEL = "google_genai:gemini-2.5-flash"

SYSTEM_PROMPT = (
    "You are a coding agent running in the user's terminal. "
    "Use your tools to complete the user's task, then briefly summarize what you did. "
    "The working directory is the folder the user launched you from."
)


# -------- the same 4 tools --------

@tool
def list_files(path: str = ".") -> str:
    """List the files in a directory. Folders end with /."""
    entries = [e.name + ("/" if e.is_dir() else "") for e in os.scandir(path or ".")]
    return "\n".join(sorted(entries)) or "(empty directory)"


@tool
def read_file(path: str) -> str:
    """Read a text file and return its contents."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@tool
def write_file(path: str, content: str) -> str:
    """Create or overwrite a text file with the given content."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved {path} ({len(content)} characters)"


@tool
def run_command(command: str) -> str:
    """Run a shell command and return its output. The user approves it first."""
    answer = input(f"  Run '{command}'? [y/N] ")
    if answer.strip().lower() != "y":
        return "The user declined to run this command."
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
    output = (result.stdout + result.stderr).strip()
    return output or f"(no output, exit code {result.returncode})"


TOOLS = {t.name: t for t in [list_files, read_file, write_file, run_command]}
model = init_chat_model(MODEL, api_key=GEMINI_API_KEY).bind_tools(list(TOOLS.values()))


# -------- the nodes: each one is a function that updates the state --------

def agent_node(state: MessagesState):
    reply = model.invoke([SystemMessage(SYSTEM_PROMPT)] + state["messages"])
    return {"messages": [reply]}


def tool_node(state: MessagesState):
    results = []
    for call in state["messages"][-1].tool_calls:
        try:
            output = TOOLS[call["name"]].invoke(call["args"])
        except Exception as e:
            # Hand the error back to the model so it can recover instead of crashing the graph.
            output = f"Error: {type(e).__name__}: {e}"
        results.append(ToolMessage(content=str(output), tool_call_id=call["id"]))
    return {"messages": results}


def should_continue(state: MessagesState):
    # Tool calls pending? Go run them. Otherwise the agent is done.
    return "tools" if state["messages"][-1].tool_calls else END


# -------- the graph: you draw the agent loop as edges --------

def build_graph(checkpointer=None):
    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tool_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, ["tools", END])
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)


def main():
    # The checkpointer saves the state after every node. Memory is free.
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "chat"}}

    print("Mini agent ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break
        state = graph.invoke({"messages": [{"role": "user", "content": user_input}]}, config)
        print(f"\nAgent: {state['messages'][-1].content}")


if __name__ == "__main__":
    main()
