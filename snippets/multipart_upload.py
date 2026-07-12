"""Snippet: multipart upload via requests."""

from __future__ import annotations

from typing import Optional, Tuple

import requests


def upload_file(
    session: requests.Session,
    url: str,
    field_name: str,
    filename: str,
    content: bytes,
    content_type: str = "application/octet-stream",
    extra_fields: Optional[dict] = None,
    **kwargs,
) -> requests.Response:
    """
    extra_fields: additional form fields (e.g. csrf token).
    """
    files = {field_name: (filename, content, content_type)}
    data = extra_fields or {}
    return session.post(url, files=files, data=data, **kwargs)


def upload_path(
    session: requests.Session,
    url: str,
    field_name: str,
    path: str,
    content_type: str = "application/octet-stream",
    extra_fields: Optional[dict] = None,
    **kwargs,
) -> requests.Response:
    with open(path, "rb") as f:
        data = f.read()
    name = path.rsplit("/", 1)[-1]
    return upload_file(session, url, field_name, name, data, content_type, extra_fields, **kwargs)
