import pytest
from daming_os.growth.advanced import LLMCouncilRole

def test_ssrf_prevention_scheme():
    # Provide dummy API key so it doesn't trigger early return
    role = LLMCouncilRole(base_url="file:///etc/passwd", api_key="dummy_key", model="dummy_model")
    proposal = {"payload": {"test": "data"}}
    result = role.review(proposal, role="reviewer")
    assert "LLM review fallback" in result.get("evidence", "")
    assert "Invalid URL scheme: file" in result.get("evidence", "")

def test_ssrf_prevention_domain():
    # Provide dummy API key so it doesn't trigger early return
    role = LLMCouncilRole(base_url="http://127.0.0.1:8080", api_key="dummy_key", model="dummy_model")
    proposal = {"payload": {"test": "data"}}
    result = role.review(proposal, role="reviewer")
    assert "LLM review fallback" in result.get("evidence", "")
    assert "resolves to private/loopback IP 127.0.0.1" in result.get("evidence", "")

def test_ssrf_prevention_domain_localhost():
    # Provide dummy API key so it doesn't trigger early return
    role = LLMCouncilRole(base_url="http://localhost:8080", api_key="dummy_key", model="dummy_model")
    proposal = {"payload": {"test": "data"}}
    result = role.review(proposal, role="reviewer")
    assert "LLM review fallback" in result.get("evidence", "")
    assert "resolves to private/loopback IP 127.0.0.1" in result.get("evidence", "")
