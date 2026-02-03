"""
DeepSearch Agent - A multi-step research agent using LangGraph with Human-in-the-Loop.

This agent performs comprehensive web research through two phases:

Phase 1: Plan & Refine (Human-in-the-Loop)
- Generates a research plan with specific goals
- User can approve or request refinements via natural conversation
- Nothing proceeds without explicit approval

Phase 2: Autonomous Research Pipeline (Parallel Execution)
- Converts plan into report sections
- Researches ALL sections in parallel using Send API
- Evaluates overall quality and fills gaps
- Composes final report with citations

Based on Google ADK's DeepSearch agent, ported to LangGraph and Gradient ADK.
"""

import os
import sys
import logging
import operator
from typing import Dict, List, Optional, Any, Annotated
from typing_extensions import TypedDict
from enum import Enum

from dotenv import load_dotenv
from gradient_adk import entrypoint
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command, Send
from langchain_gradient import ChatGradient
from pydantic import BaseModel, Field

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DeepSearch")

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import prompts - edit prompts.py to customize agent behavior
from prompts import INTENT_CLASSIFICATION_PROMPT, get_section_analysis_prompt

from agents.planner import (
    generate_initial_plan,
    refine_plan,
    format_plan_for_display,
    ResearchPlan
)
from agents.section_planner import plan_sections, ReportOutline
from agents.composer import compose_report
from tools.serper_search import serper_search


class WorkflowPhase(str, Enum):
    """Current phase of the workflow."""
    PLANNING = "planning"
    RESEARCHING = "researching"
    COMPOSING = "composing"
    COMPLETE = "complete"


# ============================================================================
# STATE DEFINITIONS
# ============================================================================

class SectionResearchState(TypedDict):
    """State for individual section research (used with Send)."""
    topic: str
    section_index: int
    section_title: str
    section_description: str
    search_queries: List[str]


class SectionResult(TypedDict):
    """Result from researching a single section."""
    section_index: int
    section_title: str
    section_description: str
    findings: List[Dict[str, Any]]
    combined_summary: str
    sources: Dict[str, Dict[str, Any]]
    quality_score: float


class DeepSearchState(TypedDict, total=False):
    """State for the DeepSearch workflow."""
    # Input
    topic: str
    thread_id: str

    # Phase tracking
    phase: str
    status_message: str

    # Planning phase
    research_plan: Optional[ResearchPlan]
    plan_display: str
    plan_approved: bool
    plan_iteration: int
    user_feedback: str

    # Section planning
    report_outline: Optional[ReportOutline]
    total_sections: int

    # Research phase - uses Annotated with operator.add for parallel collection
    section_results: Annotated[List[SectionResult], operator.add]
    all_sources: Dict[str, Dict[str, Any]]
    max_section_iterations: int

    # Output
    final_report: Optional[Any]
    markdown_report: str


# ============================================================================
# INTENT CLASSIFICATION
# ============================================================================

class UserIntent(BaseModel):
    """Classification of user intent from their message."""
    intent: str = Field(description="One of: 'approve', 'refine', 'question', 'other'")
    feedback: str = Field(description="If intent is 'refine', extract the specific feedback/changes requested. Otherwise empty string.")
    reasoning: str = Field(description="Brief explanation of why this intent was chosen")


def get_intent_classifier():
    return ChatGradient(
        model="openai-gpt-4.1",
        temperature=0
    )


def classify_user_intent(message: str, plan_display: str) -> UserIntent:
    """Classify the user's intent from their natural language message."""
    classifier = get_intent_classifier()
    structured_classifier = classifier.with_structured_output(UserIntent)

    prompt = INTENT_CLASSIFICATION_PROMPT.format(
        plan_display=plan_display,
        user_response=message
    )

    result = structured_classifier.invoke([{"role": "user", "content": prompt}])
    logger.info(f"Classified intent: {result.intent} - {result.reasoning}")

    return result


# ============================================================================
# PLANNING PHASE NODES
# ============================================================================

