# OSWE Study Roadmap

**Goal**: Systematic preparation for OffSec WEB-300 (OSWE) focusing on white-box code review, vulnerability chaining, and production-quality PoC development.

**Duration**: 6-10 weeks depending on prior experience (assume 15-20 hours/week).

**Core Philosophy** (from course + successful candidates):
- Read the source → find the bug → weaponize it end-to-end in a script.
- Script *everything* — even "simple" steps.
- Report as you go.
- Master  the 6-8 primary vuln classes in the syllabus; variations and chains appear on exam.
- Time management: recon 10-15 min, vuln ID + manual 30-45 min, PoC 60-90+ min, docs 20-30 min per target.

---

## Prerequisites

Before diving deep:
- Solid web app pentest basics (Burp Suite Pro strongly recommended, HTTP, cookies, sessions, auth flows).
- Comfortable with Python `requests` (or `httpx`), argparse, sessions, proxies.
- Basic SQL, at least one of Java/.NET/PHP source reading ability (decompilers: jd-gui, dnSpy, etc.).
- Linux comfort (reverse shells, netcat, python -m http.server, etc.).
- Git + Markdown note taking.

**Quick self-check**: Can you write a 50-line Python script that logs into a form, extracts a token, and submits an authenticated request with Burp proxy support? If not, spend 1 week on Exploit Writing for OSWE.md + PortSwigger labs first.

**Track yourself**: Copy habits into [Progress-Tracker.md](Progress-Tracker.md) and log sessions under [study-log/](study-log/). For exam week ops, use [Exam-Day-Runbook.md](Exam-Day-Runbook.md).

---

## Recommended Lab / Practice Sources (in order)

1. **OffSec WEB-300 course labs + Challenge Labs** (primary — do all modules, complete and fully script the 6+ white-box Challenge Labs. These are the closest to exam machines).
2. **This repo's PoC examples + Notes** (study patterns, reproduce locally where possible).
3. **PortSwigger Web Security Academy** (free advanced labs for modern context + breadth — SQLi, deserial, SSRF, SSTI, prototype pollution, XXE, file upload, etc.; pair every lab with a mini non-interactive PoC).
4. **bmdyy GitHub labs** (highly recommended across 2025-2026 reviews): tudo (PHP), testr (Python IDE XSS/code inj), order (blind SQLi ORDER BY), and others. Docker-friendly practice for white-box review + exploitation.
5. **PentesterLab** (selected exercises: SQLi to Shell series, XSS + MySQL FILE, etc.).
6. **HackTheBox** (web machines + dedicated playlists for OSWE-style vulns — see README).
7. **VulnHub** (SecureCode, dev/random/pipe, Potato, etc.).
8. **Code review practice**: codereviewlab.com, Sonar security code challenges, OWASP Secure Coding Dojo, Secure Code Review challenges on GitHub.

**Docker teaching labs (recommended daily practice)**:
```bash
cd labs && ./labctl.sh up && ./labctl.sh urls
```
Full catalog/ports: [labs/README.md](labs/README.md) · pairing: [Lab-Setup-Matrix.md](Lab-Setup-Matrix.md).
Each PoC has `poc-examples/*/lab/` with Dockerfile + compose.

---

## 8-Week Study Plan

### Week 1: Foundations + PoC Methodology
- Read: `Building a Reusable OSWE PoC Skeleton.md` (full), `Exploit Writing for OSWE.md` (full), `COMPLETE-POC-GUIDE.md`.
- Study: `poc-examples/advanced-skeleton/` (modules, patterns). Run the examples.
- Practice: PortSwigger "SQL injection" + "File upload" sections; write 3-4 small PoCs (login + auth token reuse, simple param tampering).
- Code review: Pick one small open source app; spend 45 min hunting dangerous functions using `guides/Dangerous-Sinks-Cheatsheet.md`.
- Drills: `Speed-Drills.md` D1 (skeleton bootstrap); start `study-log/` + `Progress-Tracker.md`.
- Output: Your first "stage-based" PoC using the skeleton for a simple vuln.
- Repo resources: OSWE-PoC-Skeleton-Guide.md, advanced-skeleton/QUICKSTART.md, Exam-Day-Runbook (skim once).

