"""
Prompt templates for the Customer Support Agent.

This file defines the LangChain PromptTemplates used by the agent.
The prompt_manager loads optimized versions of these fields from prompt_versions/.

Customization:
- Edit BASELINE_SYSTEM_INSTRUCTION to change the default behavior and response style
- Edit CATEGORY_LABELS to add/remove/rename categories
- Run `python optimize.py` to automatically optimize these prompts with DSPy
"""

from langchain_core.prompts import ChatPromptTemplate

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# The model the agent uses at inference. A smaller, cheaper model whose
# baseline performance DSPy optimization improves.
TASK_MODEL = "openai-gpt-oss-20b"

# A stronger model used as the MIPROv2 proposer (generates candidate
# instructions) and the LLM-as-judge during evaluation. Only used during
# optimization and evaluation, not at inference.
JUDGE_MODEL = "openai-gpt-oss-120b"

# =============================================================================
# CONFIGURABLE PROMPT COMPONENTS
# =============================================================================

BASELINE_SYSTEM_INSTRUCTION = (
    "You are a customer support agent. Classify the customer's email into one of "
    "the provided categories and write a helpful response."
)

# The category labels and response format are fixed so the parser in main.py
# can always match on them. DSPy can add its own definitions of what each
# category means during optimization — the labels and format never change.
CATEGORY_LABELS = """Categories: billing, technical, account, general"""

RESPONSE_FORMAT = """Response format:
Category: <category>
Response: <response>"""

# =============================================================================
# PROMPT TEMPLATE ASSEMBLY
# =============================================================================

SYSTEM_TEMPLATE = """{system_instruction}

{category_labels}

{response_format}

{few_shot_examples}"""

HUMAN_TEMPLATE = """Customer email:
{email_text}"""


def build_prompt(
    system_instruction: str = BASELINE_SYSTEM_INSTRUCTION,
    category_labels: str = CATEGORY_LABELS,
    response_format: str = RESPONSE_FORMAT,
    few_shot_examples: str = "",
) -> ChatPromptTemplate:
    """Build a ChatPromptTemplate from the given components."""
    system_content = SYSTEM_TEMPLATE.format(
        system_instruction=system_instruction,
        category_labels=category_labels,
        response_format=response_format,
        few_shot_examples=few_shot_examples,
    ).strip()

    return ChatPromptTemplate.from_messages([
        ("system", system_content),
        ("human", HUMAN_TEMPLATE),
    ])
