# ManageEngine Applications Manager — SQLi → PostgreSQL → RCE

**Pattern**: Injectable HTTP parameter (often unauth servlet) → stacked/time-based SQLi on **PostgreSQL** → file read/write / large objects → webshell under Tomcat web root.  
**PoC**: `poc-examples/manageengine-sqli/`  
**Guides**: `guides/Postgres-SQLi-to-RCE.md`, `guides/Advanced-SQLi-Techniques.md`, `guides/Blind-SQLi-Automation.md`

Version context in training labs is often older builds (e.g. around **12900** era). Confirm exact build in your environment.

---

## Environment

| Item | Typical lab value |
|------|-------------------|
| App | ManageEngine Applications Manager |
| Web | `http://TARGET:9090/` (common default) |
| App server | Embedded **Tomcat** |
| DB | Bundled **PostgreSQL** |
| Install path (Linux example) | `/opt/ManageEngine/AppManager/` |
| Web root hint | `.../working/apache-tomcat/webapps/ROOT/` |
| Default UI creds | Often `admin` / `admin` (still exploit unauth paths if present) |

Decompile / inspect servlets under webapps and `WEB-INF` for parameter names.

---

## Recon

### Entry points
- Servlets under `/servlet/*`
- Authenticated admin APIs
- Export/report parameters touching SQL

### High-value historical pattern
- Servlet such as **`AMUserResourcesSyncServlet`**
- Parameter such as **`ForMasRange`** (name may vary by build — always verify in source)

### White-box
```bash
# After obtaining class files / sources
grep -Rn "ForMasRange\|createStatement\|executeQuery\|+\s*request" .
```

Look for:
```java
// illustrative anti-pattern
String id = request.getParameter("ForMasRange");
stmt.execute("SELECT ... " + id + " ...");
```

### Black-box probes
- Time-based: inject `pg_sleep(5)` / stacked sleep
- Boolean differentials if any reflection
- Error-based if verbose SQL errors enabled (less common in prod-like builds)

---

## Vulnerability hypothesis

| Field | Detail |
|-------|--------|
| Class | SQL injection (CWE-89) → OS command/file write via DB features |
| Data flow | HTTP param → string-built SQL → PostgreSQL → file system / UDF |
| Preconditions | Reachable injectable param; DB user privileges for write/exec primitives |
| Impact | Unauth or low-auth RCE on host |

### Why PostgreSQL matters
MySQL muscle memory is not enough. Postgres offers:
- `pg_sleep` for blind confirm
- `pg_read_file` / `pg_ls_dir` (role-dependent)
- `COPY ... TO/FROM` for file write/read (superuser-oriented)
- Large objects: `lo_import` / `lo_export` / `lo_from_bytea` patterns for binary webshells

See `guides/Postgres-SQLi-to-RCE.md`.

---

## Chain outline

### Step 1 — Confirm injection
```http
GET /servlet/AMUserResourcesSyncServlet?ForMasRange=1';/* crafted */ HTTP/1.1
```
Measure timing with `pg_sleep`. Document baseline latency.

### Step 2 — Fingerprint DB & privileges
Via blind extraction or errors:
- `version()`
- `current_user` / `session_user`
- `current_database()`
- superuser check (`usesuper` / role attributes)

### Step 3 — Recon file system via DB
- Read sensitive configs if `pg_read_file` allowed
- List dirs to locate Tomcat `webapps/ROOT`
- Confirm writable locations

### Step 4 — Write webshell
Options (privilege-dependent):
1. `COPY (SELECT '<?php ...') TO '/path/shell.jsp'` (JSP often more natural on Tomcat than PHP)
2. Large object write + export to web path
3. Other build-specific features

Prefer **JSP** on Java stacks.

### Step 5 — Execute
`curl http://TARGET:9090/shell.jsp?cmd=id` (or POST body designs)

### Step 6 — Script
PoC stages: detect → privilege → write → verify → optional reverse shell.  
Match `poc-examples/manageengine-sqli/poc.py`.

---

## Evidence

| Artifact | Proves |
|----------|--------|
| Timing chart / logs | SQLi confirm |
| Extracted version/user | DB control |
| Webshell GET response | RCE |
| Source snippet of concat | Root cause |

---

## Findings

### Root cause
Untrusted HTTP input concatenated into SQL executed by a powerful database account colocated with a writable application server directory.

### Fixes
1. Parameterized queries / bind variables exclusively.
2. Least-privilege DB role (no superuser for app pool; revoke file primitives).
3. Disable unused servlets; authn all sync endpoints.
4. WAF is not sufficient; fix code.
5. Separate DB host from app where possible; block `COPY` to app paths via OS permissions.

### OSWE tips
- Java + Postgres stacks: decompile early; map `web.xml` servlet routes.
- Stacked queries may need specific syntax/termination for the driver.
- Blind extraction: implement binary search once; reuse for paths and flags.
- Webshell language must match container (JSP/servlet vs PHP).
- Time box: if write primitive fails, try alternate path (UDF, different directory, authenticated SQLi elsewhere).

### Pitfalls
- Assuming MySQL `INTO OUTFILE` semantics on Postgres
- Writing PHP into Tomcat without PHP engine
- Network egress blocked for reverse shell — use in-band command output first
- Destructive SQL without snapshot

---

## Related resources

| Resource | Location |
|----------|----------|
| PoC + Notes | `poc-examples/manageengine-sqli/` |
| Postgres RCE guide | `guides/Postgres-SQLi-to-RCE.md` |
| Advanced SQLi | `guides/Advanced-SQLi-Techniques.md` |
| Blind automation | `guides/Blind-SQLi-Automation.md` |
| Lab matrix | `Lab-Setup-Matrix.md` |
