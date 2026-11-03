from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def ask_user(question: str) -> str:
    """Ask the user a question and wait for the answer.

    Use only when you cannot continue without information that only the user
    has, such as a choice between options. Ask one short, clear question.
    """
    return interrupt({"kind": "user_question", "question": question})
