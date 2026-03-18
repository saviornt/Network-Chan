# Network-Chan

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Network-Chan Project Board](https://img.shields.io/badge/Project%20Board-View-blue?logo=github)](https://github.com/users/saviornt/projects/8)

Private, autonomous SDN NetOps – edge intelligence meets central reasoning

## Overview

Network-Chan is a **local-only**, research-grade autonomous SDN management plane tailored for home/lab environments, with extensibility toward prosumer and small-to-medium business use cases.

It uses a split architecture with three clearly separated layers:

- **Appliance**  
  Lightweight, always-on edge MLOps controller running on Raspberry Pi 5.  
  Handles real-time telemetry ingestion, anomaly detection, lightweight inference (TinyML), topology-aware reasoning (GNNs), and reinforced meta-learning (TinyML + TinyGNN + Q-Learning + REPTILE).

- **Assistant**  
  Central AIOps controller running on a PC or server.  
  Performs global training, policy optimization, explainable analytics (RL-MAML, GNNs), incident retrieval (FAISS), and user interaction via an LLM-grounded dashboard.

- **Governance Layer**  
  Enforces safety-first policies: autonomy modes, RBAC, fail-open design, recoverable snapshots/rollback, and audit trails.

**Core principles**:

- Fully local processing — **zero cloud dependency**
- Fail-open: network continues to function even if AI components are offline
- Recoverable: every change is snapshotted with automatic rollback on failure
- Policy-governed: all actions are whitelisted and constrained by configurable autonomy levels
- Safety and Security without compromising functionality or user control

**Technology highlights**:

- Telemetry & observability: Prometheus, psutil, Netmiko, PySNMP, and manufacturer APIs
- ML/RL: ONNX Runtime (edge inference), PyTorch Geometric (GNNs), Ray RLlib (training), Numba (performance)
- Dashboard UI/UX: FastAPI (both layers), Jinja2 (Appliance config), Vue 3 (Assistant dashboard)
- Comms & security: asyncio-mqtt (TLS), Pydantic v2, pyotp (2FA/TOTP)

This monorepo contains the code for Appliance, Assistant, and shared utilities (models, settings, auth, MQTT helpers).  
The project is in early development — currently focused on allowing the MLOps controller to retrieve telemetry and statistics from network devices and provide basic MLOps at the edge. We are currently targeting an MVP for home-lab testing in Q2 2026.

## Goals and Success Criteria

- Build a safe, self-remediating SDN control plane that reduces manual intervention for issues like interface flaps or congestion.
- Enable multi-agent RL across network devices (e.g., switches/routers as agents).
- Provide an intuitive AIOps application with data analytics, network adminstration through a central application (manually and AI-driven), with a chat-based LLM assistant that can provide recommendations and insights, and is optionally integrated with with emotional/personality UX.
- KPIs: MTTD/MTTR <60s, false positive rate <3%, LLM accuracy >90%.

For full details, see [docs/vision.md](docs/vision.md) and the project proposal documents.

## Project Structure

This is a monorepo for easy management of interdependencies:

- **`appliance/`**: Edge MLOps code for the Raspberry Pi 5 (telemetry, edge RL, automation daemon).
- **`assistant/`**: Central AIOps code for the PC/server (LLM, dashboard, global training).
- **`shared/`**: Common utilities (e.g., DB schema, MQTT helpers).
- **`docs/`**: Documentation (architecture, backlog, risks, etc).
- **`scripts/`**: Deployment and update scripts.

See individual READMEs in `appliance/` and `assistant/` for component-specific details.

## Prerequisites

- Python 3.12+
- Raspberry Pi 5 (for Appliance)
- TP-Link Omada SDN hardware (e.g., ER707-M2 router, OC200 controller) for initial testing
- Optional: Docker for containerized development

## Usage

### Running the Appliance (Edge Controller)

- Navigate to `appliance/` and follow its README for setup.
- Example: `python src/main.py` (stub—expand as code develops).

### Running the Assistant (Central Controller)

- Navigate to `assistant/` and start the FastAPI server:

  ```terminal
  uvicorn src.app:app --reload
  ```

- Access the API at `http://localhost:8000` (docs at `/docs`).

### Testing

- Run tests: `pytest appliance/tests/` or `pytest assistant/tests/`.

For live home lab deployment: Configure VLANs as per `docs/network_design.md`, deploy to Pi, and test in staging.

## Development Guidelines

- **Branching**: Use GitHub Flow (feature branches from `main`).
- **Commits**: Follow Conventional Commits (e.g., `feat: add telemetry ingest`).
- **Coding Standards**: PEP 8, Google-style docstrings. Use Ruff for linting & formatting.
- **Fast-Agile**: 1-2 day sprints; backlog in `docs/backlog.md`.
- **Tools**: VS Code recommended; GitHub Projects for Kanban and issue tracking.

See `docs/development_guidelines.md` for full details.

## Contributing

Contributions welcome! Fork the repo, create a feature branch, and submit a PR. Follow the code of conduct (to be added). For major changes, open an issue first.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by AIOps market trends and open-source tools like Ray, PyTorch Geometric, and Ollama.

Last updated: March 17, 2026.
