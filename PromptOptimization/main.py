"""
Customer Support Agent - Prompt Optimization Template

A customer support email classifier and responder that uses optimized prompts.
The system prompt is loaded from versioned prompt files managed by prompt_manager.py.
Run `python optimize.py` to optimize the prompt with DSPy.

LangGraph orchestration: classify email -> generate response
"""

import os
import re
from typing import TypedDict

from dotenv import load_dotenv
from gradient_adk import entrypoint
from langchain_gradient import ChatGradient
from langgraph.graph import END, START, StateGraph

import prompt_manager
from prompts import CATEGORY_DEFINITIONS, RESPONSE_GUIDELINES, build_prompt

load_dotenv()

VALID_CATEGORIES = {"billing", "technical", "account", "general"}
DEFAULT_MODEL = "openai-gpt-4.1"


# =============================================================================
# STATE
# =============================================================================

class SupportState(TypedDict):
    email_text: str
    category: str
    response: str
    prompt_version: str


# =============================================================================
# NODES
# =============================================================================

def classify_and_respond(state: SupportState) -> dict:
    """Classify the email and generate a response in a single LLM call."""
    # Load the active prompt version
    version = prompt_manager.get_active_version()
    if version is None:
        prompt_manager.create_baseline()
        version = prompt_manager.get_active_version()

    prompt = build_prompt(
        system_instruction=version["system_instruction"],
        category_definitions=CATEGORY_DEFINITIONS,
        response_guidelines=RESPONSE_GUIDELINES,
        few_shot_examples=version.get("few_shot_examples", ""),
    )

    llm = ChatGradient(model=DEFAULT_MODEL, temperature=0.2)
    chain = prompt | llm
    result = chain.invoke({"email_text": state["email_text"]})
    content = result.content

    # Parse category from the response
    category = "general"
    match = re.search(r"Category:\s*(\w+)", content, re.IGNORECASE)
    if match:
        parsed = match.group(1).lower()
        if parsed in VALID_CATEGORIES:
            category = parsed

    # Extract the response text (everything after the Category line)
    response_text = re.sub(
        r"^Category:\s*\w+\s*\n?", "", content, count=1, flags=re.IGNORECASE
    ).strip()

    return {
        "category": category,
        "response": response_text,
        "prompt_version": version["name"],
    }


# =============================================================================
# GRAPH
# =============================================================================

def build_graph():
    workflow = StateGraph(SupportState)
    workflow.add_node("classify_and_respond", classify_and_respond)
    workflow.add_edge(START, "classify_and_respond")
    workflow.add_edge("classify_and_respond", END)
    return workflow.compile()


agent = build_graph()


# =============================================================================
# ENTRYPOINT
# =============================================================================

@entrypoint
async def main(input: dict, context: dict) -> dict:
    """
    Customer support agent entrypoint.

    Args:
        input: {"prompt": "customer email text"}

    Returns:
        {"category": "billing|technical|account|general",
         "response": "agent response text",
         "prompt_version": "v1_baseline"}
    """
    email_text = input.get("prompt", "")
    if not email_text:
        return {"error": "Please provide a 'prompt' field with the customer email text."}

    result = await agent.ainvoke({"email_text": email_text, "category": "", "response": "", "prompt_version": ""})
    return {
        "category": result["category"],
        "response": result["response"],
        "prompt_version": result["prompt_version"],
    }
