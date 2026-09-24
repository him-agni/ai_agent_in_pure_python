import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are a helpful AI assistant, answer precisely in short sentences."
    ),
    contents=[
        types.Content(role="model", parts=[types.Part(text="An AI agent is simply an LLM connected to tools in a loop.")]),
        types.Content(role="user", parts=[types.Part(text="Explain what an AI agent is in one sentence.")]),
    ],
)

print(response.text)