**Milestone**: Comfortable creating a new PoC dir from skeleton in <15 min.

### Week 2: SQL Injection (MySQL + Second Order + Postgres)
- Primary: `guides/Advanced-SQLi-Techniques.md`, `guides/Blind-SQLi-Automation.md`, `notes/SECOND-ORDER-SQLI.md`, `poc-examples/second-order-sqli/`, `poc-examples/manageengine-sqli/`.
- MSSQL focus: `poc-examples/mssql-sqli-xp-cmdshell/`, `notes/MSSQL-SQLI-XP-CMDSHELL.md`, `guides/Advanced-SQLi-Techniques.md` (xp_cmdshell, OLE).
- Postgres RCE: `guides/Postgres-SQLi-to-RCE.md` + ManageEngine case study.
- Practice: PentesterLab SQLi to Shell (MySQL + Postgres editions), PortSwigger blind + second-order labs. Script binary-search extraction yourself.
- Code review patterns: string concat in queries, prepared statements misuse, stored procs.
- Challenge: Automate full chain on one manageengine-like or second-order target.
- Extras: MySQL LOAD_FILE / INTO OUTFILE, Postgres UDF/COPY/lo_export.
- Drills: Speed D2; Cold-Start Card C or H.

**Milestone**: Reliable time-based + boolean blind SQLi PoC with <10 requests per char extraction + RCE path.

### Week 3: PHP Type Juggling + Object Injection / Auth Chains
- Type juggling: `guides/PHP-Type-Juggling-Methodology.md`, `notes/ATUTOR-2.2.1-TYPE-JUGGLING.md`, `poc-examples/atutor-type-juggling/`, old OWASP PHP Magic Tricks PDF.
- PHP Object Injection: `guides/PHP-Deserialization-Patterns.md`, `notes/PHP-OBJECT-INJECTION.md`, `poc-examples/php-object-injection/`.
- Full chain example: `notes/ATUTOR-2.2.1-AUTH-RCE.md`, `poc-examples/atutor-type-juggling/`.
- Practice: ATutor 2.2.1 install (or equivalent), bmdyy labs if available, PortSwigger PHP type juggling if present.
- Focus: Magic hashes (0e...), POP chain construction on paper before coding, PHAR deserialization.
- Drills: Speed D6; Cold-Start Card A.

**Milestone**: Working type juggling auth bypass + file upload RCE PoC; ability to build a basic POP chain from 3-4 classes.

### Week 4: Java Deserialization + XXE
- Java: `guides/Java-Deserialization-Methodology.md` (master this), `poc-examples/java-deserialization-commons/`, `notes/JAVA-DESERIALIZATION-COMMONS-COLLECTIONS.md`.
- XXE: `guides/XXE-Attack-Vectors.md`, `poc-examples/xxe-file-read-ssrf/` (full Notes.md lab manual), `notes/XXE-FILE-READ-SSRF.md`.
- Tools: ysoserial (multiple gadget chains), marshalsec.
- Practice: Java deserial webapp from README, XXE-Study GitHub, custom XXE in SVG/DOCX if possible.
- Code review: ObjectInputStream, XMLDecoder, XStream, Jackson default typing; sinks cheatsheet Java section.
- Variations: signed objects, JEP 290 bypasses, different delivery (headers, files, RMI).
- Drills: Speed D4 (deserial card A); Cold-Start XXE path via Speed D8.

**Milestone**: ysoserial-driven PoC with 3+ delivery methods + callback verification; XXE file read + OOB exfil working script.

### Week 5: .NET Deserialization + Node.js + SSTI
- .NET: `guides/DotNet-Deserialization-Guide.md`, `notes/DOTNET-VIEWSTATE-DESERIALIZATION.md` + `notes/DOTNETNUKE-COOKIE-DESERIALIZATION.md`, `poc-examples/dotnet-viewstate-deserialization/` (full Notes.md lab manual).
- Node: `notes/NODEJS-DESERIALIZATION.md`, `poc-examples/nodejs-deserialization/` (full Notes.md), Bassmaster case for JS injection.
- SSTI: `guides/SSTI-Exploitation-Guide.md`, `notes/SSTI-JINJA2-FLASK.md`, `poc-examples/ssti-jinja2-flask/`.
- Tools: ysoserial.net, dnSpy for decompile.
- Practice: Pwnworks .NET challenges, Celestial HTB (Node), GoSecure SSTI workshop, custom Flask/Jinja apps.
- Focus: Machine key attacks, ObjectDataProvider, node-serialize IIFE, Jinja2 MRO escapes + polyglots.
- Drills: Cold-Start Cards B, E, G.

