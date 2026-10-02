"""Level 2: OpenAI Agents SDK (running on Gemini). Your functions, their loop. Sessions give you memory for free."""

import os
import subprocess

from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    SQLiteSession,
    function_tool,
    set_tracing_disabled,
)
from openai import AsyncOpenAI

from dotenv import load_dotenv

load_dotenv()  # reads GEMINI_API_KEY from the .env file in the project root
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set. Add it to the .env file in the project root.")

# Gemini speaks the OpenAI Chat Completions format, so point the OpenAI client at Google
gemini_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
set_tracing_disabled(True)  # tracing uploads to OpenAI and would need an OpenAI key

MODEL = OpenAIChatCompletionsModel(model="gemini-2.5-flash", openai_client=gemini_client)


# -------- tools are plain Python functions, the SDK reads the docstrings --------

@function_tool
def list_files(path: str = ".") -> str:
    """List the files in a directory. Folders end with /."""
    entries = [e.name + ("/" if e.is_dir() else "") for e in os.scandir(path)]
    return "\n".join(sorted(entries)) or "(empty directory)"


@function_tool
def read_file(path: str) -> str:
    """Read a text file and return its contents."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@function_tool
def write_file(path: str, content: str) -> str:
    """Create or overwrite a text file with the given content."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved {path} ({len(content)} characters)"


@function_tool
def run_command(command: str) -> str:
    """Run a shell command and return its output. The user approves it first."""
    answer = input(f"  Run '{command}'? [y/N] ")
    if answer.strip().lower() != "y":
        return "The user declined to run this command."
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
    output = (result.stdout + result.stderr).strip()
    return output or f"(no output, exit code {result.returncode})"


# -------- the agent: system prompt + tools, the SDK runs the loop --------

agent = Agent(
    name="Mini coding agent",
    instructions=(
        "You are a coding agent running in the user's terminal. "
        "Use your tools to complete the user's task, then briefly summarize what you did. "
        "The working directory is the folder the user launched you from."
    ),
    model=MODEL,
    tools=[list_files, read_file, write_file, run_command],
)


def main():
    session = SQLiteSession("mini-agent")
    print("Mini agent ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break
        result = Runner.run_sync(agent, user_input, session=session)
        print(f"\nAgent: {result.final_output}")


if __name__ == "__main__":
    main()
