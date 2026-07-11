# ATutor 2.2.1 — Authentication Weakness → Privileged RCE

**Pattern**: Auth bypass or blind data access → privileged feature → file write / code execution.  
**Related**: type juggling case (`notes/ATUTOR-2.2.1-TYPE-JUGGLING.md`), PoC `poc-examples/atutor-type-juggling/`.  
**Often involves**: SQLi (blind) for credential/token material **or** juggling reset, then **zip/upload** style RCE.

---

## Environment

| Item | Typical lab value |
|------|-------------------|
| App | ATutor **2.2.1** |
| URL | `http://TARGET/ATutor/` |
| Stack | Apache + PHP + MySQL |
| Goals | Account takeover / admin → remote code execution |
| Source focus | Auth, member queries, file/zip import, module paths |

Snapshot after clean install so upload experiments are reversible.

---

## Recon

### Entry points
- Login, registration, password reminder
- Search / blog / social features (often SQLi surface in older LMS apps)
- Course tools, file storage, zip import, photo/module upload
- Admin configuration and user management

### Roles & trust boundaries
```text
Guest → Student → Instructor → Admin
                 ↘ file/zip features may appear before full admin
```

Map **which roles can upload or extract archives**.

### White-box checklist
1. SQL built with string concat near login, search, `member_id`, course ids.
2. Missing auth checks on admin PHP scripts (direct request).
3. Upload handlers: extension blacklist, zip slip / traversal on extract.
4. Paths where extracted files become web-accessible.

### Black-box signals
- Boolean/time blind differences on search or login error paths
- Upload responses revealing absolute paths
- Admin scripts reachable without session (quick win if present)

---

## Vulnerability hypothesis

| Field | Detail |
|-------|--------|
| Class | Broken authn/authz + insecure file handling (chain) |
| Path A | Type juggling / weak token → password reset → admin |
| Path B | Blind SQLi → hash/token/email enum → session or reset abuse |
| Path C | Auth’d low-priv user → insecure zip/upload → webshell |
| Impact | RCE as www-data (or app pool user) |

### Generic chain diagram

```text
[Unauth/low-priv]
    │
    ├─(juggling/SQLi/direct)─► privileged session
    │
    └─► privileged file feature (upload / zip / module)
              │
              ▼
         webshell or PHP in web root
              │
              ▼
             RCE / flag
```

---

## Chain outline (exam-style stages)

### Stage 0 — Environment & notes
Fill CASE template; enable Burp; create student account; note PHP/MySQL versions.

### Stage 1 — Find the auth weakness
Pick the first viable of:
- Loose token compare (see type juggling note)
- SQLi to dump `AT_members` style tables / password hashes
- IDOR on user objects
- Missing `authenticate()` on sensitive script

**Manual proof**: session as user you should not be, or extracted secret.

### Stage 2 — Stabilize access
- PoC: login POST, cookie jar, follow redirects
- Detect role (admin menu markers)

### Stage 3 — Map privileged dangerous actions
Prioritize:
1. Arbitrary file upload
2. Zip upload with extract
3. Plugin/module install
4. Template/config write

Document **filter rules** (extensions, content-type, size).

### Stage 4 — Achieve code execution
- Upload PHP or polyglot per `guides/File-Upload-to-RCE.md`
- Zip traversal if extract is naive (`../` to web root)
- Confirm via HTTP GET with `cmd` or static marker file

### Stage 5 — Non-interactive PoC
Stages in Python: bypass → login → upload/extract → verify callback or response body.  
Do not leave interactive Burp clicks as the only path.

### Stage 6 — Report evidence
Screenshots of bypass, admin proof, shell, flag. Report snippets from `Report-Snippet-Templates.md`.

---

## Evidence

| Evidence | Purpose |
|----------|---------|
| SQLi true/false or dump snippet | Data layer |
| Auth bypass request | Trust boundary fail |
| Upload request + on-disk/URL path | Write primitive |
| Command output | RCE |
| Full PoC transcript | Repro |

---

## Findings

### Root causes (often multiple)
1. Weak cryptographic comparison or injectable queries in identity flows.
2. Authorization not enforced consistently on file/admin features.
3. Upload/zip handling trusts client filenames and types.

### Fixes
- Parameterized SQL everywhere; least-privilege DB user.
- Strict token compares (`hash_equals`); secure reset design.
- AuthZ middleware on every privileged route.
- Upload: allow-list extensions, random server-side names, store outside docroot, no zip slip (canonicalize paths), malware scanning optional.
- Disable dangerous admin features on internet-facing LMS if unused.

### OSWE tips
- ATutor-class machines train **chaining**, not single CVEs in isolation.
- Blind SQLi: budget time for binary search; script early (`guides/Blind-SQLi-Automation.md`).
- Zip/upload filters: keep a bypass matrix open (`guides/File-Upload-to-RCE.md`).
- If reset mail is “sent” in lab, find token in DB via SQLi rather than waiting on SMTP.
- Revert snapshots after destructive upload tests.

### Pitfalls
- Extracting hashes but not cracking/using them within time box — prefer session/reset paths
- Webshell uploaded to non-executed directory
- Forgetting second-order aspects (payload stored, triggered later)

---

## Related resources

| Resource | Location |
|----------|----------|
| Type juggling deep dive | `notes/ATUTOR-2.2.1-TYPE-JUGGLING.md` |
| Working PoC folder | `poc-examples/atutor-type-juggling/` |
| File upload guide | `guides/File-Upload-to-RCE.md` |
| Blind SQLi | `guides/Blind-SQLi-Automation.md` |
| Decision trees | `guides/Chain-Decision-Trees.md` |
