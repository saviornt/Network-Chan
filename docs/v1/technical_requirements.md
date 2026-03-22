# Network-Chan Technical Requirements Documentation

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  
**Version:** 1.0  

## Introduction

This document outlines the comprehensive technical requirements for Network-Chan, a local-only autonomous SDN management plane. It blends the three-brain architecture (Perception, Decision, Governance) from the project proposal with the split design (Appliance on Raspberry Pi 5 for edge perception and lightweight learning, Assistant on PC for central decision-making, governance, and UX). Requirements are categorized into functional (what the system does), non-functional (how well it performs), and technical (specific specs).

Functional requirements are expressed as user stories and use cases for agility. All requirements prioritize local-only operation, fail-open safety, and extensibility for homelab to enterprise scaling.

## Functional Requirements

Functional requirements define what the system must do, focusing on user needs and system behavior. They are derived from the project vision of a self-remediating SDN with AI assistance.

### User Stories (Prioritized)

1. **As a network admin, I want real-time telemetry ingestion from devices so I can monitor health.**  
   - Acceptance: System scrapes metrics (Prometheus, SNMP, psutil) every 10–60s; graph builder (NetworkX) produces topology-aware features for GNN inputs.

2. **As an edge controller, I want lightweight anomaly detection to flag issues fast.**  
   - Acceptance: TinyML model (TFLite/ONNX) runs <10ms on Pi; detects test failures (flaps, rogue DHCP) >95% accuracy.

3. **As a decision engine, I want multi-agent RL to optimize policies across devices.**  
   - Acceptance: PettingZoo env models agents (routers/APs); Ray RLlib trains RL-MAML/GNN policies; adapts via REPTILE on edge.

4. **As a governance engine, I want to enforce safety rules and autonomy modes so actions are controlled.**  
   - Acceptance: FastAPI microservice rejects invalid requests; supports 5 autonomy levels; logs all approvals immutably.

5. **As an execution daemon, I want trusted remediation commands to apply changes safely.**  
   - Acceptance: Executes whitelisted Netmiko/Omada API calls with timeouts; verifies success or rolls back <60s.

6. **As an incident manager, I want persistent memory for retrieval-augmented generation.**  
   - Acceptance: Incidents stored in SQLite + FAISS embeddings; top-k retrieval precision >80% for LLM queries.

7. **As an admin, I want a dashboard with chat and voice for interactive queries.**  
   - Acceptance: Vue 3 UI shows real-time topology/charts; LLM (Ollama + LangChain) processes natural language with RAG; optional TTS/STT confirms actions.

8. **As a researcher, I want a digital twin for simulation to validate RL models.**  
   - Acceptance: Mininet emulates topology; PettingZoo + Ray runs distributed experiments.

9. **As a user, I want optional emotional/personality UX to make interactions engaging.**  
   - Acceptance: VAD scoring maps events to tone; configurable templates (calm-professional, etc.); default off.

10. **As an operator, I want analytics and reports to review performance.**  
    - Acceptance: Pandas trends/forecasting; PDF/CSV exports with MTTD/MTTR KPIs.

### Use Cases

1. **Incident Detection & Remediation**  
   - Actor: System (autonomous).  
   - Pre: Network event occurs (e.g., high latency).  
   - Steps: Perception ingests telemetry → TinyML detects anomaly → Q-Learning selects action → Governance approves (per mode) → Execution applies (Netmiko) → Post-verification → Incident stored (SQLite/FAISS).  
   - Post: MTTR <60s; audit log entry.

2. **User Query via Chat**  
   - Actor: Admin.  
   - Pre: Logged in (TOTP).  
   - Steps: Query "What's causing congestion?" → RAG retrieves incidents (FAISS) → LLM generates response with confidence → Optional VAD/personality tones reply.  
   - Post: Grounded advice; action suggestions require approval.

