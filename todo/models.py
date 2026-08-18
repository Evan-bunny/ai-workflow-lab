"""Task 数据模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Task:
    """一条待办任务。"""

    title: str
    done: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "done": self.done}

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(id=data["id"], title=data["title"], done=data.get("done", False))
