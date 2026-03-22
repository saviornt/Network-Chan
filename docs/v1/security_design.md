# Network-Chan Security Design Document

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  
**Version:** 1.0  

## Introduction

This Security Design Document (SDD) outlines the security architecture for Network-Chan, a local-only autonomous SDN management plane. It addresses access control, encryption, authentication, and network security layers, aligned with the three-brain model (Perception, Decision, Governance) and split design (Appliance on Raspberry Pi 5 for edge operations, Assistant on PC for central reasoning/UX). The design prioritizes a zero-trust approach, fail-safe principles, and compliance with standards like GDPR (privacy) and NIST (risk management), ensuring the system is secure for homelab to enterprise use.

Key threats mitigated: Unauthorized access (e.g., MQTT injection), data exposure (telemetry leaks), policy bypass (rogue actions), and firmware vulnerabilities (Omada/TP-Link). All security features are local-only, with no cloud dependencies.

## Threat Model Assumptions

- **Environment**: Local network (no public exposure); admin workstation trusted but 2FA-required.
- **Attackers**: Internal (rogue device/user), external (compromised LAN), or supply-chain (firmware).
- **Assets**: Telemetry data, ML models, audit logs, device configs.
- **Vectors**: MQTT tampering, API injection, physical Pi access, LLM prompt injection.

## Access Control

Access control uses Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) to enforce least-privilege. Implemented via MQTT ACLs, FastAPI guards, and policy engine.

- **Roles**:  
  - Admin: Full access (config changes, model updates, audits).  
  - Operator: Read-only + approved remediations.  
  - Viewer: Metrics/dashboard only.  
  - LLM/Agent: Restricted to suggest-only (no execute without approval).  

- **Implementation**:  
  - **MQTT**: Mosquitto ACL file (topic-based: admin can pub/sub all; operator sub only to /status). Mutual TLS certs for client auth.  
  - **FastAPI**: Dependency injection for role checks (e.g., @app.get("/config", dependencies=[Depends(check_admin_role)]).  
  - **Policy Engine**: ABAC rules (e.g., "allow if autonomy_mode >= SAFE and severity < critical"). Whitelists for commands (JSON schema validation).  
  - **Auditing**: All access logged immutably in SQLite (policy_audits table).  

- **Diagram**: RBAC Flow  

  ```mermaid
  sequenceDiagram
      User->>FastAPI: Request /config
      FastAPI->>Auth: Verify TOTP/role
      Auth->>FastAPI: Approved?
      alt Approved
          FastAPI->>Policy Engine: Check ABAC
          Policy Engine->>FastAPI: Allowed
          FastAPI->>User: Response
      else Denied
          FastAPI->>User: 403 Forbidden
      end
      FastAPI->>SQLite: Log access
  ```

## Encryption

Encryption protects data at rest, in transit, and during processing, using industry standards like AES/TLS.

- **Data at Rest**:  
  - SQLite DB: Encrypted with SQLCipher (AES-256). Key from env var or TPM on Pi.  
  - FAISS Indexes: File-level encryption (encfs or eCryptfs on Pi filesystem).  
  - Model Checkpoints: Encrypted blobs in MLflow registry (AES-256, signed with HMAC).  

- **Data in Transit**:  
  - MQTT: TLS 1.3 with mutual certs (self-signed CA managed centrally). Cipher suites: AES-256-GCM.  
  - FastAPI APIs: HTTPS only (TLS 1.3, certs from same CA).  
  - SNMP/Netmiko: v3 with AES encryption for polls/commands.  

- **Data in Processing**:  
  - Redact PII (e.g., IPs in embeddings) before FAISS/LLM.  
  - Secure Enclaves: Optional TEE (Trusted Execution Environment) on Pi ARM TrustZone for sensitive RL updates.  

- **Key Management**: Central CA on Assistant; rotate keys quarterly; backups encrypted.

## Authentication

Authentication ensures only authorized entities access components, using multi-factor and certificate-based methods.

- **User Authentication (Assistant Dashboard)**:  
  - TOTP 2FA (pyotp, Google Authenticator-compatible). QR generation on first login.  
  - Session Cookies: HTTPOnly, Secure, SameSite=Strict; expire after 1 hour.  

- **Device/Component Authentication**:  
  - MQTT: Mutual TLS certs + username/password fallback.  
  - FastAPI: JWT tokens (RS256) for API calls; validate roles.  
  - LLM/Agents: API keys with scope (e.g., read-only for queries).  

- **Implementation Flow**: User logs in (username/pass + TOTP) → receives JWT → JWT in Authorization header for APIs/WebSocket.  

- **Diagram**: Authentication Flow  

  ```mermaid
  sequenceDiagram
      User->>Dashboard: Login (user/pass/TOTP)
      Dashboard->>Auth Module: Verify
      Auth Module->>Dashboard: JWT Token
      Dashboard->>User: Session Cookie
      User->>API: Request with Bearer JWT
      API->>Auth: Validate JWT/role
      API->>User: Response
  ```

## Network Security Layers

A layered defense (defense-in-depth) protects the system at network, transport, application levels.

- **Network Layer**:  
  - VLAN Isolation: Management VLAN for Appliance/Assistant/broker; staging VLAN for experiments; production VLAN monitored only.  
  - Firewall: ufw on Pi (allow 8001/TCP LAN-only, 1883/TCP for MQTT); ACLs on ER707 (block staging → production).  

- **Transport Layer**:  
  - TLS 1.3 Everywhere: MQTT (mutual certs), FastAPI (HTTPS), SNMP v3 (encrypted).  
  - Cipher Suites: AES-256-GCM-SHA384; no weak ciphers.  

- **Application Layer**:  
  - Input Validation: Pydantic schemas for all APIs/MQTT payloads; sanitize for injection.  
  - Rate Limiting: 10 requests/min on APIs (FastAPI middleware); MQTT message limits.  
  - Logging/Monitoring: All events to Prometheus (security_alerts_total metric); anomaly detection on access patterns.  

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
            RBAC[RBAC]
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

This SDD ensures Network-Chan is secure by design, with layered protections minimizing risks. It will be reviewed during Phase 3 security hardening.
