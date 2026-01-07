import os
import json
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from typing import Dict, Literal
from gradient_adk import entrypoint
from tavily import TavilyClient
from langgraph.config import get_stream_writer

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


@tool
def search_tool(query: str) -> dict:
    """
    A tool to search  a query on the web using Tavily for detailed and up to date information.
    If you need to look up recent information beyond your knowledge cutoff date, use this tool.
    """
    response = tavily_client.search(query)
    return response


# This function determines whether to branch to the tools node or the answer model node
def tools_branch_condition(
    state,
    messages_key: str = "messages",
) -> Literal["tools", "answer_model_call"]:
    if isinstance(state, list):
        ai_message = state[-1]
    elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
        ai_message = messages[-1]
    elif messages := getattr(state, messages_key, []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return "answer_model_call"


def build_graph():

    # We have two models - one for the initial decision making (non-streaming), and one for the final answer (streaming)
    decision_model = ChatOpenAI(
        model="openai-gpt-4.1",
        base_url="https://inference.do-ai.run/v1",
        api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY"),
    )
    answer_model = ChatOpenAI(
        model="openai-gpt-4.1",
        base_url="https://inference.do-ai.run/v1",
        api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY"),
        streaming=True,
    )

    tools = [search_tool]
    decision_model = decision_model.bind_tools(tools)

    async def decision_model_call(state: MessagesState):
        messages = state["messages"]
        system_prompt = SystemMessage(
            "Determine if the user query is out of your scope of knowledge and requires a web search. If so, invoke the tool. Otherwise, simply repeat the original query so that the next model can answer it."
        )
        response = await decision_model.ainvoke([system_prompt] + messages)
        return {"messages": response}

    # In order to stream from the answer model, we use a stream writer to yield chunks as they arrive
    # We store the streamed chunks in a custom key in the state dict, which we can then access in the entrypoint.
    # For more information, see https://docs.langchain.com/oss/python/langgraph/streaming#llm-tokens
    async def answer_model_call(state: MessagesState):
        messages = state["messages"]
        writer = get_stream_writer()
        async for response in answer_model.astream(messages):
            writer({"custom_llm_chunk": response})
        return {"result": "completed"}

    builder = StateGraph(MessagesState)
    builder.add_node("decision_model_call", decision_model_call)
    builder.add_node("tools", ToolNode(tools))
    builder.add_node("answer_model_call", answer_model_call)
    builder.add_edge(START, "decision_model_call")
    builder.add_conditional_edges(
        "decision_model_call",
        tools_branch_condition,
    )
    builder.add_edge("tools", "answer_model_call")
    builder.add_edge("answer_model_call", END)
    graph = builder.compile()
    return graph


AGENT_GRAPH = build_graph()


@entrypoint
async def main(input: Dict, context: Dict):
    """Entrypoint"""

    input_request = input.get("prompt")

    # As mentioned earlier, we stream the response from the answer model by accessing the custom key in the state dict
    async for _, chunk in AGENT_GRAPH.astream(input_request, stream_mode=["custom"]):
        chunk_data = chunk.get("custom_llm_chunk", None)
        if chunk_data and chunk_data.content:
            response_text = chunk_data.content
            yield json.dumps({"response": response_text}) + "\n"


# # You can stream responses from this agent by sending a streaming request to the endpoint.
# import requests
# import json

# def stream_endpoint(url: str, body : dict, headers : dict = {}, chunk_size: int = 1024):
#     payload = json.dumps(body)
#     with requests.post(url, data = payload, headers=headers, stream=True) as resp:
#         resp.raise_for_status()
#         for chunk in resp.iter_content(chunk_size=chunk_size):
#             if chunk:  # filter keep-alive chunks
#                 yield chunk

# if __name__ == "__main__":
#     body = {
#         "prompt" : {
#             "messages" : "Who were winners and runners up of the women's 2025 cricket world cup?"
#         }
#     }
#
#     headers = {"Authorization": f"Bearer {os.getenv('DIGITALOCEAN_API_TOKEN')}"}

#     buffer = ""
#     for chunk in stream_endpoint(url, body=body, headers=headers):
#         buffer += chunk.decode("utf-8")
#         while "\n" in buffer:
#             line, buffer = buffer.split("\n", 1)
#             if not line.strip():
#                 continue
#             response = json.loads(line)
#             print(response["response"], end="", flush=True)
