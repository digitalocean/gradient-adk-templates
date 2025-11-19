from langgraph.graph import MessagesState
from langchain_openai import ChatOpenAI

REWRITE_PROMPT = (
    "Look at the input and try to reason about the underlying semantic intent / meaning.\n"
    "Here is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Formulate an improved question:"
)

rewriter_model = ChatOpenAI(
    model="openai-gpt-4.1",
    base_url="https://inference.do-ai.run/v1",
    api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY"),
    temperature=0
)


def rewrite_question(state: MessagesState):
    """Rewrite the original user question."""
    messages = state["messages"]
    question = messages[0].content
    prompt = REWRITE_PROMPT.format(question=question)
    response = rewriter_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [{"role": "user", "content": response.content}]}
