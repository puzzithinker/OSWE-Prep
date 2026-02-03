"""
OSWE PoC Advanced Skeleton Modules

Reusable components for OSWE exploit development:
- logger: Structured logging with console and file output
- payload_server: HTTP server for hosting payloads and catching callbacks
- listener: Interactive reverse shell listener with select() multiplexing
- stages: Stage management with dependencies and retry logic
- sqli: Blind SQL injection with binary search and async support
"""

from .logger import Logger, create_logger
from .payload_server import PayloadServer
from .listener import InteractiveListener, ListenerManager, create_listener
from .stages import StageManager, Stage, StageStatus, StageResult
from .sqli import (
    BlindSQLi,
    SQLDialect,
    MySQLDialect,
    PostgreSQLDialect,
    MSSQLDialect,
    SQLiConfig
)

__all__ = [
    # Logger
    'Logger',
    'create_logger',

    # Payload Server
    'PayloadServer',

    # Listener
    'InteractiveListener',
    'ListenerManager',
    'create_listener',

    # Stage Management
    'StageManager',
    'Stage',
    'StageStatus',
    'StageResult',

    # SQL Injection
    'BlindSQLi',
    'SQLDialect',
    'MySQLDialect',
    'PostgreSQLDialect',
    'MSSQLDialect',
    'SQLiConfig',
]

__version__ = '1.0.0'
