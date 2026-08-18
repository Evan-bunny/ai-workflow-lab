"""重复任务（--repeat）功能测试。"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from todo import cli
from todo.models import Task
from todo.storage import Storage

TODAY = date.today()
DUE = date(2026, 8, 20)


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

def test_task_repeat_roundtrip() -> None:
    task = Task(title="晨跑", repeat="daily")
    restored = Task.from_dict(task.to_dict())
    assert restored.repeat == "daily"


def test_task_from_legacy_dict_without_repeat() -> None:
    legacy = {"id": "abc123", "title": "旧任务", "done": False}
    task = Task.from_dict(legacy)
    assert task.repeat is None


def test_task_from_dict_invalid_repeat_tolerated() -> None:
    task = Task.from_dict({"id": "x", "title": "t", "repeat": "每小时"})
    assert task.repeat is None


# ---------- add --repeat ----------

def test_add_with_repeat(patch_storage) -> None:
    path = patch_storage([])
    assert cli.main(["add", "晨跑", "--repeat", "daily"]) == 0
    tasks = Storage(path=path).load()
    assert tasks[0].repeat == "daily"


def test_add_without_repeat_unchanged(patch_storage) -> None:
    path = patch_storage([])
    assert cli.main(["add", "买牛奶"]) == 0
    assert Storage(path=path).load()[0].repeat is None


def test_add_with_invalid_repeat_rejected(patch_storage, capsys) -> None:
    patch_storage([])
    # argparse choices 校验失败会以退出码 2 终止
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["add", "晨跑", "--repeat", "monthly"])
    assert excinfo.value.code == 2


# ---------- done 生成下一条任务 ----------

def test_done_daily_with_due_spawns_next_day(patch_storage) -> None:
    task = Task(title="晨跑", due=DUE, repeat="daily")
    path = patch_storage([task])
    assert cli.main(["done", task.id]) == 0
    tasks = Storage(path=path).load()
    assert len(tasks) == 2
    assert tasks[0].done is True
    nxt = tasks[1]
    assert nxt.done is False
    assert nxt.due == DUE + timedelta(days=1)
    assert nxt.repeat == "daily"
    assert nxt.id != task.id


def test_done_weekly_with_due_spawns_next_week(patch_storage) -> None:
    task = Task(title="周报", due=DUE, repeat="weekly")
    path = patch_storage([task])
    assert cli.main(["done", task.id]) == 0
    tasks = Storage(path=path).load()
    assert tasks[1].due == DUE + timedelta(days=7)
    assert tasks[1].repeat == "weekly"


def test_done_repeat_without_due_uses_today_as_base(patch_storage) -> None:
    task = Task(title="喝水", repeat="daily")
    path = patch_storage([task])
    assert cli.main(["done", task.id]) == 0
    tasks = Storage(path=path).load()
    assert tasks[1].due == TODAY + timedelta(days=1)


def test_done_repeat_keeps_title_priority_tags(patch_storage) -> None:
    task = Task(title="晨跑", priority="high", tags=["健康", "运动"], repeat="weekly")
    path = patch_storage([task])
    assert cli.main(["done", task.id]) == 0
    nxt = Storage(path=path).load()[1]
    assert nxt.title == "晨跑"
    assert nxt.priority == "high"
    assert nxt.tags == ["健康", "运动"]


def test_done_non_repeat_spawns_nothing(patch_storage) -> None:
    task = Task(title="一次性任务", due=DUE)
    path = patch_storage([task])
    assert cli.main(["done", task.id]) == 0
    tasks = Storage(path=path).load()
    assert len(tasks) == 1
    assert tasks[0].done is True


def test_done_twice_does_not_spawn_duplicate(patch_storage) -> None:
    """重复执行 done 不应重复生成下一条周期任务（回归测试）。"""
    task = Task(title="每日站会", repeat="daily")
    path = patch_storage([task])
    assert cli.main(["done", task.id]) == 0
    assert cli.main(["done", task.id]) == 0
    tasks = Storage(path=path).load()
    # 原始任务 + 仅一条自动生成的下一条
    assert len(tasks) == 2
    assert tasks[0].done is True
    assert tasks[1].done is False


def test_done_twice_on_completed_non_repeat_is_noop(patch_storage, capsys) -> None:
    """非周期任务重复 done 只提示已是完成状态。"""
    task = Task(title="一次性任务")
    path = patch_storage([task])
    assert cli.main(["done", task.id]) == 0
    assert cli.main(["done", task.id]) == 0
    assert "已是完成状态" in capsys.readouterr().out
    assert len(Storage(path=path).load()) == 1
