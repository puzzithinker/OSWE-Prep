"""Snippet: requests.Session with proxy + common helpers."""

from __future__ import annotations

from typing import Any, Optional

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def make_session(proxy: Optional[str] = None, verify: bool = False) -> requests.Session:
    s = requests.Session()
    s.verify = verify
    if proxy:
        s.proxies.update({"http": proxy, "https": proxy})
    s.headers.update(
        {
            "User-Agent": "OSWE-PoC/1.0",
        }
    )
    return s


def get(
    s: requests.Session,
    url: str,
    *,
    timeout: float = 15.0,
    **kwargs: Any,
) -> requests.Response:
    return s.get(url, timeout=timeout, allow_redirects=True, **kwargs)


def post(
    s: requests.Session,
    url: str,
    *,
    data: Any = None,
    json: Any = None,
    timeout: float = 15.0,
    **kwargs: Any,
) -> requests.Response:
    return s.post(url, data=data, json=json, timeout=timeout, allow_redirects=True, **kwargs)
