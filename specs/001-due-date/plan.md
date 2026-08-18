# Implementation Plan: 任务截止日期（due-date）

**Branch**: `001-due-date` | **Date**: 2026-08-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-due-date/spec.md`

## Summary

为 Task 模型增加可选 `due` 字段（`YYYY-MM-DD`），`add` 支持 `--due`，`list` 展示日期并对逾期任务打标，新增 `--overdue` / `--today` 筛选。所有变更遵守章程：测试先行、存储向后兼容、零新依赖。

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: 仅标准库（argparse / json / dataclasses / datetime）；pytest（dev）
**Storage**: 本地 JSON 文件（`~/.todo-cli.json`）
**Testing**: `uv run pytest`
**Target Platform**: macOS / Linux CLI
**Constraints**: 无新运行时依赖；旧数据文件零迁移可读；逾期判定以本地自然日为粒度

## Constitution Check

| 原则 | 判定 | 说明 |
|---|---|---|
| I. 简单优先 | ✅ | 仅用标准库 `datetime.date`，无新依赖，无超前设计 |
| II. 测试先行 | ✅ | tasks 阶段先列测试任务再列实现任务 |
| III. 存储向后兼容 | ✅ | `from_dict` 用 `.get("due")`，缺失字段容错为 None |
| IV. CLI 文本协议 | ✅ | 错误走 stderr + 非零退出；正常输出走 stdout |
| V. 类型标注与文档 | ✅ | 新函数全标注 + 中文文档字符串 |

无违规项，无需 Complexity Tracking。

## Project Structure

### Documentation (this feature)

```text
specs/001-due-date/
├── spec.md              # 已完成
├── plan.md              # 本文件
└── tasks.md             # 下一阶段产出
```

### Source Code (repository root)

```text
todo/
├── models.py            # Task 增加 due: date | None
├── storage.py           # from_dict/to_dict 序列化兼容（改动很小）
└── cli.py               # add --due 参数、list 日期展示/逾期标记、--overdue/--today

tests/
├── test_basics.py       # 既有测试（不得破坏）
└── test_due_date.py     # 新增：本功能全部验收场景
```

## 设计要点

1. **模型**：`Task.due: date | None = None`；`to_dict` 序列化为 `"2026-08-20"` 字符串或 `null`；`from_dict` 用 `data.get("due")` 容错，`None` 或缺失时保持 `None` —— 满足 FR-003。
2. **校验**：`add` 中用 `datetime.date.fromisoformat()` 解析 `--due`，`ValueError` 时 `parser.error()`（自动走 stderr + exit 2）—— 满足 FR-002。
3. **逾期判定**：纯函数 `is_overdue(task, today: date) -> bool`：`task.due is not None and not task.done and task.due < today`。`today` 作为参数注入便于测试 —— 满足 FR-005。
4. **展示**：list 行格式 `[x] id  标题  (截止: 2026-08-20) !逾期`，无日期任务不渲染日期段 —— 满足 FR-004 / FR-007。
5. **筛选**：`--overdue` 与 `--today` 互斥（`add_mutually_exclusive_group`），仅作用于未完成任务 —— 满足 FR-006。

## 风险与对策

| 风险 | 对策 |
|---|---|
| `date.fromisoformat` 接受 `20260820` 这类紧凑格式，超出规格 | 解析前先正则校验 `^\d{4}-\d{2}-\d{2}$` |
| 逾期标记中文字符影响对齐 | 简单字符串拼接，不追求等宽对齐（章程 I：简单优先） |
| 旧测试因输出格式变化失败 | list 无日期任务的输出保持与现状逐字符一致 |
