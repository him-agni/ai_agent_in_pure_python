import os
import subprocess

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are a coding agent running in the user's terminal.
You can list files, read files, write files, and run shell commands.
Use your tools to complete the user's task, then briefly summarize what you did.
The working directory is the folder the user launched you from."""


def list_files(path="."):
    entries = []
    for entry in os.scandir(path):
        entries.append(entry.name + ("/" if entry.is_dir() else ""))
    return "\n".join(sorted(entries)) or "(empty directory)"


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved {path} ({len(content)} characters)"


def run_command(command):
    answer = input(f"  Run '{command}'? [y/N] ")
    if answer.strip().lower() != "y":
        return "The user declined to run this command."
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=120
    )
    output = (result.stdout + result.stderr).strip()
    return output or f"(no output, exit code {result.returncode})"


TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
}

TOOL_SCHEMAS = [
    types.Tool(function_declarations=[
        {
            "name": "list_files",
            "description": "List the files in a directory. Folders end with /.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to list, e.g. '.'"},
                },
                "required": ["path"],
            },
        },
        {
            "name": "read_file",
            "description": "Read a text file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path of the file to read"},
                },
                "required": ["path"],
            },
        },
        {
            "name": "write_file",
            "description": "Create or overwrite a text file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path of the file to write"},
                    "content": {"type": "string", "description": "Full contents of the file"},
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "run_command",
            "description": "Run a shell command and return its output. The user approves it first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run"},
                },
                "required": ["command"],
            },
        },
    ]),
]


def run_tool(tool_call):
    name = tool_call.name
    args = tool_call.args
    print(f"  tool: {name}({args})")
    try:
        return str(TOOLS[name](**args))
    except Exception as error:
        return f"Error: {error}"



def run_agent(messages):
    while True:
        response = client.models.generate_content(
            model=MODEL,
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=TOOL_SCHEMAS,
            ),
        )
        messages.append(response.candidates[0].content)

        # No tool calls means the model is done and answered in plain text
        if not response.function_calls:
            return response.text

        tool_results = []
        for tool_call in response.function_calls:
            result = run_tool(tool_call)
            tool_results.append(types.Part.from_function_response(name=tool_call.name, response={"result": result}))
        messages.append(types.Content(role="user", parts=tool_results))
       
            
def main():
    messages = []
    print("Mini agent ready. Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break
        messages.append(types.Content(role="user", parts=[types.Part(text=user_input)]))
        reply = run_agent(messages)
        print(f"\nAgent: {reply}")


if __name__ == "__main__":
    main()
