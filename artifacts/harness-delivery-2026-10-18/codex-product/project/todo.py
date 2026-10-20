#!/usr/bin/env python3
"""一个使用 JSON 文件保存任务的本地待办工具。"""

import argparse
import json
from pathlib import Path
import sys


DATA_FILE = Path(__file__).resolve().with_name("tasks.json")


def load_tasks():
    if not DATA_FILE.exists():
        return []
    tasks = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(tasks, list) or any(
        not isinstance(task, dict)
        or type(task.get("id")) is not int
        or not isinstance(task.get("title"), str)
        or type(task.get("done")) is not bool
        for task in tasks
    ):
        raise ValueError("任务文件格式不正确")
    return tasks


def save_tasks(tasks):
    # 先写临时文件，再替换，避免写入中断时破坏已有任务。
    temporary = DATA_FILE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(DATA_FILE)


def main():
    parser = argparse.ArgumentParser(description="本地待办工具：添加、列出和完成任务")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="添加任务")
    add.add_argument("title", help="任务内容，含空格时请加引号")
    commands.add_parser("list", help="列出全部任务")
    done = commands.add_parser("done", help="标记任务完成")
    done.add_argument("id", type=int, help="任务编号")
    args = parser.parse_args()

    if args.command == "add" and not args.title.strip():
        parser.error("任务内容不能为空")

    try:
        tasks = load_tasks()
        if args.command == "add":
            task = {"id": len(tasks) + 1, "title": args.title.strip(), "done": False}
            tasks.append(task)
            save_tasks(tasks)
            print(f"已添加 #{task['id']}：{task['title']}")
        elif args.command == "list":
            if not tasks:
                print("暂无任务。使用 add 添加一个任务。")
            for task in tasks:
                status = "x" if task["done"] else " "
                print(f"[{status}] {task['id']}. {task['title']}")
        else:
            task = next((task for task in tasks if task["id"] == args.id), None)
            if task is None:
                print(f"错误：找不到任务 #{args.id}", file=sys.stderr)
                return 1
            if task["done"]:
                print(f"任务 #{args.id} 已经完成。")
            else:
                task["done"] = True
                save_tasks(tasks)
                print(f"已完成 #{args.id}：{task['title']}")
    except (OSError, ValueError) as error:
        print(f"错误：无法读取或保存任务：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
