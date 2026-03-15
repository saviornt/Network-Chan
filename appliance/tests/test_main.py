# appliance/tests/test_main.py

import pytest
from unittest.mock import AsyncMock, patch
from appliance.src import main  # Import module

class StopLoop(Exception):
    pass

@pytest.mark.asyncio
async def test_run_loop_integration(monkeypatch) -> None: # type: ignore
    iteration_count = 0
    max_iterations = 5  # Enough to trigger %5==0

    async def mock_sleep(*args): # type: ignore
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count >= max_iterations:
            raise StopLoop
        return None  # Continue loop

    # Mocks...
    mock_ingest = AsyncMock()
    mock_ingest.collect_metrics.return_value = None
    mock_ingest.metrics = [{'cpu': 95.0}]  # Trigger anomaly
    mock_ingest.persist_metrics.return_value = None

    mock_detect = AsyncMock()
    mock_detect.check_anomalies.return_value = (True, "Alert")

    mock_agent = AsyncMock()
    mock_agent.select_action.return_value = 1
    mock_agent.update.return_value = None

    mock_learner = AsyncMock()
    mock_learner.adapt_to_tasks.return_value = None

    with patch('appliance.src.main.TelemetryIngestor', return_value=mock_ingest):
        with patch('appliance.src.main.AnomalyDetector', return_value=mock_detect):
            with patch('appliance.src.main.QLearningAgent', return_value=mock_agent):
                with patch('appliance.src.main.ReptileMetaLearner', return_value=mock_learner):
                    with patch('asyncio.sleep', mock_sleep): # type: ignore
                        with pytest.raises(StopLoop):
                            await main.run_loop()

    assert mock_ingest.collect_metrics.call_count == max_iterations
    mock_detect.check_anomalies.assert_called()
    mock_agent.select_action.assert_called()
    mock_agent.update.assert_called()
    mock_learner.adapt_to_tasks.assert_called()  # Now triggered after 5
    mock_ingest.persist_metrics.assert_called()