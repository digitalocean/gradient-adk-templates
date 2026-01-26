"""
Image Generation Tool using fal's fast-sdxl model.

Generates images via DigitalOcean's Serverless Inference API.
"""

import os
import time
import logging
import requests
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# API Configuration
INFERENCE_API_URL = "https://inference.do-ai.run/v1"
MODEL_ID = "fal-ai/fast-sdxl"


class ImageGenerationResult(BaseModel):
    """Result of image generation."""
    success: bool
    image_url: Optional[str] = None
    error: Optional[str] = None
    prompt: str = ""


def get_api_key() -> str:
    """Get the Gradient Model Access Key."""
    key = os.environ.get("GRADIENT_MODEL_ACCESS_KEY")
    if not key:
        raise ValueError("GRADIENT_MODEL_ACCESS_KEY environment variable not set")
    return key


def generate_image(
    prompt: str,
    output_format: str = "square",
    num_inference_steps: int = 4,
    guidance_scale: float = 3.5,
    enable_safety_checker: bool = True,
    timeout: int = 120
) -> ImageGenerationResult:
    """
    Generate an image using fal's fast-sdxl model.

    Args:
        prompt: Text description of the image to generate
        output_format: Aspect ratio - "square", "landscape_4_3", "portrait_3_4", etc.
        num_inference_steps: Number of processing iterations (default: 4)
        guidance_scale: How closely to follow the prompt (default: 3.5)
        enable_safety_checker: Enable content filtering (default: True)
        timeout: Maximum time to wait for result in seconds

    Returns:
        ImageGenerationResult with image URL or error
    """
    logger.info(f"Generating image for prompt: {prompt[:100]}...")

    try:
        api_key = get_api_key()
    except ValueError as e:
        return ImageGenerationResult(success=False, error=str(e), prompt=prompt)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Submit async image generation request
    payload = {
        "model_id": MODEL_ID,
        "input": {
            "prompt": prompt,
            "output_format": output_format,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "num_images": 1,
            "enable_safety_checker": enable_safety_checker
        },
        "tags": [
            {"key": "type", "value": "social-media-crew"}
        ]
    }

    try:
        # Submit the async request
        response = requests.post(
            f"{INFERENCE_API_URL}/async-invoke",
            headers=headers,
            json=payload,
            timeout=30
        )
        if response.status_code != 200 and response.status_code != 202:
            logger.error(f"Image generation request failed: {response.status_code}")
            return ImageGenerationResult(
                success=False,
                error=f"API error: {response.status_code} - {response.text}",
                prompt=prompt
            )

        result = response.json()
        request_id = result.get("request_id") or result.get("id")

        if not request_id:
            # Check if we got a synchronous response with the image
            if "images" in result or "output" in result:
                images = result.get("images") or result.get("output", {}).get("images", [])
                if images:
                    image_url = images[0].get("url") if isinstance(images[0], dict) else images[0]
                    logger.info(f"Image generated successfully: {image_url}")
                    return ImageGenerationResult(
                        success=True,
                        image_url=image_url,
                        prompt=prompt
                    )

            logger.error(f"No request ID in response: {result}")
            return ImageGenerationResult(
                success=False,
                error="No request ID returned from API",
                prompt=prompt
            )

        logger.info(f"Image generation submitted, request_id: {request_id}")

        # Poll for completion
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_response = requests.get(
                f"{INFERENCE_API_URL}/async-invoke/{request_id}/status",
                headers=headers,
                timeout=30
            )

            if status_response.status_code != 200:
                logger.warning(f"Status check failed: {status_response.status_code}")
                time.sleep(2)
                continue

            status_result = status_response.json()
            status = status_result.get("status", "").lower()

            if status == "completed" or status == "succeeded":
                # Extract image URL from result
                output = status_result.get("output", {})
                images = output.get("images", [])

                if images:
                    image_url = images[0].get("url") if isinstance(images[0], dict) else images[0]
                    logger.info(f"Image generated successfully: {image_url}")
                    return ImageGenerationResult(
                        success=True,
                        image_url=image_url,
                        prompt=prompt
                    )
                else:
                    return ImageGenerationResult(
                        success=False,
                        error="No images in response",
                        prompt=prompt
                    )

            elif status == "failed" or status == "error":
                error_msg = status_result.get("error", "Unknown error")
                logger.error(f"Image generation failed: {error_msg}")
                return ImageGenerationResult(
                    success=False,
                    error=error_msg,
                    prompt=prompt
                )

            # Still processing
            time.sleep(2)

        # Timeout
        logger.error("Image generation timed out")
        return ImageGenerationResult(
            success=False,
            error=f"Generation timed out after {timeout} seconds",
            prompt=prompt
        )

    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return ImageGenerationResult(
            success=False,
            error=f"Request failed: {str(e)}",
            prompt=prompt
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return ImageGenerationResult(
            success=False,
            error=f"Unexpected error: {str(e)}",
            prompt=prompt
        )


def create_social_media_image_prompt(
    topic: str,
    platform: str = "twitter",
    style: str = "modern and eye-catching"
) -> str:
    """
    Create an optimized prompt for social media image generation.

    Args:
        topic: The topic/theme of the social media post
        platform: Target platform (twitter, instagram, linkedin)
        style: Visual style description

    Returns:
        Optimized image generation prompt
    """
    platform_hints = {
        "twitter": "bold, attention-grabbing, suitable for a tweet",
        "instagram": "visually stunning, Instagram-worthy, high aesthetic appeal",
        "linkedin": "professional, business-appropriate, clean design"
    }

    hint = platform_hints.get(platform.lower(), platform_hints["twitter"])

    prompt = f"""A {style} digital illustration or graphic for social media about {topic}.
The image should be {hint}.
High quality, vibrant colors, professional design, no text or words in the image."""

    return prompt
