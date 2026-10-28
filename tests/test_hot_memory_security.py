import unittest
import sys
import os
import shutil

# Add the project directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from daming_os.memory.hot import SessionStateMachine

class TestHotMemorySecurity(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(__file__), "test_hot_memory_dir")
        self.state_machine = SessionStateMachine(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_valid_session_key(self):
        # Valid key should succeed in writing and reading
        valid_key = "user-123_session"
        data = {"key": "value"}

        success = self.state_machine.write_memory(valid_key, data)
        self.assertTrue(success)

        read_data = self.state_machine.read_memory(valid_key)
        self.assertEqual(read_data, data)

    def test_invalid_session_key_directory_traversal(self):
        # Invalid key with directory traversal should fail and return False/{}
        invalid_key = "../../../etc/passwd"
        data = {"key": "value"}

        success = self.state_machine.write_memory(invalid_key, data)
        self.assertFalse(success)

        read_data = self.state_machine.read_memory(invalid_key)
        self.assertEqual(read_data, {})

    def test_invalid_session_key_special_chars(self):
        # Invalid key with spaces and special chars should fail
        invalid_key = "invalid key @#!"
        data = {"key": "value"}

        success = self.state_machine.write_memory(invalid_key, data)
        self.assertFalse(success)

        read_data = self.state_machine.read_memory(invalid_key)
        self.assertEqual(read_data, {})

if __name__ == "__main__":
    unittest.main()
