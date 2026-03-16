# appliance/src/config.py

from typing import List, Dict
import os

class Config:
    def __init__(self) -> None:
        # Stub load from .env (use dotenv.load_dotenv() later)
        self.autonomous_mode: int = int(os.getenv('AUTONOMOUS_MODE', '3'))
        self.mqtt_broker: str = os.getenv('MQTT_BROKER', 'localhost:1883')
        self.db_path: str = os.getenv('DB_PATH', 'network_chan.db')
        self.role: str = os.getenv('ROLE', 'admin')
        self.whitelist_actions: List[str] = os.getenv('WHITELIST_ACTIONS', 'reset_interface,throttle_bandwidth').split(',')
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        self.prune_days: str = os.getenv('LOG_PRUNE_TIMEFRAME', '90')
        self.model_path: str = os.getenv('MODEL_PATH', 'mock_model.onnx')
        self.audit_mode: str = os.getenv('AUDIT_MODE', 'off-peak') # 'auto', 'off-peak', 'always'

        # Constants for modes
        # Observer: AI is in observe only, all changes must be manually performed
        # Advisor: The AI makes recommendations based on the current environment
        # Supervised: The AI makes a recommendation and then the user can apply that recommendation or decline
        # Semi-Autonomous: The AI can make small remediations that will not cause network outages
        # Autonomous: The AI is in full autonomous mode but is still dependant on policy guidelines
        # Experimental: The AI can make changes regardless of policy guidelines
        self.AUTONOMOUS_MODES: Dict[int, str] = {
            0: "Observer",
            1: "Advisor",
            2: "Supervised",
            3: "Semi-Autonomous",
            4: "Autonomous",
            5: "Experimental"
        }
        if self.autonomous_mode not in self.AUTONOMOUS_MODES:
            raise ValueError("Invalid AUTONOMOUS_MODE")

config = Config()  # Global instance