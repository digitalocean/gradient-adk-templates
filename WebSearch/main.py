import os
from gradient_adk import entrypoint
from langchain_core.tools import tool
from langchain_gradient import ChatGradient
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from pydantic import BaseModel

from langchain_community.tools import DuckDuckGoSearchRun

# Import prompts - edit prompts.py to customize agent behavior
from prompts import SYSTEM_PROMPT

search = DuckDuckGoSearchRun()


@tool
def web_search(query: str) -> str:
    """Perform a web search using DuckDuckGo."""
    results = search.run(query)
    return results


llm = ChatGradient(
    model="openai-gpt-oss-120b",
)

agent = create_agent(
    llm, tools=[web_search], system_prompt=SYSTEM_PROMPT
)


class Message(BaseModel):
    content: str


@entrypoint
async def entry(data, context):
    query = data["prompt"]
    inputs = {"messages": [HumanMessage(content=query)]}
    result = await agent.ainvoke(inputs)
    return result["messages"][-1].content
