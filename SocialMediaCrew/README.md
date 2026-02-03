# SocialMediaCrew - Multi-Agent Workflows with Image Generation

A complete social media content creation system with five specialized agents that research trends, write posts, optimize for platforms, review quality, and generate images. Built with LangGraph for workflow orchestration on the DigitalOcean Gradient AI Platform.

## Use Case

Automate social media content creation with AI. This template demonstrates a production-ready multi-agent pipeline that produces platform-optimized posts with AI-generated images, complete with revision loops and quality control.

**When to use this template:**
- You're building content generation pipelines
- You need multi-agent workflows with feedback loops
- You want to integrate image generation into agent workflows

## Key Concepts

**Multi-agent workflows** allow you to break complex tasks into specialized steps, each handled by a focused agent. This template uses five agents in sequence: a Researcher gathers trending topics, a Copywriter drafts content, a Social Media Manager optimizes for the target platform, a Reviewer scores quality and requests revisions if needed, and an Image Prompt Designer creates prompts for visual content.

**Image generation** on the Gradient AI Platform uses DigitalOcean's Serverless Inference. The template shows how to call image models (like fal fast-sdxl) from within your agent workflow, allowing you to produce complete posts with accompanying visuals in a single pipeline run.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Social Media Crew Pipeline                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Input: { topic, platform, content_type }                               │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │   Researcher    │◄────▶ Serper Web Search                           │
│  │                 │                                                    │
│  │ - Trend research│                                                    │
│  │ - Key insights  │                                                    │
│  │ - Viral hooks   │                                                    │
│  └────────┬────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │   Copywriter    │◄────────────────────────────┐                      │
│  │                 │                             │                      │
│  │ - Draft content │                             │ revision             │
│  │ - Hooks & CTAs  │                             │ feedback             │
│  └────────┬────────┘                             │                      │
│           │                                      │                      │
│           ▼                                      │                      │
│  ┌─────────────────┐                             │                      │
│  │ Social Media    │                             │                      │
│  │ Manager         │                             │                      │
│  │                 │                             │                      │
│  │ - Platform fit  │                             │                      │
│  │ - Optimization  │                             │                      │
│  └────────┬────────┘                             │                      │
│           │                                      │                      │
│           ▼                                      │                      │
│  ┌─────────────────┐                             │                      │
│  │    Reviewer     │─────────────────────────────┘                      │
│  │                 │      (if not approved)                             │
│  │ - Quality score │                                                    │
│  │ - Brand safety  │                                                    │
│  │ - Viral check   │                                                    │
│  └────────┬────────┘                                                    │
│           │ (approved)                                                  │
│           ▼                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                             │
│  │ Image Prompt    │──▶│ Image Generator │                             │
│  │ Designer        │    │                 │                             │
│  │                 │    │ fal fast-sdxl   │                             │
│  │ - Art direction │    │ via Gradient    │                             │
│  └─────────────────┘    └────────┬────────┘                             │
│                                  │                                      │
│                                  ▼                                      │
│  Output: { post, hashtags, image, metrics }                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- DigitalOcean account
- Serper API key ([get one free](https://serper.dev/api-keys))

### Getting API Keys

1. **DigitalOcean API Token**:
   - Go to [API Settings](https://cloud.digitalocean.com/account/api/tokens)
   - Generate a new token with read/write access

2. **DigitalOcean Inference Key**:
   - Go to [GenAI Settings](https://cloud.digitalocean.com/gen-ai)
   - Create or copy your inference key
   - Used for both LLM and image generation

3. **Serper API Key**:
   - Sign up at [serper.dev](https://serper.dev)
   - Get your free API key from the dashboard

## Setup

### 1. Create Virtual Environment

```bash
cd SocialMediaCrew
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```
DIGITALOCEAN_INFERENCE_KEY=your_inference_key
SERPER_API_KEY=your_serper_key
```

## Running Locally

### Start the Agent

```bash
export DIGITALOCEAN_API_TOKEN=your_token
gradient agent run
```

### Test with curl

**Create a Twitter thread:**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "topic": "AI productivity tools for developers",
        "platform": "twitter",
        "content_type": "thread"
    }'
```

**Create an Instagram post:**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "topic": "sustainable living tips",
        "platform": "instagram",
        "content_type": "single_post"
    }'
```

**With brand guidelines:**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "topic": "cloud computing benefits",
        "platform": "linkedin",
        "content_type": "single_post",
        "brand_guidelines": "Professional tone, avoid jargon, focus on business value"
    }'
```

## Deployment

### 1. Configure Agent Name

Edit `.gradient/agent.yml`:

```yaml
agent_name: my-social-media-crew
```

### 2. Deploy

```bash
gradient agent deploy
```

### 3. Invoke Deployed Agent

```bash
curl --location 'https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer <DIGITALOCEAN_API_TOKEN>' \
    --data '{
        "topic": "AI productivity tools",
        "platform": "twitter",
        "content_type": "thread"
    }'
```

## Sample Input/Output

### Input

```json
{
    "topic": "remote work productivity",
    "platform": "twitter",
    "content_type": "thread"
}
```

### Output

```json
{
    "success": true,
    "platform": "twitter",
    "content_type": "thread",
    "main_post": "I've worked remotely for 5 years. Here's what actually moves the needle on productivity (not what you'd expect):",
    "thread_posts": [
        {
            "post_number": 2,
            "content": "1/ Your environment matters more than your tools.\n\nI tried every app and system. Nothing worked until I fixed my workspace.\n\nDedicated desk + natural light + noise-canceling headphones = 3x output."
        },
        {
            "post_number": 3,
            "content": "2/ The 'fake commute' hack changed everything.\n\n15-minute walk before work. Brain shifts into work mode.\n\nNo walk = I'm checking Slack in my pajamas at 11pm."
        }
    ],
    "hashtags": ["#RemoteWork", "#Productivity", "#WFH"],
    "call_to_action": "What's your top remote work hack? Reply below",
    "best_posting_time": "Tuesday 9-11 AM EST",
    "engagement_prediction": "High",
    "review": {
        "approved": true,
        "quality_score": 8,
        "viral_potential": 7,
        "brand_safe": true,
        "summary": "Strong hook with personal credibility, actionable tips"
    },
    "image": {
        "url": "https://.......", // Images generated with fal are available at a URL
        "prompt": "minimalist home office with laptop and coffee, morning sunlight, clean aesthetic",
        "art_style": "digital illustration"
    }
}
```

## Project Structure

```
SocialMediaCrew/
├── .gradient/
│   └── agent.yml              # Deployment configuration
├── agents/
│   ├── __init__.py
│   ├── researcher.py          # Trend research and insights
│   ├── copywriter.py          # Content creation and revision
│   ├── social_media_manager.py # Platform optimization
│   ├── reviewer.py            # Quality control
│   └── image_prompt_designer.py # AI art direction
├── tools/
│   ├── __init__.py
│   ├── image_generator.py     # fal fast-sdxl integration
│   └── web_search.py          # Serper API search
├── main.py                     # LangGraph workflow
├── prompts.py                  # All agent prompts (edit this to customize!)
├── requirements.txt
├── .env.example
└── README.md
```

## Agents

### Researcher
Searches the web for trending topics, statistics, and insights. Identifies viral hooks and angles for the content.

### Copywriter
Creates the initial content draft, including hooks, body, and call-to-action. Handles revisions based on reviewer feedback.

### Social Media Manager
Optimizes content for the target platform. Adjusts length, tone, hashtags, and formatting.

### Reviewer
Scores content on quality (1-10), checks brand safety, and assesses viral potential. Approves or returns with feedback.

### Image Prompt Designer
Analyzes the approved content and creates a focused image prompt with subject and art style.

## Customization

### Customizing the Prompts

The easiest way to adapt this template is by editing **`prompts.py`**. This file contains all the prompts used by the five agents, plus platform guidelines and best practices.

**Key prompts you can customize:**

| Prompt/Function | Agent | Purpose |
|----------------|-------|---------|
| `get_research_prompt()` | Researcher | How to synthesize research |
| `get_content_creation_prompt()` | Copywriter | Content creation guidelines |
| `get_revision_prompt()` | Copywriter | How to handle revisions |
| `get_optimization_prompt()` | Social Media Manager | Optimization criteria |
| `get_review_prompt()` | Reviewer | Review criteria and thresholds |
| `get_image_prompt_design()` | Image Designer | Image prompt generation |
| `TWITTER_GUIDELINES` | Copywriter | Platform-specific rules |
| `TWITTER_BEST_PRACTICES` | Social Media Manager | Platform best practices |

**Example: Change Brand Voice**

```python
# In prompts.py, modify get_copywriter_system:
def get_copywriter_system(platform: str) -> str:
    return f"""You are a {platform} content creator for a tech startup.
Your voice is:
- Casual and friendly, but smart
- Uses tech analogies and references
- Never corporate or salesy
- Occasionally self-deprecating
- Loves a good pun"""
```

**Example: Stricter Review Criteria**

```python
# In prompts.py, modify get_review_prompt to add criteria:
def get_review_prompt(platform: str, content_text: str, ...) -> str:
    return f"""...
**Additional Review Criteria for Our Brand:**
- Must include at least one data point or statistic
- No competitors mentioned by name
- CTA must be soft (no hard sell)
- Must align with our values: innovation, accessibility, sustainability
..."""
```

**Example: Add TikTok Support**

```python
# In prompts.py, add new guidelines:
TIKTOK_GUIDELINES = """
- Hook must land in first 3 seconds
- Keep text concise - users are watching, not reading
- Reference trending sounds where applicable
- Include a "call to duet" or "call to stitch" CTA
- End with a question to drive comments
"""

TIKTOK_BEST_PRACTICES = """
- Most viral length: 15-60 seconds
- Use trending hashtags sparingly (2-3 max)
- Personal stories outperform polished content
- Behind-the-scenes performs well
- Educational content with a twist works great
"""

# Then update get_platform_guidelines and get_platform_best_practices
```

### Adding a New Platform

Edit `agents/social_media_manager.py`:

```python
PLATFORM_GUIDELINES = {
    "twitter": {...},
    "instagram": {...},
    "linkedin": {...},
    # Add TikTok
    "tiktok": {
        "max_length": 150,
        "tone": "casual, trendy",
        "hashtag_count": "3-5",
        "best_practices": [
            "Start with a hook in first 3 seconds",
            "Use trending sounds reference",
            "End with a question or CTA"
        ]
    }
}
```

### Changing the Image Model

Edit `tools/image_generator.py`:

```python
MODEL_ID = "fal-ai/flux/schnell",  # Use a different image generation model
```

### Disabling Image Generation

Skip image generation for text-only output:

```python
# In main.py, modify the workflow
workflow.add_conditional_edges(
    "reviewer",
    lambda state: "end" if state["skip_image"] else "image_prompt_designer"
)
```

## Workflow Details

### Revision Loop

1. Copywriter creates initial draft
2. Social Media Manager optimizes
3. Reviewer evaluates (score 1-10)
4. If score < 7: return to Copywriter with feedback
5. If score >= 7: proceed to image generation
6. Maximum 3 revisions before forcing approval

### Platform-Specific Optimization

| Platform | Post Length | Hashtags | Tone |
|----------|-------------|----------|------|
| Twitter | 280 chars/tweet | 1-2 | Casual, punchy |
| Instagram | 2,200 chars | 5-10 | Visual, lifestyle |
| LinkedIn | 3,000 chars | 3-5 | Professional |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Image generation fails | Check `DIGITALOCEAN_INFERENCE_KEY` has GenAI access |
| Serper search returns empty | Verify API key and check rate limits |
| Content stuck in revision loop | Increase `max_revisions` or lower quality threshold |
| Slow responses | Normal for multi-agent workflows (30-60s) |

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Serper API Documentation](https://serper.dev/docs)
- [DigitalOcean GenAI Serverless](https://docs.digitalocean.com/products/genai/how-to/inference/)
- [Gradient ADK Documentation](https://docs.digitalocean.com/products/gradient/adk/)
