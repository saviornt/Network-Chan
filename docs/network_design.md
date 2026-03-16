# Network-Chan Network Design Document

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  
**Version:** 1.0  

## Introduction

This Network Design Document (NDD) details how Network-Chan integrates into various network environments as a standalone MLOps network appliance (Raspberry Pi 5) and its associated AIOps application (PC/server). It covers subnetting, routing, redundancy, failover strategies, and common network types (home, small business, enterprise). The design emphasizes local-only operation, safety-first principles (fail-open, recoverable states), and extensibility, aligning with the three-brain architecture: Perception (edge telemetry on Appliance), Decision/Governance (central on Assistant), and Execution (trusted daemon on Appliance).

Network-Chan fits as a management plane controller: the Appliance resides on a dedicated management VLAN for monitoring/remediation, while the Assistant connects via secure MQTT for analytics/UX. All designs assume TP-Link Omada ecosystem as primary, with Netmiko for multi-vendor support. No cloud dependencies; focus on on-premises resilience.

## High-Level Network Topology

Network-Chan deploys in a segmented topology to isolate management traffic, staging for experiments, and production. The Appliance (Pi 5) connects to the management VLAN, polling devices via SNMP/Netmiko/Omada API. The Assistant (PC) connects to the same LAN, subscribing to MQTT for data flows.

### Topology Diagram

```mermaid
graph TD
    subgraph "Home / SMB Network Example"
        A[Internet Modem / ISP Router]
        A --> B[TP-Link ER707-M2 Gateway<br>Omada SDN Controller]
        B --> C[Management VLAN<br>(192.168.100.0/24)]
        B --> D[Production VLAN<br>(192.168.1.0/24)]
        B --> E[Staging VLAN<br>(192.168.200.0/24)]
        C --> F[Network-Chan Appliance<br>(Pi 5 – Perception + Execution)]
        D --> G[Switches / Routers / APs / IoT Devices]
        E --> H[Mininet Sim / Lab Devices]
        F -->|SNMP/Netmiko/Omada API| G
        F -->|MQTT/TLS| I[Mosquitto Broker]
        I --> J[Network-Chan Assistant<br>(PC – Decision + Governance + UI)]
        J -->|Command Publish| I
        J --> K[Admin Workstation / Mobile<br>(Vue Dashboard Access)]
    end

    subgraph "Enterprise Network Example (Scaled)"
        L[Firewall / Core Router]
        L --> M[Management Network<br>(10.0.100.0/24)]
        L --> N[Production Network<br>(10.0.1.0/16)]
        L --> O[DMZ / Staging Network<br>(10.0.200.0/24)]
        M --> P[Network-Chan Appliance Cluster<br>(Multiple Pi 5s)]
        P -->|Multi-Vendor API/Netmiko| N
        P -->|MQTT/TLS| Q[Redundant Brokers]
        Q --> R[Network-Chan Assistant Server<br>(High-Avail Cluster)]
        R -->|Command Publish| Q
        R --> S[Enterprise Admin Console]
    end
```

Data Flows: Telemetry from devices → Appliance (perception) → MQTT → Assistant (decision/governance) → optional command back to Appliance (execution).

## Integration Points

- **Appliance Integration**: Ethernet connection to ER707-M2 or switch in management VLAN; polls via SNMP v3 (PySNMP), CLI (Netmiko), API (Omada REST). Exports Prometheus metrics (<http://pi-ip:8001/metrics>).  
- **Assistant Integration**: LAN connection to MQTT broker; subscribes to Appliance topics; optional direct API to Appliance for fallback (http over TLS). Vue dashboard at <http://assistant-ip:8000>.  
- **External Points**: Home Assistant (MQTT sensors/commands), Mininet (simulation API for testing), Grafana (embedded iframes in dashboard).  
- **Security Integration**: Mutual TLS certs for MQTT; RBAC on APIs; firewall rules (ufw on Pi: allow 8001/TCP LAN-only).

## Subnetting and Routing

Subnetting uses VLANs for isolation; routing via ER707-M2 (or core router in enterprise). Assume IPv4; IPv6 optional.

- **Subnetting Scheme** (Home/SMB Example):  
  - Management VLAN (VLAN 100): 192.168.100.0/24 (Appliance Pi at .10, MQTT broker at .20, Assistant at .30).  
  - Production VLAN (VLAN 1): 192.168.1.0/24 (devices/APs).  
  - Staging VLAN (VLAN 200): 192.168.200.0/24 (experimental/Mininet).  
  - Rationale: /24 for simplicity; separates traffic to prevent Appliance overload.  

- **Routing**:  
  - Inter-VLAN: ER707 as layer 3 router (static routes or OSPF for enterprise). Appliance routes via ER707 default gateway.  
  - NAT/Firewall: ER707 NATs to internet; ACLs block staging VLAN from production. Assistant routes to Pi via LAN switch.  
  - Dynamic Routing: OSPF/BGP in enterprise for redundancy; static in home/SMB.  

- **Enterprise Example**:  
  - Management Network: 10.0.100.0/24 (Appliance cluster).  
  - Production: 10.0.1.0/16 (segmented by dept).  
  - Staging/DMZ: 10.0.200.0/24.  
  - Routing: Core router (e.g., Cisco) with VRRP for failover; VLAN trunking to switches.

## Redundancy and Failover Strategies

- **Appliance Redundancy**: Single Pi in home (hot spare optional); cluster (2–3 Pis) in enterprise with VRRP for IP failover. Failover: Heartbeat script detects failure, switches MQTT broker endpoint.  
- **MQTT Broker**: Redundant Mosquitto instances (HA mode or cluster via MQTT 5.0 bridges); failover via DNS round-robin or Pi fallback broker.  
- **Assistant Failover**: Active-passive (manual switch in home); Kubernetes cluster in enterprise.  
- **Network Failover**: ER707 dual-WAN (ISP redundancy); Pi Ethernet failover via bonding if multi-NIC.  
- **Data Failover**: SQLite WAL mode + cron backups; FAISS index replication via rsync.  
- **General Strategies**: Fail-open (default device configs if Appliance down); 60s auto-rollback on failed changes; autonomy modes limit risk.

## Common Network Types and Network-Chan Fit

### Home Network

- **Typical Setup**: Modem → ER707 Gateway → Switch/APs (5–10 devices).  
  - Fit: Appliance on management VLAN monitors APs; auto-throttles guest Wi-Fi. Assistant on home PC for dashboard.  
  - Subnetting: Simple /24 VLANs. Routing: Static via ER707. Redundancy: None (low-cost). Failover: Manual Pi reboot.

### Small Business Network

- **Typical Setup**: Firewall → Core Switch → Multiple APs/VLANs (20–50 devices).  
  - Fit: Appliance clusters for multi-site; audits VLAN security. Assistant on server for reports.  
  - Subnetting: /24 per VLAN (management/production/guest). Routing: OSPF. Redundancy: Dual ER707 with VRRP. Failover: Auto-switch to spare Pi.

### Enterprise Network

- **Typical Setup**: Core Router/Firewall → Layer 3 Switches → Distributed APs (100+ devices).  
  - Fit: Appliance per site; multi-agent RL across routers. Assistant on VM cluster for centralized governance.  
  - Subnetting: /16 production, /24 management/DMZ. Routing: BGP/OSPF. Redundancy: N+1 Pi clusters, redundant brokers. Failover: VRRP + auto-failover scripts.

This NDD ensures Network-Chan integrates seamlessly into diverse networks, with emphasis on safety and resilience. It will be updated during Phase 1 with detailed configs.
