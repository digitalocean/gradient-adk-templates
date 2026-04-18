# Prompt Optimization Template

Automatically optimize your agent's system prompt using DSPy, evaluate with both custom metrics and DigitalOcean's built-in evaluators, and deploy the best version to production.

**Use Case:** A customer support email classifier and responder that categorizes emails (billing, technical, account, general) and generates helpful responses. The prompt optimization workflow improves both classification accuracy and response quality.

| Feature | Tool |
|---------|------|
| Prompt optimization | DSPy MIPROv2 |
| Agent orchestration | LangGraph StateGraph |
| Prompt structure | LangChain ChatPromptTemplate |
| LLM inference | DigitalOcean Serverless |
| Evaluation | Local DSPy metrics + DigitalOcean platform evaluation |
| Deployment | DigitalOcean ADK |

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

# Run the interactive optimization workflow
python interactive.py

# Or run optimization directly (scriptable)
python optimize.py light my_version_name
```

Example response from the agent:

```json
{
  "output": "Category: billing\nResponse: I'm sorry to hear about the duplicate charge on your subscription. I understand how frustrating unexpected billing issues can be. Here's what I'd recommend:\n\n1. Log in to your account and navigate to the Billing section to verify the duplicate charge\n2. If confirmed, click \"Request Refund\" next to the duplicate transaction\n3. If you don't see that option, contact our billing team directly at billing@support.example.com\n\nThe refund typically processes within 3-5 business days. Please don't hesitate to reach out if you need further assistance."
}
```

## Example: Before and After Optimization

The baseline prompt is intentionally minimal — just a one-line instruction with category names and a response format:

**Before (baseline):**
```
[System Instruction]
You are a customer support agent. Classify the customer's email into one of
the provided categories and write a helpful response.

[Category Labels]  (fixed)
Categories: billing, technical, account, general

[Response Format]  (fixed)
Response format:
Category: <category>
Response: <response>

[Few-Shot Examples]
(none)
```

After running MIPROv2 optimization, DSPy rewrites the system instruction with detailed guidance and adds bootstrapped few-shot examples. The category labels and response format stay fixed so parsing never breaks:

**After (optimized):**
```
[System Instruction]
You are a customer support agent for a cloud platform. Given a customer email,
classify it into one of the categories and write a professional, empathetic
response with actionable next steps.

**Task Overview**
You are acting as an expert customer‑support agent for a cloud‑platform
service. For each incoming support email you must:

1. **Classify** – assign the email to exactly one of the four predefined
   categories: billing, technical, account, or general.
2. **Reply** – write a professional, courteous, and empathetic response that
   (a) acknowledges the user's concern, (b) summarizes the next actionable
   steps you recommend, and (c) invites the user to follow up if needed.

**Classification Details**
- billing – invoices, charges, refunds, credits, payment methods, or
  usage‑cost discrepancies.
- technical – connectivity, performance, errors, logs, deployments, or any
  functional issue with the platform's services.
- account – ownership, permissions, role changes, account settings, password
  resets, or profile information.
- general – informational queries, feature requests, feedback, or anything
  that does not fit the three categories above.

**Style & Tone Guidelines**
- Empathy – begin by acknowledging the user's problem.
- Clarity – use plain language, avoid jargon unless necessary.
- Actionability – each step must be concrete.
- Professionalism – maintain a courteous, helpful demeanor.

[Category Labels]  (fixed)
Categories: billing, technical, account, general

[Response Format]  (fixed)
Response format:
Category: <category>
Response: <response>

[Few-Shot Examples]
Examples:

Email: I'm getting timeout errors when trying to SSH into my droplet. It was
working fine until this morning.
Category: technical
Response: Hi there, I'm sorry you're having trouble SSH‑ing into your
droplet—let's get that sorted out quickly. Here's what we can check right now:
1. Is the droplet up? Log into your control panel and confirm it is running.
2. Is the SSH service running? From the console, run: sudo systemctl status sshd
3. Firewall / security group rules — check that port 22 is still allowed.
4. IP address changes — verify the IP shown in the panel matches what you're
   connecting to.
