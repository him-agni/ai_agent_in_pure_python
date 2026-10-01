"""Level 1: CrewAI. You describe the agent like a job posting, the framework does the rest."""

import os
import subprocess

from crewai import Agent, Crew, Task
from crewai.tools import tool

from dotenv import load_dotenv

load_dotenv()  # reads GEMINI_API_KEY from the .env file in the project root
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set. Add it to the .env file in the project root.")

MODEL = "gemini/gemini-3.6-flash"


# -------- the same 4 tools as always, now wearing CrewAI decorators --------

@tool("List files")
def list_files(path: str = ".") -> str:
    """List the files in a directory. Folders end with /."""
    entries = [e.name + ("/" if e.is_dir() else "") for e in os.scandir(path)]
    return "\n".join(sorted(entries)) or "(empty directory)"


@tool("Read file")
def read_file(path: str) -> str:
    """Read a text file and return its contents."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@tool("Write file")
def write_file(path: str, content: str) -> str:
    """Create or overwrite a text file with the given content."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved {path} ({len(content)} characters)"


@tool("Run command")
def run_command(command: str) -> str:
    """Run a shell command and return its output. The user approves it first."""
    answer = input(f"  Run '{command}'? [y/N] ")
    if answer.strip().lower() != "y":
        return "The user declined to run this command."
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
    output = (result.stdout + result.stderr).strip()
    return output or f"(no output, exit code {result.returncode})"


# -------- the agent: no loop, no schemas, just a description --------

coder = Agent(
    role="Coding Assistant",
    goal="Complete the user's task using your tools, then summarize what you did.",
    backstory="A careful developer working inside the user's project folder.",
    tools=[list_files, read_file, write_file, run_command],
    llm=MODEL,
    verbose=True,
)


def main():
    request = input("What should the agent do? ")
    task = Task(
        description=request,
        expected_output="A short summary of what was done.",
        agent=coder,
    )
    crew = Crew(agents=[coder], tasks=[task])
    result = crew.kickoff()
    print(f"\n{result}")


if __name__ == "__main__":
    main()
