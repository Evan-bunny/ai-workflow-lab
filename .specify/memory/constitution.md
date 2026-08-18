<!--
Sync Impact Report
- Version change: 0.0.0 → 1.0.0（首次正式批准）
- Modified principles: 无（模板占位符全部填充）
- Added sections: Core Principles（5 条）、技术约束、开发工作流、Governance
- Removed sections: 无
- Follow-up TODOs: 无
-->
# todo-cli Constitution

## Core Principles

### I. 简单优先（Simplicity First, NON-NEGOTIABLE）
每个功能必须用能满足需求的最简方案实现；禁止为"将来可能用到"的需求设计（YAGNI）。
新功能不得引入新的第三方运行时依赖，除非规格文档中明确论证其必要性。

### II. 测试先行（Test-First）
任何行为变更必须先写或先改测试，再写实现；红-绿-重构循环。
完成的唯一定义：`uv run pytest` 全部通过。严禁在测试未绿时宣称任务完成。

### III. 存储向后兼容（NON-NEGOTIABLE）
JSON 存储格式的任何变更必须能读取旧版本数据文件，不允许静默丢字段；
新增字段必须有默认值，反序列化时对缺失字段容错。

### IV. CLI 文本协议
所有功能通过命令行子命令暴露；正常输出到 stdout，错误到 stderr 并以非零码退出；
人类可读输出为默认格式。

### V. 显式文档字符串与类型标注
所有公开函数必须有中文文档字符串和完整类型标注；
注释解释"为什么"，不复述代码"做什么"。

## 技术约束

- Python 3.13+，依赖用 uv 管理，测试框架 pytest（pythonpath 已配置为项目根）。
- 数据持久化仅使用本地 JSON 文件，默认路径 `~/.todo-cli.json`。
- 不引入网络服务、数据库或 GUI——本项目定位是本地 CLI。

## 开发工作流

- 提交信息用中文，格式 `类型: 简述`（feat / fix / chore / test / docs）。
- 每个功能按 Spec Kit 流程执行：spec → plan → tasks → implement，规格评审通过后才写代码。
- 代码评审时对照 constitution 逐条检查合规性。

## Governance

本章程优先级高于所有其他开发习惯与临时指令。修订必须：
1. 写明修订原因并更新 Sync Impact Report；2. 按语义化版本递增版本号
（MAJOR=原则删除/重定义，MINOR=新增原则/章节，PATCH=措辞澄清）；
3. 修订后方可实施依赖新原则的工作。
所有实现任务在 review 时必须验证与本章程的合规性；复杂度超出原则限制时必须给出书面论证。

**Version**: 1.0.0 | **Ratified**: 2026-08-18 | **Last Amended**: 2026-08-18
