# Network-Chan Release & Deployment Plan

**Prepared for:** Home lab / research deployment  
**Project name:** Network-Chan  
**Date:** 2026-03-14  
**Version:** 1.0  

## Introduction

This Release & Deployment Plan outlines the strategies, processes, and tools for releasing and deploying Network-Chan, ensuring smooth transitions from development to production while maintaining the system's local-only, fail-open design. It covers the Continuous Integration / Continuous Deployment (CI/CD) pipeline, staging/production environments, rollback procedures, and disaster recovery, aligned with the Agile development plan (2-week sprints, GitHub Flow branching).

The plan prioritizes safety: Automated tests in CI, canary releases, and quick rollbacks to minimize downtime in the three-brain architecture. The Appliance (Pi 5) deploys as a lightweight image/service, while the Assistant (PC/server) uses Docker for portability. All deployments are local/on-premises, with no cloud involvement.

## Continuous Integration / Continuous Deployment (CI/CD) Pipeline

The CI/CD pipeline automates building, testing, and deploying to ensure code quality and rapid iteration. It uses GitHub Actions (free/open-source, integrates with repo), supporting the monorepo structure (Appliance/Assistant/shared).

### Pipeline Overview

- **Tools**: GitHub Actions (workflows), Docker (containerization), pytest/Jest (tests), Black/ESLint (linting), Snyk/Bandit (security scans).  
- **Triggers**: Push/PR to main/feature branches; manual for releases.  
- **Stages**: Build → Test → Deploy (staging) → Promote (production).  

### CI Workflow (On Every Commit/PR)

```yaml
name: CI

on: [push, pull_request]

jobs:
  build-test-appliance:
    runs-on: ubuntu-latest  # ARM emulation for Pi
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with: python-version: '3.12'
      - run: pip install -r Appliance/requirements.txt
      - run: pytest Appliance/  # Unit/integration
      - run: black --check Appliance/  # Linting
      - run: bandit -r Appliance/  # Security
      - run: docker build -t network-chan-appliance Appliance/  # Image build

  build-test-assistant:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python & Node
        uses: actions/setup-python@v5
        with: python-version: '3.12'
      - uses: actions/setup-node@v4
        with: node-version: '20'
      - run: pip install -r Assistant/requirements.txt
      - run: pytest Assistant/  
      - run: black --check Assistant/
      - run: bandit -r Assistant/
      - cd Assistant/frontend && npm install && npm run test && npm run build
      - run: docker build -t network-chan-assistant Assistant/

  shared-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: black --check shared/
```

### CD Workflow (On Main Merge/Release Tag)

```yaml
name: CD

on:
  push:
    branches: [main]
    tags: [v*]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t network-chan-appliance Appliance/ --push-to-staging-repo
      - run: docker build -t network-chan-assistant Assistant/ --push-to-staging-repo
      - run: ssh staging-pi 'docker pull && docker restart appliance-container'  # Or ansible-playbook

  promote-production:
    needs: deploy-staging
    if: startsWith(github.ref, 'refs/tags/v')  # On tags only
    runs-on: ubuntu-latest
    steps:
      - run: ssh prod-pi 'docker pull from staging && docker tag && docker restart'  # Blue-green swap
      - name: Create Release
        uses: actions/create-release@v1
        with: token: ${{ secrets.GITHUB_TOKEN }}
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
```

- **Security in Pipeline**: Secrets via GitHub secrets; scan for vulns; signed commits required.

## Staging/Production Environments

- **Environments Setup**:  
  - **Development**: Local Pi/PC with Mininet sim (dockerized for consistency).  
  - **Staging**: Dedicated lab VLAN on physical hardware (ER707 router + APs); mirrors production but with experimental features enabled. Appliance/Assistant deployed via Docker.  
  - **Production**: Management/production VLANs on live network; blue-green deployment (two identical setups, switch via router config).  

- **Promotion Process**: Staging auto-deploys on main merge; production manual on tagged releases (after staging soak test 24–48 hours).  

- **Configuration Management**: Env vars + dotenv files; secrets in Vault or encrypted .env (no hardcoding).  

## Rollback and Disaster Recovery Procedures

### Rollback Procedures

- **Code Rollback**: Git revert/merge to previous tag; CI/CD redeploys.  
- **Config Rollback**: Appliance snapshots configs pre-change (SQLite + filesystem); auto-rollback on failure (<60s via watchdog script).  
  - Manual: `ssh pi 'sqlite3 db.sqlite "SELECT config FROM snapshots WHERE id=last"' > restore.conf; apply via Netmiko`.  
- **Model Rollback**: MLflow registry versions models; rollback command publishes prior checkpoint via MQTT.  
- **Process**: Detect failure (heartbeat/alert) → trigger rollback script → verify (post-checks) → log incident.

### Disaster Recovery Procedures

- **Recovery Time Objective (RTO)**: <5 min for Appliance (systemd restart); <15 min for Assistant.  
- **Recovery Point Objective (RPO)**: <1 hour data loss (hourly backups).  
- **Backup Strategy**: Cron rsync/SQLite .backup for DB/FAISS/files; encrypted to local storage.  
- **DR Steps**:  
  1. **Detection**: Prometheus alerts on downtime.  
  2. **Failover**: Switch to spare Pi (VRRP IP failover); Assistant manual restart.  
  3. **Restore**: rsync backups → restart services; test connectivity.  
  4. **Post-Recovery**: Audit logs for root cause; update runbooks.  
- **Testing**: Quarterly DR drills in staging (simulate Pi failure).  

This plan ensures reliable, automated releases with strong safety nets, supporting Agile iteration. It will be refined based on sprints.
