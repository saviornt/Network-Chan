import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from appliance.src.utils.logging_setup import prune_logs

if __name__ == "__main__":
    prune_logs()