#!/usr/bin/env python3
"""Flag low-value comments in staged changes, per the code-comments skill.

Advisory by default: prints offenders and exits 0 so it never blocks a commit.
Set COMMENT_CHECK_STRICT=1 to make violations fail the commit (override with
`git commit --no-verify`). Scans only added lines in staged source files.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

SOURCE_RE = re.compile(r"\.(ts|tsx|js|jsx|mjs|cjs|py|go|rs|java|kt|c|h|cpp|cc)$")

# A staged hunk line that adds a comment. We only look at "+ " diff lines.
LINE_COMMENT_RE = re.compile(r"^\+\s*(//|#)\s?(.*)$")
BLOCK_COMMENT_RE = re.compile(r"^\+\s*(/\*+|\*|\*/)\s?(.*)$")

TICKET_RE = re.compile(
    r"\b([A-Z][A-Z0-9]+-\d+)\b"               # JIRA-123, ABC-9
    r"|#\d{2,}\b"                               # #1234
    r"|\b(jira|ticket|issue|fixes|closes|see pr|pull request)\b",
    re.IGNORECASE,
)
PROVENANCE_RE = re.compile(
    r"\b(used by|called from|added for|introduced for|needed for|for the .* (flow|feature|page))\b",
    re.IGNORECASE,
)
NARRATION_RE = re.compile(
    r"\b(removed|renamed|moved|changed to|switched to|now uses|new in v|previously|used to)\b",
    re.IGNORECASE,
)

BLOCK_WARN_THRESHOLD = 5  # consecutive added comment lines = verbose preamble


def staged_files() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [f for f in out.splitlines() if SOURCE_RE.search(f)]


def staged_added_comments(path: str) -> list[tuple[int, str]]:
    """Return (line_no_in_new_file, comment_text) for added comment lines."""
    diff = subprocess.run(
        ["git", "diff", "--cached", "-U0", "--", path],
        capture_output=True, text=True, check=True,
    ).stdout
    results: list[tuple[int, str]] = []
    new_lineno = 0
    for line in diff.splitlines():
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            new_lineno = int(m.group(1)) if m else 0
            continue
        if line.startswith("+") and not line.startswith("+++"):
            lc = LINE_COMMENT_RE.match(line)
            bc = BLOCK_COMMENT_RE.match(line)
            if lc:
                results.append((new_lineno, lc.group(2).strip()))
            elif bc:
                results.append((new_lineno, bc.group(2).strip()))
            new_lineno += 1
        elif not line.startswith("-"):
            new_lineno += 1
    return results


def classify(text: str) -> str | None:
    if TICKET_RE.search(text):
        return "ticket/PR reference"
    if PROVENANCE_RE.search(text):
        return "provenance note"
    if NARRATION_RE.search(text):
        return "change narration"
    return None


def main() -> int:
    findings: list[str] = []
    for path in staged_files():
        comments = staged_added_comments(path)
        run_len, run_start = 0, 0
        prev_lineno = None
        for lineno, text in comments:
            kind = classify(text)
            if kind:
                findings.append(f"  {path}:{lineno}  [{kind}]  {text[:70]}")
            if prev_lineno is not None and lineno == prev_lineno + 1:
                run_len += 1
            else:
                run_len, run_start = 1, lineno
            if run_len == BLOCK_WARN_THRESHOLD:
                findings.append(
                    f"  {path}:{run_start}  [verbose block]  "
                    f"{BLOCK_WARN_THRESHOLD}+ consecutive comment lines"
                )
            prev_lineno = lineno

    if not findings:
        return 0

    strict = os.environ.get("COMMENT_CHECK_STRICT") == "1"
    sys.stderr.write(
        "\ncode-comments: low-value comments in staged changes "
        "(default is none - comment only the non-obvious WHY):\n"
        + "\n".join(findings)
        + "\n\nSee the code-comments skill. "
        + ("Commit blocked (COMMENT_CHECK_STRICT=1); fix or `git commit --no-verify`.\n"
           if strict else "Advisory only - commit proceeds.\n")
    )
    return 1 if strict else 0


if __name__ == "__main__":
    sys.exit(main())
