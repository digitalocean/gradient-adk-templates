"""
Social Media Crew - Multi-Agent Content Creation System

A crew of AI agents that collaborate to create viral social media content:
- Researcher: Researches trending topics and gathers insights
- Copywriter: Creates engaging content based on research
- Social Media Manager: Optimizes content for maximum engagement
- Reviewer: Vets content for quality and brand safety

Uses LangGraph for workflow orchestration and Gradient ADK for deployment.
Includes image generation via fal's fast-sdxl model.
"""

import os
import logging
from typing import TypedDict, Optional, List, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from gradient_adk import entrypoint

from agents.researcher import research_topic, ResearchBrief
from agents.copywriter import create_content, rewrite_content, SocialMediaContent
from agents.social_media_manager import optimize_content, OptimizedContent
from agents.reviewer import review_content, compile_feedback_for_revision, ContentReview
from agents.image_prompt_designer import design_image_prompt, compile_image_prompt, ImagePromptDesign
from tools.image_generator import generate_image, ImageGenerationResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Model configuration
MODEL = "openai-gpt-4.1"
BASE_URL = "https://inference.do-ai.run/v1"

# Maximum revision iterations
MAX_REVISIONS = 3


def get_model(temperature: float = 0.3) -> ChatOpenAI:
    """Get a ChatOpenAI instance configured for Gradient."""
    return ChatOpenAI(
        model=MODEL,
        base_url=BASE_URL,
        api_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY"),
        temperature=temperature
    )


# =============================================================================
# State Definition
# =============================================================================

class CrewState(TypedDict, total=False):
    """State for the Social Media Crew workflow."""
    # Input
    topic: str
    platform: str  # twitter, instagram, linkedin
    content_type: str  # single_post, thread
    brand_guidelines: Optional[str]

    # Research phase
    research_brief: Optional[dict]  # ResearchBrief as dict for serialization

    # Content creation phase
    draft_content: Optional[dict]  # SocialMediaContent as dict
    optimized_content: Optional[dict]  # OptimizedContent as dict

    # Review phase
    review_result: Optional[dict]  # ContentReview as dict
    revision_count: int
    revision_feedback: Optional[str]

    # Image prompt design
    image_prompt_design: Optional[dict]  # ImagePromptDesign as dict
    compiled_image_prompt: Optional[str]

    # Image generation
    image_result: Optional[dict]  # ImageGenerationResult as dict

    # Output
    final_content: Optional[dict]
    error: Optional[str]


# =============================================================================
# Workflow Nodes
# =============================================================================

def research_node(state: CrewState) -> CrewState:
    """Researcher agent: Research the topic."""
    topic = state["topic"]
    platform = state.get("platform", "twitter")

    logger.info(f"[Researcher] Researching topic: {topic}")

    try:
        brief = research_topic(topic, platform)
        logger.info(f"[Researcher] Research complete. Key facts: {len(brief.key_facts)}")

        return {
            **state,
            "research_brief": brief.model_dump()
        }
    except Exception as e:
        logger.error(f"[Researcher] Research failed: {e}")
        return {
            **state,
            "error": f"Research failed: {str(e)}"
        }


def copywriter_node(state: CrewState) -> CrewState:
    """Copywriter agent: Create content based on research."""
    research_dict = state.get("research_brief")
    platform = state.get("platform", "twitter")
    content_type = state.get("content_type", "thread")
    revision_feedback = state.get("revision_feedback")

    if not research_dict:
        return {**state, "error": "No research brief available"}

    research_brief = ResearchBrief(**research_dict)

    logger.info(f"[Copywriter] Creating {content_type} for {platform}")

    try:
        if revision_feedback and state.get("draft_content"):
            # Rewrite based on feedback
            original_content = SocialMediaContent(**state["draft_content"])
            content = rewrite_content(original_content, revision_feedback, research_brief)
            logger.info("[Copywriter] Content revised based on feedback")
        else:
            # Create new content
            content = create_content(research_brief, platform, content_type)
            logger.info("[Copywriter] Initial draft created")

        return {
            **state,
            "draft_content": content.model_dump(),
            "revision_feedback": None  # Clear feedback after revision
        }
    except Exception as e:
        logger.error(f"[Copywriter] Content creation failed: {e}")
        return {
            **state,
            "error": f"Content creation failed: {str(e)}"
        }


