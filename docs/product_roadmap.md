# Network-Chan Product Roadmap

**Project name:** Network-Chan  
**Date:** 2026-03-21  
**Version:** 1.1

## Executive Summary

This is the **complete micro-view product roadmap** for Network-Chan — a detailed, sequential breakdown of every major step from current state (shared components mostly ready) through to full MVP (Appliance + Application integrated on real hardware) and beyond.  

It is built for solo development:

- 1-week sprints (1–2 day tasks)
- GitHub Issues → auto-cards in "Network-Chan Project Development" board
- Testing flow: Manual QA (on real Pi 5 / emulator) → Automated QA (pytest/MyPy in GitHub Actions)
- Definition of Done: Works as intended + no errors + manual verification + (where applicable) CI pass
- MVP = Both layers working together locally on your hardware (telemetry up, models down, centralized config/logs, TOTP 2FA)

The roadmap follows the 9 phases defined in the agile plan and expands each into specific, actionable tasks with deliverables, success criteria, and dependencies.

## Full Micro-View Roadmap (Phase-by-Phase)

### Phase 1: Shared Components Stability (March 24 – April 6, 2026 | 2 weeks)

**Goal**: Make shared layer rock-solid before any layer-specific work.

**Week 1 (Mar 24–30)**

- Review/debug/refactor shared/src (logging_factory.py, shared_settings.py, Pydantic models, asyncio-mqtt helpers, UTC datetime pattern, Numba njit usage)
- Add missing `__init__.py` exports and fix any validator inconsistencies
- Enable basic GitHub Actions CI (Ruff lint + MyPy strict)
- Update all Google-style docstrings and type hints
- Test package installation in Docker Pi 5 emulator

**Week 2 (Mar 31 – Apr 6)**

- Add structured logging factory usage everywhere in shared
- Create comprehensive test suite for shared utilities (pytest)
- Manual QA: Run full package install + basic import tests on real Pi 5
- Success criteria: Shared package installs cleanly, all tests pass, no deprecation warnings

**Deliverables**: Production-ready shared package (pip-installable), CI enabled, docs updated  
**Dependencies**: None (current focus)

### Phase 2: Telemetry Ingestion & Appliance Basics (April 7 – April 27, 2026 | 3 weeks)

**Goal**: Get real data flowing from Omada hardware.

**Week 1**

- Implement async telemetry ingestion (Omada API + SNMP v3 + psutil) using asyncio-mqtt
- Store raw incidents, telemetry and time-series metrics in Appliance local SQLite + FAISS
- Publish Prometheus-compatible time-series metrics

**Week 2**

- Add TinyML basic inference stub (TinyGNN + Q-Learning + REPTILE) on incoming telemetry
- Create local FastAPI + Jinja2 config/settings/log viewer (port 8001)
- Implement forced TOTP 2FA setup on first Appliance login

**Week 3**

- Manual QA on real ER707-M2/OC220 hardware
- Add checkpointing and basic rollback safety
- Success criteria: Live metrics visible in local UI, no crashes, data published to MQTT

**Deliverables**: Working Appliance telemetry loop + local UI  
**Dependencies**: Phase 1 complete

### Phase 3: Appliance Core & Standalone Test (April 28 – May 18, 2026 | 3 weeks)

**Goal**: Make Appliance fully functional standalone.

**Week 1**

- Debug/refactor Q-Learning + REPTILE small-scale training loop (async run_episode)
- Add policy guardrails + autonomy mode checks

**Week 2**

- Implement local TinyML remediation execution (Netmiko/Omada API calls)
- Add checkpoint path safety + mkdir logic
- Full Mininet simulation validation

**Week 3**

- Manual QA on real hardware (end-to-end anomaly detection → remediation)
- Add unit tests for Q-Learning paths
- Success criteria: Appliance runs autonomously, detects/remediates issues, rolls back safely

**Deliverables**: Standalone Appliance MVP core  
**Dependencies**: Phase 2

### Phase 4: Application Basics & Integration (May 19 – June 8, 2026 | 3 weeks)

**Goal**: Build central layer and first integration.

**Week 1**

- Set up Application as background service (persistent, Electron/browser launch)
- Implement central multi-agent GNN-based RL-MAML training (Ray RLlib + PettingZoo)

**Week 2**

- Add model quantization + MQTT push to Appliance
- Implement full SQLite + FAISS ingest on Application side
- Build centralized config/logs viewer in Vue 3 / Vite dashboard

**Week 3**

- Add TOTP 2FA + auto-logout on Application
- Manual end-to-end test (telemetry → central training → model push)
- Success criteria: Application receives data, trains, pushes updates, dashboard shows everything

**Deliverables**: Working Application with first bidirectional link  
**Dependencies**: Phase 3

### Phase 5: Communications (June 9 – June 15, 2026 | 1 week)

**Goal**: Solidify bidirectional flow and security.

**Tasks**:

- Full bidirectional MQTT testing (telemetry up, models down, config sync)
- End-to-end testing on real hardware (Pi 5 + PC)
- Enforce auto-logout + TOTP everywhere
- Add TLS verification and ACL hardening

**Deliverables**: Rock-solid communication layer  
**Success criteria**: Zero dropped messages, secure TLS, seamless model updates

### Phase 6: Polish & Alpha Testing (June 16 – July 6, 2026 | 3 weeks)

**Goal**: Make the system feel complete and stable in home lab.

**Week 1–2**:

- Add voice/personality UX (VAD + optional TTS/STT)
- Implement multi-agent coordination (PettingZoo agents)
- Home-lab stress testing (Locust + Mininet chaos)

**Week 3**:

- Full alpha testing on your actual network
- Bug fixes + performance tuning (Numba njit paths)
- Success criteria: Stable 24/7 run, voice works, multi-agent improves decisions

**Deliverables**: Polished, production-feeling system in your lab

### Phase 7: MVP & Beta Readiness (July 7 – July 20, 2026 | 2 weeks)

**Goal**: Package and show the world.

**Tasks**:

- Create final Docker images + Pi SD card guide
- Build beta distribution (GitHub release + QR code installer flow)
- Record demonstration videos for social media (X, Reddit r/homelab, etc.)
- Success criteria: Anyone can install and run full system from QR/website

**Deliverables**: MVP ready for public beta

### Phase 8: Post-MVP Release (July 21 – August 31, 2026 | 6 weeks)

**Goal**: Get feedback and funding.

**Tasks**:

- Publish demos on social media channels
- Reach out to angel investors and mentors (list prepared in advance)
- Run structured feedback sessions with early beta users
- Iterate based on feedback (continuous development loop)

**Deliverables**: Investor meetings scheduled, beta community growing

### Phase 9: CI/CD Loop & Future Enhancements (September 2026 onward)

**Goal**: Make development sustainable and forward-looking.

**Tasks**:

- Fully enable and expand CI/CD pipeline (full test coverage, security scans)
- Research and implement PQC cryptography (ML-KEM key exchange + ML-DSA signatures for MQTT and model signing)
- Loop through continuous development based on user/investor feedback
- Add any new enhancements (Home Assistant deeper integration, etc.)

**Deliverables**: Production-grade CI/CD + quantum-resistant security layer

## Success Metrics for Full Project

- Appliance + Application running 24/7 on real hardware with zero crashes
- MTTD/MTTR <60 seconds in lab tests
- False positive rate <3%
- Beta users able to install via QR/website and run full system
- Positive investor/mentor feedback + at least one funding conversation

This micro-view roadmap is now the single source of truth for development from today through post-MVP. We will update it every 4 weeks or after each major phase completion.
