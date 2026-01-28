"""
CrewAI Trivia Generator
Searches for news articles on a specific date and topic, then generates interesting trivia.
"""

import os
from crewai import LLM, Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
from gradient_adk import entrypoint
from typing import Dict

# Import prompts - edit prompts.py to customize agent behavior
from prompts import (
    RESEARCHER_ROLE,
    RESEARCHER_BACKSTORY,
    get_researcher_goal,
    TRIVIA_GENERATOR_ROLE,
    TRIVIA_GENERATOR_GOAL,
    TRIVIA_GENERATOR_BACKSTORY,
    get_research_task_description,
    RESEARCH_TASK_EXPECTED_OUTPUT,
    get_trivia_task_description,
    TRIVIA_TASK_EXPECTED_OUTPUT,
)

# Load environment variables
load_dotenv()

# Initialize the search tool
search_tool = SerperDevTool()


def create_trivia_crew(date: str, topic: str):
    """
    Creates a crew with two agents:
    - Research Agent: Finds news articles
    - Trivia Agent: Generates interesting facts
    """

    # Create the base LLM that will be used by the agents
    llm = LLM(
        model="openai-gpt-4.1",
        base_url="https://inference.do-ai.run/v1",
        api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY"),
        temperature=0.5
    )

    # Agent 1: News Researcher
    researcher = Agent(
        role=RESEARCHER_ROLE,
        goal=get_researcher_goal(topic, date),
        backstory=RESEARCHER_BACKSTORY,
        tools=[search_tool],
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    # Agent 2: Trivia Generator
    trivia_generator = Agent(
        role=TRIVIA_GENERATOR_ROLE,
        goal=TRIVIA_GENERATOR_GOAL,
        backstory=TRIVIA_GENERATOR_BACKSTORY,
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    # Task 1: Research news articles
    research_task = Task(
        description=get_research_task_description(topic, date),
        agent=researcher,
        expected_output=RESEARCH_TASK_EXPECTED_OUTPUT,
    )

    # Task 2: Generate trivia
    trivia_task = Task(
        description=get_trivia_task_description(topic, date),
        agent=trivia_generator,
        expected_output=TRIVIA_TASK_EXPECTED_OUTPUT,
        context=[research_task],  # This task depends on the research task
    )

    # Create the crew
    crew = Crew(
        agents=[researcher, trivia_generator],
        tasks=[research_task, trivia_task],
        process=Process.sequential,  # Tasks execute in order
        verbose=True,
    )

    return crew


@entrypoint
async def main(input: Dict, context: Dict):
    date = input.get("date")
    topic = input.get("topic")

    crew = create_trivia_crew(date, topic)
    result = crew.kickoff()

    return {"result": result}
