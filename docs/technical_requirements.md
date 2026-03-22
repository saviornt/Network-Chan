# Network-Chan Technical Requirements Documentation

**Project name:** Network-Chan  
**Date:** 2026-03-21  
**Version:** 1.1

## Introduction

This document defines the technical requirements for Network-Chan, a local-only autonomous SDN management plane. It covers core capabilities (what the system must do), quality & operational attributes (how well it must perform), and technical specifications (hardware/software/protocols), aligned with the current split architecture:

- **Network Appliance** — lightweight edge MLOps controller (Raspberry Pi 5 reference) for real-time telemetry, small-scale TinyML inference/training, and policy-approved remediation.
- **Application** — central AIOps component (PC/server) for global training, model distribution, persistent RAG, governance, and user interfaces.

All processing is strictly local — no cloud, no external APIs, no recurring third-party costs.

## Core Capabilities

### User Stories (Prioritized)

1. **As a system, ingest real-time telemetry** from Omada API, SNMP v3, Netmiko, psutil so ML features can be built.
   - Acceptance: Metrics scraped every 10–60s; published via MQTT; stored locally (SQLite/FAISS).

2. **As the Network Appliance, run lightweight inference** for anomaly detection and remediation.
   - Acceptance: TinyML (TinyGNN, Q-Learning and REPTILE) runs <10ms on Pi; small-scale local updates; detects common issues >95% in lab.

3. **As the Application, perform global training** and push quantized model updates to Appliance.
   - Acceptance: multi-agent, GNN-based RL-MAML using Q-Learning elements; quantized models pushed via MQTT; Appliance applies minor local updates between pushes.

4. **As an admin, configure and monitor** both layers securely.
   - Acceptance: Appliance local FastAPI+Jinja2 UI for setup/logs; Application Vue dashboard for centralized config/logs view; mandatory TOTP 2FA on first login.

5. **As the system, enforce safety** and autonomy.
   - Acceptance: Policy engine validates actions; configurable autonomy levels; atomic changes + rollback <60s.

6. **As a researcher/user, extend/extend** the system.
   - Acceptance: Modular (PettingZoo envs, Mininet sims); open-source core on GitHub.

### Standalone Capability

The Network Appliance must operate fully standalone (no Application required):

- Slower adaptation (no central training pushes)
- Basic remediation and local UI sufficient for core functionality

## Quality & Operational Attributes

- **Privacy & Security** — Local-only; TLS 1.3 on MQTT; forced TOTP 2FA setup; future PQC (ML-KEM/ML-DSA) planned.
- **Reliability** — Fail-open; recoverable snapshots/rollback; 24/7 operation on Pi 5.
- **Performance** — Edge inference <10ms; telemetry ingestion <60s latency; Application training cycles reasonable on ≥16GB PC.
- **Usability** — Intuitive setup (TOTP during onboarding); WCAG 2.1 AA dashboard; optional voice/personality UX.
- **Extensibility** — Modular plugins (Netmiko for vendors); Mininet/PettingZoo for research.

## Technical Specifications

### Hardware

- **Network Appliance** — Raspberry Pi 5 (8GB recommended); TP-Link Omada ER707-M2 + OC220 as reference SDN.
- **Application** — Mini-PC/NUC/PC with ≥16GB RAM, ≥4-core CPU (for Ray RLlib/Ollama).
- **Network** — Management VLAN recommended; staging VLAN for testing.

### Software & Languages

- **Core Language**: Python 3.12+
- **Frameworks/Libraries**:
  - Telemetry/Monitoring: Prometheus, Grafana, PySNMP, psutil, Netmiko
  - Edge ML: TinyML (ONNX/TFLite), TinyGNN, Q-Learning + REPTILE (Numba accelerated)
  - Central ML: Ray RLlib, PettingZoo, PyTorch Geometric
  - Storage: SQLite (sqlalchemy) + FAISS (both layers)
  - Messaging: asyncio-mqtt + Mosquitto (TLS)
  - Governance/UI: FastAPI (backend), Vue 3 + Vite (Application dashboard), Jinja2 (Appliance config UI), pyotp (TOTP)
  - LLM/RAG: Ollama + LangChain
  - Other: Pydantic v2 (validation/settings), Numba (JIT), ReportLab (PDF exports)

### Protocols & Standards

- **Telemetry**: SNMP v3, MQTT 5.0/TLS, Omada Northbound API
- **Security**: TLS 1.3, TOTP 2FA (mandatory setup), future ML-KEM/ML-DSA PQC
- **Accessibility**: WCAG 2.1 AA (dashboard)
- **Simulation**: Mininet

### KPIs & Testing Priorities

- Code coverage (>80% target)
- Telemetry/metrics ingestion reliability
- Edge inference latency (<10ms)
- MTTD/MTTR simulation (<60s)
- False positive rate (<3%)

This document is the current blueprint — it will be refined iteratively as development progresses.
