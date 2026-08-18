"""Task 数据模型。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date


PRIORITIES = ("high", "medium", "low")


@dataclass
class Task:
    """一条待办任务。

    due 为可选截止日期，为 None 表示无日期；priority 为优先级，
    默认 medium；tags 为标签列表。三者都需兼容缺失字段的旧版数据。
    """

    title: str
    done: bool = False
    due: date | None = None
    priority: str = "medium"
    tags: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "done": self.done,
            "due": self.due.isoformat() if self.due else None,
            "priority": self.priority,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        # 旧版数据没有 due / priority 字段；非法值一律容错为默认值，保证向后兼容
        raw_due = data.get("due")
        due: date | None = None
        if isinstance(raw_due, str):
            try:
                due = date.fromisoformat(raw_due)
            except ValueError:
                due = None
        raw_priority = data.get("priority")
        priority = raw_priority if raw_priority in PRIORITIES else "medium"
        # 旧版数据没有 tags 字段；非列表或含非字符串元素一律容错为空列表
        raw_tags = data.get("tags")
        tags = [t for t in raw_tags if isinstance(t, str)] if isinstance(raw_tags, list) else []
        return cls(
            id=data["id"],
            title=data["title"],
            done=data.get("done", False),
            due=due,
            priority=priority,
            tags=tags,
        )
