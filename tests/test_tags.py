"""tags 标签功能测试（T2）。"""

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

def test_task_tags_roundtrip() -> None:
    task = Task(title="写周报", tags=["工作", "周报"])
    restored = Task.from_dict(task.to_dict())
    assert restored.tags == ["工作", "周报"]


def test_task_from_legacy_dict_without_tags() -> None:
    legacy = {"id": "abc123", "title": "旧任务", "done": False}
    task = Task.from_dict(legacy)
    assert task.tags == []


def test_task_from_dict_invalid_tags_tolerated() -> None:
    task = Task.from_dict({"id": "x", "title": "t", "tags": "notalist"})
    assert task.tags == []
    task2 = Task.from_dict({"id": "x", "title": "t", "tags": ["ok", 1, None]})
    assert task2.tags == ["ok"]


# ---------- add --tags ----------

def test_add_with_tags(patch_storage) -> None:
    path = patch_storage([])
    assert cli.main(["add", "交报告", "--tags", "工作,紧急"]) == 0
    assert Storage(path=path).load()[0].tags == ["工作", "紧急"]


def test_add_tags_strip_whitespace_and_empty(patch_storage) -> None:
    path = patch_storage([])
    assert cli.main(["add", "交报告", "--tags", " 工作 ,, 紧急 "]) == 0
    assert Storage(path=path).load()[0].tags == ["工作", "紧急"]


def test_add_without_tags_defaults_empty(patch_storage) -> None:
    path = patch_storage([])
    assert cli.main(["add", "买牛奶"]) == 0
    assert Storage(path=path).load()[0].tags == []


# ---------- list --tag ----------

def test_list_filter_by_tag(patch_storage, capsys) -> None:
    patch_storage([
        Task(title="工作任务", tags=["工作"]),
        Task(title="生活任务", tags=["生活"]),
        Task(title="双标签任务", tags=["工作", "生活"]),
        Task(title="无标签任务"),
    ])
    assert cli.main(["list", "--tag", "工作"]) == 0
    out = capsys.readouterr().out
    assert "工作任务" in out
    assert "双标签任务" in out
    assert "生活任务" not in out
    assert "无标签任务" not in out


def test_list_tag_no_match_shows_empty(patch_storage, capsys) -> None:
    patch_storage([Task(title="工作任务", tags=["工作"])])
    assert cli.main(["list", "--tag", "不存在"]) == 0
    assert "（没有任务）" in capsys.readouterr().out


def test_list_tag_mutually_exclusive_with_overdue(patch_storage) -> None:
    patch_storage([])
    with pytest.raises(SystemExit):
        cli.main(["list", "--tag", "工作", "--overdue"])
