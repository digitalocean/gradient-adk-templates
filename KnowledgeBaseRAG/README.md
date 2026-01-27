# KnowledgeBaseRAG - DigitalOcean Knowledge Base Integration

An agent that queries your DigitalOcean-managed Knowledge Base using natural language. This template demonstrates how to integrate with DigitalOcean's Knowledge Base service for document retrieval without managing your own vector store.

## Use Case

Use DigitalOcean's managed Knowledge Base service to build a Q&A agent over your documents. Unlike the RAG template that manages its own embeddings, this approach uses DigitalOcean's infrastructure for document storage and retrieval.

**When to use this template:**
- You want managed document storage and retrieval
- You're already using DigitalOcean Knowledge Bases
- You don't want to manage embedding infrastructure

## Key Concepts

**DigitalOcean Knowledge Bases** provide managed document storage and retrieval without the complexity of running your own vector database. You upload documents or provide URLs, and DigitalOcean automatically handles chunking, embedding, and indexing. Your agent queries the Knowledge Base via API, receiving relevant passages to use as context for generating answers.

This approach differs from the RAG template, which manages its own embeddings and vector store. With Knowledge Bases, you trade some customization flexibility for simpler infrastructure - no need to manage OpenAI API keys for embeddings or worry about vector store persistence.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│               KnowledgeBaseRAG Agent                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Input: { prompt }                                      │
│           │                                             │
│           ▼                                             │
│  ┌────────────────────────────────────┐                 │
│  │              LLM                   │◄────────────┐   │
│  │                                    │             │   │
│  │  Bound to query_digitalocean_kb    │             │   │
│  │  tool                              │      tool   │   │
│  │                                    │      results│   │
│  │  The LLM decides:                  │             │   │
│  │  1. Whether to query the KB        │             │   │
│  │  2. When to respond to the user    │             │   │
│  └──────────────┬─────────────────────┘             │   │
│                 │                                   │   │
│          (calls tool)                               │   │
│                 │                                   │   │
│                 ▼                                   │   │
│  ┌────────────────────────────────────┐             │   │
│  │   query_digitalocean_kb Tool       │             │   │
│  │                                    │             │   │
│  │  ┌──────────────────────────────┐  │             │   │
│  │  │  DigitalOcean Knowledge Base │  │             │   │
│  │  │                              │  │             │   │
│  │  │  - Managed vector storage    │  │             │   │
│  │  │  - Automatic embeddings      │  │             │   │
│  │  │  - Semantic search           │  │             │   │
│  │  └──────────────────────────────┘  │             │   │
│  └──────────────┬─────────────────────┘             │   │
│                 │                                   │   │
│                 └───────────────────────────────────┘   │
│                 (results return to same LLM)            │
│                                                         │
│                 │ (when done reasoning)                 │
│                 ▼                                       │
│  Output: Answer based on Knowledge Base                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

The agent uses a **single LLM in a reasoning loop**. The LLM has the Knowledge Base query tool bound to it and decides when to retrieve context. Tool results are returned to the same LLM, which synthesizes the retrieved documents into a coherent answer.

## Prerequisites

- Python 3.10+
- DigitalOcean account
- A DigitalOcean Knowledge Base with content

### Getting API Keys

