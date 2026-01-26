"""
Researcher Agent - Trending Topics Research.

This agent researches trending topics, gathers insights, and provides
context for creating viral social media content.
"""

import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from tools.web_search import (
    search_trending_topics,
    search_topic_insights,
    search_viral_content,
    SearchResults
)

logger = logging.getLogger(__name__)

# Model configuration
MODEL = "openai-gpt-4.1"
BASE_URL = "https://inference.do-ai.run/v1"


def get_model(temperature: float = 0.3) -> ChatOpenAI:
    """Get a ChatOpenAI instance configured for Gradient."""
    return ChatOpenAI(
        model=MODEL,
        base_url=BASE_URL,
        api_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY"),
        temperature=temperature
    )


class TrendingTopic(BaseModel):
    """A trending topic identified by research."""
    topic: str = Field(description="The trending topic")
    relevance_score: int = Field(description="Relevance score 1-10")
    why_trending: str = Field(description="Why this topic is trending")
    potential_angles: List[str] = Field(description="Potential angles for content")


class ResearchBrief(BaseModel):
    """Research brief compiled by the Researcher agent."""
    main_topic: str = Field(description="The main topic for content creation")
    trending_context: str = Field(description="Current trending context around this topic")
    key_facts: List[str] = Field(description="Key facts and statistics to include")
    viral_hooks: List[str] = Field(description="Potential viral hooks or angles")
    target_emotions: List[str] = Field(description="Emotions to target for engagement")
    hashtag_suggestions: List[str] = Field(description="Suggested hashtags")
    content_warnings: List[str] = Field(description="Topics or angles to avoid")


def research_topic(topic: str, platform: str = "twitter") -> ResearchBrief:
    """
    Research a topic and compile a brief for content creation.

    Args:
        topic: The topic to research
        platform: Target social media platform

    Returns:
        ResearchBrief with insights for content creation
    """
    logger.info(f"Researching topic: {topic} for {platform}")

    # Gather research from multiple sources
    trending_results = search_trending_topics(topic)
    insights_results = search_topic_insights(topic)
    viral_results = search_viral_content(topic, platform)

    # Compile research context
    research_context = _compile_research_context(
        trending_results, insights_results, viral_results
    )

    # Use LLM to synthesize research into a brief
    model = get_model(temperature=0.3)
    structured_model = model.with_structured_output(ResearchBrief)

    prompt = f"""You are a social media research expert. Analyze the following research
and create a comprehensive brief for creating viral {platform} content about "{topic}".

Research Data:
{research_context}

Create a research brief that will help a copywriter create engaging, viral content.
Focus on:
1. What's currently trending related to this topic
2. Key facts and statistics that would resonate with audiences
3. Viral hooks and angles that have worked for similar content
4. Emotional triggers that drive engagement
5. Relevant hashtags for discoverability
6. Any sensitive areas to avoid

Be specific and actionable in your recommendations."""

    brief = structured_model.invoke([
        {"role": "system", "content": "You are an expert social media researcher who identifies viral content opportunities."},
        {"role": "user", "content": prompt}
    ])

    logger.info(f"Research brief compiled for: {topic}")
    return brief


def identify_trending_topics(topic_area: str, count: int = 5) -> List[TrendingTopic]:
    """
    Identify trending topics within a topic area.

    Args:
        topic_area: The general area to search (e.g., "AI", "tech", "marketing")
        count: Number of trending topics to identify

    Returns:
        List of trending topics with analysis
    """
    logger.info(f"Identifying trending topics in: {topic_area}")

    # Search for trending content
    results = search_trending_topics(topic_area)

    if results.error:
        logger.error(f"Search failed: {results.error}")
        return []

    # Compile search results
    search_summary = "\n".join([
        f"- {r.title}: {r.snippet}"
        for r in results.results
    ])

    # Use LLM to identify and analyze trending topics
    model = get_model(temperature=0.3)

    prompt = f"""Analyze these search results about trending {topic_area} topics and identify
the top {count} trending topics that would make great social media content.

Search Results:
{search_summary}

For each topic, explain:
1. What the topic is
2. Why it's trending (score 1-10 for relevance)
3. Potential content angles

Return exactly {count} trending topics."""

    class TrendingTopicsList(BaseModel):
        topics: List[TrendingTopic] = Field(description=f"List of {count} trending topics")

    structured_model = model.with_structured_output(TrendingTopicsList)

    result = structured_model.invoke([
        {"role": "system", "content": "You are a trend analyst who identifies viral content opportunities."},
        {"role": "user", "content": prompt}
    ])

    logger.info(f"Identified {len(result.topics)} trending topics")
    return result.topics


def _compile_research_context(
    trending: SearchResults,
    insights: SearchResults,
    viral: SearchResults
) -> str:
    """Compile search results into a research context string."""
    sections = []

    if trending.results:
        sections.append("## Trending Topics")
        for r in trending.results[:5]:
            sections.append(f"- {r.title}: {r.snippet}")

    if insights.results:
        sections.append("\n## Topic Insights")
        for r in insights.results[:5]:
            sections.append(f"- {r.title}: {r.snippet}")

    if viral.results:
        sections.append("\n## Viral Content Examples")
        for r in viral.results[:5]:
            sections.append(f"- {r.title}: {r.snippet}")

    return "\n".join(sections) if sections else "No research data available."
