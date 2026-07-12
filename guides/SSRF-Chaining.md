# SSRF Chaining Methodology

**Why**: Recent WEB-300 reviews list advanced SSRF alongside classic classes. Alone, SSRF is recon; chained, it becomes RCE or secret theft.

**Related**: XXE guide (SSRF via XML) · Challenge-Lab-Playbook · Chain-Decision-Trees.

---

## 1. Find SSRF

### White-box

```bash
rg -n "curl_exec|file_get_contents\s*\(\s*\$|HttpClient|RestTemplate|requests\.(get|post)|axios\.|fetch\(|WebClient|HttpURLConnection|curl_setopt" 
rg -n "url=|target=|webhook|callback|redirect|proxy|fetch" --glob '*.{php,js,java,cs,py}'
```

### Black-box

- Features: “import from URL”, webhooks, PDF renderers, link previews, health checks, avatar by URL  
- Observe DNS/HTTP hit on collaborator when you supply a URL  

---

## 2. Classification

| Type | Notes |
|------|--------|
| Basic | Server fetches attacker URL |
| Blind | Only timing/DNS/OOB |
| Filtered | Block localhost, only http/https, keyword bans |
| Protocol | `file://`, `gopher://`, `dict://` (environment-dependent) |

---

## 3. Impact paths (chain trees)

```text
SSRF confirmed
├─ Cloud metadata (169.254.169.254) → keys/creds → lateral
├─ Internal admin HTTP → auth bypass / deserial / debug endpoints
├─ Redis/memcached/gopher chains (rare, high impact)
├─ file:// → LFI-like read (if allowed)
├─ Hit localhost app ports → second-order vulns
└─ XSS/PDF renderer → other issues
```

Exam mindset: map **what the server can reach** that you cannot from outside.

---

## 4. Bypass ideas (study list)

- IP encoding (decimal, hex, IPv6, DNS rebinding — time box)  
- Redirect open to internal after allow-list check on first hop  
- Alternate hostnames (`localtest.me`, etc.)  
- URL parser differentials (`@`, `#`, backslash)  

Use PortSwigger SSRF labs; script fetch + OOB verification.

---

## 5. PoC stages

```text
recon_feature()
probe_collaborator()
enumerate_internal_ports_or_paths()
exfil_or_hit_secondary_vuln()
verify_impact()
```

Prefer OOB DNS/HTTP for blind cases (`snippets` + http.server / collaborator).

---

## 6. XXE intersection

XXE external HTTP entities are SSRF with XML packaging — reuse OOB DTD skills from `guides/XXE-Attack-Vectors.md`.

---

## 7. Defenses (report)

- Allow-list destinations; block link-local/metadata  
- No attacker-controlled URLs to privileged networks  
- Disable unnecessary URL schemes  
- Network egress controls from app tier  

---

## 8. OSWE tactics

- Treat SSRF as **routing to a new attack surface**, not the end.  
- After internal hit, re-enter sink greps as if new host.  
- Script discovery of internal paths once one port responds.  
