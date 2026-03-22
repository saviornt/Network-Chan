# Network-Chan Autonomous NetOps Architecture

## System Overview

The **Network-Chan ecosystem** consists of two cooperating systems:

1. **MLOps Controller (Edge Device)**
   Runs on the **Raspberry Pi 5** within the network and performs real-time telemetry collection, machine learning inference, and automated remediation.

2. **AIOps Platform (Operations Server)**
   Runs on a separate PC or server and provides observability, analytics, operator interaction, and higher-level reasoning through dashboards and AI assistants.

Both systems communicate primarily through **MQTT messaging**.

```text
Network Devices
      │
      ▼
Network-Chan MLOps Controller (Edge)
      │
      ▼
MQTT Message Bus
      │
      ▼
Network-Chan AIOps Platform (Server)
      │
      ▼
Vue NOC Dashboard + LLM Assistant
```

---

## 1. MLOps Controller (Edge System)

Purpose:
Provide **autonomous network optimization and remediation** directly within the network.

Typical hardware:

```text
Raspberry Pi 5
PCIe NVMe storage
Active cooling
```

This system focuses on **low-latency decision making**.

---

### Core Responsibilities

#### Telemetry Collection

Sources include:

* Omada API
* SNMP
* Netmiko
* psutil
* device polling

Collected metrics:

```text
latency
packet loss
link utilization
wifi channel usage
client count
CPU load
temperature
error counters
```

---

#### Feature Engineering Pipeline

Telemetry is converted into ML-ready features.

Example transformations:

```text
raw metrics
   │
window aggregation
   │
trend detection
   │
feature vector
```

Example output:

```text
{
 latency_mean_30s: 18,
 packet_loss_rate: 0.01,
 client_density: 36,
 bandwidth_trend: 0.62,
 wifi_noise_floor: -89
}
```

---

### ML Decision Engine

The MLOps controller runs lightweight models:

#### TinyML

Used for:

```text
anomaly detection
predictive network failure
traffic pattern analysis
```

---

#### TinyGNN

Represents the network topology as a graph:

Nodes:

```text
routers
switches
access points
clients
```

Edges:

```text
wired links
wireless associations
routing paths
```

This allows prediction of:

```text
congestion propagation
routing bottlenecks
device dependency chains
```

---

#### Reinforcement Learning

Algorithms:

```text
Q-Learning
REPTILE meta-learning
```

Purpose:

Learn optimal responses to network conditions.

Example state:

```text
latency
packet_loss
client_load
wifi_interference
```

Possible actions:

```text
change AP channel
reassign clients
restart device
modify bandwidth rules
reroute traffic
```

Reward function example:

```text
reward =
 - latency
 - packet_loss
 - congestion
 + network stability
```

---

### Policy Engine

The policy engine acts as a **safety layer** between ML decisions and automation.

Example rules:

```text
max_device_reboots_per_hour = 1
max_channel_changes_per_10min = 2
```

Autonomy levels:

```text
0.  Observer: AI is in observe only, all changes must be manually performed
1.  Advisor: AI can suggest actions, but requires manual approval
2.  Supervised: AI makes recommendations and then the user can apply that recommendation or decline
3.  Semi-Autonomous: AI can make small remediations that will not cause network outages, but larger changes require approval
4.  Autonomous: AI is in full autonomous mode but is still dependant on policy guidelines
5.  Experimental: AI can make any change it wants, but all changes are logged and can be rolled back
```

---

### Automation Layer

Automation executes approved actions using:

```text
Omada API
Netmiko
SNMP write commands
```

Examples:

```text
set_wifi_channel
restart_access_point
disable_port
apply_bandwidth_limit
reconfigure_vlan
```

---

### MQTT Event Publishing

The controller publishes structured events to MQTT topics.

Example topic hierarchy:

```text
network-chan/
   telemetry/
   anomalies/
   actions/
   ai-insights/
   system/
```

Example event:

```text
network-chan/anomalies/ap1

{
 anomaly_score: 0.92,
 type: "wifi_interference",
 suggested_action: "channel_change"
}
```

---

Perfect — I can add a **Security Layer section** to the MLOps Controller and document **security practices for the entire Network-Chan ecosystem**. I’ll incorporate your points and provide a clear structure.

---

### Security Layer

Ensures that the edge controller not only manages network performance but also maintains the integrity, confidentiality, and availability of network operations.

**Responsibilities:**

1. **Anomaly Detection for Security Threats**

   * Monitors traffic patterns, device behavior, and system metrics.
   * Detects unusual activity such as:

     * Unexpected network scans
     * Port scanning attempts
     * Unusual bandwidth spikes
     * Rogue device connections
   * Generates alerts and publishes them to the **MQTT broker** for AIOps monitoring.

2. **Security Audits**

   * Periodically checks the configuration and status of network devices.
   * Verifies compliance with baseline security policies.
   * Produces reports for review in both MLOps and AIOps dashboards.

3. **Integration with Existing Security Appliances**

   * Interfaces with firewalls, IDS/IPS, and other appliances on the network.
   * Can push recommended policies or suggest automated actions based on ML insights.
   * Provides a unified view of both MLOps-driven actions and existing security controls.

