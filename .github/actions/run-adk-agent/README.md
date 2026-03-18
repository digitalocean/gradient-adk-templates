# Run ADK Agent

A reusable GitHub Action that runs `gradient agent run` to validate an ADK agent starts and is available at http://localhost:8080.

## Usage

```yaml
- uses: actions/checkout@v4
- uses: ./.github/actions/run-adk-agent
  with:
    working-directory: WebSearch
    digitalocean-inference-key: ${{ secrets.DIGITALOCEAN_INFERENCE_KEY }}
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `working-directory` | Yes | - | Path to agent directory (e.g., WebSearch, StateGraph, RAG) |
| `digitalocean-inference-key` | Yes | - | DigitalOcean GenAI inference key for LLM calls |
| `python-version` | No | `3.10` | Python version |
| `openai-api-key` | No | - | OpenAI API key (for RAG embeddings; not needed for WebSearch) |

## Secrets Setup

Add the required secret in your GitHub repo before the workflow can run:

1. Go to your repo on GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `DIGITALOCEAN_INFERENCE_KEY`
4. Value: Your DigitalOcean GenAI inference key (from [GenAI Settings](https://cloud.digitalocean.com/gen-ai))
5. Click **Add secret**

The secret is stored encrypted by GitHub and never shown in logs or to contributors.

## Secrets by Template

| Template | Required | Optional |
|----------|----------|----------|
| WebSearch | `DIGITALOCEAN_INFERENCE_KEY` | - |
| StateGraph | `DIGITALOCEAN_INFERENCE_KEY` | - |
| RAG | `DIGITALOCEAN_INFERENCE_KEY` | `OPENAI_API_KEY` |
| Others | See template `.env.example` | - |

## GitHub Enterprise

Works on GitHub.com and GitHub Enterprise Server. Uses standard `actions/checkout` and `actions/setup-python`.
