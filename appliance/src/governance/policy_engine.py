# appliance/src/policy_engine.py

import asyncio

from numba import jit  # type: ignore

from src.config.shared_settings import AUTONOMOUS_MODES, app_settings


@jit(nopython=True)  # type: ignore[misc]
def check_autonomy_level(level: int, required: int) -> bool:  # Numba for fast rule eval
    return level >= required  # Mock threshold


class PolicyEngine:
    def __init__(self) -> None:
        self.autonomy_levels: list[int] = list(AUTONOMOUS_MODES.keys())
        self.role: str = app_settings.role
        self.whitelist: dict[str, bool] = {
            action: True for action in app_settings.whitelist_actions
        }
        self.current_level: int = app_settings.autonomous_mode

    async def approve_action(self, action: str) -> tuple[bool, str]:
        await asyncio.sleep(0)  # Async for potential DB/RBAC query
        if action not in self.whitelist:
            return False, "Action not whitelisted"
        if not check_autonomy_level(self.current_level, 3):  # Mock required=3
            return False, "Insufficient autonomy level"
        if self.role != "admin":
            return False, "Unauthorized role"
        return True, "Approved"


# Usage stub
async def main() -> None:
    engine = PolicyEngine()
    approved, msg = await engine.approve_action("reset_interface")
    print(approved, msg)


if __name__ == "__main__":
    asyncio.run(main())