4. **Secure Access to Dashboards**

   * Admin authentication requires:

     * Username and password
     * Time-based One-Time Password (TOTP)
   * Applies to both **MLOps and AIOps dashboards**.

5. **Encrypted Messaging**

   * All MQTT messages are encrypted with **SSL/TLS**.
   * Ensures telemetry, alerts, and automation commands are transmitted securely.

6. **Data Privacy**

   * Any **Personally Identifiable Information (PII)** in logs is automatically redacted before storage or transmission.
   * Promotes compliance with GDPR and privacy best practices.

---

### Security Flow Example

```text
Network telemetry → Security Layer anomaly detection
       │
       ▼
Alert generated → MQTT (SSL/TLS)
       │
       ▼
AIOps Dashboard / Admin
       │
       ▼
Optional automated remediation / integration with firewall or IDS
```

---

## 2. Security Practices in the Network-Chan Ecosystem

1. **Dashboard Access**

   * Both MLOps and AIOps dashboards require **strong credentials** + **TOTP 2FA**.
   * Logs of admin access are recorded and monitored for unusual login attempts.

2. **Data Transmission**

   * All MQTT communication is encrypted via **SSL/TLS**.
   * TLS certificates can be self-signed or issued by an internal PKI.
   * Optionally, mutual TLS authentication can be implemented for additional trust between MLOps and AIOps systems.

3. **Data Handling**

   * Telemetry and logs are filtered for PII before storage or transmission.
   * Sensitive information, such as client MAC addresses or device identifiers, is anonymized if necessary.
   * Retention policies control how long logs and ML datasets are stored on the NVMe SSD.

4. **Model & Automation Safety**

   * ML models are sandboxed in containers.
   * Policy engine ensures that even if an ML model produces unexpected actions, they **cannot violate security rules** (e.g., disabling firewall rules, opening ports).

5. **Audit & Compliance**

   * Both controllers maintain **audit trails** of actions, policy changes, and automated events.
   * Reports are accessible to admins through the dashboards.
   * Facilitates regulatory compliance for enterprise or SMB networks.

---

## 2. AIOps Platform (Operations Server)

Purpose:

Provide **human oversight, analytics, and orchestration tools** for administrators or NOCs.

Runs on:

```text
PC
home server
datacenter server
```

It **subscribes to MQTT topics published by the MLOps controller**.

---

### Core Components

#### Data Ingestion

The AIOps platform subscribes to:

```text
network-chan/telemetry
network-chan/anomalies
network-chan/actions
network-chan/system
```

Data is stored in:

```text
time series database
analytics warehouse
log archive
```

---

#### Vue NOC Dashboard

Primary operator interface.

Functions:

Network visualization

```text
device health map
latency heatmaps
topology graphs
```

Operational monitoring

```text
alerts
anomaly reports
device status
automation history
```

Administrative tools

```text
autonomous mode controls
policy editing
device management
log viewer
```

---

#### LLM Assistant

The AIOps system includes an AI assistant that can:

```text
explain network anomalies
summarize incidents
recommend remediation steps
generate configuration suggestions
```

Example queries:

```text
Why did latency spike at 14:30?
Which device caused packet loss today?
Generate a weekly network health report.
```

The LLM uses:

```text
telemetry data
incident logs
automation history
ML model outputs
```

---

#### Data Analytics Engine

Provides deeper analysis:

```text
traffic pattern analysis
capacity forecasting
device reliability scoring
anomaly clustering
```

This allows long-term insights that the edge controller cannot compute efficiently.

---

#### Automated Report Generation

Reports may include:

```text
daily network summary
weekly performance report
security anomaly report
capacity planning analysis
```

These can be exported as:

```text
PDF
HTML dashboards
CSV datasets
```

---

## 3. Communication Model

All interaction between systems flows through MQTT.

```text
MLOps Controller
      │
 publishes
      │
      ▼
MQTT Broker
      │
      ▼
AIOps Platform
      │
 processes / analyzes
      │
      ▼
Vue Dashboard + LLM
```

The AIOps platform can also send **control messages** back.

Example topics:

```text
network-chan/control/policy
network-chan/control/automation
network-chan/control/model
```

Example command:

```text
{
 action: "retrain_model",
 model: "tinyml-anomaly"
}
```

---

## 4. Deployment Model

Typical deployment:

```text
Home / SMB Network

           ┌───────────────────┐
           │   AIOps Server    │
           │ Vue Dashboard     │
           │ LLM Assistant     │
           └────────┬──────────┘
                    │ MQTT
                    ▼
           ┌───────────────────┐
           │ MLOps Controller  │
           │ Raspberry Pi 5    │
           │ ML + Automation   │
           └────────┬──────────┘
                    │
                    ▼
           Network Devices
```

---

## 5. Advantages of this Architecture

### Low latency response

The edge controller handles immediate remediation without waiting for the server.

---

### Scalable monitoring

The AIOps server can monitor **multiple MLOps controllers**.

---

### Operator oversight

Admins maintain full visibility through the dashboard.

---

### AI-assisted operations

The LLM assistant enables faster troubleshooting and reporting.

---

### Modular architecture

Each subsystem can evolve independently.
