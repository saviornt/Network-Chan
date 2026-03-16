# Network-Chan Agile Development Plan

**Project Overview**  
Network-Chan is a local-only, research-grade autonomous SDN management plane for home/lab networks. It combines an edge MLOps controller (Raspberry Pi 5 Appliance) and a central AIOps controller (server/workstation Assistant) into a three-brain, safety-first architecture that performs real-time telemetry ingestion and edge inference (TinyML, Q-Learning, REPTILE meta-learning), global training, policy optimization, and explainable analytics (RL-MAML, GNNs, LLM assistant), persistent incident memory and retrieval (SQLite + FAISS), multi-agent RL where each switch/router can act as an agent, secure command & telemetry transport (MQTT/TLS, RBAC), and an admin interface with chat and optional TTS/STT and personality/emotional expression (VAD model).  

Key operational principles: local-only, fail-open (network functions continue without AI oversight), recoverable (snapshots + rollback), and policy-governed automation.

**Agile Methodology Adoption**  
This plan uses **Scrum** (a subset of Agile) with 2-week sprints, daily standups (15-min check-ins), sprint planning/review/retrospectives, and a prioritized product backlog. We focus on iterative delivery of MVPs (Minimum Viable Products), user stories, and continuous feedback. Tools: GitHub Projects for backlog/kanban, Discord/Slack for standups, Google Docs for retros.  

**Roles**  

- **Product Owner (PO)**: Dave — prioritizes backlog, defines acceptance criteria.  
- **Scrum Master**: Dave or delegate — facilitates ceremonies, removes blockers.  
- **Development Team**: 1–2 developers (cross-functional: Python, ML, networking).  

**Product Vision**  
Deliver a safe, testable, self-remediating SDN control plane that adapts to home/lab networks via edge meta-learning and central RL, with a usable AIOps console for analytics and LLM-grounded advice. Success measured by MTTD/MTTR, false positive rate <3%, and high-precision incident retrieval.

**Epics (High-Level Backlog Groups)**  

1. **Perception & Telemetry**: Ingest and process network data across edge and central.  
2. **Decision & Learning**: Edge lightweight RL/meta-learning + central advanced training.  
3. **Governance & Safety**: Policy enforcement, RBAC, fail-safes.  
4. **Execution & Automation**: Trusted daemon for actions.  
5. **Memory & Retrieval**: Incident storage and RAG for LLM.  
6. **Admin UI & UX**: Dashboard, chat, TTS/STT, emotional/personality layer.  
7. **Integration & Testing**: MQTT, digital twin, HA tie-in, validation.  

**Product Backlog** (Prioritized User Stories)  
Backlog is dynamic — PO reprioritizes each sprint. Stories follow INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable). Estimates in story points (1 = 1/2 day, 3 = 1 day, 5 = 2 days, 8 = 3–4 days).  

| Priority | User Story | Epic | Acceptance Criteria | Points | Dependencies |
|----------|------------|------|---------------------|--------|--------------|
| 1 | As a network admin, I want real-time telemetry ingestion from Omada and local interfaces so I can monitor health. | 1 | Prometheus scrapes Pi metrics; SNMP/psutil data in DB; Grafana shows basic graphs. | 8 | Phase 0 hardware |
| 2 | As an edge controller, I want lightweight TinyML anomaly detection on Pi to flag issues fast. | 2 | TFLite model runs <10 ms; detects test flaps/congestion >90% accuracy. | 5 | 1.1 monitoring |
| 3 | As a policy enforcer, I want RBAC and command whitelists to prevent unauthorized actions. | 3 | FastAPI governance endpoint rejects invalid requests; logs all approvals. | 5 | MQTT basics |
| 4 | As an execution daemon, I want trusted Netmiko/Omada API calls for remediations. | 4 | Daemon executes whitelisted commands; verifies success/timeout. | 5 | 3 governance |
| 5 | As an incident manager, I want FAISS + SQLite storage for episodic records. | 5 | Ingest synthetic incidents; retrieve top-k similar with >80% precision. | 8 | 1 telemetry |
| 6 | As an admin, I want a Vue dashboard with real-time charts and tool buttons. | 6 | Dashboard shows live Pi status/topology; dark mode toggle works. | 8 | MQTT subscriber |
| 7 | As an LLM assistant, I want RAG with FAISS retrieval for grounded responses. | 2 | Query returns relevant incidents; LLM includes confidence/explainability. | 5 | 5 memory |
| 8 | As a user, I want optional TTS/STT voice interface for hands-free queries. | 6 | Browser mic → STT → LLM → TTS response; confirmation for actions. | 5 | Dashboard |
| 9 | As a developer, I want Mininet digital twin for RL training/validation. | 7 | PettingZoo env wraps Mininet; Ray RLlib trains basic agents. | 8 | GNN basics |
| 10 | As a security operator, I want auto-rollback on failure with snapshots. | 3 | Failed change triggers rollback <60 s; logs full audit. | 5 | Execution daemon |
| ... | (Additional stories: multi-agent RL scaling, VAD emotional UX, HA MQTT tie-in, etc.) | ... | ... | ... | ... |

