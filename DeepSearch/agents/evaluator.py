import os
import logging
from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient

logger = logging.getLogger(__name__)

SECTION_EVALUATOR_PROMPT = """You are a critical research evaluator. Your task is to assess the quality and completeness of research findings for a specific section of a report.

Research Topic: {topic}
Section Title: {section_title}
Section Description: {section_description}

Research Findings:
{findings}

Identified Gaps:
{gaps}

Evaluate the research based on:
1. Coverage: Does the research adequately address the section's objectives?
2. Depth: Is the information detailed enough for comprehensive writing?
3. Source Quality: Are the sources credible and diverse?
4. Completeness: Are there critical gaps that need to be filled?

Provide your evaluation with:
- An overall grade (pass/fail)
- Specific feedback on strengths and weaknesses
- Up to 3 follow-up search queries if the section needs more research"""


class SectionEvaluation(BaseModel):
    """Evaluation feedback for a section's research quality."""
    grade: Literal["pass", "fail"] = Field(
        description="'pass' if research is sufficient, 'fail' if more research needed"
    )
    strengths: List[str] = Field(description="What's working well")
    weaknesses: List[str] = Field(description="Areas that need improvement")
    follow_up_queries: List[str] = Field(
        description="Suggested follow-up queries if more research needed (max 3)"
    )
    summary: str = Field(description="Brief evaluation summary")


def get_evaluator_model():
    return ChatGradient(
        model="openai-gpt-4.1",
        temperature=0.1
    )


def evaluate_section(state: dict) -> dict:
    """
    Evaluate the quality of research for the most recently completed section.

    Args:
        state: Current state containing section findings

    Returns:
        Updated state with evaluation results
    """
    topic = state.get("topic", "")
    section_findings = state.get("section_findings", [])
    section_evaluations = state.get("section_evaluations", [])
    current_section_index = state.get("current_section_index", 0)
    evaluation_iterations = state.get("evaluation_iterations", {})
    max_section_iterations = state.get("max_section_iterations", 2)

    # Get the most recently completed section
    if not section_findings:
        logger.warning("No section findings to evaluate")
        return {"section_needs_more_research": False}

    latest_section = section_findings[-1]
    section_title = latest_section["section_title"]
    section_key = f"section_{len(section_findings) - 1}"

    # Track iteration count for this section
    current_iterations = evaluation_iterations.get(section_key, 0)

    logger.info(f"Evaluating section '{section_title}' (iteration {current_iterations + 1})")

    # Format findings for the prompt
    findings_text = latest_section.get("combined_summary", "")
    if not findings_text:
        findings_text = "No findings available"

    gaps_text = "\n".join(latest_section.get("gaps", [])) or "No gaps identified"

    evaluator_model = get_evaluator_model()
    structured_model = evaluator_model.with_structured_output(SectionEvaluation)

    prompt = SECTION_EVALUATOR_PROMPT.format(
        topic=topic,
        section_title=section_title,
        section_description=latest_section.get("section_description", ""),
        findings=findings_text,
        gaps=gaps_text
    )

    evaluation = structured_model.invoke([{"role": "user", "content": prompt}])

    logger.info(f"  Evaluation grade: {evaluation.grade}")
    logger.info(f"  Strengths: {len(evaluation.strengths)}, Weaknesses: {len(evaluation.weaknesses)}")

    # Update evaluation tracking
    evaluation_iterations[section_key] = current_iterations + 1

    # Determine if we need more research for this section
    needs_more = (
        evaluation.grade == "fail" and
        current_iterations < max_section_iterations and
        len(evaluation.follow_up_queries) > 0
    )

    if needs_more:
        logger.info(f"  Section needs more research. Follow-up queries: {evaluation.follow_up_queries}")
    else:
        if evaluation.grade == "pass":
            logger.info(f"  Section passed evaluation")
        else:
            logger.info(f"  Section failed but max iterations reached, moving on")

    section_evaluations.append({
        "section_title": section_title,
        "evaluation": evaluation.model_dump(),
        "iteration": current_iterations + 1
    })

    return {
        "section_evaluations": section_evaluations,
        "evaluation_iterations": evaluation_iterations,
        "section_needs_more_research": needs_more,
        "current_follow_up_queries": evaluation.follow_up_queries if needs_more else [],
        "last_evaluation": evaluation
    }


def enhanced_section_research(state: dict) -> dict:
    """
    Perform enhanced research for a section based on evaluator feedback.

    Args:
        state: Current state with follow-up queries

    Returns:
        Updated state with additional findings
    """
    # Import here to avoid circular imports
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools.serper_search import serper_search

    topic = state.get("topic", "")
    follow_up_queries = state.get("current_follow_up_queries", [])
    section_findings = state.get("section_findings", [])
    all_sources = state.get("all_sources", {})

    if not follow_up_queries or not section_findings:
        return {}

    # Get the section we're enhancing
    latest_section = section_findings[-1]
    section_title = latest_section["section_title"]

    logger.info(f"Performing enhanced research for section '{section_title}'")

    researcher_model = ChatGradient(
        model="openai-gpt-4.1",
        temperature=0.2
    )

    enhanced_findings = []

    for query in follow_up_queries[:3]:
        logger.info(f"  Follow-up query: {query[:50]}...")

        try:
            search_results = serper_search(query, num_results=5)

            # Simple analysis
            results_text = "\n".join([
                f"- {r.title}: {r.snippet}"
                for r in search_results.results
            ])

            analysis_prompt = f"""Analyze these search results for the section "{section_title}" of a report on "{topic}".
Query: {query}

Results:
{results_text}

Provide a brief summary of the key findings that address gaps in the current research."""

            response = researcher_model.invoke([{"role": "user", "content": analysis_prompt}])

            enhanced_findings.append({
                "query": query,
                "summary": response.content,
                "findings": [
                    {
                        "content": r.snippet,
                        "source_url": r.link,
                        "source_title": r.title
                    }
                    for r in search_results.results[:3]
                ]
            })

            # Track sources
            for r in search_results.results[:3]:
                if r.link not in all_sources:
                    all_sources[r.link] = {
                        "url": r.link,
                        "title": r.title,
                        "sections": []
                    }
                if section_title not in all_sources[r.link]["sections"]:
                    all_sources[r.link]["sections"].append(section_title)

            logger.info(f"    Added {len(search_results.results[:3])} findings")

        except Exception as e:
            logger.error(f"    Error in follow-up query: {str(e)}")

    # Update the latest section with enhanced findings
    if enhanced_findings:
        latest_section["query_results"].extend(enhanced_findings)
        for ef in enhanced_findings:
            if "summary" in ef:
                latest_section["combined_summary"] += f"\n\n{ef['summary']}"
            latest_section["all_findings"].extend(ef.get("findings", []))

        section_findings[-1] = latest_section

    return {
        "section_findings": section_findings,
        "all_sources": all_sources,
        "current_follow_up_queries": []
    }


def route_after_section_evaluation(state: dict) -> str:
    """
    Routing function to determine next step after section evaluation.

    Args:
        state: Current state with evaluation results

    Returns:
        Name of the next node to execute
    """
    if state.get("section_needs_more_research", False):
        return "enhanced_section_research"

    # Check if there are more sections to research
    outline = state.get("report_outline")
    current_index = state.get("current_section_index", 0)

    if outline and current_index < len(outline.sections):
        return "research_section"

    return "compose_report"
