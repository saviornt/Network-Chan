# Network-Chan Test Plans & QA Documentation

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  
**Version:** 1.0  

## Introduction

This Test Plans & QA Documentation outlines the comprehensive testing strategy for Network-Chan, ensuring the system meets functional, non-functional, and security requirements across its three-brain architecture and split design (Appliance on Raspberry Pi 5 for edge operations, Assistant on PC for central reasoning/UX). Testing follows Agile principles, with continuous integration (CI) via GitHub Actions, and emphasizes safety (e.g., fail-open validation), privacy (redacted test data), and performance in local-only environments.

The plan covers unit, integration, system, and acceptance testing, plus specialized load/performance/network stress tests. Bug tracking is integrated into the development workflow. All tests are automated where possible, with manual reviews for UX and RL behaviors. Tools include pytest (Python), Jest (Vue/JS), Mininet (network sim), and Locust (load). Test environments: Local Pi/PC setup, Mininet sim, staging VLAN.

## Test Strategy

- **Approach**: Test-Driven Development (TDD) for new features; CI/CD enforces 80%+ code coverage. Tests run on every PR/commit.
- **Scope**: Covers Appliance (monitoring/learning/automation), Assistant (dashboard/LLM/agent), MQTT bridge, and end-to-end flows.
- **Environments**:  
  - Unit/Integration: Local Docker (simulate Pi/PC).  
  - System/Stress: Lab VLAN with ER707 router + APs.  
  - Acceptance: Full home/lab network + Mininet sim.  
- **Test Data**: Synthetic incidents (generated via scripts); redacted real data for privacy.
- **Metrics**: MTTD/MTTR simulation (<60s goal), false positive rate <3%, coverage >80%, bug resolution <48 hours.

## Test Cases

### Unit Testing

Focus: Individual modules/functions (e.g., isolated Q-Learning update). Use pytest; run in CI.

- **Example Cases (Appliance - network_learning.py)**:  
  - TC-U1: Verify REPTILE meta-update adapts model params (input: few-shot tasks; expected: init weights shift >5%).  
  - TC-U2: Test Q-Learning table update (input: state/action/reward; expected: Q-value changes by alpha * delta).  
  - TC-U3: Edge case: Max state space — ensure no memory overflow (<100MB).  

- **Example Cases (Assistant - agent.py)**:  
  - TC-U4: LLM RAG query retrieves top-k incidents (input: query; expected: FAISS precision >80%).  
  - TC-U5: VAD scoring maps event to tone (input: severity=-0.5; expected: negative valence).  

- **Coverage**: 90%+ for core logic; mock externals (e.g., Omada API).

### Integration Testing

Focus: Interactions between modules (e.g., monitoring → learning → automation). Use pytest + Mininet for sim.

- **Example Cases (Appliance)**:  
  - TC-I1: Monitoring features → learning input (input: simulated traffic spike; expected: anomaly score >0.7 triggers Q-action).  
  - TC-I2: MQTT publish/subscribe loop (input: command to run audit; expected: execution + response published <10s).  
  - TC-I3: FAISS + SQLite insert/retrieve (input: incident; expected: top-k similar returns correct vector_id).  

- **Example Cases (Assistant)**:  
  - TC-I4: MQTT subscriber → LLM context (input: Pi alert; expected: grounded response with confidence >0.8).  
  - TC-I5: Dashboard WebSocket → agent call (input: chat query; expected: real-time response in <5s).  

- **Coverage**: End-to-end flows; simulate failures (e.g., MQTT disconnect).

### System Testing

Focus: Full system in integrated environment (Pi + PC + broker + devices). Manual/automated scripts.

