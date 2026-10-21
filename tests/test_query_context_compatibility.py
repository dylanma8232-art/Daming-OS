from unittest.mock import Mock

import pytest

from daming_os.memory.core import MemorySystem, QueryContext, QueryOptions


def test_context_and_options_share_cached_retrieval_without_mutation():
    memory = MemorySystem.__new__(MemorySystem)
    memory.embedding_provider = Mock()
    memory.embedding_provider.embed.return_value = [1.0]
    memory.cache = Mock()
    memory.cache.get.return_value = [{"id": "first"}, {"id": "second"}]
    context = QueryContext(top_k=1)
    assert memory.query("question", context=context) == [{"id": "first"}]
    assert memory.query("question", options=QueryOptions(top_k=1)) == [{"id": "first"}]
    assert context.query_vector is None
    with pytest.raises(ValueError):
        memory.query("question", options=QueryOptions(), context=context)
