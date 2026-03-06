"""
Prompt templates for the Customer Support Agent.

This file defines the LangChain PromptTemplates used by the agent.
The prompt_manager loads optimized versions of these fields from prompt_versions/.

Customization:
- Edit BASELINE_SYSTEM_INSTRUCTION to change the default behavior
- Edit CATEGORY_DEFINITIONS to add/remove/rename categories
- Edit RESPONSE_GUIDELINES to change response style
- Run `python optimize.py` to automatically optimize these prompts with DSPy
"""

from langchain_core.prompts import ChatPromptTemplate

# =============================================================================
# CONFIGURABLE PROMPT COMPONENTS
# =============================================================================

BASELINE_SYSTEM_INSTRUCTION = (
    "You are a customer support agent. Classify the customer's email into one of "
    "the provided categories and write a helpful response."
)

CATEGORY_DEFINITIONS = """Categories:
- billing: Payment issues, charges, refunds, invoices, pricing questions
- technical: Bugs, errors, performance issues, configuration problems, API issues
- account: Account settings, access, permissions, security, profile changes
- general: Product questions, feature inquiries, comparisons, documentation requests"""

RESPONSE_GUIDELINES = """Guidelines for your response:
- Be empathetic and professional
- Acknowledge the customer's concern
- Provide actionable next steps
- Keep responses concise but thorough
- If you need more information, ask specific questions"""

# =============================================================================
# PROMPT TEMPLATE ASSEMBLY
# =============================================================================

SYSTEM_TEMPLATE = """{system_instruction}

{category_definitions}

{response_guidelines}

{few_shot_examples}"""

HUMAN_TEMPLATE = """Customer email:
{email_text}

Respond with the category on the first line as "Category: <category>" followed by your response."""


def build_prompt(
    system_instruction: str = BASELINE_SYSTEM_INSTRUCTION,
    category_definitions: str = CATEGORY_DEFINITIONS,
    response_guidelines: str = RESPONSE_GUIDELINES,
    few_shot_examples: str = "",
) -> ChatPromptTemplate:
    """Build a ChatPromptTemplate from the given components."""
    system_content = SYSTEM_TEMPLATE.format(
        system_instruction=system_instruction,
        category_definitions=category_definitions,
        response_guidelines=response_guidelines,
        few_shot_examples=few_shot_examples,
    ).strip()

    return ChatPromptTemplate.from_messages([
        ("system", system_content),
        ("human", HUMAN_TEMPLATE),
    ])
