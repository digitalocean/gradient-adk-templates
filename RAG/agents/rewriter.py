from langgraph.graph import MessagesState
from langchain_gradient import ChatGradient

# Import prompts from central prompts.py - edit that file to customize
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import REWRITE_PROMPT

rewriter_model = ChatGradient(
    model="openai-gpt-4.1",
    temperature=0
)


def rewrite_question(state: MessagesState):
    """Rewrite the original user question."""
    messages = state["messages"]
    question = messages[0].content
    prompt = REWRITE_PROMPT.format(question=question)
    response = rewriter_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [{"role": "user", "content": response.content}]}
