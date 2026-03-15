# Network-Chan MLOps Appliance

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)

## Overview

The Appliance is the edge MLOps component of Network-Chan, a local-only autonomous SDN management plane. It runs on a Raspberry Pi 5 as a lightweight, always-on controller focused on real-time operations. Key features include:

- **Telemetry Ingestion**: Collects network metrics via Prometheus scrapers, SNMP (PySNMP), Omada API, and psutil.
- **Edge Inference**: Lightweight anomaly detection and action selection using TinyML (TFLite/ONNX), Q-Learning for RL, REPTILE for meta-learning adaptation, and a quantized TinyGNN (e.g., Graph Convolutional Network or GCN) for topology-aware reasoning on network graphs.
- **Automation**: Trusted daemon for safe remediations (e.g., interface resets) with policy whitelists and rollbacks.
- **Transport**: Secure MQTT/TLS for telemetry pub/sub to the Assistant and incident logging, including model updates.
- **Config UI**: Simple web page (FastAPI) for on-device setup and status.

Designed for standalone autonomy: The Appliance operates independently if the Assistant is offline, ensuring fail-open safety (network continues without AI). It can create and utilize a small, efficient GNN locally for tasks like graph embeddings in Q-Learning states, while receiving optimized, quantized model updates from the Assistant's full GNN (e.g., via MQTT artifact publishing). This hybrid approach balances edge efficiency (<20ms inference, ~50–200KB model size) with advanced central training.

The Appliance feeds data to the central Assistant for global training while handling fast-loop decisions on the Pi.

This folder contains code specific to the Appliance. See the root [README.md](../README.md) for the full project overview.

## Goals and Success Criteria

- Provide millisecond-level reactions to local events (e.g., congestion, flaps) with >95% anomaly detection accuracy, enhanced by topology-aware GNN embeddings.
- Adapt models via few-shot meta-learning on the Pi without heavy compute.
- Integrate with SDN devices (primary: TP-Link Omada; extensible via Netmiko).
- KPIs: Inference <10ms, false positives <3%, episodic records for RAG.

For details, see [../docs/vision.md](../docs/vision.md).

## Folder Structure

- **`src/`**: Core Python code (e.g., `telemetry_ingest.py` for metrics, `edge_rl.py` for Q-Learning/REPTILE).
- **`tests/`**: Unit and integration tests (pytest).
- **`requirements.txt`**: Dependencies (e.g., torch, networkx, paho-mqtt).

## Prerequisites

- Raspberry Pi 5 (8GB recommended for ML).
- Python 3.12+ installed on the Pi (via apt or pyenv).
- Network access to SDN devices (e.g., ER707-M2 on management VLAN).
- Optional: Docker for containerized runs (arm64 support).

## Installation

1. Clone the monorepo and navigate here:

   ```terminal
   git clone https://github.com/SaviorNT/Network-Chan.git
   cd Network-Chan/appliance
   ```

2. Create and activate a virtual environment:

   ```terminal
   python -m venv .venv
   source .venv/bin/activate  # On Pi/Linux
   ```

3. Install dependencies:

   ```terminal
   pip install -r requirements.txt
   ```

4. Configure: Edit `src/config.py` (stub) for MQTT broker, device IPs, etc. Use .env for secrets.

5. Deploy as a service: Use systemd (example unit file in `scripts/appliance.service`—copy to /etc/systemd/system/).

## Usage

### Running the Appliance

- Start the main loop:

  ```terminal
  python src/main.py  # (Add this file as entry point; stub for telemetry + RL)
  ```

- Config Page: If using FastAPI for UI:

  ```terminal
  uvicorn src.app:app --host 0.0.0.0 --port 8001
  ```

  Access at `http://pi-ip:8001/config`.

### Example Workflow

- Telemetry collects every 10–60s.
- Anomalies trigger Q-Learning actions (e.g., throttle bandwidth).
- Publish episodes to MQTT for Assistant sync.
- Monitor logs: `journalctl -u network-chan-appliance` (if systemd).

For testing: Use Mininet sims or staging VLAN as per [../docs/network_design.md](../docs/network_design.md).

## Development Notes

- **Focus**: Keep lightweight for Pi (ARM CPU, no GPU needed—quantize models).
- **Testing**: Run `pytest tests/`; aim for 80% coverage.
- **Integration**: MQTT for Assistant comms; SQLite/FAISS for local storage.
- Follow root guidelines: Conventional Commits, PEP 8.

## Contributing

See root [README.md](../README.md) for guidelines. For Appliance-specific issues, label them "appliance".

## License

MIT License - see root [LICENSE](../LICENSE).

Last updated: March 14, 2026.
