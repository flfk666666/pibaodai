#!/usr/bin/env python3
"""CLI for the experimental personal character panel. No network or API calls."""

import argparse
import json
import sys

from panel_store import PanelError, Store, render, summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="角色看板：私人MD存档、续测、局部复测。评分待定留空。")
    parser.add_argument("--state-dir", required=True, help="公开仓库和Skill目录之外的私人档案目录")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--profile-id", required=True)
    for name in ("status", "render"):
        commands.add_parser(name)
    record = commands.add_parser("record")
    record.add_argument("--item", required=True)
    record.add_argument("--payload-file", required=True)
    record.add_argument("--expect-revision", required=True, type=int)
    retest = commands.add_parser("retest")
    retest.add_argument("--items", required=True, help="逗号分隔子项ID，例如A1,E1")
    retest.add_argument("--expect-revision", required=True, type=int)
    for name in ("pause", "check-evidence"):
        command = commands.add_parser(name)
        command.add_argument("--expect-revision", required=True, type=int)
    args = parser.parse_args(argv)
    try:
        store = Store(args.state_dir)
        if args.command == "init":
            state = store.init(args.profile_id)
        elif args.command == "record":
            with open(args.payload_file, encoding="utf-8-sig") as handle:
                payload = json.load(handle)
            state = store.record(args.item, payload, args.expect_revision)
        elif args.command == "retest":
            state = store.retest([item.strip() for item in args.items.split(",")], args.expect_revision)
        elif args.command == "pause":
            state = store.pause(args.expect_revision)
        elif args.command == "check-evidence":
            state = store.check_evidence(args.expect_revision)
        else:
            state = store.read()
        if args.command == "render":
            print(render(state), end="")
        else:
            print(json.dumps({"ok": True, "revision": state["revision"], "state": state,
                              "summary": summary(state)}, ensure_ascii=False, allow_nan=False))
        return 0
    except (PanelError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
