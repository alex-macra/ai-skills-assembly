---
name: automation
description: "Repeatable infrastructure: CI/CD pipelines, GitHub Actions, deploy and release scripts, dev-server orchestration, cron and scheduled jobs, container builds, backups, rollback. Use when setting up or fixing CI, writing a Dockerfile or deploy script, or on any deploy, release, pipeline, or schedule request."
license: MIT
metadata:
  display-name: "Automation"
  version: "1.1"
  platforms: "claude-code codex"
  tags: "ci-cd deploy scripts infrastructure"
---

# Automation

Manual steps are a bug. Anything done more than twice - install, build, test, deploy, backup, restore - gets a script. Anything done on a schedule gets a job runner.

## Principles

- **Idempotent.** Running the script twice should produce the same outcome as running it once.
- **Fail loud.** `set -euo pipefail` in bash; exit non-zero on any unhandled error; never `|| true` to swallow failures.
- **Reproducible from a clean checkout.** No "you also need to install X manually" - that goes in the script.
- **One thing per script.** `build.sh`, `test.sh`, `deploy.sh`. A 600-line `do-everything.sh` is a footgun.
- **Inputs via flags or env, outputs to stdout, errors to stderr.** The Unix way composes; a script that writes to random paths doesn't.

## CI/CD (GitHub Actions)

### Structure
- One workflow per concern: `ci.yml` (build + test), `deploy.yml` (release), `nightly.yml` (slow checks).
- Trigger on `pull_request` and `push` to main; avoid `workflow_dispatch`-only critical jobs.
- Reuse via `workflow_call` or composite actions when ≥2 workflows share steps.

### Performance
- Cache `node_modules` / `.venv` / build artifacts keyed by lockfile hash. Stale caches lie - invalidate aggressively when lockfile changes.
- Matrix only when the matrix is meaningful (multiple OS, multiple runtime versions). Don't matrix `[true, false]` flags.
- Parallel jobs > sequential steps. CI charges per-minute on the wall-clock of the longest job, not the sum.

### Secrets
- Use the platform's secret store (GitHub Secrets, GitLab CI Variables). Never echo a secret in logs.
- Scope secrets to environments (`production`, `staging`). Production secrets are not visible to PR builds from forks.
- Rotate keys when someone leaves the project or a CI runner is replaced.

### Required checks
- Lint, type-check, tests must all pass before merge. Configure branch protection to enforce.
- Don't add "advisory only" required checks - either it blocks merge or it doesn't.

## Deploy scripts

### Shape of a good deploy script
```
1. Build artifact      (deterministic - same input → same output)
2. Run smoke check     (does the artifact start? does /health respond?)
3. Push to target      (registry, server, CDN)
4. Switch traffic      (zero-downtime if possible)
5. Health check live   (real traffic hitting new version is OK)
6. Roll back on fail   (script ends with "you can run ./rollback.sh")
```

### Atomic deploys
- Build into `dist.tmp/`, then atomically rename to `dist/`. Don't write into the live directory.
- Same for symlinks: `ln -sfn new-release current-release` is atomic at the inode level.
- Database migrations: run them *before* the new app version starts. Migrations are forward-compatible with the *previous* app version, so rollback works.

### Rollback
- Every deploy script needs a documented rollback. "Just run the previous version's deploy again" is a documented rollback - write it down.
- Keep N previous releases on disk. Rolling back is `ln -sfn` to the previous one, not a full re-deploy.

## Containers

- One process per container. If you need a sidecar, write a docker-compose / pod manifest, don't run two daemons in one image.
- Multi-stage builds: builder stage with dev deps, final stage with runtime only. Final image stays small.
- Pin base images by digest (`@sha256:...`) for production. `latest` is a vulnerability waiting to happen.
- `HEALTHCHECK` in the Dockerfile so the orchestrator knows the process is actually serving, not just running.
- Don't run as root. `USER 1000` in the final stage.

## Scheduled jobs (cron, GitHub Actions schedule, systemd timers)

- Cron expressions are nearly write-only. Add a comment: `# Every 15 minutes Mon-Fri 9am-5pm UTC`.
- Idempotent jobs. Two scheduled runs overlapping should not corrupt state.
- Lock file or atomic check-and-set if double-execution is dangerous (`flock`, DB-level advisory lock).
- Log every run with start/end timestamps and exit code. A silent cron is an undebuggable cron.
- Alert on missed runs (the absence of a log is the signal).

## Dev-server orchestration

- A single `npm run dev` (or `make dev`) starts everything a contributor needs. If they need to remember to start three services in three terminals, you have a contributor-onboarding bug.
- Use `concurrently`, `npm-run-all`, or a Procfile-style runner (`overmind`, `foreman`).
- Different ports per service, documented in `README.md` and `.env.example`.

## Agent and local harness patterns

- Keep project-local automation close to the project: commands, hooks, and routing registries live under the repo, not in a global dotfile, when they encode project rules.
- Hook-style guardrails should be grounded in a documented rule, path-gated, advisory by default, and robust enough that a hook bug never blocks normal work.
- Blocking hooks are for narrow, high-confidence safety rules only, such as refusing `git commit` or `git push` on `main`/`master` unless the user explicitly asks for that workflow.
- Prefer trigger registries over hardcoded prompt logic when routing skills or specialist agents. Match by keyword, intent regex, and mentioned path globs; keep project-specific rules in the project.
- Slash-command equivalents should be thin wrappers around repeatable scripts or read-only status checks: build check, diff recap, status, scaffold, backup, deploy.
- Health check endpoints (`/health`, `/_status`) so the dev launcher knows when something is ready.

## Release workflow

- Semver where it makes sense (libraries). Date-based versions (`2026.05.11`) for apps where "breaking change" is a fuzzy concept.
- Auto-generated changelog from commit messages (Conventional Commits + `changesets` / `release-please`).
- Tag the commit, push the tag, let CI build and publish on tag.
- Never publish from a laptop. Build artifacts come from CI.

## Backups & disaster recovery

- The backup nobody has tested isn't a backup. Quarterly: take a backup, restore it to a fresh environment, verify the restored app works.
- 3-2-1 rule: 3 copies, 2 different media, 1 offsite.
- Document the RTO (recovery time objective) and RPO (recovery point objective). If you don't know, find out before the incident.

## Observability

- Every long-running script logs progress at fixed intervals - silence for >5 minutes is indistinguishable from a hang.
- Structured logs (JSON) ship to a central store. Grep on a single VM doesn't scale.
- Metrics for the things you'd want to alert on (latency, error rate, queue depth). Dashboards for everything else.
- Alerts only on symptoms (user-impacting), not causes - a single 500 isn't an alert, sustained > X% is.

## Anti-patterns

- "Run this on the prod server" - write it in the deploy script.
- "Set this env var manually" - put it in the secret store with provisioning automation.
- Manual DB migrations in production - wrap in a script with a dry-run mode.
- `kubectl edit` / `vim` on a running config - change in version control, redeploy.
- "We'll write the runbook later" - the runbook is the deploy script's `--help` output and the README.

## Verification before declaring done

- Run the script on a clean machine (or container) - no leftover state from your dev box.
- Read the logs of a successful run. Are they useful for an oncall who has never seen this project?
- Read the logs of a failed run (force one). Does the error tell you what to do?
- Time it. If the happy path takes > 10 minutes, that cost is real.
