# WebSearch - Tool Calling Basics

A minimal agent that demonstrates how to give LLMs the ability to call external tools. This is the simplest pattern for extending what an LLM can do beyond its training data.

## Use Case

This template shows how to build a web search agent, but the real focus is on **tool calling** - the fundamental pattern that lets LLMs interact with external systems. Once you understand this pattern, you can connect agents to any API, database, or service.

**Template Highlights:**
- How to define and bind tools to an LLM
- How the LLM decides when to use a tool vs. answer directly
- Using LangChain's `create_agent` helper for quick setup
- Automatic tracing of tool calls on the Gradient AI Platform

## Key Concepts

**Tool calling** is how LLMs interact with the outside world. Instead of just generating text, the LLM can decide to invoke a function, receive the result, and then continue reasoning. This template uses DuckDuckGo search as the tool, but the same pattern applies to any external capability you want to give your agent.

The agent works by binding a tool definition to the LLM. When a user asks a question, the LLM examines the available tools and decides whether to call one. If it calls a tool, the result is fed back to the LLM, which then formulates the final response.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  WebSearch Agent                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Input: { prompt }                                  │
│           │                                         │
│           ▼                                         │
│  ┌─────────────────────────────────────┐            │
│  │           LLM (GPT-4.1)             │            │
│  │                                     │            │
│  │  Decides whether to:                │            │
│  │  1. Answer directly                 │            │
│  │  2. Search the web first            │            │
│  └──────────────┬──────────────────────┘            │
│                 │                                   │
│          (needs search)                             │
│                 │                                   │
│                 ▼                                   │
│  ┌─────────────────────────────────────┐            │
│  │       DuckDuckGo Search Tool        │            │
│  │                                     │            │
│  │  - Queries the web                  │            │
│  │  - Returns search results           │            │
│  │  - No API key needed                │            │
│  └──────────────┬──────────────────────┘            │
│                 │                                   │
│                 ▼                                   │
│  ┌─────────────────────────────────────┐            │
│  │           LLM (GPT-4.1)             │            │
│  │                                     │            │
│  │  Synthesizes search results         │            │
│  │  into a coherent answer             │            │
│  └──────────────┬──────────────────────┘            │
│                 │                                   │
│                 ▼                                   │
│  Output: Answer with web search results             │
│                                                     │
└─────────────────────────────────────────────────────┘
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

No additional API keys required - DuckDuckGo search is free.

## Setup

### 1. Create Virtual Environment

```bash
cd WebSearch
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

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "prompt": "Who won the 2024 Super Bowl?"
    }'
```

## Deployment

### 1. Configure Agent Name

Edit `.gradient/agent.yml`:

```yaml
agent_name: my-web-search-agent
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
        "prompt": "Who won the 2024 Super Bowl?"
    }'
```

## Sample Input/Output

### Input

```json
{
    "prompt": "What is the current price of Bitcoin?"
}
```

### Output

```json
{
    "response": "Based on my web search, Bitcoin is currently trading at approximately $67,500 USD. However, cryptocurrency prices are highly volatile and change constantly. For the most accurate real-time price, I recommend checking a cryptocurrency exchange like Coinbase or Binance directly."
}
```

### Input (No Search Needed)

```json
{
    "prompt": "What is the capital of France?"
}
```

### Output

```json
{
    "response": "The capital of France is Paris."
}
```

## Project Structure

```
WebSearch/
├── .gradient/
│   └── agent.yml          # Deployment configuration
├── main.py                 # Agent with DuckDuckGo tool
├── prompts.py              # System prompt (edit this to customize!)
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
└── README.md
```

## Code Walkthrough

### Creating the Agent

```python
from langchain_gradient import ChatGradient
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.tools import DuckDuckGoSearchRun

# Initialize the LLM
llm = ChatGradient(model="openai-gpt-4.1")

# Create the search tool
search_tool = DuckDuckGoSearchRun()

# Create the agent
agent = create_tool_calling_agent(llm, [search_tool], prompt)
executor = AgentExecutor(agent=agent, tools=[search_tool])

# Run
result = executor.invoke({"input": "Your question here"})
```

## Customization

### Customizing the Agent's Behavior

The easiest way to adapt this template is by editing **`prompts.py`**. This file contains the system prompt that defines how the agent behaves.

**Example: Research Assistant**

```python
# In prompts.py, change SYSTEM_PROMPT to:
SYSTEM_PROMPT = """You are a research assistant that helps users find accurate,
up-to-date information. When searching the web:
- Always cite your sources with URLs
- Distinguish between facts and opinions
- Note when information might be outdated
- Provide balanced perspectives on controversial topics"""
```

**Example: Technical Support Agent**

```python
SYSTEM_PROMPT = """You are a technical support specialist. When helping users:
- Search for the most recent documentation and solutions
- Provide step-by-step instructions when applicable
- Warn about common pitfalls or mistakes
- Suggest alternative approaches when the primary solution is complex"""
```

**Example: News Summarizer**

```python
SYSTEM_PROMPT = """You are a news analyst that helps users stay informed.
When searching for news:
- Summarize key points concisely
- Include publication dates to show recency
- Present multiple perspectives on news stories
- Focus on factual reporting over opinion pieces"""
```

### Adding More Tools

Add additional tools to the agent:

```python
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

# Create tools
search_tool = DuckDuckGoSearchRun()
wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

# Add both tools to the agent
agent = create_tool_calling_agent(llm, [search_tool, wiki_tool], prompt)
```

### Using a Different Search Provider

Replace DuckDuckGo with Tavily (requires API key):

```python
from langchain_community.tools.tavily_search import TavilySearchResults

search_tool = TavilySearchResults(max_results=5)
```

### Customizing the System Prompt

Modify agent behavior:

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful research assistant. Always cite your sources."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])
```

### Adding Memory

Enable conversation history:

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

executor = AgentExecutor(
    agent=agent,
    tools=[search_tool],
    memory=memory
)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Tool not found" error | Ensure `duckduckgo-search` is installed |
| Rate limiting | DuckDuckGo may rate limit; add delays between requests |
| Empty search results | Try rephrasing your query or check internet connectivity |

## Notes

- DuckDuckGo search is free but may have rate limits for high-volume usage
- For production use, consider Tavily or Serper for more reliable search
- All tool calls are automatically traced to the Gradient AI Platform after deployment

## Resources

- [LangChain Tools Documentation](https://python.langchain.com/docs/modules/tools/)
- [DuckDuckGo Search Tool](https://python.langchain.com/docs/integrations/tools/ddg/)
- [Gradient ADK Documentation](https://docs.digitalocean.com/products/gradient/adk/)
