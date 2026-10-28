import os
import json
import logging
import re
from typing import Dict, Any

logger = logging.getLogger("daming_os.memory.hot")

class SessionStateMachine:
    """
    Manages atomic os.replace operations for .tmp session memories to prevent tearing.
    Layer 1 (Hot).
    """
    def __init__(self, session_dir: str):
        self.session_dir = session_dir
        os.makedirs(self.session_dir, exist_ok=True)

    def write_memory(self, session_key: str, data: Dict[str, Any]) -> bool:
        if not re.match(r"^[a-zA-Z0-9_-]+$", session_key):
            logger.error(f"Invalid session_key: {session_key}")
            return False

        tmp_path = os.path.join(self.session_dir, f"hot_memory_{session_key}.tmp")
        target_path = os.path.join(self.session_dir, f"hot_memory_{session_key}.json")
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, target_path)
            return True
        except Exception as e:
            logger.error(f"Failed to write hot memory for {session_key}: {e}")
            return False

    def read_memory(self, session_key: str) -> Dict[str, Any]:
        if not re.match(r"^[a-zA-Z0-9_-]+$", session_key):
            logger.error(f"Invalid session_key: {session_key}")
            return {}

        target_path = os.path.join(self.session_dir, f"hot_memory_{session_key}.json")
        if not os.path.exists(target_path):
            return {}
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read hot memory for {session_key}: {e}")
            return {}
