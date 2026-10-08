---
name: doc-standard
description: 中文技术文档写作规范与项目记忆（术语表、决策记录）格式。当用户要求撰写、修改、重组、审计任何项目文档（README、AGENTS.md、架构文档、教程、手册、决策记录、复盘），或判断"这条信息该写在哪""文档该叫什么、章节怎么排"，或在设计过程中提炼领域术语、维护 CONTEXT.md、判断决策是否值得记为 ADR 时使用。也被全局 AGENTS.md 2.8 驱动，用于项目记忆骨架的初始化与维护。
---

# 文档与项目记忆规范

核心方法两条：**每个事实只有一个家**；**每条可机械检查的规则配一个可执行的检查**。项目记忆（术语表、决策记录）随设计过程当场生长，不批量、不留待办。

## 何时使用

- 撰写、修改、重组、审计任何项目文档；判断"这条信息该写在哪""文档该叫什么、章节怎么排"。
- 设计过程中主动建模：挑战模糊术语、当场更新 CONTEXT.md、判断决策是否值得记为 ADR（主动协议，见 [references/domain-modeling.md](./references/domain-modeling.md)）。
- 初始化或维护项目记忆骨架（全局 AGENTS.md 2.8 驱动）：项目 AGENTS.md、CONTEXT.md、docs/architecture.md、doc-structure.json、doc-budgets.json。

## 内容地图

| 你要做的事 | 归属 |
|---|---|
| 写作细则：分层、命名、骨架、写作规则、事实核查、反 slop、长度预算、机器门禁 | [references/writing-rules.md](./references/writing-rules.md) |
| 主动建模协议：挑战术语、场景检验、对照代码、何时记 ADR | [references/domain-modeling.md](./references/domain-modeling.md) |
| 术语表（CONTEXT.md）格式 | [references/CONTEXT-FORMAT.md](./references/CONTEXT-FORMAT.md) |
| 决策记录默认：`yyyy-mm-dd-主题.md`，骨架 问题 → 决策 → 备选方案 → 后果（项目可用 doc-structure.json 覆盖） | [references/writing-rules.md](./references/writing-rules.md) 第三、四节 |

## 关键默认速览

- 文档族分层：根 AGENTS.md（常驻指令）→ 架构文档 → 模块 README → 决策记录（为什么）/ 操作手册（怎么做）/ 事后复盘（事故故事）；同一事实只写一次，其余地方链接。
- 术语 → 根 CONTEXT.md；难逆且非显而易见的决策 → docs/adr/；操作步骤 → docs/cookbook/（动宾短语命名）。
- 门禁：`python3 scripts/check_docs.py <目录或文件>...`（一段一行、禁用词、链接锚点、长度预算、命名骨架、代码块真实编译）。

## 完成标准

- 每个新事实有且只有一个家，其他地方是链接；
- 所有操作性声明都实际执行过；
- 反 slop 清单逐项自查通过、`check_docs.py` 全绿；
- 改动涉及的 README 和代码注释契约随代码同步更新。
