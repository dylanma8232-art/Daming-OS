import pytest
import sqlite3
from datetime import datetime, timezone
from daming_os.quality import QualityGate

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_quality.db")

@pytest.fixture
def quality_gate(db_path):
    return QualityGate(db_path=db_path)

def get_task_row(db_path, task_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT risk, state, review_note, updated_at FROM quality_tasks WHERE task_id=?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def test_initialization(db_path):
    # This should create the table
    gate = QualityGate(db_path=db_path)

    # Verify table creation
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quality_tasks'")
    assert cursor.fetchone() is not None
    conn.close()

def test_register_valid_risk(quality_gate, db_path):
    quality_gate.register("task1", "normal")
    quality_gate.register("task2", "high")

    row1 = get_task_row(db_path, "task1")
    assert row1 is not None
    assert row1[0] == "normal"
    assert row1[1] == "open"
    assert row1[2] is None

    row2 = get_task_row(db_path, "task2")
    assert row2 is not None
    assert row2[0] == "high"
    assert row2[1] == "open"
    assert row2[2] is None

def test_register_invalid_risk(quality_gate):
    with pytest.raises(ValueError, match="risk must be normal or high"):
        quality_gate.register("task1", "invalid")

def test_register_update_existing(quality_gate, db_path):
    # Register initially
    quality_gate.register("task1", "high")
    # Change risk, should retain previous state (open initially)
    quality_gate.register("task1", "normal")

    row1 = get_task_row(db_path, "task1")
    assert row1[0] == "normal"
    assert row1[1] == "open"

def test_complete(quality_gate, db_path):
    quality_gate.register("task1", "normal")
    quality_gate.complete("task1")

    row1 = get_task_row(db_path, "task1")
    assert row1[1] == "completed"

def test_review(quality_gate, db_path):
    quality_gate.register("task1", "high")
    quality_gate.register("task2", "high")

    quality_gate.review("task1", passed=True, note="LGTM")
    row1 = get_task_row(db_path, "task1")
    assert row1[1] == "reviewed"
    assert row1[2] == "LGTM"

    quality_gate.review("task2", passed=False, note="Needs work")
    row2 = get_task_row(db_path, "task2")
    assert row2[1] == "rejected"
    assert row2[2] == "Needs work"

def test_blocked(quality_gate):
    # Normal tasks don't block
    quality_gate.register("task1", "normal")

    # High task that is open - BLOCKS
    quality_gate.register("task2", "high")

    # High task that is completed - BLOCKS (needs review)
    quality_gate.register("task3", "high")
    quality_gate.complete("task3")

    # High task that is reviewed - NO BLOCK
    quality_gate.register("task4", "high")
    quality_gate.review("task4", passed=True)

    # High task that is rejected - NO BLOCK (it's not open or completed)
    quality_gate.register("task5", "high")
    quality_gate.review("task5", passed=False)

    blocked = quality_gate.blocked()
    assert "task2" in blocked
    assert "task3" in blocked
    assert "task1" not in blocked
    assert "task4" not in blocked
    assert "task5" not in blocked

    # Check ordering by updated_at (register/complete update the updated_at)
    # task2 was updated before task3
    assert blocked == ["task2", "task3"]
