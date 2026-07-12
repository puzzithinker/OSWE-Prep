"""Snippet: minimal WebSocket client for command-injection style labs.

Requires: pip install websocket-client
Prep only — pin versions you trust in your lab venv.
See guides/WebSocket-Attack-Patterns.md.
"""

from __future__ import annotations

from typing import Optional


def ws_send_receive(
    url: str,
    message: str,
    *,
    timeout: float = 10.0,
    header: Optional[list] = None,
) -> str:
    """
    url: ws://host:port/path or wss://...
    message: raw string or JSON text to send after connect.
    """
    try:
        from websocket import create_connection  # type: ignore
    except ImportError as e:
        raise SystemExit("Install websocket-client in prep env") from e

    ws = create_connection(url, timeout=timeout, header=header or [])
    try:
        ws.send(message)
        return ws.recv()
    finally:
        ws.close()


# Example:
# resp = ws_send_receive("ws://127.0.0.1:8080/cmd", '{"cmd":"id"}')
# print(resp)
