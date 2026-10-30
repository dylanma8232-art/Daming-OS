import tempfile
import unittest

from daming_os.adapter import AgentContext
from daming_os.hooks import DamingHookBridge
from daming_os.runtime import DamingRuntime


class TestScopedSessionIsolation(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.runtime = DamingRuntime(self.tmp_dir.name)
        self.bridge = DamingHookBridge(adapter=self.runtime.adapter)

    def tearDown(self):
        self.runtime.close()
        self.tmp_dir.cleanup()

    def test_hot_journal_tenant_isolation(self):
        # Two tenants using the same local session ID
        payload_tenant_a = {
            "agent_id": "agent-1",
            "session_id": "shared-session-123",
            "tenant_id": "tenant-a",
            "input": "User input for tenant A",
            "output": "Result for tenant A",
            "metadata": {"messages": []},
        }
        payload_tenant_b = {
            "agent_id": "agent-1",
            "session_id": "shared-session-123",
            "tenant_id": "tenant-b",
            "input": "User input for tenant B",
            "output": "Result for tenant B",
            "metadata": {"messages": []},
        }

        # Tenant A completes a turn
        self.bridge.after_turn(payload_tenant_a)

        # Tenant B starts a turn before making any writes
        b_before = self.bridge.before_turn(payload_tenant_b)

        # Tenant B's compacted messages should NOT contain Tenant A's history
        b_compacted = b_before.get("daming_compacted_messages", [])
        for msg in b_compacted:
            self.assertNotIn("Result for tenant A", msg.get("content", ""))

        # Tenant B completes a turn
        self.bridge.after_turn(payload_tenant_b)

        # Check compacted history for both tenants
        a_before = self.bridge.before_turn(payload_tenant_a)
        b_before_2 = self.bridge.before_turn(payload_tenant_b)

        a_compacted_contents = [msg.get("content", "") for msg in a_before.get("daming_compacted_messages", [])]
        b_compacted_contents = [msg.get("content", "") for msg in b_before_2.get("daming_compacted_messages", [])]

        self.assertTrue(any("Result for tenant A" in c for c in a_compacted_contents))
        self.assertFalse(any("Result for tenant B" in c for c in a_compacted_contents))

        self.assertTrue(any("Result for tenant B" in c for c in b_compacted_contents))
        self.assertFalse(any("Result for tenant A" in c for c in b_compacted_contents))

    def test_consolidation_does_not_collapse_identical_turns_across_tenants(self):
        # Two different tenants store identical content with same session_id
        ctx_a = AgentContext(agent_id="agent-1", session_id="shared-session", tenant_id="tenant-a")
        ctx_b = AgentContext(agent_id="agent-1", session_id="shared-session", tenant_id="tenant-b")

        self.runtime.adapter.after_turn("Same input", "Same output", ctx_a)
        self.runtime.adapter.after_turn("Same input", "Same output", ctx_b)

        promoted = self.runtime.adapter.memory.promote_pending_memories()
        # Both turns should be promoted and not collapsed as duplicate item_ids
        self.assertEqual(promoted, 2)


if __name__ == "__main__":
    unittest.main()
