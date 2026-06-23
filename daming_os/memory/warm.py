import logging
from typing import List, Dict, Any

logger = logging.getLogger("daming_os.memory.warm")

def vector_search(query: str, query_vector: List[float], db_path: str, top_k: int = 20) -> List[Dict[str, Any]]:
    """LanceDB Dense Vector Search. Layer 2 (Warm)."""
    try:
        import lancedb
        db = lancedb.connect(db_path)
        tables = db.list_tables()
        if hasattr(tables, 'tables'):
            table_names = list(tables.tables)
        else:
            table_names = list(tables) if isinstance(tables, (list, tuple)) else []

        if 'learnings' in table_names:
            table = db.open_table('learnings')
            results = table.search(query_vector).limit(top_k).to_list()
            return [{"id": r.get("item_id", r.get("id", "")), "score": 1.0 - r.get("_distance", 0), "source": "lancedb"} for r in results]
    except Exception as e:
        logger.warning(f"LanceDB search failed: {e}")
    return []
