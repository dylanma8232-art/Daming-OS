import time
import os
from daming_os.memory.core import SpreadingActivationTraverser
from daming_os.memory.db import HardenedSQLiteManager

db_path = "test_perf.db"

# create dummy db
manager = HardenedSQLiteManager(db_path)
conn = manager._get_connection()
conn.execute("""
    CREATE TABLE IF NOT EXISTS wiki_edges (
        source_node TEXT,
        target_node TEXT,
        link_type TEXT,
        weight REAL
    )
""")
# Insert dummy data
edges = []
for i in range(1000):
    for j in range(10):
        edges.append((f"node_{i}", f"node_{(i+j)%1000}", "link", 0.5))
conn.executemany("INSERT INTO wiki_edges (source_node, target_node, link_type, weight) VALUES (?, ?, ?, ?)", edges)
conn.commit()
conn.close()

traverser = SpreadingActivationTraverser()
seed_ids = ["node_1", "node_50", "node_100"]

start = time.time()
for _ in range(1000):
    traverser.traverse(seed_ids, db_path)
end = time.time()

print(f"Time taken: {end - start:.4f} seconds")

# clean up
os.remove(db_path)
