# ATutor 2.2.1 — PHP Type Juggling (Auth Bypass)

**Pattern**: Loose comparison on secrets/tokens → authentication bypass → privileged actions.  
**Related PoC**: `poc-examples/atutor-type-juggling/`  
**Methodology**: `guides/PHP-Type-Juggling-Methodology.md`  
**Often chained with**: password reset → admin login → file upload RCE (`notes/ATUTOR-2.2.1-AUTH-RCE.md`)

---

## Environment

| Item | Typical lab value |
|------|-------------------|
| Host OS | Kali attacker + Linux LAMP target |
| App | ATutor **2.2.1** (LMS) |
| Web URL | `http://TARGET/ATutor/` |
| Admin URL | `http://TARGET/ATutor/admin/` |
| Stack | Apache, **PHP 5.x** (type juggling behavior is classic here), MySQL |
| Source | Install tree under web root; focus on auth / password-reset / member code |
| Creds | Install wizard creates admin; register student accounts for contrast |

**Setup sketch**:
```bash
# Obtain ATutor 2.2.1 package (authorized lab only)
# Deploy under Apache docroot, complete install wizard, snapshot VM
```

See PoC `Notes.md` for install details and stage commands.

---

## Recon

### Entry points
- Login / logout
- Account registration
- **Password reminder / reset** flows (high value for type juggling)
- Email confirmation / hash-based tokens
- Admin vs student role boundaries

### Roles
| Role | Capabilities of interest |
|------|--------------------------|
| Guest | Register, trigger reset |
| Student | Limited profile/content |
| Instructor/Admin | File managers, course tools, config — RCE candidates post-bypass |

### White-box first pass (10–15 min)
Search PHP for:
```bash
grep -Rn '==' --include='*.php' . | head   # then focus auth files
grep -Rn 'md5\|sha1\|reset\|confirm\|token\|hash' --include='*.php' .
grep -Rn '===\|hash_equals' --include='*.php' .   # hope to find absences near secrets
```

**Sink class**: any `if ($user_input == $secret_from_db)` or `== md5(...)` without `hash_equals` / `===`.

### Vulnerable pattern (illustrative)

```php
// Conceptual pattern — loose compare on token/hash material
if ($user_provided_token == $row['confirmation_hash']) {
    // treat as valid reset / login / confirm
}
```

PHP’s `==` coerces numeric-looking strings. Strings matching `0e[0-9]+` become **float 0** in numeric context, so two different “magic hashes” compare equal:

```php
"0e462097431906509019562988736854" == "0e830400451993494058024219903391"; // true
```

Known plaintexts whose **MD5** is a magic hash (examples used in teaching):
- `240610708` → MD5 `0e462097431906509019562988736854`
- `QNKCDZO` → MD5 `0e830400451993494058024219903391`

---

## Vulnerability hypothesis

| Field | Detail |
|-------|--------|
| Class | PHP type juggling / type confusion (CWE-843-ish auth logic) |
| Data flow | Attacker-controlled token/parameter → loose `==` against DB hash/token → auth decision true |
| Preconditions | Loose compare on hash/token; feasible to supply magic value **or** force secret into magic form (version/flow dependent) |
| Impact | Password reset / login bypass → account takeover → often admin → upload/RCE |

### Data-flow diagram

```text
Attacker
  → password reset / confirm endpoint (token param)
  → PHP loose comparison against stored hash
  → success branch: set session / allow password change
  → admin features (upload, modules)
  → webshell / code exec
```

---

## Chain outline

### Step 1 — Map reset / token validation
- Identify parameters: `id`, `e`, `m`, `hash`, `confirm`, etc.
- Trace from request to SQL fetch of member row to comparison.

### Step 2 — Confirm juggling condition
- Prove loose compare exists (source) or behaviorally (lab).
- Document whether exploit is: supply magic token, generate collision-friendly state, or other app-specific path taught in course materials.

### Step 3 — Bypass authentication boundary
- Complete reset or confirm flow as high-value user (admin).
- Establish authenticated session; save cookies for PoC.

### Step 4 — Privilege verification
- Hit admin-only URL; capture proof (HTML title, menu, HTTP 200 vs redirect).

### Step 5 — Bridge to RCE (typical OSWE-style chain)
- File manager / lesson zip upload / module install
- Bypass weak extension filters if present
- Execute PHP; `whoami` / flag read

### Step 6 — Script non-interactive chain
Stages: recon → trigger/bypass → login → upload → verify.  
Reference: `poc-examples/atutor-type-juggling/poc.py`.

---

## Evidence

| Artifact | What it proves |
|----------|----------------|
| Source snippet of `==` on token | Root cause |
| Request/response of successful bypass | Auth impact |
| Admin page after bypass | Privilege |
| Webshell/command output | Terminal impact |
| PoC log with stages | Reproducibility |

Store under `poc-examples/atutor-type-juggling/Screenshots/` and `Logs/`.

---

## Findings

### Root cause
Authentication or token validation used **loose equality** on values that can be coerced to numbers, breaking the assumption that only the legitimate secret satisfies the check.

### Fix ideas
1. Use `hash_equals($a, $b)` for secrets (timing-safe, string compare).
2. Prefer `===` only when types are guaranteed identical strings; still better with `hash_equals`.
3. Do not compare attacker strings to MD5 hex with `==`.
4. Use cryptographically random tokens (sufficient length) + single-purpose, time-limited rows.
5. Invalidate tokens on use; rate-limit reset endpoints.

### OSWE exam tips
- Grep `==` near `md5`, `sha1`, `password`, `token`, `confirm` early.
- Magic hashes are a **teaching tool** — understand coercion, don’t only memorize one string.
- Type juggling alone may not be the flag: always map **post-auth** dangerous features.
- Script cookie/session handling carefully after reset (redirects, multiple Set-Cookie).
- PHP version matters for some edge coercions; note lab PHP version in Environment.

### Common pitfalls
- Testing only `===` mental model while app is PHP 5 loose compares elsewhere
- Forgetting to follow multi-step reset (email link simulation in lab)
- Uploading shell but wrong web path / permissions
- Spending too long on juggling when a second vuln (SQLi) is the intended primary path on a sibling machine

---

## Related resources

| Resource | Path / link |
|----------|-------------|
| PoC + lab notes | `poc-examples/atutor-type-juggling/` |
| Auth/RCE sibling case | `notes/ATUTOR-2.2.1-AUTH-RCE.md` |
| Methodology | `guides/PHP-Type-Juggling-Methodology.md` |
| OWASP type juggling PDF | README Learning Material table |
| Chain trees | `guides/Chain-Decision-Trees.md` |
