"""基础测试：models 与 storage。"""

from __future__ import annotations

from todo.models import Task
from todo.storage import Storage


def test_task_roundtrip() -> None:
    task = Task(title="写周报")
    restored = Task.from_dict(task.to_dict())
    assert restored.id == task.id
    assert restored.title == "写周报"
    assert restored.done is False


def test_storage_add_and_load(tmp_path) -> None:
    storage = Storage(path=tmp_path / "todo.json")
    storage.add(Task(title="买牛奶"))
    tasks = storage.load()
    assert len(tasks) == 1
    assert tasks[0].title == "买牛奶"


def test_storage_mark_done(tmp_path) -> None:
    storage = Storage(path=tmp_path / "todo.json")
    task = Task(title="跑步")
    storage.add(task)
    assert storage.mark_done(task.id) is True
    assert storage.load()[0].done is True
    assert storage.mark_done("不存在") is False


def test_storage_empty(tmp_path) -> None:
    storage = Storage(path=tmp_path / "todo.json")
    assert storage.load() == []
