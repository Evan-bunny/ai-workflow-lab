# todo-cli 项目约定

一个极简的 Python todo 命令行工具，同时是三种 AI 开发 Workflow（Spec Kit / Ralph Loop / 多 Agent 编排）的实战演示仓库。

## 技术约定
- Python 3.13+，依赖用 `uv` 管理
- 测试用 pytest，运行方式：`uv run pytest`
- CLI 入口：`uv run todo`（或 `uv run python -m todo.cli`）
- 所有公开函数加类型标注
- 注释和文档字符串用中文
- 提交信息用中文，格式：`类型: 简述`（如 `feat: 增加 xxx 命令`）

## 结构
- `todo/models.py` — 数据模型
- `todo/storage.py` — JSON 存储层
- `todo/cli.py` — 命令行入口（argparse 子命令）
- `tests/` — pytest 测试
- `specs/` — Spec Kit 规格文档（spec / plan / tasks）
- `PROMPT.md` / `fix_plan.md` / `ralph-loop.sh` — Ralph Loop 三件套

## 硬性要求
- 任何改动后必须 `uv run pytest` 全绿才算完成
- 存储格式变更必须向后兼容（能读旧 JSON）
