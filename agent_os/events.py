import logging
from typing import Callable, Dict, List, Any

logger = logging.getLogger("agent_os.events")

class Event:
    """Base class for all Agent OS events."""
    pass

class EvolutionCompletedEvent(Event):
    """Fired when the Growth System completes a successful evolution."""
    def __init__(self, proposal_id: str, diff_summary: str, scope_tags: List[str]):
        self.proposal_id = proposal_id
        self.diff_summary = diff_summary
        self.scope_tags = scope_tags

class LogEvent(Event):
    """Fired when an Agent encounters an error or discovers a new finding."""
    def __init__(self, log_type: str, content: str, metadata: dict = None):
        self.log_type = log_type
        self.content = content
        self.metadata = metadata or {}

class EventBus:
    """A simple synchronous Pub/Sub event bus to decouple subsystems."""
    def __init__(self):
        self._subscribers: Dict[type, List[Callable[[Event], None]]] = {}

    def subscribe(self, event_type: type, callback: Callable[[Event], None]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event: Event):
        event_type = type(event)
        subscribers = self._subscribers.get(event_type, [])
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event subscriber {callback}: {e}")

# Global event bus instance
bus = EventBus()
