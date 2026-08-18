# fix_plan.md — Ralph Loop 任务列表

为 todo-cli 增加以下功能。每个任务的验收标准：实现 + 测试 + `uv run pytest` 全绿。
存储格式变更必须向后兼容（能读旧 JSON）。

## 任务

- [x] T1 priority 优先级：`add` 支持 `--priority high|medium|low`（默认 medium）；list 中 high 任务显示 `[!]` 前缀标记
- [x] T2 tags 标签：`add` 支持 `--tags a,b,c`（逗号分隔）；新增 `list --tag <名>` 只显示含该标签的任务
- [x] T3 search 搜索：新增 `todo search <关键词>` 子命令，对任务标题做大小写不敏感的子串匹配并输出匹配任务
- [ ] T4 stats 统计：新增 `todo stats` 子命令，输出总任务数、已完成数、未完成数、逾期未完成数

## 备注

（agent 卡点时在此记录）
