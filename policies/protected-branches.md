# Protected branch policy

## Authorization

- A request to create, update, review, approve, ship, or release a pull request does not authorize a direct protected-branch push or merge.
- A direct push requires the current user message to name the exact target branch and ask for a direct push.
- A merge requires the current user message to name the exact target branch and ask to merge it.
- An administrative bypass requires explicit authorization in the current user message.

## Before an authorized operation

- Resolve the repository, remote, source branch, and target branch.
- Confirm the worktree and staged diff contain only intended changes.
- Verify required checks, reviews, branch protection, and base freshness; stop on ambiguity or unavailable verification.

## Enforcement

The local merge guard is advisory defense-in-depth and can be bypassed. Enforce this policy with remote branch protection, required reviews and checks, and credentials that cannot bypass them. Use the visible local override only when the current user message authorizes the exact protected operation.
