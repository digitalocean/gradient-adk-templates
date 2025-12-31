import os
from enum import Enum
from typing import NotRequired, Optional, TypedDict

from dotenv import load_dotenv
from gradient_adk import entrypoint
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

load_dotenv()


class State(TypedDict):
    topic: str
    joke: str
    improved_joke: str
    final_joke: str
    spicy_instruction: NotRequired[Optional[str]]
    spicy_override: NotRequired[Optional[bool]]


class PunchlineStatus(str, Enum):
    PASS = "Pass"
    FAIL = "Fail"


class SpicyStatus(str, Enum):
    SPICY = "Spicy"
    NOT_SPICY = "NotSpicy"


# N O D E S
def generate_joke(state: State):
    """First LLM call to generate initial joke"""

    msg = llm.invoke(
        f"Write a short joke about {state['topic']} in two sentences or less"
    )
    return {"joke": msg.content}


def add_spicy_note(state: State):
    """Insert an instruction to make the joke extra sassy."""

    instruction = "Make the joke extra sassy."
    return {"spicy_instruction": instruction}


def improve_joke(state: State):
    """Second LLM call to improve the joke"""

    msg = llm.invoke(f"make the joke funnier and quirky: {state['joke']}")
    return {"improved_joke": msg.content}


def polish_joke(state: State):
    """Third LLM call for final polish"""

    msg = llm.invoke(
        f"Remove any explanation of the joke or punchline: {state['improved_joke']}"
    )
    return {"final_joke": msg.content}


def check_punchline(state: State):
    """Simple check - does the joke contain "?" or "!" """

    if "?" in state["joke"] or "!" in state["joke"]:
        return PunchlineStatus.PASS
    return PunchlineStatus.FAIL


def check_if_spicy(state: State):
    """Detect whether the topic implies we should add extra spice."""

    override = state.get("spicy_override")
    if override is True:
        return SpicyStatus.SPICY
    if override is False:
        return SpicyStatus.NOT_SPICY

    topic = state.get("topic", "")
    if isinstance(topic, str) and "spicy" in topic.lower():
        return SpicyStatus.SPICY
    return SpicyStatus.NOT_SPICY


def route_to_spice_check(state: State):
    """No-op node that allows separate spicy routing."""
    return {}


llm = ChatOpenAI(
    base_url="https://inference.do-ai.run/v1",
    model="openai-gpt-oss-120b",
    api_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY"),
)


@entrypoint
async def main(input):
    # Setup the graph
    workflow = StateGraph(State)

    # Add Nodes
    workflow.add_node("generate_joke", generate_joke)
    workflow.add_node("add_spicy_note", add_spicy_note)
    workflow.add_node("spice_router", route_to_spice_check)
    workflow.add_node("improve_joke", improve_joke)
    workflow.add_node("polish_joke", polish_joke)

    # Add Edges
    workflow.add_edge(START, "generate_joke")
    workflow.add_conditional_edges(
        source="generate_joke",
        path=check_punchline,
        path_map={PunchlineStatus.PASS: "spice_router", PunchlineStatus.FAIL: END},
    )
    workflow.add_conditional_edges(
        source="spice_router",
        path=check_if_spicy,
        path_map={
            SpicyStatus.SPICY: "add_spicy_note",
            SpicyStatus.NOT_SPICY: "improve_joke",
        },
    )
    workflow.add_edge("add_spicy_note", "improve_joke")
    workflow.add_edge("improve_joke", "polish_joke")
    workflow.add_edge("polish_joke", END)

    # Compile and run
    app = workflow.compile()

    topic = input.get("topic")
    spicy_override = input.get("spicy")

    initial_state = {"topic": topic}
    if spicy_override is not None:
        initial_state["spicy_override"] = spicy_override

    result = await app.ainvoke(initial_state)

    return result["final_joke"]
