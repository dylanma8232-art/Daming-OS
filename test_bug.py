import sys
import os

from daming_os.memory.compactor import MessageCompactor

compactor = MessageCompactor()

# mock llm provider
class MockLLM:
    def complete(self, messages):
        return "compressed text"

compactor.llm_provider = MockLLM()

messages = [
    {"content": "A" * 100, "id": "1"},
]
# Let's say 1 token is approx 1 char for our mock fallback
compacted = compactor.compact_sync(messages, max_tokens=20)
print(compacted)
