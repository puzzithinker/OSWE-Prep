# Speed Drills for OSWE

Timed exercises to reduce exam friction. Do cold (no peeking at full PoCs first). Grade yourself honestly.

**How to use**: set a timer, stop when it rings, write what blocked you, then finish untimed and update `Progress-Tracker.md`.

---

## Drill schedule (suggested)

| Day | Drill IDs | Total time |
|-----|-----------|------------|
| Mon | D1, D2 | ~40 min |
| Wed | D3, D4 | ~45 min |
| Fri | D5, D6 | ~50 min |
| Sun | D7 or full mock stage | 60–90 min |

---

## D1 — Skeleton bootstrap (target: 15 min)

**Setup**: empty directory, no copy-paste from memory of a full exploit.

**Task**:
1. Create `poc.py` with argparse: `--host`, `--port`, `--proxy`, `--lhost`, `--lport`.
2. Session object + optional Burp proxy.
3. Four stage functions: `recon`, `exploit`, `verify`, `main`.
4. Logging helper that prints `[+]`, `[-]`, `[*]`.
5. `if __name__ == "__main__"` wiring.

**Pass criteria**: runs `--help`, proxy toggle works, stages callable.

**Repo help after timer**: `Building a Reusable OSWE PoC Skeleton.md`, `poc-examples/advanced-skeleton/`.

---

## D2 — Boolean blind extract stub (target: 10 min code + 5 min explain)

**Task** (pseudocode or real function):
1. Function `check(condition_sql) -> bool` using true/false page differential OR time.
2. Function `extract_char(query, position) -> str` binary search ASCII 32–126.
3. Explain request budget for 8-char password.

**Pass criteria**: correct binary search bounds; clear true/false signal definition.

**Repo help**: `guides/Blind-SQLi-Automation.md`, second-order / manageengine PoCs.

---

## D3 — Dangerous sink first pass (target: 20 min)

**Setup**: any small open-source PHP/Java/.NET app ZIP (or a repo snapshot).

**Task**:
1. Identify language/stack in 2 minutes.
2. Run mental/physical greps from `guides/Dangerous-Sinks-Cheatsheet.md`.
3. List top 5 sinks with file paths.
4. Rank which one you’d try first and why.

**Pass criteria**: ranked list with data-flow guess for #1.

---

## D4 — Deserial gadget selection (target: 10 min)

**Scenario card** (pick one at random):

| Card | Known facts |
|------|-------------|
| A | Java app, Commons Collections 3.2.1 on classpath, cookie is base64 `rO0…` |
| B | ASP.NET, `__VIEWSTATE` present, `web.config` has machineKey |
| C | PHP, `unserialize($_COOKIE['data'])`, app has custom classes with `__destruct` |
| D | Node, `node-serialize` in package.json, session cookie looks JSON-like |

**Task**: name tool/gadget approach, delivery location, first verification command (ping/sleep/DNS), then RCE follow-up.

**Pass criteria**: coherent 5-step plan without needing the full payload bytes.

---

## D5 — File upload bypass decision tree (target: 5–8 min)

**Scenario**: upload form rejects `.php`, allows images; response shows `/uploads/2024/img_*.jpg`.

**Task**: write ordered bypass list (8 techniques) and how you’d confirm execution vs needing LFI.

**Pass criteria**: includes content-type, double ext, case, magic bytes, path discovery; mentions LFI fallback.

**Repo help**: `guides/File-Upload-to-RCE.md`, `guides/Chain-Decision-Trees.md`.

---

## D6 — Type juggling recognition (target: 8 min)

**Task**: given pseudocode:

```php
if ($_GET['token'] == $row['reset_token']) { /* reset ok */ }
// reset_token is md5 of random data
```

Explain:
1. Why `==` is dangerous
2. What a magic hash is
3. Preconditions for practical exploit
4. Next chain step after password reset

**Pass criteria**: mentions `0e` scientific notation coercion and strict `===` fix.

**Repo help**: `guides/PHP-Type-Juggling-Methodology.md`, ATutor notes.

---

## D7 — Chain narrative (target: 15 min writing)

**Prompt**: “Stored XSS in support ticket viewed by admin; admin can install plugins.”

**Task**: write exam-style chain outline (8–12 bullets) + evidence list + PoC stages titles only.

**Pass criteria**: clear privilege boundary crossing; no skipped trust steps.

**Repo help**: `guides/XSS-to-RCE-Chaining.md`, Atmail study.

---

## D8 — XXE path choice (target: 8 min)

**Facts**: endpoint accepts XML; no reflection of entity body; outbound HTTP allowed.

**Task**: choose in-band vs error-based vs OOB; sketch DTD hosting plan; one SSRF follow-up idea.

**Repo help**: `guides/XXE-Attack-Vectors.md`, xxe PoC Notes.

---

## D9 — Postgres SQLi RCE path (target: 10 min)

**Facts**: stacked queries work; `current_user` is superuser; web root guessed at `/opt/app/web/`.

**Task**: ordered techniques: `COPY`, large objects, `pg_read_file` for recon, webshell write, verify.

**Repo help**: `guides/Postgres-SQLi-to-RCE.md`, ManageEngine notes.

---

## D10 — Full mock stage (target: 90 min)

**Setup**: pick one `poc-examples/*` target you have **not** scripted yourself from scratch recently. Or a bmdyy/PortSwigger lab.

**Rules**:
1. Notes in CASE-template form as you go
2. Manual confirm then script
3. No reading the example `poc.py` until 60 min mark (optional peek)
4. Produce working stages or honest failure write-up

**Pass criteria**: either flag/RCE proof + report snippet, or clear pivot plan if blocked.

---

## Scoring log

| Date | Drill | Time | Pass? | Blocker | Fix |
|------|-------|------|-------|---------|-----|
| | | | | | |

---

## Related

- [Exam-Day-Runbook.md](Exam-Day-Runbook.md)
- [Progress-Tracker.md](Progress-Tracker.md)
- [drills/Cold-Start-Drills.md](drills/Cold-Start-Drills.md) (longer scenario cards)
- [study-log/](study-log/) (session logging)