3. **Policy Update**  
   - Actor: System (central RL).  
   - Pre: New data from edge.  
   - Steps: GNN encodes topology → RL-MAML trains → Model registry (MLflow) versions checkpoint → Push to edge via MQTT.  
   - Post: Edge REPTILE adapts quickly.

4. **Security Audit**  
   - Actor: Scheduler.  
   - Pre: Off-peak time.  
   - Steps: Run nmap → Analyze issues → Publish report (MQTT) → LLM summarizes if queried.  
   - Post: Issues logged; auto-remediate low-risk (e.g., close port) in FULL mode.

## Non-Functional Requirements

Non-functional requirements ensure the system is performant, scalable, secure, and compliant.

### Performance

- Latency: Edge inference <10ms; central LLM response <5s; remediation <60s.  
- Throughput: Handle 100 devices/metrics scrape every 10s; MQTT 1k messages/min.  
- Uptime: Appliance 99.9% (fail-open); Assistant 99% (non-critical).

### Scalability

- Horizontal: Support multi-Pi (via device_id in MQTT); central scales to 10k incidents in FAISS.  
- Vertical: Pi handles 1–50 devices; Assistant to 500+ with better hardware.  
- Growth: Modular plugins for new SDN vendors; Ray for distributed RL training.

### Security

- Authentication: TOTP 2FA on dashboard; MQTT TLS + mutual certs/RBAC.  
- Authorization: Whitelists for commands; autonomy modes limit actions.  
- Data Protection: Redact PII before embedding; local-only storage; encrypted backups.  
- Auditing: Immutable logs for all decisions/actions; signed model checkpoints.

### Compliance

- Privacy: GDPR-like (local-only, no cloud; user consent for voice).  
- Standards: SNMP v3, MQTT 5.0, TLS 1.3.  
- Accessibility: WCAG 2.1 AA for dashboard (voice alt, color contrast).

### Usability

- Intuitive UI: Responsive Vue dashboard; optional voice for hands-free.  
- Learnability: Modes start at ADVISE; docs/guides for setup.

### Reliability

- Fail-Open: Network defaults if AI offline.  
- Recoverability: Rollback <60s; snapshots per change.

### Maintainability

- Modularity: Three-brain split; clean code with types/tests.  
- Extensibility: Plugins for vendors (Netmiko), RL envs (PettingZoo).

## Technical Requirements

### Hardware Specifications

- **Appliance (Pi 5)**: Raspberry Pi 5 (8GB RAM), TP-Link ER707-M2 gateway + OC220 controller, test switches/APs/IoT devices.  
- **Assistant (PC)**: Mini-PC/NUC with ≥16GB RAM, ≥4-core CPU (for Ollama/GNN training).  
- **Networking**: Management VLAN, staging/lab VLAN for testing.

### Software Specifications

- **Languages**: Python 3.12 (core), JavaScript (Vue dashboard).  
- **Frameworks/Libs**:  
  - Monitoring: Prometheus, Grafana, PySNMP, psutil, Netmiko.  
  - ML/RL: TinyML (TensorFlow Lite/ONNX), PyTorch Geometric (GNNs), Ray RLlib, PettingZoo, REPTILE.  
  - Memory: SQLite, FAISS.  
  - Messaging: paho-mqtt, Mosquitto.  
  - Assistant: Ollama, LangChain, FastAPI, Vue 3 + Vite.  
  - Other: Numba (JIT), Pandas (analytics), ReportLab (PDF).  
- **Tools**: Mininet (simulation), MLflow (registry), Optuna (HPO).

### Protocols and Networking Requirements

- **Telemetry**: SNMP v3, MQTT 5.0/TLS with ACLs.  
- **APIs**: FastAPI (REST for governance/UI).  
- **Networking**: Local-only (no public exposure); mutual TLS certs; rate limits on changes.  
- **Standards**: WCAG 2.1 (UI), GDPR-like privacy (redaction/consent).

This requirements documentation provides a blueprint for development, ensuring alignment with the project vision and scope. It will be refined iteratively via Agile backlog grooming.
