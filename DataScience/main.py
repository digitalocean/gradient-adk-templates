"""
Data Science Agent - Main Workflow

A data science agent that can:
1. Translate natural language questions into SQL queries
2. Execute queries against PostgreSQL or MySQL databases
3. Perform data analysis with Python code
4. Generate visualizations and charts

Uses LangGraph for workflow orchestration and Gradient ADK for deployment.
"""

import os
import logging
from typing import TypedDict, Optional, List, Literal, Annotated
from pydantic import BaseModel, Field
from langchain_gradient import ChatGradient
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from gradient_adk import entrypoint

from tools.database import DatabaseConnection, get_schema, format_results_as_table
from agents.nl2sql import execute_nl2sql, QueryResult
from agents.data_analyst import run_analysis, AnalysisResult

# Import prompts - edit prompts.py to customize agent behavior
from prompts import (
    get_intent_classification_prompt,
    INTENT_CLASSIFIER_SYSTEM,
    QUERY_SUMMARIZER_SYSTEM,
    get_query_summary_prompt,
    ANALYSIS_SUMMARIZER_SYSTEM,
    get_analysis_summary_prompt,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Model configuration
MODEL = "openai-gpt-4.1"

# Query retry configuration
DEFAULT_MAX_QUERY_RETRIES = 5


def get_model(temperature: float = 0.0) -> ChatGradient:
    """Get a ChatGradient instance."""
    return ChatGradient(
        model=MODEL,
        temperature=temperature
    )


# =============================================================================
# State and Response Models
# =============================================================================

class ImageData(BaseModel):
    """Image data for visualizations."""
    base64_data: str = Field(description="Base64 encoded image data")
    file_path: Optional[str] = Field(default=None, description="Path to saved image file")
    mime_type: str = Field(default="image/png", description="Image MIME type")


class AgentResponse(BaseModel):
    """Final response from the agent."""
    summary: str = Field(description="Text summary/explanation for the user")
    sql_query: Optional[str] = Field(default=None, description="SQL query that was executed")
    data_table: Optional[str] = Field(default=None, description="Formatted data table")
    analysis_code: Optional[str] = Field(default=None, description="Python analysis code that was run")
    images: List[ImageData] = Field(default_factory=list, description="Generated visualizations")
    error: Optional[str] = Field(default=None, description="Error message if something failed")


class DataScienceState(TypedDict, total=False):
    """State for the data science workflow."""
    # Input
    message: str

    # Configuration
    max_query_retries: int  # Max retries for failed SQL queries (default: 5)

    # Intent classification
    intent: str  # "query", "analyze", "visualize", "schema", "help"
    needs_visualization: bool

    # Database (schema_info is serializable, connection is created on demand)
    schema_info: Optional[dict]

    # Query execution
    query_result: Optional[QueryResult]
    query_data: Optional[dict]

    # Analysis
    analysis_result: Optional[AnalysisResult]

    # Output
    response: Optional[AgentResponse]
    error: Optional[str]


# Module-level database connection (not stored in state)
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """Get or create the database connection."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
        _db_connection.connect()
    return _db_connection


# =============================================================================
# Intent Classification
# =============================================================================

class UserIntent(BaseModel):
    """Classified user intent."""
    intent: Literal["query", "analyze", "visualize", "schema", "help"]
    needs_visualization: bool = Field(description="Whether the request needs a chart or graph")
    rephrased_question: str = Field(description="Clear question for processing")


def classify_intent(state: DataScienceState) -> DataScienceState:
    """Classify the user's intent from their message."""
    message = state["message"]
    logger.info(f"Classifying intent for: {message[:100]}...")

    prompt = get_intent_classification_prompt(message)

    model = get_model(temperature=0.0)
    structured_model = model.with_structured_output(UserIntent)

    intent = structured_model.invoke([
        {"role": "system", "content": INTENT_CLASSIFIER_SYSTEM},
        {"role": "user", "content": prompt}
    ])

    logger.info(f"Classified intent: {intent.intent}, needs_visualization: {intent.needs_visualization}")

    return {
        **state,
        "intent": intent.intent,
        "needs_visualization": intent.needs_visualization or intent.intent == "visualize",
        "message": intent.rephrased_question
    }


# =============================================================================
# Database Operations
# =============================================================================

def connect_database(state: DataScienceState) -> DataScienceState:
    """Connect to the database and get schema info."""
    logger.info("Connecting to database...")

    try:
        db = get_db_connection()
        schema_info = db.get_schema_info()

        logger.info(f"Connected. Found {len(schema_info.get('tables', {}))} tables")

        return {
            **state,
            "schema_info": schema_info
        }
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return {
            **state,
            "error": f"Failed to connect to database: {str(e)}"
        }


def execute_query(state: DataScienceState) -> DataScienceState:
    """Execute NL2SQL query with automatic retry on failure."""
    message = state["message"]
    max_retries = state.get("max_query_retries", DEFAULT_MAX_QUERY_RETRIES)

    try:
        db = get_db_connection()
    except Exception as e:
        return {**state, "error": f"No database connection: {str(e)}"}

    logger.info(f"Executing NL2SQL for: {message[:100]}... (max retries: {max_retries})")

    result = execute_nl2sql(message, db, max_retries=max_retries)

    if result.success:
        logger.info(f"Query returned {result.row_count} rows")
        return {
            **state,
            "query_result": result,
            "query_data": result.data
        }
    else:
        logger.error(f"Query failed after retries: {result.error}")
        return {
            **state,
            "query_result": result,
            "error": result.error
        }


def run_data_analysis(state: DataScienceState) -> DataScienceState:
    """Run data analysis with Python code."""
    message = state["message"]
    query_data = state.get("query_data")
    schema_info = state.get("schema_info", {})

    if not query_data:
        logger.warning("No query data available for analysis")
        return {**state, "error": "No data available for analysis. Please query data first."}

    # Create data description
    data_description = f"""
Database schema has tables: {list(schema_info.get('tables', {}).keys())}

Current data from query:
- Columns: {query_data.get('columns', [])}
- Row count: {query_data.get('row_count', 0)}
"""

    logger.info(f"Running analysis: {message[:100]}...")

    result = run_analysis(message, query_data, data_description)

    return {
        **state,
        "analysis_result": result
    }


# =============================================================================
# Response Generation
# =============================================================================

def generate_schema_response(state: DataScienceState) -> DataScienceState:
    """Generate response for schema queries."""
    # Fetch schema directly from database
    try:
        db = get_db_connection()
        schema_info = db.get_schema_info()
    except Exception as e:
        return {
            **state,
            "response": AgentResponse(
                summary=f"Failed to get schema: {str(e)}",
                error=str(e)
            )
        }

    lines = ["**Database Schema**\n"]
    for table_name, table_info in schema_info.get("tables", {}).items():
        lines.append(f"\n**{table_name}**")
        for col in table_info.get("columns", []):
            nullable = "(nullable)" if col["nullable"] else ""
            lines.append(f"  - `{col['name']}` {col['type']} {nullable}")

    summary = "\n".join(lines)

    return {
        **state,
        "response": AgentResponse(summary=summary)
    }


def generate_help_response(state: DataScienceState) -> DataScienceState:
    """Generate help response."""
    summary = """**Data Science Agent Help**

I can help you with:

1. **Query Data**: Ask questions about the database in natural language
   - "Show me all flights from JFK to LAX"
   - "How many customers are in the Gold tier?"

2. **Analyze Data**: Get insights and statistics
   - "What's the average flight delay by month?"
   - "Which routes have the highest revenue?"

3. **Visualize Data**: Create charts and graphs
   - "Create a chart showing delays by airport"
   - "Plot monthly revenue trends"

4. **Schema Info**: Learn about the database structure
   - "What tables are available?"
   - "Show me the schema"

The database contains airline data including:
- Flights and schedules
- Airports
- Aircraft
- Customers and loyalty programs
- Tickets and sales

Just ask your question in plain English!"""

    return {
        **state,
        "response": AgentResponse(summary=summary)
    }


def generate_query_response(state: DataScienceState) -> DataScienceState:
    """Generate response for query results."""
    query_result = state.get("query_result")

    if not query_result:
        return {
            **state,
            "response": AgentResponse(
                summary="No query was executed.",
                error=state.get("error")
            )
        }

    if not query_result.success:
        return {
            **state,
            "response": AgentResponse(
                summary=f"Query failed: {query_result.error}",
                error=query_result.error
            )
        }

    # Generate summary using LLM
    prompt = get_query_summary_prompt(
        question=state.get('message', ''),
        query=query_result.query,
        row_count=query_result.row_count,
        formatted_result=query_result.formatted_result
    )

    model = get_model(temperature=0.3)
    response = model.invoke([
        {"role": "system", "content": QUERY_SUMMARIZER_SYSTEM},
        {"role": "user", "content": prompt}
    ])

    summary = response.content

    return {
        **state,
        "response": AgentResponse(
            summary=summary,
            sql_query=query_result.query,
            data_table=query_result.formatted_result
        )
    }


def generate_analysis_response(state: DataScienceState) -> DataScienceState:
    """Generate response for analysis results."""
    analysis_result = state.get("analysis_result")
    query_result = state.get("query_result")

    if not analysis_result:
        return {
            **state,
            "response": AgentResponse(
                summary="Analysis could not be completed.",
                error=state.get("error")
            )
        }

    # Prepare images
    images = []
    if analysis_result.images:
        for i, img_data in enumerate(analysis_result.images):
            image_path = analysis_result.image_paths[i] if i < len(analysis_result.image_paths) else None
            images.append(ImageData(
                base64_data=img_data,
                file_path=image_path
            ))

    if not analysis_result.success:
        return {
            **state,
            "response": AgentResponse(
                summary=f"Analysis failed: {analysis_result.error}",
                error=analysis_result.error,
                analysis_code=analysis_result.code
            )
        }

    # Generate summary
    prompt = get_analysis_summary_prompt(
        question=state.get('message', ''),
        explanation=analysis_result.explanation,
        output=analysis_result.output,
        has_visualization=bool(images)
    )

    model = get_model(temperature=0.3)
    response = model.invoke([
        {"role": "system", "content": ANALYSIS_SUMMARIZER_SYSTEM},
        {"role": "user", "content": prompt}
    ])

    summary = response.content

    return {
        **state,
        "response": AgentResponse(
            summary=summary,
            sql_query=query_result.query if query_result else None,
            analysis_code=analysis_result.code,
            images=images
        )
    }


def handle_error(state: DataScienceState) -> DataScienceState:
    """Handle errors and generate error response."""
    error = state.get("error", "An unknown error occurred")

    return {
        **state,
        "response": AgentResponse(
            summary=f"I encountered an error: {error}",
            error=error
        )
    }


# =============================================================================
# Routing
# =============================================================================

def route_by_intent(state: DataScienceState) -> str:
    """Route to appropriate node based on intent."""
    if state.get("error"):
        return "handle_error"

    intent = state.get("intent", "help")

    if intent == "schema":
        return "generate_schema_response"
    elif intent == "help":
        return "generate_help_response"
    else:
        return "connect_database"


def route_after_query(state: DataScienceState) -> str:
    """Route after query execution."""
    if state.get("error"):
        return "handle_error"

    if state.get("needs_visualization") or state.get("intent") in ["analyze", "visualize"]:
        return "run_analysis"
    else:
        return "generate_query_response"


def route_after_analysis(state: DataScienceState) -> str:
    """Route after analysis."""
    if state.get("error") and not state.get("analysis_result"):
        return "handle_error"
    return "generate_analysis_response"


# =============================================================================
# Workflow Definition
# =============================================================================

def create_workflow():
    """Create the LangGraph workflow."""
    workflow = StateGraph(DataScienceState)

    # Add nodes
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("connect_database", connect_database)
    workflow.add_node("execute_query", execute_query)
    workflow.add_node("run_analysis", run_data_analysis)
    workflow.add_node("generate_schema_response", generate_schema_response)
    workflow.add_node("generate_help_response", generate_help_response)
    workflow.add_node("generate_query_response", generate_query_response)
    workflow.add_node("generate_analysis_response", generate_analysis_response)
    workflow.add_node("handle_error", handle_error)

    # Define edges
    workflow.add_edge(START, "classify_intent")

    workflow.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "generate_schema_response": "generate_schema_response",
            "generate_help_response": "generate_help_response",
            "connect_database": "connect_database",
            "handle_error": "handle_error"
        }
    )

    workflow.add_edge("connect_database", "execute_query")

    workflow.add_conditional_edges(
        "execute_query",
        route_after_query,
        {
            "run_analysis": "run_analysis",
            "generate_query_response": "generate_query_response",
            "handle_error": "handle_error"
        }
    )

    workflow.add_conditional_edges(
        "run_analysis",
        route_after_analysis,
        {
            "generate_analysis_response": "generate_analysis_response",
            "handle_error": "handle_error"
        }
    )

    # Terminal edges
    workflow.add_edge("generate_schema_response", END)
    workflow.add_edge("generate_help_response", END)
    workflow.add_edge("generate_query_response", END)
    workflow.add_edge("generate_analysis_response", END)
    workflow.add_edge("handle_error", END)

    return workflow


