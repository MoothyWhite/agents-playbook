---
name: gen-secret
description: "Generate random secrets (passwords, API keys, tokens, salts, encryption keys, etc.) and write them in place into .env / docker-compose / config files, with the plaintext never entering the conversation. Use when the user needs to generate or rotate secrets, fill .env.example placeholders, replace CHANGEME markers or default credentials, prepare secrets for a docker-compose deployment, or mentions generating passwords, random strings, secrets, or key rotation."
version: 1.0.0
---

# gen-secret — one secret per call, substituted into files

Core primitive: each invocation of `scripts/gen-secret.sh` generates **one** random secret, then either prints it to the terminal or substitutes it in place into a target file. Need N secrets? Call it N times.

```bash
bash <skill-dir>/scripts/gen-secret.sh [generation options] [target options]
```

## Why it is designed this way

When writing to a file, the secret passes only through shell variables — it never appears in command-line arguments (invisible to `ps`) and is never printed to the terminal in file mode. The goal: **when the agent configures secrets for the user, the plaintext exists only on disk and never lands in the conversation record**. Therefore:

- The agent always uses file-target mode (`-f`), so secrets land on disk without echoing.
- stdout mode (no `-f`) prints the plaintext — that is for the user running it in their own terminal; the agent must not use it.
- After writing, never view the target file's contents by any means (no cat / Read / grep / sed to extract keys or values, including any indirect parsing tricks). Verify only through three content-free channels: the script's confirmation output, the remaining-placeholder **count** (`grep -c '__[A-Z_]*__' file` — outputs a count only), and file permissions (`stat -c %a file` — should be 600).

## Scenario matrix

| Scenario | Mode | Invocation |
|----------|------|------------|
| Project ships `.env.example` with placeholder values (e.g. `SALT="salt"`) | key replacement | `-f .env -k SALT` |
| One secret appears in multiple places (e.g. password embedded in `DATABASE_URL`) | placeholder replacement | `-f .env -p __PGPASS__` |
| Compose file declares `${VAR:-default}` variables | write to adjacent `.env` | `-f .env -k VAR --append` |
| Rotate an existing secret | key replacement | `-f .env -k REDIS_AUTH` |
| User grabs a random string in their own terminal | stdout mode | omit `-f` |

## Parameters

**Generation options:**

- `-l, --length N` — secret length (default 32)
- `-c, --charset hex|digit|alpha|alnum|urlsafe|base64|full` — character set (default `alnum`)
- `--no-ambiguous` — additionally exclude `0 O 1 l I`; good for secrets transcribed by hand
- `--prefix STR` — prepend a literal prefix, e.g. `--prefix sk-` (not counted in length)

**Target options:**

- `-f, --file PATH` — edit a file in place; requires `-k` or `-p`
- `-k, --key KEY` — replace the value of every `KEY=...` line (supports `export KEY=`); with `--append`, appends the key if absent (creates the file with 600 permissions if it does not exist)
- `-p, --placeholder STR` — replace every occurrence of STR in the file; **all positions get the same secret**
- `--no-backup` — skip the default `PATH.bak.<timestamp>` backup
- `-q, --quiet` — suppress confirmation output in file mode

## Choosing a charset

- `hex` — when the consumer requires hex (e.g. Langfuse's `ENCRYPTION_KEY`: `-c hex -l 64`)
- `urlsafe` — when the secret goes into a URL (e.g. the password inside `DATABASE_URL`; avoids `@ : /` breaking connection-string parsing)
- `alnum` — universal default for dotenv scenarios
- `base64` / `full` — contains special characters; needs manual quoting in dotenv — use only after confirming the consumer supports it
- Entropy reference: 32 hex chars ≈ 128 bit; 32 alnum ≈ 190 bit; 32 urlsafe = 192 bit

## Workflow examples

**Example 1: generate config from .env.example**

Input: the project provides `.env.prod.example` with `SALT="salt"` and a placeholder `ENCRYPTION_KEY`
Output:

```bash
cp .env.prod.example .env
gen-secret.sh -f .env -k SALT -c hex -l 32
gen-secret.sh -f .env -k ENCRYPTION_KEY -c hex -l 64
```

**Example 2: keep derived values consistent**

Input: `DATABASE_URL` embeds `POSTGRES_PASSWORD`; both places must hold the same password
Output: first write a unique placeholder token, then replace all occurrences at once:

```
POSTGRES_PASSWORD=__PGPASS__
DATABASE_URL=postgresql://postgres:__PGPASS__@postgres:5432/postgres
```

```bash
gen-secret.sh -f .env -p __PGPASS__ -c urlsafe -l 24
```

**Example 3: all-in-one docker-compose deployment**

Input: `${VAR:-default}` values in the compose file need overriding
Output: do not touch the compose file; write to the adjacent `.env` (compose reads it automatically at startup):

```bash
gen-secret.sh -f .env -k CLICKHOUSE_PASSWORD --append -c alnum -l 24
```

## Notes

- Key replacement discards trailing inline comments on the replaced lines; the `.example` file remains the documented reference.
- Confirm `.env` permissions are 600 when done (files created by `--append` are 600 automatically).
- Before rotating a key that encrypts existing data (e.g. `ENCRYPTION_KEY`), warn the user first: old data will become undecryptable.
