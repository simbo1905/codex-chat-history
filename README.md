# codex-chat-history

> A **SKILL.md** plus a **`uv run --script`** helper to **back up**, **list**, and **inspect** Codex CLI session rollouts under `$CODEX_HOME/sessions` — gzip mirrors that keep the `YYYY/MM/DD` layout, optional line-size histograms, and user-message extraction. This is **not** about Cursor IDE agent transcripts; see **[cursor-chat-history](https://github.com/simbo1905/cursor-chat-history)** for those.

## TL;DR

Jump to [Install](#install), or fetch **SKILL.md** alone:

```bash
mkdir -p ~/.codex/skills/codex_chat_history && \
  curl -fsSL https://raw.githubusercontent.com/simbo1905/codex-chat-history/main/codex_chat_history/SKILL.md \
  -o ~/.codex/skills/codex_chat_history/SKILL.md
```

---

## What lives on disk

Codex stores append-only **`rollout-*.jsonl`** files:

```text
$CODEX_SESSIONS_ROOT/YYYY/MM/DD/rollout-....jsonl
```

If **`CODEX_SESSIONS_ROOT`** is unset, use **`$CODEX_HOME/sessions`**. If **`CODEX_HOME`** is unset, use **`~/.codex`**.

Bundled in **`codex_chat_history/`**:

| File | Role |
|------|------|
| **`SKILL.md`** | Skill instructions for agents |
| **`codex_chat_history.py`** | `backup`, `list`, `profile`, `bounds`, `user-messages`; optional **`--archived`** on the first four includes **`$CODEX_HOME/archived_sessions/`** after **`--src`**. |
| **`codex_prompt_history_search.py`** | Search **`$CODEX_HOME/history.jsonl`** (prompt history): **`--mode EXACT|ANY|FUZZY`**, **`-j/--json`**, CSV columns UTC date / `ts` / `session_id` / `text`. |
| **`line_histogram.awk`** | Optional histograms / line slices for huge JSONL |

Details, env vars, and **`jq`** recipes: [**`codex_chat_history/SKILL.md`**](codex_chat_history/SKILL.md).

**Repo (canonical):** [github.com/simbo1905/codex-chat-history](https://github.com/simbo1905/codex-chat-history)  
**Gist (SKILL + scripts + awk):** [gist.github.com/simbo1905/34f66e28462c02a2e64ecdf9389fbe51](https://gist.github.com/simbo1905/34f66e28462c02a2e64ecdf9389fbe51)  
**Related:** Cursor transcripts — [cursor-chat-history](https://github.com/simbo1905/cursor-chat-history)

## Install

**Codex CLI (personal):**

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/simbo1905/codex-chat-history.git ~/.codex/skills/codex_chat_history
```

**Claude Code (personal)** — same layout works under Claude’s skills dir:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/simbo1905/codex-chat-history.git ~/.claude/skills/codex_chat_history
```

**Single project:** clone into **`.codex/skills/`** or **`.claude/skills/`** in that repo instead of `$HOME`.

Then:

```bash
chmod +x ~/.codex/skills/codex_chat_history/codex_chat_history/codex_chat_history.py
chmod +x ~/.codex/skills/codex_chat_history/codex_chat_history/codex_prompt_history_search.py
~/.codex/skills/codex_chat_history/codex_chat_history/codex_chat_history.py --help
```

## Smoke test (read-only source)

Only **reads** `~/.codex/sessions` (or **`--src`**). Writes to a **temp** tree.

```bash
PY=/path/to/codex_chat_history/codex_chat_history/codex_chat_history.py
DEST=$(mktemp -d)
uv run --script "$PY" backup --dry-run --dest "$DEST"
uv run --script "$PY" backup --dest "$DEST"
uv run --script "$PY" backup --dest "$DEST"   # expect: 0 new rollout gzip writes (skip by mtime)
mv "$DEST" "${DEST}.old"
DEST=$(mktemp -d)
uv run --script "$PY" backup --dest "$DEST"   # full mirror again
uv run --script "$PY" list --archived | head -n 2   # optional: includes archived rollouts after sessions
# Optional integrity (default sessions root = ~/.codex/sessions):
# R=$(find "$HOME/.codex/sessions" -name 'rollout-*.jsonl' -type f -print -quit)
# REL=${R#"$HOME/.codex/sessions/"}
# gunzip -c "$DEST/$REL.gz" | diff -q - "$R" && echo OK
rm -rf "${DEST}.old" "$DEST"
```

## Release checklist

1. On **`main`**, run the smoke test against real sessions; optionally **`gunzip -c` … `diff`** one **`rollout-*.jsonl`** as above.
2. **Tag** if you want a named snapshot: **`git tag v0.x.y && git push origin v0.x.y`** (optional for a skill repo).
3. **Sync the public gist** from **`codex_chat_history/`** on **`main`**:

   ```bash
   D=codex_chat_history
   GIST=34f66e28462c02a2e64ecdf9389fbe51
   gh gist edit "$GIST" --filename SKILL.md "$D/SKILL.md"
   gh gist edit "$GIST" --filename line_histogram.awk "$D/line_histogram.awk"
   gh gist edit "$GIST" --filename codex_chat_history.py "$D/codex_chat_history.py"
   gh gist edit "$GIST" --filename codex_prompt_history_search.py "$D/codex_prompt_history_search.py"
   gh api -X PATCH "gists/$GIST" \
     -f description='Codex Chat History: SKILL + codex_chat_history.py + codex_prompt_history_search.py + line_histogram.awk (mirrors https://github.com/simbo1905/codex-chat-history)'
   ```

4. Refresh **README** / **SKILL.md** if behavior or defaults changed.

## Copyright

Skill text and tooling © 2026 LiveMore Capital [livemorecapital.com](https://www.livemorecapital.com) (where not otherwise noted).
