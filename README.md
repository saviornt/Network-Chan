# Network-Chan

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)

## Overview

Network-Chan is a local-only, research-grade autonomous SDN (Software-Defined Networking) management plane designed for home/lab environments, with potential scalability to prosumer or enterprise settings. It features a split architecture:

- **Appliance**: A lightweight, always-on edge MLOps controller running on a Raspberry Pi 5 for real-time telemetry ingestion, anomaly detection, and reinforced meta-learning (using TinyML, Q-Learning, and REPTILE).
- **Assistant**: A central AIOps controller on a PC/server for global training, policy optimization, explainable analytics (RL-MAML, GNNs), and user interaction via an LLM-grounded dashboard.

The system follows a three-brain, safety-first model:

- **Perception Brain**: Real-time data collection and edge inference.
- **Decision Brain**: Learning and policy generation.
- **Governance Brain**: Safety enforcement, RBAC, and fail-safes (e.g., fail-open design, recoverable snapshots).

Key principles: Local-only processing (no cloud), fail-open (network runs without AI), recoverable states, and policy-governed automation. Built with technologies like Prometheus for telemetry, FAISS for incident retrieval, Ray RLlib for RL, and FastAPI/Vue for the UI.

This monorepo contains code for both the Appliance and Assistant, along with shared utilities. The project is in early development, targeting an MVP for home lab testing.

## Goals and Success Criteria

- Build a safe, self-remediating SDN control plane that reduces manual intervention for issues like interface flaps or congestion.
- Enable multi-agent RL across network devices (e.g., switches/routers as agents).
- Provide an intuitive AIOps console with chat-based LLM advice and optional emotional/personality UX.
- KPIs: MTTD/MTTR <60s, false positive rate <3%, LLM accuracy >90%.

For full details, see [docs/vision.md](docs/vision.md) and the project proposal documents.

## Project Structure

This is a monorepo for easy management of interdependencies:

- **`appliance/`**: Edge MLOps code for the Raspberry Pi 5 (telemetry, edge RL, automation daemon).
- **`assistant/`**: Central AIOps code for the PC/server (LLM, dashboard, global training).
- **`shared/`**: Common utilities (e.g., DB schema, MQTT helpers).
- **`docs/`**: Documentation (architecture, backlog, risks).
- **`scripts/`**: Deployment and update scripts.
- **`tests/`**: Unit/integration tests (per component).

See individual READMEs in `appliance/` and `assistant/` for component-specific details.

## Prerequisites

- Python 3.12+
- Raspberry Pi 5 (for Appliance)
- TP-Link Omada SDN hardware (e.g., ER707-M2 router, OC200 controller) for initial testing
- Optional: Docker for containerized development

## Installation

1. Clone the repo:

   ```terminal
   git clone https://github.com/yourusername/Network-Chan.git
   cd Network-Chan
   ```

2. Create and activate a virtual environment:

   ```terminal
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies (run in subfolders as needed):

   ```terminal
   pip install -r appliance/requirements.txt
   pip install -r assistant/requirements.txt
   ```

4. For development: Install pre-commit hooks (once online):

   ```terminal
   pip install pre-commit
   pre-commit install
   ```

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
- **Coding Standards**: PEP 8, Google-style docstrings. Use Black for formatting.
- **Agile**: 2-week sprints; backlog in `docs/backlog.md`.
- **Tools**: VS Code recommended; GitHub Projects for Kanban.

See `docs/development_guidelines.md` for full details.

## Contributing

Contributions welcome! Fork the repo, create a feature branch, and submit a PR. Follow the code of conduct (to be added). For major changes, open an issue first.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by AIOps market trends and open-source tools like Ray, PyTorch Geometric, and Ollama.
- Thanks to xAI for Grok assistance in project planning.

For questions, contact Dave (project owner). Last updated: March 14, 2026.
