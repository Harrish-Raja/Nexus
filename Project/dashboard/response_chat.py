"""The response assistant: one question, one model call, answered from the documents."""

import streamlit as st

from config import config
from dashboard.api_client import call_service
from dashboard.incident_queue import badge


def _show_answer(question_type, was_refused, answer, sources):
    marks = badge(question_type, config.CHAT_TYPE_BADGE_COLOURS.get(question_type, "gray"))
    if was_refused:
        marks += " " + badge("Refused", "gray")
    st.markdown(marks)
    st.markdown(answer)
    if sources:
        st.caption("From " + sources)


def render_response_chat_page():
    st.title("Response chat")
    main, side = st.columns([3, 1])
    with side.container(border=True):
        st.markdown("**What the assistant answers**")
        st.markdown("  \n".join(badge(kind, config.CHAT_TYPE_BADGE_COLOURS[kind])
                                for kind in config.CHAT_TYPE_OPTIONS))
        st.caption("Answers come only from Merrowfield Digital's procedures, policies, standards "
                   "and playbooks, and each one names the documents it drew on. The assistant "
                   f"remembers your last {config.CHAT_HISTORY_TURN_LIMIT} exchanges.")
        if st.session_state.get("role") not in config.CHAT_INCIDENT_STATUS_ROLES:
            st.caption("An incident is discussed here only once its customers have been told, "
                       "and then only in the words of the notice they were sent.")

    turns = call_service("GET", "/chat/turns", {"turn_limit": config.CHAT_PAGE_TURN_LIMIT}, None)
    with main:
        for turn in reversed(turns):
            st.chat_message("user").markdown(turn["question_text"])
            with st.chat_message("assistant"):
                _show_answer(turn["question_type"], turn["was_refused"], turn["answer_text"],
                             turn["source_documents"])

    question = st.chat_input("Ask about a procedure, a reporting rule, what customers should do, "
                             "or an incident by its reference.")
    if question is None:
        return
    if len(question.strip()) < config.CHAT_QUESTION_MINIMUM_CHARACTERS:
        st.warning(f"Ask with at least {config.CHAT_QUESTION_MINIMUM_CHARACTERS} characters.")
        return
    with main:
        st.chat_message("user").markdown(question)
        with st.spinner("Searching the documents - this costs one model call."):
            reply = call_service("POST", "/chat/ask", None, {"question": question.strip()})
        with st.chat_message("assistant"):
            _show_answer(reply["question_type"], reply["was_refused"], reply["answer"],
                         ", ".join(reply["source_documents"]))
