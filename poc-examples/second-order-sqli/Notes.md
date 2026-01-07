# Second-Order SQL Injection PoC Notes

## Vulnerability Summary
- **Target**: Applications with SQL injection in stored data
- **Type**: Second-Order SQLi → Data exfiltration/RCE
- **Impact**: Privilege escalation, data theft, RCE

## Key Concepts
Unlike first-order SQLi, the payload is stored in the database during one operation and executed in a different context later (often with higher privileges).

## Quick Usage
```bash
python3 poc.py 192.168.1.10 80 10.10.14.5 4444 \\
  --register-endpoint /register --trigger-endpoint /admin/search
```

## OSWE Exam Tips
- Look for stored user input: registration, profile updates, comments
- Identify trigger points: admin panels, searches, exports, reports
- Use time-based detection first (SLEEP, WAITFOR)
- Higher privileges in trigger context often allow xp_cmdshell, file writes

## Common Patterns
1. Register with payload in lastname/bio
2. Admin searches users → SQLi executes
3. Export to CSV → SQLi in concatenated query
4. Email notifications → SQLi in template rendering

## References
- PortSwigger: https://portswigger.net/kb/issues/00100210_sql-injection-second-order
- Pentest Blog: https://pentest.blog/exploiting-second-order-sqli-flaws-by-using-burp-custom-sqlmap-tamper/
