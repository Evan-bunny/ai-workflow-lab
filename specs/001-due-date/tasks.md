# Tasks: 任务截止日期（due-date）

**Input**: Design documents from `/specs/001-due-date/`
**Prerequisites**: plan.md ✅, spec.md ✅

**Tests**: 本功能遵循章程原则 II（测试先行），测试任务先于实现任务。

**Organization**: 按用户故事分组，每个故事可独立实现与验证。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无依赖）
- **[Story]**: 所属用户故事（US1/US2/US3）

---

## Phase 1: 基础（阻塞所有故事）

- [ ] T001 在 `todo/models.py` 的 `Task` 中增加 `due: date | None = None` 字段，更新 `to_dict`（ISO 字符串或 null）与 `from_dict`（`data.get("due")` 容错，非法/缺失均归一为 None）
- [ ] T002 在 `tests/test_due_date.py` 新建测试文件：Task 带日期的序列化往返；旧格式（无 due 字段）字典反序列化不报错且 due 为 None（FR-003）

**Checkpoint**: `uv run pytest` 全绿（含既有 4 个测试）

---

## Phase 2: User Story 1 - 创建任务时指定截止日期 (Priority: P1) 🎯 MVP

**Independent Test**: `add --due 2026-08-20` 后数据文件含该日期；非法日期报错且文件不变

### Tests（先写，确认失败）

- [ ] T003 [US1] `tests/test_due_date.py`：`main(["add", "交报告", "--due", "2026-08-20"])` 返回 0 且存储中任务 due 为 `date(2026,8,20)`（FR-001）
- [ ] T004 [P] [US1] `tests/test_due_date.py`：非法日期 `2026-13-40`、`明天`、`20260820` 均被拒绝，退出码非 0 且数据文件无变化（FR-002、SC-004）
- [ ] T005 [P] [US1] `tests/test_due_date.py`：不带 `--due` 的 add 行为与旧版一致，due 为 None（FR-003）

### Implementation

- [ ] T006 [US1] `todo/cli.py`：`add` 子命令增加 `--due` 参数；先正则校验 `^\d{4}-\d{2}-\d{2}$` 再 `date.fromisoformat` 解析，失败时向 stderr 输出中文错误并返回非零码

**Checkpoint**: US1 测试全绿——MVP 可交付

---

## Phase 3: User Story 2 - 列表展示日期与逾期标记 (Priority: P2)

**Independent Test**: 构造逾期/今天/未来/无日期四类任务，list 输出逐行符合预期

### Tests（先写，确认失败）

- [ ] T007 [US2] `tests/test_due_date.py`：未完成且 due < 今天的任务行含 `!逾期` 标记；due == 今天的不含（FR-005、Edge Case）
- [ ] T008 [P] [US2] `tests/test_due_date.py`：已完成任务即使曾逾期也不显示逾期标记（Acceptance 2）
- [ ] T009 [P] [US2] `tests/test_due_date.py`：无日期任务的 list 输出与旧格式逐字符一致（FR-007、SC-002）

### Implementation

- [ ] T010 [US2] `todo/cli.py`：新增纯函数 `is_overdue(task, today)`；`list` 输出追加 `(截止: YYYY-MM-DD)` 与 `!逾期` 标记

**Checkpoint**: US2 测试全绿

---

## Phase 4: User Story 3 - 按日期筛选 (Priority: P3)

**Independent Test**: 多日期数据下 `--overdue` / `--today` 各自仅命中目标任务

### Tests（先写，确认失败）

- [ ] T011 [US3] `tests/test_due_date.py`：`list --overdue` 仅输出已逾期的未完成任务（FR-006）
- [ ] T012 [P] [US3] `tests/test_due_date.py`：`list --today` 仅输出今天到期的未完成任务；无日期任务不被任一筛选命中（FR-007）

### Implementation

- [ ] T013 [US3] `todo/cli.py`：`list` 增加互斥参数组 `--overdue` / `--today`，筛选仅作用于未完成任务

**Checkpoint**: 全部测试绿，三个故事均可独立演示

---

## Phase 5: 收尾

- [ ] T014 全量回归 `uv run pytest`（新旧测试全绿）；手工 smoke：`add --due` + `list` 实跑一遍真实数据文件
- [ ] T015 提交：`feat: 任务支持截止日期（--due / 逾期标记 / 日期筛选）`

---

## Dependencies & Execution Order

- T001 → 阻塞其余一切（模型先行）；T002 可与 T003~T005 并行起草
- 故事顺序：US1（P1）→ US2（P2）→ US3（P3），每个故事内部"测试先行"
- 并行机会：每个故事内的测试任务标 [P]，可一次性写完；实现任务均为串行（同改 `cli.py`）

## Implementation Strategy

单 agent 顺序执行即可（任务量小、均改同一文件）；若拆给多 agent，仅测试任务可并行。
