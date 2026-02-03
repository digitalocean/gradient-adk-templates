# Crew - Using External Frameworks with Gradient ADK

A multi-agent system built with CrewAI that researches news and generates trivia facts. This template demonstrates that you can deploy agents built with **any Python framework** on the DigitalOcean Gradient AI Platform - not just LangGraph.

## Use Case

This template builds a trivia generator using CrewAI, but the key takeaway is **framework flexibility**. Whether you prefer CrewAI, AutoGen, or any other agent framework, the Gradient ADK lets you deploy it with the same simple workflow: wrap your logic in an `@entrypoint` function, and run `gradient agent deploy`.

**Template Highlights:**
- Deploy CrewAI agents (or any framework) on the Gradient AI Platform
- Use DigitalOcean's serverless inference as the LLM backend
- Combine framework-specific patterns with Gradient's deployment infrastructure
- Integrate external tools (Serper search) within your chosen framework

## Key Concepts

**Framework flexibility** is a core principle of the Gradient ADK. While many templates use LangGraph, the ADK doesn't require it. Any Python code that accepts input and returns output can become a deployed agent.

This template uses CrewAI's role-based agent pattern: a Researcher agent gathers information, then passes context to a Trivia Generator agent. CrewAI manages the agent coordination, while the Gradient ADK handles deployment, scaling, and infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Crew AI Workflow                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Input: { date, topic }                                 │
│           │                                             │
│           ▼                                             │
│  ┌─────────────────────┐                                │
│  │   News Researcher   │                                │
│  │                     │                                │
│  │  - Searches Google  │◄──── Serper API                │
│  │  - Finds articles   │                                │
│  │  - Extracts facts   │                                │
│  └──────────┬──────────┘                                │
│             │ context                                   │
│             ▼                                           │
│  ┌─────────────────────┐                                │
│  │  Trivia Generator   │                                │
│  │                     │                                │
│  │  - Reviews research │                                │
│  │  - Creates trivia   │                                │
│  │  - Adds sources     │                                │
│  └──────────┬──────────┘                                │
│             │                                           │
│             ▼                                           │
│  Output: 5 trivia facts with sources                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
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

3. **Serper API Key**:
   - Sign up at [serper.dev](https://serper.dev)
   - Get your free API key from the dashboard

## Setup

### 1. Create Virtual Environment

```bash
cd Crew
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

Edit `.env` with your credentials:

```
DIGITALOCEAN_INFERENCE_KEY=your_inference_key
SERPER_API_KEY=your_serper_key
```

## Running Locally

### Start the Agent

```bash
export DIGITALOCEAN_API_TOKEN=your_token  # On Windows: set DIGITALOCEAN_API_TOKEN=your_token
gradient agent run
```

### Test with curl

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "date": "16th November 2025",
        "topic": "AI Laws and Regulations"
    }'
```

## Deployment

### 1. Configure Agent Name

Edit `.gradient/agent.yml` to set your agent name:

```yaml
agent_name: my-trivia-crew
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
        "date": "16th November 2025",
        "topic": "AI Laws and Regulations"
    }'
```

## Sample Input/Output

### Input

```json
{
    "date": "16th November 2025",
    "topic": "AI Laws and Regulations"
}
```

### Output

```json
{
    "trivia_facts": [
        {
            "fact": "The EU AI Act, which came into full effect in 2025, categorizes AI systems into four risk levels: unacceptable, high, limited, and minimal risk.",
            "source": "https://example.com/eu-ai-act"
        },
        {
            "fact": "China's AI governance framework requires all generative AI services to register with the government before public release.",
            "source": "https://example.com/china-ai-rules"
        }
    ]
}
```

## Project Structure

```
Crew/
├── .gradient/
│   └── agent.yml          # Deployment configuration
├── main.py                 # CrewAI agents, tasks, and entry point
├── prompts.py              # All agent prompts (edit this to customize!)
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
└── README.md
```

## Customization

### Customizing Prompts

The easiest way to adapt this template is by editing **`prompts.py`**. This file contains all the agent roles, goals, backstories, and task descriptions in one place.

**Key prompts you can customize:**

| Variable | Purpose | Example Change |
|----------|---------|----------------|
| `RESEARCHER_ROLE` | Agent's role title | Change to "Sports Research Specialist" |
| `RESEARCHER_BACKSTORY` | Agent's persona/expertise | Adjust expertise area and tone |
| `get_researcher_goal()` | What the researcher should find | Focus on different content types |
| `TRIVIA_GENERATOR_ROLE` | Trivia agent's role | Change to "Quiz Question Creator" |
| `TRIVIA_GENERATOR_BACKSTORY` | Trivia agent's persona | Adjust for educational vs entertainment focus |
| `get_trivia_task_description()` | Output format and requirements | Change from trivia to flashcards or quiz |

**Example: Converting to a Quiz Generator**

```python
# In prompts.py, change:
TRIVIA_GENERATOR_ROLE = "Quiz Question Creator"

TRIVIA_GENERATOR_BACKSTORY = """You are an educational content creator who
specializes in creating multiple-choice quiz questions. You excel at
testing knowledge while making learning fun."""

def get_trivia_task_description(topic: str, date: str) -> str:
    return f"""Based on the news articles found, create 5 multiple-choice
quiz questions about {topic} from {date}.

Each question should:
- Have 4 answer options (A, B, C, D)
- Include the correct answer marked
- Test factual knowledge from the articles
- Be challenging but fair
"""
```

### Adding New Agents

Edit `main.py` to add agents to your crew:

```python
@agent
def fact_checker(self) -> Agent:
    return Agent(
        config=self.agents_config['fact_checker'],
        tools=[SerperDevTool()],
        verbose=True
    )
```

### Changing the Search Tool

Replace Serper with another search provider in `main.py`:

```python
from crewai_tools import DuckDuckGoSearchTool

# Use DuckDuckGo instead (no API key required)
tools=[DuckDuckGoSearchTool()]
```

### Modifying Task Flow

CrewAI supports different process types:

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.hierarchical,  # or Process.sequential
        verbose=True
    )
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Slow responses (30-40s) | Normal for multi-agent workflows with web search |
| Serper API errors | Verify your API key and check rate limits |
| Empty trivia results | Try a more specific date and topic combination |

## Notes

- Response times are typically 30-40 seconds due to multiple LLM calls and web searches
- Native trace viewing for CrewAI agents is not yet available on the Gradient AI Platform
- The Serper API has rate limits on the free tier

## Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [Serper API Documentation](https://serper.dev/docs)
- [Gradient ADK Documentation](https://docs.digitalocean.com/products/gradient/adk/)
