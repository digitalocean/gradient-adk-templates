# DeepSearch - Research Agent with Human-in-the-Loop

A comprehensive research agent that conducts multi-step web research and produces detailed reports with citations. Features human-in-the-loop plan approval and parallel section research using LangGraph's advanced features.

Based on [Google ADK's DeepSearch agent](https://github.com/google/adk-samples/tree/main/python/agents/deep-search), adapted for the DigitalOcean Gradient AI Platform with Serper for web search.

## Use Case

Build a research assistant that creates thorough, well-cited reports on any topic. The agent first generates a research plan for your approval, then executes parallel research across multiple sections before composing the final report.

**When to use this template:**
- You need comprehensive research with human oversight
- You're building workflows that require human-in-the-loop (HITL) interactions
- You need a reference for parallel task execution in LangGraph

## Key Concepts

**Human-in-the-loop (HITL)** workflows pause execution to get user input before proceeding. This template uses LangGraph's `interrupt()` function to present a research plan and wait for approval. The user can approve, request changes, or ask questions - and the agent interprets natural language responses to determine the next action. State persistence via `thread_id` allows the conversation to span multiple API calls.

**Parallel execution** dramatically speeds up research by processing multiple sections simultaneously. After the plan is approved, the agent uses LangGraph's `Send` API to dispatch research tasks for each section concurrently (fan-out). Results are automatically collected using annotated reducers (fan-in), then consolidated into the final report. This pattern is essential for any workflow where independent subtasks can run in parallel.

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: PLANNING (Human-in-the-Loop)               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Input: { message: "research topic", thread_id? }                      │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────┐                                                   │
│  │  Generate Plan  │                                                   │
│  │                 │                                                   │
│  │  Creates goals: │                                                   │
│  │  [RESEARCH] ... │                                                   │
│  │  [DELIVERABLE]  │                                                   │
│  └────────┬────────┘                                                   │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────┐         ┌─────────────────┐                       │
│  │  Human Review   │◄──────▶│   User Input    │                       │
│  │   (interrupt)   │         │                 │                       │
│  │                 │         │ "looks good" ───┼──▶ approve           │
│  │  Waits for      │         │ "add X" ────────┼──▶ refine            │
│  │  user response  │         │ "why Y?" ───────┼──▶ question          │
│  └────────┬────────┘         └─────────────────┘                       │
│           │                                                            │
│     (if refine)──────────────────────────┐                             │
│           │                              ▼                             │
│           │                     ┌─────────────────┐                    │
│           │                     │   Refine Plan   │                    │
│           │                     │                 │                    │
│           │                     │  Updates based  │                    │
│           │                     │  on feedback    │                    │
│           │                     └────────┬────────┘                    │
│           │                              │                             │
│           │◄─────────────────────────────┘                             │
│           │                                                            │
│     (if approved)                                                      │
│           │                                                            │
├───────────┼────────────────────────────────────────────────────────────┤
│           │           PHASE 2: PARALLEL RESEARCH                       │
├───────────┼────────────────────────────────────────────────────────────┤
│           ▼                                                            │
│  ┌─────────────────┐                                                   │
│  │  Plan Sections  │                                                   │
│  │                 │                                                   │
│  │  Converts plan  │                                                   │
│  │  to report      │                                                   │
│  │  sections       │                                                   │
│  └────────┬────────┘                                                   │
│           │                                                            │
│           ▼  FAN-OUT (Send API)                                        │
│  ┌───────────────────────────────────────────────┐                     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │                     │
│  │  │Section 1 │  │Section 2 │  │Section 3 │ ... │  (parallel)         │
│  │  │          │  │          │  │          │     │                     │
│  │  │ Search   │  │ Search   │  │ Search   │     │◄── Serper API       │
│  │  │ Analyze  │  │ Analyze  │  │ Analyze  │     │                     │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘     │                     │
│  │       │             │             │           │                     │
│  └───────┼─────────────┼─────────────┼───────────┘                     │
│          │             │             │                                 │
│          └─────────────┼─────────────┘                                 │
│                        │  FAN-IN (reducer)                             │
│                        ▼                                               │
│  ┌─────────────────────────────────────────────┐                       │
│  │           Consolidate Research              │                       │
│  │                                             │                       │
│  │  Aggregates all section results             │                       │
│  │  Collects sources for citations             │                       │
│  └────────────────────┬────────────────────────┘                       │
│                       │                                                │
│                       ▼                                                │
│  ┌─────────────────────────────────────────────┐                       │
│  │            Compose Report                   │                       │
│  │                                             │                       │
│  │  Synthesizes findings into markdown         │                       │
│  │  Adds citations and sources                 │                       │
│  └────────────────────┬────────────────────────┘                       │
│                       │                                                │
│                       ▼                                                │
│  Output: { report, sources, thread_id }                                │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
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
cd DeepSearch
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

### Interactive Usage

**Step 1: Start new research**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "message": "Recent advances in quantum computing and their practical applications"
    }'
