"""Command line interface for Mnemos.

Every command goes through the store. There is no in-process copy of
durable facts anywhere in this module.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from .agent import RecallEngine
from .memory.agreement import Agreement, AgreementError
from .memory.gate import evaluate_payment
from .memory.keepsake import export_keepsake, import_keepsake
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

    agree = sub.add_parser("agree", help="create an agreement and mark it agreed")
    agree.add_argument("name")
    agree.add_argument("--with", dest="counterparty", help="counterparty")
    agree.add_argument("--amount", type=float, help="agreed amount")
    agree.add_argument("--note")

    advance = sub.add_parser("advance", help="move an agreement one state forward")
    advance.add_argument("name")
    advance.add_argument("--to", required=True, help="target state")

    pay = sub.add_parser("pay", help="pay against a remembered agreement")
    pay.add_argument("name")
    pay.add_argument("amount", type=float)

    keepsake = sub.add_parser("keepsake", help="portable memory packs")
    keepsake_sub = keepsake.add_subparsers(dest="keepsake_command", required=True)

    export = keepsake_sub.add_parser("export", help="write memory to a .mne pack")
    export.add_argument("path")

    import_ = keepsake_sub.add_parser("import", help="merge a .mne pack into memory")
    import_.add_argument("path")

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

        if args.command == "agree":
            agreement = Agreement(
                store,
                args.name,
                amount=args.amount,
                counterparty=args.counterparty,
                note=args.note,
            )
            agreement.advance("agreed")
            print(f"agreement {args.name} is agreed")
            return 0

        if args.command == "advance":
            agreement = Agreement.open(store, args.name)
            if agreement is None:
                print(f"no agreement named {args.name!r}")
                return 1
            try:
                agreement.advance(args.to)
            except AgreementError as error:
                print(f"refused: {error}")
                return 1
            print(f"agreement {args.name} is now {agreement.state}")
            return 0

        if args.command == "pay":
            result = evaluate_payment(store, args.name, args.amount)
            print(f"gate: {result.reason}")
            if result.allowed:
                print("payment authorized (executor not wired yet)")
                return 0
            print("payment refused")
            return 1

        if args.command == "keepsake":
            if args.keepsake_command == "export":
                summary = export_keepsake(store, args.path)
                print(
                    f"keepsake written to {summary['path']} "
                    f"({summary['entities']} entities, "
                    f"{summary['events']} events)"
                )
                return 0
            summary = import_keepsake(store, args.path)
            print(
                f"keepsake merged: {summary.get('entities_imported', 0)} entities, "
                f"{summary.get('events_imported', 0)} events"
            )
            return 0

        parser.error(f"unknown command {args.command!r}")
        return 2
    finally:
        store.close()
