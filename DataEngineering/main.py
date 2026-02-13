"""
Data Engineering Agent

A multi-agent system for Snowflake data engineering tasks including:
- Pipeline Development: Build and modify dbt pipelines, create models, manage schemas
- Troubleshooting: Diagnose pipeline issues, analyze logs, fix errors
- Data Quality: Run data quality checks, validate transformations, ensure data integrity

Built with LangGraph and deployable to DigitalOcean Gradient AI.

Supports multi-turn conversations via thread_id for maintaining context across requests.
"""

import os
import uuid
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

from typing import Dict, Literal, TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_gradient import ChatGradient
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from gradient_adk import entrypoint

from tools import ALL_TOOLS


# Global checkpointer for conversation persistence
# Note: MemorySaver stores state in memory; for production with multiple instances,
# consider using a persistent backend like Redis or PostgreSQL
memory = MemorySaver()


# Agent state with message history accumulation
class DataEngineeringState(TypedDict):
    """State for the data engineering workflow."""
    # Messages accumulate across the conversation using operator.add
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_request: str
    task_type: str  # pipeline_development, troubleshooting, data_quality, exploration
    context: str
    plan: str
    result: str
    needs_clarification: bool


# System prompts for different agent roles
ROUTER_PROMPT = """You are a data engineering task router. Analyze the user's request and determine the type of task.

Task Types:
1. **pipeline_development** - Creating or modifying dbt models, building new transformations, adding new tables to the pipeline, managing model dependencies
2. **troubleshooting** - Diagnosing pipeline failures, analyzing errors, fixing broken models, debugging data issues
3. **data_quality** - Running data quality checks, validating data, comparing source and target tables, identifying data anomalies
4. **exploration** - Exploring schemas, understanding existing data, sampling tables, analyzing column statistics

Respond with ONLY one of: pipeline_development, troubleshooting, data_quality, exploration"""


PIPELINE_DEVELOPER_PROMPT = """You are an expert dbt and Snowflake data engineer specializing in building data pipelines.

Your capabilities:
- Create new dbt models following the medallion architecture (staging → intermediate → marts)
- Modify existing models to add features or fix issues
- Design proper data transformations with clean SQL
- Manage model dependencies using ref() and source()
- Write data quality tests for models
- Follow dbt best practices (CTEs, proper naming, documentation)

Architecture Guidelines:
- **Staging**: Clean raw data, cast types, rename columns, basic filtering
- **Intermediate**: Business logic, joins, aggregations (often ephemeral)
- **Marts**: Final fact and dimension tables for analytics

When creating models:
1. First understand the source data structure
2. Plan the transformation logic
3. Generate clean, well-documented SQL
4. Add appropriate tests

Always explain your approach before making changes."""


TROUBLESHOOTER_PROMPT = """You are an expert data pipeline troubleshooter specializing in dbt and Snowflake.

Your capabilities:
- Diagnose dbt model failures and compilation errors
- Analyze Snowflake query errors and performance issues
- Debug data transformation logic
- Identify dependency issues in the DAG
- Fix common dbt and SQL problems

Troubleshooting Process:
1. Understand the error or symptom
2. Check dbt logs and test results
3. Examine the relevant model code
4. Identify root cause
5. Propose and implement fixes

Common issues to check:
- Syntax errors in SQL/Jinja
- Missing dependencies (ref/source)
- Type mismatches in transformations
- Null handling issues
- Duplicate key violations
- Performance bottlenecks

Always explain the root cause before proposing fixes."""


DATA_QUALITY_PROMPT = """You are a data quality expert specializing in Snowflake data validation.

Your capabilities:
- Run comprehensive data quality checks on tables
- Compare source and target row counts
- Identify data anomalies and outliers
- Validate data transformations
- Check for duplicates, nulls, and data freshness
- Analyze column statistics and distributions

Quality Checks to Perform:
1. **Completeness**: Check for nulls and missing data
2. **Accuracy**: Validate values are within expected ranges
3. **Consistency**: Compare related tables and columns
4. **Timeliness**: Check data freshness and loading timestamps
5. **Uniqueness**: Identify duplicates in key columns

Always provide actionable recommendations for fixing quality issues."""


