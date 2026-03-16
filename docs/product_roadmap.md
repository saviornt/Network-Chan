# Network-Chan Product Roadmap

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  
**Version:** 1.0  

## Executive Summary

This Product Roadmap outlines the high-level timeline for Network-Chan's features, releases, and market milestones, linking them to strategic goals like building a safe autonomous SDN control plane, enabling multi-agent RL, and providing usable AIOps admin tools. It serves as a guide for investors, stakeholders, and the development team, emphasizing iterative Agile delivery.

The roadmap is divided into phases tied to quarterly releases, with flexibility for feedback-driven adjustments. Strategic goals are mapped to steps: e.g., perception/telemetry in early phases supports MTTD/MTTR KPIs, while governance/safety ensures low false positives. Market milestones focus on beta testing, crowdfunding, and commercialization to capitalize on the AIOps market's 20%+ CAGR.

Expected outcomes: MVP in Q2 2026, full 1.0 in Q4 2026, with 500–1,000 units sold in Year 1 via freemium model (free Appliance core, premium Assistant features).

## Strategic Goals and Link to Development Steps

Network-Chan's roadmap is anchored in three core goals, with practical steps ensuring alignment:

1. **Build Safe Autonomous SDN Control Plane** (Goal: MTTD/MTTR <60s, false positives <3%)  
   - Steps: Phase 1 focus on edge perception/learning; Phase 2 governance; Phase 3 validation.  
   - Link: Early monitoring (Q2) → RL automation (Q3) → multi-agent scaling (Q4).

2. **Enable Multi-Agent RL Across Devices** (Goal: High-precision remediation in lab VLANs)  
   - Steps: Phase 2 edge RL prototype; Phase 4 full GNN/RL-MAML training.  
   - Link: Mininet sims (Q2) → PettingZoo agents (Q3) → staging VLAN rollout (Q4).

3. **Provide Usable AIOps Console** (Goal: LLM accuracy >90%, intuitive UX)  
   - Steps: Phase 3 memory/LLM; Phase 2 dashboard.  
   - Link: FAISS RAG (Q3) → Vue chat/UI (Q3) → VAD/personality polish (Q4).

## High-Level Timeline

The timeline assumes a part-time team (1–2 developers), starting March 2026. Phases overlap slightly for parallel work. Total to 1.0: 6–9 months.

| Quarter | Phase / Focus | Key Features & Activities | Releases & Milestones | Risks / Dependencies |
|---------|---------------|---------------------------|-----------------------|----------------------|
| Q1 2026 (Mar–May) | Phase 0–1: Foundations + Perception | Hardware setup, Prometheus + Grafana install, SNMP/psutil telemetry, graph builder (NetworkX), SQLite + FAISS prototype, basic exporters. | Internal Alpha 0.1: Running Pi with metrics dashboard. | Low risk; dep: Pi 5 + ER707 hardware. |
| Q2 2026 (Jun–Aug) | Phase 2: Edge RL & TinyML | TinyML anomaly detector (TFLite/ONNX), Q-Learning agent prototype, REPTILE meta-loop, snapshots/rollback (Netmiko), Mosquitto MQTT with TLS. | MVP Release 0.2: Standalone Appliance with monitoring/learning/automation. Beta testing starts (5–10 users). | Medium risk (RL convergence); dep: Mininet sims. |
| Q3 2026 (Sep–Nov) | Phase 3: Memory, FAISS & LLM Assistant | Incident ingestion → FAISS + SQLite, basic chat UI with RAG/LLM (Ollama), VAD scoring + personality templates, Vue dashboard foundation. | Release 0.3: Assistant integration, full dashboard, voice prototype. Kickstarter campaign launch. | Medium risk (LLM accuracy); dep: FAISS retrieval tuning. |
| Q4 2026 (Dec–Feb 2027) | Phase 4: Multi-Agent RL + GNNs | PettingZoo env + Mininet integration, GNN-based agents (PyG), RL-MAML training (Ray RLlib), staging VLAN validation. | Release 1.0: Full system with multi-agent RL, governance engine. Market launch (Etsy, Pi stores). | High risk (policy safety); dep: Lab VLAN setup. |
| Q1 2027+ (Ongoing) | Phase 5: Hardening & Polish | Security audit, CI/CD, TTS/STT (if desired), user docs, MLflow model registry, Optuna HPO. | Release 1.1+: Premium features (custom personalities, enterprise integrations). Scale to MSPs. | Low risk; dep: Beta feedback. |

## Features & Releases Roadmap

Releases are tied to Agile sprints (2-week cycles), with MVPs every quarter. Features prioritized by value (e.g., core monitoring first).

### Release 0.1 – Alpha (Q1 2026 End)

- Features: Telemetry ingestion, basic Prometheus/Grafana dashboards, SQLite logging.
- Strategic Link: Builds perception brain for MTTD goals.
- Market Milestone: Internal demo; share architecture docs on GitHub.

### Release 0.2 – MVP (Q2 2026 End)

- Features: Edge TinyML anomaly detection, Q-Learning + REPTILE hybrid for predictions, automation engine, security auditing scheduler, MQTT pub/sub.
- Strategic Link: Enables safe remediation and multi-agent prototypes.
- Market Milestone: Beta program launch (r/homelab recruitment); Appliance kit prototype ready for testing.

### Release 0.3 – Beta (Q3 2026 End)

- Features: FAISS RAG for LLM, VAD emotional UX, Vue dashboard with charts/topology, analytics tools, TOTP 2FA, voice interface.
- Strategic Link: Provides grounded LLM advice and usable console.
- Market Milestone: Kickstarter campaign; free Appliance downloads + premium Assistant beta.

### Release 1.0 – GA (Q4 2026 End)

- Features: Full GNN + RL-MAML training, multi-agent PettingZoo env, policy engine with autonomy modes, Mininet sims, MLflow registry.
- Strategic Link: Achieves high-precision multi-agent RL and <3% false positives.
- Market Milestone: Official launch (Etsy/Pi stores); freemium pricing ($0 Appliance core, $5/month Assistant premium); Phoenix tech meetup demo.

### Post-1.0 Roadmap (2027+)

- **Q1 2027**: Enterprise extensions (multi-site federation, custom agents).  
- **Q2 2027**: Mobile app proxy via HA.  
- **Ongoing**: Community contributions (plugins for more SDN vendors).  
- Market Milestones: 1,000 units sold; partnerships (e.g., TP-Link); conference talks.

## Linking Strategic Goals to Development Steps

- **Goal 1 (Safe Autonomous SDN)**: Phases 1–2 (edge RL + governance) → Q2 MVP with rollback; Phase 4 (GNN/multi-agent) → 1.0 release.  
- **Goal 2 (Multi-Agent RL)**: Phase 2 (edge Q-Learning) → early prototypes; Phase 4 (PettingZoo + Ray) → full implementation.  
- **Goal 3 (Usable AIOps Console)**: Phase 3 (FAISS/LLM + Vue) → beta dashboard; post-1.0 UX polish.  

This roadmap ensures incremental value, with each release building toward business impact (e.g., beta feedback drives 1.0 features).

## Risks and Contingencies

- **Technical Delay**: RL convergence issues — contingency: fallback to rule-based in MVP (20% time buffer).  
- **Market Adoption**: Slow homelab uptake — contingency: Phoenix beta focus, free tier.  
- **Cost Overrun**: Hardware/testing — contingency: Simulate with Mininet (reduce physical deps).  

This roadmap positions Network-Chan for success—delivering value early while scaling strategically.
