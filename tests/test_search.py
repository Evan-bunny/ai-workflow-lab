"""search 搜索功能测试（T3）。"""

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


def test_search_substring_match(patch_storage, capsys) -> None:
    patch_storage([
        Task(title="写周报"),
        Task(title="写日报"),
        Task(title="买牛奶"),
    ])
    assert cli.main(["search", "写"]) == 0
    out = capsys.readouterr().out
    assert "写周报" in out
    assert "写日报" in out
    assert "买牛奶" not in out


def test_search_case_insensitive(patch_storage, capsys) -> None:
    patch_storage([Task(title="Read Python Book")])
    assert cli.main(["search", "python"]) == 0
    assert "Read Python Book" in capsys.readouterr().out


def test_search_mixed_case_keyword(patch_storage, capsys) -> None:
    patch_storage([Task(title="read python book")])
    assert cli.main(["search", "PYTHON"]) == 0
    assert "read python book" in capsys.readouterr().out


def test_search_no_match_shows_empty(patch_storage, capsys) -> None:
    patch_storage([Task(title="写周报")])
    assert cli.main(["search", "不存在"]) == 0
    assert "（没有任务）" in capsys.readouterr().out


def test_search_empty_storage(patch_storage, capsys) -> None:
    patch_storage([])
    assert cli.main(["search", "任意"]) == 0
    assert "（没有任务）" in capsys.readouterr().out


def test_search_matches_done_and_undone(patch_storage, capsys) -> None:
    """搜索不区分完成状态，两者都要显示。"""
    patch_storage([
        Task(title="写周报", done=True),
        Task(title="写日报", done=False),
    ])
    assert cli.main(["search", "写"]) == 0
    out = capsys.readouterr().out
    assert "写周报" in out
    assert "写日报" in out


def test_search_output_format_like_list(patch_storage, capsys) -> None:
    """搜索结果复用 list 的展示格式（高优先级标记、截止/逾期）。"""
    yesterday = date.today() - timedelta(days=1)
    patch_storage([Task(title="紧急写周报", priority="high", due=yesterday)])
    assert cli.main(["search", "周报"]) == 0
    out = capsys.readouterr().out
    assert "[!]" in out
    assert "!逾期" in out