```

Response:
```json
{
    "thread_id": "abc12345",
    "phase": "planning",
    "status": "Plan generated. Awaiting user approval.",
    "plan": "## Research Plan: Quantum Computing...\n\n**1. [RESEARCH] Current hardware developments**\n...",
    "awaiting_input": true
}
```

**Step 2: Approve or refine the plan**

To approve:
```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "thread_id": "abc12345",
        "message": "Looks good, proceed with the research"
    }'
```

To request changes:
```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "thread_id": "abc12345",
        "message": "Add more focus on quantum error correction and remove the section about quantum supremacy"
    }'
```

**Step 3: Get the final report**

After approval, the agent researches and returns:
```json
{
    "thread_id": "abc12345",
    "phase": "complete",
    "status": "Research complete!",
    "report": "# Quantum Computing: Recent Advances...\n\n## Introduction\n...",
    "sources": [
        "https://example.com/quantum-article-1",
        "https://example.com/quantum-article-2"
    ],
    "awaiting_input": false
}
```

## Deployment

### 1. Configure Agent Name

Edit `.gradient/agent.yml`:

```yaml
agent_name: my-deep-search-agent
```

### 2. Deploy

```bash
gradient agent deploy
```

### 3. Invoke Deployed Agent

```bash
# Start research
curl --location 'https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer <DIGITALOCEAN_API_TOKEN>' \
    --data '{
        "message": "Climate change mitigation strategies"
    }'

# Continue conversation
curl --location 'https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer <DIGITALOCEAN_API_TOKEN>' \
    --data '{
        "thread_id": "abc12345",
        "message": "Approved, start the research"
    }'