def social_media_manager_node(state: CrewState) -> CrewState:
    """Social Media Manager agent: Optimize content."""
    draft_dict = state.get("draft_content")

    if not draft_dict:
        return {**state, "error": "No draft content available"}

    draft_content = SocialMediaContent(**draft_dict)

    logger.info(f"[Social Media Manager] Optimizing content for {draft_content.platform}")

    try:
        optimized = optimize_content(draft_content)
        logger.info(f"[Social Media Manager] Optimizations applied: {len(optimized.optimizations_made)}")

        return {
            **state,
            "optimized_content": optimized.model_dump()
        }
    except Exception as e:
        logger.error(f"[Social Media Manager] Optimization failed: {e}")
        return {
            **state,
            "error": f"Optimization failed: {str(e)}"
        }


def reviewer_node(state: CrewState) -> CrewState:
    """Reviewer agent: Review and approve/reject content."""
    optimized_dict = state.get("optimized_content")
    brand_guidelines = state.get("brand_guidelines")
    revision_count = state.get("revision_count", 0)

    if not optimized_dict:
        return {**state, "error": "No optimized content available"}

    optimized_content = OptimizedContent(**optimized_dict)

    logger.info(f"[Reviewer] Reviewing content (revision #{revision_count})")

    try:
        review = review_content(optimized_content, brand_guidelines)

        if review.approved:
            logger.info(f"[Reviewer] Content APPROVED (Quality: {review.overall_quality}/10)")
        else:
            logger.info(f"[Reviewer] Content needs REVISION (Quality: {review.overall_quality}/10)")

        return {
            **state,
            "review_result": review.model_dump(),
            "revision_count": revision_count + 1
        }
    except Exception as e:
        logger.error(f"[Reviewer] Review failed: {e}")
        return {
            **state,
            "error": f"Review failed: {str(e)}"
        }


def prepare_revision_node(state: CrewState) -> CrewState:
    """Prepare feedback for revision."""
    review_dict = state.get("review_result")

    if not review_dict:
        return state

    review = ContentReview(**review_dict)
    feedback = compile_feedback_for_revision(review)

    logger.info("[Coordinator] Preparing revision feedback for copywriter")

    return {
        **state,
        "revision_feedback": feedback
    }


def design_image_prompt_node(state: CrewState) -> CrewState:
    """Design an optimal image prompt based on the topic."""
    topic = state.get("topic", "")
    platform = state.get("platform", "twitter")

    if not topic:
        return {**state, "error": "No topic available for image prompt design"}

    logger.info(f"[Image Prompt Designer] Designing image for topic: {topic}")

    try:
        # Design a simple image prompt based on the topic
        design = design_image_prompt(topic, platform)

        # Compile into the final prompt
        compiled_prompt = compile_image_prompt(design)

        logger.info(f"[Image Prompt Designer] Design complete - Style: {design.art_style}")

        return {
            **state,
            "image_prompt_design": design.model_dump(),
            "compiled_image_prompt": compiled_prompt
        }
    except Exception as e:
        logger.error(f"[Image Prompt Designer] Design failed: {e}")
        # Fall back to a basic prompt if design fails
        return {
            **state,
            "compiled_image_prompt": f"Professional digital illustration about {topic}. No text or words."
        }


