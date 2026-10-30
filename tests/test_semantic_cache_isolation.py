import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from daming_os.config import config
from daming_os.memory.cache import HardenedSemanticCache
from daming_os.memory.core import MemorySystem, QueryOptions
from daming_os.memory.governance import MemoryScope


class TestSemanticCacheIsolation(unittest.TestCase):
    def test_l2_cache_scope_partitioning(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_file = os.path.join(tmp, "semantic-cache.json")
            cache = HardenedSemanticCache(cache_file=cache_file, l_min=1)

            query_a = "scope:tenant_a|agent_1|session_1\nWhat is the system secret key?"
            vector_a = [0.1, 0.2, 0.3, 0.4, 0.5]
            response_a = [{"id": "secret_a", "content": "Tenant A Secret"}]

            cache.set(query_a, response_a, query_vector=vector_a)

            # Tenant B asks the exact same long question with identical vector
            query_b = "scope:tenant_b|agent_1|session_1\nWhat is the system secret key?"
            vector_b = [0.1, 0.2, 0.3, 0.4, 0.5]

            # L2 cache lookup for Tenant B must return None due to scope partitioning
            res_b = cache.get(query_b, query_vector=vector_b)
            self.assertIsNone(res_b)

            # Tenant A lookup should hit L1 or L2
            res_a = cache.get(query_a, query_vector=vector_a)
            self.assertEqual(res_a, response_a)

    def test_semantic_cache_explicit_scope_param(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_file = str(Path(tmp_dir) / "test-cache-explicit.json")
            cache = HardenedSemanticCache(cache_file=cache_file)

            scope_a = MemoryScope(tenant_id="tenantA")
            scope_b = MemoryScope(tenant_id="tenantB")

            vector_a = [1.0, 0.0, 0.0]
            vector_b = [0.99, 0.01, 0.0]

            cache.set("what is my bank account number", [{"id": "account_a"}], vector_a, scope=scope_a)

            # Tenant B query with scope_b
            res_b = cache.get("what is my bank account number", vector_b, scope=scope_b)
            self.assertIsNone(res_b, "Tenant B query with explicit scope should miss Tenant A's cache entry")

            # Tenant A query with scope_a
            res_a = cache.get("tell me my bank account number", vector_b, scope=scope_a)
            self.assertIsNotNone(res_a, "Tenant A query with explicit scope should hit Tenant A's cache entry")
            self.assertEqual(res_a[0]["id"], "account_a")

    def test_daming_memory_tenant_cache_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(config, "WORKSPACE_ROOT", tmp), \
                 patch.object(config, "MEMORY_DB_PATH", os.path.join(tmp, "memory.db")):
                memory = MemorySystem()

                scope_a = MemoryScope(tenant_id="tenant_a", agent_id="agent_1", session_id="session_1")
                scope_b = MemoryScope(tenant_id="tenant_b", agent_id="agent_1", session_id="session_1")

                # Store memory for Tenant A
                memory.store("Tenant A sensitive configuration data", metadata={"type": "config"}, scope=scope_a)
                memory.promote_pending_memories()

                # Tenant A queries memory (populates L2 cache for Tenant A scope)
                results_a = memory.query("What is the sensitive configuration data?", options=QueryOptions(scope=scope_a))
                self.assertGreater(len(results_a), 0)
                self.assertIn("Tenant A", results_a[0]["content"])

                # Tenant B queries identical question
                results_b = memory.query("What is the sensitive configuration data?", options=QueryOptions(scope=scope_b))
                # Tenant B must not see Tenant A's memories via L2 cache
                for r in results_b:
                    self.assertNotIn("Tenant A", r.get("content", ""))

    def test_cached_result_revalidation_filters_deleted_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(config, "WORKSPACE_ROOT", tmp), \
                 patch.object(config, "MEMORY_DB_PATH", os.path.join(tmp, "memory.db")):
                memory = MemorySystem()

                scope_a = MemoryScope(tenant_id="tenant_a", agent_id="agent_1", session_id="session_1")

                # Store memory for Tenant A
                memory.store("Temporary secret token to be deleted", metadata={"type": "temp"}, scope=scope_a)
                memory.promote_pending_memories()

                # First query populates cache
                results_1 = memory.query("What is the temporary secret token?", options=QueryOptions(scope=scope_a))
                self.assertGreater(len(results_1), 0)

                item_id = results_1[0]["id"]

                # Delete metadata record directly from SQLite to simulate deletion/expiry
                with sqlite3.connect(memory.sqlite_path) as conn:
                    conn.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
                    conn.commit()

                # Second query hits cache, but revalidation should filter out deleted item
                results_2 = memory.query("What is the temporary secret token?", options=QueryOptions(scope=scope_a))
                deleted_ids = [r["id"] for r in results_2]
                self.assertNotIn(item_id, deleted_ids)


if __name__ == "__main__":
    unittest.main()
