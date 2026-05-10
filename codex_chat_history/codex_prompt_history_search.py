#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13.0,<3.14"
# dependencies = []
# ///
"""Search ~/.codex/history.jsonl (prompt history: session_id, ts, text)."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from difflib import SequenceMatcher
from enum import Enum
from pathlib import Path


def _codex_home() -> Path:
    raw = os.environ.get("CODEX_HOME", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.home() / ".codex"


def _history_path() -> Path:
    raw = os.environ.get("CODEX_HISTORY_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return _codex_home() / "history.jsonl"


class MatchMode(str, Enum):
    EXACT = "EXACT"
    ANY = "ANY"
    FUZZY = "FUZZY"


@dataclass(frozen=True)
class HistoryRow:
    session_id: str
    ts: int
    text: str

    def date_utc(self) -> str:
        return datetime.fromtimestamp(self.ts, tz=UTC).strftime("%Y-%m-%d")

    def as_csv_log4j(self) -> str:
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="")
        w.writerow([self.date_utc(), str(self.ts), self.session_id, self.text])
        return buf.getvalue()

    def as_json_line(self) -> str:
        return json.dumps(
            {
                "date": self.date_utc(),
                "ts": self.ts,
                "session_id": self.session_id,
                "text": self.text,
            },
            ensure_ascii=False,
        )


def _word_tokens(phrase: str) -> list[str]:
    return [t for t in re.split(r"\s+", phrase.strip()) if t]


def _matches_exact(phrase: str, text: str) -> bool:
    return phrase in text


def _matches_any(phrase: str, text: str) -> bool:
    words = _word_tokens(phrase)
    if not words:
        return False
    return any(w in text for w in words)


def _matches_fuzzy(phrase: str, text: str, threshold: float) -> bool:
    if not phrase.strip():
        return False
    needle = phrase.strip().lower()
    hay = text.lower()
    if needle in hay:
        return True
    return SequenceMatcher(None, needle, hay).quick_ratio() >= threshold


def _parse_line(line: str) -> HistoryRow | None:
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None
    sid = obj.get("session_id")
    ts = obj.get("ts")
    text = obj.get("text")
    if not isinstance(sid, str) or not isinstance(text, str):
        return None
    if isinstance(ts, bool) or ts is None:
        return None
    try:
        ts_i = int(ts)
    except (TypeError, ValueError):
        return None
    return HistoryRow(session_id=sid, ts=ts_i, text=text)


def cmd_search(args: argparse.Namespace) -> None:
    path: Path = args.file.expanduser().resolve()
    if not path.is_file():
        print(f"error: history file not found: {path}", file=sys.stderr)
        sys.exit(1)

    mode = MatchMode(args.mode.upper())
    phrase: str = args.phrase
    threshold = float(args.fuzzy_threshold)

    matcher = {
        MatchMode.EXACT: lambda row: _matches_exact(phrase, row.text),
        MatchMode.ANY: lambda row: _matches_any(phrase, row.text),
        MatchMode.FUZZY: lambda row: _matches_fuzzy(phrase, row.text, threshold),
    }[mode]

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            row = _parse_line(raw)
            if row is None:
                continue
            if not matcher(row):
                continue
            if args.json:
                print(row.as_json_line())
            else:
                print(row.as_csv_log4j())


def main() -> None:
    p = argparse.ArgumentParser(
        description="Search Codex prompt history (history.jsonl: session_id, ts, text).",
    )
    p.add_argument(
        "phrase",
        nargs="+",
        help="Search phrase (for EXACT, substring match in text field)",
    )
    p.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Path to history.jsonl (default: $CODEX_HISTORY_PATH or $CODEX_HOME/history.jsonl)",
    )
    p.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Emit one JSON object per matching line",
    )
    p.add_argument(
        "--mode",
        choices=[m.value for m in MatchMode],
        default=MatchMode.EXACT.value,
        help="EXACT substring | ANY any whole word from phrase | FUZZY difflib quick_ratio",
    )
    p.add_argument(
        "--fuzzy-threshold",
        type=float,
        default=0.65,
        help="FUZZY mode: minimum SequenceMatcher.quick_ratio (default 0.65)",
    )
    args = p.parse_args()
    args.phrase = " ".join(args.phrase)
    if args.file is None:
        args.file = _history_path()
    cmd_search(args)


if __name__ == "__main__":
    main()