If these checks don't resolve the issue, let me know and I can open a support
ticket. Best regards, Cloud Support Team
```

In a representative run, optimization improved classification accuracy from 67% to 88% (+21pp) while maintaining high response quality (4.8 → 4.9/5). DSPy discovers that adding detailed classification definitions, tone guidance, and real examples from the training data drives most of the gain — even though the underlying LLM is the same. Due to the stochastic nature of both the models and the optimization process, your exact scores may vary between runs.

## How It Works

### Agent Orchestration with LangGraph (`main.py`)

The agent is built as a LangGraph `StateGraph` — a stateful, node-based execution graph that makes the processing pipeline explicit and extensible. The graph maintains a typed state (`SupportState`) that tracks the email text, predicted category, generated response, and which prompt version produced the result:

```
START -> classify_and_respond -> END
```

LangGraph handles orchestration so the agent's behaviour is deterministic and inspectable, and prompt version tracking is embedded directly into the graph state.

### Structured Prompts with LangChain (`prompts.py`)

The agent's prompt is assembled from modular components using LangChain's `ChatPromptTemplate`:

- **System instruction** — The behavioural directive, response style, and any category definitions that DSPy produces during optimization
- **Category labels** — The fixed list of category names (`billing, technical, account, general`)
- **Response format** — The fixed output structure (`Category: <category>\nResponse: <response>`)
- **Few-shot examples** — Demonstrations bootstrapped during optimization

DSPy optimizes the system instruction and few-shot examples together — MIPROv2 rewrites the instruction and selects which demonstrations to include based on what combination scores best on the training metric. This means DSPy can improve the response guidelines, add category definitions, adjust tone, or restructure the instruction however it sees fit.

The category labels and response format are intentionally kept as fixed, non-optimizable sections. The parsing logic in `main.py` depends on the exact label names and the `Category:` / `Response:` prefix format to extract structured output. By fixing these, DSPy can freely optimize *everything else* — response style, category definitions, instruction framing — without risk of breaking the parser. DSPy is free to add its own definitions of what each category means within the optimized instruction; it just can't rename the labels themselves.

### Prompt Version Management (`prompt_manager.py`)

Every optimization run produces a new prompt version saved as a JSON file in `prompt_versions/`. Each version stores the system instruction, few-shot examples, evaluation scores, optimizer metadata, and a timestamp. You can compare any two versions side-by-side, set any version as active, and rollback instantly — all before deploying. The active version is what the agent uses at runtime.

### How MIPROv2 Optimizes Your Prompt (`optimize.py`)

[MIPROv2](https://dspy.ai/api/optimizers/MIPROv2/) (Multi-prompt Instruction PRoposal Optimizer v2) is a DSPy optimizer that automatically improves both the system instruction and few-shot examples through a multi-stage process:

1. **Bootstrapping** — MIPROv2 runs the agent on training examples and collects successful input-output traces. These become candidate few-shot demonstrations.
2. **Instruction proposal** — A separate "proposer" LLM analyzes the task signature, training data, and bootstrapped traces to generate candidate system instructions that might improve performance.
3. **Bayesian search** — MIPROv2 treats the choice of instruction and demo combination as a hyperparameter optimization problem. It uses a Bayesian surrogate model to efficiently search the space of (instruction, demos) combinations, evaluating each candidate against the training set using your metric function.
4. **Selection** — The combination that scores highest on the metric is returned as the optimized program.

The optimization intensity (light / medium / heavy) controls how many trials the Bayesian search runs — more trials explore more combinations but take longer and make more LLM calls.

All LLM calls during optimization are routed through DigitalOcean's Serverless Inference endpoint, so no external API keys are needed.

### System Prompt Quality Measurement

The template measures prompt quality at two levels:

**During optimization** — DSPy uses a composite metric (`support_metric` in `optimize.py`) that combines classification accuracy (60%) with a response quality heuristic (40%). The heuristic checks for non-trivial length, empathetic language, and actionable guidance. This metric is fast enough to run hundreds of times during the Bayesian search without incurring excessive LLM calls.

**During evaluation** — The local evaluation harness (`evaluate.py`) runs the agent on a held-out validation set and measures:
- **Classification accuracy** — exact match on predicted vs expected category, with per-category breakdown
- **Response quality** — an LLM-as-judge (`gpt-oss-120b`) scores each response on a 1-5 rubric anchored to clear level descriptions (Excellent / Good / Acceptable / Poor / Unacceptable), checking whether it addresses the customer's issue, uses an appropriate tone, and provides actionable next steps

These scores are saved to the prompt version file, so you can track quality across optimization runs and make informed decisions about which version to deploy.

### Two-Tier Evaluation: Local vs Platform

This template provides two complementary evaluation approaches for different stages of the workflow:

**Local DSPy Evaluation (option 2)** runs during development, before deployment. It uses `data/val.csv` — a validation set of 24 labeled examples with expected categories and response traits. The evaluation calls the LLM directly (via DO Serverless) and computes custom metrics: exact-match accuracy and LLM-as-judge quality scores. This is fast, repeatable, and useful for comparing prompt versions head-to-head during iteration.

**Platform Evaluation (option 7)** runs after deployment against the live agent endpoint. It uses a separate held-out dataset (`data/gradient_eval_dataset.csv`) with examples that were **not** used during optimization or local evaluation. DigitalOcean's built-in evaluator provides platform-grade metrics across multiple categories:
- **Correctness** — general hallucinations, instruction following
- **User outcomes** — goal progress and completion
- **Safety & security** — PII leak detection, toxicity, prompt injection

The key difference: local evaluation tells you whether the optimized prompt is better than the baseline on *your* metrics. Platform evaluation tells you whether the deployed agent meets production quality standards on a broader set of concerns (hallucinations, safety, user outcomes) using examples the agent has never seen. Use both — local evaluation for fast iteration, platform evaluation for deployment validation.

### Interactive Workflow (`interactive.py`)

A menu-driven CLI that guides you through the full optimize-evaluate-deploy cycle. It imports the optimization engine from `optimize.py`, the evaluation harness from `evaluate.py`, and version management from `prompt_manager.py`:

```
=== PROMPT OPTIMIZATION WORKFLOW ===

