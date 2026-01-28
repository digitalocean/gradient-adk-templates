import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient

# Import prompts from central prompts.py - edit that file to customize
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import PLAN_GENERATOR_PROMPT, PLAN_REFINEMENT_PROMPT

logger = logging.getLogger(__name__)


class ResearchGoal(BaseModel):
    """A single research goal."""
    objective: str = Field(description="Clear objective describing what to find or create")
    goal_type: str = Field(description="Either 'RESEARCH' or 'DELIVERABLE'")
    key_questions: List[str] = Field(description="Key questions to answer for this goal")


class ResearchPlan(BaseModel):
    """A complete research plan."""
    topic: str = Field(description="The research topic")
    goals: List[ResearchGoal] = Field(description="List of research goals")
    summary: str = Field(description="Brief summary of the research approach")


def get_planner_model():
    return ChatGradient(
        model="openai-gpt-4.1",
        temperature=0.3
    )


def format_plan_for_display(plan: ResearchPlan) -> str:
    """Format a research plan for human-readable display."""
    output = f"## Research Plan: {plan.topic}\n\n"
    output += f"**Summary:** {plan.summary}\n\n"
    output += "### Goals:\n\n"

    for i, goal in enumerate(plan.goals, 1):
        output += f"**{i}. [{goal.goal_type}] {goal.objective}**\n"
        output += "   Key questions:\n"
        for q in goal.key_questions:
            output += f"   - {q}\n"
        output += "\n"

    return output


def generate_initial_plan(state: dict) -> dict:
    """
    Generate an initial research plan for the given topic.

    Args:
        state: Current state containing the topic

    Returns:
        Updated state with the research plan
    """
    topic = state.get("topic", "")
    logger.info(f"Generating initial research plan for topic: {topic}")

    if not topic:
        logger.error("No topic provided for research plan generation")
        return {
            "research_plan": None,
            "plan_display": "Error: No research topic provided.",
            "plan_approved": False,
            "plan_iteration": 1
        }

    try:
        planner_model = get_planner_model()
        structured_model = planner_model.with_structured_output(ResearchPlan)

        prompt = PLAN_GENERATOR_PROMPT.format(topic=topic)
        logger.info(f"Invoking LLM for plan generation...")
        plan = structured_model.invoke([{"role": "user", "content": prompt}])

        if not plan or not plan.goals:
            logger.warning("LLM returned empty or invalid plan")
            return {
                "research_plan": None,
                "plan_display": "Error: Failed to generate a valid research plan. Please try again.",
                "plan_approved": False,
                "plan_iteration": 1
            }

        plan_display = format_plan_for_display(plan)
        logger.info(f"Generated plan with {len(plan.goals)} goals")

        return {
            "research_plan": plan,
            "plan_display": plan_display,
            "plan_approved": False,
            "plan_iteration": 1
        }

    except Exception as e:
        logger.error(f"Error generating research plan: {str(e)}")
        return {
            "research_plan": None,
            "plan_display": f"Error generating research plan: {str(e)}",
            "plan_approved": False,
            "plan_iteration": 1
        }


def refine_plan(state: dict) -> dict:
    """
    Refine the research plan based on user feedback.

    Args:
        state: Current state containing the plan and user feedback

    Returns:
        Updated state with refined plan
    """
    current_plan = state.get("research_plan")
    feedback = state.get("user_feedback", "")
    iteration = state.get("plan_iteration", 1)

    logger.info(f"Refining plan (iteration {iteration + 1}) based on feedback: {feedback[:100]}...")

    if not current_plan:
        logger.error("No current plan to refine")
        return {
            "research_plan": None,
            "plan_display": "Error: No existing plan to refine.",
            "plan_iteration": iteration + 1,
            "user_feedback": ""
        }

    try:
        planner_model = get_planner_model()
        structured_model = planner_model.with_structured_output(ResearchPlan)

        current_plan_text = format_plan_for_display(current_plan)
        prompt = PLAN_REFINEMENT_PROMPT.format(
            current_plan=current_plan_text,
            feedback=feedback
        )

        logger.info(f"Invoking LLM for plan refinement...")
        refined_plan = structured_model.invoke([{"role": "user", "content": prompt}])

        if not refined_plan or not refined_plan.goals:
            logger.warning("LLM returned empty or invalid refined plan")
            return {
                "research_plan": current_plan,  # Keep the original plan
                "plan_display": format_plan_for_display(current_plan) + "\n\n*Note: Failed to apply refinement. Original plan preserved.*",
                "plan_iteration": iteration + 1,
                "user_feedback": ""
            }

        plan_display = format_plan_for_display(refined_plan)
        logger.info(f"Refined plan now has {len(refined_plan.goals)} goals")

        return {
            "research_plan": refined_plan,
            "plan_display": plan_display,
            "plan_iteration": iteration + 1,
            "user_feedback": ""  # Clear feedback after processing
        }

    except Exception as e:
        logger.error(f"Error refining plan: {str(e)}")
        return {
            "research_plan": current_plan,  # Keep the original plan
            "plan_display": format_plan_for_display(current_plan) if current_plan else f"Error refining plan: {str(e)}",
            "plan_iteration": iteration + 1,
            "user_feedback": ""
        }
