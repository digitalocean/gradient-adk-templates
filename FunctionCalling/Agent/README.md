# Function Calling Agent

The agent code for the FunctionCalling template. This folder is what gets deployed via `gradient agent deploy`.

## How It Works

The agent reads `function_config.py` at startup and dynamically creates a LangGraph tool that calls your DigitalOcean Serverless Function over HTTP. The LLM decides when to invoke the function based on the user's prompt, constructs the correct input parameters, and interprets the response.

No code changes are needed when you swap functions — just update `function_config.py` and restart.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   Function Calling Agent                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: { prompt }                                           │
│           │                                                  │
│           ▼                                                  │
│  ┌────────────────────────────────────┐                      │
│  │          LLM (GPT-4.1)            │                      │
│  │                                    │                      │
│  │  Reads function_config.py to       │                      │
│  │  understand what the function      │                      │
│  │  does and what parameters it       │                      │
│  │  needs. Decides whether to:        │                      │
│  │  1. Answer directly                │                      │
│  │  2. Call the serverless function   │                      │
│  └──────────────┬─────────────────────┘                      │
│                 │                                             │
│          (needs function)                                    │
│                 │                                             │
│                 ▼                                             │
│  ┌────────────────────────────────────┐                      │
│  │   DO Serverless Function (HTTP)    │                      │
│  │                                    │                      │
│  │  - Receives JSON parameters        │                      │
│  │  - Runs your custom logic          │                      │
│  │  - Returns JSON result             │                      │
│  └──────────────┬─────────────────────┘                      │
│                 │                                             │
│                 ▼                                             │
│  ┌────────────────────────────────────┐                      │
│  │          LLM (GPT-4.1)            │                      │
│  │                                    │                      │
│  │  Interprets the function result    │                      │
│  │  and responds in natural language  │                      │
│  └──────────────┬─────────────────────┘                      │
│                 │                                             │
│                 ▼                                             │
│  Output: { "response": "..." }                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- DigitalOcean account
- A deployed serverless function (run `../Setup/setup.sh` for the sample)

### Getting API Keys

