# Network-Chan Development Guidelines and Coding Standards

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  
**Version:** 1.0  

## Introduction

This Development Guidelines and Coding Standards document establishes the best practices for building Network-Chan, ensuring code quality, maintainability, collaboration, and alignment with 2026 industry standards. It covers version control strategies, branching model, code review process, documentation conventions, and naming standards. These guidelines are mandatory for all contributors and are enforced via CI/CD tools (e.g., GitHub Actions) to automate compliance.

The standards draw from up-to-date practices as of 2026, including PEP 8/12 (Python), ECMAScript 2025 (JS for Vue), and tools like Black, ESLint, and Prettier for auto-formatting. Emphasis is on clean code, test-driven development (TDD), and security-by-default (e.g., linting for vulnerabilities).

## Version Control Strategies

- **Repository Management**: Use Git with GitHub as the central repo (monorepo for Appliance/Assistant/shared). All code, docs, and configs are versioned. No binary files (e.g., models in MLflow registry instead).
- **Commit Practices**:  
  - Atomic commits: Small, focused changes (one logical unit per commit).  
  - Conventional Commits: Follow spec (e.g., `feat: add MQTT publisher`, `fix: resolve anomaly threshold bug`, `docs: update architecture.md`). Use tools like commitlint for enforcement.  
  - Signed Commits: Require GPG signing for all commits to verify authorship.  
  - Commit Hooks: Pre-commit (via pre-commit framework) for linting/formatting before push.

- **Release Tagging**: Semantic Versioning 2.0 (SemVer): MAJOR.MINOR.PATCH (e.g., 1.2.3). Tag releases (e.g., `git tag v1.2.3`) and use GitHub Releases for changelogs/artifacts.

## Branching Model

Follow **GitHub Flow** (simplified trunk-based development), the most up-to-date standard in 2026 for fast-paced, collaborative projects like this. It emphasizes short-lived branches and continuous integration over complex models like GitFlow.

- **Main Branch**: `main` is always production-ready and protected (requires PR approval + passing CI).  
- **Feature Branches**: Create from `main` (e.g., `feat/mqtt-publisher`, `fix/anomaly-detection`). Keep small (1–3 days work).  
- **Release Branches**: Rare; use tags on `main` for releases. For hotfixes: `hotfix/anomaly-bug` from tag.  
- **Workflow**:  
  1. Branch from `main`.  
  2. Commit often.  
  3. Open PR early (draft if WIP).  
  4. Merge to `main` after review/CI pass.  
  5. Deploy from `main`.  
- **Tools**: GitHub branch protection rules (require 1 approval, status checks); auto-merge on green CI.

- **Diagram**: GitHub Flow  

  ```mermaid
  gitGraph
      commit id: "main-start"
      branch feat/mqtt
      commit id: "feat1"
      commit id: "feat2"
      checkout main
      merge feat/mqtt id: "merge-pr"
      commit id: "hotfix" type: HIGHLIGHT
      branch hotfix/bug
      commit id: "fix1"
      checkout main
      merge hotfix/bug
      commit tag: "v1.0.0"
  ```

## Code Review Process

Code reviews ensure quality, knowledge sharing, and bug prevention. All changes to `main` require PR review.

- **PR Guidelines**:  
  - Title: Conventional Commit style (e.g., `feat: implement MQTT publisher`).  
  - Description: What/Why/How + links to issues/stories. Include screenshots for UI changes.  
  - Size: <300 lines preferred; split large PRs.  
  - Labels: `feat`, `fix`, `docs`, `chore`.  

- **Review Process**:  
  1. **Submit PR**: From feature branch to `main`; assign reviewers (at least 1).  
  2. **Automated Checks**: GitHub Actions run lint (Black/ESLint), tests (pytest), security scan (Bandit/Snyk), coverage (>80%). PR blocked if fails.  
  3. **Human Review**: Within 24 hours. Focus on: logic, standards compliance, edge cases, security. Use GitHub comments (suggest mode for fixes).  
  4. **Approval**: Minimum 1 approval from non-author; resolve all conversations.  
  5. **Merge**: Squash-merge with Conventional Commit title; auto-delete branch.  
- **Tools**: GitHub PR templates, Actions workflows, Codecov for coverage reports.  
- **Best Practices**: Be constructive; review own PR first; pair-review complex changes.

## Documentation and Naming Conventions

### Documentation Conventions

- **Inline Docs**: Python docstrings (Google style, enforced by pydocstyle); JS JSDoc. Cover params, returns, examples.  
- **Module Docs**: README.md per module (purpose, usage, examples).  
- **Project Docs**: Root README (overview/install), /docs/ for architecture/plan/schema. Use Markdown + Mermaid for diagrams.  
- **API Docs**: FastAPI auto-Swagger (/docs); comment endpoints.  
- **Change Docs**: Changelog.md (Keep a Changelog format); auto-generate from commits.  
- **Tools**: Sphinx for full API docs if enterprise; MkDocs for site.

### Naming Conventions

Follow 2026 best practices: PEP 8/12 for Python, Airbnb style for JS (Vue). Enforce with linters.

- **Python**:  
  - Variables/Functions: snake_case (e.g., `network_monitor`).  
  - Classes: CamelCase (e.g., `NetworkLearner`).  
  - Constants: UPPER_SNAKE (e.g., `MQTT_BROKER_PORT`).  
  - Files: lowercase_underscore.py.  
  - Imports: Absolute; group stdlib, third-party, local.  

- **JavaScript (Vue)**:  
  - Variables/Functions: camelCase (e.g., `fetchTelemetry`).  
  - Components: PascalCase (e.g., `NetworkTopology.vue`).  
  - Constants: UPPER_SNAKE.  
  - Files: kebab-case.vue for components, camelCase.js for utils.  

- **General**: Descriptive names (e.g., `compute_anomaly_score` > `calc_score`); avoid abbreviations unless standard (e.g., `rl` for RL). Prefix private with `_`.  
- **Enforcement**: Black (Python formatter), Prettier/ESLint (JS); run on pre-commit.

This document ensures consistent, high-quality development. It will be reviewed quarterly and updated as standards evolve.
