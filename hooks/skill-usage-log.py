#!/usr/bin/env python3
"""Opt-in PreToolUse hook: append one private JSONL line per skill invocation.

Never blocks the tool call - always exits 0, even on malformed input.
Set ``AI_SKILLS_USAGE_LOG`` to override the default log target.
"""
from __future__ import annotations

import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path


def log_path() -> tuple[Path, bool]:
    configured = os.environ.get("AI_SKILLS_USAGE_LOG", "").strip()
    if configured:
        return Path(configured).expanduser(), True
    return Path.home() / ".ai-skills" / "skill-usage.jsonl", False


def prepare_log_directory(path: Path, custom: bool) -> bool:
    parent = path.parent
    existed = parent.exists()
    if parent.is_symlink():
        return False
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if parent.is_symlink() or not parent.is_dir():
        return False
    if not custom or not existed:
        parent.chmod(0o700)
    return True


def append_record(path: Path, record: dict) -> None:
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY | getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    if no_follow:
        flags |= no_follow
    elif path.is_symlink():
        return

    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags, 0o600)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            return
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            descriptor = None
            handle.write(json.dumps(record) + "\n")
    except OSError:
        return
    finally:
        if descriptor is not None:
            os.close(descriptor)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return 0
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            return 0
        skill = tool_input.get("skill") or tool_input.get("command") or ""
        if not isinstance(skill, str) or not skill:
            return 0

        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "skill": skill,
            "cwd": payload.get("cwd", "") if isinstance(payload.get("cwd", ""), str) else "",
        }
        path, custom = log_path()
        if prepare_log_directory(path, custom):
            append_record(path, record)
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
