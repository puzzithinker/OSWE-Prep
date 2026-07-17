# SSRF Chaining — Case Notes

## Docker lab

`cd labs && ./labctl.sh up ssrf` — see [`lab/README.md`](lab/README.md).

---

## Environment

- URL: http://127.0.0.1:8115
- Internal: 127.0.0.1:9999 (in-container only)
- Flag: via SSRF to `/internal/flag`

## Vulnerability hypothesis

- Class: SSRF (CWE-918)
- Data flow: HTTP param `url` → server-side fetch → internal admin-like service
- Impact: read internal-only flag/secret

## Chain outline

1. Find `/fetch`  
2. Point at `http://127.0.0.1:9999/internal/flag`  
3. Parse flag from response  

## Findings

- Root cause: unvalidated URL fetch  
- Fix: allow-list destinations; block link-local/loopback from untrusted input; network policy  

## Methodology

- `guides/SSRF-Chaining.md`
