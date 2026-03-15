# appliance/src/main.py

from typing import NoReturn, List, Dict, Any
import asyncio
import numpy as np  # For states in RL
from .telemetry.telemetry_ingest import TelemetryIngestor
from .detection.anomaly_detection import AnomalyDetector
from .ml.edge_rl import QLearningAgent
from .ml.meta_learner import ReptileMetaLearner
from .ml.tiny_gnn import TinyGNN
from .governance.policy_engine import PolicyEngine
from .logging_setup import setup_logging, prune_logs

logger = setup_logging()

async def run_loop() -> NoReturn:
    prune_logs()
    ingestor = TelemetryIngestor()
    detector = AnomalyDetector()
    agent = QLearningAgent()  # Q-Learning integration
    meta_learner = ReptileMetaLearner()  # REPTILE integration
    gnn = TinyGNN()  # Tiny GNN integration
    engine = PolicyEngine()  # Policy engine integration
    cycle_count: int = 0  # For periodic meta-adaptation

    while True:  # Infinite async loop for always-on
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
                    logger.info("Executing approved action")
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

if __name__ == "__main__":
    logger.info("Starting NetworkChan MLOps Network Appliance...")
    asyncio.run(run_loop())