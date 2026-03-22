# Network-Chan UI/UX Design Specifications

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  
**Version:** 1.0  

## Introduction

This UI/UX Design Specs document outlines the user interface and experience for Network-Chan, covering both the MLOps Network Appliance (simple, on-device configuration page on Raspberry Pi 5) and the associated AIOps Application (full-featured dashboard on the Assistant PC/server). The design prioritizes safety, usability, and extensibility, aligning with the three-brain architecture: Perception (data views), Decision (analytics/insights), and Governance (controls/approvals).

UI/UX principles:

- **Safety-First**: Clear confirmation for destructive actions, autonomy mode indicators, audit logs accessible.
- **Intuitive & Responsive**: Mobile-friendly (Bootstrap grid), dark/light modes, keyboard navigation (WCAG 2.1 AA).
- **Fun yet Professional**: Optional emotional/personality overlays (VAD-based tones) for chat; default neutral.
- **Tools Used**: Figma for wireframes/mockups, Bootstrap 5 for styling, Chart.js for visuals, Vis.js for topology.

Specs include wireframes (low-fidelity sketches), mockups (high-fidelity descriptions), and style guides. All designs are local-only, no cloud dependencies.

## Appliance UI/UX (Simple On-Device Configuration Page)

The Appliance UI is a minimal, consumer-like web page served by FastAPI (at <http://pi-ip:8001/config>), similar to a router's admin panel. It focuses on setup, status viewing, and basic controls— no advanced analytics or chat. Target users: Admins needing quick local access without Assistant.

### Appliance Wireframes

**Login/Welcome Page** (Low-Fidelity Sketch – ASCII Art):

```text
+----------------------------+
|       Network-Chan Appliance |
|        Configuration        |
+----------------------------+
| Username: [input]          |
| Password: [input]          |
| [Login Button]             |
+----------------------------+
| Status: Online             |
| Uptime: 2 days 3 hours     |
+----------------------------+
```

**Main Config Dashboard** (Low-Fidelity Sketch):

```text
+----------------------------+
| Dashboard | Config | Logs  |
+----------------------------+
| Network Status             |
| Clients: 18                |
| Devices: 12                |
| Anomaly Score: 0.12        |
+----------------------------+
| Learned Parameters         |
| Congestion Threshold: 0.68 |
| [Edit] [Reset]             |
+----------------------------+
| MQTT Broker: localhost:1883|
| [Save Changes]             |
+----------------------------+
```

### Appliance Mockups

**Login Page Mockup Description**: Clean, centered form on white/dark background. Bootstrap card with logo (simple network icon). Input fields with validation (red borders on error). Button: Primary blue (#007bff). No fancy animations—fast load on Pi.

**Main Config Dashboard Mockup Description**: Tabbed layout (Bootstrap nav-tabs). Status section: Green/red indicators for health. Learned parameters: Editable table with tooltips (e.g., "Threshold learned from REPTILE"). Save button with confirmation modal. Style: Minimalist, sans-serif fonts, responsive columns for mobile (collapses to single column <768px).

### Appliance Style Guide

- **Color Palette**:  
  - Primary: #007bff (blue – actions/buttons).  
  - Success: #28a745 (green – OK status).  
  - Warning: #ffc107 (yellow – anomalies).  
  - Danger: #dc3545 (red – alerts).  
  - Neutral: #6c757d (gray – text).  
  - Background: #f8f9fa (light) / #343a40 (dark).  

- **Typography**:  
  - Font Family: Roboto (sans-serif, Google Fonts CDN).  
  - Headings: H1 24px bold, H2 20px, H3 16px.  
  - Body: 14px regular.  
  - Code/Logs: Monaco monospace, 12px.  

- **Icons**: Bootstrap Icons (CDN) – e.g., bi bi-gear for config, bi bi-shield-check for security. Size: 24px.  

- **Layout**: Bootstrap grid (12-column responsive). Padding: 20px. Modals for confirms. Accessibility: ARIA labels, high contrast (4.5:1 ratio), keyboard nav.

- **Dark Mode**: Toggle via button; auto-detect system pref (prefers-color-scheme media query).

## AIOps Application UI/UX (Full-Featured Dashboard on Assistant)

The AIOps Application is the rich, interactive dashboard (Vue 3 served by FastAPI), incorporating emotional/personality UX, chat, voice, analytics, and reports. Target users: Admins seeking insights and control.

### Application Wireframes

**Login Page** (Low-Fidelity Sketch):

```text
+----------------------------+
|       Network-Chan         |
|        Login               |
+----------------------------+
| Username: [input]          |
| Password: [input]          |
| TOTP Code: [input]         |
| [Login Button]             |
| [Generate QR for Setup]    |
+----------------------------+
| Dark Mode Toggle           |
+----------------------------+
```

**Main Dashboard Overview** (Low-Fidelity Sketch):

```text
+----------------------------+
| Overview | Analytics | Chat |
+----------------------------+
| Network Topology [Vis.js]  |
+----------------------------+
| Status Gauges              |
| Clients: 18 [Green]        |
| Anomaly: 0.12 [Yellow]     |
+----------------------------+
| Alert Timeline [Chart.js]  |
+----------------------------+
| Learned Predictions        |
| Congestion: 0.68 [Heatmap] |
+----------------------------+
| [Export PDF/CSV]           |
+----------------------------+
```

**Chat Interface** (Low-Fidelity Sketch):

```text
+----------------------------+
| Chat with Network-Chan     |
+----------------------------+
| [Personality Dropdown]     |
| [Voice Toggle Button]      |
+----------------------------+
| Log:                       |
| User: What's the status?   |
| Chan: All good [Joy Icon]  |
+----------------------------+
| Input: [text field]        |
| [Send]                     |
+----------------------------+
```

### Application Mockups

**Login Page Mockup Description**: Centered Bootstrap card with Network-Chan logo (network graph icon). TOTP field with QR button (pops modal with base64 image). Dark mode toggle in corner. Background gradient (blue to gray). Button: Primary blue, rounded.

**Main Dashboard Overview Mockup Description**: Tabbed nav (Bootstrap tabs). Topology: Vis.js interactive graph with nodes (devices, colored by status). Gauges: Chart.js doughnuts for metrics (green/red). Timeline: Chart.js line with annotations for alerts. Heatmap: Chart.js matrix for anomalies over time. Export buttons in footer. Responsive: Mobile stacks sections vertically.

**Chat Interface Mockup Description**: Card layout with scrollable log. Bubbles: User right-aligned (blue), Chan left-aligned (gray, with VAD emoji if enabled, e.g., smiling for joy). Personality dropdown: Select changes tone (e.g., "waifu" adds cute phrasing). Voice button: Mic icon, toggles recording. Dark mode: Inverts colors for readability.

### Application Style Guide

- **Color Palette**:  
  - Primary: #007bff (blue – buttons/actions).  
  - Success: #28a745 (green – healthy status).  
  - Warning: #ffc107 (yellow – anomalies).  
  - Danger: #dc3545 (red – alerts/failures).  
  - Neutral: #6c757d (gray – text).  
  - Background: #f8f9fa (light) / #343a40 (dark).  
  - Accent: #fd7e14 (orange – learned insights).  

- **Typography**:  
  - Font Family: Roboto (sans-serif, primary), Monaco (monospace for logs/code).  
  - Headings: H1 28px bold, H2 24px, H3 18px.  
  - Body: 14px regular.  
  - Chat: 16px for readability.  

- **Icons**: Bootstrap Icons + custom (e.g., network graph for topology). Size: 24–32px.  

- **Layout**: Bootstrap 12-column grid, responsive breakpoints (mobile <576px stacks, tablet 768px adjusts). Padding: 15–20px. Modals for confirms/QR. Animations: Subtle CSS transitions (e.g., fade-in alerts, 0.3s).

- **Dark Mode**: System pref detect + toggle; invert colors (white text on dark bg).  

- **Accessibility**: ARIA roles (e.g., aria-live for chat updates), alt text for icons/charts, contrast 4.5:1+, keyboard focus styles.  

- **Emotional UX**: VAD indicators as subtle icons/colors (e.g., green glow for positive valence); personality toggles change bubble styles (e.g., rounded for waifu, sharp for rogue).

This spec provides a foundation for implementation—wireframes/mockups can be prototyped in Figma for iteration.
