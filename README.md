# Gradient ADK Templates

Production-ready templates for building and deploying AI agents on the DigitalOcean Gradient AI Platform using the Agent Development Kit (ADK).

## What is Gradient ADK?

The Gradient Agent Development Kit (ADK) is DigitalOcean's framework for building, testing, and deploying AI agents. It provides:

- **Simple deployment**: Deploy agents with a single command using `gradient agent deploy`
- **Framework flexibility**: Build agents with LangGraph, CrewAI, or any Python framework
- **Managed infrastructure**: Automatic scaling, monitoring, and logging
- **Integrated inference**: Direct access to DigitalOcean GenAI Serverless Inference

## Templates

Each template demonstrates a specific agent architecture or capability. Choose based on your use case:

| Template | Use Case | Key Concepts | Complexity |
|----------|----------|--------------|------------|
| [StateGraph](./StateGraph/) | Learn LangGraph basics | Conditional routing, state management | Beginner |
| [WebSearch](./WebSearch/) | Simple tool-using agent | Tool binding, DuckDuckGo search | Beginner |
| [KnowledgeBaseRAG](./KnowledgeBaseRAG/) | Query DigitalOcean Knowledge Bases | Knowledge Base integration | Beginner |
| [RAG](./RAG/) | Document Q&A over PDFs | Multi-agent retrieval, query rewriting | Intermediate |
| [MCP](./MCP/) | Connect to external tools | Model Context Protocol, multi-tool agents | Intermediate |
| [Crew](./Crew/) | Multi-agent collaboration | CrewAI framework, sequential tasks | Intermediate |
| [SocialMediaCrew](./SocialMediaCrew/) | Content creation pipeline | Multi-agent workflow, image generation | Advanced |
| [DataScience](./DataScience/) | Natural language to SQL | Database queries, self-healing, visualization | Advanced |
| [DeepSearch](./DeepSearch/) | Multi-step research | Human-in-the-loop, parallel execution | Advanced |

## Quick Start

### Prerequisites

- Python 3.10+
- DigitalOcean account with API access
- [Gradient CLI](https://docs.digitalocean.com/products/gradient/) installed

### Installation

```bash
# Install the Gradient CLI
pip install gradient-adk

# Clone this repository
git clone https://github.com/digitalocean/gradient-adk-templates.git
cd gradient-adk-templates
```

### Running a Template

```bash
# Navigate to a template
cd StateGraph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run locally
export DIGITALOCEAN_API_TOKEN=your_token
gradient agent run

# Deploy to production
gradient agent deploy
```

## Template Overview

### Beginner Templates

**[StateGraph](./StateGraph/)** - A joke generator that demonstrates LangGraph fundamentals: state management, conditional routing, and multi-step LLM chains. Start here to understand how Gradient ADK agents work.

**[WebSearch](./WebSearch/)** - A minimal agent that uses DuckDuckGo for web search. Shows how to bind tools to LLMs using LangChain's `create_agent` helper function.

**[KnowledgeBaseRAG](./KnowledgeBaseRAG/)** - Query your DigitalOcean-managed Knowledge Base. Demonstrates integration with DigitalOcean's Knowledge Base service for document retrieval.

### Intermediate Templates

**[RAG](./RAG/)** - A multi-agent RAG system for document Q&A. Features query rewriting, document retrieval from local PDFs, and answer generation with citations.

**[MCP](./MCP/)** - Demonstrates the Model Context Protocol for connecting to external tools. Includes both cloud-hosted (Tavily search) and local (calculator) MCP servers.

**[Crew](./Crew/)** - A CrewAI-based agent that researches news and generates trivia facts. Shows how to deploy agents built with frameworks other than LangGraph.

### Advanced Templates

**[SocialMediaCrew](./SocialMediaCrew/)** - A complete content creation pipeline with five specialized agents: Researcher, Copywriter, Social Media Manager, Reviewer, and Image Prompt Designer. Includes automatic revision loops and AI image generation.

**[DataScience](./DataScience/)** - A data science agent that converts natural language to SQL, executes queries, analyzes results, and generates visualizations. Features self-healing queries that automatically retry on failure.

**[DeepSearch](./DeepSearch/)** - A research agent with human-in-the-loop plan approval and parallel section research using LangGraph's Send API. Produces comprehensive reports with citations.

## Common Patterns

### Agent Structure

All templates follow a consistent structure:

```
TemplateName/
├── .gradient/
│   └── agent.yml          # Deployment configuration
├── agents/                 # Agent modules (if multi-agent)
├── tools/                  # Tool implementations
├── main.py                 # Entry point with @entrypoint decorator
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
└── README.md
```

### Entry Point

Every agent requires a `main.py` with an `@entrypoint` decorator:

```python
from gradient_adk import entrypoint

@entrypoint
def main(input: dict) -> dict:
    # Your agent logic here
    return {"response": "..."}
```

### Environment Variables

Common environment variables across templates:

| Variable | Description | Required For |
|----------|-------------|--------------|
| `DIGITALOCEAN_API_TOKEN` | DigitalOcean API token | All templates |
| `DIGITALOCEAN_INFERENCE_KEY` | GenAI Serverless Inference key | All templates |
| `SERPER_API_KEY` | Serper web search API | Crew, SocialMediaCrew, DeepSearch |
| `TAVILY_API_KEY` | Tavily search API | MCP |
| `OPENAI_API_KEY` | OpenAI API (for embeddings) | RAG |

## Resources

- [Gradient AI Documentation](https://docs.digitalocean.com/products/gradient/)
- [Agent Development Kit Guide](https://docs.digitalocean.com/products/gradient/adk/)
- [DigitalOcean GenAI Platform](https://www.digitalocean.com/products/gradient)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [CrewAI Documentation](https://docs.crewai.com/)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
