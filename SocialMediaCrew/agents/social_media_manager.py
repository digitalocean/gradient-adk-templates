"""
Social Media Manager Agent - Content Optimization.

This agent optimizes and polishes social media content for maximum
engagement, ensuring platform best practices are followed.
"""

import os
import sys
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient

from agents.copywriter import SocialMediaContent, ThreadPost

# Import prompts from central prompts.py - edit that file to customize
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import (
    get_optimization_system,
    get_optimization_prompt,
    get_platform_best_practices,
    ENGAGEMENT_ANALYST_SYSTEM,
)

logger = logging.getLogger(__name__)

# Model configuration
MODEL = "openai-gpt-4.1"


def get_model(temperature: float = 0.4) -> ChatGradient:
    """Get a ChatGradient instance."""
    return ChatGradient(
        model=MODEL,
        temperature=temperature
    )


class OptimizationSuggestion(BaseModel):
    """A suggestion for content optimization."""
    area: str = Field(description="Area of improvement")
    original: str = Field(description="Original text or element")
    suggested: str = Field(description="Suggested improvement")
    reason: str = Field(description="Why this improves engagement")


class OptimizedContent(BaseModel):
    """Optimized social media content."""
    platform: str = Field(description="Target platform")
    content_type: str = Field(description="Type of content")
    main_post: str = Field(description="Optimized main post")
    thread_posts: List[ThreadPost] = Field(default_factory=list, description="Optimized thread posts")
    hashtags: List[str] = Field(description="Optimized hashtags")
    call_to_action: str = Field(description="Optimized CTA")
    hook_used: str = Field(description="The viral hook")
    image_prompt: str = Field(description="Optimized image prompt")
    best_posting_time: str = Field(description="Suggested posting time")
    engagement_prediction: str = Field(description="Predicted engagement level")
    optimizations_made: List[str] = Field(description="List of optimizations applied")


def optimize_content(content: SocialMediaContent) -> OptimizedContent:
    """
    Optimize social media content for maximum engagement.

    Args:
        content: Content from the Copywriter agent

    Returns:
        OptimizedContent with improvements applied
    """
    logger.info(f"Optimizing content for {content.platform}")

    model = get_model(temperature=0.4)
    structured_model = model.with_structured_output(OptimizedContent)

    content_text = _format_content(content)
    platform_best_practices = get_platform_best_practices(content.platform)

    prompt = get_optimization_prompt(content.platform, content_text, platform_best_practices)

    optimized = structured_model.invoke([
        {"role": "system", "content": get_optimization_system(content.platform)},
        {"role": "user", "content": prompt}
    ])

    logger.info(f"Content optimized with {len(optimized.optimizations_made)} improvements")
    return optimized


def analyze_engagement_potential(content: SocialMediaContent) -> dict:
    """
    Analyze the engagement potential of content.

    Args:
        content: Content to analyze

    Returns:
        Analysis dictionary with scores and insights
    """
    logger.info("Analyzing engagement potential")

    model = get_model(temperature=0.2)

    content_text = _format_content(content)

    class EngagementAnalysis(BaseModel):
        hook_score: int = Field(description="Hook strength 1-10")
        value_score: int = Field(description="Value delivered 1-10")
        shareability_score: int = Field(description="Likelihood to be shared 1-10")
        comment_potential: int = Field(description="Likelihood to get comments 1-10")
        overall_score: int = Field(description="Overall engagement potential 1-10")
        strengths: List[str] = Field(description="Content strengths")
        weaknesses: List[str] = Field(description="Areas for improvement")
        viral_potential: str = Field(description="Low/Medium/High/Very High")

    structured_model = model.with_structured_output(EngagementAnalysis)

    prompt = f"""Analyze this social media content for engagement potential on {content.platform}.

**Content:**
{content_text}

Score each aspect from 1-10 and provide specific strengths and weaknesses.
Be honest and critical - this helps improve the content."""

    analysis = structured_model.invoke([
        {"role": "system", "content": ENGAGEMENT_ANALYST_SYSTEM},
        {"role": "user", "content": prompt}
    ])

    return analysis.model_dump()


def suggest_variations(content: SocialMediaContent, count: int = 3) -> List[str]:
    """
    Suggest alternative hooks or angles for the content.

    Args:
        content: Original content
        count: Number of variations to suggest

    Returns:
        List of alternative hook/opening variations
    """
    logger.info(f"Generating {count} content variations")

    model = get_model(temperature=0.8)

    class HookVariations(BaseModel):
        variations: List[str] = Field(description="Alternative hooks/openings")

    structured_model = model.with_structured_output(HookVariations)

    prompt = f"""Create {count} alternative opening hooks for this {content.platform} content.

**Current opening:**
{content.main_post[:280]}

**Content topic:** {content.hook_used}

Create {count} completely different hooks that could work for the same content.
Each should use a different psychological trigger:
- Curiosity gap
- Controversial take
- Surprising statistic
- Personal story hook
- Question hook
- Bold claim

Make each hook scroll-stopping and authentic."""

    result = structured_model.invoke([
        {"role": "system", "content": "You are a viral content specialist who creates irresistible hooks."},
        {"role": "user", "content": prompt}
    ])

    return result.variations


def _format_content(content: SocialMediaContent) -> str:
    """Format content for display."""
    lines = [f"Main Post:\n{content.main_post}"]

    if content.thread_posts:
        lines.append("\nThread:")
        for post in content.thread_posts:
            lines.append(f"[{post.post_number}] {post.content}")

    lines.append(f"\nHashtags: {' '.join(content.hashtags)}")
    lines.append(f"CTA: {content.call_to_action}")
    lines.append(f"Hook: {content.hook_used}")

    return "\n".join(lines)


