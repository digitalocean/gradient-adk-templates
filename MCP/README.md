# MCP - Model Context Protocol Integration

An agent that connects to external tools via the Model Context Protocol (MCP). This template demonstrates how to use both cloud-hosted and local MCP servers to extend LLM capabilities with web search and precise calculations.

## Use Case

Connect your agent to external tools and services using the standardized Model Context Protocol. This template shows how to overcome common LLM limitations - lack of current information and mathematical accuracy - by integrating Tavily search and a calculator via MCP.

**When to use this template:**
- You want to use MCP-compatible tools
- You need to connect to external services via a standard protocol
- You're building agents that require precise calculations or real-time data

## Key Concepts

**Model Context Protocol (MCP)** is an open standard for connecting LLMs to external tools and data sources. Instead of writing custom integrations for each tool, MCP provides a unified protocol that any compatible server can implement. This means you can easily swap tools, combine multiple services, and benefit from a growing ecosystem of MCP-compatible servers.

This template demonstrates both **remote and local MCP servers**. Remote servers (like Tavily search) are cloud-hosted services accessed via HTTP, while local servers (like the calculator) run as subprocesses on the same machine. LangChain's `MultiServerMCPClient` connects to multiple servers simultaneously, exposing all their tools to your agent through a single interface.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         MCP Agent                                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Input: { prompt }                                                   │
│           │                                                          │
│           ▼                                                          │
│  ┌────────────────────────────────────┐                              │
│  │          LLM (GPT-4.1)             │◄─────────────────────┐       │
│  │                                    │                      │       │
│  │  Bound to MCP tools:               │                      │       │
│  │  - tavily_search                   │            tool      │       │
│  │  - calculator                      │            results   │       │
│  │                                    │                      │       │
│  │  The LLM decides:                  │                      │       │
│  │  1. Which tool(s) to call          │                      │       │
│  │  2. When to stop and respond       │                      │       │
│  └──────────────┬─────────────────────┘                      │       │
│                 │                                            │       │
│         (calls tool)                                         │       │
│         ┌───────┴───────┐                                    │       │
│         │               │                                    │       │
│         ▼               ▼                                    │       │
│  ┌────────────────┐  ┌────────────────┐                      │       │
│  │ Tavily Search  │  │  Calculator    │                      │       │
│  │ (Remote MCP)   │  │  (Local MCP)   │                      │       │
│  │                │  │                │                      │       │
│  │ Cloud-hosted   │  │ Local process  │                      │       │
│  │ web search     │  │ for math       │                      │       │
│  └───────┬────────┘  └───────┬────────┘                      │       │
│          │                   │                               │       │
│          └─────────┬─────────┘                               │       │
│                    │                                         │       │
│                    └─────────────────────────────────────────┘       │
│                    (results return to same LLM)                      │
│                                                                      │
│                 │ (when done reasoning)                              │
│                 ▼                                                    │
│  Output: Answer combining search + calculation                       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

The agent uses a **single LLM in a reasoning loop**. The LLM has MCP tools bound to it and autonomously decides which tools to call based on the user's query. Tool results are returned to the same LLM, which can then call additional tools or generate the final response.

## Prerequisites

