---
name: architect-review
description: "Clean code and architecture evaluation: module boundaries, coupling and cohesion, abstraction levels, naming, dependency direction, complexity hotspots, refactoring strategy. Use for a code, design, or architecture review, refactor planning, tech debt evaluation, or is this design right."
license: MIT
metadata:
  display-name: "Architect Review"
  version: "1.1"
  platforms: "claude-code codex"
  tags: "review architecture refactoring clean-code"
---

# Architect review

You are evaluating code or a design - not just shipping a feature. Slow down. Look across files, not just inside one.

## What "good" looks like (use as a checklist)

### Module boundaries
- Each module has one reason to change. If the same file changes for "auth" AND "billing" reasons, it's two files pretending to be one.
- Public surface is small and intentional. Anything not exported is internal - confirm callers respect that.
- Cyclic imports are a structural smell, never just a workaround. Break the cycle by extracting the shared concept or inverting the dependency.

### Coupling
- Modules depend on **abstractions** their consumers control, not on **concretions** they happen to use.
- A high-level module (business logic) must not import a low-level module (HTTP client, DB driver) directly. Inject it.
- Configuration, clocks, randomness, IO - pass them in. Hardcoded singletons make code untestable and rigid.

### Cohesion
- Functions in a file should manipulate the same data or serve the same purpose. A `utils.ts` with 14 unrelated helpers is a smell.
- A class with mostly-disjoint subsets of methods that touch disjoint subsets of fields is two classes.

### Abstraction levels
- Within one function, all statements should sit at roughly the same level of abstraction. `if (user.isAdmin) { db.exec("UPDATE ...") }` mixes policy and SQL.
- Don't abstract until you have ≥3 real instances. Two-instance abstractions almost always misfit the third.
- Conversely: don't tolerate the third copy. By copy three, the shared shape is real.

### Naming
- Names answer "what does this represent?" - not "what's its type?" or "where is it used?".
- Reject: `data`, `info`, `manager`, `handler`, `helper`, `util`, `process`, `do<X>`. They convey nothing.
- A good name lets you delete the comment that was about to explain it.

### Dependency direction
- Dependencies point inward, toward stable abstractions. Domain logic doesn't import infrastructure.
- "Stable" = changes infrequently. UI changes weekly; domain rules change yearly. UI imports domain, not the reverse.

### Complexity hotspots
- Cyclomatic complexity > ~10 in one function: split it.
- Nesting depth > 3: extract or invert. `if (!x) return;` beats `if (x) { ... }` wrapping the whole function.
- Long parameter lists (>4): the parameters belong to an object you haven't named yet.
- A flag parameter (`doThing(x, true)`) usually means two functions.

### Error handling
- Errors are part of the domain, not afterthoughts. A `Result<T, E>` or typed exceptions tell the caller what can fail.
- Don't catch what you can't handle. Re-throw or let it propagate.
- No empty `catch {}` blocks. Ever.

### Tests as design feedback
- Hard-to-test code is usually badly-designed code. If a function needs 9 mocks, it's doing 9 things.
- Tests that break on every refactor are testing implementation, not behavior.

## How to do a review

1. **Read the diff once, top-to-bottom**, no nitpicks. Form a hypothesis: what is this change *really* doing?
2. **Locate the change in the architecture.** Which layer? Which boundary? Does it respect existing direction of dependencies?
3. **List concerns by severity**, using the ladder below.
4. **For each concern, propose the smallest change that resolves it.** "Rewrite this module" is rarely the answer. "Extract these 3 lines into a function with this name" usually is.
5. **Note what's *good*.** A review that's only critical doesn't teach the pattern to repeat.

Severity: Blocker (correctness, security, data loss) / Should-fix (compounding design debt) / Nit.

## When proposing refactors
- Refactors are behavior-preserving. If you change behavior, that's a separate change with its own tests.
- One refactor per commit. "Rename + extract + reorder" is three commits.
- Tests must stay green after every step. If they go red, you broke behavior.

## Anti-patterns to flag
- "Manager," "Helper," "Util" classes (god objects waiting to happen).
- Premature interfaces with one implementation.
- Configuration via environment variable read deep inside a function.
- `if (env === 'test') { ... }` branches in production code.
- Comment smells - restatement, ticket refs, provenance notes, verbose preambles: defer to the `code-comments` skill.
- `TODO` without an owner or a date.
- Re-implementing a stdlib/framework primitive.

## What this skill is *not*
Not a style nitpicker. Tabs vs spaces, single vs double quotes, import order - that's the formatter's job. Focus on structure and intent.
