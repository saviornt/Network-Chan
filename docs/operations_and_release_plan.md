# Network-Chan Operations & Release Plan

**Project name:** Network-Chan  
**Date:** 2026-03-21  
**Version:** 1.0 (merged release + maintenance, expanded for solo-dev use)  

## Executive Summary

This document combines and expands the original release deployment and maintenance support plans into a single, comprehensive operations guide. It covers CI/CD, packaging, deployment, updates, monitoring, backup/DR, support channels, and SLAs.

Focus is on solo-developer practicality: emulator-first validation, Docker for easy testing, Pi 5 image creation, QR code installer flow, and automated documentation generation. All processes prioritize safety (rollback <60s), local-only operation, and minimal overhead.

MVP milestone: Appliance + Application working together on real hardware → beta packaging and public release.

## Release & Deployment Strategy

### CI/CD Pipeline (GitHub Actions)

All changes go through a multi-stage workflow (`.github/workflows/ci-cd.yml`):

```yaml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python 3.12
        uses: actions/setup-python@v5
        with: python-version: '3.12'
      - name: Install deps
        run: pip install -r requirements-dev.txt
      - name: Ruff lint & format
        run: ruff check --fix . && ruff format .
      - name: MyPy type check
        run: mypy .
      - name: pytest
        run: pytest --cov --cov-report=xml

  build-docs:
    needs: lint-and-test
    if: success()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build MkDocs
        run: mkdocs build
      - name: Deploy to GitHub Pages
        if: github.ref == 'refs/heads/main'
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
```

- Triggers on every push/PR.
- Only proceeds to docs build/deploy if lint/type/tests pass.
- Deploy to GitHub Pages happens automatically on main.

### Environments & Promotion Flow

1. **Development** — Local emulator + VS Code.
2. **Staging** — Docker Compose (emulator + Application containers) on your PC.
3. **Production** — Real Raspberry Pi 5 + home network.

Promotion: Manual (after 24–48h soak in staging) → tag release on GitHub.

## Packaging & Distribution

- **Docker Images**:
  - `network-chan-emulator` (Pi 5 simulation + Appliance).
  - `network-chan-application` (central layer).
  - Published to GitHub Container Registry on every main push.

- **Raspberry Pi 5 Image**:
  - Custom Raspberry Pi Imager script (pre-installed Appliance + Docker).
  - Download via QR code on kit or GitHub Releases.

- **Installer Flow**:
  - QR code on kits/retail hardware → website → one-click download (Docker Compose + setup script).
  - Self-assembly kits: User sources Pi 5 components per guide.

- **Beta Release**: GitHub Release with Docker images + Pi image + QR installer link.

## Update & Maintenance Process

- **Versioning**: SemVer (MAJOR.MINOR.PATCH).
- **Update Delivery**:
  - Patches: Weekly for critical bugs (auto-update toggle in Appliance UI).
  - Minor releases: Quarterly (new features).
  - Major releases: Biannual (breaking changes with migration scripts).
- **Auto-Update Mechanism**:
  - Appliance: `update.sh` script pulls new Docker image or git pull + restart (systemd).
  - Application: Dashboard notification + one-click update.
- **Rollback**: Atomic snapshots before every change; watchdog script triggers <60s rollback on failure.

## Monitoring & Alerting

- **Tools**: Prometheus (scraped on Appliance) + Grafana (embedded in Application dashboard).
- **Key Metrics**:
  - Telemetry ingestion latency.
  - Inference time (<10ms).
  - MQTT round-trip time.
  - Autonomy level changes.
  - Security alerts (TOTP failures, TLS errors).
- **Alerts**: MQTT → Application dashboard (visual + optional email for critical).

## Backup & Disaster Recovery

- **Backup**:
  - Cron rsync + SQLite `.backup` command (daily on Appliance).
  - Encrypted to local storage or external drive.
- **Disaster Recovery**:
  - RTO: <5 min (Appliance restart); <15 min (Application).
  - RPO: <1 hour data loss.
  - Steps:
    1. Detect failure (Prometheus alert).
    2. Failover to spare Docker container or spare Pi.
    3. Restore from last backup + replay MQTT delta logs.
    4. Verify and resume.

## Support Channels & SLAs (Post-Beta)

- **Community (Free)**: GitHub Discussions, Reddit r/NetworkChan.
- **Beta Users**: Priority GitHub Issues + email.
- **Future Paid Tiers**: Dedicated Slack/email (response <24h critical, <72h standard).
- **Escalation**: P1 bugs (network outage) → immediate personal review.

## Security in Operations

- TLS 1.3 enforced on all MQTT/FastAPI traffic.
- TOTP 2FA mandatory on first login.
- All updates signed (future ML-DSA signatures).
- Fail-open design: Network continues if Network-Chan unavailable.

## Post-Launch Roadmap

- **Month 1–3**: Beta release, community feedback, minor patches.
- **Month 4–6**: First retail kit sales, documentation expansion.
- **Month 7+**: Enterprise extensions, PQC integration, investor demos.

This plan is designed for solo development but scales easily as the project grows. It will be reviewed quarterly or after major releases.
