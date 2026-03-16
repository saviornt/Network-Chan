# appliance/tests/test_main.py

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from appliance.src.main import run_loop  # Import function


class StopLoop(Exception):
    pass


@pytest.mark.asyncio
async def test_run_loop_integration(monkeypatch: pytest.MonkeyPatch) -> None:
    iteration_count = 0
    max_iterations = 5  # Enough to trigger %5==0

    async def mock_sleep(*args: Any) -> None:
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count >= max_iterations:
            raise StopLoop
        return None  # Continue loop

    # Mocks for all classes in loop
    mock_ingest = AsyncMock()
    mock_ingest.collect_metrics.return_value = None
    mock_ingest.metrics = [{"cpu": 95.0}]  # Trigger anomaly
    mock_ingest.persist_metrics.return_value = None

    mock_detect = AsyncMock()
    mock_detect.check_anomalies.return_value = (True, "Alert")

    mock_gnn = AsyncMock()
    mock_gnn.embed_graph.return_value = np.random.rand(10).reshape(2, 5)  # Mock embedding

    mock_agent = AsyncMock()
    mock_agent.select_action.return_value = 1
    mock_agent.update.return_value = None
    mock_agent.state_dim = 10  # Set to int to fix TypeError (< int and AsyncMock)

    mock_learner = AsyncMock()
    mock_learner.adapt_to_tasks.return_value = None

    mock_engine = AsyncMock()
    mock_engine.approve_action.return_value = (True, "Approved")

    mock_daemon = AsyncMock()
    mock_daemon.execute_action.return_value = (True, "Remediated")
    mock_daemon.rollback_action.return_value = None

    mock_audit_task = Mock()
    mock_audit_task.cancel.return_value = None

    with patch("appliance.src.main.prune_logs", return_value=None):
        with patch("appliance.src.main.TelemetryIngestor", return_value=mock_ingest):
            with patch("appliance.src.main.AnomalyDetector", return_value=mock_detect):
                with patch("appliance.src.main.TinyGNN", return_value=mock_gnn):
                    with patch("appliance.src.main.QLearningAgent", return_value=mock_agent):
                        with patch("appliance.src.main.ReptileMetaLearner", return_value=mock_learner):
                            with patch("appliance.src.main.PolicyEngine", return_value=mock_engine):
                                with patch("appliance.src.main.RemediationDaemon", return_value=mock_daemon):
                                    with patch("asyncio.create_task", return_value=None):  # Mock audit_task
                                        with patch("asyncio.sleep", mock_sleep):
                                            with pytest.raises(StopLoop):
                                                await run_loop()

    assert mock_ingest.collect_metrics.call_count == max_iterations
    mock_detect.check_anomalies.assert_called()
    mock_gnn.embed_graph.assert_called()
    mock_agent.select_action.assert_called()
    mock_agent.update.assert_called()
    mock_learner.adapt_to_tasks.assert_called()
    mock_engine.approve_action.assert_called()
    mock_daemon.execute_action.assert_called()
    mock_daemon.rollback_action.assert_not_called()  # Success case
    mock_audit_task.cancel.assert_called_once()
    mock_ingest.persist_metrics.assert_called()