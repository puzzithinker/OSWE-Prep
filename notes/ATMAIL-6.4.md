# Atmail 6.4 — Stored XSS → Privileged Action → RCE

**Pattern**: XSS in content viewed by privileged user → session riding / CSRF-like admin action → server-side code execution (plugin/theme/file write).  
**Study guide (concepts)**: `Atmail-6.4-XSS-RCE-Study.md`  
**PoC**: `poc-examples/atmail-xss-rce/`  
**Methodology**: `guides/XSS-to-RCE-Chaining.md`

CVE commonly referenced in training material: **CVE-2012-2593** (verify against your lab build).

---

## Environment

| Item | Typical lab value |
|------|-------------------|
| App | Atmail **6.4** (webmail) |
| Roles | Standard mailbox user vs **admin** |
| Services | HTTP(S), MySQL/DB, MTA components as packaged |
| URLs | User webmail UI + admin console paths |
| Attacker goal | Land HTML/JS in admin view → trigger dangerous admin feature |

**Lab notes**: dual-browser or two sessions (attacker user + admin). Snapshot before plugin installs.

---

## Recon

### Entry points
- Email body / subject rendering (HTML mail)
- Address book, calendar, notes, signatures
- Admin settings that display user-controlled strings
- File/plugin/theme upload in admin

### Privileged sinks (what XSS must drive)
Focus on **server-side effects**, not alert boxes:
- Install plugin / module
- Write config or template
- Upload PHP/CGI under web root
- Backup/restore that extracts files
- Command-oriented admin tools (rare but high value)

### White-box / source focus
1. Where is mail HTML sanitized? Allow-list vs strip?
2. Which templates echo body without encoding?
3. Admin routes: CSRF tokens? SameSite cookies?
4. Plugin install path validation

### Black-box
- Send mail with simple HTML probe from attacker account
- Admin opens message → observe execution context (cookie scope, origin)
- Map admin forms (multipart uploads, POST targets)

---

## Vulnerability hypothesis

| Field | Detail |
|-------|--------|
| Class | Stored XSS (CWE-79) chained to broken CSRF/authZ assumptions + insecure install |
| Data flow | Attacker email → stored → admin WebKit/browser → JS in admin origin → authenticated admin HTTP → file write / plugin |
| Preconditions | Admin views attacker content; dangerous action reachable with admin session; weak anti-CSRF or XSS bypasses token handling |
| Impact | RCE as web/mail application user |

### Chain diagram

```text
Attacker mailbox
    → stores XSS payload in message (or other admin-visible field)
Admin opens message
    → JS runs as admin origin
    → XHR/fetch/form POST to admin install/upload endpoint
Server
    → writes executable payload
Attacker
    → hits webshell URL / triggers plugin code
```

---

## Chain outline

### Step 1 — Confirm stored render
- Inject minimal HTML/JS marker safe for lab
- Prove admin (or privileged) view executes it
- Record exact DOM sink (innerHTML, unescaped template, etc.) if source available

### Step 2 — Minimize payload
- Exam mindset: smallest reliable script
- Prefer absolute URLs to attacker payload server for multi-step actions
- Handle charset / mail client filtering (strip `script`, event handlers, SVG, etc.)

### Step 3 — Identify privileged action
- From admin UI or source, list file-write primitives
- Capture a **normal** admin install/upload request in Burp (headers, multipart fields, tokens)

### Step 4 — Weaponize XSS as request automation
- From admin browser context, replay that request
- If CSRF token required: read token from DOM/page JS runs in, then submit
- If cookie-only CSRF model: simple forged request may work

### Step 5 — Get code execution
- Plugin with PHP/server code, or upload webshell via admin file feature
- Locate public URL path
- Verify with safe command / flag read

### Step 6 — Full Python PoC
Typical stages (see example PoC):
1. Authenticate attacker (and optionally drive mail send via HTTP if UI allows)
2. Deliver stored payload (IMAP/SMTP/API/web compose)
3. Optional: automate admin trigger if lab allows dual-session scripting; else document “admin open” + deliver second-stage
4. Verify shell

Many training PoCs **simulate** admin execution by replaying the privileged request with an admin session cookie obtained in lab — be explicit in notes which trust step is simulated vs XSS-triggered.

---

## Evidence

| Artifact | Proves |
|----------|--------|
| Mail source / stored content | Injection |
| Admin browser executing marker | XSS in privileged context |
| Privileged HTTP from that context | Session riding |
| File on disk / plugin row | Server effect |
| Command output | RCE |

---

## Findings

### Root cause
1. Insufficient output encoding / HTML sanitization in privileged views.
2. Dangerous administrative actions available to browser sessions without robust step-up auth.
3. Plugin/file install trusts uploaded content as executable code.

### Fixes
- Strict sanitization (allow-list HTML) for mail bodies; encode on output.
- CSP where feasible (mail HTML is hard — defense in depth).
- CSRF tokens + SameSite cookies on all admin state changes.
- Plugin signing / disable arbitrary plugin upload in production.
- Admin actions: re-auth for install; store plugins outside auto-exec paths when possible.

### OSWE tips
- XSS grade is measured by **chain impact**, not `alert(1)`.
- Always capture a clean privileged request before writing JS.
- Script mail delivery and verification; don’t rely on GUI clicking for every retry.
- Time box filter bypass experiments; pivot sanitizer bypass techniques systematically.
- Report: show privileged boundary crossing clearly.

### Pitfalls
- XSS in user-only views that admin never opens
- HttpOnly cookies → cannot steal session via `document.cookie` (still can CSRF/session ride)
- Over-large payloads stripped by mail filters
- Plugin installed but not in web-exec path

---

## Related resources

| Resource | Location |
|----------|----------|
| Conceptual study | `Atmail-6.4-XSS-RCE-Study.md` |
| PoC | `poc-examples/atmail-xss-rce/` |
| XSS→RCE guide | `guides/XSS-to-RCE-Chaining.md` |
| Upload guide | `guides/File-Upload-to-RCE.md` |
| Chain trees | `guides/Chain-Decision-Trees.md` |
