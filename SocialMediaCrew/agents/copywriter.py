"""
Copywriter Agent - Content Creation.

This agent creates engaging social media content based on research briefs,
crafting viral-worthy posts and threads.
"""

import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from agents.researcher import ResearchBrief

logger = logging.getLogger(__name__)

# Model configuration
MODEL = "openai-gpt-4.1"
BASE_URL = "https://inference.do-ai.run/v1"


def get_model(temperature: float = 0.7) -> ChatOpenAI:
    """Get a ChatOpenAI instance configured for Gradient."""
    return ChatOpenAI(
        model=MODEL,
        base_url=BASE_URL,
        api_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY"),
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

    platform_guidelines = _get_platform_guidelines(platform)

    prompt = f"""You are an expert social media copywriter known for creating viral content.

Create a {content_type} for {platform} based on this research brief:

**Topic:** {research_brief.main_topic}

**Trending Context:** {research_brief.trending_context}

**Key Facts to Include:**
{chr(10).join(f'- {fact}' for fact in research_brief.key_facts)}

**Viral Hooks to Consider:**
{chr(10).join(f'- {hook}' for hook in research_brief.viral_hooks)}

**Target Emotions:** {', '.join(research_brief.target_emotions)}

**Suggested Hashtags:** {', '.join(research_brief.hashtag_suggestions)}

**Avoid:** {', '.join(research_brief.content_warnings) if research_brief.content_warnings else 'Nothing specific'}

**Platform Guidelines:**
{platform_guidelines}

{"Create a thread with " + str(thread_length) + " posts. The first post should hook readers, middle posts deliver value, and the last post should have a strong CTA." if content_type == "thread" else "Create a single impactful post."}

Requirements:
1. Start with an attention-grabbing hook (pattern interrupt, controversial take, or surprising stat)
2. Deliver genuine value - don't be clickbait
3. Use conversational, authentic tone
4. Include a clear call-to-action
5. Suggest an image prompt that would complement the content

Make the content feel authentic and shareable, not corporate or salesy."""

    content = structured_model.invoke([
        {"role": "system", "content": f"You are a viral {platform} content creator with millions of followers. You write content that gets massive engagement."},
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

    prompt = f"""You are revising social media content based on reviewer feedback.

**Original Content:**
{original_text}

**Reviewer Feedback:**
{feedback}

**Original Research Brief:**
Topic: {research_brief.main_topic}
Key Facts: {', '.join(research_brief.key_facts[:3])}
Viral Hooks: {', '.join(research_brief.viral_hooks[:3])}

Please revise the content to address the feedback while maintaining:
1. The viral potential and hook
2. Authentic, conversational tone
3. Clear value delivery
4. Strong call-to-action

Create improved content that addresses all feedback points."""

    revised_content = structured_model.invoke([
        {"role": "system", "content": "You are an expert copywriter revising content based on editorial feedback."},
        {"role": "user", "content": prompt}
    ])

    logger.info("Content revised successfully")
    return revised_content


def _get_platform_guidelines(platform: str) -> str:
    """Get platform-specific content guidelines."""
    guidelines = {
        "twitter": """
- Character limit: 280 per post (but threads can be longer)
- Use line breaks for readability
- Emojis can increase engagement but don't overdo it
- First line is crucial - it shows in preview
- End threads with a retweet request or follow CTA
- Use 2-3 relevant hashtags max
""",
        "instagram": """
- Captions can be up to 2,200 characters
- First 125 characters show in preview - make them count
- Use more hashtags (up to 30, but 5-10 targeted ones work best)
- Include a clear CTA (save, share, comment)
- Emojis are expected and increase engagement
- Break up text with line breaks and emojis
""",
        "linkedin": """
- Professional but personable tone
- First 2 lines are crucial (before "see more")
- Longer posts (1,300+ characters) often perform well
- Use minimal hashtags (3-5)
- Include a question to drive comments
- Share insights, lessons learned, or industry perspectives
- Avoid overly promotional content
"""
    }
    return guidelines.get(platform.lower(), guidelines["twitter"])


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
