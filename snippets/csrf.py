"""Snippet: pull CSRF / nonce tokens from HTML (adapt selectors per app)."""

from __future__ import annotations

import re
from typing import Optional

import requests


def csrf_from_html(
    html: str,
    *,
    name_attrs: tuple[str, ...] = ("csrf", "csrf_token", "_token", "authenticity_token", "nonce"),
) -> Optional[str]:
    for name in name_attrs:
        # <input type="hidden" name="csrf" value="...">
        m = re.search(
            rf'<input[^>]+name=["\']{re.escape(name)}["\'][^>]+value=["\']([^"\']+)["\']',
            html,
            re.I,
        )
        if m:
            return m.group(1)
        m = re.search(
            rf'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']{re.escape(name)}["\']',
            html,
            re.I,
        )
        if m:
            return m.group(1)
        # meta name="csrf-token" content="..."
        m = re.search(
            rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            html,
            re.I,
        )
        if m:
            return m.group(1)
    return None


def fetch_csrf(session: requests.Session, url: str, **kwargs) -> Optional[str]:
    r = session.get(url, **kwargs)
    r.raise_for_status()
    return csrf_from_html(r.text)
