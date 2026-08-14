# Delivery checklist

Use this checklist as the compact state record for a delivery-loop run.

## Status block

```markdown
**Delivery Status**
- Phase:
- Goal:
- Accepted plan:
- Current evidence:
- Checks run:
- Failures:
- Fixes applied:
- Reruns:
- Live evidence:
- Review findings:
- PR:
- Blockers:
- Next gate:
```

## Phase checklist

| Phase | Required input | Exit evidence | Stop condition | Next gate |
| --- | --- | --- | --- | --- |
| Intake | User goal, repo, branch, worktree state, constraints, and plan-approval state. | Status block names the goal, branch, constraints, and whether a plan is accepted. | Goal or repo cannot be identified, or user constraints conflict. | Research or plan gate. |
| Research | Intake summary plus the uncertain approach, API, prior art, or feasibility question. | Local sources checked, facts separated from assumptions, and recommendation captured. | Key decision still needs user preference or external access. | Plan gate. |
| Plan gate | Goal, constraints, and enough evidence to make implementation decisions. | One decision-complete `<proposed_plan>` or confirmed accepted plan. | No accepted plan in the current conversation. | Implementation after approval. |
| Implementation | Accepted plan and applicable project or stack guidance. | Scoped changes recorded with notable files and rationale. | Change needs new scope, dependency install, credentials, or destructive action. | Integration / see it live. |
| Integration / see it live | Implemented change and the command, app, endpoint, scene, or UI path to exercise. | Concrete proof such as screenshot path, response, stdout/stderr, or observed state. | App/path cannot run for environment reasons or missing access. | Quality loop. |
| Quality loop | Implemented change, live evidence when relevant, and focused validation commands. | Checks, failures, fixes, and reruns recorded; broad suite run after focused fixes pass. | Same focused failure survives two fix attempts, three quality cycles fail to converge, or failure is out of scope. | PR gate or review loop. |
| PR gate | Diff summary and validation evidence. | Handoff summary, residual risks, and PR status if already authorized. | Commit, push, PR creation, or PR update lacks explicit approval. | Review loop after approval or handoff. |
| Review loop | Current diff, validation evidence, and review scope. | Normal review and adversarial findings recorded, scoped fixes applied, affected checks rerun. | Finding is broad/out of scope or needs user decision. | Final smoke. |
| Final smoke | Final local state and critical-path smoke command or target. | Fast critical-path evidence after final fixes. | Smoke target unavailable or failure persists outside task scope. | Await merge. |
| Await merge | PR URL or handoff target, validation, review, and smoke evidence. | User-facing summary with CI/merge status if checked and next action. | Merge, deploy, or production action not explicitly authorized. | User decision. |

1. Intake
   - Identify repo, branch, worktree cleanliness, task goal, and explicit constraints.
   - Check whether the user has already accepted a plan in this conversation.

2. Research
   - Search local code first for prior art and conventions.
   - Use external sources only when local context cannot answer the decision.
   - Separate verified facts from assumptions.

3. Plan gate
   - Produce one decision-complete `<proposed_plan>`.
   - Stop until the user approves implementation.

4. Implementation
   - Keep edits scoped to the accepted plan.
   - Preserve unrelated user or parallel changes.
   - Record notable files changed and why.

5. Integration / see it live
   - Start the relevant app, server, scene, endpoint, or command.
   - Exercise the exact changed path.
   - Capture concrete evidence: screenshot path, response body, stdout/stderr, or observed state.

6. Quality loop
   - Run the cheapest focused check first.
   - Fix in-scope failures.
   - Rerun the focused check.
   - Run the broader suite once focused checks pass.
   - Include unit/integration, E2E, accessibility, security, type/lint, or project validation only when applicable.

7. PR gate
   - Summarize diff and validation.
   - Ask before commit, push, or PR creation unless the user already explicitly requested it.

8. Review loop
   - Run normal code/architecture review.
   - Run adversarial review after the normal pass.
   - Fix real scoped defects.
   - Rerun checks affected by each fix.

9. Final smoke
   - Run the fast critical path smoke test after final local fixes.
   - After deploy or merge, smoke the deployed target if the user asks and scope is clear.

10. Await merge
   - Never merge into a protected branch (`main`, `master`, `develop`, or the repository default) unless the current user message explicitly names that branch as the merge target and asks to merge it.
   - Keep the PR open or draft when that instruction is absent; a release, approval, or general shipping request is not enough.
   - Report PR URL, CI status if checked, validation, residual risks, and next user action.

## Stop conditions

- Stop after two failed attempts against the same focused failure.
- Stop after three total quality cycles without convergence.
- Stop before dependency installation, credential use, live security testing, commit, push, PR creation, merge, rebase, destructive Git actions, or production actions unless explicitly authorized. For `main`/`master`, require an explicit merge instruction in the current message.
- Stop when failures appear preexisting or out of scope; report evidence instead of broadening the task.

## Rerun policy

- After a fix, rerun the smallest check that proves the fix.
- After multiple focused fixes, rerun the broader relevant suite once.
- After review fixes, rerun only checks that could be affected plus the smoke test.
