"""API routers package for Network-Chan.

This package collects all FastAPI APIRouters defined in submodules.
Import this package in the main application to include all routes:

    from fastapi import FastAPI
    from shared.src.api import auth_router, telemetry_router  # etc.

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(telemetry_router)
    ...

Exported routers:
    - auth_router: Authentication endpoints (login, password change, TOTP setup)
    - (add new routers here as endpoints are created)
"""

from .auth import router as auth_router

# Add future routers here, e.g.:
# from .telemetry import router as telemetry_router
# from .health import router as health_router

__all__ = [
    "auth_router",
    # "telemetry_router",
    # "health_router",
    # ...
]
