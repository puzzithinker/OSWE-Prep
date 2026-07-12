# Challenge Lab & Exam Playbook (WEB-300 / OSWE)

How to approach official **Challenge Labs** and the **exam** the way successful 2025–2026 candidates describe: structured white-box method, two-flag progression, full automation.

**Related**: [Exam-Day-Runbook.md](Exam-Day-Runbook.md) · [guides/Chain-Decision-Trees.md](guides/Chain-Decision-Trees.md) · [snippets/](snippets/) · [Report-Snippet-Templates.md](Report-Snippet-Templates.md)

This is study methodology, not a walkthrough of any official lab. Always follow the current [OSWE Exam Guide](https://help.offsec.com/hc/en-us/articles/360046869951-WEB-300-Advanced-Web-Attacks-and-Exploitation-OSWE-Exam-Guide).

---

## Mental model

```text
Anonymous / low-priv
        │
        ▼
   1st FLAG  — highest privilege inside the web app (often admin)
        │
        ▼
   Abuse privileged features
        │
        ▼
   2nd FLAG  — OS-level: file read / RCE / shell → proof file
        │
        ▼
   Single non-interactive PoC that does both (or clear staged scripts per rules)
```

Challenge Labs and the exam are **designed** around this progression. Use that structure to prioritise (without assuming any specific chain).

---

## Debug VM vs target VM

| | Debug VM | Target VM |
|--|----------|-----------|
| Purpose | Break things, attach debugger, confirm SQL/payloads | Real flags / simulated users |
| Access | Often SSH/root for inspection | Attack only as the app allows |
| Workflow | Develop & fix PoC here first | Final verification + flags |
| Habit | Do **not** depend on a pre-attached web IDE on exam day | Same exploit, different host |

**Exam habit**: reverse-engineer source yourself (decompile if needed), set up debugging if useful — see [guides/Remote-Debugging-and-Decompilation.md](guides/Remote-Debugging-and-Decompilation.md).

---

## Phase 0 — Setup (10–15 min)

- [ ] Notes file from `notes/CASE-template.md`
- [ ] Burp project + scope
- [ ] PoC dir from skeleton / `snippets/`
- [ ] Proxy toggle in script (`--proxy`)
- [ ] Listener / HTTP server ready for later stages
- [ ] Time box written for this lab (e.g. 4h mock)

---

## Phase 1 — Black-box tour (10–30 min)

**Do not open source yet.** Interact as a normal user. Proxy everything.

Document:

| Area | Questions |
|------|-----------|
| Register | Open? Invite? Email confirm? |
| Login | Errors leak users? Remember-me? |
| Reset | Token / OTP / link? |
| Profile | Upload? Hidden fields? |
| Content | Posts, tickets, comments (admin-viewable?) |
| Upload / download / export | Paths, types |
| Admin-only UI | Anything visible when unauth? |

Keep a list: **Input → Processing → Output** and every half-baked attack idea.

**Actionable**: timer on; curiosity over exploitation.

---

## Phase 2 — Source map (20–40 min)

Answer deliberately (not random grepping):

1. Language(s) and frameworks  
2. Routing / controllers / entrypoints  
3. Authn (cookie, JWT, session store) and Authz (roles)  
4. Template engine  
5. Database + ORM / raw SQL style  
6. Config files (`.env`, `web.config`, `application.properties`)  
7. Privileged features only admins get  

Quick high-value checks (then stop and attack):

- Config secrets  
- String-built SQL  
- Custom “sanitize” functions  
- Weak RNG for tokens  
- Deserial / `eval` / upload / XXE parsers  
- HttpOnly missing on session cookies  

See [guides/Dangerous-Sinks-Cheatsheet.md](guides/Dangerous-Sinks-Cheatsheet.md).

---

## Phase 3 — First flag (in-app privilege)

### Goal outcomes (examples)

- Create account when registration is closed  
- Hijack or impersonate admin  
- Promote self (`isAdmin`, role field)  
- Bypass access control on admin routes  

### Common pattern classes

| Pattern | Look for |
|---------|----------|
| XSS → session | Admin-visible sinks; cookie flags |
| XSS → CSRF / action | Privileged POSTs from admin browser |
| Profile / mass assignment | Hidden role fields |
| SQLi | Dump hashes, tokens, flip roles |
| File read (pre-admin) | Keys, JWT secrets, configs |
| Weak tokens | Reset / invite / OTP predictability — [Weak-Token-and-RNG.md](guides/Weak-Token-and-RNG.md) |
| Prototype pollution | Merge/clone of user JSON — [Prototype-Pollution-Methodology.md](guides/Prototype-Pollution-Methodology.md) |

### Metagame (fair use of lab design)

While hunting the **first** flag, deprioritise unauthenticated full OS RCE theories that would skip the whole design — unless evidence is overwhelming. After admin, deprioritise pure client-side issues that no longer expand OS impact.

### Automation

As soon as a step works manually:

```text
manual confirm → stage_N() in PoC → re-run from stage 0 → next step
```

Never leave “I’ll click this later” as the only path.

---

## Phase 4 — Second flag (OS impact)

Focus on **privileged** surfaces:

| Pattern | Notes |
|---------|--------|
| Command injection | Admin tools, exports, “test connection” |
| Plugin / theme / module upload | Code load on server |
| SQLi → DB file/RCE | Postgres COPY/LO, MSSQL xp_cmdshell, MySQL FILE |
| LFI / path traversal | Include + upload polyglot |
| XXE | Admin XML/SVG/DOCX parsers |
| SSTI | Report/templates as admin |
| Arbitrary write | Cron, webroot, config overwrite |
| SSRF | Reach internal admin / metadata / debug — [SSRF-Chaining.md](guides/SSRF-Chaining.md) |
| WebSocket command paths | [WebSocket-Attack-Patterns.md](guides/WebSocket-Attack-Patterns.md) |

Second flag is often **file read of a proof path**, not always a glamorous reverse shell. Prefer reliable in-band read when egress is painful.

---

## Phase 5 — PoC quality bar

Before “done”:

- [ ] argparse: target host/port, listener, optional proxy, no hard-coded secrets  
- [ ] Single command line gets flags or clear success markers  
- [ ] **Zero interactive prompts** during run  
- [ ] Proxy off for final runs  
- [ ] Revert / cold target → re-run **twice**  
- [ ] Works from a clean shell (exam Kali mindset)  
- [ ] Stages logged; failures exit non-zero  

See [snippets/](snippets/) and skeleton guides.

### Failure mode to avoid

> Got all flags manually → scripts flaky → fail grading  

Treat the **script as a deliverable**, not an afterthought. Re-test after every edit.

---

## Phase 6 — Report as you go

After each flag:

1. Finalise PoC stages up to that point  
2. Screenshots + stage log  
3. Draft report section (vuln, data flow, steps, impact)  
4. Then continue  

Tools: [Report-Snippet-Templates.md](Report-Snippet-Templates.md), optional [Sysreptor](https://github.com/syslifters/sysreptor) for practice reports.

---

## Mock exam protocol (use on Challenge Labs)

| Rule | Detail |
|------|--------|
| Time box | 3–6 hours per lab (adjust) |
| No hints first | Discord only after honest stuck time |
| Full PoC | Required even if flag already known |
| Notes | CASE template completed |
| Score yourself | 1st flag / 2nd flag / script reliability |

Do **all white-box** challenge labs before booking when possible. Treat black-box-only labs as optional skill practice (exam is white-box-first).

---

## Readiness checklist (Challenge Labs → exam)

- [ ] All white-box Challenge Labs completed without excessive spoiling  
- [ ] Each has a cold-running automated PoC  
- [ ] Snippet library populated from real pain points  
- [ ] Can decompile + attach debugger without hand-holding  
- [ ] Comfortable 1st-flag vs 2nd-flag prioritisation under time  
- [ ] Two full practice reports written  
- [ ] Exam-Day-Runbook internalized  

---

## Related repo resources

| Need | Path |
|------|------|
| Time boxes / exam ops | `Exam-Day-Runbook.md` |
| Pivot trees | `guides/Chain-Decision-Trees.md` |
| Sinks | `guides/Dangerous-Sinks-Cheatsheet.md` |
| Code snippets | `snippets/` |
| Docker practice apps | `labs/` |
| Progress | `Progress-Tracker.md` |

---

## Credits (methodology synthesis)

Preparation patterns reflected in public 2025–2026 write-ups (BRM OSWE Guide, Steflan, RootShooter, and others) — adapted for this repo’s structure. Not affiliated with OffSec.
