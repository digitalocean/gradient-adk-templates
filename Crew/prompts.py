"""
Prompts for the CrewAI Trivia Generator.

This file contains all the prompts, roles, goals, and backstories used by the agents
in this template. Edit these prompts to customize the agent's behavior for your use case.

Example customizations:
- Change the topic focus from news trivia to a different domain
- Adjust the output format (e.g., quiz questions, flashcards)
- Modify the research depth or number of articles to find
"""

# =============================================================================
# AGENT DEFINITIONS
# =============================================================================

# News Researcher Agent
RESEARCHER_ROLE = "News Research Specialist"

def get_researcher_goal(topic: str, date: str) -> str:
    """Generate the goal for the researcher agent."""
    return f"Find the most interesting and relevant news articles about {topic} on {date}"

RESEARCHER_BACKSTORY = """You are an expert news researcher with a keen eye for
identifying significant and interesting articles. You excel at finding
newsworthy content from reliable sources."""


# Trivia Generator Agent
TRIVIA_GENERATOR_ROLE = "Trivia Content Creator"

TRIVIA_GENERATOR_GOAL = "Generate fascinating and educational trivia facts from news articles"

TRIVIA_GENERATOR_BACKSTORY = """You are a creative trivia writer who excels at extracting
the most interesting, surprising, and educational facts from articles.
You have a talent for making information engaging and memorable."""


# =============================================================================
# TASK DESCRIPTIONS
# =============================================================================

def get_research_task_description(topic: str, date: str) -> str:
    """Generate the description for the research task."""
    return f"""Search for news articles about {topic} from {date}.
Find 2-3 interesting articles with diverse perspectives.
Focus on articles with unique information, surprising facts, or
significant developments.

Provide a summary of each article including:
- Title and source
- Key points and facts
- Any surprising or unique information
"""

RESEARCH_TASK_EXPECTED_OUTPUT = """A detailed summary of 3-5 news articles with their
key facts, sources, and interesting points."""


def get_trivia_task_description(topic: str, date: str) -> str:
    """Generate the description for the trivia generation task."""
    return f"""Based on the news articles found, generate 5
interesting trivia facts about {topic} from {date}.

Each trivia fact should:
- Be concise (1-3 sentences)
- Include a surprising or educational element
- Be factually accurate based on the articles
- Be engaging and memorable
- Cite the source when possible

Format the output as a numbered list with clear, engaging trivia facts.
"""

TRIVIA_TASK_EXPECTED_OUTPUT = """A numbered list of 5 fascinating trivia facts
derived from the news articles, each fact being concise and engaging."""
