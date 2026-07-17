# Lab Setup Matrix

Quick index: **what to run**, **how it pairs with this repo**, and **what skill it trains**. Authorized labs and public resources only.

---

## How to use

1. Pick a skill from Progress-Tracker gaps.  
2. Find a row below.  
3. Stand up lab → work CASE template → script → compare with `poc-examples/*` only after your attempt.  

---

## Docker teaching labs (preferred daily practice)

All default labs: `cd labs && ./labctl.sh up` — see [labs/README.md](labs/README.md).

| Skill | Docker service | Host URL | Lab source |
|-------|----------------|----------|------------|
| File upload → RCE | `file-upload` | http://127.0.0.1:8101 | `poc-examples/file-upload-rce/lab/` |
| SSTI Jinja2 | `ssti` | http://127.0.0.1:8102 | `poc-examples/ssti-jinja2-flask/lab/` |
| XXE | `xxe` | http://127.0.0.1:8103 | `poc-examples/xxe-file-read-ssrf/lab/` |
| Node deserial | `node-deserial` | http://127.0.0.1:8104 | `poc-examples/nodejs-deserialization/lab/` |
| Bassmaster-style JS | `bassmaster` | http://127.0.0.1:8105 | `poc-examples/bassmaster-js-injection/lab/` |
| PHP object injection | `php-poi` | http://127.0.0.1:8106 | `poc-examples/php-object-injection/lab/` |
| Type juggling | `type-juggling` | http://127.0.0.1:8107 | `poc-examples/atutor-type-juggling/lab/` |
| Second-order SQLi | `second-order` | http://127.0.0.1:8108 | `poc-examples/second-order-sqli/lab/` |
| XSS → admin plugin | `xss-chain` | http://127.0.0.1:8109 | `poc-examples/atmail-xss-rce/lab/` |
| Postgres SQLi | `pg-sqli` | http://127.0.0.1:8110 | `poc-examples/manageengine-sqli/lab/` |
| Java deserial | `java-deserial` (profile `heavy`) | http://127.0.0.1:8111 | `poc-examples/java-deserialization-commons/lab/` |
| MSSQL SQLi | `mssql-sqli` (profile `heavy`) | http://127.0.0.1:8112 | `poc-examples/mssql-sqli-xp-cmdshell/lab/` |
| .NET JSON deserial | `dotnet-json` | http://127.0.0.1:8113 | `poc-examples/dotnet-viewstate-deserialization/lab/` |
| Prototype pollution | `prototype-pollution` | http://127.0.0.1:8114 | `poc-examples/prototype-pollution/lab/` |
| SSRF chaining | `ssrf` | http://127.0.0.1:8115 | `poc-examples/ssrf-chaining/lab/` |
| WebSocket injection | `websocket` | http://127.0.0.1:8116 | `poc-examples/websocket-injection/lab/` |

These are **teaching clones** of the vuln class (not full vendor products). Use course VMs for exact ATutor/Atmail/ManageEngine when available.

## Repo PoC labs (notes + scripts)

| Skill | Repo notes | PoC dir | Docker |
|-------|------------|---------|--------|
| Java deserial | `notes/JAVA-DESERIALIZATION-COMMONS-COLLECTIONS.md` | `poc-examples/java-deserialization-commons/` | `:8111` heavy |
| MSSQL SQLi RCE | `notes/MSSQL-SQLI-XP-CMDSHELL.md` | `poc-examples/mssql-sqli-xp-cmdshell/` | `:8112` heavy |
| ManageEngine / PG SQLi | `notes/MANAGEENGINE-APPS-MANAGER-SQLI-RCE.md` | `poc-examples/manageengine-sqli/` | `:8110` |
| Second-order SQLi | `notes/SECOND-ORDER-SQLI.md` | `poc-examples/second-order-sqli/` | `:8108` |
| Type juggling | `notes/ATUTOR-2.2.1-TYPE-JUGGLING.md` | `poc-examples/atutor-type-juggling/` | `:8107` |
| XSS→RCE | `notes/ATMAIL-6.4.md` | `poc-examples/atmail-xss-rce/` | `:8109` |
| Bassmaster JS | `notes/BASSMASTER-1.5.1-JS-INJECTION.md` | `poc-examples/bassmaster-js-injection/` | `:8105` |
| Node deserial | `notes/NODEJS-DESERIALIZATION.md` | `poc-examples/nodejs-deserialization/` | `:8104` |
| .NET ViewState / JSON | `notes/DOTNET-VIEWSTATE-DESERIALIZATION.md` | `poc-examples/dotnet-viewstate-deserialization/` | `:8113` (JSON); ViewState on Windows |
| DNN cookie | `notes/DOTNETNUKE-COOKIE-DESERIALIZATION.md` | (patterns) | use `:8113` + Windows DNN |
| PHP POI | `notes/PHP-OBJECT-INJECTION.md` | `poc-examples/php-object-injection/` | `:8106` |
| SSTI Jinja | `notes/SSTI-JINJA2-FLASK.md` | `poc-examples/ssti-jinja2-flask/` | `:8102` |
| XXE | `notes/XXE-FILE-READ-SSRF.md` | `poc-examples/xxe-file-read-ssrf/` | `:8103` |
| File upload | `notes/FILE-UPLOAD-TO-RCE.md` | `poc-examples/file-upload-rce/` | `:8101` |
| Prototype pollution | `poc-examples/prototype-pollution/Notes.md` | `poc-examples/prototype-pollution/` | `:8114` |
| SSRF chaining | `poc-examples/ssrf-chaining/Notes.md` | `poc-examples/ssrf-chaining/` | `:8115` |
| WebSocket injection | `poc-examples/websocket-injection/Notes.md` | `poc-examples/websocket-injection/` | `:8116` |

