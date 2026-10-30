import tempfile
from pathlib import Path
from daming_os.memory.cache import HardenedSemanticCache
from daming_os.memory.governance import MemoryScope


def test_semantic_cache_l2_scope_isolation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache_file = str(Path(tmp_dir) / "test-cache.json")
        cache = HardenedSemanticCache(cache_file=cache_file)

        tenant_a_query = "scope:tenantA||\nwhat is my bank account number"
        tenant_b_query = "scope:tenantB||\nwhat is my bank account number"
        tenant_a_var = "scope:tenantA||\ntell me my bank account number"

        vector_a = [1.0, 0.0, 0.0]
        vector_b = [0.99, 0.01, 0.0]  # Very high cosine similarity to vector_a

        # Store response for Tenant A
        cache.set(tenant_a_query, [{"id": "account_a", "content": "Tenant A account: 12345"}], vector_a)

        # Tenant B queries with nearly identical embedding vector
        result_b = cache.get(tenant_b_query, vector_b)
        assert result_b is None, "Tenant B should NOT receive Tenant A's cached result"

        # Tenant A queries with semantic variation
        result_a_var = cache.get(tenant_a_var, vector_b)
        assert result_a_var is not None, "Tenant A should hit L2 cache for its own scope"
        assert result_a_var[0]["id"] == "account_a"


def test_semantic_cache_explicit_scope_param():
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
        assert res_b is None, "Tenant B query with explicit scope should miss Tenant A's cache entry"

        # Tenant A query with scope_a
        res_a = cache.get("tell me my bank account number", vector_b, scope=scope_a)
        assert res_a is not None, "Tenant A query with explicit scope should hit Tenant A's cache entry"
        assert res_a[0]["id"] == "account_a"
