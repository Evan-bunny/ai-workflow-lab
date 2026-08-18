# ai-workflow-lab

> 用三种 AI 开发 Workflow 造同一个 todo-cli 的实战记录：
> **Spec Kit 规格驱动** · **Ralph Loop 自主循环** · **多 Agent 并行编排**

这个仓库的主角不是 todo-cli 本身（它只是个足够小的练手载体），而是**开发它的过程**。仓库里的每一类文件都对应一种当下主流的 AI 编程工作流，你可以照着复现、对比体感，选出适合自己团队的打法。

## 背景

2026 年的 AI 编程已经过了"对话框里边聊边写"的阶段，沉淀出了几套可复用的工程化 workflow。但看文章和亲手跑一遍完全是两回事——这个仓库就是一次完整动手的记录：同一个项目、三种范式、全部真实跑完，包括踩坑。

最终成果：**59 个测试全绿，12+ 个语义化 commit**，每个功能的出生方式都不同。

## 快速开始

```bash
# 需要 Python 3.13+ 和 uv（https://docs.astral.sh/uv/）
uv sync                 # 安装依赖（会把 todo 命令装进虚拟环境）
uv run todo --help      # 查看 CLI
uv run pytest           # 跑测试（59 个）
```

试两下：

```bash
uv run todo add "写周报" --due 2026-08-20 --priority high --tags 工作,周报
uv run todo add "每日站会" --repeat daily
uv run todo list --overdue
uv run todo search 周报
uv run todo stats
uv run todo export /tmp/todo.md
```

## 三种 Workflow 实战

### 练习 1：Spec Kit —— 规格驱动开发

**思路**：规格文档是唯一事实来源。先让 AI 生成规格，人审规格（审文字比审代码便宜），AI 再严格按规格实现。

**流程**（GitHub Spec Kit 五阶段流水线）：

```
constitution → specify → plan → tasks → implement
```

**本仓库中的关键文件**：

| 文件 | 内容 |
|---|---|
| [`.specify/memory/constitution.md`](.specify/memory/constitution.md) | 项目章程：5 条不可协商原则（测试先行、存储向后兼容……） |
| [`specs/001-due-date/spec.md`](specs/001-due-date/spec.md) | due-date 功能规格：3 个用户故事、7 条功能需求、可测量的成功标准 |
| [`specs/001-due-date/plan.md`](specs/001-due-date/plan.md) | 技术方案 + Constitution Check 合规表 |
| [`specs/001-due-date/tasks.md`](specs/001-due-date/tasks.md) | 15 个任务按用户故事分组，独立任务标注 `[P]` |

**结果**：实现阶段严格执行测试先行——先写出 7 个红灯测试，再实现转绿，全程零返工。规格里"旧数据零迁移"一句话直接变成了兼容测试。

**体感**：成本在前期文档（约占一半时间），换来实现阶段零跑偏。**适合**：重要功能、多人协作、需求复杂要追溯的场景。小 bug 修复用它就是杀鸡用牛刀。

---

### 练习 2：Ralph Loop —— 自主循环

**思路**：`while` 循环反复启动 agent，**每轮全新 context，磁盘上的文件是唯一记忆**。agent 每轮读任务清单 → 做一个任务 → 测试 → commit → 退出，直到全部完成。

**本仓库中的关键文件**：

| 文件 | 内容 |
|---|---|
| [`PROMPT.md`](PROMPT.md) | 每轮注入的固定指令（含 RALPH_STATUS 状态块约定） |
| [`fix_plan.md`](fix_plan.md) | 任务清单——循环的"共享状态" |
| [`ralph-loop.sh`](ralph-loop.sh) | 20 行 bash 循环：上限 8 轮 + 双重完成判定（显式 `EXIT_SIGNAL` + 清单无未完成项） |

**结果**：4 个功能（priority / tags / search / stats）无人值守完成，**4 轮收敛、约 8 分钟、每轮恰好一个任务一个 commit**，43 个测试全绿。

**踩坑记录**：`kimi -p`（无头模式）不能搭配 `--yolo`，第一轮循环 8 次全灭——幸好有轮次上限兜底。这正好说明了为什么 Ralph 循环必须有防失控设计。

**体感**：魔幻般省心，但前提刁钻——任务必须**可客观验证**（测试全绿）且**边界清晰**，否则循环会"游荡"。**适合**：批量机械任务、补测试、积压 issue、"睡前启动早上 review"。生产环境务必套沙箱。

**自己复现**：把 [`fix_plan.md`](fix_plan.md) 里的任务换成你自己的（保持 `- [ ]` 格式），然后：

```bash
./ralph-loop.sh 8    # 参数是最大轮数
```

---

### 练习 3：多 Agent 并行编排

**思路**：主 agent 只做调度，子代理各自带干净 context 并行干活。读操作放心并行，写操作必须"任务干净切分 + 合并集中收口"。

**3a. 扇出调研**：3 个只读 explore 子代理并行调研代码库（storage 兼容性 / CLI 扩展性 / 测试缺口），一次拿回三份报告，主 context 只装结论不装过程。

**3b. worktree 并行开发**：

```bash
git worktree add ../wt-export -b feat/export        # agent A：export 导出命令
git worktree add ../wt-recurring -b feat/recurring  # agent B：重复任务
```

两个 agent 同时开发、各自测试全绿、各自 commit；合并回主干时 `cli.py` 如期冲突（相邻位置各加函数），人工一分钟收口。

**教训**：子代理把 `__pycache__` 也提交了——**并行 agent 更需要明确的提交纪律**，这类约定要写进 [`AGENTS.md`](AGENTS.md)。

**体感**：任务能干净切成互不依赖的几块就并行；步骤强耦合就老老实实串行。**适合**：大代码库调研、多模块并行开发。

---

## 选型速查

| 场景 | 用哪个 |
|---|---|
| 大功能 / 需求复杂 / 要追溯 | Spec Kit（规格驱动） |
| 批量、可自动验证的机械任务 | Ralph Loop（自主循环） |
| 大库调研 / 多模块并行开发 | 多 Agent 编排 |
| 小修小补 | 都不用，直接改 |

三者不互斥，实战中是叠加的：`AGENTS.md` 打地基 → 规格决定做什么 → `[P]` 任务并行加速 → 可验证的部分交给循环跑完 → 对抗审查收口。

## 项目结构

```
├── todo/                  # todo-cli 源码（载体项目）
├── tests/                 # 59 个 pytest 测试
├── specs/001-due-date/    # 【Spec Kit】spec / plan / tasks 三份规格文档
├── .specify/              # 【Spec Kit】脚手架与项目章程
├── .spec-commands/        # 【Spec Kit】各阶段 prompt 模板
├── PROMPT.md              # 【Ralph Loop】每轮注入的指令
├── fix_plan.md            # 【Ralph Loop】任务清单（共享状态）
├── ralph-loop.sh          # 【Ralph Loop】循环驱动脚本
├── AGENTS.md              # 【上下文工程】项目约定（所有 workflow 的地基）
└── pyproject.toml         # uv 管理的 Python 包（含 todo 命令入口）
```
Thanks to all contributors! 
## License

[MIT](LICENSE)
