"""命令行入口：add / list / done。"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date

from .models import PRIORITIES, Task
from .storage import Storage

# 严格限定 YYYY-MM-DD，避免 fromisoformat 接受 20260820 这类紧凑格式
_DUE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_due(raw: str) -> date:
    """解析 --due 参数，非法输入抛出 ValueError 由调用方转为 CLI 错误。"""
    if not _DUE_PATTERN.match(raw):
        raise ValueError(f"日期格式必须是 YYYY-MM-DD，收到：{raw}")
    return date.fromisoformat(raw)


def is_overdue(task: Task, today: date) -> bool:
    """未完成且截止日期早于今天才算逾期；今天到期不算逾期。"""
    return task.due is not None and not task.done and task.due < today


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="极简 todo 命令行工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="新增任务")
    p_add.add_argument("title", help="任务标题")
    p_add.add_argument("--due", help="截止日期，格式 YYYY-MM-DD")
    p_add.add_argument("--priority", choices=PRIORITIES, default="medium",
                       help="优先级，默认 medium")
    p_add.add_argument("--tags", help="标签，逗号分隔，如 a,b,c")

    p_list = sub.add_parser("list", help="列出所有任务")
    group = p_list.add_mutually_exclusive_group()
    group.add_argument("--overdue", action="store_true", help="只看已逾期的未完成任务")
    group.add_argument("--today", action="store_true", help="只看今天到期的未完成任务")
    group.add_argument("--tag", help="只显示含该标签的任务")

    p_done = sub.add_parser("done", help="标记任务完成")
    p_done.add_argument("id", help="任务 ID")

    return parser


def _cmd_add(args: argparse.Namespace, storage: Storage) -> int:
    due: date | None = None
    if args.due is not None:
        try:
            due = parse_due(args.due)
        except ValueError as e:
            print(f"错误：{e}", file=sys.stderr)
            return 2
    tags: list[str] = []
    if args.tags:
        # 逗号分隔，去掉空白并过滤空标签
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    task = Task(title=args.title, due=due, priority=args.priority, tags=tags)
    storage.add(task)
    print(f"已添加 [{task.id}] {task.title}")
    return 0


def _cmd_list(args: argparse.Namespace, storage: Storage) -> int:
    today = date.today()
    tasks = storage.load()

    if args.overdue:
        tasks = [t for t in tasks if is_overdue(t, today)]
    elif args.today:
        tasks = [t for t in tasks if t.due is not None and not t.done and t.due == today]
    elif args.tag:
        tasks = [t for t in tasks if args.tag in t.tags]

    if not tasks:
        print("（没有任务）")
        return 0
    for t in tasks:
        mark = "x" if t.done else " "
        line = f"[{mark}] {t.id}  {t.title}"
        # 高优先级任务加 [!] 前缀标记
        if t.priority == "high":
            line = "[!] " + line
        if t.due is not None:
            line += f"  (截止: {t.due.isoformat()})"
            if is_overdue(t, today):
                line += " !逾期"
        print(line)
    return 0


def _cmd_done(args: argparse.Namespace, storage: Storage) -> int:
    if storage.mark_done(args.id):
        print(f"已完成 {args.id}")
        return 0
    print(f"找不到任务 {args.id}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    storage = Storage()

    if args.command == "add":
        return _cmd_add(args, storage)
    if args.command == "list":
        return _cmd_list(args, storage)
    if args.command == "done":
        return _cmd_done(args, storage)
    return 1  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
