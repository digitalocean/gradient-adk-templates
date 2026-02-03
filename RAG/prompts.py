"""
Prompts for the RAG (Retrieval-Augmented Generation) Agent.

This file contains all the prompts used by the RAG pipeline:
- Document grading prompts
- Question rewriting prompts
- Answer generation prompts

Edit these prompts to customize how the agent retrieves, evaluates,
and synthesizes information from your documents.

Example customizations:
- Change the answer style (concise vs detailed)
- Add domain-specific grading criteria
- Modify how questions are rewritten
- Add citation requirements
"""

# =============================================================================
# DOCUMENT GRADING PROMPT
# =============================================================================

# Used to evaluate whether retrieved documents are relevant to the user's question
GRADE_PROMPT = (
    "You are a grader assessing relevance of a retrieved document to a user question. \n "
    "Here is the retrieved document: \n\n {context} \n\n"
    "Here is the user question: {question} \n"
    "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n"
    "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."
)


# =============================================================================
# QUESTION REWRITING PROMPT
# =============================================================================

# Used to reformulate questions when initial retrieval doesn't find relevant documents
REWRITE_PROMPT = (
    "Look at the input and try to reason about the underlying semantic intent / meaning.\n"
    "Here is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Formulate an improved question:"
)


# =============================================================================
# ANSWER GENERATION PROMPT
# =============================================================================

# Used to generate the final answer from retrieved context
GENERATE_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, just say that you don't know. "
    "Use three sentences maximum and keep the answer concise.\n"
    "Question: {question} \n"
    "Context: {context}"
)


# =============================================================================
# ALTERNATIVE PROMPTS (uncomment and modify for different use cases)
# =============================================================================

# Detailed Answer Generation (for technical documentation)
# GENERATE_PROMPT = (
#     "You are a technical documentation assistant. "
#     "Use the following retrieved context to answer the question thoroughly. "
#     "Provide step-by-step explanations when applicable. "
#     "If the context doesn't contain enough information, say so and explain what's missing.\n"
#     "Question: {question} \n"
#     "Context: {context}"
# )

# Citation-focused Answer Generation
# GENERATE_PROMPT = (
#     "You are a research assistant that provides well-cited answers. "
#     "Use the retrieved context to answer the question. "
#     "Reference specific parts of the documents in your answer. "
#     "If you don't have enough information, acknowledge the limitations.\n"
#     "Question: {question} \n"
#     "Context: {context}"
# )

# Conversational Answer Generation
# GENERATE_PROMPT = (
#     "You are a friendly assistant helping users understand documents. "
#     "Based on the context provided, answer the question in a conversational tone. "
#     "If the information isn't in the documents, be honest and suggest what else might help.\n"
#     "Question: {question} \n"
#     "Context: {context}"
# )

# Strict Relevance Grading (for high-precision retrieval)
# GRADE_PROMPT = (
#     "You are a strict grader assessing relevance of a retrieved document to a user question. \n "
#     "Here is the retrieved document: \n\n {context} \n\n"
#     "Here is the user question: {question} \n"
#     "The document must directly answer the question or contain key information needed. "
#     "Tangentially related content should be graded as 'no'. \n"
#     "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant."
# )
