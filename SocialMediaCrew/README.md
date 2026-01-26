# Social Media Crew

A multi-agent system that collaborates to create viral social media content. Built with LangGraph for workflow orchestration and deployed on DigitalOcean's Gradient platform.

## Overview

The Social Media Crew consists of four specialized AI agents that work together:

```
┌───────────────────────────────────────────────────────────────────┐
│                       Social Media Crew                           │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │  Researcher  │───>│  Copywriter  │───>│   Social     │        │
│  │              │    │              │    │   Media      │        │
│  │ - Trends     │    │ - Drafts     │    │   Manager    │        │
│  │ - Insights   │    │ - Hooks      │    │              │        │
│  │ - Facts      │    │ - CTAs       │    │ - Optimizes  │        │
│  └──────────────┘    └──────────────┘    └──────────────┘        │
│                                                 │                 │
│                                                 ▼                 │
│                                          ┌──────────────┐        │
│                                          │   Reviewer   │        │
│                                          │              │        │
│                                          │ - Quality    │        │
│                                          │ - Safety     │        │
│                                          │ - Feedback   │        │
│                                          └──────────────┘        │
│                                            │         │            │
│                                     Approved      Rejected        │
│                                            │         │            │
│                                            ▼         └──>(loop)   │
│  ┌──────────────┐    ┌──────────────────────────────────┐        │
│  │    Image     │<───│      Image Prompt Designer       │        │
│  │  Generator   │    │                                  │        │
│  │              │    │ - Analyzes content               │        │
│  │ fal fast-sdxl│    │ - Art style selection            │        │
│  └──────────────┘    │ - Color palette design           │        │
│         │            │ - Composition & mood             │        │
│         │            │ - Elements to include/exclude    │        │
│         ▼            └──────────────────────────────────┘        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                  Final Content Package                      │  │
│  │  - Optimized post/thread                                   │  │
│  │  - AI-designed image with full art direction               │  │
│  │  - Posting recommendations                                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Agents

### 1. Researcher
- Researches trending topics using web search
- Gathers facts, statistics, and insights
- Identifies viral hooks and angles
- Suggests hashtags and emotional triggers

### 2. Copywriter
- Creates engaging social media content
- Writes scroll-stopping hooks
- Crafts threads or single posts
- Handles revisions based on feedback

### 3. Social Media Manager
- Optimizes content for each platform
- Improves readability and engagement
- Suggests best posting times
- Predicts engagement levels

### 4. Reviewer
- Reviews content for quality (1-10 score)
- Checks brand safety
- Assesses viral potential
- Approves or provides revision feedback

### 5. Image Prompt Designer
- Analyzes content to determine what visual would work best
- Creates a simple, focused image subject
- Selects an appropriate art style

## Features

- **Multi-Platform Support**: Twitter/X, Instagram, LinkedIn
- **Content Types**: Single posts or threads
- **Image Generation**: Uses fal's fast-sdxl model
- **Quality Control**: Automatic review and revision loop
- **Brand Safety**: Content is checked for safety issues
- **Trending Research**: Web search for current trends

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `DIGITALOCEAN_INFERENCE_KEY`: Your Gradient model access key (for LLM and image generation)
- `SERPER_API_KEY`: Serper API key for web search

### 3. Deploy to Gradient

```bash
gradient-adk deploy
```

## Usage

### Basic Usage

```python
from main import main

result = main({
    "topic": "AI productivity tools",
    "platform": "twitter",
    "content_type": "thread"
})

print(result["main_post"])
print(result["image"]["url"])
```

### Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic` | string | required | Topic for the content |
| `platform` | string | "twitter" | Target platform: twitter, instagram, linkedin |
| `content_type` | string | "thread" | Content type: single_post, thread |
| `brand_guidelines` | string | None | Optional brand guidelines to follow |
| `thread_id` | string | None | Thread ID for conversation continuity |

### Output

```json
{
  "success": true,
  "platform": "twitter",
  "content_type": "thread",
  "main_post": "The hook that starts your thread...",
  "thread_posts": [
    {"post_number": 2, "content": "Second post..."},
    {"post_number": 3, "content": "Third post..."}
  ],
  "hashtags": ["#AI", "#Productivity"],
  "call_to_action": "Follow for more tips!",
  "hook_used": "Surprising statistic hook",
  "best_posting_time": "Tuesday 9-11 AM",
  "engagement_prediction": "High",
  "review": {
    "approved": true,
    "quality_score": 8,
    "viral_potential": 7,
    "summary": "Strong content with good hook..."
  },
  "image": {
    "url": "https://...",
    "prompt": "A glowing brain made of circuit boards, digital illustration style",
    "art_style": "digital illustration"
  }
}
```

## Example Topics

- "AI productivity tools for remote workers"
- "The future of electric vehicles"
- "Mental health tips for entrepreneurs"
- "Web3 and decentralized finance explained"
- "Sustainable living hacks"

## Workflow Details

### Revision Loop

If the Reviewer doesn't approve the content, it goes back to the Copywriter with specific feedback. This continues until:
- Content is approved
- Maximum revisions (3) are reached

### Image Generation

After content approval, the Image Prompt Designer agent analyzes the content and creates a simple, focused prompt with:
- A clear visual subject that represents the content
- An appropriate art style

The prompt is then used to generate an image via fal's fast-sdxl model on DigitalOcean's Serverless Inference API.

## Local Development

Run locally:

```bash
python main.py "Your topic here"
```

## Project Structure

```
SocialMediaCrew/
├── .gradient/
│   └── agent.yml          # Gradient agent configuration
├── agents/
│   ├── __init__.py
│   ├── researcher.py           # Trending topic research
│   ├── copywriter.py           # Content creation
│   ├── social_media_manager.py # Content optimization
│   ├── reviewer.py             # Quality control
│   └── image_prompt_designer.py # AI art direction for images
├── tools/
│   ├── __init__.py
│   ├── image_generator.py # fal fast-sdxl integration
│   └── web_search.py      # Serper API search
├── main.py                # LangGraph workflow
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Platform Guidelines

### Twitter/X
- First tweet hooks in <5 seconds
- Thread length: 5-10 tweets
- 1-2 relevant hashtags
- End with CTA (follow/retweet)

### Instagram
- First 125 characters show in preview
- Use emojis as visual breaks
- 5-10 targeted hashtags
- Strong save/share CTA

### LinkedIn
- First 2 lines are crucial
- Personal stories with lessons
- 3-5 hashtags max
- End with a question
