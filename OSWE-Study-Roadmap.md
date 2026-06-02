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

---

## Recommended Lab / Practice Sources (in order)

1. **OffSec WEB-300 course labs + Challenge Labs** (primary — do all, script the chains).
2. **This repo's PoC examples + Notes** (study patterns, reproduce locally where possible).
3. **PortSwigger Web Security Academy** (free advanced labs for modern context + breadth; pair each with a mini PoC).
4. **PentesterLab** (selected exercises: SQLi to Shell series, XSS + MySQL FILE, etc.).
5. **bmdyy student labs** (GitHub repos with OSWE-like whitebox challenges — highly recommended in recent reviews).
6. **HackTheBox** (machines tagged with relevant vulns: file upload, deserial, SQLi, etc. — see README HTB list and Ippsec videos).
7. **VulnHub** (SecureCode, dev/random/pipe, etc.).
8. **Code review practice**: codereviewlab.com, Hacker101 source review, OWASP code review guide.

**Docker-friendly targets in this repo** (see individual Notes.md for setup):
- Many have Docker or simple LAMP/Win VM instructions.

---

## 8-Week Study Plan

### Week 1: Foundations + PoC Methodology
- Read: `Building a Reusable OSWE PoC Skeleton.md` (full), `Exploit Writing for OSWE.md` (full), `COMPLETE-POC-GUIDE.md`.
- Study: `poc-examples/advanced-skeleton/` (modules, patterns). Run the examples.
- Practice: PortSwigger "SQL injection" + "File upload" sections; write 3-4 small PoCs (login + auth token reuse, simple param tampering).
- Code review: Pick one small open source app; spend 45 min hunting dangerous functions.
- Output: Your first "stage-based" PoC using the skeleton for a simple vuln.
- Repo resources: OSWE-PoC-Skeleton-Guide.md, advanced-skeleton/QUICKSTART.md.

**Milestone**: Comfortable creating a new PoC dir from skeleton in <15 min.

### Week 2: SQL Injection (MySQL + Second Order + Postgres)
- Primary: `guides/Advanced-SQLi-Techniques.md`, `notes/SECOND-ORDER-SQLI.md`, `poc-examples/second-order-sqli/`, `poc-examples/manageengine-sqli/`.
- MSSQL focus: `poc-examples/mssql-sqli-xp-cmdshell/`, `notes/MSSQL-SQLI-XP-CMDSHELL.md`, `guides/Advanced-SQLi-Techniques.md` (xp_cmdshell, OLE).
- Practice: PentesterLab SQLi to Shell (MySQL + Postgres editions), PortSwigger blind + second-order labs. Script binary-search extraction yourself.
- Code review patterns: string concat in queries, prepared statements misuse, stored procs.
- Challenge: Automate full chain on one manageengine-like or second-order target.
- Extras: MySQL LOAD_FILE / INTO OUTFILE, Postgres UDF/COPY/lo_export.

**Milestone**: Reliable time-based + boolean blind SQLi PoC with <10 requests per char extraction + RCE path.

### Week 3: PHP Type Juggling + Object Injection / Auth Chains
- Type juggling: `notes/ATUTOR-2.2.1-TYPE-JUGGLING.md`, `poc-examples/atutor-type-juggling/`, old OWASP PHP Magic Tricks PDF.
- PHP Object Injection: `guides/PHP-Deserialization-Patterns.md`, `notes/PHP-OBJECT-INJECTION.md`, `poc-examples/php-object-injection/`.
- Full chain example: `notes/ATUTOR-2.2.1-AUTH-RCE.md`, `poc-examples/atutor-type-juggling/`.
- Practice: ATutor 2.2.1 install (or equivalent), bmdyy labs if available, PortSwigger PHP type juggling if present.
- Focus: Magic hashes (0e...), POP chain construction on paper before coding, PHAR deserialization.

**Milestone**: Working type juggling auth bypass + file upload RCE PoC; ability to build a basic POP chain from 3-4 classes.

### Week 4: Java Deserialization + XXE
- Java: `guides/Java-Deserialization-Methodology.md` (master this), `poc-examples/java-deserialization-commons/`, `notes/JAVA-DESERIALIZATION-COMMONS-COLLECTIONS.md`.
- XXE: `guides/XXE-Attack-Vectors.md`, `poc-examples/xxe-file-read-ssrf/`, `notes/XXE-FILE-READ-SSRF.md`.
- Tools: ysoserial (multiple gadget chains), marshalsec.
- Practice: Java deserial webapp from README, XXE-Study GitHub, custom XXE in SVG/DOCX if possible.
- Code review: ObjectInputStream, XMLDecoder, XStream, Jackson default typing.
- Variations: signed objects, JEP 290 bypasses, different delivery (headers, files, RMI).

**Milestone**: ysoserial-driven PoC with 3+ delivery methods + callback verification; XXE file read + OOB exfil working script.

### Week 5: .NET Deserialization + Node.js + SSTI
- .NET: `guides/.NET-Deserialization-Guide.md`, `notes/DOTNET-VIEWSTATE-DESERIALIZATION.md` + `notes/DOTNETNUKE-COOKIE-DESERIALIZATION.md`, `poc-examples/dotnet-viewstate-deserialization/`.
- Node: `notes/NODEJS-DESERIALIZATION.md`, `poc-examples/nodejs-deserialization/`.
- SSTI: `guides/SSTI-Exploitation-Guide.md`, `notes/SSTI-JINJA2-FLASK.md`, `poc-examples/ssti-jinja2-flask/`.
- Tools: ysoserial.net, dnSpy for decompile.
- Practice: Pwnworks .NET challenges, Celestial HTB (Node), GoSecure SSTI workshop, custom Flask/Jinja apps.
- Focus: Machine key attacks, ObjectDataProvider, node-serialize IIFE, Jinja2 MRO escapes + polyglots.

