"""delete 命令与 Storage.delete 测试。"""

from __future__ import annotations

from todo.cli import main
from todo.models import Task
from todo.storage import Storage


def test_storage_delete_existing(tmp_path) -> None:
    storage = Storage(path=tmp_path / "todo.json")
    task = Task(title="写周报")
    storage.add(task)
    assert storage.delete(task.id) is True
    assert storage.load() == []


def test_storage_delete_missing_id(tmp_path) -> None:
    storage = Storage(path=tmp_path / "todo.json")
    storage.add(Task(title="买牛奶"))
    assert storage.delete("no-such-id") is False
    assert len(storage.load()) == 1


def test_storage_delete_only_removes_target(tmp_path) -> None:
    storage = Storage(path=tmp_path / "todo.json")
    keep = Task(title="保留")
    drop = Task(title="删除")
    storage.add(keep)
    storage.add(drop)
    storage.delete(drop.id)
    tasks = storage.load()
    assert len(tasks) == 1
    assert tasks[0].id == keep.id


def test_cli_delete(tmp_path, capsys, monkeypatch) -> None:
    path = tmp_path / "todo.json"
    monkeypatch.setattr("todo.cli.Storage", lambda: Storage(path=path))
    assert main(["add", "周报"]) == 0
    task_id = Storage(path=path).load()[0].id
    assert main(["delete", task_id]) == 0
    assert Storage(path=path).load() == []


def test_cli_delete_missing_id(tmp_path, capsys, monkeypatch) -> None:
    path = tmp_path / "todo.json"
    monkeypatch.setattr("todo.cli.Storage", lambda: Storage(path=path))
    assert main(["delete", "no-such-id"]) == 1
    assert "找不到任务" in capsys.readouterr().err
