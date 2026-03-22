# Network-Chan Security Design Document

**Project name:** Network-Chan  
**Date:** 2026-03-21  
**Version:** 1.1 (updated with autonomy levels & current architecture)  

## Introduction

This Security Design Document (SDD) outlines the security architecture for Network-Chan, a local-only autonomous SDN management plane with two cooperating layers:

- **Network Appliance** — lightweight edge MLOps controller (Raspberry Pi 5 reference) for real-time perception, small-scale inference, and policy-approved remediation.
- **Application** — central AIOps component (PC/server) for global training, model distribution, persistent memory with RAG, governance, and user interfaces.

All processing is strictly local — no cloud dependencies. The design enforces zero-trust principles, fail-safe operation (fail-open, recoverable states), and privacy (GDPR-inspired no external data sharing).

Key threats mitigated: Unauthorized access (MQTT injection), data exposure (telemetry leaks), policy bypass (rogue AI actions), firmware vulnerabilities (Omada/TP-Link), physical access (Pi).

## Threat Model Assumptions

- **Environment**: Local network (no public exposure); admin workstation trusted but requires TOTP 2FA.
- **Attackers**: Internal (rogue device/user), external (compromised LAN), supply-chain (firmware).
- **Assets**: Telemetry data, ML models/checkpoints, audit logs, device configs.
- **Vectors**: MQTT tampering, API injection, physical Pi access, prompt injection (LLM).

## Access Control

Access control combines Role-Based Access Control (RBAC) for human users and Attribute-Based Access Control (ABAC) with **autonomy levels** for AI/ML decisions.

- **Human User Roles**:
  - Admin: Full access (config changes, model updates, audits).
  - Operator: Read-only + approved remediations.
  - Viewer: Metrics/dashboard only.

- **AI/ML Autonomy Levels** (governing automated decisions/remediations):
  Stored as integer (env var) with enum for type safety. Lower levels prioritize safety; higher enable automation.

  ```text
  0 - OBSERVER: Monitor & log only — no suggestions or actions
  1 - ADVISOR: Suggest actions via dashboard/LLM
  2 - SUPERVISED: Suggest + require approval for most actions
  3 - SEMI_AUTONOMOUS: Auto-execute safe/low-risk actions
  4 - AUTONOMOUS: Full self-healing with rollback guardrails
  5 - EXPERIMENTAL: Bleeding-edge/research mode — no safety nets
  ```

- **Implementation**:
  - **MQTT**: Mosquitto ACL file (topic-based restrictions); mutual TLS certs.
  - **FastAPI**: Dependency injection for role + autonomy checks (e.g., `Depends(check_autonomy_level(min_level=3))`).
  - **Policy Engine**: ABAC rules evaluate autonomy level + action risk/severity. Example:
    - Level 0–1: No execution allowed.
    - Level 2: Require human approval (dashboard/LLM prompt).
    - Level 3–4: Auto-execute if whitelisted + rollback snapshot exists.
    - Level 5: Bypass some checks (research mode only).
  - **Auditing**: Every decision/action logged immutably in SQLite (policy_audits table) with autonomy level, user/role (if human), timestamp, outcome.

- **Centralized Visibility**: Appliance pushes config/logs to Application via MQTT → unified dashboard view (reduces direct Appliance login).

## Authentication

- **User Authentication (Application Dashboard & Appliance UI)**:
  - Mandatory TOTP 2FA (pyotp, Google Authenticator-compatible).
  - **Forced setup on first login**: QR code generated + secret shared; user must scan, verify code, and confirm before access granted.
  - Session Cookies: HTTPOnly, Secure, SameSite=Strict; expire after inactivity (1 hour default).
  - Appliance local UI (FastAPI+Jinja2): Same TOTP flow for initial setup/logs.

- **Device/Component Authentication**:
  - MQTT: Mutual TLS certs + optional username/password fallback.
  - FastAPI APIs: JWT tokens (RS256) for calls; validate roles + autonomy.

- **Flow**:
  - First login: Username/password → TOTP setup (QR + verification) → JWT issued.
  - Subsequent: TOTP + JWT in headers/cookies.

## Encryption

- **Data at Rest**:
  - SQLite: Encrypted with SQLCipher (AES-256). Key from env var or TPM (Pi).
  - FAISS Indexes: File-level encryption.
  - Model Checkpoints: AES-256 encrypted blobs in MLflow (signed with HMAC).

- **Data in Transit**:
  - MQTT: TLS 1.3 mandatory with mutual certs (self-signed CA). Strong ciphers only (AES-256-GCM).
  - FastAPI: HTTPS only (TLS 1.3).
  - SNMP/Netmiko: v3 with AES encryption.

- **Data in Processing**:
  - Redact PII (e.g., IPs in embeddings) before FAISS/LLM.
  - Future PQC: Planned upgrade to ML-KEM (key encapsulation) + ML-DSA (digital signatures) for MQTT TLS and model signing/checkpoint integrity.

- **Key Management**: Central CA on Application; quarterly rotation; encrypted backups.

## Network Security Layers

Layered defense:

- **Network Layer**:
  - VLAN Isolation: Management VLAN for Appliance/Application/broker; staging VLAN for tests.
  - Firewall: ufw on Pi (LAN-only ports: 8001 for UI, MQTT 1883/8883); ACLs on ER707.

- **Transport Layer**:
  - TLS 1.3 everywhere (mutual certs); no weak ciphers.

- **Application Layer**:
  - Input Validation: Pydantic schemas for APIs/MQTT payloads; sanitize inputs.
  - Rate Limiting: FastAPI middleware (10 req/min); MQTT message limits.
  - Monitoring: Prometheus (security_alerts_total); anomaly detection on access patterns.

- **Diagram**: Security Layers

  ```mermaid
  graph TD
      subgraph "Audit"
          Immutable_Logs[Immutable Logs]
          Alerts[Alerts]
      end
      subgraph "Data"
          Encryption_at_Rest[Encryption at Rest]
          Redaction[Redaction]
      end
      subgraph "Application"
          Input_Validation[Input Validation]
          Rate_Limiting[Rate Limiting]
          RBAC_ABAC[RBAC + Autonomy ABAC]
      end
      subgraph "Transport"
          TLS_1_3[TLS 1.3]
          Mutual_Certs[Mutual Certs]
      end
      subgraph "Network"
          VLAN_Isolation[VLAN Isolation]
          Firewall_ACLs[Firewall ACLs]
      end
  ```

This SDD ensures Network-Chan is secure by design, with layered protections and enforceable autonomy boundaries. It will be reviewed quarterly or after major milestones.
