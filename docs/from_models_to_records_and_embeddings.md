# FAISS Embedding Integration Pattern

Network-Chan uses a **hybrid storage approach** for semantic search and RAG:

- **SQLite** (`network_chan.db`): Source of truth for structured records (full ORM models: `XxxRecord` classes).
- **FAISS** (`network_chan_vectors.index`): Fast vector similarity search (embeddings only).
- **Bridge table** (`faiss_vectors_metadata`): Links every FAISS vector back to its SQLite entity.

## Generic Embedding & Indexing Flow

When creating or updating any persistent entity that should be searchable via FAISS (e.g. Incident, AuditEvent, PolicyDecision, AnomalyDetectionResult, ModelRegistry):

### 1. Generate embedding text

Combine key fields into a concise, meaningful string.  
Examples:  

- Incident: description + severity + root_cause + affected_devices  
- AuditEvent: action_type + actor + reason + before/after_state summary  
- Anomaly: reason + related_metrics + severity + anomaly_score  
   → Use a consistent embedding model (e.g. `all-MiniLM-L6-v2` from sentence-transformers).

### 2. Add to FAISS index

```python
index = FaissIndex.load_or_create()  # from shared/src/database/faiss.py
vector_id = index.add(embedding_vector)  # returns internal FAISS int ID
```

### 3. Create bridge metadata record

Insert into `faiss_vectors_metadata` table:

```python
metadata = FaissVectorMetadata(
    vector_id=vector_id,
    entity_type="audit_event",          # or "incident", "anomaly_detection_result", etc.
    entity_id=new_record.id,            # UUID of the XxxRecord
    description=short_summary[:500],    # optional, generated or from model
    embedding_model="all-MiniLM-L6-v2", # or from config/service
    extra={
        "action_type": event.action_type,  # example fields
        "approved": event.approved,
        "severity": record.severity,
        # ... any other context useful for filtering or display
    }
)
await db.add(metadata)
await db.commit()
```

### 4. Retrieval pattern (for RAG / similarity search)

```python
# FAISS search → get top-k vector_ids + distances
vector_ids, distances = index.search(query_embedding, k=5)

# Lookup metadata for those vector_ids
metadata_rows = await db.execute(
    select(FaissVectorMetadata).where(FaissVectorMetadata.vector_id.in_(vector_ids))
).scalars().all()

# Fetch full records from SQLite
full_records = await db.execute(
    select(XxxRecord).where(XxxRecord.id.in_([m.entity_id for m in metadata_rows]))
).scalars().all()
```

## Implementation Location

All embedding, indexing, and bridge creation logic should live in service layers, not in model files or low-level CRUD:

- `shared/src/services/anomaly_service.py`
- `shared/src/services/audit_service.py`
- `shared/src/services/incident_service.py`
- `shared/src/services/policy_service.py`
etc.

This keeps models focused on structure/validation and services responsible for business logic + persistence + vectorization.
Guidelines

- Only embed entities that benefit from semantic search (incidents, audits, policy decisions, anomalies, model versions).
- Use consistent embedding model across the system (configurable via settings).
- Keep description ≤ 500 chars for bridge records (truncate if needed).
- Log embedding operations with structured logging (get_logger(component="faiss")).
- Handle FAISS index loading/creation failures gracefully (e.g. fallback to empty index in dev).

This pattern ensures traceability (SQLite), fast semantic retrieval (FAISS), and clean separation of concerns.
