# DotNetNuke (DNN) — Cookie / Profile Deserialization → RCE

**Pattern**: Untrusted serialized .NET object graph in cookie (or similar client storage) → server deserializes with dangerous gadgets → RCE.  
**Related PoC**: `poc-examples/dotnet-viewstate-deserialization/` (ViewState-focused sibling patterns)  
**Guide**: `guides/DotNet-Deserialization-Guide.md`  
**Tools**: **ysoserial.net**, dnSpy, `web.config` machine keys when ViewState/MAC involved

Training discussions often reference older DNN lines (**&lt; 9.1.1** era vulnerabilities). Always match your exact lab version and public advisories.

---

## Environment

| Item | Typical lab value |
|------|-------------------|
| App | DotNetNuke CMS (version per lab) |
| Stack | IIS + ASP.NET |
| Auth | Forms auth cookies, DNN personalization cookies, profile data |
| Config | `web.config` (machineKey, httpRuntime, modules) |
| Goal | Forge cookie → gadget chain → command execution |

Windows lab VM recommended for realistic IIS + ysoserial.net workflow.

---

## Recon

### Entry points
- Cookies on all authenticated (and sometimes anonymous) requests
- Personalization / profile properties
- Any hidden fields carrying serialized blobs
- Web services / API with binary or XML .NET payloads

### Fingerprints
- `DNN*` cookies, `.DOTNETNUKE`, language/personalization cookies
- ASP.NET: `__VIEWSTATE`, `__EVENTVALIDATION`
- Response headers: `X-AspNet-Version`, Server IIS

### White-box / config
```text
web.config → machineKey, httpCookies, modules
DNN source / decompiled DLLs → Deserialize usage, XmlSerializer, BinaryFormatter, LosFormatter, ObjectStateFormatter
```

Search patterns:
```text
BinaryFormatter
LosFormatter
ObjectStateFormatter
XmlSerializer
TypeNameHandling  (JSON.NET)
Deserialize(
```

### Black-box
- Decode Base64 cookies; look for .NET serialization signatures
- Change one bit → behavior change / error (MAC fail vs deserialize error)
- Presence of detailed errors can leak types

---

## Vulnerability hypothesis

| Field | Detail |
|-------|--------|
| Class | Insecure deserialization (CWE-502) |
| Data flow | Attacker cookie → server deserialize → gadget (`ObjectDataProvider`, etc.) → `Process.Start` / equivalent |
| Preconditions | Gadget chain available in loaded assemblies; MAC/encryption weak, missing, or key known; endpoint deserializes untrusted data |
| Impact | RCE as app pool identity (`IIS APPPOOL\...`) |

### Conceptual flow

```text
ysoserial.net payload
    → set as DNN-related cookie / serialized profile blob
    → HTTP request to any page that loads personalization
    → deserializer builds object graph
    → malicious getters/ctors fire
    → OS command / reverse shell
```

Related sibling: **ViewState** deserialization when `machineKey` known (Exchange-style and many ASP.NET apps) — same gadget mindset, different transport.

---

## Chain outline

### Step 1 — Identify serialized client state
- Burp: list cookies; Base64 decode candidates
- Note encryption/MAC (unreadable blob vs structured XML)

### Step 2 — Recover keys or bypass integrity
- Read `web.config` / backups / source repo / misconfig disclosure
- Historical vulns: weak or exposed keys; certain DNN cookie handling flaws without needing classic ViewState
- If MAC fails: stop and re-check key/alg (`SHA1`/`HMACSHA256`, AES, etc.)

### Step 3 — Choose formatter + gadget
ysoserial.net examples (lab syntax varies by version):

```text
ysoserial.exe -g ObjectDataProvider -f BinaryFormatter -c "cmd /c whoami"
ysoserial.exe -p ViewState -g ... --validationkey=... --decryptionkey=...
```

For XML-oriented paths, pick plugins/formatters matching the app.

### Step 4 — Deliver
- Replace cookie value; send GET/POST to page that deserializes on load
- Prefer **OOB verify** first: `ping`, HTTP callback, `nslookup`

### Step 5 — Interactive control
- Reverse shell (PowerShell) or webshell write under site directory
- Mind app pool permissions and Defender

### Step 6 — Script
Python: login if needed → set cookie → trigger → verify.  
See `poc-examples/dotnet-viewstate-deserialization/poc.py` for session/payload orchestration patterns.

---

## Evidence

| Artifact | Proves |
|----------|--------|
| Cookie before/after | Delivery channel |
| `web.config` machineKey (lab) | Integrity bypass basis |
| Callback / whoami | Code exec |
| dnSpy screenshot of deserialize call | Root cause |

---

## Findings

### Root cause
Deserialization of attacker-controllable data (cookie/profile) without adequate type allow-listing, combined with powerful gadget chains in the .NET ecosystem and sometimes recoverable cryptographic keys.

### Fixes
1. Do not deserialize untrusted data; prefer simple session IDs server-side.
2. If serialization required: strict allow-listed types; avoid `BinaryFormatter` (obsolete/dangerous).
3. Protect ViewState: `enableViewStateMac`, strong unique `machineKey`, encrypt sensitive state.
4. Keep DNN/.NET components patched; remove unused modules reducing gadget surface.
5. Cookie flags: HttpOnly, Secure, SameSite (does not fix deserial but reduces theft).

### OSWE tips
- Treat **.NET deserial** as: find blob → find key/alg or insecure path → ysoserial.net → verify OOB → shell.
- dnSpy productivity beats guessing cookie formats.
- ObjectDataProvider + ExpandedWrapper patterns appear often in training material — understand *why* getters execute.
- Windows vs Linux payloads differ; match OS.
- Time box key hunting: check config files, installers, and repo secrets first.

### Pitfalls
- Wrong validation/decryption algorithm combo
- Payload too large for cookie limits — try alternate channel (ViewState, body)
- AV killing shell — use quieter verify (`whoami` to file, ICMP)
- Confusing DNN-specific cookie bugs with generic ViewState-only methodology

---

## Related resources

| Resource | Location |
|----------|----------|
| .NET methodology (expanded) | `guides/DotNet-Deserialization-Guide.md` |
| ViewState PoC example | `poc-examples/dotnet-viewstate-deserialization/` |
| Alvaro Muñoz talks / JSON attacks | README Learning Material |
| ysoserial.net | https://github.com/pwntester/ysoserial.net |
| Chain trees | `guides/Chain-Decision-Trees.md` |