**Always read** each `poc-examples/*/lab/README.md` and `Notes.md`.

---

## Public practice platforms

| Resource | Trains | Script it? | Link / notes |
|----------|--------|------------|--------------|
| OffSec WEB-300 Challenge Labs | Full exam-like chains | **Required** | Course access |
| bmdyy labs (tudo, testr, order, …) | White-box PHP/Python/SQLi | Yes | [bmdyy-Labs.md](bmdyy-Labs.md) · https://github.com/bmdyy |
| PortSwigger Academy | Breadth + modern variants | Mini-PoCs | [PortSwigger-Lab-Tracker.md](PortSwigger-Lab-Tracker.md) |
| Official WEB-300 Challenge Labs | Exam-format white-box | **Required** if enrolled | [Challenge-Lab-Playbook.md](Challenge-Lab-Playbook.md) |
| PentesterLab SQLi to Shell | MySQL/Postgres file/RCE | Yes | README Practice Labs |
| GoSecure SSTI workshop | Template injection | Yes | README |
| GoSecure XXE workshop | XXE | Yes | README |
| java-deserialize-webapp | Java deserial | Yes | GitHub hvqzao |
| XXE-Study | XXE | Yes | GitHub HLOverflow |
| Pwnworks .NET | .NET deserial | Yes | GitHub abhisek |
| VulnHub SecureCode etc. | Mixed web | Yes | README |
| HTB (Popcorn, Arkham, Celestial, …) | Class-specific | Optional | README HTB table |

---

## Suggested Docker / local tool baseline

```text
Attacker: Kali + Burp + Python 3.10+ + uv
Labs:     Docker Engine + Compose v2 (`labs/labctl.sh`)
Java:     jd-gui / jadx, ysoserial.jar
.NET:     dnSpy/ILSpy, ysoserial.net (Windows VM for ViewState)
Listener: nc, python -m http.server
```

```bash
cd labs && ./labctl.sh up && ./labctl.sh smoke
```

---

## Skill → first lab path

| If weak in… | Start here |
|-------------|------------|
| Challenge Lab method / two flags | `Challenge-Lab-Playbook.md` |
| Snippet speed | `snippets/` + re-script one old lab |
| Prototype pollution | Docker `:8114` + PortSwigger PP + `guides/Prototype-Pollution-Methodology.md` |
| SSRF chaining | Docker `:8115` + `guides/SSRF-Chaining.md` |
| WebSocket / live channels | Docker `:8116` + `guides/WebSocket-Attack-Patterns.md` |
| Debugger / decompile | `guides/Remote-Debugging-and-Decompilation.md` |
| PoC skeleton | `poc-examples/advanced-skeleton/` + Week 1 roadmap |
| Blind SQLi | PortSwigger blind labs → `guides/Blind-SQLi-Automation.md` → second-order PoC |
| MSSQL RCE | `poc-examples/mssql-sqli-xp-cmdshell/` |
| Postgres RCE | ManageEngine notes + Postgres guide |
| Java deserial | java-deserialize-webapp + Commons PoC |
| .NET deserial | Pwnworks + .NET guide |
| Type juggling | ATutor notes + PoC |
| XSS chains | Atmail study + XSS guide |
| XXE | GoSecure workshop + xxe PoC |
| SSTI | GoSecure SSTI + Flask PoC |
| Upload | File-Upload guide + upload PoC |
| Node | Bassmaster + node-serialize PoCs |

---

## Snapshot hygiene

- Snapshot VMs before upload/RCE tests  
- Revert after destructive SQL  
- Separate lab network / host-only adapters  
- Never point PoCs at production  

---

## Related

- [OSWE-Study-Roadmap.md](OSWE-Study-Roadmap.md)  
- [Progress-Tracker.md](Progress-Tracker.md)  
- [Exam-Day-Runbook.md](Exam-Day-Runbook.md)  
- [README.md](README.md) practice tables  
