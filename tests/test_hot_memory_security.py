import pytest
import os
import shutil
from daming_os.memory.hot import SessionStateMachine

@pytest.fixture
def test_session_dir():
    dir_name = "test_hot_memory_session_dir"
    os.makedirs(dir_name, exist_ok=True)
    yield dir_name
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)

def test_hot_memory_valid_session_key(test_session_dir):
    machine = SessionStateMachine(test_session_dir)
    assert machine.write_memory("valid_key_123", {"data": "test"}) == True
    assert machine.read_memory("valid_key_123") == {"data": "test"}

def test_hot_memory_invalid_session_key_path_traversal(test_session_dir):
    machine = SessionStateMachine(test_session_dir)
    assert machine.write_memory("../../../../../tmp/hacked", {"data": "test"}) == False
    assert machine.read_memory("../../../../../tmp/hacked") == {}

def test_hot_memory_invalid_session_key_forward_slash(test_session_dir):
    machine = SessionStateMachine(test_session_dir)
    assert machine.write_memory("valid/key", {"data": "test"}) == False
    assert machine.read_memory("valid/key") == {}

def test_hot_memory_invalid_session_key_special_chars(test_session_dir):
    machine = SessionStateMachine(test_session_dir)
    assert machine.write_memory("valid@key!", {"data": "test"}) == False
    assert machine.read_memory("valid@key!") == {}

def test_semantic_cache_l2_scope_isolation(tmp_path):
    from daming_os.memory.cache import HardenedSemanticCache

    cache_file = str(tmp_path / "cache.json")
    cache = HardenedSemanticCache(cache_file=cache_file)

    query_tenant1 = "scope:tenant1|agent1|session1\nWhat is the secret key?"
    query_tenant2 = "scope:tenant2|agent1|session1\nWhat is the secret key?"

    # Vector that is identical or near-identical for both questions
    vec1 = [0.1] * 10
    vec2 = [0.1] * 10

    cache.set(query_tenant1, [{"id": "secret1", "content": "Tenant 1 Secret"}], query_vector=vec1)

    # L1 cache miss for tenant2 because query string differs
    # L2 cache lookup for tenant2 must NOT return tenant1's response
    result_tenant2 = cache.get(query_tenant2, query_vector=vec2)
    assert result_tenant2 is None

    # L2 cache lookup for tenant1 should hit (or L1 hit)
    result_tenant1 = cache.get(query_tenant1, query_vector=vec1)
    assert result_tenant1 == [{"id": "secret1", "content": "Tenant 1 Secret"}]