def generate_plan_node(state: DeepSearchState) -> dict:
    """Generate the initial research plan."""
    logger.info("=" * 60)
    logger.info("PHASE 1: PLANNING")
    logger.info("=" * 60)
    logger.info(f"Generating initial plan for: {state.get('topic', '')}")

    result = generate_initial_plan(state)
    result["phase"] = WorkflowPhase.PLANNING.value
    result["status_message"] = "Plan generated. Awaiting user approval."

    return result


def human_review_node(state: DeepSearchState) -> dict:
    """Human-in-the-loop node for plan review using LangGraph interrupt."""
    plan_display = state.get("plan_display", "")
    iteration = state.get("plan_iteration", 1)

    logger.info(f"Plan iteration {iteration} ready for review")

    # Interrupt and wait for user response
    user_message = interrupt({
        "type": "plan_review",
        "message": "Please review the research plan.",
        "plan": plan_display,
        "iteration": iteration
    })

    logger.info(f"Received user message: {user_message}")

    # Classify the user's intent
    intent_result = classify_user_intent(str(user_message), plan_display)

    if intent_result.intent == "approve":
        logger.info("Plan APPROVED by user")
        return {
            "plan_approved": True,
            "status_message": "Plan approved. Starting parallel research pipeline."
        }
    elif intent_result.intent == "refine":
        logger.info(f"Plan refinement requested: {intent_result.feedback}")
        return {
            "plan_approved": False,
            "user_feedback": intent_result.feedback or str(user_message),
            "status_message": "Refining plan based on feedback..."
        }
    elif intent_result.intent == "question":
        logger.info(f"User asked a question: {user_message}")
        return {
            "plan_approved": False,
            "user_feedback": f"User question: {user_message}. Please address this in an updated plan.",
            "status_message": "Addressing your question and updating the plan..."
        }
    else:
        return {
            "plan_approved": False,
            "user_feedback": str(user_message),
            "status_message": "Processing your feedback..."
        }


def refine_plan_node(state: DeepSearchState) -> dict:
    """Refine the plan based on user feedback."""
    feedback = state.get("user_feedback", "")
    logger.info(f"Refining plan based on feedback: {feedback[:100]}...")

    result = refine_plan(state)
    result["status_message"] = "Plan refined. Please review the updated plan."

    return result


def route_after_review(state: DeepSearchState) -> str:
    """Route based on whether plan was approved."""
    if state.get("plan_approved", False):
        return "plan_sections"
    return "refine_plan"


# ============================================================================
# RESEARCH PHASE NODES (PARALLEL EXECUTION)
# ============================================================================

def plan_sections_node(state: DeepSearchState) -> dict:
    """Convert approved plan into report sections."""
    logger.info("=" * 60)
    logger.info("PHASE 2: PARALLEL RESEARCH PIPELINE")
    logger.info("=" * 60)
    logger.info("Converting plan to report sections...")

    result = plan_sections(state)
    result["phase"] = WorkflowPhase.RESEARCHING.value
    result["section_results"] = []  # Initialize empty list for parallel results
    result["status_message"] = f"Created {result.get('total_sections', 0)} sections. Starting parallel research."

    return result


def dispatch_section_research(state: DeepSearchState) -> List[Send]:
    """
    Fan-out: Dispatch parallel research for each section using Send API.

    This creates a Send for each section, which will be executed in parallel.
    Results are automatically collected via the Annotated reducer.
    """
    outline = state.get("report_outline")
    topic = state.get("topic", "")

    if not outline or not outline.sections:
        logger.warning("No sections to research")
        return []

    logger.info(f"Dispatching {len(outline.sections)} sections for parallel research...")

    sends = []
    for idx, section in enumerate(outline.sections):
        logger.info(f"  -> Section {idx + 1}: {section.title}")
        sends.append(Send("research_section", {
            "topic": topic,
            "section_index": idx,
            "section_title": section.title,
            "section_description": section.description,
            "search_queries": section.search_queries
        }))

    return sends


