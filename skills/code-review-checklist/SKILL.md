---
name: code-review-checklist
version: 1.0.0
description: A concise code review checklist to apply before requesting merge.
type: content
tags: [review, quality, process]
---

# Code Review Checklist

Apply this checklist when reviewing a pull request:

1. **Correctness** — Does the change do what it claims? Edge cases handled?
2. **Tests** — Are there tests for new behavior? Do they pass?
3. **Readability** — Clear names, no dead code, comments only where needed.
4. **Security** — No secrets, input validation, safe dependencies.
5. **Performance** — No obvious N+1, unbounded loops, or leaks.
6. **Observability** — Meaningful logs/metrics, no sensitive data leaked.
7. **Docs** — Public APIs / behavior changes documented.

Summarize findings as: must-fix, should-fix, nit.
