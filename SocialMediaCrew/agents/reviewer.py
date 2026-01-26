"""
Reviewer Agent - Content Quality Control.

This agent reviews content for quality, brand safety, and viral potential,
providing approval or specific feedback for revisions.
"""

import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient

from agents.copywriter import SocialMediaContent
from agents.social_media_manager import OptimizedContent

logger = logging.getLogger(__name__)

# Model configuration
MODEL = "openai-gpt-4.1"


def get_model(temperature: float = 0.2) -> ChatGradient:
    """Get a ChatGradient instance."""
    return ChatGradient(
        model=MODEL,
        temperature=temperature
    )


class ReviewFeedback(BaseModel):
    """Detailed feedback from content review."""
    category: str = Field(description="Category: hook, value, tone, cta, hashtags, safety, other")
    issue: str = Field(description="Description of the issue")
    suggestion: str = Field(description="Specific suggestion for improvement")
    severity: str = Field(description="Severity: minor, moderate, major, critical")


class ContentReview(BaseModel):
    """Complete review of social media content."""
    approved: bool = Field(description="Whether the content is approved for publishing")
    overall_quality: int = Field(description="Overall quality score 1-10")
    viral_potential: int = Field(description="Viral potential score 1-10")
    brand_safety: int = Field(description="Brand safety score 1-10")
    feedback: List[ReviewFeedback] = Field(default_factory=list, description="Specific feedback items")
    summary: str = Field(description="Summary of the review")
    approval_conditions: Optional[str] = Field(default=None, description="Conditions for approval if not approved")


def review_content(
    content: OptimizedContent,
    brand_guidelines: Optional[str] = None,
    approval_threshold: int = 7
) -> ContentReview:
    """
    Review content for quality and approval.

    Args:
        content: Optimized content to review
        brand_guidelines: Optional brand guidelines to check against
        approval_threshold: Minimum quality score for auto-approval (1-10)

    Returns:
        ContentReview with approval decision and feedback
    """
    logger.info(f"Reviewing content for {content.platform}")

    model = get_model(temperature=0.2)
    structured_model = model.with_structured_output(ContentReview)

    content_text = _format_content(content)

    brand_section = ""
    if brand_guidelines:
        brand_section = f"""
**Brand Guidelines to Follow:**
{brand_guidelines}
"""

    prompt = f"""You are a senior content reviewer for a major brand's social media presence.
Review this content thoroughly before it goes live.

**Content to Review:**
{content_text}

**Platform:** {content.platform}
**Engagement Prediction:** {content.engagement_prediction}
{brand_section}

**Review Criteria:**

1. **Hook Quality**: Is the opening scroll-stopping? Does it create curiosity?
2. **Value Delivery**: Does the content deliver real value to readers?
3. **Authenticity**: Does it sound human and authentic, not corporate or AI-generated?
4. **Tone**: Is the tone appropriate for the platform and audience?
5. **Call-to-Action**: Is the CTA clear and compelling?
6. **Hashtag Strategy**: Are hashtags relevant and not overdone?
7. **Brand Safety**: Any controversial, offensive, or risky content?
8. **Factual Accuracy**: Any claims that could be misleading?
9. **Engagement Potential**: Will this drive meaningful engagement?
10. **Grammar/Spelling**: Any errors?

**Approval Criteria:**
- Overall quality must be {approval_threshold}+ out of 10 for approval
- Brand safety must be 8+ out of 10
- No critical issues

Be constructive but honest. If content needs work, provide specific, actionable feedback.
Only approve content that is genuinely ready to publish."""

    review = structured_model.invoke([
        {"role": "system", "content": "You are a meticulous content reviewer who maintains high standards while being constructive."},
        {"role": "user", "content": prompt}
    ])

    # Apply automatic rules
    if review.brand_safety < 8:
        review.approved = False
        if not review.approval_conditions:
            review.approval_conditions = "Brand safety must be improved before approval."

    if review.overall_quality < approval_threshold:
        review.approved = False

    # Check for critical feedback
    critical_issues = [f for f in review.feedback if f.severity == "critical"]
    if critical_issues:
        review.approved = False

    logger.info(f"Review complete: {'Approved' if review.approved else 'Needs revision'} (Quality: {review.overall_quality}/10)")
    return review


