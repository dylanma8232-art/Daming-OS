import os
import tempfile
import unittest
from pathlib import Path

from daming_os.scheduling import ConfigGuard


class TestConfigGuard(unittest.TestCase):
    def test_config_guard_detects_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_path = root / "nested" / "dir" / "config_state.hash"

            # Test __init__ creates parent directory
            guard = ConfigGuard(str(state_path))
            self.assertTrue(state_path.parent.exists())

            # Test check() on initial run (no previous state)
            config1 = {"key1": "value1", "key2": 2}
            self.assertFalse(guard.check(config1))
            self.assertTrue(state_path.exists())

            # Test check() with same config
            self.assertFalse(guard.check(config1))

            # Test check() with equivalent config but different key order
            config1_reordered = {"key2": 2, "key1": "value1"}
            self.assertFalse(guard.check(config1_reordered))

            # Test check() with changed config
            config2 = {"key1": "value1", "key2": 3}
            self.assertTrue(guard.check(config2))

            # Test check() again with the changed config (should now be unchanged)
            self.assertFalse(guard.check(config2))

if __name__ == "__main__":
    unittest.main()
