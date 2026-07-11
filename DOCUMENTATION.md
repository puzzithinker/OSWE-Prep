# Documentation index

How to navigate this OSWE preparation repository.

---

## New here?

1. **[OSWE-Study-Roadmap.md](OSWE-Study-Roadmap.md)** — 8-week plan and priorities  
2. **[labs/README.md](labs/README.md)** — `./labctl.sh up` Docker teaching labs  
3. **[Progress-Tracker.md](Progress-Tracker.md)** — track readiness by vuln class  
4. **[Lab-Setup-Matrix.md](Lab-Setup-Matrix.md)** — skill → lab port → guide/PoC  

---

## Practice systems

| Document | Use when |
|----------|----------|
| [labs/README.md](labs/README.md) | Starting vulnerable apps in Docker |
| [Lab-Setup-Matrix.md](Lab-Setup-Matrix.md) | Choosing what to practice next |
| [Speed-Drills.md](Speed-Drills.md) | Timed skill drills |
| [drills/Cold-Start-Drills.md](drills/Cold-Start-Drills.md) | Scenario cards without solutions first |
| [study-log/](study-log/) | Session diary and weak areas |
| [Exam-Day-Runbook.md](Exam-Day-Runbook.md) | Exam time boxes and pivot rules |
| [Report-Snippet-Templates.md](Report-Snippet-Templates.md) | Report section templates |

---

## Methodology guides (`guides/`)

| Guide | Topic |
|-------|--------|
| [Code-Review-Checklists.md](guides/Code-Review-Checklists.md) | White-box review |
| [Dangerous-Sinks-Cheatsheet.md](guides/Dangerous-Sinks-Cheatsheet.md) | First-pass greps by language |
| [Chain-Decision-Trees.md](guides/Chain-Decision-Trees.md) | “I found X → next Y” |
| [Advanced-SQLi-Techniques.md](guides/Advanced-SQLi-Techniques.md) | SQLi → RCE |
| [Blind-SQLi-Automation.md](guides/Blind-SQLi-Automation.md) | Boolean/time extractors |
| [Postgres-SQLi-to-RCE.md](guides/Postgres-SQLi-to-RCE.md) | Postgres-specific paths |
| [Java-Deserialization-Methodology.md](guides/Java-Deserialization-Methodology.md) | Java + ysoserial |
| [DotNet-Deserialization-Guide.md](guides/DotNet-Deserialization-Guide.md) | ViewState / .NET gadgets |
| [PHP-Deserialization-Patterns.md](guides/PHP-Deserialization-Patterns.md) | PHP POI / PHAR |
| [PHP-Type-Juggling-Methodology.md](guides/PHP-Type-Juggling-Methodology.md) | Magic hashes / `==` |
| [XSS-to-RCE-Chaining.md](guides/XSS-to-RCE-Chaining.md) | XSS → privileged RCE |
| [File-Upload-to-RCE.md](guides/File-Upload-to-RCE.md) | Upload bypass matrix |
| [LFI-to-RCE.md](guides/LFI-to-RCE.md) | Include / log poison chains |
| [XXE-Attack-Vectors.md](guides/XXE-Attack-Vectors.md) | XXE / OOB / SSRF |
| [SSTI-Exploitation-Guide.md](guides/SSTI-Exploitation-Guide.md) | Template injection |

---

## PoC development

| Document | Purpose |
|----------|---------|
| [Building a Reusable OSWE PoC Skeleton.md](Building%20a%20Reusable%20OSWE%20PoC%20Skeleton.md) | Skeleton design |
| [Exploit Writing for OSWE.md](Exploit%20Writing%20for%20OSWE.md) | `requests` patterns |
| [COMPLETE-POC-GUIDE.md](COMPLETE-POC-GUIDE.md) | How examples fit together |
| [poc-examples/](poc-examples/) | Stage-based PoCs + `lab/` Docker apps |
| [poc-examples/advanced-skeleton/](poc-examples/advanced-skeleton/) | Shared modules |

---

## Case studies (`notes/`)

Copy [notes/CASE-template.md](notes/CASE-template.md) for new write-ups. Classic chains (ATutor, Atmail, ManageEngine, DNN, etc.) live under `notes/`. Each major topic links to a `poc-examples/*/Notes.md` lab manual.

---

## Docker teaching labs vs vendor VMs

| Use Docker labs when… | Use course / vendor VMs when… |
|------------------------|--------------------------------|
| Daily skill practice | Exam-like product fidelity |
| Fast reset (`labctl down/up`) | Exact ATutor/Atmail/ManageEngine paths |
| Scripting against known ports | Official Challenge Labs |

Docker apps are labeled **OSWE-LAB** and intentionally minimal. They teach the *class*, not the full commercial product.

---

## Agent / contributor notes

- [AGENTS.md](AGENTS.md) — structure and commit style for automation  
- [CLAUDE.md](CLAUDE.md) — same for Claude Code  
- Keep secrets out of the repo; public training resources only  

---

## Safety

Content is for **authorized** security testing, CTFs, and OSWE exam preparation only.
