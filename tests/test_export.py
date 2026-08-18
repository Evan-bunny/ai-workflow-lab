"""export 导出 Markdown 功能测试。"""

from __future__ import annotations

from datetime import date
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


def test_export_writes_markdown_file(patch_storage, tmp_path) -> None:
    """正常导出：返回 0，生成包含任务标题的 Markdown 文件。"""
    patch_storage([Task(title="写周报")])
    out_path = tmp_path / "export.md"
    assert cli.main(["export", str(out_path)]) == 0
    content = out_path.read_text(encoding="utf-8")
    assert "写周报" in content


def test_export_groups_undone_and_done(patch_storage, tmp_path) -> None:
    """导出内容按未完成/已完成分组，且各自出现在对应分组标题之后。"""
    patch_storage([
        Task(title="未完成任务", done=False),
        Task(title="已完成任务", done=True),
    ])
    out_path = tmp_path / "export.md"
    assert cli.main(["export", str(out_path)]) == 0
    content = out_path.read_text(encoding="utf-8")
    undone_pos = content.index("未完成")
    done_pos = content.index("已完成", undone_pos)
    # 分组标题存在且未完成在前
    assert undone_pos < done_pos
    # 各任务落在自己的分组区间内
    assert undone_pos < content.index("未完成任务") < done_pos
    assert content.index("已完成任务") > done_pos


def test_export_includes_due_and_tags(patch_storage, tmp_path) -> None:
    """导出条目包含截止日期和标签信息。"""
    patch_storage([
        Task(title="带信息任务", due=date(2026, 9, 1), tags=["工作", "紧急"]),
    ])
    out_path = tmp_path / "export.md"
    assert cli.main(["export", str(out_path)]) == 0
    content = out_path.read_text(encoding="utf-8")
    assert "2026-09-01" in content
    assert "工作" in content
    assert "紧急" in content


def test_export_refuses_to_overwrite(patch_storage, tmp_path, capsys) -> None:
    """目标文件已存在时拒绝覆盖：返回非零码、stderr 报错、原文件内容不变。"""
    patch_storage([Task(title="新任务")])
    out_path = tmp_path / "export.md"
    out_path.write_text("原有内容", encoding="utf-8")
    assert cli.main(["export", str(out_path)]) == 1
    err = capsys.readouterr().err
    assert "已存在" in err
    assert out_path.read_text(encoding="utf-8") == "原有内容"


def test_export_empty_storage(patch_storage, tmp_path) -> None:
    """空存储也能导出：两个分组标题都在，但不包含任何任务条目。"""
    patch_storage([])
    out_path = tmp_path / "export.md"
    assert cli.main(["export", str(out_path)]) == 0
    content = out_path.read_text(encoding="utf-8")
    assert "未完成" in content
    assert "已完成" in content
    assert "- [" not in content
