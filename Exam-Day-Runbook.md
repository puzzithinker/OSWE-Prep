# Exam-Day Runbook (WEB-300 / OSWE)

Practical ops checklist for the ~48h practical + 24h report window. Use with your PoC skeleton and `Report-Snippet-Templates.md`.

**Not official OffSec policy** — always re-read the current [OSWE Exam Guide](https://help.offensive-security.com/hc/en-us/articles/360046869951-WEB-300-Advanced-Web-Attacks-and-Exploitation-OSWE-Exam-Guide) before sitting.

---

## Pre-exam (T-24h to T-0)

### Environment
- [ ] Fresh Kali (or known-good snapshot) with tools installed
- [ ] Burp Suite Pro licensed and proxy working
- [ ] Python 3.10+, `uv` or venv, `requests`/`httpx`
- [ ] jd-gui / jadx, dnSpy or ILSpy, VSCode/Cursor
- [ ] ysoserial + ysoserial.net on PATH or in a known folder
- [ ] netcat, nmap, curl, git, markdown→PDF path tested
- [ ] PoC skeleton template ready to copy (`poc-examples/advanced-skeleton/`)
- [ ] Reverse shell listeners: bash, PowerShell one-liners bookmarked
- [ ] Time sync correct; proctoring tool tested if required

### Knowledge warm-up (30–60 min)
- [ ] Skim sink cheatsheet (`guides/Dangerous-Sinks-Cheatsheet.md`)
- [ ] Skim chain decision trees (`guides/Chain-Decision-Trees.md`)
- [ ] Open one prior PoC and re-run mentally: stages 0→N
- [ ] Confirm report export path (Obsidian/Markdown → PDF + cover)

### Mindset
- Flags first, polish second
- Script everything after first manual confirmation
- Report as you go (do not batch reporting to the end)
- If stuck >25–30 min on one vector: document, pivot, return later

---

## Time model (per target)

Adjust to actual exam machine count/points. Treat each target as:

| Phase | Budget | Goal |
|-------|--------|------|
| Recon + source map | 10–20 min | Entry points, roles, tech stack, decompile if needed |
| Vuln ID + manual confirm | 30–45 min | One solid sink with proof |
| Chain expansion | 20–40 min | Path to flag / RCE / privileged access |
| PoC scripting | 60–120 min | Non-interactive end-to-end script |
| Docs / screenshots | 20–30 min | Report section + evidence |
| Buffer / pivot | 15–30 min | Second path if primary dies |

**Hard rule**: After manual confirm, open the skeleton and start stages immediately. Do not “just one more manual test” for 40 minutes.

---

## First 30 minutes (any machine)

1. **Scope & notes file** — copy CASE template; fill Environment (URLs, ports, creds if given, stack).
2. **Map surface** — spider / browse; note auth roles; list interesting params and file types.
3. **Source access** — download source or decompile WARs/DLLs; note version strings.
4. **Tech fingerprint** — language (PHP/Java/.NET/Node), DB hints, template engine, upload paths.
5. **Dangerous-sink pass** — 10 min grep using `guides/Dangerous-Sinks-Cheatsheet.md`.
6. **Hypothesis** — write 1–2 vulnerability hypotheses before deep-diving.

---

## White-box first pass (45 min max)

```text
1. Entry points  → routes, servlets, controllers, .php includes
2. Auth gates    → what is public vs role-gated
3. Sinks         → SQL concat, unserialize, eval, XXE parsers, upload, SSTI
4. Data flow     → param/cookie/header/file → sink
5. Gadgets/tools → is ysoserial / file write / admin action nearby?
6. Pick one      → confirm manually → script stage 1
```

Stop grepping after you have a confirmed path. Finish the chain before hunting secondary vulns.

---

## Pivot rules

| Situation | Action |
|-----------|--------|
| Blind SQLi confirmed, no output | Binary-search extract; then RCE path (file write / xp_cmdshell / UDF) |
| Deserial sleep works, no shell | Change gadget; try reverse shell / webshell write; check egress |
| Upload accepted, 404 on shell | Find web root, LFI, include path, rename, double-ext |
| XSS only, no admin | Map admin-only actions; CSRF/session riding; stored vs reflected |
| Auth bypass, no RCE | Hunt upload, plugin install, config write, SQLi in admin area |
| Stuck >30 min | Note blockers, switch target or secondary vuln class |

---

## PoC discipline under time pressure

1. Copy advanced skeleton → `poc.py` for this target.
2. Stages always: recon → authenticate (if needed) → exploit → verify → cleanup notes.
3. Enable proxy toggle for debugging; disable for speed runs.
4. Log every HTTP status and key response snippet.
5. One working flag path > perfect code.
6. Keep secrets/URLs in argparse or env, not hard-coded mid-script mess.

Minimum viable PoC: non-interactive, takes IP/port/creds, prints flag or clear success marker.

---

## Reporting as you go

After each major stage succeeds:

1. Screenshot request/response or terminal proof (timestamped names).
2. Paste into report template section for that target.
3. Note exact payload class (not necessarily full exploit dump if policy limits — follow exam guide).
4. Record failed attempts briefly (process matters).

See `Report-Snippet-Templates.md`.

---

## Hourly check-in (use a timer)

- [ ] Flags captured this hour?
- [ ] Any target stuck >30 min without pivot?
- [ ] Report sections updated for completed stages?
- [ ] Sleep/eat/stretch if cognitive fog (48h is a marathon)

---

## Final 4–6 hours of practical

- [ ] All high-value flags locked
- [ ] Each target has a runnable PoC (or clearly documented manual chain if allowed)
- [ ] Evidence folders organized per target
- [ ] Re-run each PoC once clean (cold run) if time allows
- [ ] Note any leftover low-hanging fruit for last pass

---

## Report window

- [ ] Official cover / template requirements met
- [ ] Every flag has supporting narrative + evidence
- [ ] PoC usage documented (how to run)
- [ ] No credentials from unrelated systems; no non-exam data
- [ ] PDF renders correctly; TOC/headings consistent
- [ ] Submit early enough for upload issues

---

## Emergency kit (copy to sticky notes)

```text
Proxy:  http://127.0.0.1:8080
Listen: nc -lvnp 4444
HTTP:   python3 -m http.server 8000
Magic:  AC ED 00 05  (Java serial)
ViewState often starts: /wEP
PHP magic hash examples: 240610708 → 0e4620...
ysoserial: java -jar ysoserial.jar Gadget "cmd" > p.bin
ysoserial.net: ObjectDataProvider + ViewState plugin
Postgres sleep:  SELECT pg_sleep(5)
MSSQL sleep:     WAITFOR DELAY '0:0:5'
MySQL sleep:     SELECT SLEEP(5)
```

---

## Related repo files

| File | Use |
|------|-----|
| [Progress-Tracker.md](Progress-Tracker.md) | Pre-exam readiness |
| [Speed-Drills.md](Speed-Drills.md) | Timed practice |
| [Report-Snippet-Templates.md](Report-Snippet-Templates.md) | Report sections |
| [guides/Chain-Decision-Trees.md](guides/Chain-Decision-Trees.md) | Pivot paths |
| [guides/Dangerous-Sinks-Cheatsheet.md](guides/Dangerous-Sinks-Cheatsheet.md) | First-pass greps |
| [Lab-Setup-Matrix.md](Lab-Setup-Matrix.md) | Practice labs only |
| [OSWE-Study-Roadmap.md](OSWE-Study-Roadmap.md) | Overall plan |
