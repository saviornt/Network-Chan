# Network-Chan Vision and Scope Document

**Project name:** Network-Chan  
**Date:** 2026-03-21  
**Version:** 1.1 (updated)  

## Executive Summary

Network-Chan is a local-only, research-grade autonomous SDN (Software-Defined Networking) management plane designed primarily for home/lab environments, with extensibility toward prosumer, small-to-medium business, and professional use cases. The system is structured in two cooperating layers:

- **Network Appliance:** A lightweight, always-on edge MLOps controller (reference platform: Raspberry Pi 5) responsible for real-time perception (telemetry ingestion), lightweight inference, and immediate remediation using TinyML-packaged models (including TinyGNN, Q-Learning and REPTILE) for fast adaptation and MAML-style meta-learning.
- **Application:** A central AIOps component which runs on a PC, mini-PC, or server and provides global training using multi-agent, GNN-based RL-MAML using Q-Learning elements, policy governance, persistent incident memory with RAG, explainable analytics, and user-facing interfaces (dashboard, LLM assistant with optional voice and personality modes).

All processing remains strictly local — no cloud dependencies, no external API calls, no recurring third-party costs — ensuring privacy, security, and independence from internet connectivity or vendor ecosystems.

Core operational principles:

- Local-only execution
- Fail-open design (network continues to function without Network-Chan)
- Recoverable states via snapshots and rollback
- Policy-governed automation with configurable autonomy levels

The long-term vision is an adaptive, self-improving network guardian that reduces manual intervention for common issues (interface flaps, congestion, rogue devices, etc.) while delivering grounded, explainable insights through an intuitive interface.

## Product Vision

Network-Chan aims to bring advanced, private AIOps capabilities to everyday networks by turning commodity hardware (or a Docker-emulated environment) into an intelligent, self-healing management plane. The system learns from real traffic patterns to predict and prevent disruptions, performs autonomous security auditing, and collaborates with a central reasoning layer for complex analysis — all without ever leaving the local premises.

Key differentiators:

- Millisecond-scale edge inference using TinyML-packaged models (TinyGNN + Q-Learning + REPTILE)
- Centralized multi-agent, GNN-enhanced RL-MAML training for topology-aware, coordinated optimization
- Persistent incident memory using FAISS-based RAG for context-grounded prediction, remediation and LLM assistance
- Optional emotional/personality UX (VAD-based) for engaging user interaction; professional-neutral mode available
- Docker container for Pi 5 emulation → zero-hardware testing and development

## Target Users & Personas

- **Primary** — Home lab enthusiasts and hobbyists seeking affordable, private, autonomous network management for TP-Link Omada, Ubiquiti UniFi, or similar SDN setups.
- **Secondary** — Small-to-medium business owners and MSPs requiring low-cost, self-managing networks with auditing and reporting.
- **Tertiary** — Remote workers / hybrid professionals and researchers/educators experimenting with edge RL, GNNs, meta-learning, or AIOps in lab or home-office environments (via Mininet integration and modular code).

**Personas**:

- **Dave the Hobbyist:** Tech-savvy individual running a home lab; values easy setup, voice interaction for quick status, and automatic remediation without constant oversight.
- **Alex the Remote Parent:** Work-from-home professional balancing a career and family life that values "set-and-forget" functionality, prioritized networking traffic for productivity and robust security that doesn't require manual configuration.
- **Lisa the SMB Owner:** Runs a small-to-medium business with 20–80 devices; needs reliable uptime, simple reports, low false positives, and minimal IT staff involvement.
- **Riley the Researcher:** Academic or independent researcher testing advanced RL/GNN techniques; appreciates simulation support, extensible code, and reproducible training pipelines.

## Expected Outcomes & Business Path

- **Near-term:** Demonstrate reliable edge remediation and central coordination in lab/home environments; provide Docker-based emulation for broad testing and contribution.
- **Medium-term:** Offer optional Raspberry Pi 5 kit assembly guides (self-sourced components) for enthusiasts who prefer physical deployment.
- **Longer-term:** After proving stability and value, explore purpose-built hardware manufacturing / partnerships only if demand justifies it.

### Distribution model

Open-source core (Appliance + base Application functionality) freely available on GitHub for self-hosting and community development.

- Raspberry Pi kits offered as optional enthusiast/self-assembly bundles (user sources components per guide); each kit includes a QR code and website address directing to the latest Application download (installer/package for PC/server).
- Future retail and production-grade hardware (pre-configured, plug-and-play appliances) introduced only after system reliability is proven in real deployments; these units will also ship with a QR code and website address for downloading the matching Application version.

### Success Indicators

- Edge detection & remediation of common failures with false positive rate < 3% in staged/lab environments
- Autonomous rollback of failed changes in < 60 seconds
- MTTD/MTTR significantly reduced compared to manual intervention
- Positive feedback from beta testers across all personas
- Growing community contributions, reproducible research usage, and successful kit/Docker-based deployments

This vision positions Network-Chan as a privacy-first, extensible platform that evolves networks from static to adaptive — starting simple, scaling smartly, and always staying under user control.
