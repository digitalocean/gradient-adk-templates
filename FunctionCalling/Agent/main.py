import os

import requests
from dotenv import load_dotenv

# Load .env before local imports so FUNCTION_URL is available in function_config.py
load_dotenv()

from gradient_adk import entrypoint
from langchain_core.messages import HumanMessage
from langchain_core.tools import StructuredTool
from langchain_gradient import ChatGradient
from langgraph.prebuilt import create_react_agent
from pydantic import Field, create_model

# Import prompts - edit prompts.py to customize agent behavior
from prompts import SYSTEM_PROMPT

# Import function config - edit function_config.py to connect to your function
from function_config import FUNCTION_CONFIG

# ---------------------------------------------------------------------------
# Dynamic tool builder - creates a LangChain tool from function_config.py
# ---------------------------------------------------------------------------

_TYPE_MAP = {
    "string": (str, ...),
    "number": (float, ...),
    "integer": (int, ...),
    "boolean": (bool, ...),
}


def _build_description(config: dict) -> str:
    """Build a full tool description including the response schema.

    The base description tells the LLM *when* to call the function.
    The response schema tells it *how to interpret* what comes back.
    """
    description = config["description"]

    response_schema = config.get("response_schema")
    if response_schema:
        parts = [f"  - {name}: {spec.get('description', '')}" for name, spec in response_schema.items()]
        description += "\n\nThe function returns a JSON object with these fields:\n" + "\n".join(parts)

    return description


def _build_tool(config: dict) -> StructuredTool:
    """Create a LangChain StructuredTool from a function config dict.

    This reads the parameter definitions and response schema in
    function_config.py and builds a Pydantic model + callable so the LLM
    can invoke your serverless function with the correct arguments and
    understand the response.
    """
    fields = {}
    for param_name, param_spec in config["parameters"].items():
        py_type = _TYPE_MAP.get(param_spec.get("type", "string"), (str, ...))[0]
        fields[param_name] = (
            py_type,
            Field(description=param_spec.get("description", "")),
        )

    ArgsModel = create_model(f"{config['name']}_Args", **fields)

    url = config["url"]
    if not url:
        raise ValueError(
            "FUNCTION_URL is not set. Run `bash ../Setup/setup.sh` to deploy "
            "the sample function, or set FUNCTION_URL in your .env file."
        )

    def call_function(**kwargs) -> dict:
        response = requests.post(url, json=kwargs, timeout=30)
        response.raise_for_status()
        return response.json()

    return StructuredTool(
        name=config["name"],
        description=_build_description(config),
        func=call_function,
        args_schema=ArgsModel,
    )


def _build_agent():
    """Build the tool and agent. Deferred so import-time errors don't silently
    kill the process (which surfaces as a timeout in deployed environments)."""
    tool = _build_tool(FUNCTION_CONFIG)
    llm = ChatGradient(model="openai-gpt-4.1")
    return create_react_agent(model=llm, tools=[tool], prompt=SYSTEM_PROMPT)


# Lazy-initialized at first request
_agent = None


@entrypoint
async def entry(data, context):
    global _agent
    if _agent is None:
        _agent = _build_agent()

    query = data.get("prompt") or data.get("messages", "")
    # Handle nested input shapes (e.g. {"prompt": {"messages": "..."}})
    if isinstance(query, dict):
        query = query.get("messages") or query.get("content") or str(query)
    inputs = {"messages": [HumanMessage(content=query)]}
    result = await _agent.ainvoke(inputs)
    return {"response": result["messages"][-1].content}
