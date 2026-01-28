import os
from gradient_adk import entrypoint
from langchain_core.tools import tool
from langchain_gradient import ChatGradient
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from pydantic import BaseModel
from gradient import Gradient

# Import prompts - edit prompts.py to customize agent behavior
from prompts import SYSTEM_PROMPT

client = Gradient(access_token=os.environ.get("DIGITALOCEAN_API_TOKEN"))

@tool
def query_digitalocean_kb(query: str, num_results: int) -> str:
    """Perform a query against the DigitalOcean Gradient AI knowledge base."""
    response = client.retrieve.documents(
        knowledge_base_id=os.environ.get("DIGITALOCEAN_KB_ID"),
        num_results=num_results,
        query=query,
    )
    if response and response.results:
        return response.results
    return []


llm = ChatGradient(
    model="openai-gpt-oss-120b",
)

agent = create_agent(
    llm, tools=[query_digitalocean_kb], system_prompt=SYSTEM_PROMPT
)


class Message(BaseModel):
    content: str


@entrypoint
async def entry(data, context):
    query = data["prompt"]
    inputs = {"messages": [HumanMessage(content=query)]}
    result = await agent.ainvoke(inputs)
    return result["messages"][-1].content
