# agents-playbook

一套可移植的 AI 编码助手配置：全局行为规则（AGENTS.md）加一组即插即用的 skill。适用于任何兼容 AGENTS.md 的 agent CLI（Kimi Code、Claude Code 等）。

## 组成

- `AGENTS.md` —— 全局行为规则：操作红线、编码哲学、质量底线、工具偏好。放 `~/.agents/AGENTS.md` 全局生效；放项目根目录则只对该项目的 agent 生效。
- `skills/` —— 24 个 skill，涵盖文档规范、代码审查、Git 协作、测试调试、安全审计等。每个 skill 一个目录，含 `SKILL.md` 与可选的 `references/`、`scripts/`。
- `skills/doc-standard/scripts/check_docs.py` —— 可移植的文档门禁：一段一行、命名骨架、长度预算、代码块真实编译，可用于任意项目。

## 快速开始

1. 克隆本仓库。
2. 将 `AGENTS.md` 复制到 `~/.agents/AGENTS.md`，`skills/` 复制到 `~/.agents/skills/`。
3. 在 agent CLI 中开启新会话即可生效。

## 许可

MIT，见 [LICENSE](LICENSE)。
