#!/usr/bin/env python3
"""
Custom Logging Module for OSWE PoC Development

Provides structured logging with:
- Color-coded console output
- File-based audit trail
- Stage-specific logging
- Request/response capture
- Timing information

Usage:
    from modules.logger import Logger

    log = Logger("exploit_name")
    log.info("Starting exploitation")
    log.success("Payload executed")
    log.error("Authentication failed")
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Logger:
    """
    Custom logger for OSWE exploit development.

    Features:
    - Dual output: console (colored) and file (plain text)
    - Stage tracking
    - Request/response logging
    - Timing information
    - Audit trail in Logs/ directory
    """

    def __init__(self, name: str, log_dir: str = "Logs", verbose: bool = True):
        """
        Initialize logger.

        Args:
            name: Logger name (typically exploit name)
            log_dir: Directory for log files
            verbose: Enable verbose console output
        """
        self.name = name
        self.verbose = verbose
        self.start_time = datetime.now()

        # Create log directory
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create log file with timestamp
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{name}_{timestamp}.log"

        # Initialize file logger
        self._setup_file_logger()

        # Stage tracking
        self.current_stage = None
        self.stage_count = 0

    def _setup_file_logger(self):
        """Configure file-based logging."""
        self.file_logger = logging.getLogger(f"{self.name}_file")
        self.file_logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        self.file_logger.handlers.clear()

        # File handler
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.DEBUG)

        # Format: [timestamp] [LEVEL] message
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        self.file_logger.addHandler(fh)

        # Write header
        self._log_header()

    def _log_header(self):
        """Write log file header."""
        header = f"""
{'=' * 80}
Exploit: {self.name}
Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
Log File: {self.log_file}
{'=' * 80}
"""
        self.file_logger.info(header.strip())

    def _console(self, message: str, color: str = ""):
        """Print colored message to console."""
        if self.verbose:
            print(f"{color}{message}{Colors.ENDC}")

    def _file(self, message: str, level: str = "INFO"):
        """Write message to file."""
        log_method = getattr(self.file_logger, level.lower(), self.file_logger.info)
        log_method(message)

    def info(self, message: str):
        """Log informational message."""
        self._console(f"[*] {message}", Colors.BLUE)
        self._file(message, "INFO")

    def success(self, message: str):
        """Log success message."""
        self._console(f"[+] {message}", Colors.GREEN)
        self._file(f"SUCCESS: {message}", "INFO")

    def error(self, message: str):
        """Log error message."""
        self._console(f"[-] {message}", Colors.RED)
        self._file(f"ERROR: {message}", "ERROR")

    def warning(self, message: str):
        """Log warning message."""
        self._console(f"[!] {message}", Colors.YELLOW)
        self._file(f"WARNING: {message}", "WARNING")

    def debug(self, message: str):
        """Log debug message."""
        if self.verbose:
            self._console(f"[DEBUG] {message}", Colors.CYAN)
        self._file(f"DEBUG: {message}", "DEBUG")

    def stage(self, stage_name: str):
        """
        Begin a new exploit stage.

        Args:
            stage_name: Name of the stage
        """
        self.stage_count += 1
        self.current_stage = stage_name

        separator = "=" * 60
        stage_msg = f"Stage {self.stage_count}: {stage_name}"

        self._console(f"\n{separator}", Colors.BOLD)
        self._console(stage_msg, Colors.BOLD + Colors.HEADER)
        self._console(separator, Colors.BOLD)

        self._file(f"\n{'=' * 80}")
        self._file(f"STAGE {self.stage_count}: {stage_name}")
        self._file(f"{'=' * 80}")

    def stage_complete(self, success: bool = True):
        """Mark current stage as complete."""
        if self.current_stage:
            status = "COMPLETED" if success else "FAILED"
            self.info(f"Stage '{self.current_stage}' {status}")

    def http_request(self, method: str, url: str, **kwargs):
        """
        Log HTTP request details.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional request details (headers, data, etc.)
        """
        self.debug(f"HTTP {method} {url}")

        if 'data' in kwargs:
            self.debug(f"Request Data: {kwargs['data']}")

        if 'json' in kwargs:
            self.debug(f"Request JSON: {kwargs['json']}")

        if 'headers' in kwargs:
            self.debug(f"Request Headers: {kwargs['headers']}")

        # Log to file only
        self._file(f"REQUEST: {method} {url}", "DEBUG")
        for key, value in kwargs.items():
            self._file(f"  {key}: {value}", "DEBUG")

    def http_response(self, status_code: int, url: str, response_text: str = None):
        """
        Log HTTP response details.

        Args:
            status_code: HTTP status code
            url: Request URL
            response_text: Response body (optional, truncated if long)
        """
        self.debug(f"HTTP {status_code} from {url}")

        if response_text:
            # Truncate long responses
            truncated = response_text[:500] + "..." if len(response_text) > 500 else response_text
            self.debug(f"Response: {truncated}")

        # Full response to file
        self._file(f"RESPONSE: {status_code} from {url}", "DEBUG")
        if response_text:
            self._file(f"Response Body:\n{response_text}", "DEBUG")

    def sqli_attempt(self, payload: str, result: Optional[str] = None):
        """
        Log SQL injection attempt.

        Args:
            payload: SQL injection payload
            result: Extraction result (if any)
        """
        self.debug(f"SQLi Payload: {payload}")
        if result:
            self.success(f"Extracted: {result}")

        self._file(f"SQLI: {payload}", "DEBUG")
        if result:
            self._file(f"SQLI RESULT: {result}", "INFO")

    def payload_execution(self, payload_type: str, payload: str, success: bool):
        """
        Log payload execution attempt.

        Args:
            payload_type: Type of payload (XSS, RCE, etc.)
            payload: Payload content
            success: Whether execution was successful
        """
        status = "EXECUTED" if success else "FAILED"
        msg = f"{payload_type} payload {status}"

        if success:
            self.success(msg)
        else:
            self.error(msg)

        self._file(f"PAYLOAD ({payload_type}): {payload}", "DEBUG")
        self._file(f"PAYLOAD STATUS: {status}", "INFO")

    def credential(self, username: str, password: str, context: str = ""):
        """
        Log discovered credentials.

        Args:
            username: Username
            password: Password
            context: Additional context (where found, etc.)
        """
        msg = f"Credentials: {username}:{password}"
        if context:
            msg += f" ({context})"

        self.success(msg)
        self._file(f"CREDENTIAL: {username}:{password} | Context: {context}", "INFO")

    def flag(self, flag_value: str, location: str = ""):
        """
        Log captured flag.

        Args:
            flag_value: Flag value
            location: Where flag was found
        """
        msg = f"FLAG: {flag_value}"
        if location:
            msg += f" (from {location})"

        self.success(msg)
        self._file(f"FLAG: {flag_value} | Location: {location}", "INFO")

    def timing(self, operation: str, duration: float):
        """
        Log operation timing.

        Args:
            operation: Operation name
            duration: Duration in seconds
        """
        self.debug(f"{operation} took {duration:.2f}s")
        self._file(f"TIMING: {operation} = {duration:.2f}s", "DEBUG")

    def summary(self, **kwargs):
        """
        Log final summary.

        Args:
            **kwargs: Key-value pairs for summary
        """
        elapsed = (datetime.now() - self.start_time).total_seconds()

        separator = "=" * 60
        self._console(f"\n{separator}", Colors.BOLD)
        self._console("EXPLOITATION SUMMARY", Colors.BOLD + Colors.HEADER)
        self._console(separator, Colors.BOLD)

        self._file(f"\n{'=' * 80}")
        self._file("EXPLOITATION SUMMARY")
        self._file(f"{'=' * 80}")

        for key, value in kwargs.items():
            self._console(f"  {key}: {value}", Colors.CYAN)
            self._file(f"{key}: {value}", "INFO")

        self._console(f"  Total Time: {elapsed:.2f}s", Colors.CYAN)
        self._console(separator, Colors.BOLD)

        self._file(f"Total Time: {elapsed:.2f}s", "INFO")
        self._file(f"{'=' * 80}")

        # Log file location
        self.info(f"Full log saved to: {self.log_file}")

    def close(self):
        """Close logger and finalize log file."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self._file(f"\nExploit completed in {elapsed:.2f}s", "INFO")
        self._file(f"{'=' * 80}\n", "INFO")


