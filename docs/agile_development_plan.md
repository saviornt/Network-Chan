# Network-Chan Agile Development Plan

**Project name:** Network-Chan  
**Date:** 2026-03-21  
**Version:** 1.1 (consolidated & reset for MVP with both layers)  

## Overview & Guiding Principles

Network-Chan is a solo-developer project building a local-only autonomous SDN management plane with two layers:

- **Network Appliance** (edge on Raspberry Pi 5): real-time telemetry, lightweight TinyML inference/training (TinyGNN + Q-Learning + REPTILE), basic remediation, local config UI.
- **Application** (central on PC/server): global multi-agent GNN-based RL-MAML training (using Q-Learning elements), model quantization/push, persistent RAG, Vue dashboard with centralized config/logs view, LLM assistant.

**Current reality (March 21, 2026)**:

- Shared components (logging, Pydantic settings, asyncio-mqtt, utils) mostly production-ready — needs final review/debug/refactor.
- Docker Pi 5 emulator exists and can install shared package (needs more testing).
- Hardware: TP-Link Omada ER707-M2 + OC220 added to home network.
- Q-Learning implemented in both layers but requires debugging/refinement.
- GitHub Issues auto-create cards in "Network-Chan Project Development" board (columns: To Do → In Progress → Manual QA Testing → Automated QA Testing → Done).

**Development style** (solo-dev optimized):

- 1-week sprints (start Monday, aim close Friday; review/reflect weekend).
- Tasks sized 1–2 days each — break large work into small completable items.
- No story points (overhead for solo work).
- Prioritization: Shared stability → Telemetry ingestion → Appliance core → Application integration → full MVP loop.
- Testing flow: Manual local verification (Manual QA column) first → pytest/MyPy in GitHub Actions (Automated QA column, currently disabled until basic Appliance works).
- Definition of Done (practical solo version):
  - Code works as intended on emulator/real hardware (expected behavior observed).
  - Basic docstrings/comments updated.
  - No errors/crashes in logs.
  - Manual QA passed (tested locally).
  - If applicable: pytest/MyPy passes using GitHub Actions CI.
  - Committed to main (or feature branch merged) with Conventional Commit message.
- Definition of Ready: Clear task description, dependencies resolved (e.g., shared stable), testable locally.

**MVP Definition**:

- Appliance ingests telemetry (Omada/SNMP/psutil), runs basic TinyML inference/remediation, configurable via local UI.
- Application receives data via MQTT, performs central training, pushes quantized model updates back.
- Centralized config/logs viewable/editable via Application dashboard.
- End-to-end loop works locally on your hardware (real Pi 5 + PC) — this is the MVP for beta testing, VC/investor demos, adoption.

## Macro Roadmap Table (Next 9–12 Months)

| Phase / Milestone                  | Target Timeline     | Key Deliverables                                                                 | Status     | Dependencies / Blockers                  |
|------------------------------------|---------------------|----------------------------------------------------------------------------------|------------|------------------------------------------|
| 1. Shared Components Stability     | March–April 2026   | Final review/debug/refactor shared (logging, config, asyncio-mqtt, Pydantic, utils); enable basic CI (lint/type checks) | In Progress | None (current focus)                     |
| 2. Telemetry Ingestion & Appliance Basics | April 2026        | Omada API + SNMP + psutil ingestion → Prometheus publish; basic TinyML inference/remediation loop; local FastAPI+Jinja2 UI + TOTP setup | To Do      | Shared stability                         |
| 3. Appliance Core & Standalone Test| April–May 2026     | Q-Learning/REPTILE small-scale training/debug; policy guardrails; checkpoint safety; Mininet validation; full manual test on real Pi | To Do      | Telemetry working                        |
| 4. Application Basics & Integration| May–June 2026      | Central RL-MAML training (GNN-based); model quantization & MQTT push; SQLite/FAISS ingest; Vue dashboard basics; centralized config/logs view | To Do      | Appliance core                           |
| 5. Communications                  | June 2026          | Bidirectional MQTT (telemetry up, models down); end-to-end testing on real hardware; auto-logout + TOTP enforcement | To Do      | Application basics                       |
| 6. Polish & Alpha Testing          | June–July 2026     | Voice/personality UX, multi-agent coordination, home lab testing & refinement   | To Do      | Communications complete                  |
| 7. MVP & Beta Readiness            | July 2026          | Beta packaging (Docker + Pi guides), demonstration on social media channels (X, Reddit, etc.) | To Do      | Polish & alpha testing                   |
| 8. Post-MVP Release                | July–Aug 2026      | Contact various angel investors and mentors for product release; gather feedback for continuous development (CD) | Future     | MVP achieved                             |
| 9. CI/CD Loop & Future Enhancements| Q3–Q4 2026         | Full CI/CD loop operational; research & implement future enhancements (including PQC cryptography using ML-KEM and ML-DSA); research the use of write-ahead shadow-paging (WASP) for SQLite/FAISS and replacing SQLite with NexusLite | Future     | Post-MVP feedback & funding              |

## Current Sprint Cadence & Workflow

- **Sprint length**: 1 week (target completion Friday).
- **Daily rhythm**: Quick self-check (yesterday? Today? Blockers?) — no formal standups.
- **Backlog management**:
  - GitHub Issues → auto-added to project board.
  - Prioritize in "To Do" column (shared refactor → telemetry → Appliance → Application).
  - Move cards: To Do → In Progress → Manual QA → Automated QA → Done.
- **CI/CD**: GitHub Actions for Ruff/Black lint, MyPy types, pytest — disabled until basic functionality; enable progressively.
- **Branching**: Feature branches from `main` → PR → squash-merge with Conventional Commit.
- **Risks & Blockers**:
  - Log blockers as Issues labeled "blocker".
  - Weekly review: Adjust next week's tasks based on what blocked progress.

## Immediate Next Sprint (Week of March 24–30, 2026 – Suggested)

**Goal**: Finalize shared stability + start telemetry ingestion on emulator/real Pi.

- Review/debug/refactor shared components (logging factory, Pydantic settings, asyncio-mqtt helpers, etc.).
- Enable basic CI (lint + MyPy first; tests later).
- Implement minimal telemetry ingest (Omada API + psutil → Prometheus-compatible publish via MQTT) on emulator.
- Manual test on real hardware (ER707-M2/OC220).
- Add TOTP 2FA setup flow to Appliance local UI.
- Update README + docs with current status.

This plan resets earlier sprint/backlog docs (pre-hardware, team-oriented) to your solo reality: fast cycles, hardware validation, MVP = both layers integrated locally.

Update this doc every 4–6 weeks or after milestones.
