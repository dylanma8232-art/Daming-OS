import unittest
import sys
import os
import tempfile
import sqlite3

# Add the project directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from daming_os.quality import QualityGate

class TestQualityGate(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp()
        self.qg = QualityGate(db_path=self.temp_db_path)

    def tearDown(self):
        os.close(self.temp_db_fd)
        os.remove(self.temp_db_path)

    def _get_task(self, task_id):
        with sqlite3.connect(self.temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT task_id, risk, state, review_note FROM quality_tasks WHERE task_id=?", (task_id,))
            return cursor.fetchone()

    def test_init_creates_table(self):
        with sqlite3.connect(self.temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quality_tasks'")
            self.assertIsNotNone(cursor.fetchone())

    def test_register_valid_risk(self):
        self.qg.register("task1", risk="normal")
        task = self._get_task("task1")
        self.assertIsNotNone(task)
        self.assertEqual(task[1], "normal")
        self.assertEqual(task[2], "open")
        self.assertIsNone(task[3])

        self.qg.register("task2", risk="high")
        task = self._get_task("task2")
        self.assertIsNotNone(task)
        self.assertEqual(task[1], "high")

    def test_register_invalid_risk(self):
        with self.assertRaises(ValueError):
            self.qg.register("task3", risk="invalid")

    def test_register_preserves_state(self):
        self.qg.register("task_preserve", risk="normal")
        self.qg.complete("task_preserve")

        # Verify it was completed
        task = self._get_task("task_preserve")
        self.assertEqual(task[2], "completed")

        # Register again with different risk
        self.qg.register("task_preserve", risk="high")

        # Verify state is preserved as completed
        task = self._get_task("task_preserve")
        self.assertEqual(task[1], "high")
        self.assertEqual(task[2], "completed")

    def test_complete(self):
        self.qg.register("task_complete", risk="normal")
        self.qg.complete("task_complete")
        task = self._get_task("task_complete")
        self.assertEqual(task[2], "completed")

    def test_review_passed(self):
        self.qg.register("task_review_pass", risk="high")
        self.qg.review("task_review_pass", passed=True, note="LGTM")
        task = self._get_task("task_review_pass")
        self.assertEqual(task[2], "reviewed")
        self.assertEqual(task[3], "LGTM")

    def test_review_rejected(self):
        self.qg.register("task_review_reject", risk="high")
        self.qg.review("task_review_reject", passed=False, note="Needs work")
        task = self._get_task("task_review_reject")
        self.assertEqual(task[2], "rejected")
        self.assertEqual(task[3], "Needs work")

    def test_blocked(self):
        # Normal open -> not blocked
        self.qg.register("task_norm_open", risk="normal")
        # High open -> blocked
        self.qg.register("task_high_open", risk="high")
        # Normal completed -> not blocked
        self.qg.register("task_norm_comp", risk="normal")
        self.qg.complete("task_norm_comp")
        # High completed -> blocked (needs review)
        self.qg.register("task_high_comp", risk="high")
        self.qg.complete("task_high_comp")
        # High reviewed -> not blocked
        self.qg.register("task_high_rev", risk="high")
        self.qg.review("task_high_rev", passed=True)
        # High rejected -> not blocked (needs fixes, not 'open' or 'completed' per say)
        self.qg.register("task_high_rej", risk="high")
        self.qg.review("task_high_rej", passed=False)

        blocked_tasks = self.qg.blocked()
        self.assertEqual(len(blocked_tasks), 2)
        self.assertIn("task_high_open", blocked_tasks)
        self.assertIn("task_high_comp", blocked_tasks)

if __name__ == '__main__':
    unittest.main()
