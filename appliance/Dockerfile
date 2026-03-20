# appliance/Dockerfile
# Minimal Raspberry Pi OS-like base + Python 3.12
# Designed for arm64 (Pi 5), emulatable on x86 via QEMU

FROM --platform=linux/arm64 python:3.12-slim-bookworm

# Install minimal system deps (libomp5 for numba, others if needed later)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libomp5 \
    ca-certificates \
    libsnmp40 \                     
    git \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 networkchan

# Fake Pi OS markers so shared_settings.is_edge_device → True
# Only /etc/os-release is critical; others are optional fallbacks
RUN echo 'PRETTY_NAME="Raspberry Pi OS"' > /etc/os-release && \
    echo 'Raspberry Pi 5' > /etc/armbian-release 2>/dev/null || true

WORKDIR /app

# Switch to non-root user
USER networkchan

# Add user's .local/bin to PATH so upgraded pip/wheel are immediately usable
ENV PATH="/home/networkchan/.local/bin:${PATH}"

# Environment (overridable)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=development \
    AUTONOMOUS_MODE=advisor

# Expose (minimal config page or future uvicorn)
EXPOSE 8001

# Default command — override in compose or run manually
# We will pip install inside container, so shell for now
CMD ["bash"]