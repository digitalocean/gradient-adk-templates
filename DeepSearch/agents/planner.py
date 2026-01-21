import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

PLAN_GENERATOR_PROMPT = """You are an expert research planner. Your task is to create a comprehensive research plan for investigating a given topic.

Given the research topic, create a detailed research plan with 3-5 specific research goals. Each goal should be classified as either:
- [RESEARCH] - Goals that guide information gathering via web search
- [DELIVERABLE] - Goals that guide creation of final outputs (tables, summaries, reports)

For each goal, provide:
1. A clear objective describing what information to find or create
2. The type tag ([RESEARCH] or [DELIVERABLE])
3. Key questions to answer for this goal

Research Topic: {topic}

Create a research plan that will result in a thorough, well-cited report on this topic."""

PLAN_REFINEMENT_PROMPT = """You are an expert research planner helping to refine a research plan based on user feedback.

Current Research Plan:
{current_plan}

User Feedback: {feedback}

Please update the research plan based on the user's feedback. You can:
- Add new goals
- Remove existing goals
- Modify goal descriptions or questions
- Reorder goals

Maintain the [RESEARCH] and [DELIVERABLE] tags for each goal."""


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
    return ChatOpenAI(
        model="openai-gpt-4.1",
        base_url="https://inference.do-ai.run/v1",
        api_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY"),
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

    planner_model = get_planner_model()
    structured_model = planner_model.with_structured_output(ResearchPlan)

    prompt = PLAN_GENERATOR_PROMPT.format(topic=topic)
    plan = structured_model.invoke([{"role": "user", "content": prompt}])

    plan_display = format_plan_for_display(plan)
    logger.info(f"Generated plan with {len(plan.goals)} goals")

    return {
        "research_plan": plan,
        "plan_display": plan_display,
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

    planner_model = get_planner_model()
    structured_model = planner_model.with_structured_output(ResearchPlan)

    current_plan_text = format_plan_for_display(current_plan)
    prompt = PLAN_REFINEMENT_PROMPT.format(
        current_plan=current_plan_text,
        feedback=feedback
    )

    refined_plan = structured_model.invoke([{"role": "user", "content": prompt}])
    plan_display = format_plan_for_display(refined_plan)

    logger.info(f"Refined plan now has {len(refined_plan.goals)} goals")

    return {
        "research_plan": refined_plan,
        "plan_display": plan_display,
        "plan_iteration": iteration + 1,
        "user_feedback": ""  # Clear feedback after processing
    }
