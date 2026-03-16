# Network-Chan Vision and Scope Document

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  
**Version:** 1.0  

## Executive Summary

Network-Chan is envisioned as a local-only, research-grade autonomous SDN (Software-Defined Networking) management plane tailored for home/lab environments, with potential scalability to prosumer, professional, or enterprise settings. The product splits into a lightweight, always-on edge MLOps controller (the "Appliance" on Raspberry Pi 5) for real-time perception, lightweight reinforced meta-learning, and immediate remediation, and a central AIOps controller (the "Assistant" on a more powerful PC/server) for global training, policy optimization, explainable analytics, and user interaction.

This three-brain architecture (Perception on edge, Decision/Governance on central, UI on assistant) ensures safety-first operations while enabling advanced features like multi-agent RL across network devices, persistent incident memory with retrieval-augmented generation (RAG) for an LLM assistant, secure telemetry transport, and an admin interface with optional voice and emotional expression. Key principles include local-only processing, fail-open design (network continues without AI), recoverable states (snapshots + rollback), and policy-governed automation.

The vision is to create a "smart network appliance" that self-improves over time, reducing manual intervention for common issues like interface flaps or congestion, while providing grounded, explainable insights through an intuitive dashboard. Expected business impact: A sellable Pi-based kit for homelabs (freemium model), with enterprise extensions for MSPs via custom integrations.

## Product Vision

Network-Chan aims to democratize advanced AIOps for everyday users by turning a simple Raspberry Pi into an intelligent, self-healing network guardian. Imagine a device that not only monitors your home/lab SDN but learns from patterns to predict and prevent downtime, audits security autonomously, and collaborates with a smarter assistant for complex queries—all without cloud dependency or privacy risks.

The overarching vision is to build an ecosystem where networks become "alive" and adaptive:  

- The Appliance acts as a vigilant edge brain, reacting in milliseconds to local events using TinyML + Q-Learning + REPTILE for reinforced meta-learning.  
- The Assistant elevates it to a conversational expert, using GNNs for topology-aware reasoning, RL-MAML for global policies, and an LLM for natural-language advice grounded in past incidents.  
- Users interact via a sleek dashboard or voice, feeling empowered rather than overwhelmed by network complexity.

In essence, Network-Chan transforms passive hardware into a proactive partner, making advanced networking accessible, fun, and secure for hobbyists while scaling to professional reliability for businesses.

## Project Scope

### What's Included (In-Scope)

- **Appliance (Edge MLOps on Pi 5)**: Real-time telemetry ingestion (Prometheus, SNMP, psutil), lightweight edge inference (TinyML + Q-Learning + REPTILE for anomaly detection, congestion prediction, action selection), automation/remediation (Netmiko/Omada API), security auditing scheduler (nmap-based), local logging (SQLite + FAISS vectors), Prometheus export, MQTT publisher/subscriber for telemetry/commands, and a simple on-device configuration page (minimal FastAPI/HTML).
- **Assistant (Central AIOps on PC)**: MQTT subscriber for Pi data, global training (RL-MAML, GNNs with PyTorch Geometric), LLM assistant (Ollama + LangChain with RAG via FAISS), emotional intelligence/personality UX (VAD model + templates), voice interface (TTS/STT), full Vue 3 dashboard (real-time charts, topology view, analytics), reporting (PDF/CSV exports), and TOTP 2FA authentication.
- **Messaging & Integration**: Secure MQTT/TLS with RBAC for command/telemetry, Home Assistant tie-in via MQTT sensors/commands, Mininet digital twin for simulation/testing, PettingZoo for multi-agent RL environments, and Ray RLlib for distributed training.
- **Safety & Governance**: Policy engine (FastAPI microservice), fail-open design, snapshots/rollback (<60s), autonomy modes (OFF/ADVISE/SAFE/FULL/EXPERIMENTAL), rate limiting, and immutable audit logs.
- **Data & Memory**: Incident episodic records in SQLite/FAISS, redaction for privacy, retention policies.

