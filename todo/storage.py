"""JSON 文件存储层。"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Task

DEFAULT_PATH = Path.home() / ".todo-cli.json"


class Storage:
    """把任务列表持久化到一个 JSON 文件。"""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_PATH

    def load(self) -> list[Task]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [Task.from_dict(item) for item in data]

    def save(self, tasks: list[Task]) -> None:
        self.path.write_text(
            json.dumps([t.to_dict() for t in tasks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, task: Task) -> None:
        tasks = self.load()
        tasks.append(task)
        self.save(tasks)

    def mark_done(self, task_id: str) -> bool:
        tasks = self.load()
        for t in tasks:
            if t.id == task_id:
                t.done = True
                self.save(tasks)
                return True
        return False
