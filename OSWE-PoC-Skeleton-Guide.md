# OSWE PoC Skeleton Implementation Guide

This guide provides complete, reusable PoC skeleton examples for OSWE case studies based on the "Building a Reusable OSWE PoC Skeleton" methodology.

## Quick Start Setup

### 1. Install `uv` Package Manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create a New PoC Project

```bash
# For each vulnerability case study
uv init --bare --no-readme --vcs git <project-name>
cd <project-name>

# Create directory structure
mkdir {Archives,Screenshots,Logs}
touch Notes.md
```

### 3. Configure .gitignore

```text
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info
.venv
.env
env/
.mypy_cache/
.dmypy.json
dmypy.json
.vscode/
user.json
*.log
Logs/*
Archives/*
Screenshots/*
```

## The Skeleton Components

Every PoC follows this structure:

1. **Argument Parsing** - CLI interface with grouped arguments
2. **Context Management** - Dataclass to hold configuration and state
3. **Stage-based Execution** - Logical separation of exploit phases
4. **Logging** - Track progress and debugging
5. **Session Management** - HTTP requests with proper error handling

## Complete PoC Template Structure

### Base Template (poc_template.py)

```python
#!/usr/bin/env python3
"""
OSWE PoC Skeleton Template
Exploit: [Vulnerability Name]
CVE: [CVE-ID]
Target: [Application Name and Version]
"""

import argparse
import requests
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CHARSETS for Blind SQLi and other injection testing
# ============================================================================

CHARSETS = {
    "alpha": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "alnum": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    "hex": "0123456789abcdef",
    "ascii": "".join(chr(i) for i in range(32, 127)),
    "symbols": "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~",
    "base64": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=",
    "numeric": "0123456789",
}

# ============================================================================
# EXPLOIT CONTEXT - Central configuration and state management
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    """Centralized exploit configuration and runtime state."""

    # Target configuration
    target_ip: str
    target_port: int
    target_api_port: int
    protocol: str = "http"

    # Attacker configuration
    attacker_ip: str
    attacker_port: int
    payload_port: int

    # Exploit behavior
    delay: int = 3
    proxy: Optional[str] = None

    # Identity/user management
    username: Optional[str] = None
    password: Optional[str] = None

    # Runtime state
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    authenticated: bool = field(default=False, repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build ExploitContext from CLI arguments."""
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            target_api_port=args.target_api_port,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            payload_port=args.payload_port,
            delay=args.delay,
            proxy=args.proxy,
            username=args.username,
            password=args.password,
        )

    def get_base_url(self) -> str:
        """Construct base URL for target."""
        return f"{self.protocol}://{self.target_ip}:{self.target_port}"

    def get_api_url(self) -> str:
        """Construct API URL for target."""
        return f"{self.protocol}://{self.target_ip}:{self.target_api_port}"

    def get_proxies(self) -> Optional[dict]:
        """Return proxy configuration for requests."""
        if self.proxy:
            return {"http": self.proxy, "https": self.proxy}
        return None

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments with organized groups."""
    parser = argparse.ArgumentParser(
        description="OSWE PoC Exploit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --target-ip 192.168.1.100 --username admin --password secret
  %(prog)s --target-ip 10.10.10.5 --target-port 8080 --proxy http://127.0.0.1:8080
        """
    )

    # Target options
    target_group = parser.add_argument_group("Target options")
    target_group.add_argument(
        "--target-ip",
        type=str,
        required=True,
        help="Target server IP address"
    )
    target_group.add_argument(
        "--target-port",
        type=int,
        default=80,
        help="Target web frontend port (default: 80)"
    )
    target_group.add_argument(
        "--target-api-port",
        type=int,
        default=5000,
        help="Target API port (default: 5000)"
    )

    # Attacker options
    attacker_group = parser.add_argument_group("Attacker options")
    attacker_group.add_argument(
        "--listening-ip",
        type=str,
        default="127.0.0.1",
        help="IP to listen on for reverse shell (default: 127.0.0.1)"
    )
    attacker_group.add_argument(
        "--listening-port",
        type=int,
        default=9001,
        help="Port to listen for reverse shell (default: 9001)"
    )
    attacker_group.add_argument(
        "--payload-port",
        type=int,
        default=9999,
        help="Port for payload delivery (default: 9999)"
    )

    # Exploit options
    exploit_group = parser.add_argument_group("Exploit options")
    exploit_group.add_argument(
        "--delay",
        type=int,
        default=3,
        help="Response delay in seconds for timing inference (default: 3)"
    )

    # Identity options
    identity_group = parser.add_argument_group("Identity options")
    identity_group.add_argument(
        "--username",
        type=str,
        help="Username for authentication"
    )
    identity_group.add_argument(
        "--password",
        type=str,
        help="Password for authentication"
    )

    # Optional options
    optional_group = parser.add_argument_group("Optional options")
    optional_group.add_argument(
        "--charset",
        choices=CHARSETS.keys(),
        default="alnum",
        help="Charset for blind SQLi extraction (default: alnum)"
    )
    optional_group.add_argument(
        "--proxy",
        type=str,
        help="HTTP proxy for debugging (e.g., http://127.0.0.1:8080)"
    )

    return parser.parse_args()

# ============================================================================
# EXPLOIT STAGES
# ============================================================================

def stage_recon(ctx: ExploitContext) -> bool:
    """Stage 1: Reconnaissance - verify target is reachable."""
    print(f"[*] Stage 1: Reconnaissance")
    print(f"[*] Target: {ctx.get_base_url()}")

    try:
        response = ctx.session.get(
            ctx.get_base_url(),
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )
        print(f"[+] Target is reachable (HTTP {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[-] Target unreachable: {e}")
        return False

def stage_authenticate(ctx: ExploitContext) -> bool:
    """Stage 2: Authentication - login to target application."""
    print(f"\n[*] Stage 2: Authentication")

    if not ctx.username or not ctx.password:
        print("[!] No credentials provided, skipping authentication")
        return True

    # Example login - customize per application
    login_url = f"{ctx.get_base_url()}/login"
    login_data = {
        "username": ctx.username,
        "password": ctx.password
    }

    try:
        response = ctx.session.post(
            login_url,
            data=login_data,
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        # Check for successful authentication (customize per app)
        if "Welcome" in response.text or response.status_code == 200:
            print(f"[+] Successfully authenticated as {ctx.username}")
            ctx.authenticated = True
            return True
        else:
            print(f"[-] Authentication failed")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] Authentication error: {e}")
        return False

def stage_exploit(ctx: ExploitContext) -> bool:
    """Stage 3: Exploitation - execute the main exploit."""
    print(f"\n[*] Stage 3: Exploitation")

    # TODO: Implement vulnerability-specific exploitation logic
    print("[!] Exploit stage not implemented - customize per vulnerability")

    return True

def stage_verify(ctx: ExploitContext) -> bool:
    """Stage 4: Verification - verify exploitation was successful."""
    print(f"\n[*] Stage 4: Verification")

    # TODO: Implement verification logic
    print("[!] Verification stage not implemented - customize per vulnerability")

    return True

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution flow."""
    print("[+] OSWE PoC Skeleton")
    print("[+] " + "=" * 60)

    # Parse arguments and build context
    args = parse_args()
    ctx = ExploitContext.from_args(args)

    # Execute exploit stages
    stages = [
        ("Reconnaissance", stage_recon),
        ("Authentication", stage_authenticate),
        ("Exploitation", stage_exploit),
        ("Verification", stage_verify),
    ]

    for stage_name, stage_func in stages:
        if not stage_func(ctx):
            print(f"\n[-] Stage '{stage_name}' failed. Aborting.")
            sys.exit(1)

    print("\n[+] Exploit completed successfully!")
    print("[+] " + "=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Exploit interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

## Case Study Examples

The following sections provide complete, working PoC examples for specific OSWE vulnerabilities using the skeleton framework.

### Directory Structure for Practice

```
OSWE-Prep/
├── poc-examples/
│   ├── atutor-type-juggling/
│   │   ├── poc.py
│   │   ├── Notes.md
│   │   ├── Archives/
│   │   ├── Logs/
│   │   └── Screenshots/
│   ├── bassmaster-js-injection/
│   ├── manageengine-sqli/
│   └── atmail-xss-rce/
```

## Next Steps

1. Review the complete PoC examples in the following sections
2. Set up a lab environment for each vulnerability
3. Customize the skeleton for your specific target
4. Practice writing stages incrementally
5. Test each stage independently before chaining

## Tips for OSWE Exam

1. **Start with the skeleton** - Don't write from scratch
2. **Test incrementally** - Verify each stage before moving forward
3. **Use --proxy flag** - Debug with Burp Suite when needed
4. **Document everything** - Use Notes.md and Screenshots/
5. **Keep it simple** - Don't over-engineer, focus on working code
6. **Time management** - The skeleton saves hours during the exam

## Common Patterns by Vulnerability Type

### SQL Injection
- Stage 1: Confirm injection point
- Stage 2: Extract data length/existence
- Stage 3: Extract data character-by-character
- Stage 4: Leverage SQLi for RCE (xp_cmdshell, pg_exec, INTO OUTFILE)

### Deserialization
- Stage 1: Identify serialized data location (cookie, parameter)
- Stage 2: Generate malicious payload (ysoserial, etc.)
- Stage 3: Deliver payload to application
- Stage 4: Trigger deserialization and verify RCE

### XSS to RCE
- Stage 1: Inject stored XSS in user-visible content
- Stage 2: Craft payload to abuse admin functionality
- Stage 3: Wait for or trigger admin interaction
- Stage 4: Verify privileged action execution

### Authentication Bypass
- Stage 1: Identify bypass mechanism (type juggling, SQL, etc.)
- Stage 2: Craft authentication bypass payload
- Stage 3: Gain authenticated session
- Stage 4: Perform privileged actions

### Type Juggling
- Stage 1: Identify loose comparison points
- Stage 2: Craft magic hash or comparison bypass
- Stage 3: Bypass authentication or authorization
- Stage 4: Escalate to RCE if possible
