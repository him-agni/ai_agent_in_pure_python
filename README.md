# AI Agent in Pure Python

A learning project where I build an AI agent step by step, using the free Gemini API and plain Python (no agent frameworks).

**Core idea:** an AI agent is just an LLM + tools + a loop.

---

## Step 1: A single API call (`step1.py`)

- Send one prompt to Gemini and print the response.
- The **system instruction** tells the model how to behave (e.g. "answer in short sentences").
- Messages have roles: `user` (me) and `model` (the AI).
- The last message must be from the `user`, otherwise the model has nothing to reply to.

**Learned:** how to talk to an LLM with code.

## Step 2: Chat with memory (`step2.py`)

- Added a `while` loop so I can keep chatting (type `exit` or `quit` to stop).
- Every message (mine and the model's) is saved in a `messages` list. This list is the **context window**.
- The whole list is sent to the model every time, so it remembers earlier messages.
- The LLM itself has no memory. The "memory" is just us resending the history.

**Learned:** how chat works, and why context matters.

## Step 3: Tool calling (`step3.py`)

- Gave the model a **tool**: a Python function `read_file(path)` that reads a file.
- We describe the tool to the model (name, what it does, what inputs it needs) in `TOOL_SCHEMAS`.
- The model can't run code itself. It only **asks** us to run the tool.

How the loop works:
1. Send the messages + tool description to the model.
2. If the model asks for a tool call → we run `read_file`, add the result to `messages`, and loop again.
3. If the model doesn't ask for a tool → it has the final answer, so print it and stop.

**Learned:** this loop (model → tool → result → model) is what makes it an **agent**.

## Step 4: Mini Claude Code (`agent.py`)

- Gave the agent 4 tools, the same basic kit a coding assistant like Claude Code uses:
  - `list_files` — see what's in a folder
  - `read_file` — read a file
  - `write_file` — create or overwrite a file
  - `run_command` — run a shell command (it asks me `y/N` first, so it can't run anything without my approval)
- Same loop as Step 3, but now the model can call several tools in a row until the task is done.

### Demo: a snake game from one sentence

I typed this in plain English:

```
You: in already existing snake_game directory make a simple snake game in Python using Pygame that I can play
```

The agent decided on its own what to do:
1. `list_files('snake_game')` → checked what was already in the folder.
2. `write_file('snake_game/main.py', ...)` → wrote the whole game.

I didn't write any game code. Running `snake_game/main.py` (needs `pygame` installed) opened a working game:

![The agent's tool calls in the terminal, and the snake game it built running](images/snake_game_demo.png)

**Learned:** with just 4 tools and a loop, an LLM can turn a plain-English request into working code — a mini Claude Code in pure Python.

---

## How to run

1. Get a free API key from [Google AI Studio](https://aistudio.google.com/).
2. Create a `.env` file with: `GEMINI_API_KEY=your_key_here`
3. Install and run:
   ```
   uv sync
   uv run step1.py
   ```
