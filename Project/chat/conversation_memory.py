"""Recalls a person's own recent conversation from the record, never from the caller."""

from config import config
from persistence.models import ChatTurn
from persistence.repository import fetch_chat_turns


def recall_conversation(session, username, question_text):
    """The last few exchanges as history to read, and the earlier questions as words to search."""
    turns = list(reversed(fetch_chat_turns(session, ChatTurn.username == username,
                                           config.CHAT_HISTORY_TURN_LIMIT)))
    if turns:
        history_text = "\n\n".join(f"Asked: {turn['question_text']}\nAnswered: "
                                   f"{turn['answer_text']}" for turn in turns)
    else:
        history_text = "This is the first question in the conversation."
    search_text = " ".join([turn["question_text"] for turn in turns] + [str(question_text)])
    return {"history_text": history_text, "search_text": search_text}
