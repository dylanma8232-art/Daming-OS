import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from daming_os.events import EventBus, LogEvent

class TestEventBus(unittest.TestCase):
    @patch("daming_os.events.logger")
    def test_persist_exception_handling(self, mock_logger):
        bus = EventBus()
        mock_path = MagicMock(spec=Path)
        mock_path.parent.mkdir.side_effect = PermissionError("Access denied")
        bus.event_log_path = mock_path

        event = LogEvent("test_type", "test content")

        bus._persist(event)

        mock_logger.error.assert_called_once()
        args, _ = mock_logger.error.call_args
        self.assertEqual(args[0], "Failed to persist event: %s")
        self.assertIsInstance(args[1], PermissionError)

if __name__ == "__main__":
    unittest.main()
