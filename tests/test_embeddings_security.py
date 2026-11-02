import json
import pytest
from daming_os.memory.embeddings import OpenAICompatibleEmbeddingProvider

def test_ssrf_protection_rejects_invalid_scheme():
    """Verify that OpenAICompatibleEmbeddingProvider rejects non-http/https schemes."""
    provider = OpenAICompatibleEmbeddingProvider(
        model="test-model",
        base_url="file:///etc/passwd",
        api_key="test-key"
    )

    with pytest.raises(ValueError, match="Invalid base_url scheme"):
        provider.embed("test text")

def test_ssrf_protection_allows_http():
    """Verify that OpenAICompatibleEmbeddingProvider allows http schemes."""
    provider = OpenAICompatibleEmbeddingProvider(
        model="test-model",
        base_url="http://example.com/v1",
        api_key="test-key"
    )

    # We expect a URLError or similar because example.com/v1/embeddings doesn't exist,
    # but it should NOT raise the ValueError for invalid scheme.
    import urllib.error
    try:
        provider.embed("test text")
    except ValueError as e:
        if "Invalid base_url scheme" in str(e):
            pytest.fail("ValueError was raised for valid HTTP scheme.")
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, Exception):
        pass # Expected since it's a dummy URL

def test_ssrf_protection_allows_https():
    """Verify that OpenAICompatibleEmbeddingProvider allows https schemes."""
    provider = OpenAICompatibleEmbeddingProvider(
        model="test-model",
        base_url="https://example.com/v1",
        api_key="test-key"
    )

    import urllib.error
    try:
        provider.embed("test text")
    except ValueError as e:
        if "Invalid base_url scheme" in str(e):
            pytest.fail("ValueError was raised for valid HTTPS scheme.")
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, Exception):
        pass # Expected since it's a dummy URL
