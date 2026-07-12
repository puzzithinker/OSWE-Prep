"""Snippet: login / register stage patterns (adapt field names)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from csrf import fetch_csrf  # when used as package; else paste csrf helpers inline


def login_form(
    session: requests.Session,
    login_url: str,
    username: str,
    password: str,
    *,
    user_field: str = "username",
    pass_field: str = "password",
    csrf_page: Optional[str] = None,
    csrf_field: str = "csrf",
    extra: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> requests.Response:
    data: Dict[str, Any] = {user_field: username, pass_field: password}
    if extra:
        data.update(extra)
    if csrf_page:
        token = fetch_csrf(session, csrf_page, **kwargs)
        if token:
            data[csrf_field] = token
    return session.post(login_url, data=data, **kwargs)


def register_form(
    session: requests.Session,
    register_url: str,
    fields: Dict[str, Any],
    *,
    csrf_page: Optional[str] = None,
    csrf_field: str = "csrf",
    **kwargs,
) -> requests.Response:
    data = dict(fields)
    if csrf_page:
        token = fetch_csrf(session, csrf_page, **kwargs)
        if token:
            data[csrf_field] = token
    return session.post(register_url, data=data, **kwargs)
