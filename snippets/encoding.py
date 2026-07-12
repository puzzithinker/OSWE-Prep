"""Snippet: common encodings for payloads."""

from __future__ import annotations

import base64
import urllib.parse


def b64(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    return base64.b64encode(data).decode()


def b64d(data: str) -> bytes:
    return base64.b64decode(data)


def urlencode(s: str, safe: str = "") -> str:
    return urllib.parse.quote(s, safe=safe)


def urldecode(s: str) -> str:
    return urllib.parse.unquote(s)


def double_urlencode(s: str) -> str:
    return urlencode(urlencode(s))
