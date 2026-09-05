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
from .agent.replay import replay
from .integrations import register_with_virtuals
from .integrations.virtuals import dispatch_to_virtuals
from .memory.agreement import Agreement, AgreementError
from .memory.doctor import run_doctor
from .memory.keepsake import export_keepsake, import_keepsake
from .memory.handoff import handoff
from .memory.lessons import SEVERITIES, learn, lessons, resolve
from .memory.links import link
from .memory.tasks import Task, TaskError, unfinished
from .payments import BaseExecutor, DryRunExecutor, pay
from .memory.reflection import accept as accept_proposal
from .memory.reflection import pending as pending_proposals
from .memory.reflection import reflect as run_reflection
from .memory.reflection import reject as reject_proposal
from .memory.revision import blast_radius, is_suspect, reconsider, revise, suspect_reasons
from .memory.seal import seal_journal as seal_journal_command
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

    replay_cmd = sub.add_parser("replay", help="show the causal chain for a subject")
    replay_cmd.add_argument("subject")

    register = sub.add_parser("register", help="record this agent's identity")
    register.add_argument("--as", dest="name", default="mnemos")
    register.add_argument("--live", action="store_true", help="create the agent on Virtuals")
    register.add_argument("--agent-id", dest="agent_id", default=None, help="record a console-created agent id")

    dispatch = sub.add_parser("dispatch", help="send a task to the remembered Virtuals agent")
    dispatch.add_argument("task", nargs="+")

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

    learn_cmd = sub.add_parser("learn", help="record a lesson from a failure")
    learn_cmd.add_argument("text", nargs="+")
    learn_cmd.add_argument("--severity", default="medium", choices=SEVERITIES)

    lessons_cmd = sub.add_parser("lessons", help="list every remembered lesson")

    resolve_cmd = sub.add_parser("resolve", help="mark a lesson resolved, clearing its veto")
    resolve_cmd.add_argument("name")

    link_cmd = sub.add_parser("link", help="link two durable entities both ways")
    link_cmd.add_argument("category_a")
    link_cmd.add_argument("name_a")
    link_cmd.add_argument("category_b")
    link_cmd.add_argument("name_b")

    doctor = sub.add_parser("doctor", help="prove memory is load-bearing")

    revise_cmd = sub.add_parser("revise", help="correct a fact and taint what depended on it")
    revise_cmd.add_argument("category")
    revise_cmd.add_argument("name")
    revise_cmd.add_argument("value")
    revise_cmd.add_argument("--reason", default=None)

    blast = sub.add_parser("blast", help="show the blast radius of a fact")
    blast.add_argument("category")
    blast.add_argument("name")

    reconsider_cmd = sub.add_parser("reconsider", help="review a suspect entity")
    reconsider_cmd.add_argument("category")
    reconsider_cmd.add_argument("name")
    reconsider_cmd.add_argument("--valid", action="store_true")
    reconsider_cmd.add_argument("--invalid", action="store_true")
    reconsider_cmd.add_argument("--reason", default=None)

    suspect_cmd = sub.add_parser("suspect", help="list suspect entities")

    seal_cmd = sub.add_parser(
        "seal", help="fold the journal into a tamper-evident chain head"
    )

    mcp_cmd = sub.add_parser(
        "mcp", help="run the MCP server so any MCP client gets the memory tools"
    )
    mcp_cmd.add_argument(
        "--http",
        action="store_true",
        help="serve streamable HTTP on PORT (default 8000) instead of stdio",
    )

    pay = sub.add_parser("pay", help="pay against a remembered agreement")
    pay.add_argument("name")
    pay.add_argument("amount", type=float)
    pay.add_argument("--live", action="store_true", help="submit a real tx")
    pay.add_argument(
        "--network",
        choices=("sepolia", "mainnet"),
        default="sepolia",
        help="which Base network (default: sepolia)",
    )

    keepsake = sub.add_parser("keepsake", help="portable memory packs")
    keepsake_sub = keepsake.add_subparsers(dest="keepsake_command", required=True)

    export = keepsake_sub.add_parser("export", help="write memory to a .mne pack")
    export.add_argument("path")

    import_ = keepsake_sub.add_parser("import", help="merge a .mne pack into memory")
    import_.add_argument("path")

    handoff_cmd = sub.add_parser("handoff", help="give another agent your memory")
    handoff_cmd.add_argument("path")
    handoff_cmd.add_argument("--to", dest="recipient", default=None)

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
            store.record_event(
                evaluated={"category": args.category, "name": name},
                acted=[f"remembered {args.category} {name}"],
            )
            print(f"remembered {args.category} {name}")
            return 0

        if args.command == "ask":
            question = " ".join(args.question)
            answer = RecallEngine(store).ask(question)
            store.record_event(
                evaluated={
                    "question": question,
                    "found": answer.found_anything,
                    "sources": list(answer.sources),
                },
                acted=[f"asked: {question}"],
            )
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

        if args.command == "replay":
            print(replay(store, args.subject).text)
            return 0

        if args.command == "register":
            try:
                result = register_with_virtuals(
                    store, name=args.name, live=args.live, agent_id=args.agent_id
                )
            except RuntimeError as error:
                print(f"registration failed: {error}")
                return 1
            print(f"registration: {result.note}")
            return 0

        if args.command == "dispatch":
            task = " ".join(args.task)
            try:
                result = dispatch_to_virtuals(store, task)
            except RuntimeError as error:
                print(f"dispatch failed: {error}")
                return 1
            print(f"dispatch: {result}")
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

        if args.command == "learn":
            text = " ".join(args.text)
            learn(store, text, severity=args.severity)
            print(f"learned ({args.severity})")
            return 0

        if args.command == "lessons":
            records = lessons(store)
            for record in records:
                body = record.get("body") or {}
                print(f"  ({body.get('severity', 'medium')}) {body.get('value', '')}")
            if not records:
                print("(no lessons)")
            return 0

        if args.command == "resolve":
            record = resolve(store, args.name)
            if record is None:
                print(f"no lesson named {args.name!r}")
                return 1
            print(f"resolved lesson {args.name}")
            return 0

        if args.command == "link":
            try:
                result = link(
                    store,
                    args.category_a,
                    args.name_a,
                    args.category_b,
                    args.name_b,
                )
            except ValueError as error:
                print(f"refused: {error}")
                return 1
            print(f"linked {result['linked'][0]} <-> {result['linked'][1]}")
            return 0

        if args.command == "doctor":
            report = run_doctor()
            for name, ok, detail in report.checks:
                mark = "ok" if ok else "FAIL"
                print(f"  [{mark}] {name}: {detail}")
            print("memory is load-bearing" if report.healthy else "memory is broken")
            return 0 if report.healthy else 1

        if args.command == "revise":
            try:
                result = revise(
                    store, args.category, args.name, args.value, reason=args.reason
                )
            except ValueError as error:
                print(f"refused: {error}")
                return 1
            print(
                f"revised {result['fact']}: {result['from']} -> {result['to']}"
            )
            print(
                f"blast radius: {result['decisions_affected']} decisions, "
                f"{result['payments_affected']} payments"
            )
            for item in result["newly_suspect"]:
                print(f"  suspect: {item}")
            if not result["newly_suspect"]:
                print("  nothing depended on this fact")
            return 0

        if args.command == "blast":
            radius = blast_radius(store, f"{args.category}:{args.name}")
            print(
                f"blast radius of {radius['fact']}: {radius['decisions']} decisions, "
                f"{radius['agreements']} agreements, {radius['tasks']} tasks, "
                f"{radius['payments']} payments"
            )
            return 0

        if args.command == "reconsider":
            decision = "valid" if args.valid else "invalid" if args.invalid else None
            if decision is None:
                print("pass --valid or --invalid")
                return 1
            try:
                result = reconsider(
                    store, args.category, args.name, decision, reason=args.reason
                )
            except ValueError as error:
                print(f"refused: {error}")
                return 1
            state = "gate reopened" if result["reopened"] else "still suspect"
            print(f"reconsidered {args.category} {args.name}: {decision}, {state}")
            return 0

        if args.command == "suspect":
            found = False
            for category in ("agreement", "task"):
                for record in store.list_durable(category):
                    name = record.get("name")
                    if is_suspect(store, category, name):
                        found = True
                        print(
                            f"  {category} {name}: "
                            f"{', '.join(suspect_reasons(store, category, name))}"
                        )
            if not found:
                print("(nothing suspect)")
            return 0

        if args.command == "seal":
            result = seal_journal_command(store)
            print(
                f"sealed {result['count']} journal events, head {result['head'][:16]}"
            )
            return 0

        if args.command == "mcp":
            import os

            from .mcp import DB_ENV, run_server

            os.environ[DB_ENV] = args.db
            run_server(http=args.http)
            return 0

        if args.command == "pay":
            executor = (
                BaseExecutor(network=args.network) if args.live else DryRunExecutor()
            )
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

        if args.command == "handoff":
            summary = handoff(store, args.path, recipient=args.recipient)
            who = summary["recipient"] or "another agent"
            print(f"handed {summary['path']} to {who}")
            print(f"recipient runs: {summary['import_command']}")
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
