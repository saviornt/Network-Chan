# Network-Chan Project Proposal & General Design Document

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  

---

Executive Summary

Network-Chan is a local-only, research-grade autonomous SDN management plane for home/lab networks. It combines an edge MLOps controller (Raspberry Pi 5 Appliance) and a central AIOps controller (server/workstation Assistant) into a three-brain, safety-first architecture that performs real-time telemetry ingestion and edge inference (TinyML, Q-Learning, REPTILE meta-learning), global training, policy optimization, and explainable analytics (RL-MAML, GNNs, LLM assistant), persistent incident memory and retrieval (SQLite + FAISS), multi-agent RL where each switch/router can act as an agent, secure command & telemetry transport (MQTT/TLS, RBAC), and an admin interface with chat and optional TTS/STT and personality / emotional expression (VAD model).

Key operational principles: local-only, fail-open (network functions continue without AI oversight), recoverable (snapshots + rollback), and policy-governed automation.

---

## Goals & Success Criteria

### Primary Goals

Build a safe, testable autonomous SDN control plane that can learn and self-remediate in a real home network.

Enable multi-agent RL across devices (routing/switching/APs) while keeping strong safety guardrails.

Provide a usable AIOps admin console with analytics, reporting, and an LLM assistant that uses past incidents for grounded advice.

### Secondary Goals

Democratize advanced AIOps for homelabs by making it affordable and easy to deploy on commodity hardware.

Support research extensibility with simulation tools and modular code for experiments in edge RL and AIOps.

Create an engaging admin experience with optional personality/emotional UX to make interactions fun for hobbyists while maintaining professional modes for businesses.

## Success Criteria

Edge controller can detect & remediate common failures (e.g., interface flaps, rogue DHCP) in simulated runs and in lab VLAN with no service-disrupting false positives >95% of experiments.

Safe rollback restores network config automatically <60 seconds after a failed change.

FAISS-backed incident retrieval returns relevant past cases with high precision for admin LLM queries.

LLM assistant never executes commands without policy engine approval; natural-language requests are mapped to structured actions and logged for audit.

Appliance achieves MTTD <10s, MTTR <60s in tests, with false positive rate <3% for remediations.

LLM response accuracy >90% as judged by admin (qualitative + confidence scoring in outputs).

---

High-Level Architecture (Three-Brain Model)

The system architecture follows a three-brain model to separate perception (state), decision (policy), and governance (safety & intent) across components for independent observation, debugging, and retraction.

```text
+----------------------------+
|    Admin / UI      |
| Chat / TTS / STT   |
+----------------------------+
|       AIOps Server         |
|  (Decision + Governance)   |
+----------------------------+
| model + GNN training | policy engine |
+----------------------------+
|         Messaging / Broker (MQTT/TLS)         |
+----------------------------+
|  MLOps Edge (Pi)    |   | Execution Daemon|
|  (Perception + RL)  |   | (trusted, small)|
+----------------------------+
|       Switches / Routers / APs / IoT Devices       |
```

The MLOps Edge (Appliance on Pi 5) is the Perception Brain, handling fast-loop telemetry and lightweight reinforced meta-learning (TinyML + Q-Learning + REPTILE for anomaly, congestion prediction, action selection). It publishes telemetry and learned parameters via MQTT but operates autonomously.

The AIOps Server (Assistant on PC) is the Decision Brain (central RL/GNN/LLM) + Governance Brain, handling global training, LLM with RAG, VAD emotional expression, and the policy engine. It subscribes to Pi telemetry for context and sends approved commands back.

Key idea: split perception (state), decision (policy), and governance (safety & intent) across separate components so each can be observed, debugged, and retracted independently. The Appliance is standalone for standalone use, with the Assistant enhancing it for richer UX and training.

## Network Topology

The Appliance (Pi 5) deploys on the management VLAN, connecting to the Omada controller (OC220) via Ethernet. The Assistant (PC) connects to the same LAN, subscribing to MQTT for data flows. Staging VLAN for experiments (Mininet sims).

### Home Lab Topology

- Modem → ER707 Gateway → Switch/APs (5–10 devices).  
- Appliance on management VLAN (192.168.100.0/24); Assistant on LAN.  

### Small Business Topology

- Firewall → ER707 Gateway → Core Switch → Multiple APs (20–50 devices).  
- Appliance on management net (10.0.100.0/24); Assistant on server.  

### Enterprise Topology

- Core Router → Layer 3 Switches → Distributed APs (100+ devices).  
- Appliance per site on management (10.0.100.0/24); Assistant on VM cluster.  

## Deployment Setup

- **Appliance**: Raspberry Pi 5 (8GB RAM), TP-Link ER707-M2 + OC220.  
- **Assistant**: Mini-PC with ≥16GB RAM, ≥4-core CPU.  
- **On-Premises Deployment**: Docker Compose for Assistant (Grafana, Prometheus, Mosquitto); systemd for Appliance.  

## Integration Points

- MQTT Broker: Central pub/sub.  
- Prometheus/Grafana: Scraping on Appliance; dashboards embedded in Vue.  
- Mininet/PettingZoo: Simulation API for RL training.  
- Home Assistant: MQTT sensors/commands.

## Choice of Frameworks, Libraries, and Major Technologies

- Monitoring/Telemetry: Prometheus (scraping), Grafana (dashboards), PySNMP (polling), psutil (metrics). *Rationale*: Industry standard for time-series; Prometheus for Pi export.  
- ML/RL: TinyML (TFLite/ONNX for edge), PyTorch Geometric (GNNs), Ray RLlib (training), PettingZoo (agents), REPTILE (meta-learning). *Rationale*: TFLite <10ms on Pi; Ray scales central.  
- Memory/Retrieval: SQLite (DB), FAISS (vectors). *Rationale*: Embedded/low-overhead; FAISS for fast RAG.  
- Messaging: paho-mqtt (client), Mosquitto (broker). *Rationale*: Secure, low-latency pub/sub.  
- Governance/Execution: FastAPI (microservice), Netmiko (CLI). *Rationale*: Async for efficiency; Netmiko multi-vendor.  
- LLM/RAG: Ollama (models), LangChain (toolchains). *Rationale*: Local/offline; LangChain for RAG.  
- UI/UX: Vue 3 + Vite (dashboard), Web Speech API (voice). *Rationale*: Reactive, lightweight frontend.  
- Simulation/MLOps: Mininet (emulation), MLflow (registry), Optuna (HPO). *Rationale*: Safe testing; versioning for RL models.

This SAD provides a blueprint for implementation, with flexibility for Agile iteration. It will be updated during Phase 1 with detailed configs.
