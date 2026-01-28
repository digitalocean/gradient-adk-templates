"""
Copywriter Agent - Content Creation.

This agent creates engaging social media content based on research briefs,
crafting viral-worthy posts and threads.
"""

import os
import sys
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient

from agents.researcher import ResearchBrief

# Import prompts from central prompts.py - edit that file to customize
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import (
    get_copywriter_system,
    get_content_creation_prompt,
    get_platform_guidelines,
    REVISION_SYSTEM,
    get_revision_prompt,
)

logger = logging.getLogger(__name__)

# Model configuration
MODEL = "openai-gpt-4.1"


def get_model(temperature: float = 0.7) -> ChatGradient:
    """Get a ChatGradient instance."""
    return ChatGradient(
        model=MODEL,
        temperature=temperature
    )


class ThreadPost(BaseModel):
    """A single post in a thread."""
    post_number: int = Field(description="Position in the thread (1-indexed)")
    content: str = Field(description="The post content")
    has_hook: bool = Field(description="Whether this post contains a hook")


class SocialMediaContent(BaseModel):
    """Generated social media content."""
    platform: str = Field(description="Target platform")
    content_type: str = Field(description="Type of content: 'single_post' or 'thread'")
    main_post: str = Field(description="The main post or first post of thread")
    thread_posts: List[ThreadPost] = Field(default_factory=list, description="Additional posts if thread")
    hashtags: List[str] = Field(description="Hashtags to include")
    call_to_action: str = Field(description="The call to action")
    hook_used: str = Field(description="The viral hook used in the content")
    image_prompt: str = Field(description="Prompt for generating accompanying image")


def create_content(
    research_brief: ResearchBrief,
    platform: str = "twitter",
    content_type: str = "thread",
    thread_length: int = 5
) -> SocialMediaContent:
    """
    Create social media content based on research.

    Args:
        research_brief: Research brief from the Researcher agent
        platform: Target platform (twitter, instagram, linkedin)
        content_type: Type of content to create (single_post, thread)
        thread_length: Number of posts if creating a thread

    Returns:
        SocialMediaContent with the created content
    """
    logger.info(f"Creating {content_type} for {platform} about: {research_brief.main_topic}")

    model = get_model(temperature=0.7)
    structured_model = model.with_structured_output(SocialMediaContent)

    platform_guidelines = get_platform_guidelines(platform)

    prompt = get_content_creation_prompt(
        platform=platform,
        content_type=content_type,
        topic=research_brief.main_topic,
        trending_context=research_brief.trending_context,
        key_facts=research_brief.key_facts,
        viral_hooks=research_brief.viral_hooks,
        target_emotions=research_brief.target_emotions,
        hashtag_suggestions=research_brief.hashtag_suggestions,
        content_warnings=research_brief.content_warnings,
        platform_guidelines=platform_guidelines,
        thread_length=thread_length
    )

    content = structured_model.invoke([
        {"role": "system", "content": get_copywriter_system(platform)},
        {"role": "user", "content": prompt}
    ])

    logger.info(f"Content created: {content.content_type} with {len(content.thread_posts)} posts")
    return content


def rewrite_content(
    original_content: SocialMediaContent,
    feedback: str,
    research_brief: ResearchBrief
) -> SocialMediaContent:
    """
    Rewrite content based on feedback.

    Args:
        original_content: The original content that needs revision
        feedback: Feedback from the reviewer
        research_brief: Original research brief

    Returns:
        Revised SocialMediaContent
    """
    logger.info(f"Rewriting content based on feedback")

    model = get_model(temperature=0.7)
    structured_model = model.with_structured_output(SocialMediaContent)

    original_text = _format_content_for_display(original_content)

    prompt = get_revision_prompt(
        original_text=original_text,
        feedback=feedback,
        topic=research_brief.main_topic,
        key_facts=research_brief.key_facts,
        viral_hooks=research_brief.viral_hooks
    )

    revised_content = structured_model.invoke([
        {"role": "system", "content": REVISION_SYSTEM},
        {"role": "user", "content": prompt}
    ])

    logger.info("Content revised successfully")
    return revised_content




def _format_content_for_display(content: SocialMediaContent) -> str:
    """Format content for display in prompts."""
    lines = [f"Platform: {content.platform}"]
    lines.append(f"Type: {content.content_type}")
    lines.append(f"\nMain Post:\n{content.main_post}")

    if content.thread_posts:
        lines.append("\nThread Posts:")
        for post in content.thread_posts:
            lines.append(f"\n[{post.post_number}] {post.content}")

    lines.append(f"\nHashtags: {' '.join(content.hashtags)}")
    lines.append(f"CTA: {content.call_to_action}")

    return "\n".join(lines)
