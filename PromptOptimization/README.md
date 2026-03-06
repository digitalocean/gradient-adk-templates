# Prompt Optimization Template

Automatically optimize your agent's system prompt using DSPy, evaluate with both custom metrics and Gradient's built-in evaluators, and deploy the best version to production.

**Use Case:** A customer support email classifier and responder that categorizes emails (billing, technical, account, general) and generates helpful responses. The prompt optimization workflow improves both classification accuracy and response quality.

| Feature | Tool |
|---------|------|
| Prompt optimization | DSPy MIPROv2 |
| Agent orchestration | LangGraph StateGraph |
| Prompt structure | LangChain ChatPromptTemplate |
| LLM inference | DigitalOcean Serverless |
| Local evaluation | LLM-as-judge + exact match |
| Platform evaluation | Gradient agent evaluate |
| Deployment | Gradient ADK |

## Quick Start

```bash
# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DigitalOcean credentials

# Test the baseline agent locally
gradient agent run

# In another terminal, send a test request
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I was charged twice for my subscription last month."}'

# Run the optimization workflow
python optimize.py
```

## How It Works

### The Agent (`main.py`)

A LangGraph `StateGraph` that takes a customer email, classifies it into a category, and generates a response. The system prompt is loaded from the active prompt version (managed by `prompt_manager.py`).

```
START -> classify_and_respond -> END
```

The agent uses a `ChatPromptTemplate` with pluggable components:
- **System instruction** (what DSPy optimizes)
- **Category definitions** (the classification taxonomy)
- **Response guidelines** (tone and format rules)
- **Few-shot examples** (injected by DSPy during optimization)

### Optimization Workflow (`optimize.py`)

An interactive CLI that guides you through the full optimize-evaluate-deploy cycle:

```
=== PROMPT OPTIMIZATION WORKFLOW ===

Active prompt: v1_baseline

--- Optimize ---
[1] Run optimization (DSPy MIPROv2)

--- Evaluate ---
[2] Evaluate prompt locally (DSPy metrics)
[3] Evaluate with Gradient (local agent)

--- Manage Versions ---
[4] Compare prompt versions
[5] Set active prompt version
[6] Rollback to previous version

--- Deploy ---
[7] Deploy agent to Gradient
[8] Evaluate deployed agent (Gradient)
```

### Two-Tier Evaluation

This template showcases two complementary evaluation approaches:

**DSPy Evaluation (option 2)** — Fast, custom metrics run locally:
- Classification accuracy (exact match on category)
- Response quality (LLM-as-judge, 1-10 scale)
- Per-category breakdown
- Side-by-side version comparison

**Gradient Evaluation (options 3 & 8)** — Platform-grade evaluation with 19 built-in metrics:
- Correctness (general hallucinations)
- Instruction Following
- Tone analysis
- PII leak detection
- Prompt injection detection
- And more (see [Gradient Evaluation Metrics](https://docs.digitalocean.com/products/gradient-ai-platform/reference/agent-evaluation-metrics/))

Option 3 runs Gradient evaluation **before deployment** by starting the agent locally with `gradient agent run` and evaluating against it. Option 8 evaluates the deployed agent.

### Prompt Version Management

Every optimization run saves a new prompt version in `prompt_versions/`. Each version stores:
- The optimized system instruction
- Few-shot examples (if bootstrapped by DSPy)
- Evaluation scores
- Metadata (optimizer, timestamp)

You can compare versions, set any version as active, and rollback at any time.

## Recommended Workflow

1. **Baseline** — Run `python optimize.py` → option `[2]` to evaluate the baseline prompt
2. **Optimize** — Option `[1]` to run DSPy MIPROv2 optimization (start with "light")
3. **Evaluate locally** — Option `[2]` to see accuracy and quality scores
4. **Evaluate with Gradient** — Option `[3]` to get platform metrics on the local agent
5. **Compare** — Option `[4]` to compare baseline vs optimized side-by-side
6. **Activate** — Option `[5]` to set the best version as active
7. **Deploy** — Option `[7]` to deploy to Gradient
8. **Validate** — Option `[8]` to run Gradient evaluation on the deployed agent

## Customizing for Your Use Case

### Change the classification categories

Edit `CATEGORY_DEFINITIONS` in `prompts.py`:

```python
CATEGORY_DEFINITIONS = """Categories:
- sales: Purchase inquiries, pricing, quotes
- support: Technical issues, bug reports
- feedback: Feature requests, complaints, suggestions"""
```

### Use your own training data

Replace `data/train.csv` and `data/val.csv` with your own labeled examples. Format:

```csv
email_text,category,good_response_traits
"Your customer message here",your_category,"Expected response characteristics"
```

Aim for 30-50+ training examples and 15-20 validation examples.

### Change the evaluation metric

Edit `support_metric()` in `optimize.py` to weight what matters for your use case.

### Swap the LLM model

Change `DEFAULT_MODEL` in `main.py` and `TASK_MODEL`/`OPTIMIZER_MODEL` in `optimize.py`.

Available models on DO Serverless:
- `openai-gpt-4.1` — Most capable
- `openai-gpt-oss-120b` — Open source, cost-effective

## Project Structure

```
PromptOptimization/
├── .gradient/
│   └── agent.yml              # Gradient deployment config
├── main.py                    # Agent entrypoint (LangGraph + ChatPromptTemplate)
├── prompts.py                 # Prompt template components
├── optimize.py                # Interactive optimization workflow (DSPy + Gradient)
├── evaluate.py                # Local evaluation harness
├── prompt_manager.py          # Prompt version tracking
├── data/
│   ├── train.csv              # Training examples (40 labeled)
│   ├── val.csv                # Validation examples (20 labeled)
│   └── eval_dataset.csv       # Gradient evaluation dataset
├── prompt_versions/           # Saved prompt versions (auto-generated)
├── requirements.txt
├── .env.example
└── README.md
```

## Advanced: Using GEPA Optimizer

[GEPA](https://dspy.ai/api/optimizers/GEPA/overview/) (Genetic-Pareto Algorithm) is a newer DSPy optimizer that uses reflective prompt evolution and outperforms MIPROv2 by ~10% on benchmarks. To use it, modify `optimize.py`:

```python
# Replace MIPROv2 with GEPA
optimizer = dspy.GEPA(
    metric=support_metric,
    max_steps=50,
)
optimized = optimizer.compile(
    student,
    trainset=trainset,
)
```

GEPA is best suited for complex multi-step tasks. For straightforward classification + response tasks, MIPROv2 is typically sufficient.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DIGITALOCEAN_API_TOKEN` | DigitalOcean API token | For deployment & Gradient eval |
| `DIGITALOCEAN_INFERENCE_KEY` | GenAI Serverless Inference key | For all LLM calls |

## Resources

- [DSPy Documentation](https://dspy.ai/)
- [DSPy MIPROv2 API](https://dspy.ai/api/optimizers/MIPROv2/)
- [Gradient ADK Guide](https://docs.digitalocean.com/products/gradient-ai-platform/how-to/build-agents-using-adk/)
- [Gradient Evaluation Metrics](https://docs.digitalocean.com/products/gradient-ai-platform/reference/agent-evaluation-metrics/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
