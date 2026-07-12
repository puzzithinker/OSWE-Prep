# Exam-Day Runbook (WEB-300 / OSWE)

Practical ops checklist for the ~48h practical + 24h report window. Use with your PoC skeleton, `snippets/`, `Challenge-Lab-Playbook.md`, and `Report-Snippet-Templates.md`.

**Not official OffSec policy** — always re-read the current [OSWE Exam Guide](https://help.offsec.com/hc/en-us/articles/360046869951-WEB-300-Advanced-Web-Attacks-and-Exploitation-OSWE-Exam-Guide) before sitting.

---

## Scoring & structure (verify in live guide)

Typical public description (confirm for your sitting):

| Item | Typical |
|------|---------|
| Practical length | ~47h 45m |
| Report window | ~24h after practical |
| Targets | Two web applications, white-box |
| Flags | Two per app (priv esc / in-app high priv + OS impact) |
| Pass mark | Often cited **85** points — **very little margin** |
| PoC rule | **Single non-interactive script** per machine (or as guide states); grader must not click for you |

**Planning implication**: treat both **first flags as mandatory**; you can often afford to miss **at most one** second flag — aim for all four.

---

## Hard constraints (2025–2026 passers + guide themes)

- [ ] **No AI / LLM assistance** during the exam — snippets must already exist in *your* library  
- [ ] PoC runs **without user interaction** mid-script  
- [ ] Listeners / `python -m http.server` may be started **before** the script (confirm guide)  
- [ ] Final validation: run PoCs on exam Kali after **reverting** targets  
- [ ] Remove Burp proxy from final script args  
- [ ] Parameterise IPs/ports — no hard-coded lab values  

---

## Pre-exam (T-24h to T-0)

### Environment
- [ ] Fresh Kali (or known-good snapshot) with tools installed  
- [ ] **Proctoring + webcam + mic tested the day before** (hardware fails burn time)  
- [ ] Burp Suite Pro licensed and proxy working  
- [ ] Python 3.10+, `uv` or venv, `requests`/`httpx`, `websocket-client` if needed  
- [ ] jd-gui / jadx, dnSpy or ILSpy, VSCode  
- [ ] ysoserial + ysoserial.net on PATH or in a known folder  
- [ ] netcat, nmap, curl, git, markdown→PDF (or Sysreptor practice workflow) tested  
- [ ] PoC skeleton + **`snippets/`** ready  
- [ ] Reverse shell listeners + HTTP server commands bookmarked  
- [ ] Time sync correct  

### Knowledge warm-up (30–60 min)
- [ ] `Challenge-Lab-Playbook.md` (1st vs 2nd flag)  
- [ ] Sink cheatsheet + chain trees  
- [ ] Skim prototype pollution + SSRF + weak RNG guides  
- [ ] Open one prior PoC cold  
- [ ] Report export path confirmed  

### Mindset
- Methodology first — panic grepping wastes hours  
- Flags + **reliable scripts** both required  
- Report as you go after each flag  
- Stuck >25–30 min: note, pivot target or phase, return later

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

1. **Read exam control panel / RoE** carefully (paths, objectives, points).  
2. **Brief glance at both targets** — pick the more approachable first (you need both eventually).  
3. **CASE notes** — Environment for target A.  
4. **Black-box tour 10–20 min** — no source yet (see Challenge-Lab-Playbook).  
5. **Source / decompile** — on **debug VM**; do not assume browser VS Code.  
6. **Setup debug workflow early** if useful (SSH, jadx, logs) — [Remote-Debugging-and-Decompilation.md](guides/Remote-Debugging-and-Decompilation.md).  
7. **Hypotheses** — 1st-flag vs 2nd-flag oriented.

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

1. Copy advanced skeleton + paste from `snippets/` (csrf, blind extract, upload).  
2. Stages: recon → auth/bypass → priv → OS impact → verify.  
3. Proxy on while developing; **off for final / grading-style runs**.  
4. After first flag: freeze stages, screenshot, draft report section, **then** push RCE.  
5. After all flags: revert targets, run every PoC from exam Kali **twice**.  
6. Fix “works on my burp session only” bugs (cookies, CSRF, missing headers).  

**Failure mode**: all flags manual, scripts fail for grader → fail.  

Minimum viable PoC: non-interactive, argparse targets, prints flag or clear marker.

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
| [Challenge-Lab-Playbook.md](Challenge-Lab-Playbook.md) | Two-flag methodology |
| [snippets/](snippets/) | Exam snippet library |
| [Reporting-Tooling.md](Reporting-Tooling.md) | Sysreptor / report flow |
| [Progress-Tracker.md](Progress-Tracker.md) | Pre-exam readiness |
| [Speed-Drills.md](Speed-Drills.md) | Timed practice |
| [Report-Snippet-Templates.md](Report-Snippet-Templates.md) | Report sections |
| [guides/Chain-Decision-Trees.md](guides/Chain-Decision-Trees.md) | Pivot paths |
| [guides/Dangerous-Sinks-Cheatsheet.md](guides/Dangerous-Sinks-Cheatsheet.md) | First-pass greps |
| [Lab-Setup-Matrix.md](Lab-Setup-Matrix.md) | Practice labs only |
| [OSWE-Study-Roadmap.md](OSWE-Study-Roadmap.md) | Overall plan |
