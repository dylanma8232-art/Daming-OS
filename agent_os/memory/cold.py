import logging
from typing import List, Dict, Any
from .db import fts5_search

logger = logging.getLogger("agent_os.memory.cold")

def sparse_search(query: str, db_path: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """SQLite FTS5 Sparse Text Search. Layer 3 (Cold)."""
    try:
        return fts5_search(query, db_path=db_path, top_k=top_k)
    except Exception as e:
        logger.warning(f"FTS5 search failed: {e}")
        return []
