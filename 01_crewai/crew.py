import os

from agent import coder, list_files, read_file

from crewai import Agent, Crew, Task

from dotenv import load_dotenv

load_dotenv()  # reads GEMINI_API_KEY from the .env file in the project root
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set. Add it to the .env file in the project root.")

MODEL = "gemini/gemini-3.6-flash"

planner = Agent(
    role="Tech Lead",
    goal="Break the user's request into a short, concrete build plan.",
    backstory="A pragmatic tech lead who writes plans a junior dev can follow.",
    tools=[list_files, read_file],
    llm=MODEL,
    verbose=True,
)


def main():
    request = input("What should the crew build? ")

    plan_task = Task(
        description=f"Look at the files in this folder, then write a step by step plan for: {request}",
        expected_output="A numbered build plan, 5 steps or fewer.",
        agent=planner,
    )
    build_task = Task(
        description="Follow the plan exactly and build it.",
        expected_output="A short summary of what was built and which files changed.",
        agent=coder,
        context=[plan_task],  # the coder receives the planner's output
    )

    crew = Crew(agents=[planner, coder], tasks=[plan_task, build_task])
    result = crew.kickoff()
    print(f"\n{result}")


if __name__ == "__main__":
    main()
