"""
Prompts for the DataScience NL2SQL Agent.

This file contains all the prompts used in the data science pipeline:
- Intent classification
- SQL query generation
- SQL query error recovery
- Data analysis code generation
- Result summarization

Edit these prompts to customize the agent's behavior for your database schema,
domain, or output style.

Example customizations:
- Add domain-specific SQL patterns for your database
- Change the analysis output format
- Add company-specific data handling rules
- Modify visualization preferences
"""

# =============================================================================
# INTENT CLASSIFICATION
# =============================================================================

def get_intent_classification_prompt(message: str) -> str:
    """Generate the prompt for classifying user intent."""
    return f"""Analyze this user message and classify their intent for a data science agent.

User message: {message}

Classify as one of:
- "query": User wants to retrieve data from the database (e.g., "show me all flights", "how many customers")
- "analyze": User wants analysis of data (e.g., "what's the average delay", "find patterns")
- "visualize": User explicitly wants a chart, graph, or visualization
- "schema": User wants to know about the database structure
- "help": User needs help or has a general question

Also determine if the request would benefit from a visualization (charts, graphs, plots).
Rephrase the question clearly for processing."""

INTENT_CLASSIFIER_SYSTEM = "You classify user intent for a data science agent."


# =============================================================================
# SQL GENERATION PROMPTS
# =============================================================================

SQL_GENERATOR_SYSTEM = "You are a SQL expert that translates natural language to SQL queries."

SQL_GUIDELINES = """Important guidelines:
1. Only generate SELECT queries - no INSERT, UPDATE, DELETE, or other modifications
2. Use appropriate JOINs when data spans multiple tables
3. Use aliases for clarity when joining tables
4. Add appropriate WHERE clauses to filter data
5. Use GROUP BY and aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
6. Add ORDER BY for meaningful result ordering
7. Use LIMIT to prevent returning too many rows (default: 100)
8. Handle NULL values appropriately
9. Use appropriate date/time functions for temporal queries"""


def get_nl2sql_prompt(question: str, schema_text: str) -> str:
    """Generate the prompt for NL2SQL translation."""
    return f"""You are a SQL expert. Your task is to translate natural language questions into SQL queries.

{schema_text}

{SQL_GUIDELINES}

User Question: {question}

Generate a SQL query to answer this question. Respond with:
1. The SQL query
2. A brief explanation of what it does
3. The tables used"""


# =============================================================================
# SQL ERROR RECOVERY
# =============================================================================

SQL_FIXER_SYSTEM = "You are a SQL expert that fixes SQL queries."


def get_sql_fix_prompt(original_query: str, error_message: str, schema_text: str) -> str:
    """Generate the prompt for fixing a failed SQL query."""
    return f"""The following SQL query produced an error. Please fix it.

{schema_text}

Original Query:
{original_query}

Error Message:
{error_message}

Please provide a corrected SQL query that addresses the error. Remember:
1. Only SELECT queries are allowed
2. Check table and column names against the schema
3. Ensure proper syntax for the database type"""


# =============================================================================
# DATA ANALYSIS PROMPTS
# =============================================================================

ANALYSIS_CODE_GENERATOR_SYSTEM = "You are a data analyst writing Python code for analysis and visualization."


def get_analysis_prompt(question: str, data_description: str, data_context: str = "") -> str:
    """Generate the prompt for data analysis code generation."""
    return f"""You are a data analyst writing Python code for analysis and visualization.

{data_description}
{data_context}

Task: {question}

Write Python code to answer this question. Guidelines:
1. Use pandas for data manipulation
2. Use matplotlib or seaborn for visualizations
3. The data is already loaded in a variable called 'data' (pandas DataFrame)
4. If creating a visualization, save it using plt.savefig(output_path) where output_path is provided
5. Print any numerical results or insights
6. Keep the code concise and focused
7. Add brief comments for clarity
8. Handle potential errors gracefully
9. For visualizations:
   - Use clear titles and labels
   - Choose appropriate chart types
   - Use a clean style (seaborn or matplotlib styles)
   - Set figure size appropriately

Important: The variable 'data' contains the query results as a pandas DataFrame.
The variable 'output_path' contains the path where any visualization should be saved.

Generate only the Python code, no markdown formatting."""


ANALYSIS_FIXER_SYSTEM = "You are a data analyst fixing Python code."


def get_analysis_fix_prompt(original_code: str, error_message: str, data_description: str) -> str:
    """Generate the prompt for fixing failed analysis code."""
    return f"""The following Python code produced an error. Please fix it.

{data_description}

Original Code:
```python
{original_code}
```

Error:
{error_message}

Please provide corrected Python code that addresses the error. Maintain the same
analysis goal but fix the issues."""


# =============================================================================
# RESULT SUMMARIZATION
# =============================================================================

QUERY_SUMMARIZER_SYSTEM = "You summarize data query results concisely."


def get_query_summary_prompt(question: str, query: str, row_count: int, formatted_result: str) -> str:
    """Generate the prompt for summarizing query results."""
    return f"""Summarize these query results for the user.

Question: {question}

Query: {query}

Results ({row_count} rows):
{formatted_result}

Provide a brief, helpful summary of what the data shows."""


ANALYSIS_SUMMARIZER_SYSTEM = "You summarize data analysis results concisely and insightfully."


def get_analysis_summary_prompt(question: str, explanation: str, output: str, has_visualization: bool) -> str:
    """Generate the prompt for summarizing analysis results."""
    vis_note = "A visualization was generated." if has_visualization else "No visualization was created."
    return f"""Summarize these analysis results for the user.

Question: {question}

Analysis explanation: {explanation}

Output:
{output}

{vis_note}

Provide a clear summary of the insights and findings."""


# =============================================================================
# ALTERNATIVE PROMPTS (uncomment and modify for different use cases)
# =============================================================================

# Stricter SQL Generation (for sensitive databases)
# SQL_GUIDELINES = """Important guidelines:
# 1. Only generate SELECT queries - absolutely no modifications
# 2. Always include a LIMIT clause (max 1000 rows)
# 3. Never select * - always specify columns explicitly
# 4. Avoid expensive operations like CROSS JOIN
# 5. Do not access system tables or metadata
# ..."""

# Business-focused Summarization
# def get_query_summary_prompt(question: str, query: str, row_count: int, formatted_result: str) -> str:
#     return f"""Summarize these query results for a business stakeholder.
#
# Focus on:
# - Key insights and trends
# - Business implications
# - Actionable recommendations
# - Comparison to benchmarks if applicable
#
# Question: {question}
# ..."""

# Technical Analysis Style
# def get_analysis_summary_prompt(...) -> str:
#     return """Provide a technical analysis summary including:
# - Statistical measures (mean, median, std dev)
# - Data quality observations
# - Confidence intervals where applicable
# - Recommendations for further analysis
# ..."""