EXPLORER_PROMPT = """You are a data exploration expert helping users understand their Snowflake data.

Your capabilities:
- Navigate database schemas and table structures
- Sample data from tables to show examples
- Analyze column distributions and statistics
- Explain the data model and relationships
- Help users find the data they need

When exploring:
1. Start with the schema overview
2. List relevant tables
3. Show table structures
4. Provide data samples
5. Explain what you found

Be thorough but concise in your explanations."""


CONVERSATIONAL_PROMPT = """You are a helpful data engineering assistant. You have access to the conversation history below.

Use this context to:
- Understand what the user has already asked about
- Reference previous results or findings
- Continue work that was started earlier
- Avoid repeating information already provided

If the user's request is a follow-up, acknowledge the context and build on previous work.
If it's a new topic, you can start fresh while still being aware of what was discussed."""


def get_model(temperature: float = 0.1):
    """Create the LLM model."""
    return ChatGradient(
        model="openai-gpt-4.1",
        api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY"),
        temperature=temperature,
    )


def format_conversation_history(messages: Sequence[BaseMessage], max_messages: int = 20) -> str:
    """Format recent conversation history for context."""
    if not messages:
        return "No previous conversation."

    # Get the most recent messages (skip system messages)
    recent = [m for m in messages if not isinstance(m, SystemMessage)][-max_messages:]

    if not recent:
        return "No previous conversation."

    lines = []
    for msg in recent:
        if isinstance(msg, HumanMessage):
            lines.append(f"User: {msg.content[:500]}...")
        elif isinstance(msg, AIMessage):
            lines.append(f"Assistant: {msg.content[:500]}...")

    return "\n".join(lines) if lines else "No previous conversation."


def route_request(state: DataEngineeringState) -> dict:
    """Route the user request to the appropriate specialist agent."""
    logger.info("=" * 50)
    logger.info("ROUTING REQUEST")
    logger.info(f"User request: {state['user_request'][:100]}...")

    model = get_model(temperature=0)

    # Include conversation context for better routing
    conversation_context = format_conversation_history(state.get("messages", []))

    messages = [
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=f"""Previous conversation context:
{conversation_context}

Current user request: {state['user_request']}

Based on this context, determine the task type."""),
    ]

    response = model.invoke(messages)
    task_type = response.content.strip().lower()

    # Validate task type
    valid_types = ["pipeline_development", "troubleshooting", "data_quality", "exploration"]
    if task_type not in valid_types:
        logger.warning(f"Invalid task type '{task_type}', defaulting to 'exploration'")
        task_type = "exploration"  # Default to exploration

    logger.info(f"Routed to: {task_type}")

    return {
        "task_type": task_type,
        "messages": [AIMessage(content=f"[Routing to: {task_type}]")]
    }


