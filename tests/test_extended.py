import hashlib
import json
import os
from pathlib import Path

from daming_os.memory.extended import PathScopedRules, SicaGuard


def test_path_scoped_rules_empty():
    rules = PathScopedRules()
    assert rules.rules_for("some/path") == []


def test_path_scoped_rules_matching():
    rules_dict = {
        str(Path("src/")): ["rule1", "rule2"],
        str(Path("tests/")): ["rule3"],
    }
    rules = PathScopedRules(rules_dict)

    assert set(rules.rules_for("src/main.py")) == {"rule1", "rule2"}
    assert set(rules.rules_for("tests/test_main.py")) == {"rule3"}

    assert rules.rules_for("docs/readme.md") == []


def test_path_scoped_rules_multiple_matches():
    rules_dict = {
        str(Path("src/")): ["rule1"],
        str(Path("src/module/")): ["rule2"],
    }
    rules = PathScopedRules(rules_dict)

    assert set(rules.rules_for("src/module/file.py")) == {"rule1", "rule2"}
    assert set(rules.rules_for("src/other.py")) == {"rule1"}


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
