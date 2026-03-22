# Network-Chan Development Guidelines and Coding Standards

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-21  
**Version:** 1.1 (updated for current practices)  

## Introduction

This document establishes best practices for Network-Chan development, ensuring code quality, maintainability, and alignment with 2026 standards. It covers version control, branching, review process, documentation, naming, and testing. Guidelines are mandatory and enforced via CI/CD (GitHub Actions).

Standards draw from PEP 8/12 (Python), ECMAScript 2025 (JS/Vue), and focus on clean code, practical testing for solo dev, and security-by-default.

### Project-Specific Must-Haves

- Use **asyncio** and **asyncio-mqtt** for concurrent I/O (MQTT, FastAPI endpoints).
- Apply **Numba** `@njit` / `@jit` in performance-critical paths (e.g., RL updates).
- Use **Pydantic v2** for all data validation and **Pydantic Settings** for config.
- Logging via **structured logging factory** (`shared/src/utils/logging_factory.py`).
- UTC timestamps: `from datetime import datetime, timezone; datetime.now(timezone.utc)`.
- No deprecated APIs; target Python 3.12+.
- All stub comments labeled `# TODO:`.
- Module structure (when applicable):  
  - `xxx_settings.py` — Pydantic Settings / config classes  
  - `xxx_models.py` — Pydantic models / schemas  
  - `xxx.py` — core implementation / logic  
- Enforce via pre-commit hooks and CI.

## Version Control Strategies

- **Repository**: Git + GitHub monorepo (Network Appliance / Application / shared).
- **Commits**:
  - Atomic, focused changes.
  - Conventional Commits (`feat:`, `fix:`, `docs:`, etc.).
  - GPG-signed commits (optional but recommended).
  - Pre-commit hooks for Ruff lint/format/type checks.
- **Tagging**: SemVer (MAJOR.MINOR.PATCH); GitHub Releases for changelogs.

## Branching Model

**GitHub Flow** (trunk-based, short-lived branches):

- `main` always production-ready (protected: PR + CI required).
- Feature/hotfix branches from `main` (e.g., `feat/telemetry-ingest`, `fix/qlearning-bug`).
- Workflow:
  1. Branch from `main`.
  2. Commit often.
  3. Open PR early (draft if WIP).
  4. Merge after self-review + CI green.
  5. Delete branch.
- Solo-dev note: Self-approve PRs after CI passes; external review optional for complex changes.

## Code Review Process

- All `main` changes via PR.
- **PR Guidelines**:
  - Conventional Commit title.
  - Description: What/Why/How + issue links.
  - Small (<300 lines preferred).
- **Process**:
  1. Submit PR to `main`.
  2. CI runs (Ruff lint/format, MyPy types, pytest if enabled).
  3. Self-review (focus: logic, standards, security).
  4. Merge (squash + Conventional Commit) when green.
- Solo-dev note: CI is primary gate; manual functionality testing on real hardware/emulator before merge.

## Documentation and Naming Conventions

### Documentation

- **Inline**: Google-style docstrings (Python); JSDoc (JS/Vue). Include Args/Returns/Raises/Examples.
- **Modules**: README.md per module.
- **Project**: Root README + /docs/ (Markdown + Mermaid).
- **APIs & Code Reference**:
  - **FastAPI**: Interactive Swagger UI (`/docs` endpoint) for runtime API exploration and endpoint documentation.
  - **APIs & Code Reference**:
    - **FastAPI**: Interactive Swagger UI (`/docs`) and ReDoc (`/redoc`) for runtime endpoint exploration, testing, and documentation — auto-generated from routes, Pydantic models, and docstrings. Remains the primary tool for live API interaction during development and Manual QA.
    - **MkDocs**: Material for MkDocs theme + `mkdocstrings` plugin to automatically generate browsable code reference documentation from Google-style docstrings. The full documentation site (including hand-written pages and API summaries) is built and auto-published to GitHub Pages via a GitHub Actions workflow — but only after successful Ruff linting, MyPy type checking, and pytest runs.
      - Source: `docs/` folder at repo root
      - Auto-generated section: `docs/code/` (from docstrings across shared, appliance, application modules)
      - API reference section: `docs/api/` — includes summaries of FastAPI endpoints/models (linked or embedded from Swagger/OpenAPI spec where practical)
- **Changelog**: Keep a Changelog format.

### Naming

- **Python**:
  - snake_case variables/functions.
  - CamelCase classes.
  - UPPER_SNAKE constants.
  - lowercase_underscore.py files.
- **JavaScript (Vue)**:
  - camelCase variables/functions.
  - PascalCase components.
  - kebab-case.vue files.
- **General**: Descriptive; avoid unnecessary abbreviations; `_` prefix for private.

Enforced: Ruff (linting + formatting), pre-commit.

## Testing & CI

- **Local development**: Rely on IDE (Pylance/VS Code) for real-time type checking, linting, and debugging.
- **Manual QA**: Functionality tests on real hardware (Pi 5) or emulator — verify behavior, logs, no crashes.
- **Automated QA**: pytest (unit/integration), MyPy (strict types) — run exclusively in GitHub Actions workflow.
- **CI flow**:
  - Ruff lint/format/type checks first.
  - pytest/MyPy only after basic functionality exists (currently disabled; enable progressively).
  - Coverage target >80% where tests are added.

## Security & Best Practices

- Security-by-default: Ruff security rules in CI, input validation (Pydantic), rate limiting.
- Future: Plan PQC transition (ML-KEM key exchange + ML-DSA signatures for MQTT and model signing).

This document is reviewed quarterly or after major milestones.
