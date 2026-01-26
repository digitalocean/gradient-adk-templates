"""
Image Prompt Designer Agent - Creates simple, effective image prompts.

This agent analyzes the social media content and creates a concise image prompt
with a clear subject and appropriate art style.
"""

import os
import logging
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient

from agents.social_media_manager import OptimizedContent

logger = logging.getLogger(__name__)

# Model configuration
MODEL = "openai-gpt-4.1"


def get_model(temperature: float = 0.7) -> ChatGradient:
    """Get a ChatGradient instance."""
    return ChatGradient(
        model=MODEL,
        temperature=temperature
    )


class ImagePromptDesign(BaseModel):
    """Simple image prompt design."""
    subject: str = Field(description="What the image should show (1 sentence)")
    art_style: str = Field(description="Art style (e.g., 'digital illustration', 'minimalist', '3D render')")
    final_prompt: str = Field(description="The complete prompt (subject + style, under 50 words)")


def design_image_prompt(topic: str, platform: str) -> ImagePromptDesign:
    """
    Design a simple image prompt based on the topic.

    Args:
        topic: The main topic for the social media content
        platform: Target platform (twitter, instagram, linkedin)

    Returns:
        ImagePromptDesign with subject, style, and final prompt
    """
    logger.info(f"Designing image prompt for topic: {topic}")

    model = get_model(temperature=0.7)
    structured_model = model.with_structured_output(ImagePromptDesign)

    prompt = f"""Create a simple image prompt to visually represent this topic.

Topic: {topic}

Platform: {platform}

Rules:
- Describe ONE clear visual subject that represents the topic
- Pick ONE art style
- Keep the final prompt under 50 words
- NO text or words in the image
- Keep it simple and direct

Example good prompts:
- "A glowing brain made of circuit boards, digital illustration style"
- "Person working on laptop in cozy cafe, warm photography style"
- "Abstract waves of data flowing upward, minimalist vector art"
"""

    design = structured_model.invoke([
        {"role": "system", "content": "You create simple, clear image prompts. Be concise."},
        {"role": "user", "content": prompt}
    ])

    logger.info(f"Image prompt: {design.final_prompt}")
    return design


def compile_image_prompt(design: ImagePromptDesign) -> str:
    """
    Compile the design into the final prompt string.

    Args:
        design: The ImagePromptDesign

    Returns:
        Simple prompt string
    """
    return f"{design.final_prompt}. No text or words."
