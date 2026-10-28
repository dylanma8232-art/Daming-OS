import pytest
from typing import Dict, Any

from daming_os.scheduling import Heartbeat, HeartbeatRunner

def test_heartbeat_runner_success():
    def check_true():
        return True

    def check_false():
        return False

    def check_truthy():
        return "yes"

    runner = HeartbeatRunner([
        Heartbeat(name="service_true", check=check_true),
        Heartbeat(name="service_false", check=check_false),
        Heartbeat(name="service_truthy", check=check_truthy)
    ])

    result = runner.run()

    assert result == {
        "service_true": {"ok": True},
        "service_false": {"ok": False},
        "service_truthy": {"ok": True}
    }

def test_heartbeat_runner_failure():
    def check_error():
        raise ValueError("Connection failed")

    runner = HeartbeatRunner([
        Heartbeat(name="service_error", check=check_error)
    ])

    result = runner.run()

    assert result == {
        "service_error": {"ok": False, "error": "Connection failed"}
    }

def test_heartbeat_runner_mixed():
    def check_ok():
        return True

    def check_error():
        raise RuntimeError("Disk full")

    runner = HeartbeatRunner([
        Heartbeat(name="ok", check=check_ok),
        Heartbeat(name="error", check=check_error)
    ])

    result = runner.run()

    assert result == {
        "ok": {"ok": True},
        "error": {"ok": False, "error": "Disk full"}
    }
