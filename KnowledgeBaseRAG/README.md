# KnowledgeBaseRAG - ADK + KBaaS Demo

This template is a compact validation demo for showing that the DigitalOcean ADK and Knowledge Bases work well together.

It demonstrates:
- an ADK entrypoint that can be run locally or deployed
- a tool-backed retrieval call into a managed Knowledge Base
- grounded answers with lightweight source labels
- ADK tracing for both the agent flow and the retriever call

## What This Demo Proves

The demo is designed to answer a simple question for the ticket: can we build a clean ADK experience on top of KBaaS without standing up our own vector stack?

The answer path is:
1. The user sends a prompt to the ADK app.
2. The agent decides to call `query_digitalocean_kb`.
3. The tool queries the configured Knowledge Base.
4. Retrieved passages are returned in a citation-friendly format.
5. The model answers using those passages and cites them as `[Source N]`.

## Prerequisites

- Python 3.10+
- A DigitalOcean account
- A DigitalOcean Knowledge Base with indexed content
- A DigitalOcean API token with `genai:*` and `project:read`
- A DigitalOcean inference key

## Setup

```bash
cd KnowledgeBaseRAG
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

```bash
DIGITALOCEAN_API_TOKEN=your_digitalocean_api_token
DIGITALOCEAN_INFERENCE_KEY=your_digitalocean_inference_key
DIGITALOCEAN_KB_ID=your_knowledge_base_uuid
```

Optional knobs:

```bash
MODEL_NAME=openai-gpt-4.1
DIGITALOCEAN_KB_TOP_K=4
DIGITALOCEAN_KB_SNIPPET_CHARS=1200
```

## Run Locally

```bash
gradient agent run
```

The demo now accepts either a plain prompt string or the nested `prompt.messages` shape.

Plain prompt example:

```bash
curl --location 'http://localhost:8080/run' \
  --header 'Content-Type: application/json' \
  --data '{
    "prompt": "What does this knowledge base say about model deployment limits?"
  }'
```

Nested prompt example:

```bash
curl --location 'http://localhost:8080/run' \
  --header 'Content-Type: application/json' \
  --data '{
    "prompt": {
      "messages": "Summarize the indexing workflow and cite your sources."
    }
  }'
```

## Suggested Demo Flow

Use a Knowledge Base that contains product docs, onboarding docs, or policy docs. Then walk through a few prompts:

- "What is the product, in one paragraph?"
- "How does indexing work? Cite the sources you used."
- "What are the main setup steps for a new user?"
- "What information is missing from the docs for troubleshooting?"

What to point out during the demo:

- Answers stay grounded in KB retrieval instead of free-form model recall.
- Source labels make the response feel auditable.
- ADK traces let you show both the agent step and the retriever step.
- No separate vector DB, embedding pipeline, or custom retrieval service is needed in the app code.

## Deployment

Update the deployment name if you want:

```yaml
agent_name: knowledgebase-rag-demo
```

Then deploy:

```bash
gradient agent deploy
```

Invoke the deployed agent:

```bash
curl --location 'https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer <DIGITALOCEAN_API_TOKEN>' \
  --data '{
    "prompt": "What does the knowledge base say about indexing?"
  }'
```

## Files

```text
KnowledgeBaseRAG/
├── .env.example
├── .gradient/agent.yml
├── main.py
├── prompts.py
├── requirements.txt
└── README.md
```

## Implementation Notes

- `main.py` now accepts both common request payload shapes, so the README examples match runtime behavior.
- Retrieval results are formatted into `[Source N]` blocks with metadata when available.
- The actual Knowledge Base call is wrapped with `trace_retriever`, which makes the KB interaction easier to validate in ADK traces.
- The system prompt explicitly tells the model to retrieve before answering factual questions and to avoid unsupported claims.

## Resources

- [DigitalOcean Knowledge Bases](https://docs.digitalocean.com/products/genai/concepts/knowledge-bases/)
- [ADK Documentation](https://docs.digitalocean.com/products/gradient/adk/)
