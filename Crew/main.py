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
        role="News Research Specialist",
        goal=f"Find the most interesting and relevant news articles about {topic} on {date}",
        backstory="""You are an expert news researcher with a keen eye for 
        identifying significant and interesting articles. You excel at finding 
        newsworthy content from reliable sources.""",
        tools=[search_tool],
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    # Agent 2: Trivia Generator
    trivia_generator = Agent(
        role="Trivia Content Creator",
        goal="Generate fascinating and educational trivia facts from news articles",
        backstory="""You are a creative trivia writer who excels at extracting 
        the most interesting, surprising, and educational facts from articles. 
        You have a talent for making information engaging and memorable.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    # Task 1: Research news articles
    research_task = Task(
        description=f"""Search for news articles about {topic} from {date}.
        Find 2-3 interesting articles with diverse perspectives.
        Focus on articles with unique information, surprising facts, or 
        significant developments.
        
        Provide a summary of each article including:
        - Title and source
        - Key points and facts
        - Any surprising or unique information
        """,
        agent=researcher,
        expected_output="""A detailed summary of 3-5 news articles with their 
        key facts, sources, and interesting points.""",
    )

    # Task 2: Generate trivia
    trivia_task = Task(
        description=f"""Based on the news articles found, generate 5 
        interesting trivia facts about {topic} from {date}.
        
        Each trivia fact should:
        - Be concise (1-3 sentences)
        - Include a surprising or educational element
        - Be factually accurate based on the articles
        - Be engaging and memorable
        - Cite the source when possible
        
        Format the output as a numbered list with clear, engaging trivia facts.
        """,
        agent=trivia_generator,
        expected_output="""A numbered list of 5 fascinating trivia facts 
        derived from the news articles, each fact being concise and engaging.""",
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
