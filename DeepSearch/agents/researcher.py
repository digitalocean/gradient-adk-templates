import os
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient

logger = logging.getLogger(__name__)

# Import will be done at runtime to avoid circular imports
# from tools.serper_search import serper_search

RESEARCHER_PROMPT = """You are a thorough research analyst. Your task is to analyze search results and extract relevant information for a specific section of a research report.

Research Topic: {topic}
Current Section: {section_title}
Section Description: {section_description}
Search Query: {query}

Search Results:
{search_results}

Analyze these search results and extract:
1. Key facts and findings relevant to this section
2. Important data points, statistics, or quotes
3. Source attribution for each piece of information

Synthesize the information into a coherent summary that will help write this section of the report.
Be specific about which sources support which claims."""


class Finding(BaseModel):
    """A single research finding with source."""
    content: str = Field(description="The factual information or finding")
    source_url: str = Field(description="URL of the source")
    source_title: str = Field(description="Title of the source")


class SectionResearchOutput(BaseModel):
    """Output from researching a section."""
    summary: str = Field(description="Synthesized summary of findings for this section")
    findings: List[Finding] = Field(description="Individual findings with sources")
    quality_score: int = Field(description="Self-assessed quality score 1-10")
    gaps: List[str] = Field(description="Information gaps that might need more research")


def get_researcher_model():
    return ChatGradient(
        model="openai-gpt-4.1",
        temperature=0.2
    )


def research_current_section(state: dict) -> dict:
    """
    Research the current section by executing its search queries.

    Args:
        state: Current state containing the report outline and current section index

    Returns:
        Updated state with research findings for the current section
    """
    # Import here to avoid circular imports
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools.serper_search import serper_search

    topic = state.get("topic", "")
    outline = state.get("report_outline")
    current_index = state.get("current_section_index", 0)
    section_findings = state.get("section_findings", [])
    all_sources = state.get("all_sources", {})

    if current_index >= len(outline.sections):
        logger.info("All sections have been researched")
        return {"research_complete": True}

    current_section = outline.sections[current_index]
    logger.info(f"Researching section {current_index + 1}/{len(outline.sections)}: {current_section.title}")

    researcher_model = get_researcher_model()
    structured_model = researcher_model.with_structured_output(SectionResearchOutput)

    section_research = {
        "section_title": current_section.title,
        "section_description": current_section.description,
        "query_results": [],
        "combined_summary": "",
        "all_findings": [],
        "gaps": []
    }

    # Execute each search query for this section
    for query_index, query in enumerate(current_section.search_queries):
        logger.info(f"  Executing query {query_index + 1}/{len(current_section.search_queries)}: {query[:50]}...")

        try:
            # Perform search
            search_results = serper_search(query, num_results=5)

            # Format search results for the prompt
            formatted_results = ""
            for i, result in enumerate(search_results.results, 1):
                formatted_results += f"\n{i}. {result.title}\n"
                formatted_results += f"   URL: {result.link}\n"
                formatted_results += f"   {result.snippet}\n"

            # Analyze results
            prompt = RESEARCHER_PROMPT.format(
                topic=topic,
                section_title=current_section.title,
                section_description=current_section.description,
                query=query,
                search_results=formatted_results
            )

            research_output = structured_model.invoke([{"role": "user", "content": prompt}])

            # Store query results
            section_research["query_results"].append({
                "query": query,
                "summary": research_output.summary,
                "findings": [f.model_dump() for f in research_output.findings],
                "quality_score": research_output.quality_score,
                "gaps": research_output.gaps
            })

            section_research["all_findings"].extend([f.model_dump() for f in research_output.findings])
            section_research["gaps"].extend(research_output.gaps)

            # Track sources
            for finding in research_output.findings:
                source_key = finding.source_url
                if source_key not in all_sources:
                    all_sources[source_key] = {
                        "url": finding.source_url,
                        "title": finding.source_title,
                        "sections": []
                    }
                if current_section.title not in all_sources[source_key]["sections"]:
                    all_sources[source_key]["sections"].append(current_section.title)

            logger.info(f"    Found {len(research_output.findings)} findings, quality score: {research_output.quality_score}/10")

        except Exception as e:
            logger.error(f"    Error executing query: {str(e)}")
            section_research["query_results"].append({
                "query": query,
                "error": str(e)
            })

    # Create combined summary for the section
    if section_research["query_results"]:
        summaries = [qr.get("summary", "") for qr in section_research["query_results"] if "summary" in qr]
        section_research["combined_summary"] = "\n\n".join(summaries)

    section_findings.append(section_research)

    # Calculate average quality score
    quality_scores = [
        qr.get("quality_score", 5)
        for qr in section_research["query_results"]
        if "quality_score" in qr
    ]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 5

    logger.info(f"  Completed section '{current_section.title}' with avg quality: {avg_quality:.1f}/10")

    return {
        "section_findings": section_findings,
        "all_sources": all_sources,
        "current_section_index": current_index + 1,
        "last_section_quality": avg_quality,
        "last_section_gaps": list(set(section_research["gaps"]))
    }
