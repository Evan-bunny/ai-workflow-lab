"""priority 优先级功能测试（T1）。"""

from __future__ import annotations

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


# ---------- 模型序列化兼容 ----------

def test_task_priority_roundtrip() -> None:
    task = Task(title="写周报", priority="high")
    restored = Task.from_dict(task.to_dict())
    assert restored.priority == "high"


def test_task_from_legacy_dict_without_priority() -> None:
    legacy = {"id": "abc123", "title": "旧任务", "done": False}
    task = Task.from_dict(legacy)
    assert task.priority == "medium"


def test_task_from_dict_invalid_priority_tolerated() -> None:
    task = Task.from_dict({"id": "x", "title": "t", "priority": "urgent"})
    assert task.priority == "medium"


# ---------- add --priority ----------

def test_add_with_priority_high(patch_storage) -> None:
    path = patch_storage([])
    assert cli.main(["add", "交报告", "--priority", "high"]) == 0
    assert Storage(path=path).load()[0].priority == "high"


def test_add_without_priority_defaults_medium(patch_storage) -> None:
    path = patch_storage([])
    assert cli.main(["add", "买牛奶"]) == 0
    assert Storage(path=path).load()[0].priority == "medium"


def test_add_with_invalid_priority_rejected(patch_storage) -> None:
    patch_storage([])
    with pytest.raises(SystemExit):
        cli.main(["add", "交报告", "--priority", "urgent"])


# ---------- list [!] 前缀标记 ----------

def test_list_marks_high_priority(patch_storage, capsys) -> None:
    patch_storage([
        Task(title="紧急任务", priority="high"),
        Task(title="普通任务", priority="medium"),
        Task(title="低优先级", priority="low"),
    ])
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out
    high_line = next(l for l in out.splitlines() if "紧急任务" in l)
    medium_line = next(l for l in out.splitlines() if "普通任务" in l)
    low_line = next(l for l in out.splitlines() if "低优先级" in l)
    assert high_line.startswith("[!] ")
    assert "[!]" not in medium_line
    assert "[!]" not in low_line