Active prompt: v1_baseline

--- Optimize ---
[1] Run optimization (DSPy MIPROv2)

--- Evaluate ---
[2] Evaluate prompt locally (DSPy metrics)

--- Manage Versions ---
[3] Compare prompt versions
[4] Set active prompt version
[5] Rollback to previous version

--- Deploy ---
[6] Deploy agent
[7] Evaluate deployed agent (platform)
```

### Prompt Versioning

Every optimization run automatically becomes a version you can switch to, evaluate, compare, or rollback from. Versions are JSON files stored in `prompt_versions/` — one is marked **active** and used by the agent at runtime.

**How it works:**
- Running optimization (option `[1]`) saves a new version with a name you choose (or an auto-generated timestamped default)
- Each version stores the system instruction, few-shot examples, optimizer metadata, evaluation scores, and a creation timestamp
- The **active** version is what `main.py` loads when the agent handles a request — changing it instantly changes the agent's behaviour
- Evaluation scores are attached to each version, so you can track quality across runs

**Interactive versioning (via `python interactive.py`):**

```
# List and compare versions (option 3)
Available versions:
  v1_baseline [ACTIVE] | manual | acc=<xx>%, quality=<x.x>/5 | <timestamp>
  <your-version> | dspy_miprov2_medium | acc=<xx>%, quality=<x.x>/5 | <timestamp>

# Switch active version (option 4)
Version to activate: <your-version>
Active prompt set to: <your-version>

# Rollback (option 5) — same as switching, with confirmation
Current active: <your-version>
Version to rollback to: v1_baseline
Rolled back to: v1_baseline
```

**Scriptable versioning (via `prompt_manager.py`):**

You can also manage versions programmatically or from a script:

```python
import prompt_manager

# List all versions with scores
for v in prompt_manager.list_versions():
    print(prompt_manager.format_version_summary(v))

# Switch the active version
prompt_manager.set_active("<your-version>")

# Rollback to baseline
prompt_manager.set_active("v1_baseline")

# Load and inspect a specific version
version = prompt_manager.load_version("<your-version>")
print(version["system_instruction"])
print(version["scores"])

# Compare two versions
from evaluate import compare_versions
compare_versions("v1_baseline", "<your-version>")
```

A convenience script `version_manager.py` is also included for common operations from the command line:

```bash
# List all versions
python version_manager.py list