1. **DigitalOcean API Token**: [API Settings](https://cloud.digitalocean.com/account/api/tokens) — generate a token with read/write access
2. **DigitalOcean Inference Key**: [GenAI Settings](https://cloud.digitalocean.com/gen-ai) — create or copy your inference key

## Setup

```bash
cd Agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configure `.env` (copy from `.env.example` if needed):

```
FUNCTION_URL=https://faas-nyc1-xxx.doserverless.co/api/v1/web/fn-xxx/converter/convert
DIGITALOCEAN_API_TOKEN=your_token
DIGITALOCEAN_INFERENCE_KEY=your_key
```

## Running Locally

```bash
gradient agent run
```

### Test with curl

```bash
# Conversion request (calls the serverless function)
curl http://localhost:8080/run \
    -H 'Content-Type: application/json' \
    -d '{"prompt": "Convert 72 degrees fahrenheit to celsius"}'

# General question (LLM answers directly, no function call)
curl http://localhost:8080/run \
    -H 'Content-Type: application/json' \
    -d '{"prompt": "What is the capital of France?"}'

# Multi-step request (multiple function calls)
curl http://localhost:8080/run \
    -H 'Content-Type: application/json' \
    -d '{"prompt": "I weigh 150 pounds. What is that in kilograms and grams?"}'
```

## Deployment

### 1. Configure Agent Name

Edit `.gradient/agent.yml`:

```yaml
agent_name: my-function-calling-agent
```

### 2. Deploy

```bash
gradient agent deploy
```

### 3. Invoke Deployed Agent

```bash
curl 'https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer <DIGITALOCEAN_API_TOKEN>' \
    -d '{"prompt": "Convert 5 miles to kilometers"}'
```

## Sample Input/Output

### Input

```json
{
    "prompt": "How many kilograms is 200 pounds?"
}
```

### Output

```json
{
    "response": "200 pounds is approximately 90.72 kilograms."
}
```

## Key Files

| File | Purpose |
|------|---------|
| `function_config.py` | Defines the function name, URL, input parameters, and response schema. **This is the main file you edit.** |
| `prompts.py` | System prompt that controls the agent's behavior. |
| `main.py` | Entry point — reads config, builds a LangGraph ReAct agent with a dynamic tool, handles requests. |

## Connecting Your Own Function

### Step 1: Deploy your function

Deploy any function to DigitalOcean Functions and get its web URL:

```bash
doctl serverless deploy your-project
doctl serverless functions get your-package/your-function --url
```

### Step 2: Update `function_config.py`

Replace the sample config with your function's details:

```python
FUNCTION_CONFIG = {
    "name": "weather_lookup",
    "url": os.environ.get("FUNCTION_URL", ""),
    "description": (
        "Look up the current weather for a given city. "
        "Returns temperature, humidity, and conditions."
    ),
    "parameters": {
        "city": {
            "type": "string",
            "description": "The city name (e.g., 'New York', 'London')",
            "required": True,
        },
        "units": {
            "type": "string",
            "description": "Temperature units: 'metric' or 'imperial'",
            "required": False,
        },
    },
    "response_schema": {
        "temperature": {
            "type": "number",
            "description": "Current temperature in the requested units",
        },
        "humidity": {
            "type": "number",
            "description": "Humidity percentage (0-100)",
        },
        "conditions": {
            "type": "string",
            "description": "Weather conditions (e.g., 'sunny', 'cloudy', 'rain')",
        },
    },
}
```

### Step 3: Update `prompts.py` (optional)

```python
SYSTEM_PROMPT = """You are a weather assistant. Use the weather lookup function
to answer questions about current weather conditions in any city."""
```

That's it — the agent automatically builds the right tool from your config.

### More Examples

**Database Lookup:**
```python
FUNCTION_CONFIG = {
    "name": "product_search",
    "url": os.environ.get("FUNCTION_URL", ""),
    "description": "Search the product catalog by name or category.",
    "parameters": {
        "query": {
            "type": "string",
            "description": "Search term for product name or description",
            "required": True,
        },
        "category": {
            "type": "string",
            "description": "Product category to filter by (e.g., 'electronics', 'books')",
            "required": False,
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return",
            "required": False,
        },
    },
    "response_schema": {
        "products": {
            "type": "array",
            "description": "List of matching products, each with 'name', 'price', and 'description'",
        },
        "total_count": {
            "type": "integer",
            "description": "Total number of matches found",
        },
    },
}
```

**Notification Sender:**
```python
FUNCTION_CONFIG = {
    "name": "send_notification",
    "url": os.environ.get("FUNCTION_URL", ""),
    "description": "Send a notification message to a user via email or SMS.",
    "parameters": {
        "recipient": {
            "type": "string",
            "description": "Email address or phone number",
            "required": True,
        },
        "message": {
            "type": "string",
            "description": "The notification message to send",
            "required": True,
        },
        "channel": {
            "type": "string",
            "description": "Delivery channel: 'email' or 'sms'",
            "required": True,
        },
    },
    "response_schema": {
        "status": {
            "type": "string",
            "description": "Delivery status: 'sent', 'queued', or 'failed'",
        },
        "message_id": {
            "type": "string",
            "description": "Unique ID for tracking the notification",
        },
    },
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `FUNCTION_URL is not set` | Run `../Setup/setup.sh` or set the URL in `.env` |
| Function returns 400 | Check that the parameter names/types in `function_config.py` match your function |
| Agent doesn't call the function | Make the `description` in config more specific about when to use it |
| Timeout errors | Increase the timeout in `main.py` or the function's `limits.timeout` in `project.yml` |
| Timeout on deploy | Ensure `FUNCTION_URL` and `DIGITALOCEAN_INFERENCE_KEY` are set as env vars in the deployed environment (`.env` is local only) |
