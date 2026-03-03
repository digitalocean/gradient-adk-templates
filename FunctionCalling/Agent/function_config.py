"""
Configuration for your DigitalOcean Serverless Function.

This is the ONLY file you need to edit to connect the agent to your function.
Update the fields below to match your deployed function, and the agent will
automatically create a tool the LLM can call.

Quick start:
  1. Run Setup/setup.sh to deploy the sample function (sets FUNCTION_URL for you)
  2. Or set FUNCTION_URL in your .env and edit the config below

To connect your own function:
  1. Set "url" to your function's web URL
  2. Set "name" to a short, descriptive tool name
  3. Write a clear "description" so the LLM knows when to use it
  4. List each input parameter with its type and description
  5. Describe the response fields so the LLM can interpret the output
"""

import os

FUNCTION_CONFIG = {
    # A short name for this tool (used internally by the LLM)
    "name": "unit_converter",

    # The web URL of your deployed DigitalOcean serverless function.
    # Run `bash ../Setup/setup.sh` to deploy the sample function and set this
    # automatically, or paste your own function URL here.
    "url": os.environ.get("FUNCTION_URL", ""),

    # Describe what your function does. Be specific - the LLM reads this to decide
    # when to call the function vs. answering on its own.
    "description": (
        "Convert between different units of measurement. "
        "Supports temperature (celsius, fahrenheit, kelvin), "
        "distance (miles, kilometers, meters, feet), "
        "and weight (pounds, kilograms, grams, ounces)."
    ),

    # Define every input parameter your function accepts.
    # Supported types: "string", "number", "integer", "boolean"
    "parameters": {
        "value": {
            "type": "number",
            "description": "The numeric value to convert",
            "required": True,
        },
        "from_unit": {
            "type": "string",
            "description": "The source unit (e.g., 'celsius', 'miles', 'pounds')",
            "required": True,
        },
        "to_unit": {
            "type": "string",
            "description": "The target unit (e.g., 'fahrenheit', 'kilometers', 'kilograms')",
            "required": True,
        },
    },

    # Describe the fields your function returns.
    # This tells the LLM how to interpret and present the response to the user.
    "response_schema": {
        "original_value": {
            "type": "number",
            "description": "The original input value",
        },
        "from_unit": {
            "type": "string",
            "description": "The source unit",
        },
        "to_unit": {
            "type": "string",
            "description": "The target unit",
        },
        "converted_value": {
            "type": "number",
            "description": "The converted result value",
        },
    },
}