def research_section_node(state: SectionResearchState) -> dict:
    """
    Research a single section (runs in parallel with other sections).

    This node receives individual section state via Send and returns
    results that are automatically aggregated via the reducer.
    """
    topic = state.get("topic", "")
    section_index = state.get("section_index", 0)
    section_title = state.get("section_title", "")
    section_description = state.get("section_description", "")
    search_queries = state.get("search_queries", [])

    logger.info(f"[Section {section_index + 1}] Researching: {section_title}")

    researcher_model = ChatGradient(
        model="openai-gpt-4.1",
        temperature=0.2
    )

    all_findings = []
    sources = {}
    summaries = []
    quality_scores = []

    # Execute each search query for this section
    for query_idx, query in enumerate(search_queries):
        logger.info(f"[Section {section_index + 1}] Query {query_idx + 1}/{len(search_queries)}: {query[:50]}...")

        try:
            # Perform search
            search_results = serper_search(query, num_results=5)

            # Format results for analysis
            formatted_results = "\n".join([
                f"{i}. {r.title}\n   URL: {r.link}\n   {r.snippet}"
                for i, r in enumerate(search_results.results, 1)
            ])

            # Analyze results
            analysis_prompt = get_section_analysis_prompt(
                section_title=section_title,
                section_description=section_description,
                query=query,
                formatted_results=formatted_results,
                topic=topic
            )

            response = researcher_model.invoke([{"role": "user", "content": analysis_prompt}])
            content = response.content

            # Parse response
            summary = content.split("QUALITY:")[0].replace("SUMMARY:", "").strip() if "QUALITY:" in content else content
            try:
                quality = int(content.split("QUALITY:")[-1].strip().split()[0]) if "QUALITY:" in content else 5
            except:
                quality = 5

            summaries.append(summary)
            quality_scores.append(quality)

            # Track findings and sources
            for r in search_results.results[:3]:
                all_findings.append({
                    "content": r.snippet,
                    "source_url": r.link,
                    "source_title": r.title,
                    "query": query
                })
                if r.link not in sources:
                    sources[r.link] = {
                        "url": r.link,
                        "title": r.title,
                        "section": section_title
                    }

            logger.info(f"[Section {section_index + 1}] Query complete, quality: {quality}/10")

        except Exception as e:
            logger.error(f"[Section {section_index + 1}] Error: {str(e)}")
            summaries.append(f"Error researching: {str(e)}")
            quality_scores.append(1)

    # Calculate average quality
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 5.0

    logger.info(f"[Section {section_index + 1}] Complete - {len(all_findings)} findings, avg quality: {avg_quality:.1f}/10")

    # Return result - this gets aggregated via operator.add reducer
    return {
        "section_results": [{
            "section_index": section_index,
            "section_title": section_title,
            "section_description": section_description,
            "findings": all_findings,
            "combined_summary": "\n\n".join(summaries),
            "sources": sources,
            "quality_score": avg_quality
        }]
    }


def consolidate_research_node(state: DeepSearchState) -> dict:
    """
    Fan-in: Consolidate all parallel research results.

    By the time this node runs, all section_results have been
    collected via the operator.add reducer.
    """
    section_results = state.get("section_results", [])

    logger.info("=" * 60)
    logger.info("CONSOLIDATING PARALLEL RESEARCH RESULTS")
    logger.info("=" * 60)
    logger.info(f"Received results from {len(section_results)} sections")

    # Sort results by section index
    sorted_results = sorted(section_results, key=lambda x: x.get("section_index", 0))

    # Consolidate all sources
    all_sources = {}
    for result in sorted_results:
        for url, source_info in result.get("sources", {}).items():
            if url not in all_sources:
                all_sources[url] = source_info

    # Log summary
    total_findings = sum(len(r.get("findings", [])) for r in sorted_results)
    avg_quality = sum(r.get("quality_score", 5) for r in sorted_results) / len(sorted_results) if sorted_results else 5

    logger.info(f"Total findings: {total_findings}")
    logger.info(f"Total sources: {len(all_sources)}")
    logger.info(f"Average quality: {avg_quality:.1f}/10")

    for result in sorted_results:
        logger.info(f"  Section {result['section_index'] + 1}: {result['section_title']} - quality {result['quality_score']:.1f}/10")

    return {
        "section_results": sorted_results,  # Replace with sorted version
        "all_sources": all_sources,
        "status_message": f"Research complete. {len(sorted_results)} sections, {total_findings} findings."
    }


