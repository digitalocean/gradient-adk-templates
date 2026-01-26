import os
import logging
from typing import List
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient

logger = logging.getLogger(__name__)

SECTION_PLANNER_PROMPT = """You are an expert report architect. Your task is to convert a research plan into a structured report outline with specific sections.

Research Topic: {topic}

Research Plan Goals:
{goals}

Create a report outline with 3-6 sections. For each section:
1. Provide a clear title
2. Write a brief description of what this section will cover
3. List 2-4 specific search queries that will help gather information for this section
4. Map which research goals this section addresses

The sections should flow logically and cover all aspects of the research plan."""


class ReportSection(BaseModel):
    """A section of the report outline."""
    title: str = Field(description="Section title")
    description: str = Field(description="Brief description of what this section covers")
    search_queries: List[str] = Field(description="Specific search queries for this section")
    related_goals: List[int] = Field(description="Indices of research goals this section addresses")


class ReportOutline(BaseModel):
    """The complete report outline."""
    title: str = Field(description="Report title")
    sections: List[ReportSection] = Field(description="List of report sections")
    introduction_points: List[str] = Field(description="Key points for the introduction")
    conclusion_points: List[str] = Field(description="Key points for the conclusion")


def get_section_planner_model():
    return ChatGradient(
        model="openai-gpt-4.1",
        temperature=0.3
    )


def plan_sections(state: dict) -> dict:
    """
    Convert the research plan into a structured report outline with sections.

    Args:
        state: Current state containing the approved research plan

    Returns:
        Updated state with the report outline and sections to research
    """
    research_plan = state.get("research_plan")
    topic = state.get("topic", "")

    logger.info(f"Planning report sections for topic: {topic}")

    # Format goals for the prompt
    goals_text = ""
    for i, goal in enumerate(research_plan.goals, 1):
        goals_text += f"{i}. [{goal.goal_type}] {goal.objective}\n"
        goals_text += f"   Key questions: {', '.join(goal.key_questions)}\n"

    section_planner = get_section_planner_model()
    structured_model = section_planner.with_structured_output(ReportOutline)

    prompt = SECTION_PLANNER_PROMPT.format(
        topic=topic,
        goals=goals_text
    )

    outline = structured_model.invoke([{"role": "user", "content": prompt}])

    logger.info(f"Created report outline with {len(outline.sections)} sections")
    for i, section in enumerate(outline.sections, 1):
        logger.info(f"  Section {i}: {section.title} ({len(section.search_queries)} queries)")

    return {
        "report_outline": outline,
        "current_section_index": 0,
        "total_sections": len(outline.sections),
        "section_findings": []
    }