def quick_review(content: SocialMediaContent) -> dict:
    """
    Perform a quick review for immediate feedback.

    Args:
        content: Content to review

    Returns:
        Dictionary with quick scores and top issues
    """
    logger.info("Performing quick review")

    model = get_model(temperature=0.2)

    class QuickReview(BaseModel):
        hook_score: int = Field(description="Hook quality 1-10")
        ready_to_publish: bool = Field(description="Whether content is ready")
        top_issue: Optional[str] = Field(description="Most important issue to fix, if any")
        quick_suggestion: Optional[str] = Field(description="Quick fix suggestion")

    structured_model = model.with_structured_output(QuickReview)

    prompt = f"""Quick review this {content.platform} content:

{content.main_post}

CTA: {content.call_to_action}

Is this ready to publish? What's the biggest issue if not?"""

    result = structured_model.invoke([
        {"role": "system", "content": "You are a quick-thinking content reviewer."},
        {"role": "user", "content": prompt}
    ])

    return result.model_dump()


def check_brand_safety(content: str) -> dict:
    """
    Check content for brand safety issues.

    Args:
        content: Text content to check

    Returns:
        Dictionary with safety assessment
    """
    logger.info("Checking brand safety")

    model = get_model(temperature=0.1)

    class SafetyCheck(BaseModel):
        is_safe: bool = Field(description="Whether content is brand-safe")
        risk_level: str = Field(description="Risk level: none, low, medium, high, critical")
        concerns: List[str] = Field(default_factory=list, description="Specific concerns identified")
        recommendation: str = Field(description="Recommendation for handling")

    structured_model = model.with_structured_output(SafetyCheck)

    prompt = f"""Assess this content for brand safety:

{content}

Check for:
- Controversial political statements
- Potentially offensive content
- Misleading claims
- Inappropriate humor
- Cultural insensitivity
- Legal risks
- Reputational risks

Be thorough but not overly cautious - edgy content can work if done tastefully."""

    result = structured_model.invoke([
        {"role": "system", "content": "You are a brand safety expert who protects brands while allowing creative content."},
        {"role": "user", "content": prompt}
    ])

    return result.model_dump()


def compile_feedback_for_revision(review: ContentReview) -> str:
    """
    Compile review feedback into actionable revision instructions.

    Args:
        review: The content review

    Returns:
        Formatted feedback string for the copywriter
    """
    lines = ["# Revision Required", ""]
    lines.append(f"**Overall Assessment:** {review.summary}")
    lines.append(f"**Quality Score:** {review.overall_quality}/10")
    lines.append(f"**Viral Potential:** {review.viral_potential}/10")
    lines.append("")

    if review.approval_conditions:
        lines.append(f"**Conditions for Approval:** {review.approval_conditions}")
        lines.append("")

    if review.feedback:
        lines.append("## Specific Feedback:")
        for i, fb in enumerate(review.feedback, 1):
            severity_emoji = {
                "minor": "",
                "moderate": "",
                "major": "",
                "critical": ""
            }.get(fb.severity, "")
            lines.append(f"\n### {i}. {fb.category.title()} {severity_emoji}")
            lines.append(f"**Issue:** {fb.issue}")
            lines.append(f"**Suggestion:** {fb.suggestion}")

    return "\n".join(lines)


def _format_content(content: OptimizedContent) -> str:
    """Format content for review."""
    lines = [f"**Main Post:**\n{content.main_post}"]

    if content.thread_posts:
        lines.append("\n**Thread:**")
        for post in content.thread_posts:
            lines.append(f"[{post.post_number}] {post.content}")

    lines.append(f"\n**Hashtags:** {' '.join(content.hashtags)}")
    lines.append(f"**CTA:** {content.call_to_action}")
    lines.append(f"**Hook:** {content.hook_used}")
    lines.append(f"**Image Prompt:** {content.image_prompt}")

    return "\n".join(lines)
