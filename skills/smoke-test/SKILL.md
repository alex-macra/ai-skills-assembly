---
name: smoke-test
description: "Fast critical-path sanity check: app boots, core path works, key endpoint responds. Run after integrating a change and again after deploy or merge, not as a full user journey. Use for smoke test, sanity check, critical path verification, does it still work, or a post-deploy check."
license: MIT
allowed-tools: Bash
metadata:
  display-name: "Smoke Test"
  version: "1.1"
  platforms: "claude-code codex"
  tags: "testing smoke critical-path"
---

# Smoke test

A smoke test answers one question in seconds, not minutes: **is the thing fundamentally alive?** It runs after you integrate a change and again after deploy/merge. If it fails, you stop - you do not proceed to ship.

## The critical path - and only the critical path

Cover the few things whose failure means "nothing works":

- The app **boots** with no fatal error.
- The **primary surface** loads (home screen renders / process starts / scene loads).
- A **health/liveness** signal is green.
- **One key end-to-end action** succeeds (the single most important thing the product does).

That's it. If you're writing the tenth assertion, you've drifted into `e2e-qa` territory - pull back.

## Keep it fast and deterministic

- Seconds, not minutes. A smoke test you skip because it's slow protects nothing.
- No flaky waits, no giant fixtures, no dependence on third-party services you can't stub.
- Deterministic pass/fail with a clear signal. A "probably fine" smoke test is worthless.

## By stack

| Stack | Smoke |
|---|---|
| **Godot** | `godot --headless --quit` (boots, no parse errors) + one `--script tests/<x>_check.gd` domain path |
| **Web** | Preview/dev server up → home route returns 200 → one key API call succeeds |
| **Backend / API** | `/health` returns 200 → one representative endpoint returns the expected shape |
| **CLI** | Binary runs `--help` / a trivial real command → exit 0 |

## Post-deploy smoke (the second run)

- Hit the **deployed** URL, not localhost. Localhost passing tells you nothing about prod.
- Confirm you're testing the **new build** (version endpoint, build hash, or a marker from the change).
- If it fails post-deploy, that's a rollback trigger - surface it loudly, don't bury it.

## What this skill is *not*

- Not unit/integration testing - that's `qa-automation`.
- Not full user journeys - that's `e2e-qa`.
- It's the shallow, fast, always-run gate between "built" and "shipped."