- **Example Cases**:  
  - TC-S1: End-to-End Remediation (input: simulate congestion; expected: Pi detects, Q-selects action, governs, executes, rolls back if fails — MTTR <60s).  
  - TC-S2: Multi-Agent Sim (input: Mininet topology with 3 agents; expected: RL-MAML policy optimizes routing >90% efficiency).  
  - TC-S3: Autonomy Mode Switch (input: Set to SAFE; expected: Low-risk action auto-executes, high-risk requires approval).  
  - TC-S4: Voice/Chat Query (input: "Analyze recent incident"; expected: RAG-retrieved response with VAD tone).  

- **Coverage**: All autonomy modes; staging VLAN tests.

### Acceptance Testing

Focus: User validation against goals (e.g., MTTD/MTTR KPIs). Beta testers in Phoenix labs.

- **Example Cases**:  
  - TC-A1: Detect/Remediate Failure (input: Interface flap; expected: MTTD <10s, MTTR <60s, false positives <3% in 100 runs).  
  - TC-A2: LLM Advice Accuracy (input: Query past incident; expected: Grounded response with >90% admin-judged accuracy).  
  - TC-A3: Rollback Success (input: Failed change; expected: Auto-restore <60s, no data loss).  
  - TC-A4: UI Usability (input: Navigate dashboard; expected: Complete tasks <2 min, satisfaction score >4/5).  

- **Coverage**: UAT scripts + surveys; simulate home/SMB/enterprise setups.

## Load, Performance, and Network Stress Tests

Focus: Ensure scalability/resilience under load (e.g., 100 devices, high traffic).

- **Tools**: Locust (load), Apache JMeter (API stress), Mininet (network sim), Prometheus for metrics.  
- **Environment**: Lab VLAN with simulated devices (Mininet); measure Pi CPU/RAM/latency.  

- **Load Tests**:  
  - TC-L1: 500 MQTT messages/min (input: simulated alerts; expected: No backlog, latency <100ms).  
  - TC-L2: 50 concurrent dashboard users (input: Vue queries; expected: Response <2s, no crashes).  

- **Performance Tests**:  
  - TC-P1: Edge Inference (input: 100 features; expected: TinyML/Q-Learning <10ms on Pi).  
  - TC-P2: Central Training (input: 1k incidents; expected: RL-MAML cycle <5 min on PC).  

- **Network Stress Tests**:  
  - TC-N1: High Traffic Sim (input: Mininet 1Gbps flood; expected: Detect congestion, remediate without Pi overload).  
  - TC-N2: Disconnect/Resync (input: MQTT broker down 5 min; expected: Pi continues local ops, resyncs <30s on reconnect).  
  - TC-N3: VLAN Failover (input: Management VLAN flap; expected: Fall back to defaults, recover <60s).  

- **Coverage**: Run in CI for baselines; manual in lab for stress. Thresholds: Pi CPU <80%, RAM <70% under load.

## Bug Tracking Process

Bugs are tracked via GitHub Issues for transparency and integration with PRs/CI.

- **Process**:  
  1. **Report**: Anyone opens Issue with template (title: [Bug] Description; labels: bug, priority high/medium/low; steps to repro, expected/actual, env details).  
  2. **Triage**: PO/Scrum Master assigns priority/severity (P1 critical – blocks release; P4 cosmetic). Duplicate/close invalids within 24 hours.  
  3. **Assignment**: Add to sprint backlog; assign to dev in planning.  
  4. **Fix & Review**: Branch from main (bugfix/{issue-id}); fix + unit test; PR with "Fixes #issue-id".  
  5. **Verification**: Reviewer tests; CI passes (including regression suite).  
  6. **Closure**: Merge PR → auto-close Issue; add to changelog.  
- **Tools**: GitHub Issues + Labels (bug, enhancement); Projects board for kanban (To Do/In Progress/Done). Integrate with CI (e.g., fail PR if open P1 bugs).  
- **Metrics**: Bug resolution time <48 hours for P1; monthly bug trend report.  
- **Escalation**: P1 bugs halt sprint until fixed; retrospectives review root causes.

This plan ensures rigorous QA, with testing integrated into Agile sprints for rapid iteration. It will be updated based on retrospectives.
