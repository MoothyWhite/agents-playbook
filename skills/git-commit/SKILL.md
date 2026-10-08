---
name: git-commit
description: "Single source of truth for git commit conventions: analyzes the git diff to generate Conventional Commits messages, and defines the commit authorization and git safety protocol. Must be read before any git commit or commit-producing operation. Trigger when the user mentions commit, commit message, or conventional commits, or asks for help committing changes or writing a commit message."
---

# git-commit

This skill is the single source of truth for git commit conventions: analyze the current git diff, generate a commit message following [Conventional Commits](https://www.conventionalcommits.org/), and apply the commit authorization and git safety protocol (end of file). Every git commit operation must follow this file.

## Workflow

### 1. Read the changes and commit history

```bash
git status --porcelain
git diff --staged   # or git diff (when unstaged)
git log --oneline -20
```

### 2. Determine style: follow the repo, don't impose

Look at the recent commits in `git log`:

- If the repo already has a stable style (format, language, gitmoji usage), **follow it**, even when it differs from this file's defaults
- If there is no clear style, use this file's default (Conventional Commits)

### 3. Judge type and scope yourself

Judge from the diff's actual semantics — do not guess from file paths:

- **type**: feat / fix / docs / style / refactor / test / chore / perf / ci / build / revert (meanings in the table below)
- **scope**: the module or directory the change belongs to (e.g. auth, api, ui); omit scope when several modules are equally involved

### 4. Write the description

Hand-write one sentence stating "what was done", not a list of file names. Rules:

- Subject line within 50 characters, no trailing punctuation
- For multi-line commits, the body explains "what and why", not "how" (the diff already shows that)

### 5. Commit only after authorization

Execute only with the user's explicit consent this time:

```bash
git add <specific files>          # stage only files related to this change
git commit -m "<type>[scope]: <description>"
```

Use heredoc for multi-line commits: `git commit -m "$(cat <<'EOF' ... EOF)"`.

## Conventional Commits spec

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

The description concisely states the scope of the change (e.g. `feat(auth): add JWT login endpoint`); type/scope are English keywords.

| Type       | Meaning                                |
|------------|----------------------------------------|
| `feat`     | New feature                            |
| `fix`      | Bug fix                                |
| `docs`     | Documentation changes                  |
| `style`    | Code formatting (no logic change)      |
| `refactor` | Refactoring (no new feature or fix)    |
| `test`     | Test-related                           |
| `chore`    | Build/tooling/dependency misc          |
| `perf`     | Performance optimization               |
| `ci`       | CI/CD configuration changes            |
| `build`    | Build system or external dependencies  |
| `revert`   | Revert a commit                        |

## Gitmoji (optional)

gitmoji is **not required**. Use it only when the target repo's history already does; otherwise leave it out:

```
<type>[scope]: <gitmoji> <description>

feat: ✨ add user authentication
fix: 🐛 fix null pointer in checkout flow
refactor: ♻️ extract payment service
```

Common gitmoji quick reference:

| Gitmoji | Meaning              |
|---------|----------------------|
| ✨       | New feature          |
| 🐛       | Bug fix              |
| ♻️       | Refactor             |
| 📝       | Documentation        |
| ✅       | Tests                |
| ⚡️       | Performance          |
| 🔧       | Configuration files  |
| ⬆️       | Upgrade dependencies |

For the full gitmoji list see [references/gitmoji.md](references/gitmoji.md).

## Breaking Changes

If the change includes incompatible changes, add `!` after the type:

```
feat(api)!: change authentication endpoint response format
```

Or use a `BREAKING CHANGE` footer:

```
feat: allow config to extend other configs

BREAKING CHANGE: `extends` key behavior changed
```

## Best practices

- One logical change per commit; when the diff spans multiple unrelated concerns, suggest the user split it into separate commits
- State the change directly and concisely in the description
- Reference issues: `Closes #123`, `Refs #456`

## Git safety protocol

- **Ask the user explicitly and obtain consent before every commit**; past authorization does not carry over — every commit is an independent event
- **Never** update git config
- **Never** run destructive commands (`--force`, hard reset) unless the user explicitly asks
- **Never** skip hooks (`--no-verify`) unless the user asks
- **Never** force-push main/master
- If a commit fails because of hooks, fix the problem and create a **new commit** — do not amend
- **Never** commit secrets (`.env`, credentials.json, private keys, etc.)
