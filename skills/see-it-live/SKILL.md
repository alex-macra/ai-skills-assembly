---
name: see-it-live
description: "Launch the app and confirm the specific change is actually visible and working: screenshot the UI, curl the endpoint, boot the scene, or run the command. Use for run the app, launch the app, start the server, spin up, preview it, see it live, does it render, or before declaring a user-visible change done."
license: MIT
allowed-tools: Bash
metadata:
  display-name: "See It Live"
  version: "1.1"
  platforms: "claude-code codex"
  tags: "verification runtime evidence"
---

# See it live

Type-check passing and green tests are **not** proof the change works. Behaviour lives in the running app. Before you say "done," start the thing and observe the specific change with your own eyes (or a screenshot / a response body).

## Pick the launch path by project type

| Project type | How to launch | What to observe |
|---|---|---|
| **Godot** | `godot --headless --quit` (catches parse/script errors fast); `godot --path . <boot scene>` for interactive; `godot --headless --script tests/<x>_check.gd` for a domain path | Scene loads with no errors; the changed behaviour happens |
| **Web frontend** | Start the dev server (`npm run dev` / framework equivalent), open the changed route | Golden path renders AND the error state; screenshot it |
| **Backend / API** | Start the server, `curl` the changed endpoint with a real payload | HTTP status + response shape match expectations |
| **CLI / library** | Run the command/binary with real args | `stdout`/`stderr` AND exit code are correct |

Match the project's actual run command - check its README / `CLAUDE.md` / `package.json` scripts / `justfile` first, don't invent one.

## Confirm the *specific* change, not just "it boots"

- Before launching, write down the one thing you expect to see that proves the change works ("the Save button now shows a spinner", "`/api/jobs` returns `status: queued`").
- Launch, reproduce the exact path that exercises the change, and check for that specific signal.
- "The app still starts" is necessary, not sufficient. A change can boot fine and still be wrong.

## Capture evidence

- UI: a screenshot of the changed state (and the error state if relevant).
- API/CLI: the actual response body / stdout, pasted, not paraphrased.
- Note the command you ran so it's reproducible.

## Teardown

- Stop the dev server / kill the spawned process when done. Don't leave orphaned ports held or headless instances running.
- If you seeded data or toggled a flag to see it, revert it.

## What this skill is *not*

- Not automated testing - for repeatable checks use `qa-automation` (units) or `e2e-qa` (browser/CLI flows).
- Not a release gate - for the fast critical-path sanity pass use `smoke-test`.
- This is the human-in-the-loop "I watched it happen" step.
