import hashlib
import json
import os
from pathlib import Path

from daming_os.memory.extended import SicaGuard

def test_sicaguard_snapshot(tmp_path):
    log_file = tmp_path / "sica.log"
    guard = SicaGuard(str(log_file))

    # Create valid dummy files
    file1 = tmp_path / "file1.txt"
    file1.write_text("hello")
    file2 = tmp_path / "file2.txt"
    file2.write_text("world")

    # Create a directory to ensure it is ignored
    dir1 = tmp_path / "dir1"
    dir1.mkdir()

    # Missing file
    missing_file = tmp_path / "missing.txt"

    files_to_check = [str(file1), str(file2), str(dir1), str(missing_file)]

    # Snapshot
    result = guard.snapshot(files_to_check, action="test_action")

    # Verify result dictionary
    assert "at" in result
    assert result["action"] == "test_action"

    hashes = result["hashes"]
    assert len(hashes) == 2
    assert hashes[str(file1)] == hashlib.sha256(b"hello").hexdigest()
    assert hashes[str(file2)] == hashlib.sha256(b"world").hexdigest()
    assert str(dir1) not in hashes
    assert str(missing_file) not in hashes

    # Verify file persistence
    assert log_file.exists()
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 1

    persisted_record = json.loads(lines[0])
    assert persisted_record["at"] == result["at"]
    assert persisted_record["action"] == "test_action"
    assert persisted_record["hashes"] == hashes

def test_sicaguard_directory_creation(tmp_path):
    # Ensure intermediate directories are created
    log_file = tmp_path / "nested" / "dir" / "sica.log"
    guard = SicaGuard(str(log_file))
    assert log_file.parent.exists()
