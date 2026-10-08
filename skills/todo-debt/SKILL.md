---
name: todo-debt
description: >
  Harvest every `TODO:` comment in the codebase into a debt ledger, so the
  deliberate shortcuts and deferrals get tracked instead of rotting into
  "later means never". Use when the user says "todo debt", "/todo-debt",
  "TODO", "list the shortcuts", "debt ledger", or "what did we
  mark to do later". One-shot report, changes nothing.
---

Every deliberate simplification is marked with a `TODO:` comment naming its
ceiling and upgrade path. This collects them into one ledger so a deferral
can't quietly become permanent.

## Scan

Grep the repo for TODO comment markers, skipping `node_modules`, `.git`, and
build output:

`grep -rnE '(#|//) ?TODO:' .`  (add other comment prefixes if your stack uses them)

Each hit is one ledger row. The comment prefix keeps prose that merely
mentions the convention out of the ledger.

## Output

One row per marker, grouped by file:

`<file>:<line>, <what was simplified>. ceiling: <the limit named>. upgrade: <the trigger to revisit>.`

The convention is `TODO: <ceiling>, <upgrade path>`, so pull the ceiling and
the trigger straight from the comment. Want an owner per row too? add
`git blame -L<line>,<line>`.

Flag the rot risk: any `TODO:` comment that names no upgrade path or trigger
gets a `no-trigger` tag, those are the ones that silently rot. Generic TODOs
that mark no deliberate simplification land here too — that is expected, they
are the review candidates.

End with `<N> markers, <M> with no trigger.` Nothing found: `No TODO debt. Clean ledger.`

## Boundaries

Reads and reports only, changes nothing. To persist it, ask and it writes the
ledger to a file (e.g. `TODO-DEBT.md`). One-shot.