# Show details of a specific version
python version_manager.py show <your-version>

# Switch active version
python version_manager.py activate <your-version>

# Compare two versions side-by-side
python version_manager.py compare v1_baseline <your-version>

# Rollback to a previous version
python version_manager.py rollback v1_baseline
```

**Typical versioning workflow:**
1. Start with `v1_baseline` (auto-created on first run)
2. Run optimization → creates `v_dspy_light_...` with training accuracy
3. Evaluate locally → scores get attached to the version
4. Compare baseline vs optimized → decide which is better
5. Activate the winner → agent uses it at runtime
6. Deploy → push the active version to production
7. If something goes wrong → rollback to the previous version

## Recommended Workflow

1. **Baseline** — Run `python interactive.py` → option `[2]` to evaluate the baseline prompt
2. **Optimize** — Option `[1]` to run DSPy MIPROv2 optimization (start with "light")
3. **Evaluate locally** — Option `[2]` to see accuracy and quality scores
4. **Compare** — Option `[3]` to compare baseline vs optimized side-by-side
5. **Activate** — Option `[4]` to set the best version as active
6. **Deploy** — Option `[6]` to deploy to DigitalOcean
7. **Validate** — Option `[7]` to run platform evaluation on the deployed agent

## Customizing for Your Use Case

### Change the classification categories

Edit `CATEGORY_LABELS` in `prompts.py` and update `VALID_CATEGORIES` in `main.py` to match:

```python
CATEGORY_LABELS = """Categories: sales, support, feedback"""
```

You only need to list the label names — DSPy can learn to define them during optimization based on your training data.

### Use your own training data

Replace `data/train.csv` and `data/val.csv` with your own labeled examples. Format:

```csv
email_text,category,good_response_traits
"Your customer message here",your_category,"Expected response characteristics"
```

Aim for 30-50+ training examples and 15-20 validation examples. Include ambiguous cross-category emails (e.g., "My payment failed and now I can't access my services") — these are the cases where prompt optimization makes the biggest difference, since the baseline instruction has no disambiguation rules. Also update `data/gradient_eval_dataset.csv` with held-out examples in the platform query format (see the existing file for the schema).

### Change the evaluation metric

Edit `support_metric()` in `optimize.py` to weight what matters for your use case.

### Swap the LLM model

Change `DEFAULT_MODEL` in `main.py` and `TASK_MODEL`/`OPTIMIZER_MODEL` in `optimize.py`. See the [full list of available models](https://docs.digitalocean.com/products/gradient-ai-platform/details/models/) on the DigitalOcean AI Platform.

## Project Structure

```
PromptOptimization/
├── .gradient/
│   └── agent.yml              # ADK deployment config
├── main.py                    # Agent entrypoint (LangGraph + ChatPromptTemplate)
├── prompts.py                 # Prompt template components
├── optimize.py                # DSPy MIPROv2 optimization engine
├── interactive.py             # Interactive CLI workflow (menu-driven)
├── evaluate.py                # Local evaluation harness
├── prompt_manager.py          # Prompt version tracking
├── version_manager.py         # CLI for version management (list/show/activate/rollback/compare)
├── data/
│   ├── train.csv              # Training examples (48 labeled)
│   ├── val.csv                # Validation examples (24 labeled)
│   ├── eval_dataset.csv       # Local evaluation dataset
│   └── gradient_eval_dataset.csv  # Held-out platform evaluation dataset
├── prompt_versions/           # Saved prompt versions (auto-generated)
├── requirements.txt
├── .env.example
└── README.md
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DIGITALOCEAN_API_TOKEN` | DigitalOcean API token | For deployment & platform eval |
| `DIGITALOCEAN_INFERENCE_KEY` | GenAI Serverless Inference key | For all LLM calls |

## Resources

- [DSPy Documentation](https://dspy.ai/)
- [DSPy MIPROv2 API](https://dspy.ai/api/optimizers/MIPROv2/)
- [ADK Guide](https://docs.digitalocean.com/products/gradient-ai-platform/how-to/build-agents-using-adk/)
- [Evaluation Metrics](https://docs.digitalocean.com/products/gradient-ai-platform/reference/agent-evaluation-metrics/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
