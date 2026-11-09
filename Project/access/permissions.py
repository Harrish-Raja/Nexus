"""Decides which area a request belongs to, and whether a role reaches it."""

from config import config


def check_request_permission(role_name, request_path, request_method):
    """The area of a request from its path (and, for a decision, its method), and the verdict."""
    path = "/" + str(request_path).strip().lstrip("/")
    trimmed = path.rstrip("/") or "/"
    if str(request_method).upper() == "POST" and trimmed.endswith(config.DECISION_PATH_ENDING):
        area = config.AREA_DECISION
    else:
        area = None
        for start in sorted(config.AREA_BY_PATH_START, key=len, reverse=True):
            if trimmed == start or trimmed.startswith(start.rstrip("/") + "/"):
                area = config.AREA_BY_PATH_START[start]
                break
    allowed = area is not None and area in config.ROLE_AREA_ACCESS.get(role_name, [])
    return {"area": area, "allowed": bool(allowed)}
