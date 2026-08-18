"""due-date 功能测试（对应 specs/001-due-date/spec.md 验收场景）。"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from todo import cli
from todo.models import Task
from todo.storage import Storage

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)


def make_storage(tmp_path: Path, tasks: list[Task]) -> Storage:
    """把给定任务直接写入临时数据文件并返回 Storage。"""
    storage = Storage(path=tmp_path / "todo.json")
    storage.save(tasks)
    return storage


@pytest.fixture
def patch_storage(tmp_path, monkeypatch):
    """把 cli 里的 Storage() 重定向到临时文件，返回 (storage_path, 写入函数)。"""

    def _setup(tasks: list[Task]) -> Path:
        path = tmp_path / "todo.json"
        Storage(path=path).save(tasks)
        monkeypatch.setattr(cli, "Storage", lambda: Storage(path=path))
        return path

    return _setup


# ---------- T002：模型序列化兼容 ----------

def test_task_due_roundtrip() -> None:
    task = Task(title="交报告", due=date(2026, 8, 20))
    restored = Task.from_dict(task.to_dict())
    assert restored.due == date(2026, 8, 20)


def test_task_from_legacy_dict_without_due() -> None:
    legacy = {"id": "abc123", "title": "旧任务", "done": False}
    task = Task.from_dict(legacy)
    assert task.due is None


def test_task_from_dict_invalid_due_tolerated() -> None:
    task = Task.from_dict({"id": "x", "title": "t", "due": "不是日期"})
    assert task.due is None


# ---------- US1：add --due ----------

def test_add_with_due(patch_storage) -> None:
    path = patch_storage([])
    assert cli.main(["add", "交报告", "--due", "2026-08-20"]) == 0
    tasks = Storage(path=path).load()
    assert tasks[0].due == date(2026, 8, 20)


@pytest.mark.parametrize("bad", ["2026-13-40", "明天", "20260820"])
def test_add_with_invalid_due_rejected(patch_storage, bad, capsys) -> None:
    path = patch_storage([])
    assert cli.main(["add", "交报告", "--due", bad]) != 0
    assert json.loads(path.read_text(encoding="utf-8")) == []
    assert capsys.readouterr().err != ""


def test_add_without_due_unchanged(patch_storage) -> None:
    path = patch_storage([])
    assert cli.main(["add", "买牛奶"]) == 0
    assert Storage(path=path).load()[0].due is None


# ---------- US2：list 展示与逾期标记 ----------

def test_list_marks_overdue_only_for_past_undone(patch_storage, capsys) -> None:
    patch_storage([
        Task(title="已逾期", due=YESTERDAY),
        Task(title="今天到期", due=TODAY),
        Task(title="未来到期", due=TOMORROW),
    ])
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "已逾期" in out and "!逾期" in out
    overdue_line = next(l for l in out.splitlines() if "已逾期" in l)
    today_line = next(l for l in out.splitlines() if "今天到期" in l)
    assert "!逾期" in overdue_line
    assert "!逾期" not in today_line
    assert "(截止:" in today_line


def test_list_no_overdue_mark_for_done(patch_storage, capsys) -> None:
    patch_storage([Task(title="曾逾期", done=True, due=YESTERDAY)])
    cli.main(["list"])
    out = capsys.readouterr().out
    assert "!逾期" not in out


def test_list_task_without_due_output_unchanged(patch_storage, capsys) -> None:
    task = Task(title="买牛奶")
    patch_storage([task])
    cli.main(["list"])
    out = capsys.readouterr().out
    assert out == f"[ ] {task.id}  买牛奶\n"


# ---------- US3：日期筛选 ----------

def test_list_overdue_filter(patch_storage, capsys) -> None:
    patch_storage([
        Task(title="已逾期", due=YESTERDAY),
        Task(title="已完成逾期", done=True, due=YESTERDAY),
        Task(title="未来到期", due=TOMORROW),
        Task(title="无日期"),
    ])
    cli.main(["list", "--overdue"])
    out = capsys.readouterr().out
    assert "已逾期" in out
    assert "已完成逾期" not in out
    assert "未来到期" not in out
    assert "无日期" not in out


def test_list_today_filter(patch_storage, capsys) -> None:
    patch_storage([
        Task(title="今天到期", due=TODAY),
        Task(title="已逾期", due=YESTERDAY),
        Task(title="无日期"),
    ])
    cli.main(["list", "--today"])
    out = capsys.readouterr().out
    assert "今天到期" in out
    assert "已逾期" not in out
    assert "无日期" not in out
