import os
import json
import time
import math
import fcntl
import logging
import collections
from typing import Dict, Any, Optional, List

logger = logging.getLogger("daming_os.memory.cache")

class HardenedSemanticCache:
    """
    Decoupled L1/L2 Semantic Cache Engine.
    Supports adaptive threshold truncation and utility-based LFU-LRU mixed eviction.
    Integrates Similarity Annealing Factor to counter cache overfitting.
    Uses physical JSON persistence with fcntl.flock.
    """
    def __init__(self, 
                 max_size: int = 1000, 
                 t_inf: float = 0.82, 
                 l_min: int = 5, 
                 alpha: float = 0.15,
                 w_f: float = 0.6, 
                 w_t: float = 0.4, 
                 lambda_decay: float = 0.0289,
                 hr_window_size: int = 100,
                 hr_target: float = 0.80,
                 beta_anneal: float = 0.10,
                 cache_file: str = "/tmp/daming_os_semantic_cache.json"):
        self.max_size = max_size
        self.t_inf = t_inf
        self.l_min = l_min
        self.alpha = alpha
        self.w_f = w_f
        self.w_t = w_t
        self.lambda_decay = lambda_decay
        
        self.hr_target = hr_target
        self.beta_anneal = beta_anneal
        self.hit_history = collections.deque(maxlen=hr_window_size)
        
        self.cache_file = cache_file
        
        # Initialize file if not exists
        if not os.path.exists(self.cache_file):
            self._save_state({"l1_cache": {}, "l2_cache": {}})

    def _load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.cache_file):
            return {"l1_cache": {}, "l2_cache": {}}
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                try:
                    return json.load(f)
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return {"l1_cache": {}, "l2_cache": {}}

    def _save_state(self, state: Dict[str, Any]):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    json.dump(state, f, ensure_ascii=False, indent=2)
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def get_adaptive_threshold(self, query: str, hit_rate: float = 0.0) -> float:
        L = len(query)
        if L < self.l_min:
            return 1.0
        clamped_diff = max(0, L - self.l_min)
        threshold = self.t_inf + (1.0 - self.t_inf) * math.exp(-self.alpha * clamped_diff)
        
        if hit_rate > self.hr_target:
            normalized_diff = (hit_rate - self.hr_target) / (1.0 - self.hr_target)
            eta = self.beta_anneal * (normalized_diff ** 2)
            threshold = threshold + eta * (1.0 - threshold)
            
        return threshold

    def calculate_utility(self, freq: int, last_used: float, t_now: float) -> float:
        delta_t_seconds = t_now - last_used
        delta_t_hours = max(0.0, delta_t_seconds / 3600.0)
        utility = self.w_f * math.log1p(freq) + self.w_t * math.exp(-self.lambda_decay * delta_t_hours)
        return utility

    def get(self, query: str, query_vector: Optional[List[float]] = None) -> Optional[Any]:
        t_now = time.time()
        state = self._load_state()
        l1_cache = state.get("l1_cache", {})
        l2_cache = state.get("l2_cache", {})
        modified = False
        
        if query in l1_cache:
            entry = l1_cache[query]
            entry["freq"] += 1
            entry["last_used"] = t_now
            self.hit_history.append(1)
            modified = True
            if modified:
                self._save_state({"l1_cache": l1_cache, "l2_cache": l2_cache})
            return entry["response"]
            
        if len(query) < self.l_min or query_vector is None:
            self.hit_history.append(0)
            return None
            
        best_match_key = None
        best_similarity = -1.0
        
        for key, entry in l2_cache.items():
            cache_vector = entry["vector"]
            dot_product = sum(a * b for a, b in zip(query_vector, cache_vector))
            norm_q = math.sqrt(sum(a * a for a in query_vector))
            norm_c = math.sqrt(sum(b * b for b in cache_vector))
            if norm_q > 0.0 and norm_c > 0.0:
                similarity = dot_product / (norm_q * norm_c)
            else:
                similarity = 0.0
                
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_key = key
                
        hr = sum(self.hit_history) / len(self.hit_history) if self.hit_history else 0.0
        threshold = self.get_adaptive_threshold(query, hr)
        
        if best_match_key and best_similarity >= threshold:
            entry = l2_cache[best_match_key]
            entry["freq"] += 1
            entry["last_used"] = t_now
            self.hit_history.append(1)
            modified = True
            if modified:
                self._save_state({"l1_cache": l1_cache, "l2_cache": l2_cache})
            return entry["response"]
            
        self.hit_history.append(0)
        return None

    def set(self, query: str, response: Any, query_vector: Optional[List[float]] = None) -> None:
        t_now = time.time()
        state = self._load_state()
        l1_cache = state.get("l1_cache", {})
        l2_cache = state.get("l2_cache", {})
        
        l1_cache[query] = {
            "response": response,
            "freq": 1,
            "last_used": t_now
        }
        
        if query_vector is not None and len(query) >= self.l_min:
            if len(l2_cache) >= self.max_size:
                # Eviction logic
                least_utility = float('inf')
                evict_key = None
                for key, entry in l2_cache.items():
                    u = self.calculate_utility(entry["freq"], entry["last_used"], t_now)
                    if u < least_utility:
                        least_utility = u
                        evict_key = key
                if evict_key:
                    del l2_cache[evict_key]
                    if evict_key in l1_cache:
                        del l1_cache[evict_key]
                
            l2_cache[query] = {
                "vector": query_vector,
                "response": response,
                "freq": 1,
                "last_used": t_now
            }
            
        self._save_state({"l1_cache": l1_cache, "l2_cache": l2_cache})

    def clear(self):
        """Clear cache manually or upon receiving an evolution event."""
        self._save_state({"l1_cache": {}, "l2_cache": {}})
        self.hit_history.clear()
