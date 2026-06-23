import os
from pydantic import BaseModel, Field

class AgentOSConfig(BaseModel):
    # Base paths
    WORKSPACE_ROOT: str = Field(default_factory=lambda: os.getenv("AGENT_OS_WORKSPACE", os.getcwd()))
    
    # Memory System Paths
    MEMORY_DB_PATH: str = Field(default_factory=lambda: os.getenv("AGENT_OS_MEMORY_DB", "memory/lancedb"))
    SQLITE_META_PATH: str = Field(default_factory=lambda: os.getenv("AGENT_OS_SQLITE_META", "memory/memory_meta.db"))
    WIKI_DIR: str = Field(default_factory=lambda: os.getenv("AGENT_OS_WIKI_DIR", "wiki/main"))
    
    # Growth System Paths
    EVENT_LOG_PATH: str = Field(default_factory=lambda: os.getenv("AGENT_OS_EVENT_LOG", "memory/event_logs.jsonl"))
    GROWTH_DB_PATH: str = Field(default_factory=lambda: os.getenv("AGENT_OS_GROWTH_DB", "memory/growth_system.db"))
    SANDBOX_BASE_DIR: str = Field(default_factory=lambda: os.getenv("AGENT_OS_SANDBOX_DIR", "/tmp/sandbox"))
    PROPOSAL_DIR: str = Field(default_factory=lambda: os.getenv("AGENT_OS_PROPOSAL_DIR", "memory/evolution-proposals"))
    
    # Growth System Tuning
    GEP_THRESHOLD: float = Field(default=5.0)
    MAX_SANDBOX_RETRIES: int = Field(default=2)

config = AgentOSConfig()