**Milestone**: At least one full PoC per category; comfortable reading decompiled .NET or JS source for gadgets.

### Week 6: File Upload to RCE + XSS to RCE Chains (Core Chaining Week)
- File upload: `guides/File-Upload-to-RCE.md`, `poc-examples/file-upload-rce/`, `notes/FILE-UPLOAD-TO-RCE.md`, `guides/LFI-to-RCE.md` (upload+include chains).
- Study syllabus patterns (extension filters, content-type, magic bytes, double extensions, path traversal in upload).
- XSS chains: `guides/XSS-to-RCE-Chaining.md`, `Atmail-6.4-XSS-RCE-Study.md`, `poc-examples/atmail-xss-rce/`, `notes/ATMAIL-6.4.md` (full case).
- Decision trees: `guides/Chain-Decision-Trees.md` (upload + XSS branches).
- Additional: HTB Popcorn / Vault (file upload), Atmail PoC.
- Drills: Speed D5, D7; Cold-Start Cards D, F.
- Create your own mini vulnerable upload app (PHP/ASP.NET) and exploit all common bypasses using the new PoC as reference.
- Practice chaining: XSS → CSRF → upload plugin/shell, or SQLi → file write → include.

**Milestone**: File upload bypass matrix (8+ techniques) + end-to-end RCE PoC; full Atmail-style multi-stage script.

### Week 7: Code Review Mastery + Integration + Exam Simulation
- Deep: `guides/Code-Review-Checklists.md` (full), `guides/Dangerous-Sinks-Cheatsheet.md`, OWASP Code Review Guide.
- Revisit all previous weeks' source patterns. Practice 30-45 min "first pass" code reviews on new targets.
- Full chains: Pick 2-3 machines from bmdyy / HTB / VulnHub; treat as mini-exam (time-boxed, full PoC + notes in CASE-template format). Use `guides/Chain-Decision-Trees.md` when stuck.
- Reporting: `Report-Snippet-Templates.md` + OffSec-style cover from README links. "Report as you go".
- Speed drills: `Speed-Drills.md` full set; Cold-Start Card I (3h mock slice).
- Ops: Internalize `Exam-Day-Runbook.md` time model.

**Milestone**: Complete 2 simulated "exam machines" (source provided or whitebox) end-to-end with PoC + report snippet in <4 hours each.

### Week 8: Polish, Gaps, Full Review + Light Practice
- Re-read weak areas from `study-log/weak-areas.md` and `Progress-Tracker.md`.
- Fill gaps: Postgres RCE specifics, more .NET gadgets, advanced WAF bypasses, blind XXE variations, PHAR + file upload combos.
- Review all PoC code in this repo; refactor one of yours to be cleaner/faster.
- Light: 1-2 new PortSwigger or PentesterLab + script it.
- Mental: Exam guide (proctoring, reporting rules, ~48h practical + 24h report). Prepare clean Kali + tools + templates. Recent passers emphasize scripting speed and Obsidian-to-PDF reporting.
- Final: One full "dry run" on a complex chain you haven't touched; Go/No-Go checklist in Progress-Tracker.

---

## Topic Priority for Exam (High → Medium)

1. SQLi → RCE (MSSQL xp_cmdshell / OLE, MySQL file ops, Postgres UDF/COPY) + blind techniques + second-order.
2. Deserialization (Java Commons* / ysoserial, .NET ViewState + ObjectDataProvider / ysoserial.net, PHP unserialize + POP/PHAR, Node node-serialize).
3. File upload bypasses → webshell / malicious plugin / code exec.
4. XSS (stored/reflected) in privileged context → CSRF / admin action abuse → RCE.
5. Type juggling (PHP magic hashes / loose ==) → auth bypass → further access.
6. SSTI (Jinja2/Twig/etc sandbox escapes).
7. XXE (file read, SSRF, OOB, blind via errors).
8. Supporting: Auth bypasses, LFI to RCE, command injection, business logic abuse.

