# OSWE Progress Tracker

Living checklist. Update after every serious lab session. Goal: honest readiness, not green boxes for morale.

**Readiness bar** (from Roadmap): skeleton in &lt;20 min, 6–8 end-to-end PoCs, 45-min white-box pass finds primary + chain, 2 exam-style reports, core techniques explainable cold.

---

## Meta

| Item | Value |
|------|-------|
| Exam target date | _YYYY-MM-DD_ |
| Hours/week planned | _15–20_ |
| Current week (roadmap) | _1–8_ |
| Weak areas (top 3) | 1. ___ 2. ___ 3. ___ |
| Last full dry-run date | _YYYY-MM-DD_ |

Update weak areas in `study-log/weak-areas.md` too.

---

## Foundations

| Skill | Can do cold? | Last practiced | Notes |
|-------|--------------|----------------|-------|
| Python session + login + CSRF token | ☐ | | |
| Burp proxy toggle in PoC | ☐ | | |
| Stage-based skeleton bootstrap &lt;15 min | ☐ | | |
| Markdown report section while exploiting | ☐ | | |
| Decompile Java (jd-gui/jadx) | ☐ | | |
| Decompile .NET (dnSpy/ILSpy) | ☐ | | |
| Reverse shell + HTTP payload server | ☐ | | |

---

## Vulnerability classes (exam-priority order)

Rate each: **N** = not started · **R** = read only · **M** = manual only · **S** = scripted once · **C** = cold/scripted reliably

| Class | Level | Manual confirm | Full PoC | Report snippet | Case study reviewed | Repo path |
|-------|-------|----------------|----------|----------------|---------------------|-----------|
| SQLi MySQL → file/RCE | | ☐ | ☐ | ☐ | ☐ | `guides/Advanced-SQLi-Techniques.md` |
| SQLi MSSQL xp_cmdshell/OLE | | ☐ | ☐ | ☐ | ☐ | `poc-examples/mssql-sqli-xp-cmdshell/` |
| SQLi Postgres → RCE | | ☐ | ☐ | ☐ | ☐ | `guides/Postgres-SQLi-to-RCE.md`, manageengine |
| Blind SQLi automation | | ☐ | ☐ | ☐ | ☐ | `guides/Blind-SQLi-Automation.md` |
| Second-order SQLi | | ☐ | ☐ | ☐ | ☐ | `poc-examples/second-order-sqli/` |
| Java deserialization | | ☐ | ☐ | ☐ | ☐ | `poc-examples/java-deserialization-commons/` |
| .NET ViewState / cookie deserial | | ☐ | ☐ | ☐ | ☐ | `guides/DotNet-Deserialization-Guide.md` |
| PHP object injection / PHAR | | ☐ | ☐ | ☐ | ☐ | `poc-examples/php-object-injection/` |
| Node deserialize / JS injection | | ☐ | ☐ | ☐ | ☐ | node + bassmaster examples |
| PHP type juggling | | ☐ | ☐ | ☐ | ☐ | `notes/ATUTOR-2.2.1-TYPE-JUGGLING.md` |
| File upload → RCE | | ☐ | ☐ | ☐ | ☐ | `guides/File-Upload-to-RCE.md` |
| XSS → privileged → RCE | | ☐ | ☐ | ☐ | ☐ | `guides/XSS-to-RCE-Chaining.md` |
| SSTI (Jinja/Twig-class) | | ☐ | ☐ | ☐ | ☐ | `poc-examples/ssti-jinja2-flask/` |
| XXE file read / OOB / SSRF | | ☐ | ☐ | ☐ | ☐ | `poc-examples/xxe-file-read-ssrf/` |
| LFI → RCE | | ☐ | ☐ | ☐ | ☐ | `guides/LFI-to-RCE.md` |
| Prototype pollution | | ☐ | ☐ | ☐ | ☐ | `guides/Prototype-Pollution-Methodology.md` |
| SSRF chaining | | ☐ | ☐ | ☐ | ☐ | `guides/SSRF-Chaining.md` |
| Weak tokens / RNG | | ☐ | ☐ | ☐ | ☐ | `guides/Weak-Token-and-RNG.md` |
| WebSocket attacks | | ☐ | ☐ | ☐ | ☐ | `guides/WebSocket-Attack-Patterns.md` |
| Remote debug / decompile | | ☐ | — | ☐ | ☐ | `guides/Remote-Debugging-and-Decompilation.md` |
| Code review first pass (45 min) | | ☐ | — | ☐ | ☐ | `guides/Code-Review-Checklists.md` |
| Challenge Lab methodology | | ☐ | ☐ | ☐ | ☐ | `Challenge-Lab-Playbook.md` |
| Snippet library maintained | | ☐ | — | — | ☐ | `snippets/` |

