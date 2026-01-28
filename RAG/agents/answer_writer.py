from langgraph.graph import MessagesState
from langchain_gradient import ChatGradient

# Import prompts from central prompts.py - edit that file to customize
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import GENERATE_PROMPT

answer_model = ChatGradient(
    model="openai-gpt-4.1",
    temperature=0
)


def generate_answer(state: MessagesState):
    """Generate an answer."""
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    response = answer_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}