### What's Excluded (Out-of-Scope)

- Cloud integrations or remote access (e.g., no AWS/Azure support, no public exposure).
- Advanced hardware beyond TP-Link Omada ecosystem (e.g., no Cisco/Juniper support initially; extensible via Netmiko).
- Full-scale enterprise features like high-availability clustering, multi-site federation, or commercial licensing in MVP.
- Non-network devices (e.g., no direct IoT sensor integration beyond SNMP).
- Custom LLM fine-tuning or non-local models (stick to Ollama/offline for privacy).
- Mobile apps or non-browser UIs (focus on web dashboard; HA app can proxy if needed).
- Extensive UI customization beyond basic themes/personalities.

Scope boundaries will be managed via Agile backlog prioritization—new features (e.g., more SDN vendors) added only after MVP validation.

## Primary Goals

1. **Build a Safe, Autonomous SDN Control Plane**: Enable self-detection and remediation of common issues (e.g., interface flaps, rogue DHCP, congestion) with multi-agent RL across devices, while maintaining strong safety guardrails (policy engine, rollback).

2. **Provide Explainable AIOps Insights**: Use RAG with FAISS incident memory for an LLM assistant that delivers grounded, confidence-scored advice, reducing MTTD/MTTR.

3. **Create an Intuitive Admin Experience**: Deliver a responsive Vue dashboard with real-time visualizations (topology, heatmaps, timelines), chat/voice interface, optional emotional/personality UX (VAD), and easy reporting.

4. **Ensure Offline, Local-Only Operation**: All components run without internet; fail-open design ensures network continuity.

5. **Support Research & Extensibility**: Use Mininet for simulations, Ray RLlib for scalable training, and modular code for future expansions (e.g., more agents, hardware).

## Target Users

- **Primary Users**: Home lab enthusiasts and hobbyists in Phoenix, AZ (or similar tech-savvy areas) seeking affordable, private AIOps for TP-Link Omada setups.
- **Secondary Users**: Small business owners/MSPs needing low-cost, self-managing SDN with auditing/reporting.
- **Tertiary Users**: Researchers/educators experimenting with edge RL, GNNs, or AIOps in labs (via Mininet integration).
- **User Personas**:
  - **Dave the Hobbyist**: Tech enthusiast in Phoenix running a home lab; wants easy setup, voice chat for quick status, and auto-remediation without babysitting.
  - **Alex the MSP Operator**: Manages 5–10 client networks; needs explainable logs, reports, and low false positives for trust.
  - **Riley the Researcher**: Academic testing RL in networks; values Mininet sims, FAISS retrieval, and extensible code.

## Expected Business Impact

- **Revenue Potential**: Sell Pi-based Appliance kits ($50–100) via Etsy/Kickstarter, with freemium Assistant software (basic free, premium for advanced LLM/personality features). Target 500–2000 units in year 1 from r/homelab/Reddit, Pi forums.
- **Cost Savings for Users**: Reduces downtime by 30–50% (via predictive remediation), lowers manual intervention (MTTR <60s), and provides free auditing (vs. paid tools like SolarWinds).
- **Market Differentiation**: Unique blend of edge TinyML RL + central GNN/LLM in an affordable, private package—competes with Ubiquiti Unifi but adds true AI autonomy.
- **Research Value**: Open-source contributions to edge AIOps (e.g., REPTILE + Q-Learning hybrids) could attract collaborations, grants, or corporate interest (e.g., TP-Link partnerships).
- **Risks & Mitigations**: Low initial investment (Pi hardware ~$100); mitigate market risks with beta testing. Expected ROI: Break-even at 200 units, positive impact on personal portfolio as a showcase project.

This Vision and Scope sets the foundation for Network-Chan as a transformative, user-centric AIOps product—empowering networks to manage themselves intelligently and securely.
