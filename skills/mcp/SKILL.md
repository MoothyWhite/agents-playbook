---
name: mcp
description: MCP (Model Context Protocol) server lifecycle guide — building servers (Python/FastMCP or TypeScript SDK), verifying a server before release (real protocol session, inventory parity, failure paths, install smoke test), and auditing .mcp.json configurations (hardcoded secrets, shell injection, unpinned dependencies, unapproved servers). Use when building, shipping, or reviewing an MCP server or tool, or when asked "is my MCP config secure?", "audit my MCP servers", or "check .mcp.json".
---

# MCP servers

One protocol, three disciplines: build it well, prove it before release,
audit its configuration.

## Lifecycle map

| Stage | When | Guide |
|---|---|---|
| Build | Creating an MCP server to expose an API or service | [references/building.md](./references/building.md) |
| Release QA | Shipping or reviewing a server, tool, resource, prompt, catalog, or install path | [references/release-qa.md](./references/release-qa.md) |
| Security audit | Reviewing `.mcp.json` registrations | [references/security-audit.md](./references/security-audit.md) |

## Build defaults

- Language: TypeScript for broad client compatibility; Python/FastMCP equally supported (see language guides below).
- Transport: streamable HTTP for remote servers (stateless JSON), stdio for local servers.
- Tool quality is measured by how well agents accomplish real tasks: action-oriented names (`github_create_issue`), concise descriptions, actionable error messages, comprehensive API coverage over one-off workflow tools.

## Build references

- [references/mcp_best_practices.md](./references/mcp_best_practices.md) — naming, response formats, pagination, transport selection
- [references/python_mcp_server.md](./references/python_mcp_server.md) — FastMCP patterns and examples
- [references/node_mcp_server.md](./references/node_mcp_server.md) — TypeScript SDK patterns and examples
- [references/evaluation.md](./references/evaluation.md) — 10-question evaluation format for testing server effectiveness

Release QA proves runtime protocol behavior; the security audit reads configuration posture. The audit is report-only — never edit the config unless the user asks.