```

## Sample Input/Output

### Research Topic Input

```json
{
    "message": "The impact of AI on software development practices"
}
```

### Planning Phase Output

```json
{
    "thread_id": "d4f82a1b",
    "phase": "planning",
    "status": "Plan generated. Awaiting user approval.",
    "plan": "## Research Plan: AI Impact on Software Development\n\n**Summary:** This research will examine how AI tools are transforming coding practices, team dynamics, and software quality.\n\n### Goals:\n\n**1. [RESEARCH] Current AI coding assistants and their adoption rates**\n   Key questions:\n   - What are the leading AI coding tools?\n   - What is the adoption rate among developers?\n   - Which programming languages are best supported?\n\n**2. [RESEARCH] Impact on developer productivity**\n   Key questions:\n   - How much time do AI tools save?\n   - What tasks benefit most from AI assistance?\n   - Are there productivity drawbacks?\n\n**3. [DELIVERABLE] Best practices for AI-assisted development**\n   Key questions:\n   - How should teams integrate AI tools?\n   - What are the security considerations?\n   - How to maintain code quality with AI?\n",
    "awaiting_input": true
}
```

### Final Report Output

```json
{
    "thread_id": "d4f82a1b",
    "phase": "complete",
    "status": "Research complete!",
    "report": "# The Impact of AI on Software Development Practices\n\n## Executive Summary\n\nArtificial intelligence is fundamentally reshaping how software is written, reviewed, and maintained...\n\n## 1. Current AI Coding Assistants\n\nThe landscape of AI coding tools has expanded rapidly since 2022...\n\n[Citations: [1], [2], [3]]\n\n## Sources\n\n[1] https://example.com/ai-coding-tools-2024\n[2] https://example.com/developer-productivity-study\n...",
    "sources": [
        "https://example.com/ai-coding-tools-2024",
        "https://example.com/developer-productivity-study",
        "https://example.com/github-copilot-research"
    ],
    "awaiting_input": false
}
```

## Project Structure

```
DeepSearch/
├── .gradient/
│   └── agent.yml          # Deployment configuration
├── agents/
│   ├── __init__.py
│   ├── planner.py         # Research plan generation
│   ├── section_planner.py # Convert plan to sections
│   ├── researcher.py      # Section research (parallel)
│   ├── evaluator.py       # Quality assessment
│   └── composer.py        # Final report composition
├── tools/
│   ├── __init__.py
│   └── serper_search.py   # Web search integration
├── main.py                 # LangGraph workflow with interrupts
├── prompts.py              # All agent prompts (edit this to customize!)
├── requirements.txt
├── .env.example
└── README.md
```

## API Reference

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | Research topic (new) or response (continuing) |
| `thread_id` | string | No | Session ID for multi-turn conversations |
| `max_section_iterations` | integer | No | Max research iterations per section (default: 2) |

### Output Fields

| Field | Description |
|-------|-------------|
| `thread_id` | Session ID for continuing the conversation |
| `phase` | Current phase: `planning`, `researching`, `composing`, `complete` |
| `status` | Human-readable status message |
| `plan` | Research plan (during planning phase) |
| `report` | Final markdown report (when complete) |
| `sources` | List of source URLs used |
| `awaiting_input` | `true` if waiting for user response |

## User Intent Detection

The agent interprets natural language responses:

| Intent | Example Phrases |
|--------|-----------------|
| **Approve** | "looks good", "proceed", "yes", "let's go", "approved" |
| **Refine** | "add more about X", "remove Y", "focus on Z", "can you include" |
| **Question** | "why did you include X?", "what about Y?" |

## Customization

### Customizing the Prompts

The easiest way to adapt this template is by editing **`prompts.py`**. This file contains all the prompts used throughout the research pipeline.

**Key prompts you can customize:**

| Variable | Purpose | Example Change |
|----------|---------|----------------|
| `PLAN_GENERATOR_PROMPT` | Creates the initial research plan | Add required sections or methodology |
| `PLAN_REFINEMENT_PROMPT` | Refines plan based on feedback | Change how feedback is incorporated |
| `INTENT_CLASSIFICATION_PROMPT` | Interprets user responses | Add new intent categories |
| `get_section_analysis_prompt()` | Analyzes search results | Change synthesis requirements |
| `COMPOSER_PROMPT` | Composes the final report | Change format, style, or citation style |

**Example: Academic Research Style**

```python
# In prompts.py, modify PLAN_GENERATOR_PROMPT:
PLAN_GENERATOR_PROMPT = """You are an academic research planner creating a literature review structure.

For each goal, classify as:
- [LITERATURE] - Review of existing academic papers and studies
- [METHODOLOGY] - Research methodology to be applied
- [FINDINGS] - Expected findings or analysis sections
- [DISCUSSION] - Interpretation and implications

Research Topic: {topic}

Create an academic research plan with proper scholarly structure."""
```

**Example: Investigative Journalism Style**

```python
COMPOSER_PROMPT = """You are an investigative journalist writing a comprehensive report.

Requirements:
1. Lead with the most newsworthy finding
2. Include quotes and specific attributions
3. Present multiple perspectives on controversial points
4. Clearly distinguish between facts and analysis
5. End with implications and next steps

Research Topic: {topic}
..."""
```

**Example: Technical Documentation**

```python
COMPOSER_PROMPT = """You are a technical writer creating documentation.

Format requirements:
1. Start with an executive summary for non-technical readers
2. Include code examples or configurations where relevant
3. Add "Prerequisites" and "Next Steps" sections
4. Use tables for comparing options
5. Include troubleshooting guidance

Research Topic: {topic}
..."""
```

### Adjusting Research Depth

Control iterations per section:

```json
{
    "message": "Quantum computing advances",
    "max_section_iterations": 3
}
```

### Modifying the Planning Prompt

Edit `agents/planner.py`:

```python
PLAN_GENERATOR_PROMPT = """You are an expert research planner...

# Add custom instructions
Always include a section on:
- Historical context
- Current state of the art
- Future predictions

Research Topic: {topic}
"""
```

### Changing Search Parameters

Edit `tools/serper_search.py`:

```python
def serper_search(query: str, num_results: int = 10) -> SearchResults:
    # Increase results per query
    # Add date filtering
    params = {
        "q": query,
        "num": num_results,
        "tbs": "qdr:y"  # Last year only
    }
```

### Adding Custom Research Steps

Extend the workflow in `main.py`:

```python
# Add a fact-checking node
def fact_check_node(state: DeepSearchState) -> dict:
    """Verify key claims in the research."""
    # Fact-checking logic
    return {"fact_check_results": results}

workflow.add_node("fact_check", fact_check_node)
workflow.add_edge("consolidate_research", "fact_check")
workflow.add_edge("fact_check", "compose_report")
```

## State Persistence

The agent uses LangGraph's `MemorySaver` for state persistence:

- **In-memory by default**: State is lost when agent restarts
- **Production recommendation**: Use `PostgresSaver` or `SqliteSaver`

```python
from langgraph.checkpoint.postgres import PostgresSaver

# Replace MemorySaver with PostgresSaver
memory = PostgresSaver.from_conn_string(os.environ["DATABASE_URL"])
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Plan is empty" | Check `DIGITALOCEAN_INFERENCE_KEY` is valid |
| Serper errors | Verify `SERPER_API_KEY` and check rate limits |
| Thread not found | Ensure you're using the correct `thread_id` |
| Research takes too long | Reduce `max_section_iterations` |
| State lost on restart | Use a persistent checkpointer |

## Resources

- [LangGraph Human-in-the-Loop](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/)
- [LangGraph Send API](https://langchain-ai.github.io/langgraph/how-tos/map-reduce/)
- [Serper API Documentation](https://serper.dev/docs)
- [Google ADK DeepSearch](https://github.com/google/adk-samples/tree/main/python/agents/deep-search)
- [Gradient ADK Documentation](https://docs.digitalocean.com/products/gradient/adk/)
