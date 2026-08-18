"""stats 统计功能测试（T4）。"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from todo import cli
from todo.models import Task
from todo.storage import Storage


@pytest.fixture
def patch_storage(tmp_path, monkeypatch):
    """把 cli 里的 Storage() 重定向到临时文件，返回 (storage_path, 写入函数)。"""

    def _setup(tasks: list[Task]) -> Path:
        path = tmp_path / "todo.json"
        Storage(path=path).save(tasks)
        monkeypatch.setattr(cli, "Storage", lambda: Storage(path=path))
        return path

    return _setup


def test_stats_empty_storage(patch_storage, capsys) -> None:
    patch_storage([])
    assert cli.main(["stats"]) == 0
    out = capsys.readouterr().out
    assert "总任务数: 0" in out
    assert "已完成: 0" in out
    assert "未完成: 0" in out
    assert "逾期未完成: 0" in out


def test_stats_counts_done_and_undone(patch_storage, capsys) -> None:
    patch_storage([
        Task(title="任务一", done=True),
        Task(title="任务二", done=False),
        Task(title="任务三", done=False),
    ])
    assert cli.main(["stats"]) == 0
    out = capsys.readouterr().out
    assert "总任务数: 3" in out
    assert "已完成: 1" in out
    assert "未完成: 2" in out


def test_stats_overdue_counts_only_undone(patch_storage, capsys) -> None:
    """逾期只统计未完成任务：已完成逾期任务、今天到期的都不算逾期。"""
    yesterday = date.today() - timedelta(days=1)
    tomorrow = date.today() + timedelta(days=1)
    patch_storage([
        Task(title="逾期未完成", due=yesterday),
        Task(title="逾期已完成", due=yesterday, done=True),
        Task(title="今天到期", due=date.today()),
        Task(title="明天到期", due=tomorrow),
        Task(title="无截止日期"),
    ])
    assert cli.main(["stats"]) == 0
    out = capsys.readouterr().out
    assert "总任务数: 5" in out
    assert "已完成: 1" in out
    assert "未完成: 4" in out
    assert "逾期未完成: 1" in out
