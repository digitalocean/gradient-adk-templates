"""
NL2SQL Agent - Natural Language to SQL Translation.

This agent translates natural language questions into SQL queries,
executes them against the database, and formats the results.
"""

import os
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient

logger = logging.getLogger(__name__)

# Model configuration
MODEL = "openai-gpt-4.1"


def get_model(temperature: float = 0.0) -> ChatGradient:
    """Get a ChatGradient instance."""
    return ChatGradient(
        model=MODEL,
        temperature=temperature
    )


class SQLQuery(BaseModel):
    """Generated SQL query with explanation."""
    query: str = Field(description="The SQL SELECT query to execute")
    explanation: str = Field(description="Brief explanation of what the query does")
    tables_used: list[str] = Field(description="List of tables used in the query")


class QueryResult(BaseModel):
    """Result of a SQL query execution."""
    success: bool
    query: str
    explanation: str
    data: Optional[Dict[str, Any]] = None
    formatted_result: Optional[str] = None
    error: Optional[str] = None
    row_count: int = 0


def get_schema_prompt(schema_info: Dict[str, Any]) -> str:
    """
    Format database schema information for the LLM prompt.

    Args:
        schema_info: Database schema information

    Returns:
        Formatted schema description
    """
    lines = ["Database Schema:", ""]

    for table_name, table_info in schema_info.get("tables", {}).items():
        lines.append(f"Table: {table_name}")
        for col in table_info.get("columns", []):
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            lines.append(f"  - {col['name']} ({col['type']}) {nullable}")
        lines.append("")

    return "\n".join(lines)


def create_nl2sql_prompt(question: str, schema_info: Dict[str, Any]) -> str:
    """
    Create the prompt for NL2SQL translation.

    Args:
        question: Natural language question
        schema_info: Database schema information

    Returns:
        Formatted prompt
    """
    schema_text = get_schema_prompt(schema_info)

    prompt = f"""You are a SQL expert. Your task is to translate natural language questions into SQL queries.

{schema_text}

Important guidelines:
1. Only generate SELECT queries - no INSERT, UPDATE, DELETE, or other modifications
2. Use appropriate JOINs when data spans multiple tables
3. Use aliases for clarity when joining tables
4. Add appropriate WHERE clauses to filter data
5. Use GROUP BY and aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
6. Add ORDER BY for meaningful result ordering
7. Use LIMIT to prevent returning too many rows (default: 100)
8. Handle NULL values appropriately
9. Use appropriate date/time functions for temporal queries

User Question: {question}

Generate a SQL query to answer this question. Respond with:
1. The SQL query
2. A brief explanation of what it does
3. The tables used"""

    return prompt


def generate_sql(question: str, schema_info: Dict[str, Any]) -> SQLQuery:
    """
    Generate SQL from natural language using the LLM.

    Args:
        question: Natural language question
        schema_info: Database schema information

    Returns:
        Generated SQL query
    """
    logger.info(f"Generating SQL for question: {question}")

    prompt = create_nl2sql_prompt(question, schema_info)

    model = get_model(temperature=0.0)
    structured_model = model.with_structured_output(SQLQuery)

    sql_query = structured_model.invoke([
        {"role": "system", "content": "You are a SQL expert that translates natural language to SQL queries."},
        {"role": "user", "content": prompt}
    ])

    logger.info(f"Generated SQL: {sql_query.query}")

    return sql_query


def execute_nl2sql(
    question: str,
    db_connection,
    max_retries: int = 5
) -> QueryResult:
    """
    Complete NL2SQL pipeline: translate question, execute query, format results.

    If the query fails, the agent will attempt to fix and retry up to max_retries times.

    Args:
        question: Natural language question
        db_connection: Database connection instance
        max_retries: Maximum number of retry attempts for failed queries (default: 5)

    Returns:
        Query result with data and formatted output
    """
    from tools.database import format_results_as_table

    try:
        # Get schema information
        schema_info = db_connection.get_schema_info()

        # Generate initial SQL query
        sql_query = generate_sql(question, schema_info)
        current_query = sql_query.query
        current_explanation = sql_query.explanation

        # Track all attempts for debugging
        attempts = []

        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                logger.info(f"Executing query (attempt {attempt + 1}/{max_retries + 1}): {current_query[:100]}...")

                # Execute the query
                result = db_connection.execute_query(current_query)

                # Format the results
                formatted = format_results_as_table(result)

                if attempt > 0:
                    logger.info(f"Query succeeded after {attempt + 1} attempts")

                return QueryResult(
                    success=True,
                    query=current_query,
                    explanation=current_explanation,
                    data=result,
                    formatted_result=formatted,
                    row_count=result["row_count"]
                )

            except Exception as query_error:
                error_msg = str(query_error)
                attempts.append({
                    "attempt": attempt + 1,
                    "query": current_query,
                    "error": error_msg
                })

                logger.warning(f"Query attempt {attempt + 1} failed: {error_msg}")

                # If we have retries left, try to fix the query
                if attempt < max_retries:
                    logger.info(f"Attempting to fix query (retry {attempt + 1}/{max_retries})...")
                    try:
                        fixed_query = validate_and_fix_sql(
                            current_query,
                            error_msg,
                            schema_info
                        )
                        current_query = fixed_query.query
                        current_explanation = fixed_query.explanation
                        logger.info(f"Generated fixed query: {current_query[:100]}...")
                    except Exception as fix_error:
                        logger.error(f"Failed to generate fixed query: {fix_error}")
                        # Continue to next iteration, which will fail if this was the last retry
                else:
                    # All retries exhausted
                    logger.error(f"All {max_retries + 1} attempts failed")

                    # Build detailed error message
                    error_details = f"Query failed after {max_retries + 1} attempts.\n\n"
                    error_details += "Attempt history:\n"
                    for att in attempts:
                        error_details += f"  Attempt {att['attempt']}: {att['error'][:100]}...\n"

                    return QueryResult(
                        success=False,
                        query=current_query,
                        explanation=current_explanation,
                        error=error_details
                    )

        # Should not reach here, but just in case
        return QueryResult(
            success=False,
            query=current_query,
            explanation=current_explanation,
            error="Query execution failed unexpectedly"
        )

    except Exception as e:
        logger.error(f"NL2SQL execution failed: {e}")
        return QueryResult(
            success=False,
            query="",
            explanation="",
            error=str(e)
        )


def validate_and_fix_sql(
    original_query: str,
    error_message: str,
    schema_info: Dict[str, Any]
) -> SQLQuery:
    """
    Attempt to fix a SQL query that produced an error.

    Args:
        original_query: The query that failed
        error_message: The error message received
        schema_info: Database schema information

    Returns:
        Fixed SQL query
    """
    schema_text = get_schema_prompt(schema_info)

    prompt = f"""The following SQL query produced an error. Please fix it.

{schema_text}

Original Query:
{original_query}

Error Message:
{error_message}

Please provide a corrected SQL query that addresses the error. Remember:
1. Only SELECT queries are allowed
2. Check table and column names against the schema
3. Ensure proper syntax for the database type"""

    model = get_model(temperature=0.0)
    structured_model = model.with_structured_output(SQLQuery)

    return structured_model.invoke([
        {"role": "system", "content": "You are a SQL expert that fixes SQL queries."},
        {"role": "user", "content": prompt}
    ])
