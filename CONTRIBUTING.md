# Contributing to AI Skills Assembly

Contribute reusable, cross-project guidance. Keep organization, account, product, repository, customer, and identity-specific material in a private catalog. Contributions use this repository's MIT License; no CLA is required.

## Skills

- Put each skill at `skills/<name>/SKILL.md`; match its lowercase hyphenated frontmatter `name`.
- Include a trigger-focused `description` and `license: MIT`.
- Register it in `catalog.json` and its intended profiles; add routing rules plus positive and negative fixtures when activation applies.
- Keep optional detail in directly linked references.

## Frontmatter policy

Skills stick to agentskills.io-standard frontmatter fields so they stay portable to Codex. The library deliberately does not adopt `when_to_use` (it duplicates the description's listing cost on Claude and is invisible on Codex), `disable-model-invocation` (it severs suggestion-hook activation, since the model performs the invocation), or skill-registered hooks. Revisit only with measured need.

## Output styles

- Put each output style at `templates/output-styles/<name>.md`, lowercase hyphenated, matching its catalog key.
- Set `keep-coding-instructions: true` in its frontmatter unless the style deliberately drops Claude Code's software-engineering behavior.
- Register it in `catalog.json` under `outputStyles` and in its intended profiles. Installing a style links the file; it still needs a person to select it.

## Public boundary

- Exclude private names, paths, domains, architecture, commands, tickets, and incident narratives.
- Exclude secrets, credentials, customer data, health information, and proprietary source.
- Exclude generated caches, local settings, and installed symlinks.

## Validate

Run `python3 scripts/validate.py` before opening a pull request and report skipped checks or limitations.
