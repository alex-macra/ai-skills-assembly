# Contributing to AI Skills Assembly

Contribute reusable, cross-project guidance. Keep organization, account, product, repository, customer, and identity-specific material in a private catalog. Contributions use this repository's MIT License; no CLA is required.

## Skills

- Put each skill at `skills/<name>/SKILL.md`; match its lowercase hyphenated frontmatter `name`.
- Include a trigger-focused `description` and `license: MIT`.
- Register it in `catalog.json` and its intended profiles; add routing rules plus positive and negative fixtures when activation applies.
- Keep optional detail in directly linked references.

## Public boundary

- Exclude private names, paths, domains, architecture, commands, tickets, and incident narratives.
- Exclude secrets, credentials, customer data, health information, and proprietary source.
- Exclude generated caches, local settings, and installed symlinks.

## Validate

Run `python3 scripts/validate.py` before opening a pull request and report skipped checks or limitations.
