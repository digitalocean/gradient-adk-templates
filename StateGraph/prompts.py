"""
Prompts for the StateGraph Joke Generator.

This file contains all the prompts used in the joke generation pipeline.
Edit these prompts to customize the agent's behavior for your use case.

Example customizations:
- Change from jokes to other creative content (poems, stories, riddles)
- Adjust the tone or style (formal, casual, edgy)
- Add constraints or themes
- Change the improvement/polish criteria
"""

# =============================================================================
# JOKE GENERATION PROMPTS
# =============================================================================

def get_generate_joke_prompt(topic: str) -> str:
    """Generate the initial joke prompt."""
    return f"Write a short joke about {topic} in two sentences or less"


def get_improve_joke_prompt(joke: str) -> str:
    """Generate the prompt to improve a joke."""
    return f"Make the joke funnier and quirky: {joke}"


def get_polish_joke_prompt(improved_joke: str) -> str:
    """Generate the prompt to polish the final joke."""
    return f"Remove any explanation of the joke or punchline: {improved_joke}"


# Instruction added when spicy mode is enabled
SPICY_INSTRUCTION = "Make the joke extra sassy."


# =============================================================================
# ALTERNATIVE PROMPTS (uncomment and modify for different use cases)
# =============================================================================

# Riddle Generator
# def get_generate_joke_prompt(topic: str) -> str:
#     return f"Create a clever riddle about {topic}. Include the answer."
#
# def get_improve_joke_prompt(joke: str) -> str:
#     return f"Make this riddle more challenging but still solvable: {joke}"
#
# def get_polish_joke_prompt(improved_joke: str) -> str:
#     return f"Format the riddle clearly with the question first, then 'Answer:' on a new line: {improved_joke}"

# Dad Jokes
# def get_generate_joke_prompt(topic: str) -> str:
#     return f"Write a classic dad joke about {topic}. It should be punny and groan-worthy."
#
# def get_improve_joke_prompt(joke: str) -> str:
#     return f"Make this dad joke even more punny: {joke}"
#
# def get_polish_joke_prompt(improved_joke: str) -> str:
#     return f"Ensure the punchline lands well and remove any explanations: {improved_joke}"

# One-liner Comedy
# def get_generate_joke_prompt(topic: str) -> str:
#     return f"Write a clever one-liner joke about {topic} in the style of a stand-up comedian."
#
# def get_improve_joke_prompt(joke: str) -> str:
#     return f"Make this one-liner punchier and more unexpected: {joke}"
#
# def get_polish_joke_prompt(improved_joke: str) -> str:
#     return f"Tighten the wording to maximize impact: {improved_joke}"
