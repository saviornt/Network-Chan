# Network-Chan Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)

## Overview

The Assistant is the central AIOps component of Network-Chan, a local-only autonomous SDN management plane. It runs on a more powerful PC/server/workstation for advanced processing and user interaction. Key features include:

- **Global Training**: Advanced model training and policy optimization using RL-MAML (Ray RLlib), full GNNs (PyTorch Geometric) for topology reasoning, and model quantization for edge pushes.
- **Explainable Analytics**: LLM-grounded advice (Ollama + LangChain for RAG) with persistent incident memory (SQLite + FAISS).
- **Governance**: Policy enforcement, RBAC, autonomy modes, and safety checks (e.g., immutable audits, approval workflows).
- **Admin UI/UX**: Full-featured dashboard (Vue 3 with Chart.js/Vis.js for visuals/topology), chat interface, optional TTS/STT, and emotional/personality expression (VAD model).
- **Integration**: MQTT/TLS for secure sync with the Appliance, including publishing quantized GNN models (e.g., full GNN trained here, optimized for Appliance's TinyGNN).
- **Multi-Agent RL**: Models network devices as agents (PettingZoo env) for system-wide optimization.

The Assistant complements the Appliance's edge autonomy by handling compute-intensive tasks, providing richer insights, and pushing updates (e.g., quantized GNNs via MQTT) to enhance the Pi's standalone capabilities. It ensures explainable, grounded operations while maintaining local-only privacy.

This folder contains code specific to the Assistant. See the root [README.md](../README.md) for the full project overview.

## Goals and Success Criteria

- Deliver high-precision remediation and predictions via central GNN/RL training, with updates to the Appliance for 20–40% improved edge performance on graph data.
- Provide usable AIOps tools: LLM accuracy >90%, intuitive UX with <3% false positives in governance.
- Scale to multi-agent scenarios (e.g., VLAN optimizations) while enforcing safety.
- KPIs: MTTD/MTTR <60s overall, high-precision incident retrieval, seamless model pushes.

For details, see [../docs/vision.md](../docs/vision.md).

## Folder Structure

- **`src/`**: Core Python code (e.g., `llm_rag.py` for LLM/RAG, `global_trainer.py` for RL/GNN, `app.py` for FastAPI).
- **`tests/`**: Unit and integration tests (pytest).
- **`requirements.txt`**: Dependencies (e.g., ray[rlib], torch-geometric, langchain, fastapi).

## Prerequisites

- PC/server with sufficient CPU/GPU (e.g., for GNN training).
- Python 3.12+.
- Access to Appliance via local network (MQTT broker).
- Optional: Vue CLI for frontend dev, Docker for containerization.

## Installation

1. Clone the monorepo and navigate here:

   ```terminal
   git clone https://github.com/SaviorNT/Network-Chan.git
   cd Network-Chan/assistant
   ```

2. Create and activate a virtual environment:

   ```terminal
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:

   ```terminal
   pip install -r requirements.txt
   ```

4. Frontend Setup (if using Vue dashboard):

   ```terminal
   cd src/frontend  # (Add this subfolder as needed)
   npm install
   ```

5. Configure: Edit `src/config.py` for MQTT, LLM model (e.g., Ollama endpoint), DB path.

## Usage

### Running the Assistant

- Start the FastAPI backend:

  ```terminal
  uvicorn src.app:app --reload
  ```

  Access API at `http://localhost:8000` (Swagger docs at `/docs`).

- Run Training Loop (e.g., for GNN/RL):

  ```terminal
  python src/global_trainer.py  # Processes Appliance data, pushes quantized models via MQTT
  ```

- Dashboard: Serve Vue app:

  ```terminal
  npm run serve  # Local dev server
  ```

  Access at `http://localhost:5173` (or integrated with FastAPI).

### Example Workflow

- Subscribe to MQTT for Appliance telemetry.
- Train full GNN on aggregated data; quantize and publish to Appliance.
- User queries via chat: LLM retrieves incidents via FAISS RAG, provides grounded advice.
- Governance: Approve/reject actions with RBAC checks.

For testing: Simulate with Mininet or connect to live Appliance as per [../docs/test_plans.md](../docs/test_plans.md).

## Development Notes

- **Focus**: Handle heavy compute (e.g., full GNN with PyG); optimize for quantization (TFLite/ONNX) before MQTT pushes.
- **GNN Integration**: Train complex models (e.g., GraphSAGE); push int8-quantized versions to Appliance for dynamic loading.
- **Testing**: Run `pytest tests/`; include end-to-end with MQTT mocks.
- **Integration**: FastAPI for APIs; Vue for UX; Ollama for local LLM.
- Follow root guidelines: Conventional Commits, PEP 8.

## Contributing

See root [README.md](../README.md) for guidelines. For Assistant-specific issues, label them "assistant".

## License

MIT License - see root [LICENSE](../LICENSE).

Last updated: March 14, 2026.
