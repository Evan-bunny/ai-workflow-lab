# Feature Specification: 任务截止日期（due-date）

**Feature Branch**: `001-due-date`

**Created**: 2026-08-18

**Status**: Draft

**Input**: User description: "为 todo-cli 的任务增加截止日期（due date）支持"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 创建任务时指定截止日期 (Priority: P1)

用户在添加任务时，可以附带一个截止日期，以便记住任务的完成时限。

**Why this priority**: 这是整个功能的核心价值——没有"带日期的任务"，其余一切（展示、提醒）都无从谈起。

**Independent Test**: 执行 `todo add "交报告" --due 2026-08-20`，然后 `todo list` 能看到该任务及其截止日期，即交付了"记录时限"这一完整价值。

**Acceptance Scenarios**:

1. **Given** 空任务列表，**When** 用户执行 `add` 并附带合法的 `--due` 日期，**Then** 任务被创建且持久化保存了该截止日期
2. **Given** 空任务列表，**When** 用户执行 `add` 不附带 `--due`，**Then** 任务被创建且截止日期为空（与旧行为一致）
3. **Given** 空任务列表，**When** 用户提供格式非法的日期（如 `2026-13-40`、`明天`），**Then** 命令以非零码退出并在 stderr 给出中文错误提示，任务不被创建

---

### User Story 2 - 列表中直观看到截止日期与逾期状态 (Priority: P2)

用户在查看任务列表时，能直接看到每个任务的截止日期；已逾期且未完成的任务有明确的视觉标记。

**Why this priority**: 记录日期之后，最自然的需求就是"一眼看出什么快到期/已逾期"。

**Independent Test**: 手工准备含逾期、今天到期、未来到期、无日期四类任务的数据文件，`todo list` 输出中四类任务呈现符合预期。

**Acceptance Scenarios**:

1. **Given** 存在未完成且截止日期早于今天的任务，**When** 用户执行 `list`，**Then** 该任务行显示日期并带 `!逾期` 标记
2. **Given** 存在已完成但曾逾期的任务，**When** 用户执行 `list`，**Then** 该任务行不显示逾期标记（已完成即免责）
3. **Given** 存在无截止日期的任务，**When** 用户执行 `list`，**Then** 该任务行不显示任何日期信息，排版不错位

---

### User Story 3 - 按截止日期筛选查看 (Priority: P3)

用户只想看"今天到期"或"已逾期"的任务，快速聚焦紧急事项。

**Why this priority**: 锦上添花；列表已能展示日期后，筛选只是便利性增强。

**Independent Test**: 准备多日期任务数据，分别用筛选参数执行 `list`，核对输出仅包含符合条件的任务。

**Acceptance Scenarios**:

1. **Given** 存在不同截止日期的未完成任务，**When** 用户执行 `list --overdue`，**Then** 仅输出已逾期的未完成任务
2. **Given** 存在今天到期与其他日期到期的任务，**When** 用户执行 `list --today`，**Then** 仅输出今天到期的未完成任务

---

### Edge Cases

- 截止日期早于今天的任务允许创建（用户可能补录任务），创建时不警告、仅在 list 中标记逾期
- "今天"到期不算逾期；逾期判定以自然日（本地时区）为粒度，不涉及具体时刻
- 旧版本创建的无日期数据文件必须能正常读取，且任务行为与升级前一致
- 闰年、月末等合法日期（如 2024-02-29、2026-01-31）必须被正确接受

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 在 `add` 命令上提供可选的 `--due <日期>` 参数，接受 `YYYY-MM-DD` 格式
- **FR-002**: 系统 MUST 校验日期格式与合法性，非法输入时报错且不写入任何数据
- **FR-003**: 系统 MUST 将截止日期随任务一起持久化，且能无损读取旧版（无日期字段）数据文件
- **FR-004**: `list` 命令 MUST 在每个有日期的任务行展示其截止日期
- **FR-005**: `list` 命令 MUST 对"未完成且截止日期早于今天"的任务显示逾期标记
- **FR-006**: 系统 MUST 提供 `list --overdue` 与 `list --today` 两种筛选，且筛选仅作用于未完成任务
- **FR-007**: 无截止日期的任务在展示与筛选中 MUST 行为不变（不被 `--overdue`/`--today` 命中）

### Key Entities

- **Task（任务）**：在现有 `id / title / done` 基础上增加可选属性 `due`（截止日期，可为空）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 规格中全部验收场景对应的自动化测试通过（`uv run pytest` 全绿）
- **SC-002**: 用 v1（无日期）数据文件升级后，所有既有命令行为与升级前完全一致（零迁移成本）
- **SC-003**: 用户用一条命令即可完成"带截止日期创建任务"，无需二次编辑
- **SC-004**: 非法日期输入 100% 被拒绝且数据文件不产生任何变化

## Assumptions

- 用户只在本地单机上使用，日期以运行机器的本地时区为准
- 截止日期精度为"天"，不支持时间点与提醒/通知功能（超出本期范围）
- 暂不提供修改既有任务日期的命令（如需要将作为后续功能另行立项）
