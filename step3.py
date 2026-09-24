import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))



def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File {path} not found"


TOOL_SCHEMAS = [
    types.Tool(function_declarations=[
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
    ]),
]

messages = [
    types.Content(role="user", parts=[types.Part(text="What is inside notes.txt, notes1.txt and notes2.txt? Summarize it in one line.")]),
]

while True:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=messages,
        config=types.GenerateContentConfig(tools=TOOL_SCHEMAS),
    )
    messages.append(response.candidates[0].content)

    # No tool calls means the model is done and gave us a normal answer
    if not response.function_calls:
        print(response.text)
        break

    tool_results = []
    for tool_call in response.function_calls:
        args = tool_call.args
        print(f"Model wants to run: read_file({args})")

        result = read_file(**args)

        tool_results.append(types.Part.from_function_response(name=tool_call.name, response={"result": result}))
    messages.append(types.Content(role="user", parts=tool_results))
    
    print(messages)
