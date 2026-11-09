"""Entry point 6: the dashboard - signing in, the navigation and the five pages.

Run with:  python -m streamlit run run_dashboard.py
"""

import streamlit as st

from config import config
from dashboard.api_client import ServiceError, ServiceUnreachable, call_service
from dashboard.audit_trail import render_audit_trail_page
from dashboard.decision_queue import render_decision_queue_page
from dashboard.incident_detail import render_incident_detail_page
from dashboard.incident_queue import render_incident_queue_page
from dashboard.response_chat import render_response_chat_page

PAGE_RENDERERS = {
    config.PAGE_QUEUE: render_incident_queue_page,
    config.PAGE_INCIDENT: render_incident_detail_page,
    config.PAGE_DECISION: render_decision_queue_page,
    config.PAGE_AUDIT: render_audit_trail_page,
    config.PAGE_CHAT: render_response_chat_page,
}


def _sign_in_form():
    _, middle, _ = st.columns([1, 2, 1])
    with middle.container(border=True):
        st.title(f":material/shield_lock: {config.DASHBOARD_TITLE}")
        st.caption(config.DASHBOARD_SUBTITLE)
        with st.form("sign_in"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary", icon=":material/login:",
                                              width="stretch")
        if submitted:
            try:
                account = call_service("POST", "/auth/signin", None,
                                       {"username": username, "password": password})
            except ServiceError:
                st.error(config.SIGN_IN_FAILED_MESSAGE)
                return
            except ServiceUnreachable as error:
                st.error(str(error))
                return
            st.session_state.update({"session_token": account["session_token"],
                                     "display_name": account["display_name"],
                                     "role": account["role"], "pages": account["pages"]})
            st.rerun()


def _sign_out():
    try:
        call_service("POST", "/auth/signout", None, None)
    except (ServiceError, ServiceUnreachable):
        pass
    for key in ["session_token", "display_name", "role", "pages", "selected_incident"]:
        st.session_state.pop(key, None)


def _safely(renderer):
    def draw():
        try:
            renderer()
        except ServiceError as error:
            if error.status_code == 401:
                for key in ["session_token", "display_name", "role", "pages"]:
                    st.session_state.pop(key, None)
            st.error(error.message)
        except ServiceUnreachable as error:
            st.error(str(error))
    return draw


def main():
    st.set_page_config(page_title=config.DASHBOARD_TITLE, page_icon=":material/shield_lock:",
                       layout="wide")
    if not st.session_state.get("session_token"):
        _sign_in_form()
        return

    pages = [st.Page(_safely(PAGE_RENDERERS[name]), title=name,
                     url_path=name.lower().replace(" ", "_"))
             for name in st.session_state.get("pages", []) if name in PAGE_RENDERERS]
    navigation = st.navigation(pages, position="top")
    header, account = st.columns([3, 2])
    header.markdown(f"**:material/shield_lock: {config.DASHBOARD_TITLE}**  \n"
                    f":gray[{config.DASHBOARD_SUBTITLE}]")
    with account:
        name_column, button_column = st.columns([3, 1])
        name_column.markdown(f"**{st.session_state['display_name']}** "
                             f":blue-badge[{st.session_state['role']}]")
        if button_column.button("Sign out", icon=":material/logout:"):
            _sign_out()
            st.rerun()
    navigation.run()


if __name__ == "__main__":
    main()