**Target before booking exam**: all high-priority rows at **S** or **C**; at least 6 at **C**.

---

## Classic chain case studies

| Case | Read | Lab stood up | Manual chain | Scripted | Notes quality OK |
|------|------|--------------|--------------|----------|------------------|
| Atmail XSS→RCE | ☐ | ☐ | ☐ | ☐ | ☐ |
| ATutor type juggling | ☐ | ☐ | ☐ | ☐ | ☐ |
| ATutor auth/SQLi→RCE | ☐ | ☐ | ☐ | ☐ | ☐ |
| ManageEngine SQLi→Postgres RCE | ☐ | ☐ | ☐ | ☐ | ☐ |
| Bassmaster JS injection | ☐ | ☐ | ☐ | ☐ | ☐ |
| DNN / .NET cookie or ViewState | ☐ | ☐ | ☐ | ☐ | ☐ |
| Java Commons Collections | ☐ | ☐ | ☐ | ☐ | ☐ |

---

## Official / external practice

| Resource | Status | Scripted? | Notes |
|----------|--------|-----------|-------|
| WEB-300 modules (all) | ☐ | ☐ | |
| Challenge Labs (white-box) | ☐ | ☐ | Closest to exam |
| Challenge Labs (black-box) | ☐ | ☐ | |
| bmdyy labs (tudo, testr, order…) | ☐ | ☐ | |
| PortSwigger: SQLi + deserial + XXE + SSTI + upload | ☐ | ☐ | Mini-PoC each |
| PentesterLab SQLi to Shell series | ☐ | ☐ | |
| 2× timed “exam machine” dry runs | ☐ | ☐ | &lt;4h each + report |

---

## PoC portfolio (your scripts)

| # | Target / class | LOC ~ | Cold re-run OK? | Path |
|---|----------------|-------|-----------------|------|
| 1 | | | ☐ | |
| 2 | | | ☐ | |
| 3 | | | ☐ | |
| 4 | | | ☐ | |
| 5 | | | ☐ | |
| 6 | | | ☐ | |
| 7 | | | ☐ | |
| 8 | | | ☐ | |

---

## Reporting practice

| Artifact | Done | Date |
|----------|------|------|
| Report snippet templates customized | ☐ | |
| Full practice report #1 | ☐ | |
| Full practice report #2 | ☐ | |
| PDF export pipeline verified | ☐ | |
| Exam-day runbook read once | ☐ | |

---

## Speed drills (from Speed-Drills.md)

| Drill | Best time | Target | Date |
|-------|-----------|--------|------|
| Skeleton bootstrap | | &lt;15 min | |
| Boolean blind 1-char extract logic | | &lt;10 min code | |
| ysoserial payload + delivery outline | | &lt;10 min | |
| First-pass sink hunt on sample app | | &lt;45 min | |
| File-upload bypass decision | | &lt;5 min plan | |

---

## Weekly review (copy per week)

```markdown
### Week of YYYY-MM-DD
- Hours studied:
- PoCs completed/improved:
- Weak area progress:
- Next week focus:
- Blockers:
```

---

## Go / No-Go (exam booking)

Book only if most of these are true:

- [ ] 6+ cold, documented, end-to-end PoCs across different classes
- [ ] Blind SQLi extraction scripted without copy-paste panic
- [ ] At least one deserial class (Java or .NET) cold
- [ ] At least one full multi-stage chain (XSS or auth→upload or SQLi→RCE) cold
- [ ] Challenge Labs (or equivalent) fully scripted where possible
- [ ] Two practice reports written
- [ ] Exam-Day-Runbook internalized
- [ ] Sleep and logistics plan for 48h exists
