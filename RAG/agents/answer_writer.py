from langgraph.graph import MessagesState
from langchain_gradient import ChatGradient

GENERATE_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, just say that you don't know. "
    "Use three sentences maximum and keep the answer concise.\n"
    "Question: {question} \n"
    "Context: {context}"
)

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
