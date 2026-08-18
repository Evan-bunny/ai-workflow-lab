"""命令行入口：add / list / done / search / stats / export。"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from .models import PRIORITIES, REPEATS, Task
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
    p_add.add_argument("--repeat", choices=REPEATS,
                       help="重复规则：daily 每天 / weekly 每周")

    p_list = sub.add_parser("list", help="列出所有任务")
    group = p_list.add_mutually_exclusive_group()
    group.add_argument("--overdue", action="store_true", help="只看已逾期的未完成任务")
    group.add_argument("--today", action="store_true", help="只看今天到期的未完成任务")
    group.add_argument("--tag", help="只显示含该标签的任务")

    p_done = sub.add_parser("done", help="标记任务完成")
    p_done.add_argument("id", help="任务 ID")

    p_delete = sub.add_parser("delete", help="删除任务")
    p_delete.add_argument("id", help="任务 ID")

    p_search = sub.add_parser("search", help="按标题关键词搜索任务")
    p_search.add_argument("keyword", help="搜索关键词（大小写不敏感）")

    sub.add_parser("stats", help="统计任务数量（总数/已完成/未完成/逾期未完成）")

    p_export = sub.add_parser("export", help="导出所有任务为 Markdown 文件")
    p_export.add_argument("path", help="导出文件路径（已存在时拒绝覆盖）")

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
    task = Task(title=args.title, due=due, priority=args.priority, tags=tags,
                repeat=args.repeat)
    storage.add(task)
    print(f"已添加 [{task.id}] {task.title}")
    return 0


def _format_task_line(task: Task, today: date) -> str:
    """生成单行任务展示文本，list 和 search 共用。"""
    mark = "x" if task.done else " "
    line = f"[{mark}] {task.id}  {task.title}"
    # 高优先级任务加 [!] 前缀标记
    if task.priority == "high":
        line = "[!] " + line
    if task.due is not None:
        line += f"  (截止: {task.due.isoformat()})"
        if is_overdue(task, today):
            line += " !逾期"
    return line


def _print_tasks(tasks: list[Task], today: date) -> None:
    """统一输出任务列表，空列表打印占位提示。"""
    if not tasks:
        print("（没有任务）")
        return
    for t in tasks:
        print(_format_task_line(t, today))


def _cmd_list(args: argparse.Namespace, storage: Storage) -> int:
    today = date.today()
    tasks = storage.load()

    if args.overdue:
        tasks = [t for t in tasks if is_overdue(t, today)]
    elif args.today:
        tasks = [t for t in tasks if t.due is not None and not t.done and t.due == today]
    elif args.tag:
        tasks = [t for t in tasks if args.tag in t.tags]

    _print_tasks(tasks, today)
    return 0


def _cmd_search(args: argparse.Namespace, storage: Storage) -> int:
    """标题大小写不敏感的子串匹配。"""
    keyword = args.keyword.lower()
    tasks = [t for t in storage.load() if keyword in t.title.lower()]
    _print_tasks(tasks, date.today())
    return 0


def _cmd_stats(args: argparse.Namespace, storage: Storage) -> int:
    """输出任务统计：总数、已完成、未完成、逾期未完成。"""
    today = date.today()
    tasks = storage.load()
    done = sum(1 for t in tasks if t.done)
    undone = len(tasks) - done
    overdue = sum(1 for t in tasks if is_overdue(t, today))
    print(f"总任务数: {len(tasks)}")
    print(f"已完成: {done}")
    print(f"未完成: {undone}")
    print(f"逾期未完成: {overdue}")
    return 0


def _format_export_line(task: Task) -> str:
    """生成单条任务的 Markdown 列表行，附带截止日期和标签信息。"""
    mark = "x" if task.done else " "
    line = f"- [{mark}] {task.title}"
    if task.due is not None:
        line += f"（截止: {task.due.isoformat()}）"
    if task.tags:
        line += f"（标签: {', '.join(task.tags)}）"
    return line


def _render_export_markdown(tasks: list[Task]) -> str:
    """把任务列表渲染为按未完成/已完成分组的 Markdown 文本。"""
    undone = [t for t in tasks if not t.done]
    done = [t for t in tasks if t.done]
    lines = ["# 任务导出", "", "## 未完成", ""]
    lines += [_format_export_line(t) for t in undone]
    lines += ["", "## 已完成", ""]
    lines += [_format_export_line(t) for t in done]
    lines.append("")
    return "\n".join(lines)


def _cmd_export(args: argparse.Namespace, storage: Storage) -> int:
    """导出所有任务为 Markdown 文件；目标已存在时报错并拒绝覆盖。"""
    out_path = Path(args.path)
    if out_path.exists():
        print(f"错误：文件已存在，拒绝覆盖：{out_path}", file=sys.stderr)
        return 1
    out_path.write_text(_render_export_markdown(storage.load()), encoding="utf-8")
    print(f"已导出到 {out_path}")
    return 0


def _cmd_delete(args: argparse.Namespace, storage: Storage) -> int:
    """按 ID 删除任务；ID 不存在时报错返回 1。"""
    if not storage.delete(args.id):
        print(f"找不到任务 {args.id}", file=sys.stderr)
        return 1
    print(f"已删除 {args.id}")
    return 0


def next_occurrence(task: Task, today: date) -> Task:
    """按重复规则生成下一条任务。

    daily 在基准日期上加 1 天，weekly 加 7 天；基准为原任务的截止日期，
    无截止日期则以 today 为基准。标题、优先级、标签和重复规则原样继承。
    """
    delta = timedelta(days=1 if task.repeat == "daily" else 7)
    base = task.due if task.due is not None else today
    return Task(
        title=task.title,
        due=base + delta,
        priority=task.priority,
        tags=list(task.tags),
        repeat=task.repeat,
    )


def _cmd_done(args: argparse.Namespace, storage: Storage) -> int:
    """标记完成；若任务带重复规则，同时自动生成下一条任务。"""
    task = next((t for t in storage.load() if t.id == args.id), None)
    if not storage.mark_done(args.id):
        print(f"找不到任务 {args.id}", file=sys.stderr)
        return 1
    print(f"已完成 {args.id}")
    if task is not None and task.repeat is not None:
        nxt = next_occurrence(task, date.today())
        storage.add(nxt)
        print(f"已生成下一条 [{nxt.id}] {nxt.title}（截止: {nxt.due.isoformat()}）")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    storage = Storage()

    if args.command == "add":
        return _cmd_add(args, storage)
    if args.command == "list":
        return _cmd_list(args, storage)
    if args.command == "done":
        return _cmd_done(args, storage)
    if args.command == "delete":
        return _cmd_delete(args, storage)
    if args.command == "search":
        return _cmd_search(args, storage)
    if args.command == "stats":
        return _cmd_stats(args, storage)
    if args.command == "export":
        return _cmd_export(args, storage)
    return 1  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
