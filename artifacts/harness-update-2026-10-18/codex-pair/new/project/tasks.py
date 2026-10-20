#!/usr/bin/env python3
"""A persistent, local task ledger using only the Python standard library."""

import argparse
from contextlib import closing
import json
import sqlite3
import sys


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="SQLite database file")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="Create a task")
    add.add_argument("title")
    commands.add_parser("list", help="List tasks as JSON")
    done = commands.add_parser("done", help="Mark a task as done")
    done.add_argument("id", type=int)
    commands.add_parser("export", help="Export tasks as Markdown")
    return parser.parse_args()


def run(args):
    if args.command == "add" and not args.title.strip():
        raise ValueError("title must not be blank")

    with closing(sqlite3.connect(args.db)) as database:
        # Leave the transaction before returning output, so commit failures cannot
        # produce a successful-looking result.
        with database:
            database.execute(
                "CREATE TABLE IF NOT EXISTS tasks ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "title TEXT NOT NULL, "
                "done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)))"
            )
            if args.command == "add":
                cursor = database.execute(
                    "INSERT INTO tasks (title) VALUES (?)", (args.title,)
                )
                output = str(cursor.lastrowid)
            elif args.command == "done":
                cursor = database.execute(
                    "UPDATE tasks SET done = 1 WHERE id = ?", (args.id,)
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"task ID {args.id} does not exist")
                output = None
            else:
                rows = database.execute(
                    "SELECT id, title, done FROM tasks ORDER BY id"
                ).fetchall()
                if args.command == "list":
                    output = json.dumps(
                        [
                            {"id": task_id, "title": title, "done": bool(done)}
                            for task_id, title, done in rows
                        ],
                        ensure_ascii=False,
                    )
                else:
                    output = "\n".join(
                        f"- [{'x' if done else ' '}] {title}"
                        for _, title, done in rows
                    )
    return output


def main():
    args = parse_args()
    try:
        output = run(args)
        if output is not None and output != "":
            print(output)
    except (sqlite3.Error, ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
