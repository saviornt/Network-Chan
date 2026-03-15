# Sprint Plan for Network-Chan

This document outlines the sprints for the project, following the Agile Development Plan (2-week cycles, daily standups, planning/review/retros). Sprints are tied to the product roadmap phases (e.g., Sprint 0–2 for Foundations/Phase 1). Dates are approximate based on current timeline (start: March 15, 2026). Adjust as needed in retros.

Sprints focus on iterative delivery toward Appliance MVP (standalone edge by end Sprint 3/Phase 2). Backlog items from `backlog.md`; measure velocity (points completed) and KPIs (e.g., code coverage >80%).

## Sprint 0: Offline Foundations (March 15–16, 2026)

**Goal**: Set up monorepo structure, stubs, and docs while waiting for internet/hardware. Build habits (types/async/Numba) without runs.

**Duration**: Short prep sprint (1–2 days, offline-focused).

**Stories/Tasks (Total: 10 points)**:

- TK-001: Add type annotations and async stubs to shared utils (2 points).
- US-001 (partial): Stub telemetry ingestion with mocks (3 points).
- TK-002: Expand docs (backlog, architecture, risks) with tables/diagrams (3 points).
- TK-003: Commit atomic stubs for anomaly detection (2 points).

**Ceremonies**:

- **Planning**: Review backlog; prioritize offline mocks.
- **Daily Standups**: Self-notes (e.g., "Yesterday: Added db stub; Today: Telemetry; Blockers: None").
- **Review**: Check commits; all stubs typed/async.
- **Retro**: What went well: Quick stubs. Improve: Add more tests early. Action: Install pytest post-internet.

**Velocity Target**: 10 points (light sprint).

## Sprint 1: Post-Internet Foundations (March 17–30, 2026)

**Goal**: Sync repo, install deps, run/test stubs, complete Phase 0 (setup) and start Phase 1 (Perception).

**Duration**: 2 weeks.

**Stories/Tasks (Total: 15 points)**:

- TK-004: Push repo to GitHub, setup Projects board (2 points).
- TK-005: Install base deps (numpy, numba, pytest); run MyPy checks (2 points).
- US-001: Implement async telemetry ingestion with mocks (full) (8 points).
- US-002: Stub lightweight anomaly detection with Numba (3 points).

**Ceremonies**:

- **Planning**: Groom backlog; assign points.
- **Daily Standups**: 15-min (notes or Discord once setup).
- **Review**: Demo running stubs; coverage >50%.
- **Retro**: Evaluate velocity; adjust for hardware arrival (March 19).

**Velocity Target**: 15 points; Risks: Dep install issues (mitigate: venv checks).

## Sprint 2: Perception & Edge Basics (March 31–April 13, 2026)

**Goal**: Complete Phase 1 (telemetry/graph builder); integrate with arriving hardware (Pi/TP-Link); basic tests.

**Duration**: 2 weeks.

**Stories/Tasks (Total: 20 points)**:

- US-001 (integration): Connect telemetry to real Omada/psutil on Pi (5 points). Dep: Hardware.
- US-006: Build NetworkX graph builder with async processing (5 points).
- TK-006: Add unit tests for telemetry (pytest async) (3 points).
- US-002: Expand anomaly detection to TinyML stub (7 points).

**Ceremonies**:

- **Planning**: Prioritize hardware integration.
- **Daily Standups**: Track blockers (e.g., Pi setup).
- **Review**: Demo metrics ingestion on Pi; MTTD sim <60s.
- **Retro**: Hardware learnings; improve test coverage.

**Velocity Target**: 20 points; Risks: Setup delays (mitigate: Guides in docs).

## Sprint 3: Edge Learning & MVP (April 14–27, 2026)

**Goal**: Phase 2 (Decision on edge); implement Q-Learning/REPTILE/TinyGNN; achieve Appliance MVP (standalone autonomy).

**Duration**: 2 weeks.

**Stories/Tasks (Total: 25 points)**:

- US-003: Q-Learning agent with async updates (5 points).
- US-004: REPTILE meta-learning loop (8 points).
- US-007: Integrate TinyGNN (quantized GCN) for topology (8 points).
- TK-007: System tests with Mininet (4 points).

**Ceremonies**:

- **Planning**: Focus on MVP KPIs.
- **Daily Standups**: Monitor perf on Pi.
- **Review**: Demo self-remediation in staging VLAN.
- **Retro**: MVP readiness; plan Assistant parallel.

**Velocity Target**: 25 points; Risks: RL convergence (mitigate: Mocks/Numba).

## Future Sprints (Post-MVP, Q2–Q4 2026)

- **Sprint 4**: Governance & Assistant Integration (e.g., MQTT sync, policy engine; 30 points).
- **Sprint 5**: Multi-Agent RL & UI (e.g., GNN pushes, Vue dashboard; 35 points).
- **Sprint 6**: Testing/Validation (full QA, beta deploy; 25 points).
- Adjust based on retros/roadmap (e.g., Q3: Multi-Pi scaling).

Overall Plan Notes:

- Tools: GitHub for tracking; update this file in retros.
- Metrics: Track velocity, burndown; aim for sustainable pace.
- Blockers: Hardware/internet—use offline mocks as buffer.

Last Groomed: March 15, 2026.
