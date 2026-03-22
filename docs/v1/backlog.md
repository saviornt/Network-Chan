# Product Backlog for Network-Chan

This is a prioritized, living backlog based on the agile artifacts document. Groomed for Appliance MVP focus. Estimated in Fibonacci points.

## Epics

- EP-001: Perception & Telemetry (Ingest and process network data on edge).
- EP-002: Decision & Learning (Edge RL/meta-learning + central training).
- EP-003: Governance & Safety (Policy enforcement, RBAC).
- ... (Expand as needed; see full in agile doc).

## Prioritized Stories/Tasks

| Priority | Type  | ID     | Description                                                                 | Epic    | Points | Dependencies                  | Acceptance Criteria |
|----------|-------|--------|-----------------------------------------------------------------------------|---------|--------|-------------------------------|---------------------|
| 1        | Epic  | EP-001| Perception & Telemetry Ingest                                              | -       | -      | -                             | -                   |
| 2        | Story | US-001| As a system, ingest real-time telemetry from Omada/psutil/SNMP so features can be built. | EP-001 | 8      | Hardware setup                | Metrics scraped every 10-60s; stored in SQLite; >95% uptime in tests. |
| 3        | Story | US-002| As an edge controller, implement lightweight anomaly detection on Pi.     | EP-001 | 5      | US-001                        | TinyML model runs <10ms; detects flaps >95% accuracy in mocks. |
| 4        | Epic  | EP-002| Decision & Learning Systems                                                | -       | -      | EP-001                        | -                   |
| 5        | Story | US-003| As an edge RL agent, implement Q-Learning for action selection on Pi.     | EP-002 | 5      | US-002                        | Q-table updates async; rewards simulated; Numba for perf. |
| 6        | Story | US-004| As a meta-learner, implement REPTILE for model adaptation on Pi.          | EP-002 | 8      | US-003                        | Few-shot tasks adapt weights >5%; async loops. |
| 7        | Story | US-005| As a central trainer, implement GNNs (PyG) for topology reasoning on Assistant. | EP-002 | 8      | EP-001                        | Graph embeddings generated; quantized pushes via MQTT. |
| 8        | Task  | TK-001| Add type annotations and async stubs to all shared utils.                 | EP-001 | 2      | -                             | MyPy checks pass; no sync blocking. |
| ...      | ...   | ...    | (Add more from agile doc; groom weekly)                                    | ...     | ...    | ...                           | ...                 |

## Definition of Ready (DoR)

- Story has clear acceptance criteria.
- Dependencies resolved.
- Estimated in points during planning.

## Definition of Done (DoD)

- Code reviewed (PR approved).
- Tests pass (>80% coverage).
- Docs updated (e.g., README stubs).
- Deployed to staging (Mininet/Pi).
- No lint errors (Black, MyPy).

Backlog groomed on: March 15, 2026. Use GitHub Issues for tracking once online.
