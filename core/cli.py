"""Command line interface for Mnemos.

Every command goes through the store. There is no in-process copy of
durable facts anywhere in this module.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from .agent import RecallEngine
from .agent.recap import recap
from .integrations import register_with_virtuals
from .memory.agreement import Agreement, AgreementError
from .memory.keepsake import export_keepsake, import_keepsake
from .memory.tasks import Task, TaskError, unfinished
from .payments import BaseExecutor, DryRunExecutor, pay
from .memory.reflection import accept as accept_proposal
from .memory.reflection import pending as pending_proposals
from .memory.reflection import reflect as run_reflection
from .memory.reflection import reject as reject_proposal
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

    recap_cmd = sub.add_parser("recap", help="summarize the journal and agreements")
    recap_cmd.add_argument("--since", default=None)
    recap_cmd.add_argument("--limit", type=int, default=20)

    register = sub.add_parser("register", help="record this agent's identity")
    register.add_argument("--as", dest="name", default="mnemos")

    agree = sub.add_parser("agree", help="create an agreement and mark it agreed")
    agree.add_argument("name")
    agree.add_argument("--with", dest="counterparty", help="counterparty")
    agree.add_argument("--amount", type=float, help="agreed amount")
    agree.add_argument("--note")

    advance = sub.add_parser("advance", help="move an agreement one state forward")
    advance.add_argument("name")
    advance.add_argument("--to", required=True, help="target state")

    delegate = sub.add_parser("delegate", help="hand an agreement's work to an agent")
    delegate.add_argument("name")
    delegate.add_argument("--to", required=True, dest="agent_id")
    delegate.add_argument("--task", required=True)

    task = sub.add_parser("task", help="create a task that survives restarts")
    task.add_argument("name")
    task.add_argument("objective", nargs="*")

    tasks = sub.add_parser("tasks", help="list all tasks")
    tasks.add_argument("--open", action="store_true", dest="open_only")

    work = sub.add_parser("work", help="mark a task working (or clear a blocker)")
    work.add_argument("name")

    block = sub.add_parser("block", help="mark a task blocked")
    block.add_argument("name")

    complete = sub.add_parser("complete", help="mark a task completed")
    complete.add_argument("name")

    resume = sub.add_parser("resume", help="show unfinished work, work first")

    pay = sub.add_parser("pay", help="pay against a remembered agreement")
    pay.add_argument("name")
    pay.add_argument("amount", type=float)
    pay.add_argument("--live", action="store_true", help="submit on Base Sepolia")

    keepsake = sub.add_parser("keepsake", help="portable memory packs")
    keepsake_sub = keepsake.add_subparsers(dest="keepsake_command", required=True)

    export = keepsake_sub.add_parser("export", help="write memory to a .mne pack")
    export.add_argument("path")

    import_ = keepsake_sub.add_parser("import", help="merge a .mne pack into memory")
    import_.add_argument("path")

    reflect = sub.add_parser("reflect", help="detect repeated patterns in the journal")
    reflect.add_argument("--since", default=None)
    reflect.add_argument("--min-hits", type=int, default=2)

    proposals = sub.add_parser("proposals", help="list pending proposals")

    accept = sub.add_parser("accept", help="promote a proposal to an active preference")
    accept.add_argument("name")

    reject = sub.add_parser("reject", help="archive a proposal")
    reject.add_argument("name")

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

        if args.command == "recap":
            result = recap(store, since=args.since, limit=args.limit)
            print(result.text)
            return 0

        if args.command == "register":
            result = register_with_virtuals(store, name=args.name)
            print(f"registration: {result.note}")
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

        if args.command == "delegate":
            agreement = Agreement.open(store, args.name)
            if agreement is None:
                print(f"no agreement named {args.name!r}")
                return 1
            try:
                agreement.note_delegation(args.agent_id, args.task)
                agreement.advance("delegated")
            except AgreementError as error:
                print(f"refused: {error}")
                return 1
            print(f"delegated {args.name} to {args.agent_id}")
            return 0

        if args.command == "task":
            objective = " ".join(args.objective) or None
            Task(store, args.name, objective=objective)
            print(f"task {args.name} queued")
            return 0

        if args.command == "tasks":
            records = store.list_durable("task")
            for record in records:
                if args.open_only and record.get("status") == "completed":
                    continue
                body = record.get("body") or {}
                objective = body.get("objective") or ""
                print(f"  {record.get('name')} ({record.get('status')}): {objective}")
            return 0

        if args.command in ("work", "block", "complete"):
            target = {"work": "working", "block": "blocked", "complete": "completed"}[args.command]
            task = Task.open(store, args.name)
            if task is None:
                print(f"no task named {args.name!r}")
                return 1
            try:
                task.advance(target)
            except TaskError as error:
                print(f"refused: {error}")
                return 1
            print(f"task {args.name} is now {task.state}")
            return 0

        if args.command == "resume":
            records = unfinished(store)
            if not records:
                print("nothing unfinished")
                return 0
            for record in records:
                body = record.get("body") or {}
                objective = body.get("objective") or ""
                print(f"  {record.get('name')} ({record.get('status')}): {objective}")
            return 0

        if args.command == "pay":
            executor = BaseExecutor() if args.live else DryRunExecutor()
            try:
                outcome = pay(store, args.name, args.amount, executor=executor)
            except RuntimeError as error:
                print(f"executor error: {error}")
                return 1
            print(f"gate: {outcome.reason}")
            if outcome.allowed:
                detail = f"payment sent ({outcome.executor})"
                if outcome.transaction:
                    detail += f" tx={outcome.transaction}"
                print(detail)
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

        if args.command == "reflect":
            report = run_reflection(
                store, since=args.since, min_hits=args.min_hits
            )
            print(
                f"scanned {report['events_scanned']} journal events, "
                f"wrote {len(report['proposals'])} proposals"
            )
            for name in report["proposals"]:
                print(f"  {name}")
            return 0

        if args.command == "proposals":
            records = pending_proposals(store)
            for record in records:
                print(f"  {record.get('name')}")
            if not records:
                print("(no pending proposals)")
            return 0

        if args.command == "accept":
            accepted = accept_proposal(store, args.name)
            if accepted is None:
                print(f"no proposal named {args.name!r}")
                return 1
            print(f"accepted {args.name}")
            return 0

        if args.command == "reject":
            if not reject_proposal(store, args.name):
                print(f"no proposal named {args.name!r}")
                return 1
            print(f"rejected {args.name}")
            return 0

        parser.error(f"unknown command {args.command!r}")
        return 2
    finally:
        store.close()
