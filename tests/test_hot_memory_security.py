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