Expect chains, not isolated vulns.

---

## Core WEB-300 / OSWE Lab Patterns & Practice Targets

The WEB-300 syllabus uses real-world case studies to teach repeatable white-box chains that lead to auth bypass or RCE. These classic patterns remain highly relevant:

| Pattern / Classic Example | Focus Areas | Primary Repo Resources |
|---------------------------|-------------|------------------------|
| XSS → privileged abuse → RCE (e.g. Atmail) | Stored/reflected XSS discovery, request minimization, session riding / admin action abuse, file upload RCE | `Atmail-6.4-XSS-RCE-Study.md`, `poc-examples/atmail-xss-rce/`, `notes/ATMAIL-6.4.md` |
| Blind SQLi → auth bypass + upload RCE (e.g. ATutor) | Response comparison / data exfil, parameterization misuse, file upload filter bypasses (zip traversal etc.) | `notes/ATUTOR-2.2.1-AUTH-RCE.md`, `guides/Advanced-SQLi-Techniques.md` |
| PHP Type Juggling (e.g. ATutor) | Loose `==` comparisons, magic hashes (0e...), auth token / reset bypasses | `notes/ATUTOR-2.2.1-TYPE-JUGGLING.md`, `poc-examples/atutor-type-juggling/` |
| Java SQLi → DB RCE (e.g. ManageEngine servlet) | Source recovery (decompile + web.xml servlet maps), blind SQLi bypasses, Postgres large objects / UDF / COPY for shells | `notes/MANAGEENGINE-APPS-MANAGER-SQLI-RCE.md`, `poc-examples/manageengine-sqli/` |
| Node.js JS Injection (e.g. Bassmaster) | Plugin / prototype issues, arbitrary code exec sinks | `notes/BASSMASTER-1.5.1-JS-INJECTION.md`, `poc-examples/bassmaster-js-injection/` |
| .NET Deserialization (e.g. DNN cookie) | XmlSerializer gadgets, ObjectDataProvider + ExpandedWrapper, ysoserial.net | `notes/DOTNETNUKE-COOKIE-DESERIALIZATION.md`, `poc-examples/dotnet-viewstate-deserialization/` |

**Workflow for any target or module**:
- Read source / decompile → map entry points (servlets, routes, handlers) → trace tainted data to sinks.
- Confirm manually (Burp), then immediately build incremental stages in Python (`requests` + proxy toggle).
- Reproduce / extend using the advanced skeleton.
- Update `notes/*.md` (CASE template) and refactor PoC for clarity/logging.
- Script full non-interactive chains (the exam expects one working script per target that gets the flags).

Additional modern emphasis (from recent passers):
- Complete and fully automate the official Challenge Labs (multiple white-box + black-box) — these are the closest practice to the exam format.
- Practice remote debugging and source recovery early.
- Expect to spend significant time scripting (100-250+ LOC per machine is common).
- Report as you go (many use Obsidian + export to PDF + official cover).

See also the curated modern reviews in README.md for 2025-2026 experiences and tips.

---

## Daily / Weekly Habits That Work

- **Code review sessions**: 3-4x/week, 30-60 min on fresh code. Use `guides/Code-Review-Checklists.md` + `guides/Dangerous-Sinks-Cheatsheet.md`. Document in CASE-template.md format.
- **PoC increments**: Never "just test manually". After manual confirmation, immediately start scripting the next stage.
- **Notes**: After every lab/target, fill or update a case study (Environment / Recon / Hypothesis / Chain / Evidence / Findings). Copy `notes/CASE-template.md`.
- **Burp + Python loop**: Every target you touch, proxy your PoC. Fix issues faster.
- **Time tracking**: Log sessions in `study-log/` and time per stage. Goal: reduce PoC dev time week over week.
- **Drills**: 1–2 speed drills mid-week; one cold-start card on weekends.
- **Review Friday**: Re-read your own PoCs + notes from 2 weeks ago; improve one; update Progress-Tracker and weak-areas.

