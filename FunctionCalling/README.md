# FunctionCalling - Serverless Function Agent

A minimal agent that invokes a DigitalOcean Serverless Function as a tool. This is the simplest way to connect an LLM agent to your own custom backend logic running on DigitalOcean Functions.

## Project Layout

This template is split into two folders to keep the function setup code out of the agent deployment:

```
FunctionCalling/
├── Setup/                       # Function deployment (not included in agent deploy)
│   ├── setup.sh                 #   One-command script to deploy the sample function
│   └── sample_function/         #   Sample unit converter DO serverless function
│       ├── project.yml
│       └── packages/converter/convert/__main__.py
│
└── Agent/                       # Agent code (this is what gets deployed)
    ├── .gradient/agent.yml      #   Gradient ADK deployment config
    ├── main.py                  #   Entry point — builds tool from config, runs agent
    ├── function_config.py       #   ★ Edit this to connect to YOUR function
    ├── prompts.py               #   System prompt (edit to customize behavior)
    ├── requirements.txt         #   Python dependencies
    └── .env.example             #   Environment variable template
```

**`Setup/`** contains the setup script and sample serverless function. Run `setup.sh` once to deploy the sample function and configure the agent's `.env`. This folder is not part of the agent deployment — it's purely for bootstrapping.

**`Agent/`** contains the agent code that gets deployed via `gradient agent deploy`. Edit `function_config.py` to point the agent at any serverless function, and `prompts.py` to customize the agent's behavior.

## Quick Start

### 1. Deploy the sample function

```bash
cd Setup
bash setup.sh
```

This deploys a unit converter to DigitalOcean Functions and saves the URL to `Agent/.env`.

### 2. Set up the agent

```bash
cd Agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Add your credentials to `Agent/.env`:

```
FUNCTION_URL=<auto-filled by setup.sh>
DIGITALOCEAN_API_TOKEN=your_token
DIGITALOCEAN_INFERENCE_KEY=your_key
```

### 3. Run locally

```bash
cd Agent
gradient agent run
```

### 4. Test it

```bash
curl http://localhost:8080/run \
    -H 'Content-Type: application/json' \
    -d '{"prompt": "Convert 72 fahrenheit to celsius"}'
```

### 5. Deploy

```bash
cd Agent
gradient agent deploy
```

## Connecting Your Own Function

1. Deploy any function to DigitalOcean Functions
2. Edit `Agent/function_config.py` with your function's name, URL, parameters, and response schema
3. Optionally edit `Agent/prompts.py` to tailor the agent's behavior

See [`Agent/README.md`](Agent/README.md) for full details on configuration, customization examples, and troubleshooting.

## Cleaning Up

To remove the sample function:

```bash
doctl serverless undeploy converter/convert
```

## Resources

- [DigitalOcean Functions Docs](https://docs.digitalocean.com/products/functions/)
- [doctl Serverless Reference](https://docs.digitalocean.com/reference/doctl/reference/serverless/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Gradient ADK Documentation](https://docs.digitalocean.com/products/gradient/adk/)
