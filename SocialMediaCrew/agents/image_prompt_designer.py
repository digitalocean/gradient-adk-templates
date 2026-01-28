"""
Image Prompt Designer Agent - Creates simple, effective image prompts.

This agent analyzes the social media content and creates a concise image prompt
with a clear subject and appropriate art style.
"""

import os
import sys
import logging
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient

from agents.social_media_manager import OptimizedContent

# Import prompts from central prompts.py - edit that file to customize
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import (
    IMAGE_DESIGNER_SYSTEM,
    get_image_prompt_design,
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

    prompt = get_image_prompt_design(topic, platform)

    design = structured_model.invoke([
        {"role": "system", "content": IMAGE_DESIGNER_SYSTEM},
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
