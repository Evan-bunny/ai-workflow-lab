"""命令行入口：add / list / done。"""

from __future__ import annotations

import argparse
import sys

from .models import Task
from .storage import Storage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="极简 todo 命令行工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="新增任务")
    p_add.add_argument("title", help="任务标题")

    sub.add_parser("list", help="列出所有任务")

    p_done = sub.add_parser("done", help="标记任务完成")
    p_done.add_argument("id", help="任务 ID")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    storage = Storage()

    if args.command == "add":
        task = Task(title=args.title)
        storage.add(task)
        print(f"已添加 [{task.id}] {task.title}")
        return 0

    if args.command == "list":
        tasks = storage.load()
        if not tasks:
            print("（没有任务）")
            return 0
        for t in tasks:
            mark = "x" if t.done else " "
            print(f"[{mark}] {t.id}  {t.title}")
        return 0

    if args.command == "done":
        if storage.mark_done(args.id):
            print(f"已完成 {args.id}")
            return 0
        print(f"找不到任务 {args.id}", file=sys.stderr)
        return 1

    return 1  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
