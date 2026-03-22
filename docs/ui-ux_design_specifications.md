# Network-Chan UI/UX Design Specifications

**Project name:** Network-Chan  
**Date:** 2026-03-21  
**Version:** 1.1 (updated with Omada/UniFi/enterprise inspiration & LLM sidebar)  

## Introduction

This UI/UX Design Specs document outlines the user interface and experience for Network-Chan, covering:

- **Network Appliance** — minimal web-based configuration page (FastAPI + Jinja2) at `http://<appliance-ip>:8001/config` for initial setup, status, logs, and basic controls.
- **Application** — full-featured AIOps dashboard (FastAPI backend + Vue 3 + Vite frontend) for topology, analytics, LLM assistant, centralized config/logs view, and advanced controls.

**Design Inspirations** (based on research):

- **TP-Link Omada**: Clean card-based overview, health score gauge, traffic bars, device status colors (green/yellow/red) — the overall professional aesthetic you like.
- **UniFi Network Application**: Prominent topology map, real-time graphs, dark theme, client/traffic insights.
- **Enterprise (Cisco DNA Center, Aruba Central, Juniper Mist)**: Health scores, drill-down capability, policy matrices, reduced information density.
- **VS Code / Gemini Sidebar**: Persistent LLM Assistant sidebar — chat-only or interactive mode with buttons/forms for actions.

Principles:

- Safety-First: Clear confirmations, autonomy level indicators, audit logs visible.
- Intuitive & Responsive: Mobile-friendly, dark/light modes, keyboard navigation (WCAG 2.1 AA).
- Minimal Edge vs. Rich Central: Appliance UI is simple; Application dashboard is the primary interface.
- Local-Only: No cloud dependencies.

Tools: Figma for wireframes/mockups, Bootstrap 5/Tailwind for styling, Chart.js for visuals, Vis.js for topology, Web Speech API for voice.

## Network Appliance UI/UX (Minimal On-Device Configuration)

Served by FastAPI + Jinja2 at `http://<appliance-ip>:8001/config` — router-like admin page. Focus: onboarding, status, logs, basic controls.

**Key Features**:

- Forced TOTP 2FA setup on first login (QR code + verification).
- Status cards (uptime, autonomy level, last incident).
- Paginated log viewer.
- Basic config forms and autonomy level selector (0–5).
- Dark/light mode toggle.

**Wireframe (ASCII)**:

```text
+----------------------------+
| Network-Chan Appliance     |
| Configuration              |
+----------------------------+
| Status: Online             |
| Autonomy: 1 (Advisor)      |
| Uptime: 2d 3h              |
+----------------------------+
| Logs: [View]               |
| Actions: [Restart]         |
+----------------------------+
```

## Application UI/UX (Full AIOps Dashboard)

Primary interface. Runs as background service; accessed via browser or Electron wrapper.

**Layout & Structure** (inspired by Omada + UniFi + enterprise):

- **Top Bar**: Site selector, search, autonomy level indicator (slider/dropdown with tooltip), alerts bell.
- **Persistent LLM Sidebar** (like Github Copilot/Gemini in VS Code):
  - Toggleable (chat-only or interactive mode).
  - Chat-only: Simple conversation history with buttons/forms for actions (e.g., "Apply Fix", "Show Topology", "Change Autonomy", "Run Diagnostic")
  - Interactive mode: AI Character with VAD-based personality (optional emojis, voice and tonal changes) based on network state and context. Web Speech API for voice input.
- **Main Content**:
  - Overview tab: Card-based dashboard (health score gauge like Omada, device counts, traffic bars).
  - Topology tab: Full-screen Vis.js map (like UniFi) with device connections, signal strength, color-coded status.
  - Clients/Traffic tabs: Real-time graphs, top clients/apps, heatmaps.
  - Centralized Config/Logs: Table + search (pulls from Appliance via MQTT).
  - Export buttons (PDF/CSV) in footer.

**Style Guide** (Omada-inspired with improvements):

- Color Palette: Primary blue (#007bff), success green, warning yellow, danger red.
- Typography: Clear, concise labels (improved wording vs. Omada).
- Icons: Bootstrap Icons + custom network graph.
- Layout: Responsive grid; reduced density with logical grouping.
- Dark Mode: System preference + toggle.
- Accessibility: ARIA roles, high contrast, keyboard nav.

**Onboarding Flow (Both Layers)**:

1. First access → Login + forced TOTP setup (QR + verification).
2. Appliance: Basic config (MQTT broker, autonomy start at 1).
3. Application: Connect to Appliance MQTT, pull initial config/logs.
4. Dashboard shows unified view; LLM sidebar ready for queries/actions.

This spec provides the foundation for implementation. Wireframes/mockups can be prototyped in Figma for iteration.
