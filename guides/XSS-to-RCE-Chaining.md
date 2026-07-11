# XSS → Privileged Action → RCE Chaining

**Goal**: Treat XSS as a **trust-boundary crossing primitive**, not an alert box. Build OSWE-quality chains ending in server-side impact.

**Companions**: `notes/ATMAIL-6.4.md`, `Atmail-6.4-XSS-RCE-Study.md`, `poc-examples/atmail-xss-rce/`.

---

## 1. Mental model

```text
Attacker injects script into content
    → Victim with HIGHER privilege views it
        → Browser executes JS with victim origin + cookies
            → JS performs state-changing request victim is allowed to make
                → Server executes dangerous admin feature
                    → File write / plugin / config → RCE
```

**Key insight**: HttpOnly session cookies still allow **session riding** (CSRF from XSS). You may not steal the cookie; you can still *use* the session.

---

## 2. When XSS is exam-grade

| Weak XSS | Strong XSS (exam interest) |
|----------|----------------------------|
| Self-XSS only | Stored in admin view |
| No dangerous actions | Plugin install / file write / template edit |
| Sandboxed admin | Same-origin admin console |
| CSP blocks all | No CSP or bypassable |

---

## 3. Recon methodology

### Find injection

- Reflective params, stored fields, mail bodies, tickets, profiles, logs viewed in UI  
- Encoding context: HTML body, attribute, JS string, URL  

### Find privileged victims

- Admin ticket queues, moderation, mail admin, “login as” previews  

### Find dangerous actions (Burp while admin)

Capture **raw HTTP** for:
- File upload / theme / plugin install  
- Backup import  
- Configuration save writing files  
- User creation with roles  

Record: URL, method, CSRF token location, multipart fields.

---

## 4. Weaponization steps

### Step A — Prove privileged execution

Minimal marker in admin-visible field (lab-safe). Confirm event handlers or script run as admin origin.

### Step B — Automate the privileged request

From JS:
1. Read CSRF token from DOM / meta / cookie if needed.  
2. `fetch` / `XMLHttpRequest` / form submit to admin endpoint.  
3. Include credentials (`credentials: 'include'` for fetch).  

### Step C — Deliver code execution payload

- Upload webshell via captured multipart shape  
- Install malicious plugin package  
- Write PHP/ASPX/JSP through template editor  

### Step D — Attacker retrieves control

Hit shell URL from attacker machine; no admin browser needed after install.

---

## 5. Filter bypass mindset (brief)

| Defense | Directions |
|---------|------------|
| Tag strip | Event handlers, SVG, math, encoding |
| Keyword block | Concatenation, JSFuck-like (time box!) |
| Mail client sanitize | Alternate fields (signature, display name) |
| CSP | nonce reuse, gadget scripts already on page |

Don’t sink 2 hours into exotic bypass if another chain exists.

---

## 6. CSRF vs XSS

| Primitive | Needs victim browser? | Needs CSRF token? |
|-----------|----------------------|-------------------|
| Classic CSRF | Yes (visit attacker page) | Often blocked by token |
| XSS on same origin | Yes (view content) | Token readable → bypass |
| Stolen cookie (non-HttpOnly) | No after theft | N/A |

XSS on admin origin is the **CSRF killer**.

---

## 7. PoC architecture

```text
Stage 1: Auth as low-priv attacker
Stage 2: Store XSS payload (compose mail / create ticket / API)
Stage 3: (Lab) Optionally simulate admin trigger OR document admin open
Stage 4: Verify plugin/shell exists (attacker HTTP)
Stage 5: Execute command / read flag
```

**Honesty in notes**: if your script uses stolen admin cookie from lab setup instead of real XSS trigger, label that stage “simulated privileged session” vs “XSS-delivered”.

Payload hosting:
- Inline JS for simple CSRF POSTs  
- External script `http://attacker/x.js` for multi-step installs  

---

## 8. Report narrative (what examiners want)

1. Injection point + storage  
2. Who views it and why they’re privileged  
3. Which server-side action was invoked  
4. How that yields RCE  
5. Evidence at each trust boundary  

---

## 9. Defenses (remediation language)

1. Context-aware output encoding; strict HTML sanitizer for rich text  
2. CSP with nonces; disable inline where possible  
3. CSRF tokens + SameSite; re-auth for plugin install  
4. Admin actions not reachable via simple POST without step-up  
5. Plugins signed; uploads outside web root  

---

## 10. OSWE tactics

| Do | Don’t |
|----|-------|
| Capture clean admin request first | Start with 10KB polyglot XSS |
| Script storage + verification | Rely on manual browser only |
| Prefer upload/plugin sinks | Stop at `alert` screenshots |
| Time box sanitizer fights | Ignore second vuln class |

**Related**: `guides/File-Upload-to-RCE.md`, `guides/Chain-Decision-Trees.md`, Atmail materials.
