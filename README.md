# DigitalOcean GradientAI ADK Templates & Examples

This repositiory contains example templates for building and deploying agents using DigitalOcean's Gradient ADK. Each template demonstrates a different agent architecture and can be used as a starting point for ADK deployments.

Templates included:

- `RAG/` — A multi-agent Retrieval-Augmented-Generation (RAG) Question Answering agent built with LangGraph and LangChain, using an in-memory retriever over local PDFs.
- `MCP/` — An example ADK agent that connects to tools running on MCP servers. Demonstrates calling an external MCP server (Tavily) for web search and a calculator tool via MCP.
- `Crew/` — A Crew AI example that creates a small crew of agents to research news on a topic+date and produce interesting trivia snippets.
- `WebSearch/` - A simple LangGraph agent that uses a web-search tool.
- `KnowledgeBaseRAG/` - A simple LangGraph agent that queries your DigitalOcean built Knowledge Base.
- `Streaming_and_Tools/` - A LangGraph agent that uses a web-search tool and streams back responses

Each template directory includes a `main.py` (the ADK entrypoint) and a `requirements.txt`. See the README in each template for details and quickstart instructions:

- `RAG/README.md` — details and local run/deploy notes for the RAG Q&A agent.
- `MCP/README.md` — details for setting up MCP connections and required environment variables.
- `Crew/README.md` — details for the Crew AI trivia generator and its search tool.
- `WebSearch/README.md` — details for the WebSearch agent.
- `KnowledgeBaseRAG/README.md` — details for the Agent that queries your DigitalOcean Knowledge Base.
- `Streaming_and_Tools/README.md` - details for the agent that uses a search tool and streams responses.