**Backlog Grooming**: Weekly session to refine/prioritize stories, split epics, add details.

## Sprint Planning

**Sprint Duration**: 2 weeks (10 business days).  
**Velocity Target**: 20–30 points per sprint (adjust based on retros).  
**Ceremonies**:  

- **Sprint Planning** (2 hours): Select top backlog items to fit velocity; define tasks/subtasks.  
- **Daily Standup** (15 min): What did I do? What will I do? Blockers? (Slack/Zoom).  
- **Sprint Review** (1 hour): Demo working features; PO accepts/rejects.  
- **Sprint Retrospective** (1 hour): What went well? Improve? Action items.  

### Sprint 1 (Phase 1.1–1.2 prep – 2 weeks)  

- Stories: 1, 2  
- Tasks: Install Prometheus/Grafana, implement basic monitoring, setup TinyML Q-Learning prototype.  
- Output: Running Pi with metrics dashboard, initial anomaly detector.  

### Sprint 2 (Phase 1.2–1.4 – 2 weeks)  

- Stories: 3, 4  
- Tasks: Add automation rules, nmap scheduler, REPTILE integration for thresholds.  
- Output: Pi auto-remediates test scenarios.  

### Sprint 3 (Phase 1.5–1.8 – 2 weeks)  

- Stories: 5, 6  
- Tasks: MQTT pub/sub, tiny FastAPI, simple config page.  
- Output: Pi publishes data; basic on-device UI works.  

### Sprint 4 (Phase 2.1–2.3 – 2 weeks)  

- Stories: 7, 8  
- Tasks: Assistant MQTT subscriber, LangChain agent, Vue dashboard foundation.  
- Output: Dashboard shows live Pi data.  

### Sprint 5 (Phase 2.4–2.7 – 2 weeks)  

- Stories: 9, 10  
- Tasks: Analytics endpoints, voice integration, HA MQTT test.  
- Output: Full assistant with chat & voice.  

**Subsequent Sprints**: Phases 3.1–3.6 (hardening, testing, GTM) — plan dynamically based on velocity & feedback.

## Release Roadmap

- **MVP Release 0.1** (End Phase 1, ~6 weeks): Standalone Pi appliance with monitoring, learning, automation, MQTT — basic AIOps ready.  
- **Release 0.2** (End Phase 2, ~14 weeks): Full assistant integration, dashboard, LLM — usable end-to-end.  
- **Release 1.0** (End Phase 3, ~24 weeks): Polished, tested, packaged — ready for beta users & sales.  

**Release Process**: GitHub releases with changelog, Docker images, Pi SD card guide. CI/CD via GitHub Actions (lint, test, build).

## KPIs & Testing

**KPIs**  

- Mean time to detect (MTTD) of target incidents.  
- Mean time to remediate (MTTR) when allowed to auto-fix.  
- False positive rate for major remediations (goal <3%).  
- Number of rollbacks per 100 actions (trend downwards).  
- LLM response accuracy as judged by admin (qualitative logs).  

**Test Types**  

- Unit tests (all Python modules).  
- Integration tests (MQTT flows, Prometheus scrapes, execution daemon).  
- Simulation tests (Mininet + PettingZoo RL loops).  
- Canary rollout (lab VLAN → limited production).  

**Tools**: Pytest for units/integrations, Mininet for sims, Grafana for KPI dashboards.

## Risks & Mitigations

1. RL policy causes outages — mitigate: policy engine, snapshots/rollback, kill switch, rate limits, staging VLANs.  

2. Compromise of AIOps/MQTT — mitigate: TLS, mutual auth, local-only broker, RBAC, signed commands.  

3. Data privacy leakage — mitigate: redact sensitive data before embedding, offline LLM or local models, encrypted backups.  

4. Device firmware vulnerabilities (Omada/TP-Link) — mitigate: strict patch policy, monitor advisories, isolate lab devices if necessary.  

5. Storage overload on Pi (Prometheus) — mitigate: retention limits, remote storage, downsampling.

## Developer & Operator Checklist

1. Create secure CA and issue certs for Pi, server, broker.  

2. Install Prometheus + node_exporter + snmp_exporter + Grafana.  

3. Harden router (disable unused services, change defaults).  

4. Deploy Mosquitto with TLS + ACL file; test with paho-mqtt clients.  

5. Implement minimal execution daemon and Netmiko command whitelist.  

6. Build FAISS + SQLite ingestion pipeline with redaction step.  

7. Start with ADVISE mode only — log suggested changes for 2–4 weeks before enabling AUTONOMOUS.  

8. Train RL agents in Mininet staging, then test in lab VLAN.
