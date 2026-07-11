# Report Snippet Templates (OSWE-style)

Reusable Markdown sections for practice reports and exam write-ups. Adapt wording to official template requirements. Prefer **process + evidence** over raw dump of every failed payload.

---

## Global front matter

```markdown
# WEB-300 / OSWE Practice Report

**Candidate**: [name]
**Date**: [YYYY-MM-DD]
**Exam / Lab ID**: [practice only]
**Environment**: Kali [version], Burp Suite, Python 3.x

## Summary of findings

| Target | Vulnerability class | Impact | Flag / proof |
|--------|---------------------|--------|--------------|
| APP-01 | | RCE / Auth bypass | |
| APP-02 | | | |

## Methodology overview

White-box and black-box review, manual confirmation in Burp, then non-interactive
Python PoC (`requests`) following a stage-based skeleton. Proxy used during
development; disabled for final verification runs.
```

---

## Per-target skeleton

```markdown
# Target: [APP-NAME] ([IP/hostname])

## 1. Environment

| Item | Value |
|------|-------|
| URL | http://x.x.x.x:port |
| Stack | e.g. PHP 7 / Apache / MySQL |
| Source | provided ZIP / decompiled WAR / … |
| Roles tested | guest, user, admin |
| PoC path | `./pocs/app01/poc.py` |

## 2. Reconnaissance

### Application map
- Entry points: …
- Auth mechanisms: …
- Interesting parameters: …
- File upload / admin / API routes: …

### Source review highlights
- Files reviewed: `path/a.php`, `Controller.cs`, …
- Grep / sink hits: `unserialize(`, string-concat SQL, …
- High-value observation: …

### Diagram (optional)
```
User input (param X) → Function Y → Sink Z → Impact
```

## 3. Vulnerability

### Classification
- **CWE / class**: e.g. CWE-89 SQL Injection
- **Location**: file + function + line (if known)
- **Preconditions**: auth level, feature flags, DB privileges

### Root cause
[1–3 paragraphs. Explain *why* the code is wrong, not only that it is wrong.]

### Vulnerable pattern (sanitized / illustrative)
```language
// illustrative only — match exam policy on code disclosure
```

### Data flow
1. Attacker controls …
2. Application passes data to …
3. Sink interprets data as …
4. Resulting effect: …

## 4. Exploitation chain

| Step | Action | Result |
|------|--------|--------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | Flag / shell | |

### Manual confirmation
- Request summary (method, path, critical param)
- Observable effect (delay, error, content, callback)
- Screenshot: `evidence/app01/01-confirm.png`

### Automated PoC
```bash
python3 poc.py --host x.x.x.x --port 80 --proxy http://127.0.0.1:8080
# final:
python3 poc.py --host x.x.x.x --port 80 --lhost x.x.x.x --lport 4444
```

PoC stages implemented: recon, …, exploit, verify.

### Proof of impact
- Command output / flag value: …
- Screenshot: `evidence/app01/02-rce.png`
- Listener log: `evidence/app01/03-listener.txt`

## 5. Remediation (high level)

1. Immediate: …
2. Code: parameterized queries / strict compare / safe deserializer / …
3. Defense in depth: WAF is not a fix; least privilege DB user; …

## 6. Failed attempts (brief)

| Attempt | Why it failed | Lesson |
|---------|---------------|--------|
| | | |

## 7. Timeline (optional)

| Time | Activity |
|------|----------|
| 0:00 | Start recon |
| 0:25 | Confirmed sink |
| 1:40 | PoC RCE |
```

---

## Short “stage log” (during exam, paste later)

```markdown
### Stage log — [APP] — [timestamp]
- Hypothesis:
- Confirm request:
- Effect:
- Next stage:
- Blocker:
- Evidence file:
```

---

## Evidence naming convention

```text
evidence/
  app01/
    01-recon-version.png
    02-sqli-confirm.png
    03-data-extract.png
    04-rce-whoami.png
    05-flag.png
    poc-run-final.txt
```

Rules:
- Number chronologically
- One claim per screenshot
- Include URL bar or terminal context when possible
- Redact unrelated personal data

---

## Vulnerability-class one-liners (expand in section 3)

| Class | One-line root cause |
|-------|---------------------|
| SQLi | Untrusted input concatenated into SQL executed by the DB engine |
| XSS→RCE | Unescaped content executes in privileged browser context and triggers dangerous admin actions |
| Type juggling | Loose comparison (`==`) treats distinct strings as equal under PHP type coercion |
| Java deserial | `ObjectInputStream.readObject` on untrusted bytes with gadget classes on classpath |
| .NET deserial | Signed/unsigned ViewState or cookie deserialized into dangerous object graph |
| PHP POI | `unserialize` on user data with usable POP chain / magic methods |
| Node deserial | `node-serialize` IIFE or `eval`/vm on attacker JSON |
| SSTI | User input evaluated as template code in engine context |
| XXE | XML parser resolves external entities / DTD from attacker document |
| File upload | Insufficient validation of name/type/content + web-accessible storage |
| LFI | User-controlled path reaches include/read without canonicalization |

---

## PoC appendix blurb

```markdown
## Appendix A — PoC usage

### Requirements
- Python 3.10+
- `pip install requests` (or project uv lockfile)

### Usage
```bash
cd pocs/app01
python3 poc.py --help
python3 poc.py --host TARGET --port PORT [options]
```

### Stages
The script prints stage banners. Non-zero exit indicates failure at the last stage.

### Safety
Authorized lab/exam targets only. Reverse shells pointed at attacker-controlled listeners only.
```

---

## Quality checklist before submit

- [ ] Each flag has narrative + evidence
- [ ] Chain is reproducible from the write-up + PoC
- [ ] Root cause is technical, not “it was vulnerable”
- [ ] Remediation is realistic
- [ ] No broken image links
- [ ] Consistent target naming with scoreboard
- [ ] Follows latest official exam report rules