1. **DigitalOcean API Token** (with `genai:*` and `project:read` scopes):
   - Go to [API Settings](https://cloud.digitalocean.com/account/api/tokens)
   - Generate a new token
   - Ensure the token has GenAI and project read permissions

2. **DigitalOcean Inference Key**:
   - Go to [GenAI Settings](https://cloud.digitalocean.com/gen-ai)
   - Create or copy your inference key

3. **Knowledge Base ID**:
   - Go to [Knowledge Bases](https://cloud.digitalocean.com/gen-ai/knowledge-bases)
   - Create a Knowledge Base or select an existing one
   - Copy the UUID from the URL: `https://cloud.digitalocean.com/gen-ai/knowledge-bases/<UUID>`

## Setup

### 1. Create a Knowledge Base

If you don't have a Knowledge Base yet:

1. Go to [DigitalOcean Knowledge Bases](https://cloud.digitalocean.com/gen-ai/knowledge-bases)
2. Click "Create Knowledge Base"
3. Add a data source
4. Wait for indexing to complete
5. Copy the Knowledge Base UUID from the URL

### 2. Create Virtual Environment

```bash
cd KnowledgeBaseRAG
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```
DIGITALOCEAN_INFERENCE_KEY=your_inference_key
DIGITALOCEAN_KB_ID=your_knowledge_base_uuid
```

## Running Locally

### Start the Agent

```bash
export DIGITALOCEAN_API_TOKEN=your_token
gradient agent run
```

### Test with curl

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "prompt": {
            "messages": "What is the Gradient AI Platform?"
        }
    }'
```

## Deployment

### 1. Configure Agent Name

Edit `.gradient/agent.yml`:

```yaml
agent_name: my-kb-agent
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
        "prompt": {
            "messages": "What is the Gradient AI Platform?"
        }
    }'
```

## Project Structure

```
KnowledgeBaseRAG/
├── .gradient/
│   └── agent.yml          # Deployment configuration
├── main.py                 # Agent with KB query tool
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
└── README.md
```

## Code Walkthrough

### Creating the KB Query Tool

```python
from langchain.tools import tool
import requests

@tool
def query_digitalocean_kb(query: str) -> str:
    """Query the DigitalOcean Knowledge Base."""
    kb_id = os.environ.get("DIGITALOCEAN_KB_ID")
    token = os.environ.get("DIGITALOCEAN_API_TOKEN")

    response = requests.post(
        f"https://api.digitalocean.com/v2/gen-ai/knowledge-bases/{kb_id}/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query}
    )

    return response.json()["results"]
```

### Creating the Agent

```python
from langchain_gradient import ChatGradient
from langchain.agents import create_tool_calling_agent, AgentExecutor

llm = ChatGradient(model="openai-gpt-4.1")
agent = create_tool_calling_agent(llm, [query_digitalocean_kb], prompt)
executor = AgentExecutor(agent=agent, tools=[query_digitalocean_kb])
```

## Customization

### Using Multiple Knowledge Bases

Query different Knowledge Bases based on the topic:

```python
@tool
def query_product_docs(query: str) -> str:
    """Query the product documentation Knowledge Base."""
    return query_kb(os.environ["PRODUCT_KB_ID"], query)

@tool
def query_support_docs(query: str) -> str:
    """Query the support documentation Knowledge Base."""
    return query_kb(os.environ["SUPPORT_KB_ID"], query)

# Add both tools
agent = create_tool_calling_agent(llm, [query_product_docs, query_support_docs], prompt)
```

### Adding Result Filtering

Filter or process KB results before returning:

```python
@tool
def query_digitalocean_kb(query: str, max_results: int = 5) -> str:
    """Query the Knowledge Base with result limit."""
    results = raw_query_kb(query)

    # Filter to top results by relevance score
    filtered = sorted(results, key=lambda x: x["score"], reverse=True)[:max_results]

    return "\n\n".join([r["content"] for r in filtered])
```

### Combining with Web Search

Use KB for internal docs, web search for external info:

```python
from langchain_community.tools import DuckDuckGoSearchRun

@tool
def query_digitalocean_kb(query: str) -> str:
    """Query internal documentation."""
    # ... KB query implementation

search_tool = DuckDuckGoSearchRun()
search_tool.description = "Search the web for external information."

agent = create_tool_calling_agent(llm, [query_digitalocean_kb, search_tool], prompt)
```

## Resources

- [DigitalOcean Knowledge Bases](https://docs.digitalocean.com/products/genai/concepts/knowledge-bases/)
- [GenAI API Reference](https://docs.digitalocean.com/reference/api/api-reference/#tag/GenAI)
- [Gradient ADK Documentation](https://docs.digitalocean.com/products/gradient/adk/)
