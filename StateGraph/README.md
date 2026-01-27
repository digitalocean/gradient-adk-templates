# StateGraph - LangGraph Fundamentals

A joke generator that demonstrates LangGraph basics: state management, conditional routing, and multi-step LLM chains. This is the recommended starting point for learning how to build agents with the Gradient Agent Development Kit (ADK).

## Use Case

Learn the fundamentals of LangGraph by building a simple multi-step workflow. This template shows how to chain LLM calls, implement conditional branching, and add quality gates - patterns used in every LangGraph agent.

**When to use this template:**
- You're new to LangGraph or the Gradient ADK
- You want to understand state management and routing
- You need a minimal example to build from

## Key Concepts

**LangGraph StateGraph** is the foundation for building agent workflows. You define a typed state object that flows through the graph, and each node is a function that reads the current state, performs some work (like calling an LLM), and returns updates to the state. This pattern makes complex multi-step agent logic easy to reason about and debug.

**Conditional edges** let you route the workflow based on state or logic. In this template, the agent checks if the joke has a good punchline before continuing, and routes to different nodes based on whether "spicy" mode is enabled. These branching patterns are essential for building agents that adapt their behavior to intermediate results.

## Architecture

```
                      ┌─────────┐
                      │  START  │
                      └────┬────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  generate_joke  │
                  │                 │
                  │  Creates initial│
                  │  joke draft     │
                  └────────┬────────┘
                           │
                    ┌──────┴──────┐
                    │             │
              (punchline      (punchline
                 pass)           fail)
                    │             │
                    ▼             ▼
             ┌────────────┐    ┌─────┐
             │spice_router│    │ END │
             └─────┬──────┘    └─────┘
                   │
            ┌──────┴──────┐
            │             │
        (spicy)      (not spicy)
            │             │
            ▼             │
    ┌───────────────┐     │
    │ add_spicy_note│     │
    │               │     │
    │ Extra sass    │     │
    └───────┬───────┘     │
            │             │
            └──────┬──────┘
                   │
                   ▼
          ┌──────────────┐
          │ improve_joke │
          │              │
          │ Enhance the  │
          │ humor        │
          └──────┬───────┘
                 │
                 ▼
          ┌──────────────┐
          │ polish_joke  │
          │              │
          │ Final edits  │
          │ and timing   │
          └──────┬───────┘
                 │
                 ▼
             ┌─────┐
             │ END │
             └─────┘
```

## Prerequisites

- Python 3.10+
- DigitalOcean account

### Getting API Keys

1. **DigitalOcean API Token**:
   - Go to [API Settings](https://cloud.digitalocean.com/account/api/tokens)
   - Generate a new token with read/write access

2. **DigitalOcean Inference Key**:
   - Go to [GenAI Settings](https://cloud.digitalocean.com/gen-ai)
   - Create or copy your inference key

## Setup

### 1. Create Virtual Environment

```bash
cd StateGraph
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
```

## Running Locally

### Start the Agent

```bash
export DIGITALOCEAN_API_TOKEN=your_token
gradient agent run
```

### Test with curl

**Basic request (uses default topic):**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{}'
```

**With a custom topic:**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "topic": "software engineers"
    }'
```

**Force spicy mode:**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "topic": "remote work",
        "spicy": true
    }'
```

## Deployment

### 1. Configure Agent Name

Edit `.gradient/agent.yml`:

```yaml
agent_name: my-joke-generator
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
        "topic": "cloud computing"
    }'
```

## Sample Input/Output

### Input

```json
{
    "topic": "machine learning",
    "spicy": false
}
```

### Output

```json
{
    "joke": "Why did the neural network break up with the decision tree? Because it found someone with deeper layers and better connections. The decision tree saw it coming from a mile away - after all, it's great at making predictions, just not about its own love life."
}
```

### Spicy Mode Output

```json
{
    "joke": "Why did the neural network ghost the decision tree? Because it realized it could do better with literally any architecture that wasn't stuck in the 1980s. The decision tree didn't even see it coming - which is ironic, given that 'seeing things coming' is literally its only job."
}
```

## Project Structure

```
StateGraph/
├── .gradient/
│   └── agent.yml          # Deployment configuration
├── main.py                 # Complete LangGraph workflow
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
└── README.md
```

## Code Walkthrough

### Defining State

```python
from typing_extensions import TypedDict

class JokeState(TypedDict):
    topic: str
    joke: str
    spicy: bool
```

### Creating Nodes

```python
def generate_joke(state: JokeState) -> dict:
    """Generate an initial joke about the topic."""
    response = model.invoke(f"Write a joke about {state['topic']}")
    return {"joke": response.content}
```

### Conditional Routing

```python
def spice_router(state: JokeState) -> str:
    """Route based on whether joke should be spicy."""
    if state.get("spicy") or "spicy" in state["topic"].lower():
        return "add_spicy_note"
    return "improve_joke"
```

### Building the Graph

```python
from langgraph.graph import StateGraph, START, END

workflow = StateGraph(JokeState)

# Add nodes
workflow.add_node("generate_joke", generate_joke)
workflow.add_node("add_spicy_note", add_spicy_note)
workflow.add_node("improve_joke", improve_joke)
workflow.add_node("polish_joke", polish_joke)

# Add edges
workflow.add_edge(START, "generate_joke")
workflow.add_conditional_edges("generate_joke", punchline_check)
workflow.add_conditional_edges("generate_joke", spice_router)
workflow.add_edge("add_spicy_note", "improve_joke")
workflow.add_edge("improve_joke", "polish_joke")
workflow.add_edge("polish_joke", END)

# Compile
graph = workflow.compile()
```

## Customization

### Adding a New Node

Add a step that checks joke appropriateness:

```python
def check_appropriateness(state: JokeState) -> dict:
    """Ensure joke is workplace appropriate."""
    response = model.invoke(
        f"Review this joke for workplace appropriateness and "
        f"rewrite if needed: {state['joke']}"
    )
    return {"joke": response.content}

# Add to graph
workflow.add_node("check_appropriateness", check_appropriateness)
workflow.add_edge("polish_joke", "check_appropriateness")
workflow.add_edge("check_appropriateness", END)
```

### Changing the Quality Gate

Modify the punchline check criteria:

```python
def punchline_check(state: JokeState) -> str:
    """Check if joke has a strong punchline."""
    joke = state["joke"].lower()

    # Custom criteria
    has_setup = "?" in state["joke"] or "..." in state["joke"]
    has_punchline = len(state["joke"].split("\n")) >= 2

    if has_setup and has_punchline:
        return "continue"
    return "end"
```

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Tutorials](https://langchain-ai.github.io/langgraph/tutorials/)
- [Gradient ADK Documentation](https://docs.digitalocean.com/products/gradient/adk/)
