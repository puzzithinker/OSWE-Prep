# Cold-Start Drills (Scenario Cards)

Longer exercises than `Speed-Drills.md`. Work **without** opening solution PoCs first. After the timer, compare with repo notes and update `study-log/`.

**Answer keys**: intentional hints only at the bottom of each card — not full exploits.

---

## How to run a card

1. Set timer (suggested on card).  
2. Produce: CASE-template notes + chain outline + PoC stage titles + first manual test plan.  
3. Optional stretch: implement stub functions in Python.  
4. Debrief: what was slow? Update `Progress-Tracker.md` and `study-log/weak-areas.md`.

---

## Card A — PHP reset token (45 min)

**Facts**
- PHP 5.6 app, source provided.
- Password reset URL: `/reset.php?user=admin&token=HEX`.
- Snippet in source:

```php
if ($token == $row['reset_token']) { /* set session admin */ }
// reset_token is md5(random)
```

**Tasks**
1. Name the vuln class and root cause in one paragraph.  
2. List preconditions for practical exploit.  
3. Outline chain from bypass to RCE (assume admin file manager exists).  
4. Write 5 PoC stages with function names.  
5. List 3 failed-attempt notes you’d record in a report.

**Hint**: loose compare + magic hashes; see type juggling guide.

---

## Card B — Java cookie blob (45 min)

**Facts**
- War deploy; Commons Collections 3.2.1 in `WEB-INF/lib`.
- Cookie `sessionData` Base64 starts with `rO0AB`.
- `ObjectInputStream` on cookie bytes in `AuthFilter`.

**Tasks**
1. Identify serialization magic.  
2. Choose tool + initial gadget approach.  
3. Verification ladder (3 steps before interactive shell).  
4. argparse design for a PoC.  
5. Where do you look if CommonsCollections1 fails?

**Hint**: `AC ED 00 05`; ysoserial; try multiple CC gadgets; OOB first.

---

## Card C — Postgres time delay (60 min)

**Facts**
- Unauth `GET /servlet/Sync?id=1`  
- Response delays 5s with `id=1;SELECT pg_sleep(5)--`  
- Tomcat on Linux appliance under `/opt/vendor/`.

**Tasks**
1. Confirm dialect and stacked capability.  
2. Privilege recon SQL list (5 queries).  
3. RCE plan without assuming `xp_cmdshell`.  
4. Request budget estimate to extract 12-char path via boolean (if available) or time.  
5. Webshell language choice + why.

**Hint**: ManageEngine-class / Postgres guide; JSP not PHP.

---

## Card D — Stored XSS mail (45 min)

**Facts**
- Webmail; users can send HTML mail.  
- Admin opens abuse reports.  
- Admin can install plugins via multipart POST `/admin/plugin/install` with field `csrf`.

**Tasks**
1. Draw trust-boundary diagram.  
2. Explain why HttpOnly doesn’t stop you.  
3. List data you must capture from a normal admin install request.  
4. PoC stages including honesty about “admin open” trigger.  
5. Evidence list for report.

**Hint**: XSS-to-RCE guide; Atmail pattern.

---

## Card E — ViewState only (45 min)

**Facts**
- ASP.NET app; `__VIEWSTATE` present.  
- `web.config` readable via path traversal read (not include).  
- machineKey SHA1 + AES present.

**Tasks**
1. Is MAC a blocker? Why/why not?  
2. Tooling chain to first ping.  
3. Difference vs DNN cookie deserial.  
4. PoC stages.  
5. Remediation bullets for report.

**Hint**: .NET guide; known keys = forgeable ViewState.

---

## Card F — Upload + mystery path (40 min)

**Facts**
- Upload allows `.png` only; content-type checked client-side only.  
- Server stores as `/media/2024/<random>.png`.  
- There is also `?page=` include of PHP files.

**Tasks**
1. Ordered bypass plan (8 ideas).  
2. Two separate RCE strategies (direct exec vs LFI).  
3. Which strategy first and why.  
4. Stage titles for combined PoC.

**Hint**: File-Upload + LFI guides.

---

## Card G — Node package.json (30 min)

**Facts**
```json
"dependencies": { "node-serialize": "0.0.4", "express": "4.x" }
```
- Session cookie looks like URL-encoded JSON.

**Tasks**
1. Grep plan for source.  
2. Payload concept (no need full encoding).  
3. Verify without reverse shell.  
4. Post-RCE loot list (env, files).

**Hint**: node-serialize Notes; IIFE marker.

---

## Card H — Blind boolean noise (40 min)

**Facts**
- True/false lengths differ by 3–5 bytes randomly.  
- Status always 200.  
- One substring appears only on true: `data-ok="1"`.

**Tasks**
1. Write `is_true(resp)` carefully.  
2. Pseudocode extract 1 char.  
3. When would you abandon boolean for time?  
4. What to extract first for chain value (prioritize).

**Hint**: Blind SQLi automation guide.

---

## Card I — Full mock exam slice (3 hours)

**Setup**: Pick one repo `poc-examples/*` you haven’t done from scratch recently, **or** a bmdyy lab.

**Rules**
- No reading `poc.py` until 90 minutes in (optional).  
- CASE notes continuous.  
- Report snippet for the target at end.  
- Working stages or honest failure + pivot plan.

**Debrief template** in `study-log/README.md`.

---

## Tracking table

| Date | Card | Time used | Output quality (1–5) | Weak skill exposed |
|------|------|-----------|----------------------|--------------------|
| | | | | |

---

## Related

- [Speed-Drills.md](../Speed-Drills.md)  
- [Exam-Day-Runbook.md](../Exam-Day-Runbook.md)  
- [Progress-Tracker.md](../Progress-Tracker.md)  
- [study-log/](../study-log/)  
