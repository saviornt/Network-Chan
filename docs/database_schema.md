# Network-Chan Database Schema

**Project name:** Network-Chan  
**Date:** 2026-03-21  
**Version:** 1.1 (updated for modular Pydantic + SQLAlchemy reality)  

## Introduction

Network-Chan uses **Pydantic v2 models** as the primary source of truth for data schemas and validation, with **SQLAlchemy** ORM to map those models to SQLite tables (embedded on both the Network Appliance and Application).

This approach ensures:

- Type safety and runtime validation (Pydantic).
- Automatic table creation/migration potential (SQLAlchemy metadata or future Alembic).
- Easy serialization for MQTT payloads, API responses, and logs.

**FAISS** is used alongside for vector embeddings (incident similarity search, RAG) — with metadata linked via SQLite foreign keys.

Key principles:

- Local-only, embedded (SQLite WAL mode for concurrency on Pi).
- Modular & layered: Shared models live in `/shared/src/network_chan_shared/models/`, but appliance-specific models go in `appliance/src/models/`, and application-specific models go in `application/src/models/`.
- Models created so far are conceptual and will be refactored as real needs emerge during implementation.
- Privacy & security: Redact PII before embedding; immutable audit logs.
- Replication: Appliance pushes new/changed records (incidents, audits, config) to Application via MQTT; no real-time sync to keep edge lightweight.
- Extensibility: All models are Pydantic-based → easy to add fields, validation, or MQTT serialization.

## Database Overview

- **Primary DB**: SQLite (WAL mode enabled for concurrent reads/writes on Pi).
- **Vector Store**: FAISS (file-based indexes; metadata in SQLite).
- **Usage Split**:
  - **Network Appliance** (edge): Local SQLite + small FAISS for real-time incidents, config, lightweight retrieval. Uses shared models + appliance-specific models.
  - **Application** (central): Mirrored SQLite (via MQTT deltas/full dumps) + full FAISS for long-term RAG, training history, analytics. Uses shared models + application-specific models.
- **Size Estimates**: <100 MB/year for home lab (10k incidents, 1k models); prune old entries (>90 days on edge).
- **Backup/Replication**: Cron rsync/SQLite `.backup` on edge; MQTT push of deltas to central.

## Model Organization

Models are split across the monorepo for clean layering:

- **Shared Models** (`shared/src/network_chan_shared/models/`):
  - Exported in `__init__.py`.
  - Used by both Appliance and Application.
  - Examples (conceptual; to be refactored as needed):
    - Incident models (`IncidentBaseModel`, `IncidentCreateModel`, `IncidentModel`, `IncidentRecord`, `IncidentEmbedding`, `IncidentLogEntry`)
    - Policy/Audit models (`PolicyCheckRequestModel`, `PolicyDecisionModel`, `PolicyAuditModel`, `PolicyAuditCreateModel`, `PolicyAuditReadModel`, `PolicyAuditRecord`)
    - Model Registry models (`ModelRegistryModel`, `ModelRegistryCreateModel`, `ModelRegistryReadModel`, `ModelRegistryRecord`)
    - Telemetry models (`TelemetrySampleModel`, `TelemetryPayloadModel`, `FeatureVectorModel`)
    - Vector/FAISS metadata (`VectorMetadataBase`, `VectorMetadataCreate`, `VectorMetadataRead`, `VectorSearchResult`, `FaissVectorMetadata`)
    - RL-related (`TransitionModel`, `EpisodeStatsModel`, `RLObservation`, `RLState`, `RLAction`, `RewardSignal`)
    - Auth (`LoginRequest`, `TokenResponse`, `TokenData`, `TotpSetupResponse`, `CurrentUser`)

- **Appliance-Specific Models** (`appliance/src/network_chan_appliance/models/`):
  - Edge-only concerns (e.g., local TinyML inference results, remediation execution logs, hardware-specific telemetry).
  - Examples (conceptual; to be created/refactored):
    - `LocalInferenceResultModel`
    - `RemediationExecutionModel`
    - `EdgeConfigModel`

- **Application-Specific Models** (`application/src/network_chan_application/models/`):
  - Central-only concerns (e.g., global training metrics, RAG query results, dashboard session data).
  - Examples (conceptual; to be created/refactored):
    - `GlobalTrainingMetricsModel`
    - `RagQueryResultModel`
    - `DashboardSessionModel`

## SQLAlchemy Mapping & Tables

SQLAlchemy tables are generated from Pydantic models (via `Base.metadata.create_all()` or future Alembic migrations).

Core inferred tables (based on current shared exports):

- **incidents** — From `Incident*` models
- **policy_audits** — From `PolicyAudit*` models
- **model_registry** — From `ModelRegistry*` models
- **faiss_vectors** — From `FaissVectorMetadata` / vector models
- **totp_users** — From `TotpSetupResponse` / auth models
- Others: telemetry_samples, transitions/episodes (RL), audit_events, etc.

**Indexes** (added via SQLAlchemy `__table_args__` or migrations):

- Time-range: `timestamp_start`, `timestamp_end`
- Foreign keys: `incident_id`, `faiss_vector_id`, `model_id`
- JSON fields: Use generated columns or SQLite JSON functions for queries

## Replication & Data Management

- **Appliance (edge)**: Local SQLite + small FAISS; periodic MQTT push of new/changed records (incidents, audits, config).
- **Application (central)**: Receives MQTT deltas → upsert into central tables; full FAISS for long-term RAG.
- **Backup**: Cron rsync/SQLite `.backup`; encrypted to local storage.
- **Retention**: Edge: Prune >90 days; Central: 1–2 years.

This schema is **code-defined** via Pydantic/SQLAlchemy models across the monorepo. The markdown is a high-level reference — actual tables and relationships are generated from the models themselves. Refactoring of conceptual models will occur as real usage patterns emerge during implementation.
