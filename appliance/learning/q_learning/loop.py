"""Async main loop for the Network-Chan Appliance Q-Learning agent.

This is the top-level event loop that:
- Runs continuous episodes with the agent
- Publishes stats via MQTT
- Handles graceful shutdown
- Integrates safety gating (autonomy mode check)
- Periodically saves/loads checkpoints

Run this as the main task in the Appliance's entrypoint.
"""

from __future__ import annotations

import asyncio
import signal
import sys
from typing import Optional

from shared.settings.q_learning_settings import QLearningSettings
from shared.utils.logging_factory import get_logger
from appliance.src.learning.q_learning.agent import ApplianceQLAgent
from appliance.src.learning.q_learning.dummy_env import DummyNetworkEnv
from appliance.src.settings.agent_settings import AgentSettings

# TODO: MQTT client stub (replace with real async paho-mqtt later)
# For MVP, we log to console instead
logger = get_logger("q_learning.loop.appliance")


class QLearningLoop:
    """Async main loop manager for the Appliance Q-Learning subsystem."""

    def __init__(
        self,
        qlearn_config: Optional[QLearningSettings] = None,
        agent_config: Optional[AgentSettings] = None,
    ):
        self.qlearn_config = qlearn_config or QLearningSettings()
        self.agent_config = agent_config or AgentSettings()

        self.agent = ApplianceQLAgent(
            qlearn_config=self.qlearn_config,
            agent_config=self.agent_config,
            env=DummyNetworkEnv(),  # replace with real env later
        )

        self.running = True
        self.loop_task: Optional[asyncio.Task] = None

        # Signal handlers for graceful shutdown
        self._setup_signals()

        logger.info(
            "QLearningLoop initialized",
            rolling_window=self.agent_config.rolling_window,
            checkpoint_interval=self.agent_config.checkpoint_interval,
        )

    def _setup_signals(self) -> None:
        """Register SIGINT/SIGTERM handlers for clean shutdown."""
        loop = asyncio.get_event_loop()

        def shutdown_handler(signum=None):
            logger.warning("Shutdown signal received", signum=signum)
            self.running = False
            if self.loop_task:
                self.loop_task.cancel()

        loop.add_signal_handler(signal.SIGINT, shutdown_handler, signal.SIGINT)
        loop.add_signal_handler(signal.SIGTERM, shutdown_handler, signal.SIGTERM)

    async def run(self) -> None:
        """Main async loop: run episodes continuously until shutdown."""
        logger.info("Starting Q-Learning main loop")

        # Load checkpoint on startup if exists
        if self.agent.load_checkpoint_if_exists():
            logger.info("Loaded checkpoint on startup")
        else:
            logger.info("No checkpoint found - starting fresh")

        while self.running:
            try:
                stats = await asyncio.to_thread(self.agent.run_episode)
                # In real version: publish stats via MQTT here
                logger.info("Episode stats published (stub)", **stats.model_dump())
            except asyncio.CancelledError:
                logger.info("Main loop cancelled during episode")
                break
            except Exception as e:
                logger.exception(
                    "Unexpected error in episode loop",
                    error_type=type(e).__name__,
                    error_msg=str(e),
                )
                await asyncio.sleep(5)  # backoff before retry

        logger.info("Main loop exiting")

    async def start(self) -> None:
        """Start the loop as an asyncio task."""
        if self.loop_task and not self.loop_task.done():
            logger.warning("Loop already running - ignoring start request")
            return

        self.loop_task = asyncio.create_task(self.run())
        try:
            await self.loop_task
        except asyncio.CancelledError:
            logger.info("Loop task cancelled")
        finally:
            self.loop_task = None

    async def stop(self) -> None:
        """Gracefully stop the loop."""
        self.running = False
        if self.loop_task:
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                pass
        logger.info("Loop stopped")


async def main():
    """Entry point for the Q-Learning loop."""
    loop = QLearningLoop()
    try:
        await loop.start()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received - shutting down")
        await loop.stop()
    except Exception as e:
        logger.exception("Fatal error in main loop", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
