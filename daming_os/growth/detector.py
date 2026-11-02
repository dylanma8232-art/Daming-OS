import logging
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from ..config import config
from ..events import bus, EvolutionTriggeredEvent, LogEvent
from .governance import GEPPolicy
from .proposals import ProposalStore

logger = logging.getLogger("daming_os.growth.detector")

class GEPDetector:
    """
    Growth Experience Point (GEP) detection engine.
    Calculates sliding window exponentially decayed scores to detect evolution triggers.
    """
    def __init__(self, proposal_store: ProposalStore = None, policy: GEPPolicy = None):
        self.policy = policy or GEPPolicy(threshold=config.GEP_THRESHOLD)
        self.gep_threshold = self.policy.threshold
        self.decay_factor = 0.5  # compatibility only; policy is authoritative
        self.window_events = []
        self.seen_events = {}  # sha256 -> timestamp
        self.proposal_store = proposal_store or ProposalStore()
        self._consumed_path = Path(config.WORKSPACE_ROOT) / "memory" / "gep-consumed.json"
        
        # Subscribe to LogEvent to calculate real-time GEP
        bus.subscribe(LogEvent, self._on_log_event)

    def close(self) -> None:
        """Detach from the process-global bus when a host runtime stops."""
        bus.unsubscribe(LogEvent, self._on_log_event)

    def _on_log_event(self, event: LogEvent):
        """Processes incoming events (errors, new findings) and calculates GEP."""
        # 5-minute SHA256 sliding window deduplication
        event_hash = hashlib.sha256(event.content.encode('utf-8')).hexdigest()
        now = datetime.now(timezone.utc).timestamp()
        
        # Clean up old seen_events (5-minute window)
        self.seen_events = {h: ts for h, ts in self.seen_events.items() if now - ts < 300}
        
        if event_hash in self.seen_events:
            logger.debug(f"Event {event_hash} deduplicated (within 5 mins).")
            return
            
        self.seen_events[event_hash] = now
        
        raw_score = self._assign_base_score(event.log_type)
        # Enforce a min(3.0, score) ceiling cap per event
        score = min(3.0, raw_score)
        
        if score > 0:
            self.window_events.append({
                "timestamp": now,
                "score": score,
                "log_type": event.log_type,
                "content": event.content,
                "hash": event_hash
            })
            
            total_gep = self.calculate_current_gep()
            logger.info(f"Current GEP: {total_gep:.2f} / {self.gep_threshold}")
            
            # Decay is evaluated in real time; three just-recorded 1.0 events
            # are microscopically below 3.0 by the time of comparison.  Treat
            # that numerical noise as the documented threshold, not a missed
            # growth trigger.
            if total_gep + 0.01 >= self.gep_threshold:
                self.trigger_evolution()

    def reconcile(self, events) -> int:
        """Replay persisted lifecycle events after a host restart.

        The normal hook remains the low-latency path; this scheduled path means
        a short-lived agent process cannot silently lose GEP evidence.

        项 8：保留回放事件的原始时间戳，并持久化已消费事件，防止旧故障被
        重复回放而虚假触发进化提案。
        """
        before = len(self.window_events)
        consumed = self._load_consumed()
        newly_seen = 0
        for event in events:
            content = str(event.get("content", ""))
            if not content:
                continue
            event_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            if event_hash in consumed or event_hash in self.seen_events:
                continue
            timestamp = self._event_timestamp(event)
            self.seen_events[event_hash] = timestamp
            score = min(3.0, self._assign_base_score(str(event.get("log_type", ""))))
            if score > 0:
                self.window_events.append({
                    "timestamp": timestamp,
                    "score": score,
                    "log_type": event.get("log_type", ""),
                    "content": content,
                    "hash": event_hash
                })
                newly_seen += 1
            consumed.add(event_hash)
        self._save_consumed(consumed)
        if newly_seen:
            total_gep = self.calculate_current_gep()
            if total_gep + 0.01 >= self.gep_threshold:
                self.trigger_evolution()
        return newly_seen

    def _event_timestamp(self, event) -> float:
        raw = event.get("timestamp")
        try:
            if isinstance(raw, (int, float)):
                return float(raw)
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            return datetime.now(timezone.utc).timestamp()

    def _load_consumed(self) -> set:
        try:
            if self._consumed_path.exists():
                return set(json.loads(self._consumed_path.read_text(encoding="utf-8")))
        except (OSError, ValueError, json.JSONDecodeError):
            logger.warning("Failed to load consumed GEP events; starting empty.")
        return set()

    def _save_consumed(self, consumed: set) -> None:
        try:
            self._consumed_path.parent.mkdir(parents=True, exist_ok=True)
            self._consumed_path.write_text(json.dumps(sorted(consumed)), encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to persist consumed GEP events: %s", exc)

    def _assign_base_score(self, log_type: str) -> float:
        """Assign base GEP score based on event type."""
        return self.policy.weights.get(log_type, 0.0)

    def calculate_current_gep(self) -> float:
        """Calculate time-decayed GEP over the sliding window."""
        now = datetime.now(timezone.utc)
        valid_events = []
        for ev in self.window_events:
            timestamp = datetime.fromtimestamp(ev["timestamp"], timezone.utc)
            if (now - timestamp).total_seconds() < self.policy.window_hours * 3600:
                valid_events.append(ev)
        self.window_events = valid_events
        return self.policy.score([{"log_type": ev.get("log_type", "task_failure"), "content": ev["content"], "timestamp": datetime.fromtimestamp(ev["timestamp"], timezone.utc).isoformat()} for ev in valid_events], now)

    def trigger_evolution(self):
        """Trigger the evolution orchestrator when GEP threshold is reached."""
        logger.warning(f"GEP Threshold ({self.gep_threshold}) reached! Triggering Evolution Protocol.")
        triggering_events = list(self.window_events)
        self.window_events.clear()  # Reset after trigger
        proposal_id = self.proposal_store.create({
            "kind": "growth",
            "gep_score": self.gep_threshold,
            "source_events": triggering_events,
        })
        bus.publish(EvolutionTriggeredEvent(
            gep_score=self.gep_threshold,
            events=triggering_events,
            proposal_id=proposal_id,
        ))
        logger.info("Created durable growth proposal: %s", proposal_id)
