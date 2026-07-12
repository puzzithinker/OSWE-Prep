#!/usr/bin/env python3
"""Snippet: standard argparse entry for OSWE-style PoCs."""

from __future__ import annotations

import argparse
from typing import Optional


def build_parser(description: str = "OSWE PoC") -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    t = p.add_argument_group("Target")
    t.add_argument("target_ip", help="Target IP or hostname")
    t.add_argument("target_port", type=int, help="Target port")
    t.add_argument("--https", action="store_true", help="Use HTTPS")

    a = p.add_argument_group("Attacker")
    a.add_argument("listening_ip", nargs="?", default="127.0.0.1", help="Callback / reverse shell IP")
    a.add_argument("listening_port", nargs="?", type=int, default=4444, help="Callback port")

    o = p.add_argument_group("Optional")
    o.add_argument("--proxy", default=None, help="e.g. http://127.0.0.1:8080 (omit for final runs)")
    o.add_argument("--timeout", type=float, default=15.0)
    return p


def base_url(args: argparse.Namespace) -> str:
    scheme = "https" if args.https else "http"
    return f"{scheme}://{args.target_ip}:{args.target_port}"


def proxies(args: argparse.Namespace) -> Optional[dict]:
    if not args.proxy:
        return None
    return {"http": args.proxy, "https": args.proxy}


# Example wiring:
# def main():
#     args = build_parser().parse_args()
#     url = base_url(args)
#     ...
# if __name__ == "__main__":
#     main()
