---
name: codex-chat-history
description: Backup, search, and inspect Codex CLI session rollout JSONL under $CODEX_HOME/sessions (date-partitioned tree). Use for mirroring rollouts to sync storage (e.g. iCloud), listing or bounding sessions by time, profiling large JSONL before reading, or extracting user-authored messages with jq or the bundled helper script.
---

# Codex Chat History

## What this covers

**Codex** stores each session as append-only **rollout** JSONL files. The on-disk layout is stable and predictable:

```text
$CODEX_SESSIONS_ROOT/YYYY/MM/DD/rollout-YYYY-MM-DDThh-mm-ss-<uuid>.jsonl
```

**Defaults (overridable; see Environment variables):**

- **`$CODEX_SESSIONS_ROOT`** — if unset, use **`$CODEX_HOME/sessions`**.
- **`$CODEX_HOME`** — if unset, use **`~/.codex`**.

So the usual path is **`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`**, which matches the structure Codex uses when **`CODEX_HOME`** is not set.

Archived sessions (after an archive action in product) may appear under:

```text
$CODEX_HOME/archived_sessions/
```

with the same `rollout-*.jsonl` filename pattern.

Each JSON line is a rollout record: a top-level **`timestamp`** plus a **`type`** / **`payload`** pair (for example `session_meta`, `event_msg`, `response_item`, `compacted`, `turn_context`). User-typed prompts are generally `type == "event_msg"` with `payload.type == "user_message"` and `payload.message`.

This skill is **not** about Cursor IDE transcripts (`~/.cursor/projects/.../agent-transcripts/...`); for those, use **[cursor-chat-history](https://github.com/simbo1905/cursor-chat-history)** (script **`cursor_chat_history.py`**).

## When to use it

- **Backup / mirror** rollouts to another directory or cloud-synced folder (gzip mirror preserves `YYYY/MM/DD` and stores `.jsonl.gz`).
- **Search or recover** what was said: extract user lines, then `rg` / filter by topic.
- **Inspect** large files safely: histogram or line-slice before loading whole files into context.
- **Bound by time**: first/last `timestamp` per file, or filesystem mtime with `--since`.

## Environment variables

All paths support **`~`** expansion. Use **absolute** paths when clarity matters.

| Variable | Purpose | If unset |
|----------|---------|----------|
| **`CODEX_HOME`** | Codex data root (`config.toml`, state DB, `sessions/`, etc.) | `~/.codex` |
| **`CODEX_SESSIONS_ROOT`** | Explicit directory containing the **`YYYY/MM/DD`** rollout tree | `$CODEX_HOME/sessions` |
| **`CODEX_SESSIONS_BACKUP_ROOT`** | Default destination root for **`backup`** (gzip mirror) | `~/icloud/.codex/sessions` |

**CLI overrides:** subcommands accept **`--src`**; **`backup`** also accepts **`--dst`** or **`--dest`** for the backup root, which wins over env defaults for that run.

**`--archived` (optional, default off):** For **`backup`**, **`list`**, **`profile`**, and **`bounds`**, pass **`--archived`** to **also** include **`$CODEX_HOME/archived_sessions/`** after finishing the same logic for **`--src`**. Archived rollouts use the same **`rollout-*.jsonl`** layout as active sessions. Does not apply to **`user-messages`** (single file).

## Bundled tools (this folder)

| File | Role |
|------|------|
| **`codex_chat_history.py`** | PEP 723 **`uv run --script`** helper (`requires-python = ">=3.13.0,<3.14"`, `dependencies = []`): **`backup`**, **`list`**, **`profile`**, **`bounds`**, **`user-messages`**; optional **`--archived`** on the first four to include **`$CODEX_HOME/archived_sessions/`** after **`--src`**. |
| **`line_histogram.awk`** | Optional: line-size histogram or extract specific line(s) from huge JSONL before parsing. |

```sh
chmod +x codex_chat_history.py
./codex_chat_history.py --help
```

Example **profile** with histogram (from repo or gist):

```sh
./codex_chat_history.py profile --awk ./line_histogram.awk --since 1d
```

Example **backup** (default destination = `$CODEX_SESSIONS_BACKUP_ROOT` or `~/icloud/.codex/sessions`):

```sh
./codex_chat_history.py backup --dry-run
./codex_chat_history.py backup --dest "$HOME/icloud/.codex/sessions"
./codex_chat_history.py list --archived
```

## Search and extract (workflows)

### 1) Know where you are reading

Resolve the sessions root once:

```sh
echo "${CODEX_SESSIONS_ROOT:-${CODEX_HOME:-$HOME/.codex}/sessions}"
```

### 2) Profile before brute-force reading

```sh
find "${CODEX_SESSIONS_ROOT:-$HOME/.codex/sessions}" -type f -name 'rollout-*.jsonl' | sort \
  | while read -r f; do
      echo "=== $f ==="
      awk -f line_histogram.awk "$f"
    done
```

### 3) Bound time per file

```sh
./codex_chat_history.py bounds
```

### 4) Extract user-authored text

With **`jq`**:

```sh
jq -r 'select(.type == "event_msg" and .payload.type == "user_message") | .payload.message' \
  "$ROLL_FILE"
```

With the script (includes simple path redaction):

```sh
./codex_chat_history.py user-messages "$ROLL_FILE"
```

### 5) Redact before share

Replace host-specific paths and usernames in anything you copy out (`<PATH>`, `<USER>` placeholders).

## Compaction signals

Rollouts may contain compaction-related content (`compacted` lines and/or `event_msg` variants such as `context_compacted`). Inspect with small slices:

```sh
grep -E 'context_compacted|"compacted"' "$ROLL_FILE" | head
jq -r 'select(.type == "compacted") | .payload.message' "$ROLL_FILE"
```

## Related: `history.jsonl`

`$CODEX_HOME/history.jsonl` is a separate, smaller **prompt history** log (not the full rollout). Rollouts under `sessions/` are the complete session transcript for resume/replay tooling.

## Retention

Codex does **not** auto-expire rollout files by age; backups and pruning are operator concerns. See Codex release notes / issue trackers for current behavior of `history.jsonl` trimming vs rollouts.

## Canonical source and releases

- **Repository:** https://github.com/simbo1905/codex-chat-history  
- **Public gist** (mirrors this folder’s three files): https://gist.github.com/simbo1905/34f66e28462c02a2e64ecdf9389fbe51  

For smoke tests, optional **`git tag`**, and **gist** sync commands, see the **Release checklist** in the repo root **README.md**.

## Copyright

Skill text and tooling © 2026 LiveMore Capital https://www.livemorecapital.com (where not otherwise noted).
