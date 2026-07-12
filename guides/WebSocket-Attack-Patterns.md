# WebSocket Attack Patterns

**Why**: 2026 reviews mention WebSocket surfaces (including command-style messages) in modern WEB-300 material and labs.

**Related**: `snippets/websocket_client.py` · CMDi / SSTI / SQLi guides · Challenge-Lab-Playbook.

---

## 1. When WebSockets appear

- Chat, notifications, collaborative editors  
- Live “run command” / IDE / terminal features  
- Real-time dashboards pushing events  

Fingerprint: browser DevTools → Network → WS; or `ws://` / `wss://` in JS.

---

## 2. White-box

```bash
rg -n "WebSocket|socket\.io|ws\.|@ServerEndpoint|SockJS|ActionCable" 
rg -n "onmessage|addEventListener\(['\"]message" --glob '*.{js,ts}'
```

Server handlers: parse JSON → SQL / shell / template / auth check.

Ask:

- Is the socket authenticated? Same session cookie?  
- Is every message authorized?  
- Is payload concatenated into shell/SQL/template?  

---

## 3. Attack classes

| Class | Idea |
|-------|------|
| CSWSH | Cross-site WebSocket hijack (browser origin issues) — lab-dependent |
| Injection in messages | SQLi / SSTI / CMDi via JSON fields |
| Auth bypass | Connect without cookie / forged subprotocol |
| IDOR over WS | Subscribe to other users’ channels |
| Blind RCE | Message triggers server exec; verify OOB |

---

## 4. Manual testing

1. Capture a legitimate WS message (Burp has limited WS support; use browser + replay tools or `websocat` / Python).  
2. Tamper fields systematically.  
3. Watch server logs on debug VM.  

---

## 5. PoC sketch

```python
# see snippets/websocket_client.py
from websocket_client import ws_send_receive
print(ws_send_receive("ws://TARGET:PORT/path", '{"cmd":"id"}'))
```

Stages:

```text
connect_authenticated()
send_probe()
send_exploit()
verify_callback_or_response()
```

Include WS steps **inside** the single non-interactive script when required for the chain.

---

## 6. Defenses (report)

- Authenticate and authorize **every** message  
- Allow-list message schemas  
- No shell/SQL from socket payload  
- Origin checks where appropriate  
- Rate limit  

---

## 7. OSWE tactics

- Don’t ignore WS just because Burp is HTTP-centric.  
- Source is often clearer than traffic for message schemas.  
- If CMDi is only on WS, the PoC **must** speak WS — practice `websocket-client` in prep.  
