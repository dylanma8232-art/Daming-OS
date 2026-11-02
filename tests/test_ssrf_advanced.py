import pytest
from daming_os.growth.advanced import LLMCouncilRole

def test_ssrf_prevention():
    # Provide dummy API key so it doesn't trigger early return
    role = LLMCouncilRole(base_url="file:///etc/passwd", api_key="dummy_key", model="dummy_model")

    proposal = {"payload": {"test": "data"}}

    result = role.review(proposal, role="reviewer")

    assert "LLM review fallback" in result.get("evidence", "")
    assert "Invalid URL scheme: file" in result.get("evidence", "")