---

## Tools & Environment Setup

- Kali (or Parrot) with latest Burp, Python 3.10+, uv or pipenv, git.
- Docker Desktop (for many targets in this repo).
- jd-gui, jadx (Java), dnSpy / ILSpy (.NET), VSCode + extensions.
- ysoserial + ysoserial.net (pre-built jars in PATH or payloads/ dirs).
- revshells.com or PayloadsAllTheThings for quick shells.
- Obsidian / Typora / Markdown + PDF export for personal notes + report drafting.

See individual poc-examples/*/Notes.md for per-vuln tool notes.

---

## Measuring Readiness

Use [Progress-Tracker.md](Progress-Tracker.md) Go/No-Go section. Summary bar:

- You can stand up a new skeleton PoC for a described vuln in <20 minutes.
- You have 6-8+ solid, documented, working end-to-end PoCs (one per major class) and have fully automated several Challenge Lab-style targets.
- You can perform a 45-min white-box code review pass on a medium app (decompile if needed) and find the primary vuln + at least one secondary + a chaining path.
- You have written at least 2 full "exam-style" reports (even if internal) using your preferred note-to-PDF workflow (`Report-Snippet-Templates.md`).
- You can explain gadget chain construction, blind SQLi extraction, file upload bypass decision tree, and source-to-sink tracing from memory.
- You have run at least one timed dry-run with `Exam-Day-Runbook.md` open.

---

## Exam Day Tips (from recent passers + this repo)

Primary checklist: **[Exam-Day-Runbook.md](Exam-Day-Runbook.md)**.

- Read the latest OSWE Exam Guide (link in README).
- Report as you go — many successful candidates use Obsidian/Markdown notes during the exam then export PDFs (combine with official cover page). Submit flags early. Use `Report-Snippet-Templates.md`.
- Use the PoC skeleton you practiced; don't invent new structure under time pressure. Include easy proxy toggle for debugging.
- Expect significant time on scripting (100-250+ lines per target common for full chains). Practice full automation of Challenge Labs.
- Flags first, beautiful code second (but commented and clean enough to understand). Always revert targets when testing.
- If stuck >20-30 min on one vector, pivot via `guides/Chain-Decision-Trees.md` and come back; multiple paths often exist.
- Document assumptions and failed attempts briefly (examiners like process). Take breaks.
- Remote debugging and decompilation skills pay off — practice them on the course content.

---

## Resources Added / Curated (see also README)

Recent high-value reviews & guides (2025-2026):
- The OSWE Guide (2026) — https://www.brunorochamoura.com/posts/oswe-guide/
- WEB-300 OSWE Review — https://medium.com/@jake.mayhew/web-300-oswe-review-offsec-web-expert-46074fbdb237
- OffSec OSWE Review (2025) — https://steflan-security.com/offsec-web-expert-oswe-review/
- OffSec AWAE/OSWE Review 2026 — https://rootshooter.medium.com/offsec-awae-oswe-review-2026-cad3c1e15946
- Obligatory OSWE Retrospective (2025) — https://notateamserver.xyz/blog/oswe-review/
- OSWE Certification Ultimate 2026 Guide — https://flashgenius.net/blog-article/oswe-certification-ultimate-2025-guide-to-offsec-web-300

Other frequently praised:
- bmdyy GitHub labs (tudo, testr, order and siblings) — https://github.com/bmdyy
- PortSwigger Web Security Academy + script every relevant lab
- Code review practice: codereviewlab.com and Sonar/OWASP challenges
- Community PoC skeletons and repos (this one, wetw0rk/AWAE-PREP forks, rizemon/exploit-writing-for-oswe)

This roadmap + the rest of the repo (PoCs, guides, case studies) gives you a closed-loop practice system: learn concept → study real PoC → reproduce + modify → apply to new target (including modern Challenge Labs) → document.

Good luck — consistent deliberate practice with the white-box + script mindset is what separates passers.

---

**Update this roadmap** as you progress. Track completed PoCs and weak areas here.
