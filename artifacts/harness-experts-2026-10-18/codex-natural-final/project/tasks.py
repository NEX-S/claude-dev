import argparse
from contextlib import closing
import json
import sqlite3
import sys


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
        if args.command == "add" and not args.title.strip():
            raise ValueError("title must not be blank")
        with closing(sqlite3.connect(args.db)) as database:
            with database:
                database.execute(
                    "CREATE TABLE IF NOT EXISTS tasks ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
                    "done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)))"
                )
                if args.command == "add":
                    output = str(database.execute(
                        "INSERT INTO tasks (title) VALUES (?)", (args.title,)
                    ).lastrowid)
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
                        output = json.dumps([
                            {"id": task_id, "title": title, "done": bool(done)}
                            for task_id, title, done in rows
                        ], ensure_ascii=False)
                    else:
                        output = "\n".join(
                            f"- [{'x' if done else ' '}] {title}"
                            for _, title, done in rows
                        )
        # A successful write must commit before its result reaches stdout.
        if output is not None and output != "":
            print(output)
    except (sqlite3.Error, ValueError, OverflowError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
