import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_gradient import ChatGradient
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv
from typing import Dict, Optional
from gradient_adk import entrypoint

# Import prompts - edit prompts.py to customize agent behavior
from prompts import SYSTEM_MESSAGE

load_dotenv()

AGENT_GRAPH: Optional[StateGraph] = None

model = ChatGradient(
    model="openai-gpt-4.1",
)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

client = MultiServerMCPClient(
    {
        "search": {
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}",
            "transport": "streamable_http",
        },
        "calculator": {
            "command": "python",
            "args": ["-m", "mcp_server_calculator"],
            "transport": "stdio",
        },
    }
)


async def build_graph():

    # First, fetch the tools from the MCP client
    # Note that this is an async operation, so it needs to be done within an async function
    tools = await client.get_tools()

    # Next, define a function that calls the model with the tools
    def call_model(state: MessagesState):
        messages = state["messages"]
        # Prepend system message if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_MESSAGE)] + list(messages)
        response = model.bind_tools(tools).invoke(messages)
        return {"messages": response}

    # Finally, we build the graph. This is a simple two-node loop between the model and the tools.
    # This allows the agent to call tools as needed, including multiple tools in sequence.
    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges(
        "call_model",
        tools_condition,
    )
    builder.add_edge("tools", "call_model")
    graph = builder.compile()
    return graph


@entrypoint
async def main(input: Dict, context: Dict):
    """Entrypoint"""

    input_request = input.get("prompt")

    # Instead of building the graph every time, we build it once and cache it.
    # This speeds up subsequent invocations.
    global AGENT_GRAPH
    if AGENT_GRAPH is None:
        AGENT_GRAPH = await build_graph()

    # Invoke the app
    result = await AGENT_GRAPH.ainvoke(input_request)
    final_response = result
    return {"response": final_response}
