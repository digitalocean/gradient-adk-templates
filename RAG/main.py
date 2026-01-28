import os
from dotenv import load_dotenv

load_dotenv()

from agents.grader import grade_documents
from agents.rewriter import rewrite_question
from agents.answer_writer import generate_answer
from tools.doc_retriever import create_retriever
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_gradient import ChatGradient
from gradient_adk import entrypoint
from typing import Dict


PDF_FOLDER_PATH = "./pdfs"

response_model = ChatGradient(
    model="openai-gpt-4.1",
    temperature=0.2
)

retriever_tool = create_retriever(PDF_FOLDER_PATH)


def generate_query_or_respond(state: MessagesState):
    """Call the model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply
    respond to the user.
    """
    response = response_model.bind_tools([retriever_tool]).invoke(state["messages"])
    return {"messages": [response]}


workflow = StateGraph(MessagesState)

# Define the nodes we will cycle between
workflow.add_node("generate_query_or_respond", generate_query_or_respond)
workflow.add_node("retrieve", ToolNode([retriever_tool]))
workflow.add_node("rewrite_question", rewrite_question)
workflow.add_node("generate_answer", generate_answer)

workflow.add_edge(START, "generate_query_or_respond")

# Decide whether to retrieve
workflow.add_conditional_edges(
    "generate_query_or_respond",
    # Assess LLM decision (call `retriever_tool` tool or respond to the user)
    tools_condition,
    {
        # Translate the condition outputs to nodes in our graph
        "tools": "retrieve",
        END: END,
    },
)

# Edges taken after the `action` node is called.
workflow.add_conditional_edges(
    "retrieve",
    # Assess agent decision
    grade_documents,
)
workflow.add_edge("generate_answer", END)
workflow.add_edge("rewrite_question", "generate_query_or_respond")

# Compile
agent_graph = workflow.compile()


@entrypoint
async def main(input: Dict, context: Dict):
    """Entrypoint"""

    input_request = input.get("prompt")
    # Invoke the app
    result = await agent_graph.ainvoke(input_request)
    final_response = result
    return {"response": final_response}
