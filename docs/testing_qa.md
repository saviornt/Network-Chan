# Network-Chan Test Plans & QA Documentation

**Project name:** Network-Chan  
**Date:** 2026-03-21  
**Version:** 1.1 (updated for IDE-first + GitHub + Docker emulation testing flow)

## Introduction

This document defines the current testing and QA approach for Network-Chan, optimized for solo development using Docker containers for testing emulators.
The strategy is pragmatic and staged:

- IDE real-time validation during coding
- Snippet-based manual checks
- GitHub Actions automated validation (lint, type check, tests, documentation generation)
- Docker-based live integration testing
- Extended real-hardware testing once Pi 5 arrives

Goal: Confirm the system "works as intended with no errors" on emulator first, then scale to real hardware. MVP priority: telemetry ingestion, TinyML inference/remediation, MQTT bidirectional loop, TOTP setup.

## Test Strategy

- **Approach**: Emulator-first; manual checks early, automation on push, live Docker validation per major feature.
- **Scope**: Network Appliance (telemetry, inference, remediation, local UI), Application (central training, model push, dashboard), MQTT bridge, end-to-end flows.
- **Environments**:
  - **Primary (current)**: Docker Pi 5 emulator (for development and integration testing).
  - **Secondary (future)**: Physical Raspberry Pi 5 + TP-Link Omada ER707-M2/OC220 home network (for extended 24/7 testing).
  - **Simulation**: Mininet (for RL policy validation post-MVP).
- **Test Data**: Synthetic incidents via scripts; mock Omada API responses.
- **Metrics (MVP focus)**:
  - Telemetry ingestion reliability (no drops).
  - Edge inference latency (<10ms target on emulator).
  - End-to-end MQTT round-trip (telemetry up → model down).
  - Code coverage (>80% target on tested paths).
  - No crashes/errors in logs during Docker/live testing.

## Test Types & Execution Flow

1. **IDE Real-Time Checks (During Coding)**
   - Pylance/VS Code: Real-time type checking, error highlighting, quick hover docs.
   - Ruff: Inline linting, formatting and type suggestions (fast local feedback to catch issues early).
   - Goal: Catch syntax, type, and style issues before committing.

2. **Snippet-Based Manual Checks**
   - Create small, focused code snippets or test scripts to verify individual pieces.
   - Run directly in IDE or terminal (e.g., `python -m my_module.test_snippet`).
   - Examples:
     - Test MQTT publish/subscribe loop with mock data.
     - Run TinyML inference on synthetic feature vector.
     - Verify TOTP setup modal and auth flow.
   - If snippet fails → fix immediately.
   - If passes → commit and push.

3. **GitHub Actions Automated Validation (On Push/PR)**
   - Workflow triggers on push/PR to main/feature branches.
   - Steps (in order):
     - Ruff lint/format/type checks.
     - pytest unit/integration tests (if present for the module).
     - MyPy strict type checking.
     - If all prior steps pass → build MkDocs site (Material theme + mkdocstrings) and auto-publish to GitHub Pages.
   - Pass criteria: All checks green, docs site builds cleanly.
   - Only after this step succeeds → proceed to live Docker testing.

4. **Live Docker Integration Testing (Per Major Feature)**
   - Once GitHub Actions passes and major feature is complete:
     - Pull latest repo.
     - Spin up two containers:
       - Emulator container (Network Appliance simulation).
       - Application container (central layer).
     - Run full end-to-end flows (telemetry ingestion → MQTT → central processing → model push → remediation).
     - Verify logs, dashboard, UI, no errors.
   - Pass criteria: Feature works end-to-end in Docker environment.

5. **Extended Real-Hardware Testing (Post-Physical Pi 5 Acquisition)**
   - Deploy to actual Raspberry Pi 5 + Omada hardware.
   - Run 24/7 in home network while developing other features.
   - Monitor stability, logs, performance over days/weeks.
   - Use as primary validation environment for alpha testing.

## Bug Tracking Process

- **Current (development phase)**: Use "Network-Chan Project Development" board.
  - Issues auto-added → To Do → In Progress → Manual QA → Automated QA → Done.
- **Post-MVP (alpha testing on home network)**: Separate board "Network-Chan Issues and Bug Reports".
  - For user-reported bugs, alpha feedback, production-like issues.
  - Process:
    1. Open Issue with template (title: [Bug] Description; labels: bug, priority, alpha-testing).
    2. Auto-added to new board.
    3. Triage: Move to In Progress → assign self.
    4. Fix in branch → PR → GitHub Actions → Docker validation.
    5. Merge → move to Done.

## Current Priorities (March 2026)

1. IDE (Pylance, Ruff) and snippet checks for shared components + telemetry ingestion on emulator.
2. Get GitHub Actions fully passing (Ruff/pytest/MyPy + MkDocs build/deploy).
3. Docker integration testing of major features (emulator + Application containers).
4. Add unit tests for TinyML/TinyGNN/Q-Learning/REPTILE paths.
5. Transition to real Pi 5 hardware testing as soon as physical device is obtained.

This plan will evolve as we add real hardware and alpha testing.
