"""Every call the dashboard makes to the service passes through here."""

import requests
import streamlit as st

from config import config


class ServiceError(Exception):
    """The service refused or failed a request; carries its status and its own message."""

    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class ServiceUnreachable(Exception):
    """The service could not be reached at all."""


def call_service(method, path, query, payload):
    """One call to the service on behalf of the signed-in person."""
    headers = {}
    token = st.session_state.get("session_token")
    if token:
        headers[config.SESSION_TOKEN_HEADER] = token
    try:
        reply = requests.request(method, config.API_BASE_URL + path, params=query, json=payload,
                                 headers=headers, timeout=config.API_REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as error:
        raise ServiceUnreachable(
            f"The BreachWatch AI service at {config.API_BASE_URL} cannot be reached "
            f"({type(error).__name__}). Start it with: python run_api_service.py") from error
    if reply.status_code >= 400:
        try:
            detail = reply.json().get("detail", reply.text)
        except ValueError:
            detail = reply.text
        if isinstance(detail, list):
            detail = "; ".join(str(item.get("msg", item)) for item in detail)
        raise ServiceError(reply.status_code, str(detail))
    return reply.json()
