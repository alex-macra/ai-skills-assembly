# Automation recipes

Stack-specific detail. The principles, when-to-automate rules, and rollback doctrine live in `SKILL.md`.

## CI/CD (GitHub Actions)

### Structure
- One workflow per concern: `ci.yml` (build + test), `deploy.yml` (release), `nightly.yml` (slow checks).
- Trigger on `pull_request` and `push` to main; avoid `workflow_dispatch`-only critical jobs.
- Reuse via `workflow_call` or composite actions when 2+ workflows share steps.

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
1. Build artifact      (deterministic - same input, same output)
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
