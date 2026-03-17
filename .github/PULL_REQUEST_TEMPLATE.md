## Summary

<!-- One or two sentences describing what this PR does and why. -->

Closes #<!-- issue number -->

---

## Type of Change

<!-- Check all that apply -->

- [ ] ✨ New feature / user story
- [ ] 🐛 Bug fix
- [ ] 🔧 Tech task / refactor
- [ ] 📚 Documentation update
- [ ] 🚀 CI/CD / tooling change
- [ ] 🔒 Security fix

## Component(s) Affected

<!-- Check all that apply -->

- [ ] `appliance/` – Raspberry Pi 5 edge controller
- [ ] `assistant/` – PC / AIOps server
- [ ] `shared/` – shared utilities
- [ ] `docs/` – documentation
- [ ] `scripts/` – deployment & tooling
- [ ] `.github/` – CI/CD

---

## Changes Made

<!-- Bullet list of meaningful changes. Keep it concise. -->

-
-

---

## Definition of Done (DoD) Checklist

> **All boxes must be checked before requesting a review.**

### Code Quality
- [ ] Code follows PEP 8 and project coding standards (see `docs/development_coding_standards.md`)
- [ ] Type annotations added / updated; `mypy` passes with no new errors
- [ ] `ruff format` and `ruff check` pass with zero warnings
- [ ] No hardcoded secrets or credentials

### Testing
- [ ] Unit / integration tests written for all new logic
- [ ] All existing tests pass (`pytest`)
- [ ] Code coverage ≥ 80 % for changed modules
- [ ] Edge cases and failure paths tested

### Review & Documentation
- [ ] PR has at least **one approving review**
- [ ] Inline docstrings added / updated (Google-style)
- [ ] README or relevant docs updated if user-facing behaviour changed
- [ ] `docs/backlog.md` updated if a story is completed
- [ ] Changelog / commit message follows [Conventional Commits](https://www.conventionalcommits.org/) (e.g. `feat:`, `fix:`, `chore:`)

### Safety & CI
- [ ] CI pipeline passes (lint ✅  type-check ✅  tests ✅)
- [ ] No new security vulnerabilities introduced
- [ ] Regression tests pass; no existing functionality broken
- [ ] Deployed to staging / Mininet sim and smoke-tested (if applicable)

---

## Screenshots / Demo

<!-- If this PR changes any UI or observable behaviour, attach screenshots or a short description of the manual test performed. -->

N/A

---

## Sprint Tracking

| Field | Value |
|-------|-------|
| Sprint | Sprint <!-- number --> |
| Story / Task ID | <!-- US-XXX / TK-XXX --> |
| Story Points | <!-- n --> |
| Epic | <!-- EP-XXX --> |
