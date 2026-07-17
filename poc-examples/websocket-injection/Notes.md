# WebSocket Injection — Case Notes

## Docker lab

`cd labs && ./labctl.sh up websocket` — see [`lab/README.md`](lab/README.md).

---

## Environment

- HTTP: http://127.0.0.1:8116
- WS: ws://127.0.0.1:8116/ws
- Flag: `/flag.txt` or `{"type":"flag"}`

## Vulnerability hypothesis

- Class: Command injection over WebSocket (CWE-78)
- Data flow: WS JSON `cmd` → `child_process.exec`
- Preconditions: connect to `/ws` (no auth in lab)

## Chain outline

1. Connect WS  
2. Send `{"type":"cmd","cmd":"id"}`  
3. Read flag via cmd or `type:flag`  

## Findings

- Root cause: shell exec of attacker message fields  
- Fix: never shell from WS payload; allow-list message types; auth every message  

## Methodology

- `guides/WebSocket-Attack-Patterns.md`