**Milestone**: At least one full PoC per category; comfortable reading decompiled .NET or JS source for gadgets.

### Week 6: File Upload to RCE + XSS to RCE Chains (Core Chaining Week)
- File upload: New dedicated resources — `guides/File-Upload-to-RCE.md` (bypass matrix, ASCII/Mermaid diagrams, full cheat sheets, decision tree), `poc-examples/file-upload-rce/` (complete stage-based PoC + rich Notes.md), `notes/FILE-UPLOAD-TO-RCE.md`.
- Study syllabus patterns (extension filters, content-type, magic bytes, double extensions, path traversal in upload).
- XSS chains: `Atmail-6.4-XSS-RCE-Study.md`, `poc-examples/atmail-xss-rce/`, `notes/ATMAIL-6.4.md`.
- Additional: HTB Popcorn / Vault (file upload), Atmail PoC.
- Create your own mini vulnerable upload app (PHP/ASP.NET) and exploit all common bypasses using the new PoC as reference.
- Practice chaining: XSS → CSRF → upload plugin/shell, or SQLi → file write → include.

**Milestone**: File upload bypass matrix (8+ techniques) + end-to-end RCE PoC; full Atmail-style multi-stage script.

### Week 7: Code Review Mastery + Integration + Exam Simulation
- Deep: `guides/Code-Review-Checklists.md` (full), OWASP Code Review Guide.
- Revisit all previous weeks' source patterns. Practice 30-45 min "first pass" code reviews on new targets.
- Full chains: Pick 2-3 machines from bmdyy / HTB / VulnHub; treat as mini-exam (time-boxed, full PoC + notes in CASE-template format).
- Reporting: Practice writing professional sections (see OffSec report template in README). "Report as you go".
- Speed drills: Binary search SQLi, gadget selection, stage skeleton in <10 min.

**Milestone**: Complete 2 simulated "exam machines" (source provided or whitebox) end-to-end with PoC + report snippet in <4 hours each.

### Week 8: Polish, Gaps, Full Review + Light Practice
- Re-read weak areas from your notes.
- Fill gaps: Postgres RCE specifics, more .NET gadgets, advanced WAF bypasses, blind XXE variations, PHAR + file upload combos.
- Review all PoC code in this repo; refactor one of yours to be cleaner/faster.
- Light: 1-2 new PortSwigger or PentesterLab + script it.
- Mental: Exam guide (proctoring, reporting rules, 47h45m + 24h report). Prepare clean Kali + tools + templates.
- Final: One full "dry run" on a complex chain you haven't touched.

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

## Daily / Weekly Habits That Work

- **Code review sessions**: 3-4x/week, 30-60 min on fresh code. Use checklists from guides/Code-Review-Checklists.md. Document in CASE-template.md format.
- **PoC increments**: Never "just test manually". After manual confirmation, immediately start scripting the next stage.
- **Notes**: After every lab/target, fill or update a case study (Environment / Recon / Hypothesis / Chain / Evidence / Findings). Copy `notes/CASE-template.md`.
- **Burp + Python loop**: Every target you touch, proxy your PoC. Fix issues faster.
- **Time tracking**: Log time per stage. Goal: reduce PoC dev time week over week.
- **Review Friday**: Re-read your own PoCs + notes from 2 weeks ago; improve one.

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

- You can stand up a new skeleton PoC for a described vuln in <20 minutes.
- You have 6-8 solid, documented, working end-to-end PoCs (one per major class).
- You can perform a 45-min code review pass on a medium app and find the primary vuln + at least one secondary.
- You have written at least 2 full "exam-style" reports (even if internal).
- You can explain gadget chain construction, binary search SQLi math, and file upload filter bypasses from memory + demo quickly.

---

## Exam Day Tips (from recent passers + this repo)

- Read the latest OSWE Exam Guide (link in README).
- Report as you go — screenshots, commands, PoC versions in a running doc.
- Use the PoC skeleton you practiced; don't invent new structure under time pressure.
- Flags first, beautiful code second (but commented and clean enough to understand).
- If stuck >20-30 min on one vector, pivot and come back; multiple paths often exist.
- Document assumptions and failed attempts briefly (examiners like process).

---

## Resources Added / Curated (see also README)

Recent high-value reviews (2025-2026):
- https://notateamserver.xyz/blog/oswe-review/
- https://steflan-security.com/offsec-web-expert-oswe-review/
- https://medium.com/@jake.mayhew/web-300-oswe-review-offsec-web-expert-46074fbdb237
- https://rootshooter.medium.com/offsec-awae-oswe-review-2026-cad3c1e15946

Other frequently praised:
- bmdyy GitHub labs (search "bmdyy tudo" or "bmdyy testr")
- https://github.com/wetw0rk/AWAE-PREP and community forks
- PortSwigger + "script every lab"
- Code review specific practice sites

This roadmap + the rest of the repo (PoCs, guides, case studies) gives you a closed-loop practice system: learn concept → study real PoC → reproduce + modify → apply to new target → document.

Good luck — consistent deliberate practice with the white-box + script mindset is what separates passers.

---

**Update this roadmap** as you progress. Track completed PoCs and weak areas here.