def compose_report_node(state: DeepSearchState) -> dict:
    """Compose the final report from all section results."""
    logger.info("=" * 60)
    logger.info("PHASE 3: COMPOSING REPORT")
    logger.info("=" * 60)

    # Convert section_results to the format expected by compose_report
    section_results = state.get("section_results", [])
    section_findings = []

    for result in section_results:
        section_findings.append({
            "section_title": result.get("section_title", ""),
            "section_description": result.get("section_description", ""),
            "combined_summary": result.get("combined_summary", ""),
            "all_findings": result.get("findings", [])
        })

    # Update state with converted format for composer
    state_for_composer = dict(state)
    state_for_composer["section_findings"] = section_findings

    result = compose_report(state_for_composer)
    result["phase"] = WorkflowPhase.COMPLETE.value
    result["status_message"] = "Report composition complete!"

    logger.info("=" * 60)
    logger.info("DEEP SEARCH COMPLETE")
    logger.info("=" * 60)

    return result


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def build_deep_search_graph() -> StateGraph:
    """Build the DeepSearch workflow graph with parallel section research."""
    workflow = StateGraph(DeepSearchState)

    # Planning phase nodes
    workflow.add_node("generate_plan", generate_plan_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("refine_plan", refine_plan_node)

    # Research phase nodes
    workflow.add_node("plan_sections", plan_sections_node)
    workflow.add_node("research_section", research_section_node)  # Parallel node
    workflow.add_node("consolidate_research", consolidate_research_node)
    workflow.add_node("compose_report", compose_report_node)

    # Planning phase edges
    workflow.add_edge(START, "generate_plan")
    workflow.add_edge("generate_plan", "human_review")
    workflow.add_conditional_edges(
        "human_review",
        route_after_review,
        {
            "plan_sections": "plan_sections",
            "refine_plan": "refine_plan"
        }
    )
    workflow.add_edge("refine_plan", "human_review")

    # Research phase edges - PARALLEL EXECUTION
    # Fan-out: dispatch_section_research creates Send for each section
    workflow.add_conditional_edges("plan_sections", dispatch_section_research, ["research_section"])

    # Fan-in: All parallel research_section nodes converge to consolidate
    workflow.add_edge("research_section", "consolidate_research")

    # Final composition
    workflow.add_edge("consolidate_research", "compose_report")
    workflow.add_edge("compose_report", END)

    return workflow


# Global checkpointer for state persistence
memory = MemorySaver()

# Build and compile the graph with checkpointing
deep_search_workflow = build_deep_search_graph()
deep_search_graph = deep_search_workflow.compile(checkpointer=memory)


# ============================================================================
# ENTRYPOINT
# ============================================================================

@entrypoint
async def main(input: Dict, context: Dict) -> Dict:
    """
    DeepSearch agent entrypoint.

    The agent uses a simple, consistent conversational interface with just two fields:
    - message: Your input (research topic to start, or response to continue)
    - thread_id: Session ID (optional for new research, required for continuing)

    The agent interprets your natural language message to determine intent:
    - New research: If no thread_id or thread_id doesn't exist, message is the research topic
    - Approval: "looks good", "proceed", "yes", "let's go", etc.
    - Refinement: "add more about X", "remove Y", "can you focus on Z", etc.

    Args:
        input: Dictionary containing:
            - message: Your input (research topic or response)
            - thread_id: Session ID (optional for new, required for continuing)
            - max_section_iterations: Max iterations per section (default 2)

    Returns:
        Dictionary containing:
            - thread_id: Session ID for continuing the conversation
            - phase: Current workflow phase
            - status: Human-readable status message
            - plan: Research plan (during planning phase)
            - report: Final markdown report (when complete)
            - sources: List of sources used
            - awaiting_input: True if waiting for user response
    """
    # Extract inputs
    message = input.get("message") or input.get("prompt", "")
    thread_id = input.get("thread_id", "")
    max_section_iterations = input.get("max_section_iterations", 2)

    logger.info(f"Request received - thread_id: {thread_id or 'new'}, message: {message[:50] if message else 'N/A'}...")

    if not message:
        return {
            "error": "Please provide a 'message' field with your research topic or response.",
            "usage": {
                "start_new": {"message": "your research topic"},
                "start_with_id": {"message": "your research topic", "thread_id": "your-session-id"},
                "continue": {"message": "your response", "thread_id": "your-session-id"}
            }
        }

    # Check if this is a continuing conversation
    config = {"configurable": {"thread_id": thread_id}} if thread_id else None
    existing_state = None

    if config:
        existing_state = deep_search_graph.get_state(config)

    # Case 1: Continuing an existing session
    if thread_id and existing_state and existing_state.values:
        # Check if graph is waiting for input
        if not existing_state.next:
            current_phase = existing_state.values.get("phase", "unknown")
            if current_phase == WorkflowPhase.COMPLETE.value:
                return {
                    "thread_id": thread_id,
                    "phase": "complete",
                    "status": "Research already complete.",
                    "report": existing_state.values.get("markdown_report", ""),
                    "sources": list(existing_state.values.get("all_sources", {}).keys()),
                    "awaiting_input": False
                }
            return {
                "thread_id": thread_id,
                "phase": current_phase,
                "status": existing_state.values.get("status_message", ""),
                "awaiting_input": False
            }

        logger.info(f"Resuming session {thread_id} with message: {message[:100]}...")

        # Resume the graph with the user's message
        try:
            result = deep_search_graph.invoke(Command(resume=message), config)
            logger.info(f"Graph resumed - phase={result.get('phase')}, status={result.get('status_message')}")
        except Exception as e:
            logger.error(f"Error during graph resumption: {str(e)}")
            return {
                "thread_id": thread_id,
                "phase": "error",
                "status": f"Error resuming research: {str(e)}",
                "plan": "",
                "awaiting_input": False
            }

        # Get the current state from the checkpointer
        final_state = deep_search_graph.get_state(config)
        if final_state and final_state.values:
            state_values = final_state.values
        else:
            state_values = result if result else {}

        # Check if research is complete
        if state_values.get("phase") == WorkflowPhase.COMPLETE.value:
            return {
                "thread_id": thread_id,
                "phase": "complete",
                "status": "Research complete!",
                "report": state_values.get("markdown_report", ""),
                "sources": list(state_values.get("all_sources", {}).keys()),
                "awaiting_input": False
            }

        # Still in planning or another phase
        return {
            "thread_id": thread_id,
            "phase": state_values.get("phase", "planning"),
            "status": state_values.get("status_message", ""),
            "plan": state_values.get("plan_display", ""),
            "awaiting_input": bool(final_state.next) if final_state else False
        }

    # Case 2: Starting new research (message is the topic)
    if not thread_id:
        import uuid
        thread_id = str(uuid.uuid4())[:8]

    config = {"configurable": {"thread_id": thread_id}}
    topic = message

    logger.info(f"Starting new research session: {thread_id}")

    initial_state: DeepSearchState = {
        "topic": topic,
        "thread_id": thread_id,
        "phase": WorkflowPhase.PLANNING.value,
        "status_message": "Starting...",
        "research_plan": None,
        "plan_display": "",
        "plan_approved": False,
        "plan_iteration": 0,
        "user_feedback": "",
        "report_outline": None,
        "total_sections": 0,
        "section_results": [],
        "all_sources": {},
        "max_section_iterations": max_section_iterations,
        "final_report": None,
        "markdown_report": ""
    }

    # Run until interrupt (plan review)
    try:
        result = deep_search_graph.invoke(initial_state, config)
        logger.info(f"Graph executed - phase={result.get('phase')}, status={result.get('status_message')}")
    except Exception as e:
        logger.error(f"Error during graph execution: {str(e)}")
        return {
            "thread_id": thread_id,
            "phase": "error",
            "status": f"Error generating research plan: {str(e)}",
            "plan": "",
            "awaiting_input": False
        }

    # Get the current state from the checkpointer
    final_state = deep_search_graph.get_state(config)
    if final_state and final_state.values:
        state_values = final_state.values
        logger.info(f"Final state retrieved - plan_display length: {len(state_values.get('plan_display', ''))}")
    else:
        state_values = result if result else {}

    # Return the plan for review
    return {
        "thread_id": thread_id,
        "phase": state_values.get("phase", "planning"),
        "status": state_values.get("status_message", ""),
        "plan": state_values.get("plan_display", ""),
        "awaiting_input": True
    }