workflow = create_workflow()
app = workflow.compile()


# =============================================================================
# Entrypoint
# =============================================================================

@entrypoint
def main(input: dict) -> dict:
    """
    Data Science Agent entrypoint.

    Args:
        input: Dictionary with:
            - message: User's natural language question or request
            - thread_id: Optional thread ID for conversation continuity
            - max_query_retries: Optional max retries for failed SQL queries (default: 5)

    Returns:
        Response dictionary with summary, data, and any visualizations
    """
    message = input.get("message", "")
    max_query_retries = input.get("max_query_retries", DEFAULT_MAX_QUERY_RETRIES)

    if not message:
        return {
            "summary": "No message provided",
            "success": False,
            "error": "Input must include a 'message' key"
        }

    logger.info(f"Processing request: {message[:100]}...")

    # Run the workflow
    initial_state = {
        "message": message,
        "max_query_retries": max_query_retries
    }
    result = app.invoke(initial_state)

    # Extract response
    response = result.get("response")

    if response:
        output = {
            "summary": response.summary,
            "success": response.error is None
        }

        if response.sql_query:
            output["sql_query"] = response.sql_query

        if response.data_table:
            output["data_table"] = response.data_table

        if response.analysis_code:
            output["analysis_code"] = response.analysis_code

        if response.images:
            output["images"] = [
                {
                    "base64": img.base64_data,
                    "path": img.file_path,
                    "mime_type": img.mime_type
                }
                for img in response.images
            ]

        if response.error:
            output["error"] = response.error

        return output

    return {
        "summary": "Unable to process request",
        "success": False,
        "error": result.get("error", "Unknown error")
    }


if __name__ == "__main__":
    # Test the agent locally
    import sys

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "What tables are in the database?"

    result = main({"message": question})
    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"Summary: {result.get('summary')}")

    if result.get("sql_query"):
        print(f"\nSQL Query:\n{result.get('sql_query')}")

    if result.get("data_table"):
        print(f"\nData:\n{result.get('data_table')}")

    if result.get("images"):
        print(f"\nGenerated {len(result.get('images'))} visualization(s)")
        for img in result.get("images"):
            if img.get("path"):
                print(f"  - Saved to: {img.get('path')}")

    if result.get("error"):
        print(f"\nError: {result.get('error')}")
