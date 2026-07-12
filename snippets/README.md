# Snippet library (exam toolkit)

Small, reusable Python fragments you **compose** under time pressure. Build these during modules and Challenge Labs — not during the exam.

**Rules for exam use**

- No LLM assistance on exam day (OffSec policy). Prepare offline.  
- Prefer copy-adapt from **your** tested snippets.  
- Parameterise IPs/ports; never hard-code proxy for final runs.  
- After pasting, cold-run the full PoC.

**Related**: `poc-examples/advanced-skeleton/`, `Building a Reusable OSWE PoC Skeleton.md`, `Challenge-Lab-Playbook.md`.

---

## Catalog

| File | Purpose |
|------|---------|
| [cli_main.py](cli_main.py) | argparse entrypoint (target + listener + proxy) |
| [http_session.py](http_session.py) | Session, proxy, GET/POST helpers |
| [csrf.py](csrf.py) | Extract CSRF / tokens from HTML |
| [multipart_upload.py](multipart_upload.py) | Multipart file upload |
| [blind_sqli.py](blind_sqli.py) | Boolean / time binary-search extract |
| [login_register.py](login_register.py) | Login / register stage patterns |
| [websocket_client.py](websocket_client.py) | Simple WebSocket send/recv |
| [encoding.py](encoding.py) | Base64 / URL helpers |
| [listener_notes.md](listener_notes.md) | nc / http.server before PoC |

---

## How to use during a Challenge Lab

1. Copy skeleton PoC.  
2. Paste only the helpers you need (or import if you maintain a private package).  
3. Wire stages: `recon → auth → exploit → verify`.  
4. Delete unused helpers to keep the submitted script readable.

---

## Build discipline

After every module or lab, ask:

- Did I rewrite CSRF parsing again? → improve `csrf.py`  
- Did blind extract copy-paste diverge? → one function in `blind_sqli.py`  
- Did multipart fail quoting? → fix `multipart_upload.py` once  

Your library quality **is** exam speed.

---

## Conversion tip (prep only)

Burp → **Copy as curl** → [curlconverter.com](https://curlconverter.com/) → Python `requests`. Then merge into your session helper and remove junk headers.