# Convenience function for quick logger creation
def create_logger(name: str, verbose: bool = True) -> Logger:
    """
    Create and return a logger instance.

    Args:
        name: Logger name
        verbose: Enable verbose output

    Returns:
        Logger instance
    """
    return Logger(name, verbose=verbose)


# Example usage
if __name__ == "__main__":
    # Demo logger functionality
    log = create_logger("demo_exploit")

    log.stage("Reconnaissance")
    log.info("Scanning target for vulnerabilities")
    log.http_request("GET", "http://target.com/")
    log.http_response(200, "http://target.com/", "<!DOCTYPE html>...")
    log.success("Target is reachable")
    log.stage_complete(success=True)

    log.stage("Exploitation")
    log.info("Attempting SQL injection")
    log.sqli_attempt("' OR 1=1--", result="admin")
    log.success("SQL injection successful")
    log.credential("admin", "password123", "SQL injection")
    log.stage_complete(success=True)

    log.stage("Post-Exploitation")
    log.info("Searching for flags")
    log.flag("OSWE{test_flag_12345}", "/root/proof.txt")
    log.stage_complete(success=True)

    log.summary(
        Target="http://target.com",
        Vulnerability="SQL Injection",
        Credentials_Found="1",
        Flags_Captured="1",
        Status="SUCCESS"
    )

    log.close()