def generate_image_node(state: CrewState) -> CrewState:
    """Generate an image using the designed prompt."""
    topic = state.get("topic", "")
    platform = state.get("platform", "twitter")
    compiled_prompt = state.get("compiled_image_prompt")

    logger.info("[Image Generator] Generating image with designed prompt")

    try:
        # Use the compiled prompt from the designer, or fall back
        if not compiled_prompt or len(compiled_prompt) < 20:
            compiled_prompt = f"Professional digital illustration about {topic}. No text or words."

        logger.info(f"[Image Generator] Using prompt: {compiled_prompt[:200]}...")

        result = generate_image(
            prompt=compiled_prompt,
            output_format="square" if platform == "instagram" else "landscape_4_3"
        )

        if result.success:
            logger.info(f"[Image Generator] Image generated: {result.image_url}")
        else:
            logger.warning(f"[Image Generator] Image generation failed: {result.error}")

        return {
            **state,
            "image_result": result.model_dump()
        }
    except Exception as e:
        logger.error(f"[Image Generator] Image generation error: {e}")
        return {
            **state,
            "image_result": {"success": False, "error": str(e), "prompt": compiled_prompt or ""}
        }


def finalize_node(state: CrewState) -> CrewState:
    """Finalize the content package."""
    optimized_dict = state.get("optimized_content")
    review_dict = state.get("review_result")
    image_dict = state.get("image_result")
    image_design_dict = state.get("image_prompt_design")

    logger.info("[Coordinator] Finalizing content package")

    final_content = {
        "content": optimized_dict,
        "review": review_dict,
        "image": image_dict,
        "image_design": image_design_dict,
        "revisions_made": state.get("revision_count", 0)
    }

    return {
        **state,
        "final_content": final_content
    }


def handle_error_node(state: CrewState) -> CrewState:
    """Handle errors in the workflow."""
    error = state.get("error", "Unknown error occurred")
    logger.error(f"[Error Handler] Workflow error: {error}")

    return {
        **state,
        "final_content": {
            "error": error,
            "partial_content": state.get("optimized_content") or state.get("draft_content")
        }
    }


# =============================================================================
# Routing Functions
# =============================================================================

def route_after_review(state: CrewState) -> str:
    """Route based on review result."""
    if state.get("error"):
        return "handle_error"

    review_dict = state.get("review_result")
    if not review_dict:
        return "handle_error"

    review = ContentReview(**review_dict)
    revision_count = state.get("revision_count", 0)

    if review.approved:
        return "design_image_prompt"
    elif revision_count >= MAX_REVISIONS:
        logger.warning(f"[Router] Max revisions ({MAX_REVISIONS}) reached, forcing approval")
        return "design_image_prompt"
    else:
        return "prepare_revision"


def route_after_error_check(state: CrewState) -> str:
    """Check for errors and route accordingly."""
    if state.get("error"):
        return "handle_error"
    return "continue"


# =============================================================================
# Workflow Definition
# =============================================================================

def create_workflow():
    """Create the LangGraph workflow for the Social Media Crew."""
    workflow = StateGraph(CrewState)

    # Add nodes
    workflow.add_node("research", research_node)
    workflow.add_node("copywriter", copywriter_node)
    workflow.add_node("social_media_manager", social_media_manager_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("prepare_revision", prepare_revision_node)
    workflow.add_node("design_image_prompt", design_image_prompt_node)
    workflow.add_node("generate_image", generate_image_node)
    workflow.add_node("finalize", finalize_node)
    workflow.add_node("handle_error", handle_error_node)

    # Define edges
    workflow.add_edge(START, "research")
    workflow.add_edge("research", "copywriter")
    workflow.add_edge("copywriter", "social_media_manager")
    workflow.add_edge("social_media_manager", "reviewer")

    # Conditional routing after review
    workflow.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "design_image_prompt": "design_image_prompt",
            "prepare_revision": "prepare_revision",
            "handle_error": "handle_error"
        }
    )

    # Revision loop back to copywriter
    workflow.add_edge("prepare_revision", "copywriter")

    # Image prompt design leads to image generation
    workflow.add_edge("design_image_prompt", "generate_image")

    # After image generation, finalize
    workflow.add_edge("generate_image", "finalize")

    # Terminal edges
    workflow.add_edge("finalize", END)
    workflow.add_edge("handle_error", END)

    return workflow


# Create workflow and compile with checkpointer
workflow = create_workflow()
checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)


# =============================================================================
# Entrypoint
# =============================================================================

