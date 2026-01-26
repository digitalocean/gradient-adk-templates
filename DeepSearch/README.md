# DeepSearch Agent

A comprehensive research agent that conducts multi-step web research and produces detailed reports with citations. This agent features a human-in-the-loop planning phase where users can interactively refine the research plan through natural conversation before autonomous execution.

This is a LangGraph port of Google ADK's [DeepSearch agent](https://github.com/google/adk-samples/tree/main/python/agents/deep-search), adapted for the Gradient ADK platform with Serper for web search.

## Overview

The DeepSearch agent operates in two phases:

### Phase 1: Plan & Refine (Human-in-the-Loop)

1. **Generate Plan**: Agent creates a research plan with specific goals tagged as `[RESEARCH]` or `[DELIVERABLE]`
2. **User Review**: Plan is presented to user for approval
3. **Natural Conversation**: User responds naturally - the agent interprets intent:
   - "Looks good, let's proceed" → Approve and start research
   - "Add more focus on X" → Refine the plan
   - "What about Y?" → Address question and update plan
4. **Iterate**: Continue refining until user approves

**Nothing proceeds without explicit user approval.**

### Phase 2: Autonomous Research Pipeline (Parallel Execution)

1. **Section Planning**: Converts approved plan into report sections with search queries
2. **Parallel Section Research**: ALL sections are researched simultaneously using LangGraph's Send API:
   - Fan-out: Each section dispatched as independent parallel task
   - Execute search queries via Serper API
   - Analyze and synthesize findings concurrently
   - Fan-in: Results automatically collected via reducer
3. **Consolidation**: Aggregate all parallel results and sources
4. **Report Composition**: Synthesize all findings into a well-cited markdown report

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: PLANNING                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌─────────────┐    ┌──────────────┐               │
│  │ Generate     │───▶│   Human     │───▶│   Refine     │               │
│  │ Plan         │    │   Review    │    │   Plan       │               │
│  └──────────────┘    └──────┬──────┘    └──────┬───────┘               │
│                             │                   │                       │
│                     approve │                   │ feedback              │
│                             ▼                   ▼                       │
│                      ┌──────────────────────────┐                       │
│                      │     (loop until approve) │                       │
│                      └──────────────────────────┘                       │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│               PHASE 2: PARALLEL RESEARCH PIPELINE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐         FAN-OUT (Send API)                           │
│  │    Plan      │    ┌─────────────────────────┐                       │
│  │   Sections   │───▶│  ┌─────┐ ┌─────┐ ┌─────┐│                       │
│  └──────────────┘    │  │ S1  │ │ S2  │ │ S3  ││  (parallel)           │
│                      │  └──┬──┘ └──┬──┘ └──┬──┘│                       │
│                      └─────┼───────┼───────┼───┘                       │
│                            │       │       │                            │
│                            ▼       ▼       ▼     FAN-IN (reducer)      │
│                      ┌─────────────────────────┐                       │
│                      │     Consolidate         │                       │
│                      │     Research            │                       │
│                      └───────────┬─────────────┘                       │
│                                  │                                      │
│                                  ▼                                      │
│                      ┌──────────────┐                                   │
│                      │   Compose    │                                   │
│                      │   Report     │                                   │
│                      └──────────────┘                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Simple interface** - just `message` and optional `thread_id`, agent interprets intent
- **Human-in-the-loop planning** using LangGraph interrupts
- **Parallel section research** using LangGraph Send API for concurrent execution
- **Automatic result aggregation** via Annotated reducers (operator.add)
- **Comprehensive logging** for visibility into agent progress
- **State persistence** via thread_id for multi-turn interactions
- **Citation tracking** with source attribution in final reports

