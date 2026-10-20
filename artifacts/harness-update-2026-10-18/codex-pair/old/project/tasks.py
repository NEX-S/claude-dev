#!/usr/bin/env python3
"""A local, single-user task ledger backed by SQLite."""

import argparse
from contextlib import closing
import json
import sqlite3
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="本地单人任务账本")
    parser.add_argument("--db", required=True, help="SQLite 数据库路径")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="创建待办")
    add.add_argument("title", metavar="TITLE")
    commands.add_parser("list", help="按 ID 输出 JSON")
    done = commands.add_parser("done", help="标记完成")
    done.add_argument("id", type=int, metavar="ID")
    commands.add_parser("export", help="输出 Markdown")
    return parser.parse_args()


def execute(args):
    if args.command == "add" and not args.title.strip():
        raise ValueError("标题不能是空白")

    # Produce output only after the transaction has committed successfully.
    with closing(sqlite3.connect(args.db)) as connection:
        with connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS tasks ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "title TEXT NOT NULL, "
                "done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)))"
            )
            if args.command == "add":
                cursor = connection.execute(
                    "INSERT INTO tasks (title) VALUES (?)", (args.title,)
                )
                output = str(cursor.lastrowid) + "\n"
            elif args.command == "done":
                cursor = connection.execute(
                    "UPDATE tasks SET done = 1 WHERE id = ?", (args.id,)
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"任务 ID {args.id} 不存在")
                output = ""
            else:
                rows = connection.execute(
                    "SELECT id, title, done FROM tasks ORDER BY id"
                ).fetchall()
                if args.command == "list":
                    output = json.dumps(
                        [
                            {"id": task_id, "title": title, "done": bool(done)}
                            for task_id, title, done in rows
                        ],
                        ensure_ascii=False,
                    ) + "\n"
                else:
                    output = "".join(
                        f"- [{'x' if done else ' '}] {title}\n"
                        for _, title, done in rows
                    )
    return output


def main():
    args = parse_args()
    try:
        output = execute(args)
    except (ValueError, sqlite3.Error, OverflowError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
