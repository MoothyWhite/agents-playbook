---
name: mcp-security-audit
description: |
  Audit MCP (Model Context Protocol) server configurations for security issues. Use this skill when:
  - Reviewing .mcp.json files for security risks
  - Checking MCP server args for hardcoded secrets or shell injection patterns
  - Validating that MCP servers use pinned versions (not @latest)
  - Detecting unpinned dependencies in MCP server configurations
  - Auditing which MCP servers a project registers and whether they're on an approved list
  - Checking for environment variable usage vs. hardcoded credentials in MCP configs
  - Any request like "is my MCP config secure?", "audit my MCP servers", or "check .mcp.json"
  keywords: [mcp, security, audit, secrets, shell-injection, supply-chain, governance]
---

# MCP Security Audit

Audit MCP server configurations for security issues — secrets exposure, shell injection, unpinned dependencies, and unapproved servers.

MCP servers give agents direct tool access to external systems. A misconfigured `.mcp.json` can expose credentials, allow shell injection, or connect to untrusted servers.

Method: read the config and check every registered server against the smell list below. Configs are small — audit by reading, no scanner script.

## Smell list

### 1. Hardcoded secrets — CRITICAL

Any credential literal in `args` or `env`: API keys, tokens, passwords, connection strings with embedded credentials, private keys. Typical shapes: `sk-...`, `ghp_...`, `AKIA...`, `Bearer ...`, `password=...`, `postgres://user:pass@...`.

Fix — reference environment variables instead:

```json
"env": { "API_KEY": "${MY_API_KEY}" }
```

### 2. Shell injection patterns — HIGH

Shell constructs in `args`: `$(...)`, backticks, `;`, `|`, `&&`, `||`, `eval`, `bash -c`, `sh -c`, `>/dev/tcp/`, `curl ... | sh`. Args should be a direct command plus plain arguments, never shell interpolation.

### 3. Unpinned dependencies — MEDIUM

Package references using `@latest` (or no version) in `args`, e.g. `npx -y some-server@latest`. Every session then executes whatever the newest registry version is — a standing supply-chain risk.

Fix — pin an exact version: `"args": ["-y", "my-mcp-server@2.1.0"]`.

### 4. Hygiene — LOW

- `npx` without `-y`: interactive prompt can hang unattended runs.
- Servers nobody recognizes or that are not on the project's approved list: flag for the user to confirm provenance.

## Output

```
MCP Security Audit — <file>
Servers scanned: N
Findings: M (x CRITICAL, y HIGH, z MEDIUM, w LOW)

[SEVERITY] <server>: <what was found>
  Fix: <narrowest fix>
```

No findings: say so plainly and list what was checked. Report only — never edit the config unless the user asks.
