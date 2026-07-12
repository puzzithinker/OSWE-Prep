# bmdyy OSWE-style labs

Community white-box / scripting practice by [William Moody (bmdyy)](https://github.com/bmdyy). Frequently recommended in 2025–2026 OSWE reviews alongside PortSwigger and official Challenge Labs.

**Authorized practice only.**

---

## Repositories (start here)

Browse: https://github.com/bmdyy?tab=repositories

Commonly cited:

| Lab | Focus | Notes |
|-----|--------|--------|
| [tudo](https://github.com/bmdyy/tudo) | PHP multi-step web app | Auth → escalate → RCE style practice |
| [testr](https://github.com/bmdyy/testr) | XSS / code injection (web IDE theme) | Script carefully |
| [order](https://github.com/bmdyy/order) | Blind SQLi in `ORDER BY` (Flask + Postgres) | Docker-friendly |
| Others on profile | Chat, etc. | Read each README |

Clone and follow each repo’s README for ports and flags. Some Dockerfiles need small package pin fixes on new hosts — normal.

---

## Suggested workflow

1. Black-box tour 15 min (Challenge-Lab-Playbook Phase 1).  
2. Source review with sinks cheatsheet.  
3. Manual chain.  
4. Full non-interactive PoC.  
5. CASE notes in `notes/` or `study-log/`.  

---

## Pair with this repo

| Skill | After bmdyy… |
|-------|----------------|
| Blind ORDER BY | `guides/Blind-SQLi-Automation.md`, second-order lab |
| PHP chains | type-juggling / upload Docker labs |
| XSS | XSS-to-RCE guide, xss-chain lab |

Optional: add compose overrides under `labs/` later if you want one-command starts; upstream READMEs remain source of truth.

---

## Related

- Lab-Setup-Matrix.md  
- labs/README.md  
- Challenge-Lab-Playbook.md  
