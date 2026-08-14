---
name: delivery-loop
description: "Bounded task-delivery conductor: research, plan, implement, quality checks, live verification, PR readiness, code review, adversarial review, smoke test, merge handoff. Use for run the delivery loop, quality loop, review loop, work this in a loop, run the orchestrator, or any guarded end-to-end workflow."
license: MIT
metadata:
  display-name: "Delivery Loop"
  version: "1.1"
  platforms: "claude-code codex"
  tags: "workflow orchestration quality process"
---

# Delivery loop

Conductor for non-trivial task work. It does not replace specialist skills; it decides which phase comes next, delegates to the right skill, records evidence, and stops at human gates.

Read `references/delivery-checklist.md` at the start of a run, then keep its status block current in user-facing updates and the final handoff.

## Core rules

- If no accepted plan exists, research as needed, draft a `<proposed_plan>`, and stop for user approval before implementation.
- If the user has explicitly approved a plan in the current conversation, continue into implementation and quality loops.
- Keep loops bounded: after repeated failures, stop with evidence, blocker, and the next decision needed.
- Never merge into a protected branch (`main`, `master`, `develop`, or the repository default) unless the current user message explicitly names that branch as the merge target and asks to merge it. A release, PR, approval, or general shipping request is not merge authorization.
- Do not commit, push, create a PR, merge, rebase, run destructive Git commands, install dependencies, or perform live security testing unless the user explicitly authorizes that action.
- Repo-local instructions (`AGENTS.md` / `CLAUDE.md`) and project workflow skills outrank this generic guidance when they apply.

## Phase map

Each phase names the specialist skill to delegate to; per-phase inputs, exit evidence, and stop conditions live in the checklist reference.

Three phases have a subagent with the relevant skills already preloaded - prefer dispatching it over running the phase inline, so its output does not crowd the main context: `qa` (phases 5-6), `shipper` (phase 7), `reviewer` (phase 8).

1. **Intake** - Confirm repo state, user goal, constraints, current branch, and whether an accepted plan already exists.
2. **Research** (`task-research`) - When the approach, API, prior art, or feasibility is uncertain.
3. **Plan gate** - Produce a decision-complete `<proposed_plan>` and wait for approval unless approval already exists.
4. **Implementation** - Apply the accepted plan using the relevant stack, automation, or domain skills under repo-local rules.
5. **See it live** (`see-it-live`) - Boot the app, curl the endpoint, run the command, or capture a screenshot proving the specific change works.
6. **Quality loop** (`qa-automation`, `e2e-qa`, `security-review`, `a11y-audit`) - Plus project validation commands as applicable. Fix real failures and rerun affected checks.
7. **PR gate** (`fast-pr-workflow`) - Summarize diff and validation; commit, push, or create/update a PR only after explicit user approval.
8. **Review loop** (`architect-review`, then `adversarial-review`) - Normal review first, falsification pass second. Fix scoped defects and rerun relevant checks.
9. **Final smoke** (`smoke-test`) - After final fixes and again after deploy/merge when applicable.
10. **Await merge** - Do not merge. Keep `main`/`master` PRs open or draft until the user explicitly names that merge in the current message; report PR URL, validation, remaining risks, and status.

## Quality loop policy

For each failed check, classify it as product defect, test defect, environment issue, or out-of-scope preexisting failure. Fix product or test defects that are in scope, rerun the smallest relevant check, then run the broader suite once the focused check passes.

Stop and ask for direction when the same failure survives two focused fix attempts, when three total quality cycles have run without convergence, or when the next step would need new dependency installation, credentials, external services, live security scope, or destructive actions.

## Review policy

Normal review looks for correctness, architecture, maintainability, and missing tests. Adversarial review tries to falsify the riskiest claim with concrete inputs, state, or interleavings. Only fix findings that are real, scoped, and tied to the task; report broader follow-ups separately.

## Handoff format

When stopping, include the current phase, what changed, checks run, failures/fixes/reruns, live evidence, PR URL if any, blockers, and the next gate. Keep it short unless the user asks for the full checklist.

## Gotchas

- The loop must not depend on memory of prior chat: a resumed or handed-off run repeats or skips phases unless the checklist status block was kept current. The status block is the state record (observed 2026-07-03, delivery-loop hardening).
- Realistic user phrasing ("work this in a loop", "plan then do quality review smoke") failed to activate the conductor until routing was broadened; when adding phrasing, extend `skills/skill-rules.json` and the routing fixtures together, not the prose alone.
