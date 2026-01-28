import os
import logging
from typing import List, Dict
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient

# Import prompts from central prompts.py - edit that file to customize
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import COMPOSER_PROMPT

logger = logging.getLogger(__name__)


class ComposedSection(BaseModel):
    """A composed section of the report."""
    title: str = Field(description="Section title")
    content: str = Field(description="Section content with inline citations")


class FinalReport(BaseModel):
    """The complete research report."""
    title: str = Field(description="Report title")
    introduction: str = Field(description="Introduction with citations")
    sections: List[ComposedSection] = Field(description="Main content sections")
    conclusion: str = Field(description="Conclusion summarizing key findings")
    references: List[str] = Field(description="Numbered reference list")


def get_composer_model():
    return ChatGradient(
        model="openai-gpt-4.1",
        temperature=0.4
    )


def format_section_findings(section_findings: List[Dict]) -> str:
    """Format section findings for the composer prompt."""
    text = ""
    for section in section_findings:
        text += f"\n### {section['section_title']}\n"
        text += f"**Description:** {section.get('section_description', '')}\n\n"
        text += f"**Research Summary:**\n{section.get('combined_summary', 'No summary available')}\n\n"

        if section.get("all_findings"):
            text += "**Key Findings:**\n"
            for finding in section["all_findings"][:10]:  # Limit to top 10 findings per section
                if isinstance(finding, dict):
                    text += f"- {finding.get('content', '')} [Source: {finding.get('source_title', 'Unknown')}]\n"
        text += "\n"
    return text


def format_sources(all_sources: Dict) -> str:
    """Format sources for the composer prompt with numbered references."""
    text = ""
    for i, (url, source) in enumerate(all_sources.items(), 1):
        title = source.get("title", "Unknown")
        text += f"[{i}] {title}\n    URL: {url}\n"
    return text


def compose_report(state: dict) -> dict:
    """
    Compose the final research report from section findings.

    Args:
        state: Current state containing all section findings

    Returns:
        Updated state with the final report
    """
    topic = state.get("topic", "")
    report_outline = state.get("report_outline")
    section_findings = state.get("section_findings", [])
    all_sources = state.get("all_sources", {})

    logger.info(f"Composing final report for topic: {topic}")
    logger.info(f"  Sections to compose: {len(section_findings)}")
    logger.info(f"  Total sources: {len(all_sources)}")

    # Get report metadata from outline
    report_title = report_outline.title if report_outline else f"Research Report: {topic}"
    introduction_points = "\n".join(report_outline.introduction_points) if report_outline else ""
    conclusion_points = "\n".join(report_outline.conclusion_points) if report_outline else ""

    # Format inputs for composer
    section_findings_text = format_section_findings(section_findings)
    sources_text = format_sources(all_sources)

    composer_model = get_composer_model()
    structured_model = composer_model.with_structured_output(FinalReport)

    prompt = COMPOSER_PROMPT.format(
        topic=topic,
        report_title=report_title,
        introduction_points=introduction_points,
        section_findings=section_findings_text,
        conclusion_points=conclusion_points,
        sources=sources_text
    )

    logger.info("  Generating report structure...")
    report = structured_model.invoke([{"role": "user", "content": prompt}])

    # Format the report as markdown
    logger.info("  Formatting markdown output...")
    markdown_report = f"# {report.title}\n\n"
    markdown_report += f"{report.introduction}\n\n"

    for section in report.sections:
        markdown_report += f"## {section.title}\n\n"
        markdown_report += f"{section.content}\n\n"

    markdown_report += f"## Conclusion\n\n{report.conclusion}\n\n"
    markdown_report += "## References\n\n"
    for ref in report.references:
        markdown_report += f"{ref}\n"

    logger.info(f"  Report composed: {len(markdown_report)} characters, {len(report.sections)} sections")

    return {
        "final_report": report,
        "markdown_report": markdown_report
    }
