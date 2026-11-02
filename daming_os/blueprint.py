"""Executable whitepaper inventory: source-script aliases → one runtime capability."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Capability:
    name: str
    source_scripts: tuple[str, ...]
    trigger: str


# The 88-file inventory contains aliases and maintenance helpers.  They are
# intentionally grouped by behavior so Daming OS does not duplicate a feature
# merely because its historical server implementation had several script names.
CAPABILITIES: tuple[Capability, ...] = (
    Capability("hot_capture", ("hot_memory_manager.py", "hot_memory_writer.py", "hot_write_turn.py", "memory_middleware.py"), "before_turn/after_turn"),
    Capability("hybrid_recall", ("hybrid_search.py", "search.py", "warm_memory_query.py", "lancedb_manager.py", "learnings_reader.py"), "before_turn"),
    Capability("graph_activation", ("hybrid_search.py --graph", "wiki_search.py"), "before_turn"),
    Capability("semantic_cache", ("semantic_cache.py", "cache_invalidator.py"), "before_turn/after_turn"),
    Capability("context_compaction", ("message_compactor.py", "session_compactor.py", "pending_summary_consumer.py", "memory_block.py"), "before_turn"),
    Capability("durable_storage", ("sqlite_manager.py", "embedding_utils.py", "migrate_memory_db.py", "fts5_rebuilder.py"), "bootstrap/deep-sleep"),
    Capability("consolidation", ("memory_consolidator.py", "memory_maintenance.py", "sleep_time_agent.py", "update-learnings-summary.py", "vectorize_diaries.py", "vectorize_learnings.py"), "daily@02:00"),
    Capability("wiki_graph_sync", ("wiki_builder.py", "wiki_sync.py", "wiki_restructure.py", "feishu-create-wiki-doc.py", "feishu-md-to-blocks.py"), "daily@03:15"),
    Capability("reviews_quality", ("daily_reviewer.py", "weekly_reviewer.py", "quality_gate.py", "quality-enforce.py", "claims_review.py", "agent_as_judge.py", "benchmark.py"), "daily/weekly"),
    Capability("archive_cleanup", ("glacier_storage.py", "cleanup-orphans.py", "system_cleaner.py", "cleanup.py", "session-cleaner.py", "session-rotator.py", "session_watchdog.py", "test_glacier.py"), "daily/weekly"),
    Capability("skill_lifecycle", ("skills_lazy_loader.py", "skill-usage-tracker.py", "skill-patch-tracker.py", "learning-to-skill.py", "apply_experience.py"), "hook/daily"),
    Capability("event_pipeline", ("event-log-writer.py", "event_log_writer.py", "event_log_reader.py", "event_auto_capture.py", "event_pipeline.py", "extract_experience.py", "proactive_discovery.py", "evolution_consumer.py", "experience_review.py"), "hook/daily"),
    Capability("gep_detection", ("gep_detector.py", "gep_manager.py", "gep_monitor.py", "capability-evolver.py", "capability_evolver.py"), "hook/daily/weekly"),
    Capability("growth_extraction", ("growth_extractor.py", "evolution_engine.py"), "daily"),
    Capability("twin_audit", ("audit_engine.py", "proposal-tracker.py"), "weekly"),
    Capability("approval", ("feishu_callback.py",), "approval_provider"),
    Capability("safe_deploy", ("code_compiler.py", "sica_guard.py", "config_guard.py", "version_manager.py"), "approval/workflow"),
    Capability("proactive_health", ("proactive_inspector.py", "memory_healthcheck.py", "system_healthcheck.py", "file_tracker.py", "verify_flow.py"), "daily"),
    Capability("command_and_meta_evolution", ("/xuexi", "meta-prompt", "plugin-container"), "hook/weekly"),
    Capability("path_rules", ("path_scoped_rules.py",), "retrieval/deploy"),
    Capability("golden_paths", ("golden_path.py",), "host/provider"),
)


def inventory() -> Dict[str, List[str]]:
    return {capability.name: list(capability.source_scripts) for capability in CAPABILITIES}


def triggers() -> Dict[str, str]:
    return {capability.name: capability.trigger for capability in CAPABILITIES}


def missing_runtime_triggers(runtime: object) -> List[str]:
    """Return whitepaper capabilities with no matching standard runtime route."""
    jobs = set(getattr(getattr(runtime, "scheduler", None), "jobs", {}))
    # 钩子/请求路径驱动，不需要调度作业。
    hooked = {"hot_capture", "hybrid_recall", "graph_activation", "semantic_cache", "context_compaction",
              "event_pipeline", "gep_detection", "approval", "safe_deploy", "command_and_meta_evolution",
              "path_rules", "golden_paths"}
    # 项 21：按 runtime.py 实际注册的调度作业（daily-maintenance / weekly-governance /
    # daily-digest / watchdog）映射能力，不再用 deep-sleep-agent / nightly-growth-pipeline
    # 等从未注册的陈旧作业名。
    scheduled = {
        "durable_storage": ("daily-maintenance",),
        "consolidation": ("daily-maintenance",),
        "wiki_graph_sync": ("daily-maintenance",),
        "reviews_quality": ("weekly-governance", "daily-digest"),
        "archive_cleanup": ("daily-maintenance", "weekly-governance"),
        "skill_lifecycle": ("weekly-governance",),
        "growth_extraction": ("weekly-governance",),
        "twin_audit": ("weekly-governance",),
        "proactive_health": ("daily-maintenance", "weekly-governance"),
    }
    return [capability.name for capability in CAPABILITIES
            if capability.name not in hooked and (
                capability.name not in scheduled or not any(job in jobs for job in scheduled[capability.name])
            )]