def gather_context(state: DataEngineeringState) -> dict:
    """Gather relevant context based on the task type."""
    logger.info("-" * 50)
    logger.info("GATHERING CONTEXT")
    task_type = state["task_type"]
    logger.info(f"Task type: {task_type}")
    model = get_model().bind_tools(ALL_TOOLS)

    # Determine what context to gather based on task type
    if task_type == "pipeline_development":
        context_prompt = """Gather context for pipeline development:
1. List the current dbt models to understand existing pipeline
2. Check the raw schema for available source data
3. If the user mentioned specific tables, get their schemas"""

    elif task_type == "troubleshooting":
        context_prompt = """Gather context for troubleshooting:
1. Check dbt test results for recent failures
2. Analyze dbt logs for errors
3. List dbt models to understand the pipeline"""

    elif task_type == "data_quality":
        context_prompt = """Gather context for data quality:
1. List schemas to understand the data layers
2. If user mentioned specific tables, run quality checks on them"""

    else:  # exploration
        context_prompt = """Gather context for exploration:
1. List all schemas
2. List tables in the schema the user is interested in (default: RAW)"""

    messages = [
        SystemMessage(content="You are a data engineering assistant. Gather the requested context using the available tools."),
        HumanMessage(content=f"User request: {state['user_request']}\n\n{context_prompt}"),
    ]

    response = model.invoke(messages)

    # Execute tool calls if any
    context_parts = []
    if response.tool_calls:
        logger.info(f"Executing {len(response.tool_calls)} tool(s) for context gathering")
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            logger.info(f"  -> Tool: {tool_name}({tool_args})")

            # Find and execute the tool
            for tool in ALL_TOOLS:
                if tool.name == tool_name:
                    try:
                        result = tool.invoke(tool_args)
                        context_parts.append(f"### {tool_name}\n{result}")
                        logger.info(f"     Result: {str(result)[:100]}...")
                    except Exception as e:
                        context_parts.append(f"### {tool_name}\nError: {str(e)}")
                        logger.error(f"     Error: {str(e)}")
                    break
    else:
        logger.info("No tools called for context gathering")

    context = "\n\n".join(context_parts) if context_parts else "No additional context gathered."
    logger.info(f"Context gathered: {len(context)} chars")

    return {"context": context}


def execute_task(state: DataEngineeringState) -> dict:
    """Execute the main task using the specialist agent."""
    logger.info("-" * 50)
    logger.info("EXECUTING TASK")
    task_type = state["task_type"]
    logger.info(f"Using specialist: {task_type}")
    model = get_model(temperature=0.2).bind_tools(ALL_TOOLS)

    # Select the appropriate system prompt
    prompts = {
        "pipeline_development": PIPELINE_DEVELOPER_PROMPT,
        "troubleshooting": TROUBLESHOOTER_PROMPT,
        "data_quality": DATA_QUALITY_PROMPT,
        "exploration": EXPLORER_PROMPT,
    }

    system_prompt = prompts.get(task_type, EXPLORER_PROMPT)

    # Include conversation history for context
    conversation_history = format_conversation_history(state.get("messages", []))

    messages = [
        SystemMessage(content=f"{system_prompt}\n\n{CONVERSATIONAL_PROMPT}"),
        HumanMessage(content=f"""
Previous Conversation:
{conversation_history}

Current Request: {state['user_request']}

Available Context:
{state['context']}

Please complete this request. Use the available tools as needed.
If you need to create or modify dbt models, provide the complete SQL code.
If this is a follow-up question, build on the previous conversation.
"""),
    ]

    # Execute with tool calling loop
    max_iterations = 10
    iteration = 0
    logger.info("Starting task execution loop (max 10 iterations)")

    for iteration in range(max_iterations):
        logger.info(f"  Iteration {iteration + 1}: Invoking LLM...")
        response = model.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            logger.info(f"  Iteration {iteration + 1}: No tool calls, task complete")
            break

        logger.info(f"  Iteration {iteration + 1}: {len(response.tool_calls)} tool call(s)")

        # Execute tool calls
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            logger.info(f"    -> Tool: {tool_name}({tool_args})")

            tool_result = "Tool not found"
            for tool in ALL_TOOLS:
                if tool.name == tool_name:
                    try:
                        tool_result = tool.invoke(tool_args)
                        logger.info(f"       Result: {str(tool_result)[:100]}...")
                    except Exception as e:
                        tool_result = f"Error: {str(e)}"
                        logger.error(f"       Error: {str(e)}")
                    break

            # Add tool result to messages
            from langchain_core.messages import ToolMessage
            messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))

    if iteration == max_iterations - 1:
        logger.warning("Reached max iterations limit")

    # Get final response
    final_response = messages[-1].content if hasattr(messages[-1], "content") else "Task completed."
    logger.info(f"Task execution complete. Response length: {len(final_response)} chars")

    return {"result": final_response}


