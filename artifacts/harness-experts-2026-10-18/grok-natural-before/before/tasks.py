import argparse
import json
import sqlite3
import sys

from application import build_gateway


def main():
    parser = argparse.ArgumentParser(description="Local single-user task ledger")
    parser.add_argument("--db", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add")
    add.add_argument("title")
    commands.add_parser("list")
    done = commands.add_parser("done")
    done.add_argument("id", type=int)
    commands.add_parser("export")
    args = parser.parse_args()
    try:
        gateway = build_gateway(args.db)
        if args.command == "add":
            output = str(gateway.add(args.title))
        elif args.command == "done":
            gateway.done(args.id)
            output = None
        elif args.command == "list":
            output = json.dumps(gateway.records(), ensure_ascii=False)
        else:
            output = "\n".join(gateway.markdown())
        if output is not None and output != "":
            print(output)
    except (sqlite3.Error, ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