- Python 3.10+
- DigitalOcean account
- Tavily API key ([get one free](https://app.tavily.com/home))

### Getting API Keys

1. **DigitalOcean API Token**:
   - Go to [API Settings](https://cloud.digitalocean.com/account/api/tokens)
   - Generate a new token with read/write access

2. **DigitalOcean Inference Key**:
   - Go to [GenAI Settings](https://cloud.digitalocean.com/gen-ai)
   - Create or copy your inference key

3. **Tavily API Key**:
   - Sign up at [tavily.com](https://app.tavily.com/home)
   - Get your free API key from the dashboard

## Setup

### 1. Create Virtual Environment

```bash
cd MCP
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
TAVILY_API_KEY=your_tavily_key
```

## Running Locally

### Start the Agent

```bash
export DIGITALOCEAN_API_TOKEN=your_token
gradient agent run
```

### Test with curl

**Query requiring both web search and calculation:**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "prompt": {
            "messages": "What is sqrt(5) + sqrt(7) times the age of the current pope?"
        }
    }'
```

**Web search only:**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "prompt": {
            "messages": "What are the latest developments in quantum computing?"
        }
    }'
```

**Calculation only:**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "prompt": {
            "messages": "Calculate 15% compound interest on $10,000 over 5 years"
        }
    }'
```

## Deployment

### 1. Configure Agent Name

Edit `.gradient/agent.yml`:

```yaml
agent_name: my-mcp-agent
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
            "messages": "What is sqrt(5) + sqrt(7) times the age of the current pope?"
        }
    }'
```

## Project Structure

```
MCP/
├── .gradient/
│   └── agent.yml          # Deployment configuration
├── main.py                 # MCP client setup and agent
├── prompts.py              # System message (edit this to customize!)
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
└── README.md
```

## Code Walkthrough

### Setting Up MCP Clients

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

mcp_client = MultiServerMCPClient({
    "search": {
        "url": "https://mcp.tavily.com/mcp",
        "transport": "streamable-http",
        "headers": {"Authorization": f"Bearer {tavily_api_key}"}
    },
    "calculator": {
        "command": "python",
        "args": ["-m", "mcp_server_calculator"],
        "transport": "stdio"
    }
})
```

### Creating the Agent with MCP Tools

```python
from langchain_gradient import ChatGradient
from langgraph.prebuilt import create_react_agent

# Get tools from MCP servers
tools = await mcp_client.get_tools()

# Create agent with MCP tools
llm = ChatGradient(model="openai-gpt-4.1")
agent = create_react_agent(llm, tools)
```

## Customization

### Customizing the Agent's Behavior

The easiest way to adapt this template is by editing **`prompts.py`**. This file contains the system message that guides how the agent uses the MCP tools.

**Example: Research Assistant**

```python
# In prompts.py, change SYSTEM_MESSAGE to:
SYSTEM_MESSAGE = """You are a research assistant with access to web search and calculation tools.
When helping users:
- Always search for the most recent information
- Cite your sources with URLs when possible
- Use the calculator for any numerical analysis
- Provide balanced perspectives on complex topics"""
```

**Example: Financial Assistant**

```python
SYSTEM_MESSAGE = """You are a financial assistant with access to web search and calculation tools.
When answering financial questions:
- Search for current market data and news
- Use the calculator for precise financial calculations
- Always note that you're not providing financial advice
- Be clear about the date of any market information"""
```

**Example: Technical Assistant**

```python
SYSTEM_MESSAGE = """You are a technical assistant with access to web search and calculation tools.
When helping with technical questions:
- Search for documentation and solutions
- Use the calculator for performance calculations or conversions
- Provide step-by-step explanations when helpful
- Note any limitations or caveats in your answers"""
```

### Adding More MCP Servers

Extend the MCP client configuration:

```python
mcp_client = MultiServerMCPClient({
    "search": {...},
    "calculator": {...},
    # Add a weather service
    "weather": {
        "url": "https://mcp.weather-api.com/mcp",
        "transport": "streamable-http",
        "headers": {"Authorization": f"Bearer {weather_api_key}"}
    },
    # Add a local data analysis tool
    "data_analysis": {
        "command": "python",
        "args": ["-m", "my_data_analysis_tool"],
        "transport": "stdio"
    }
})
```

### Creating Your Own MCP Server

Build a custom MCP server:

```python
# my_mcp_server.py
from mcp.server import Server
from mcp.types import Tool

server = Server("my-tools")

@server.tool()
async def my_custom_tool(query: str) -> str:
    """Description of what this tool does."""
    # Your tool implementation
    return result

if __name__ == "__main__":
    server.run()
```

Then add it to your agent:

```python
mcp_client = MultiServerMCPClient({
    "my_tools": {
        "command": "python",
        "args": ["my_mcp_server.py"],
        "transport": "stdio"
    }
})
```


## MCP Server Types

| Type | Transport | Use Case |
|------|-----------|----------|
| Remote HTTP | `streamable-http` | Cloud-hosted services (Tavily, etc.) |
| Local Process | `stdio` | Python packages, local scripts |
| WebSocket | `ws` | Real-time bidirectional communication |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot connect to MCP server" | Check the server URL and API key |
| Local MCP server not starting | Ensure the package is installed (`pip install mcp-server-calculator`) |
| Tool not found | Verify the MCP server exposes the expected tools |
| Timeout errors | Remote MCP servers may need longer timeouts |

## Notes

- Local MCP servers (using `command`) require the package to be installed
- Remote MCP servers are preferred for serverless deployment
- MCP is an open standard - check [modelcontextprotocol.io](https://modelcontextprotocol.io) for compatible servers

## Resources

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Servers Directory](https://github.com/modelcontextprotocol/servers)
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
- [Tavily MCP Documentation](https://docs.tavily.com/documentation/mcp)
- [Gradient ADK Documentation](https://docs.digitalocean.com/products/gradient/adk/)
