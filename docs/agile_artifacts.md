# Network-Chan Agile Artifacts Document

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  
**Version:** 1.0  

## Introduction

This Agile Artifacts Document captures the key Agile elements for Network-Chan, including the product backlog, epics, user stories, sprints, Definition of Done (DoD), and Definition of Ready (DoR). It serves as a living reference for the development team, Product Owner, and stakeholders, ensuring alignment with the project's vision of a safe, autonomous SDN management plane with edge MLOps (Appliance on Pi 5) and central AIOps (Assistant on PC).

Artifacts are managed in GitHub Projects (Kanban board) for visualization, with issues for stories/tasks. The backlog is prioritized by business value, risk, and dependencies. Epics group related stories into themes. Sprints are 2-week cycles, with planning/review/retros to adapt.

All artifacts emphasize safety (e.g., governance in stories), local-only operation, and measurable KPIs (MTTD/MTTR, false positives <3%).

## Product Backlog

The product backlog is a prioritized list of everything needed to deliver the vision, including features, fixes, and tech debt. It's groomed weekly by the Product Owner. Items are estimated in story points (Fibonacci: 1, 2, 3, 5, 8, 13) during planning.

### Prioritized Backlog Items (Top 20 – Dynamic; Full in GitHub)

| Priority | Type | Item ID | Description (User Story/Epic/Task) | Epic | Points | Dependencies |
|----------|------|---------|-------------------------------------|------|--------|--------------|
| 1 | Epic | EP-001 | Perception & Telemetry Ingest | Perception | — | — |
| 2 | Story | US-001 | As a system, I want real-time telemetry from Omada/psutil/SNMP so I can build features. | EP-001 | 8 | Hardware setup |
| 3 | Story | US-002 | As an edge controller, I want TinyML anomaly detection on Pi to flag issues. | EP-001 | 5 | US-001 |
| 4 | Epic | EP-002 | Decision & Learning Systems | Decision | — | EP-001 |
| 5 | Story | US-003 | As an edge RL agent, I want Q-Learning for action selection on Pi. | EP-002 | 5 | US-002 |
| 6 | Story | US-004 | As a meta-learner, I want REPTILE for model adaptation on Pi. | EP-002 | 8 | US-003 |
| 7 | Story | US-005 | As a central trainer, I want GNNs (PyG) for topology reasoning on Assistant. | EP-002 | 8 | EP-001 |
| 8 | Story | US-006 | As a central RL system, I want RL-MAML training with Ray RLlib. | EP-002 | 13 | US-005 |
| 9 | Epic | EP-003 | Governance & Safety | Governance | — | EP-002 |
| 10 | Story | US-007 | As a policy engine, I want RBAC and whitelists to control actions. | EP-003 | 5 | MQTT basics |
| 11 | Story | US-008 | As a governance system, I want autonomy modes (5 levels) to graduated control. | EP-003 | 5 | US-007 |
| 12 | Epic | EP-004 | Execution & Automation | Execution | — | EP-003 |
| 13 | Story | US-009 | As an execution daemon, I want trusted Netmiko/Omada calls for remediation. | EP-004 | 5 | US-008 |
| 14 | Epic | EP-005 | Memory & Retrieval | Memory | — | EP-001 |
| 15 | Story | US-010 | As an incident manager, I want SQLite + FAISS for episodic storage/retrieval. | EP-005 | 8 | Telemetry ingest |
| 16 | Epic | EP-006 | Admin UI & UX | UI | — | EP-005 |
| 17 | Story | US-011 | As an admin, I want a Vue dashboard with real-time charts and tools. | EP-006 | 8 | MQTT subscriber |
| 18 | Story | US-012 | As an admin, I want chat UI with RAG LLM queries. | EP-006 | 5 | US-010 |
| 19 | Story | US-013 | As an admin, I want optional TTS/STT voice interface. | EP-006 | 5 | US-012 |
| 20 | Story | US-014 | As an admin, I want VAD emotional expression and personality templates. | EP-006 | 3 | US-012 |

**Backlog Grooming**: Weekly; add details/estimates during sprint planning. Tech debt stories (e.g., "Refactor MQTT handler") prioritized at 10–20% per sprint.

## Sprints

Sprints are 2-week cycles (10 business days) with a velocity target of 20–30 points (adjusted via retros). Each sprint includes planning, daily standups, review, and retrospective.

- **Sprint Structure**:  
  - **Planning (2 hours)**: Select/break down stories from backlog; define tasks.  
  - **Daily Standup (15 min)**: Progress/blockers (Slack/Zoom).  
  - **Review (1 hour)**: Demo to PO/stakeholders; accept completed stories.  
  - **Retrospective (1 hour)**: What went well/improve/actions (e.g., "Improve Q-Learning convergence with better rewards").  

- **Example Sprint 1 Backlog (Phase 1.1–1.2)**: US-001 (8pts), US-002 (5pts), US-003 (5pts), US-004 (8pts). Total: 26pts.  
- **Sprint Tracking**: GitHub Projects board (To Do/In Progress/Review/Done); burndown chart in retros.

## Epics

Epics are large bodies of work grouping related stories. They span multiple sprints and are broken down progressively.

- **EP-001: Perception & Telemetry** (Q1–Q2): Ingest data, build graphs — foundation for all learning. Stories: US-001, US-002.  
- **EP-002: Decision & Learning** (Q2–Q4): Edge RL/meta + central GNN/RL-MAML. Stories: US-003 to US-006.  
- **EP-003: Governance & Safety** (Q2–Q3): Policy engine, modes, audits. Stories: US-007, US-008, US-010.  
- **EP-004: Execution & Automation** (Q2): Trusted daemon for actions. Stories: US-009.  
- **EP-005: Memory & Retrieval** (Q3): FAISS + SQLite for incidents/RAG. Stories: US-010.  
- **EP-006: Admin UI & UX** (Q3–Q4): Vue dashboard, chat, voice, VAD/personality. Stories: US-011 to US-014.  
- **EP-007: Integration & Testing** (Ongoing): MQTT, Mininet, HA tie-in. Stories: Simulation/validation.

Epics are tracked in GitHub Milestones, with progress % based on completed stories.

## Definition of Done (DoD)

DoD ensures stories are complete and shippable. A story is "Done" only if:

- Code written, reviewed (at least 1 approval), merged to main.  
- Unit/integration tests pass (>80% coverage; pytest/Jest).  
- Functional acceptance criteria met (PO verified).  
- Documentation updated (inline docstrings, README if user-facing).  
- CI pipeline passes (lint, security scan, build).  
- No new bugs introduced (regression tests pass).  
- Deployed to test env (staging VLAN); manual smoke test ok.  
- Changelog entry added (Conventional Commits).  

Enforced via PR checklists in GitHub.

## Definition of Ready (DoR)

DoR ensures stories are prepared for sprint work. A story is "Ready" if:

- Clear description + acceptance criteria (AC) defined.  
- Dependencies resolved (e.g., prior stories done).  
- Estimated in points (team consensus).  
- Prioritized by PO.  
- Risks identified (e.g., "Needs Mininet setup").  
- Testable (AC include verifiable outcomes).  
- Sized small (≤8 points; split if larger).  

Checked during grooming/planning; unready stories stay in backlog.

This document is living—update during retrospectives. It ensures Agile execution delivers value iteratively while maintaining quality.