## Quickstart

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `DIGITALOCEAN_API_TOKEN`: Your DigitalOcean API token (for deployment)
- `DIGITALOCEAN_INFERENCE_KEY`: Your DigitalOcean inference key (for LLM inference)
- `SERPER_API_KEY`: Your Serper API key (for web search) - Get one at [serper.dev](https://serper.dev)

### 4. Run locally

```bash
export DIGITALOCEAN_API_TOKEN=<your-token>
gradient agent run
```

### 5. Interactive Usage

The agent uses a simple, consistent interface:

#### Start New Research

```bash
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Recent advances in quantum computing and their practical applications"
  }'
```

Or with your own thread_id:

```bash
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Recent advances in quantum computing and their practical applications",
    "thread_id": "my-research-123"
  }'
```

**Response:**
```json
{
  "thread_id": "abc12345",
  "phase": "planning",
  "status": "Plan generated. Awaiting user approval.",
  "plan": "## Research Plan: Recent advances in quantum computing...\n\n**1. [RESEARCH] Identify current quantum computing hardware developments**\n...",
  "awaiting_input": true
}
```

#### Continue the Conversation

Use the `thread_id` from the previous response and send your message naturally:

**To approve the plan:**
```bash
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "abc12345",
    "message": "Looks good, let'\''s proceed with the research"
  }'
```

**To request changes:**
```bash
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "abc12345",
    "message": "Can you add more focus on quantum error correction? Also remove the section about quantum supremacy."
  }'
```

**To ask a question:**
```bash
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "abc12345",
    "message": "Why did you include a section on quantum cryptography?"
  }'
```

The agent interprets your natural language to determine whether you want to:
- **Approve**: "yes", "looks good", "proceed", "let's go", "start the research"
- **Refine**: "add X", "remove Y", "change Z", "more focus on...", "can you also..."
- **Question**: Any question about the plan or process

#### Final Response

When research is complete:

```json
{
  "thread_id": "abc12345",
  "phase": "complete",
  "status": "Research complete!",
  "report": "# Quantum Computing: Recent Advances and Applications\n\n## Introduction\n...",
  "sources": [
    "https://example.com/quantum-article-1",
    "https://example.com/quantum-article-2"
  ],
  "awaiting_input": false
}
```

## API Reference

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | Your input (research topic to start, or response to continue) |
| `thread_id` | string | No | Session ID (optional for new, required for continuing) |
| `max_section_iterations` | integer | No | Max evaluation iterations per section (default: 2) |

If `thread_id` is not provided or doesn't exist, `message` is treated as a new research topic.
If `thread_id` exists with an active session, `message` is your response (approve/refine).

### Output Fields

| Field | Description |
|-------|-------------|
| `thread_id` | Session ID for continuing the conversation |
| `phase` | Current workflow phase: "planning", "researching", "composing", "complete" |
| `status` | Human-readable status message |
| `plan` | Research plan (during planning phase) |
| `report` | Final markdown report (when phase="complete") |
| `sources` | List of source URLs used |
| `awaiting_input` | True if waiting for user response |

## Logging

The agent includes comprehensive logging to track progress:

```
2024-01-15 10:30:00 - DeepSearch - INFO - ============================================================
2024-01-15 10:30:00 - DeepSearch - INFO - PHASE 1: PLANNING
2024-01-15 10:30:00 - DeepSearch - INFO - ============================================================
2024-01-15 10:30:00 - DeepSearch - INFO - Generating initial plan for: quantum computing
2024-01-15 10:30:05 - DeepSearch - INFO - Plan iteration 1 ready for review
...
2024-01-15 10:30:15 - DeepSearch - INFO - Received user message: looks good, proceed
2024-01-15 10:30:16 - DeepSearch - INFO - Classified intent: approve - User explicitly wants to proceed
2024-01-15 10:30:16 - DeepSearch - INFO - Plan APPROVED by user
...
2024-01-15 10:31:00 - DeepSearch - INFO - ============================================================
2024-01-15 10:31:00 - DeepSearch - INFO - PHASE 2: PARALLEL RESEARCH PIPELINE
2024-01-15 10:31:00 - DeepSearch - INFO - ============================================================
2024-01-15 10:31:00 - DeepSearch - INFO - Dispatching 4 sections for parallel research...
2024-01-15 10:31:00 - DeepSearch - INFO -   -> Section 1: Current Hardware Developments
2024-01-15 10:31:00 - DeepSearch - INFO -   -> Section 2: Quantum Algorithms
2024-01-15 10:31:00 - DeepSearch - INFO -   -> Section 3: Practical Applications
2024-01-15 10:31:00 - DeepSearch - INFO -   -> Section 4: Future Outlook
2024-01-15 10:31:01 - DeepSearch - INFO - [Section 1] Researching: Current Hardware Developments
2024-01-15 10:31:01 - DeepSearch - INFO - [Section 2] Researching: Quantum Algorithms
2024-01-15 10:31:01 - DeepSearch - INFO - [Section 3] Researching: Practical Applications
2024-01-15 10:31:01 - DeepSearch - INFO - [Section 4] Researching: Future Outlook
...
2024-01-15 10:31:30 - DeepSearch - INFO - ============================================================
2024-01-15 10:31:30 - DeepSearch - INFO - CONSOLIDATING PARALLEL RESEARCH RESULTS
2024-01-15 10:31:30 - DeepSearch - INFO - ============================================================
2024-01-15 10:31:30 - DeepSearch - INFO - Received results from 4 sections
2024-01-15 10:31:30 - DeepSearch - INFO - Total findings: 48
2024-01-15 10:31:30 - DeepSearch - INFO - Total sources: 32
2024-01-15 10:31:30 - DeepSearch - INFO - Average quality: 7.5/10
```

## Deployment

### Update agent configuration

Edit `.gradient/agent.yml` to customize your agent name:

```yaml
agent_environment: main
agent_name: my-deep-search-agent
entrypoint_file: main.py
```

### Deploy to Gradient

```bash
gradient agent deploy
```

### Invoke deployed agent

```bash
# Start research
curl -X POST 'https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <DIGITALOCEAN_API_TOKEN>" \
  -d '{"message": "Climate change mitigation strategies"}'

# Continue conversation (using thread_id from previous response)
curl -X POST 'https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <DIGITALOCEAN_API_TOKEN>" \
  -d '{"thread_id": "abc12345", "message": "Looks good, start the research"}'
```

## Project Structure

```
DeepSearch/
├── .gradient/
│   └── agent.yml              # Agent configuration
├── agents/
│   ├── __init__.py
│   ├── planner.py             # Research plan generation & refinement
│   ├── section_planner.py     # Convert plan to report sections
│   ├── researcher.py          # Section-based web research
│   ├── evaluator.py           # Research quality evaluation
│   └── composer.py            # Final report composition
├── tools/
│   ├── __init__.py
│   └── serper_search.py       # Serper web search integration
├── main.py                    # LangGraph workflow with interrupts
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Customization

### Adjusting Research Depth

Control how many times the evaluator can request more research per section:

```json
{
  "topic": "Your topic",
  "max_section_iterations": 3
}
```

### Modifying Prompts

The agent prompts are defined in each agent module:
- `agents/planner.py`: `PLAN_GENERATOR_PROMPT`, `PLAN_REFINEMENT_PROMPT`
- `agents/section_planner.py`: `SECTION_PLANNER_PROMPT`
- `agents/researcher.py`: `RESEARCHER_PROMPT`
- `agents/evaluator.py`: `SECTION_EVALUATOR_PROMPT`
- `agents/composer.py`: `COMPOSER_PROMPT`
- `main.py`: Intent classification prompt in `classify_user_intent()`

### Changing Models

By default, the agent uses `openai-gpt-4.1` via DigitalOcean's inference endpoint. To change models, modify the `ChatOpenAI` initialization in each agent module.

## State Management

The agent uses LangGraph's `MemorySaver` checkpointer to persist state across requests. This enables:

- Multi-turn planning conversations
- Session recovery (using the same `thread_id`)
- Progress tracking during long-running research

**Note:** The default `MemorySaver` is in-memory and state is lost when the agent restarts. For production deployments, consider using a persistent checkpointer like `SqliteSaver` or `PostgresSaver`.

## Credits

This agent is a LangGraph port of Google's [ADK DeepSearch agent](https://github.com/google/adk-samples/tree/main/python/agents/deep-search), adapted for the Gradient ADK platform with Serper for web search.
