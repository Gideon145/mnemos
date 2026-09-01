"""Command line interface for Mnemos.

Every command goes through the store. There is no in-process copy of
durable facts anywhere in this module.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from .agent import RecallEngine
from .memory.store import MemoryStore

DEFAULT_DB = str(Path.home() / ".mnemos" / "memory.db")


def _slug(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    slug = slug[:limit].rstrip("_")
    return slug or "note"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mnemos", description="agent with memory")
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        help=f"path to the memory database (default: {DEFAULT_DB})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    remember = sub.add_parser("remember", help="store a durable preference")
    remember.add_argument("text")
    remember.add_argument("--category", default="preference")

    ask = sub.add_parser("ask", help="ask the agent a question")
    ask.add_argument("question", nargs="+")

    journal = sub.add_parser("journal", help="append an entry to the daily log")
    journal.add_argument("text", nargs="+")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    store = MemoryStore(args.db)
    try:
        if args.command == "remember":
            name = _slug(args.text)
            store.remember_durable(args.category, name, {"value": args.text})
            print(f"remembered {args.category} {name}")
            return 0

        if args.command == "ask":
            question = " ".join(args.question)
            answer = RecallEngine(store).ask(question)
            print(answer.answer)
            if not answer.found_anything:
                print("(nothing in memory)")
            return 0

        if args.command == "journal":
            store.record_event(acted=[" ".join(args.text)])
            print("journaled")
            return 0

        parser.error(f"unknown command {args.command!r}")
        return 2
    finally:
        store.close()
