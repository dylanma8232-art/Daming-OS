import tempfile
import unittest
from pathlib import Path

from daming_os.operations import ArchiveStore


class TestArchiveStore(unittest.TestCase):
    def test_restore_copies_archive_to_destination_and_returns_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            # Create a dummy archived file
            archived_file = root / "archive" / "data.txt"
            archived_file.parent.mkdir(parents=True)
            archived_file.write_text("archive content", encoding="utf-8")

            # Initialize ArchiveStore
            store = ArchiveStore(str(root / "store_root"))

            # Destination path where we want to restore
            destination = root / "restore_dir" / "restored_data.txt"

            # Perform restore
            result = store.restore(str(archived_file), str(destination))

            # Assertions
            self.assertEqual(result, destination)
            self.assertTrue(destination.exists())
            self.assertEqual(destination.read_text(encoding="utf-8"), "archive content")
