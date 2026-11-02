import hashlib
import json
import os
from pathlib import Path

import sqlite3

from daming_os.memory.extended import SicaGuard, FTSRebuilder


def test_ftsrebuilder_no_items_table(tmp_path):
    db_path = tmp_path / "metadata.db"
    rebuilder = FTSRebuilder(str(db_path))

    # Should run successfully even if the database is brand new and has no items table
    result = rebuilder.rebuild()
    assert result["indexed"] == 0

    # Ensure the memory_fts table is created correctly
    conn = sqlite3.connect(str(db_path))
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t[0] for t in tables]
    assert "memory_fts" in table_names
    conn.close()


def test_ftsrebuilder_empty_items_table(tmp_path):
    db_path = tmp_path / "metadata.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE items (item_id TEXT, content TEXT)")
    conn.commit()
    conn.close()

    rebuilder = FTSRebuilder(str(db_path))
    result = rebuilder.rebuild()
    assert result["indexed"] == 0

    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM memory_fts").fetchone()[0]
    assert count == 0
    conn.close()


def test_ftsrebuilder_with_items(tmp_path):
    db_path = tmp_path / "metadata.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE items (item_id TEXT, content TEXT)")
    conn.executemany("INSERT INTO items (item_id, content) VALUES (?, ?)", [
        ("id1", "This is some test content about AI."),
        ("id2", "Another item for full text search."),
    ])

    # Also simulate an existing memory_fts to ensure it gets cleared out
    conn.execute("CREATE VIRTUAL TABLE memory_fts USING fts5(item_id, content)")
    conn.execute("INSERT INTO memory_fts (item_id, content) VALUES (?, ?)", ("old_id", "old content"))
    conn.commit()
    conn.close()

    rebuilder = FTSRebuilder(str(db_path))
    result = rebuilder.rebuild()
    assert result["indexed"] == 2

    # Verify everything was updated correctly
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("SELECT item_id, content FROM memory_fts ORDER BY item_id").fetchall()
    assert len(rows) == 2
    assert rows[0] == ("id1", "This is some test content about AI.")
    assert rows[1] == ("id2", "Another item for full text search.")
    conn.close()


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
