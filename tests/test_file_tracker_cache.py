import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch

from daming_os.memory.extended import FileTracker


def test_unchanged_files_reuse_hash_between_changed_and_snapshot(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("first")
    tracker = FileTracker(str(tmp_path / "state.json"))
    tracker.snapshot([str(source)])
    with patch.object(Path, "read_bytes", side_effect=AssertionError("unexpected rehash")):
        assert tracker.changed([str(source)]) == []
        assert tracker.snapshot([str(source)])[str(source)] == hashlib.sha256(b"first").hexdigest()


def test_same_size_edit_with_restored_mtime_is_detected_before_snapshot(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("first")
    tracker = FileTracker(str(tmp_path / "state.json"))
    tracker.snapshot([str(source)])
    before = source.stat()
    assert tracker.changed([str(source)]) == []
    source.write_text("other")
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    snapshot = tracker.snapshot([str(source)])
    assert snapshot[str(source)] == hashlib.sha256(b"other").hexdigest()
    assert json.loads(tracker.path.read_text()) == snapshot
