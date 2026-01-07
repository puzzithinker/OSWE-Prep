# MSSQL SQLi to xp_cmdshell Case Study

## Environment
**Host OS**: Windows Server 2019
**Application**: Custom ASP.NET MVC application
**Database**: Microsoft SQL Server 2019 Express
**URL**: http://192.168.1.50/Products/Details?id=1
**Credentials**: SQL Server runs as NT AUTHORITY\NETWORK SERVICE

## Recon
**Entry Points**: GET parameter `id` in `/Products/Details` endpoint
**Source Code Focus**: ProductsController.cs - String concatenation in SQL query
**Render Locations**: Product details page displays query results

### Vulnerable Code
```csharp
// ProductsController.cs (line 42)
public ActionResult Details(int id)
{
    string query = "SELECT * FROM Products WHERE ProductID = " + id; // VULNERABLE
    var product = db.Database.SqlQuery<Product>(query).FirstOrDefault();
    return View(product);
}
```

## Vulnerability Hypothesis
**Class**: SQL Injection (CWE-89) + Improper Privilege Management (CWE-269)
**Data Flow**: HTTP GET parameter → Controller → String concatenation → SqlQuery()
**Preconditions**: SQL Server user has sysadmin privileges, xp_cmdshell can be enabled

## Chain Outline
1. Identify SQLi via time-based detection (WAITFOR DELAY)
2. Confirm MSSQL via error messages or @@VERSION
3. Check sysadmin privileges with IS_SRVROLEMEMBER()
4. Enable xp_cmdshell via stacked queries
5. Execute OS commands via xp_cmdshell
6. Verify RCE with ping callback or reverse shell

## Evidence
- `Screenshots/01-sqli-time-based.png` - WAITFOR DELAY causing 5 second delay
- `Screenshots/02-enable-xp-cmdshell.png` - Stacked queries enabling xp_cmdshell
- `Screenshots/03-ping-callback.png` - tcpdump showing ICMP packets
- `Logs/exploitation.log` - Full PoC output
- `Logs/mssql-audit.log` - SQL Server audit log showing xp_cmdshell execution

## Findings

### Root Cause
Application uses string concatenation to build SQL queries without parameterization. SQL Server service account has excessive sysadmin privileges, allowing xp_cmdshell enablement and OS command execution.

**Fix**:
```csharp
// SECURE: Parameterized query
public ActionResult Details(int id)
{
    string query = "SELECT * FROM Products WHERE ProductID = @id";
    var product = db.Database.SqlQuery<Product>(query,
        new SqlParameter("@id", id)).FirstOrDefault();
    return View(product);
}
```

**Defense in Depth**:
- Remove sysadmin from application SQL user
- Disable xp_cmdshell permanently
- Implement WAF rules for SQL injection patterns
- Run SQL Server with least-privilege service account