def format_response(state: DataEngineeringState) -> dict:
    """Format the final response for the user."""
    logger.info("-" * 50)
    logger.info("FORMATTING RESPONSE")
    task_type = state["task_type"]

    task_labels = {
        "pipeline_development": "Pipeline Development",
        "troubleshooting": "Troubleshooting",
        "data_quality": "Data Quality",
        "exploration": "Data Exploration",
    }

    formatted = f"""## {task_labels.get(task_type, 'Response')}

{state['result']}
"""

    logger.info(f"Response formatted as: {task_labels.get(task_type, 'Response')}")
    logger.info("=" * 50)

    # Add the final response to messages for conversation history
    return {
        "result": formatted,
        "messages": [AIMessage(content=formatted)]
    }


# Build the workflow
workflow = StateGraph(DataEngineeringState)

# Add nodes
workflow.add_node("route_request", route_request)
workflow.add_node("gather_context", gather_context)
workflow.add_node("execute_task", execute_task)
workflow.add_node("format_response", format_response)

# Define edges
workflow.add_edge(START, "route_request")
workflow.add_edge("route_request", "gather_context")
workflow.add_edge("gather_context", "execute_task")
workflow.add_edge("execute_task", "format_response")
workflow.add_edge("format_response", END)

# Compile the graph with checkpointer for conversation persistence
agent_graph = workflow.compile(checkpointer=memory)


@entrypoint
async def main(input: Dict, context: Dict):
    """Data Engineering Agent entrypoint.

    This agent helps with Snowflake and dbt data engineering tasks.

    **Conversation Support:**
    - Pass `thread_id` to maintain conversation history across requests
    - Without `thread_id`, each request starts a new conversation
    - The agent remembers previous questions and can build on earlier work

    **Request Format:**
    ```json
    {
        "prompt": "Your question or request",
        "thread_id": "optional-session-id"
    }
    ```

    **Capabilities:**
    - Pipeline Development: Create and modify dbt models
    - Troubleshooting: Diagnose and fix pipeline issues
    - Data Quality: Run quality checks and validations
    - Data Exploration: Explore schemas and sample data
    """
    user_request = input.get("prompt", "")

    if not user_request:
        logger.warning("No prompt provided in request")
        return {"response": "Please provide a data engineering request."}

    # Get or generate thread_id for conversation persistence
    thread_id = input.get("thread_id")
    is_new_conversation = not thread_id
    if not thread_id:
        # Generate a new thread_id for new conversations
        thread_id = str(uuid.uuid4())[:8]

    logger.info("")
    logger.info("=" * 50)
    logger.info("DATA ENGINEERING AGENT")
    logger.info("=" * 50)
    logger.info(f"Thread ID: {thread_id} ({'new' if is_new_conversation else 'continuing'})")
    logger.info(f"Request: {user_request[:80]}{'...' if len(user_request) > 80 else ''}")

    # Configuration for checkpointing
    config = {"configurable": {"thread_id": thread_id}}

    # Check if this is a continuing conversation
    existing_state = None
    try:
        existing_state = agent_graph.get_state(config)
    except Exception:
        pass

    if existing_state and existing_state.values and existing_state.values.get("messages"):
        # Continuing conversation - add new user message to existing history
        msg_count = len(existing_state.values.get("messages", []))
        logger.info(f"Continuing conversation with {msg_count} previous messages")
        initial_state = {
            "messages": [HumanMessage(content=user_request)],
            "user_request": user_request,
            "task_type": "",
            "context": "",
            "plan": "",
            "result": "",
            "needs_clarification": False,
        }
    else:
        # New conversation
        logger.info("Starting new conversation")
        initial_state = {
            "messages": [HumanMessage(content=user_request)],
            "user_request": user_request,
            "task_type": "",
            "context": "",
            "plan": "",
            "result": "",
            "needs_clarification": False,
        }

    # Run the workflow with checkpointing
    logger.info("Running workflow...")
    result = await agent_graph.ainvoke(initial_state, config)

    logger.info("Request complete")
    logger.info("=" * 50)

    return {
        "response": result.get("result", "No response generated."),
        "thread_id": thread_id  # Return thread_id so client can continue the conversation
    }
