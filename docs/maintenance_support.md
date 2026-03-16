# Network-Chan Maintenance & Support Plan

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  
**Version:** 1.0  

## Introduction

This Maintenance & Support Plan outlines the strategies for maintaining Network-Chan post-launch, ensuring long-term reliability, security, and usability for users in home labs, small businesses, and enterprises. It covers update delivery (features, bug fixes, patches), support levels with Service Level Agreements (SLAs) for response/resolution times, monitoring, escalation, and user channels. The plan aligns with the product's split architecture: the Appliance (Raspberry Pi 5) as an autonomous AIOps controller and the Assistant (PC/server) as the intelligence layer.

Post-launch support emphasizes community-driven open-source contributions (GitHub), with optional premium tiers for enterprise users. All updates are local-only, with no cloud dependency. The plan assumes freemium pricing: free core updates, paid for priority support/SLAs.

## Post-Launch Update Delivery

Updates are delivered iteratively via GitHub Releases, ensuring compatibility, safety, and minimal downtime. The process follows Semantic Versioning (SemVer: MAJOR.MINOR.PATCH) and Agile principles (quarterly releases post-MVP).

### Update Types and Delivery Methods

- **Features (Major/Minor Releases)**: New capabilities (e.g., new SDN vendor plugin). Delivered quarterly.  
- **Bug Fixes (Patch Releases)**: Critical/non-critical fixes. Delivered as-needed (weekly for critical).  
- **Patches (Security/Hotfixes)**: Urgent vulnerabilities. Delivered within 24–48 hours.  

- **Delivery Process**:  
  1. **Development**: Fix/develop in feature branches; test in staging (Mininet/lab VLAN).  
  2. **Release**: Tag in Git (e.g., v1.2.3); auto-build Docker images/Pi SD card images via CI (GitHub Actions).  
  3. **Notification**: GitHub release notes + email/RSS to subscribers; in-app banner on dashboard.  
  4. **Update Mechanism**:  
     - Appliance: One-command script (`scripts/update.sh`) pulls Docker image or git pull + restart (systemd). Auto-update toggle in config page.  
     - Assistant: npm/pip update + restart; dashboard prompt for manual approval.  
  5. **Compatibility**: Backward-compatible (no breaking changes in minor patches); migration scripts for major (e.g., DB schema updates).  
- **Tools**: GitHub Releases for binaries/docs; Docker Hub for images; Pi-specific image builder (Raspberry Pi Imager custom).

### Release Cadence

- Major: Biannual (new epics, e.g., multi-site support).  
- Minor: Quarterly (features from backlog).  
- Patch: Monthly or as-needed.  

## Bug Fix and Patch Process

- **Bug Reporting**: Users report via GitHub Issues (template: repro steps, env, logs). Community triage within 24 hours.  
- **Fix Process**:  
  1. **Triage**: Label priority (P1 critical – affects safety; P4 low – cosmetic). Assign to sprint.  
  2. **Development**: Fix in bugfix/ branch; add regression test.  
  3. **Testing**: CI runs unit/integration/stress; manual in lab VLAN.  
  4. **Release**: Merge to main → auto-patch release if P1/P2.  
- **Patch Delivery**: Hotfixes as GitHub patch files or Docker tags; notify via in-app alert.  
- **Tools**: GitHub Issues/Actions, Sentry for error tracking (optional, local-only mode).

## Support Levels and SLAs

Support is tiered by user type (free vs. premium), with SLAs for response (ack time) and resolution (fix time). Community forums/GitHub for all.

- **Support Levels**:  

  | Level | Description | Response SLA | Resolution SLA | Channels |
  |-------|-------------|--------------|----------------|----------|
  | Community (Free) | Self-help + community forums | 48 hours (best-effort) | 1–4 weeks | GitHub Issues, Reddit r/NetworkChan |
  | Basic (Free with registration) | Email support for bugs | 24 hours | 1–2 weeks | Email, GitHub priority labels |
  | Premium ($5/month) | Priority + phone/Slack | 4 hours (business) | 48 hours (critical) / 1 week (others) | Dedicated Slack, phone, remote debug |
  | Enterprise (Custom) | 24/7 + on-site | 1 hour | 24 hours (critical) / 72 hours (others) | Dedicated account manager, on-site |

- **SLA Definitions**:  
  - Response: Time to acknowledge/assign issue.  
  - Resolution: Time to fix/release patch (critical: P1 safety/downtime; others: P2–P4).  
  - Uptime SLA (Premium+): 99.9% for Appliance (measured via Prometheus). Credits for breaches.  
- **Escalation**: P1 → immediate dev alert (Slack hook); unresolved >SLA → PO review.

## Monitoring and Proactive Maintenance

- **Monitoring**: Prometheus + Grafana on Appliance/Assistant; alerts for uptime, errors, ML drift (e.g., anomaly false positives).  
- **Proactive**: Weekly automated scans (Snyk for vulns, MLflow for model decay); patch advisories monitored (e.g., Omada/TP-Link RSS).  
- **Maintenance Windows**: Off-peak (user-configurable); auto-updates optional with rollback.

## User Support Channels

- **Self-Help**: Docs/guides in repo, FAQ in dashboard.  
- **Community**: GitHub Discussions, Reddit r/NetworkChan, Discord server.  
- **Direct**: Email (<support@network-chan.com>) for Basic+; Slack/phone for Premium.  
- **Bug Tracking**: GitHub Issues (template enforced); link to SLAs.

## Escalation Procedures

1. **Issue Reported**: Auto-assign label/priority via bot.  
2. **Initial Response**: Acknowledge <SLA time; triage.  
3. **Development**: Fix in branch; PR review.  
4. **Escalation Path**:  
   - >50% SLA overrun → Notify PO.  
   - P1 unresolved >24 hours → All-hands debug.  
   - User dissatisfaction → Refund/credit for Premium.  

- **Tools**: GitHub notifications, Slack integrations for alerts.

This plan ensures sustainable post-launch support, with clear SLAs to build user trust. It will be reviewed annually or after major releases.
