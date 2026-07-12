# PortSwigger Web Security Academy — OSWE-oriented tracker

**Rule from 2025–2026 prep guides**: finish relevant Academy topics **and** write a mini non-interactive PoC (or Burp→Python via [curlconverter](https://curlconverter.com/)) where the lab allows automation.

Status: ☐ not started · ▢ read only · ◐ lab done · ☑ lab + scripted notes

---

## Core tracks (high priority)

| Topic | Academy path | Status | PoC / notes path |
|-------|--------------|--------|------------------|
| SQL injection (all) | SQL injection | | |
| Blind SQLi | SQL injection → Blind | | |
| Second-order SQLi | SQL injection | | |
| XSS (stored/reflected/DOM) | Cross-site scripting | | |
| CSRF | CSRF | | |
| SSRF | Server-side request forgery | | |
| XXE | XXE injection | | |
| SSTI | Server-side template injection | | |
| Insecure deserial | Insecure deserialization | | |
| File upload | File upload vulnerabilities | | |
| Access control | Access control | | |
| Prototype pollution | Prototype pollution | | |
| JWT (awareness) | JWT | | |
| Path traversal | Directory traversal | | |
| Command injection | OS command injection | | |
| WebSockets | WebSockets (if listed) | | |

---

## Per-lab mini template (copy)

```markdown
### Lab: <name>
- Date:
- Solved: yes/no
- Root cause (1–2 lines):
- PoC path or snippet:
- Exam-relevant pattern (1st flag / 2nd flag / both):
- Revisit?:
```

---

## Weekly habit

- 3–5 Academy labs / week during Roadmap weeks 1–6  
- Prefer **scripting** blind/data exfil and multi-step auth labs  
- Log completions in `study-log/`  

---

## Related

- [guides/Blind-SQLi-Automation.md](guides/Blind-SQLi-Automation.md)  
- [guides/Prototype-Pollution-Methodology.md](guides/Prototype-Pollution-Methodology.md)  
- [guides/SSRF-Chaining.md](guides/SSRF-Chaining.md)  
- [snippets/](snippets/)  