@entrypoint
def main(input: dict) -> dict:
    """
    Social Media Crew entrypoint.

    Args:
        input: Dictionary with:
            - topic: The topic for the social media content (required)
            - platform: Target platform - twitter, instagram, linkedin (default: twitter)
            - content_type: Type of content - single_post, thread (default: thread)
            - brand_guidelines: Optional brand guidelines to follow
            - thread_id: Optional thread ID for conversation continuity

    Returns:
        Dictionary with final content, review, and generated image
    """
    topic = input.get("topic", "")
    platform = input.get("platform", "twitter")
    content_type = input.get("content_type", "thread")
    brand_guidelines = input.get("brand_guidelines")
    thread_id = input.get("thread_id")

    if not topic:
        return {
            "success": False,
            "error": "Topic is required. Please provide a topic for the social media content."
        }

    logger.info(f"Starting Social Media Crew for topic: {topic}")
    logger.info(f"Platform: {platform}, Content Type: {content_type}")

    config = {"configurable": {"thread_id": thread_id or "default"}}

    # Run the workflow
    initial_state = {
        "topic": topic,
        "platform": platform,
        "content_type": content_type,
        "brand_guidelines": brand_guidelines,
        "revision_count": 0
    }

    result = app.invoke(initial_state, config=config)

    # Format output
    final_content = result.get("final_content", {})

    if result.get("error") or final_content.get("error"):
        return {
            "success": False,
            "error": result.get("error") or final_content.get("error"),
            "partial_content": final_content.get("partial_content")
        }

    # Extract the formatted content
    content = final_content.get("content", {})
    review = final_content.get("review", {})
    image = final_content.get("image", {})

    output = {
        "success": True,
        "platform": platform,
        "content_type": content_type,
        "main_post": content.get("main_post", ""),
        "thread_posts": content.get("thread_posts", []),
        "hashtags": content.get("hashtags", []),
        "call_to_action": content.get("call_to_action", ""),
        "hook_used": content.get("hook_used", ""),
        "best_posting_time": content.get("best_posting_time", ""),
        "engagement_prediction": content.get("engagement_prediction", ""),
        "review": {
            "approved": review.get("approved", False),
            "quality_score": review.get("overall_quality", 0),
            "viral_potential": review.get("viral_potential", 0),
            "summary": review.get("summary", "")
        },
        "revisions_made": final_content.get("revisions_made", 0)
    }

    # Add image if generated
    if image and image.get("success"):
        image_design = final_content.get("image_design", {})
        output["image"] = {
            "url": image.get("image_url"),
            "prompt": image.get("prompt"),
            "art_style": image_design.get("art_style", "") if image_design else ""
        }
    elif image:
        output["image_error"] = image.get("error")

    return output


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = "AI in everyday life"

    result = main({
        "topic": topic,
        "platform": "twitter",
        "content_type": "thread"
    })

    print("\n" + "=" * 60)
    print("SOCIAL MEDIA CREW RESULT")
    print("=" * 60)

    if result.get("success"):
        print(f"\nPlatform: {result.get('platform')}")
        print(f"Content Type: {result.get('content_type')}")
        print(f"\n--- MAIN POST ---\n{result.get('main_post')}")

        if result.get("thread_posts"):
            print("\n--- THREAD ---")
            for post in result.get("thread_posts", []):
                print(f"\n[{post.get('post_number')}] {post.get('content')}")

        print(f"\nHashtags: {' '.join(result.get('hashtags', []))}")
        print(f"CTA: {result.get('call_to_action')}")
        print(f"\nBest Posting Time: {result.get('best_posting_time')}")
        print(f"Engagement Prediction: {result.get('engagement_prediction')}")

        review = result.get("review", {})
        print(f"\n--- REVIEW ---")
        print(f"Approved: {review.get('approved')}")
        print(f"Quality Score: {review.get('quality_score')}/10")
        print(f"Viral Potential: {review.get('viral_potential')}/10")

        if result.get("image"):
            print(f"\n--- IMAGE ---")
            print(f"URL: {result['image'].get('url')}")
            print(f"Style: {result['image'].get('art_style')}")
    else:
        print(f"\nError: {result.get('error')}")
