# Reporting tooling (practice & exam)

OSWE is graded on **flags + non-interactive PoCs + professional report**. Tooling choices are personal; below matches common 2025–2026 workflows.

**Official rules always win** — read the current exam guide for allowed tools and report format.

---

## Principles

1. **Report as you go** — after each flag, draft the section (see Challenge-Lab-Playbook).  
2. **Evidence first** — screenshots and PoC paths before prose polish.  
3. **Reproducibility** — examiner runs your script; report explains *why* the code is wrong.  

Templates: [Report-Snippet-Templates.md](Report-Snippet-Templates.md).

---

## Practice stack options

| Tool | Role | Notes |
|------|------|--------|
| **Markdown + PDF** | Simple | Obsidian / Typora / pandoc → PDF + OffSec cover if required |
| **[Sysreptor](https://github.com/syslifters/sysreptor)** | Structured reports | Community edition; used by some 2026 passers for practice |
| **OffSec Word/template** | Exam submission shape | Follow current exam package |
| **Screenshot naming** | Evidence | `evidence/target/01-…png` convention in Report-Snippet-Templates |

### Sysreptor (practice)

```bash
# See upstream README for docker compose install
# Use only for practice reports unless exam policy allows similar tools
```

Map finding fields to: Environment, Recon, Vulnerability, Chain, PoC usage, Remediation.

---

## Exam window workflow

| When | Action |
|------|--------|
| Flag N captured | Freeze PoC stages; screenshots; draft section N |
| All flags done | Cold-run every PoC on clean shell / exam Kali |
| Report window | Assemble template; check ToC, images, script listings |
| Submit early | Leave buffer for upload issues |

---

## PoC appendix checklist

- [ ] How to run (`python3 poc.py --help` and example)  
- [ ] Dependencies listed  
- [ ] No proxy hard-coded  
- [ ] Listener assumptions documented  
- [ ] Exit codes / success strings explained  

---

## Related

- Exam-Day-Runbook.md  
- Challenge-Lab-Playbook.md  
- Report-Snippet-Templates.md  
