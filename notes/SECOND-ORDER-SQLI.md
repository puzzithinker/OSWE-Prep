# Second-Order SQL Injection Case Study

## Environment

- Host OS: Attacker Kali, target usually Linux + MySQL/MariaDB (can be any DB)
- App: Custom web app (PHP, ASP.NET, Java, Node) with registration/profile + privileged search/report functionality
- DB: MySQL 5.7/8.0 typical for examples
- Web: http://target/ (user reg) + /admin/ (search/reports)
- Key ports: 80/443 + DB internal

**Classic lab setup**: Simple PHP app with two entry points — public "register" that stores a field, and admin "search users" that uses the stored field in a concatenated query.

## Recon

- Entry points (storage): Registration forms, profile updates, comment submission, any INSERT/UPDATE that accepts user strings without heavy sanitization.
- Trigger points (execution): Admin panels (user search by lastname/email, order lookup, export to CSV/PDF, audit log viewers, email notification templates, scheduled reports).
- Roles: Low-priv (or unauth) user for storage → high-priv (admin) context for trigger. This is what makes second-order powerful and realistic.
- Data flow to watch: Stored value travels through DB, then later read into a query string or used in string concat.

**Signs**:
- You control data that later appears in admin functionality.
- Time delays or errors only appear when an admin performs an action after you registered.
- "Export all users" or "search users" features in admin.

## Vulnerability Hypothesis

- Suspected class: Second-order (stored) SQL Injection.
- Data flow: Attacker injects SQL payload into a storage query (prepared or not) → payload sits dormant in a table column → later a different code path (often higher privilege) reads the column and builds a vulnerable query via concatenation → payload executes in the second query's context.
- Preconditions:
  - At least one storage path accepts data that is later used in a dynamic query.
  - The trigger query uses string concatenation / improper escaping on the previously stored value.
  - Timing: attacker can force or wait for the trigger action (or social engineer / scheduled job).

## Chain Outline

1. **Map storage + trigger**:
   - Register a user with a test marker in the injectable field (e.g. lastname = `TEST_MARKER_123`).
   - As admin (or while watching logs), perform search/export on that field.
   - Confirm the marker appears in the generated query (via slow query log, errors, or app debug).

2. **Confirm second-order SQLi**:
   - Re-register with time-based payload in the field: `admin' AND SLEEP(5)-- -` (MySQL) or equivalent for target DB.
   - Trigger the admin action.
   - Observe ~5s delay only on trigger (not on registration).

3. **Data extraction**:
   - Use conditional time-based or boolean (if output visible to admin and you can observe side effects).
   - Or stacked queries / file write if privileges allow (rare in second-order but powerful).

4. **Escalate**:
   - Extract admin creds / session tokens.
   - Write webshell via `INTO OUTFILE` (if FILE priv + writable dir in webroot).
   - Or use other DB RCE primitives (xp_cmdshell on MSSQL, UDF on Postgres, etc.).

5. **Cleanup / persistence**: Drop shell, establish reverse shell, pivot.

## Evidence

- Registration response + admin search timing screenshots.
- DB logs or app query logs showing the concatenated payload in the second query.
- Extracted data or shell callback.

## Findings

### Root Cause
The application treats data that originated from users as "trusted" once it has been stored in the database. A later developer (or different feature) builds a query assuming the data is safe, using string concatenation instead of parameterized queries or proper escaping at the point of use.

Storage query may be safe (prepared statement), but the *consumption* query is not.

```php
// Storage (often looks safe)
$stmt = $db->prepare("INSERT INTO users (username, lastname) VALUES (?, ?)");
$stmt->execute([$username, $lastname]);   // $lastname can contain payload

// Later, in admin search (vulnerable)
$search = $_POST['search'];
$query = "SELECT * FROM users WHERE lastname = '$search'";  // payload executes here
```

### Why Second-Order Is Sneaky & Powerful
- Bypasses many WAFs and client-side filters (the malicious string is submitted "cleanly" in first request).
- Often gives you higher-privilege execution context automatically.
- Harder to find in black-box (you need to exercise both paths).
- In white-box: look for any data that crosses from user-controlled write → later read into query construction.

### DB-Specific Payloads for Second-Order

See `guides/Advanced-SQLi-Techniques.md` for full lists. Quick MySQL examples:
- Time: `foo' AND SLEEP(5)-- -`
- Boolean (if side channel): `foo' AND (SELECT ... )=1-- -`
- Stacked + file write (if possible): `foo'; SELECT '<?=system($_GET[0])?>' INTO OUTFILE '/var/www/html/s.php'-- -`

For the trigger to execute multiple statements, the second query must support stacked queries or the storage must allow comment tricks that survive to the second query.

### Fix Ideas

- **Parameterize every query**, everywhere, including those built from "internal" or previously stored data.
- Treat all data from the database as untrusted for query construction purposes.
- Use an ORM or query builder consistently that forces parameterization.
- Add canary / test users with known markers and monitor query logs or add automated tests that would catch concatenation on stored fields.
- Principle of least privilege on DB accounts (no FILE, no xp_cmdshell by default, etc.).

## OSWE Exam Tips

- **Always look for second-order** when you see INSERT/UPDATE of user data + any admin search/export/report feature.
- Enable slow query log or app debug logging during testing — the payload will appear verbatim in the second query.
- Binary search extraction still works; just the "submit payload" and "trigger + observe" are separated in time and often by role.
- In exam, you may need two PoC scripts or a single script that registers then polls/triggers the admin side (using stored admin session or by abusing another vuln to get admin).
- Common pattern in real apps and in the course (ATutor had related ideas; ManageEngine and others have multi-stage data flows).
- Time management: Spend time mapping the data flow in code first — once you find the storage + the vulnerable read, exploitation is standard SQLi.
- Reporting: Clearly document the two distinct requests and the data flow through the DB. Examiners love seeing you understood the "second-order" aspect.

## References & Related in Repo

- `poc-examples/second-order-sqli/` (PoC + 129-line Notes.md with implementation details)
- `guides/Advanced-SQLi-Techniques.md` (full section on second-order + optimization)
- `notes/MANAGEENGINE-APPS-MANAGER-SQLI-RCE.md` (similar multi-stage SQLi to RCE)
- PentesterLab "SQLi to Shell" exercises
- PortSwigger second-order labs

**See also** the detailed lab manual in the poc directory for a working two-stage automation example.
