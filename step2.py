import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

messages = []

while True:
    user_input = input("You: ")
    if user_input.strip().lower() in ("exit", "quit"):
        break

    messages.append(types.Content(role="user", parts=[types.Part(text=user_input)]))

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=messages,
    )

    reply = response.text
    messages.append(types.Content(role="model", parts=[types.Part(text=reply)]))
    print("Bot:", reply)
