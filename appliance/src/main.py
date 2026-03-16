# appliance/src/main.py
from typing import NoReturn, List, Dict, Any
import asyncio
import numpy as np  # For states in RL
from .telemetry.telemetry_ingest import TelemetryIngestor
from .ml.edge_rl import QLearningAgent
from .ml.meta_learner import ReptileMetaLearner
from .ml.tiny_gnn import TinyGNN
from .governance.policy_engine import PolicyEngine
from .security.anomaly_detection import AnomalyDetector
from .security.security_audit import SecurityAudit
from .remediation.remediation_mockup import RemediationDaemon
from .utils.logging_setup import logger, prune_logs
from .config import config

async def run_audit_scheduler(audit: SecurityAudit) -> None:
    mode = config.audit_mode
    logger.info(f"Starting security audit scheduler in {mode} mode")
    match mode:
        case 'always':
            while True:
                logger.info(f"Security audit started for audit mode {mode}...")
                await audit.perform_audit()
                await asyncio.sleep(3600)  # Every hour
        case 'off-peak':
            logger.info(f"Security audit started for audit mode {mode}...")
            await audit.schedule_audit() # Use built-in hourly check for off-peak hour
        case 'auto':
            while True:
                # Mock AI trigger: E.g., low traffic (cpu < 20%)
                mock_traffic_low = np.random.rand() < 0.3   # 30% chance to trigger
                if mock_traffic_low:
                    logger.info("Security audit triggered by low traffic")
                    await audit.perform_audit()
                await asyncio.sleep(3600)  # Every hour
        case _:
            logger.warning(f"Unknown audit mode: {mode} - defaulting to off-peak scheduling")
            await audit.schedule_audit()

async def run_loop() -> NoReturn:
    prune_logs()
    ingestor = TelemetryIngestor()
    detector = AnomalyDetector()
    agent = QLearningAgent()
    meta_learner = ReptileMetaLearner()
    gnn = TinyGNN()
    engine = PolicyEngine()
    daemon = RemediationDaemon()  # Remediation integration
    audit = SecurityAudit()  # Security audit integration
    audit_task = asyncio.create_task(run_audit_scheduler(audit))
    cycle_count: int = 0

    try:
        while True:
            await ingestor.collect_metrics(['router', 'switch'])
            if ingestor.metrics:
                cpu_values: List[float] = [m['cpu'] for m in ingestor.metrics]
                anomaly, msg = await detector.check_anomalies(cpu_values)
                if anomaly:
                    logger.warning(f"Alert: {msg}")

                    # TinyGNN: Mock graph from metrics: Features as cpu reshaped, adjacency as identity (simple nodes)
                    num_nodes = len(cpu_values)
                    features: np.ndarray = np.array(cpu_values).reshape(num_nodes, 1) # 1-dim features per node
                    adjacency: np.ndarray = np.eye(num_nodes)  # Mock connected graph
                    embedding: np.ndarray = await gnn.embed_graph(features, adjacency)

                    # Q-Learning: Use embedding to augment/augment RL state (flatten/truncate to dim), select action and update with reward
                    mock_state: np.ndarray = embedding.flatten()[:agent.state_dim]
                    if mock_state.size < agent.state_dim:
                        mock_state = np.pad(mock_state, (0, agent.state_dim - mock_state.size)) # Pad if short
                    action: int = await agent.select_action(mock_state)
                    logger.debug(f"RL Action selected: {action}")                
                    mock_reward: float = -1.0 if anomaly else 1.0  # Negative for anomaly
                    mock_next_state: np.ndarray = np.random.rand(agent.state_dim)  # Simulate next
                    await agent.update(mock_state, action, mock_reward, mock_next_state)

                    # Policy Governance
                    approved, msg = await engine.approve_action('remediate_flap') # Mock action
                    if approved:
                        success, rem_msg = await daemon.execute_action('remediate_flap', {'param': 'value'})
                        logger.info(f"Remediation: {rem_msg}")
                        if not success:
                            await daemon.rollback_action('remediate_flap')
                    else:
                        logger.warning(f"Denied: {msg}")

                # Periodic REPTILE adaptation (e.g., every 5 cycles)
                cycle_count += 1
                if cycle_count % 5 == 0:
                    mock_tasks: List[Dict[str, Any]] = [{'data': np.random.rand(10), 'labels': np.random.rand(10)} for _ in range(3)]
                    await meta_learner.adapt_to_tasks(mock_tasks)
                    logger.info("REPTILE adaptation complete")

            await ingestor.persist_metrics()
            logger.debug("Metrics persisted")
            await asyncio.sleep(10)  # Simulate 10s interval
    finally:
        audit_task.cancel()  # Ensure audit task is cleaned up on exit
        await audit_task
        logger.info("Security audit task stopped")

if __name__ == "__main__":
    logger.info("Starting NetworkChan MLOps Network Appliance...")
    asyncio.run(run_loop())