import functools
import logging
import re
from typing import Callable, Any
from .memory.core import MemorySystem
from .events import bus, LogEvent

logger = logging.getLogger("daming_os.middleware")

# 项 16：不在 import 时构建 MemorySystem，避免在当前目录生成 memory/、SQLite 与事件订阅；
# 改为装饰器首次调用时懒加载。
_global_memory = None


def _get_memory():
    global _global_memory
    if _global_memory is None:
        _global_memory = MemorySystem()
    return _global_memory


def attach_memory(auto_recall: bool = False):
    """
    Decorator to attach 大明记忆系统 3.0 to an Agent's processing function.
    Automatically injects context before the function runs and stores the result after.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(agent_input: str, *args, **kwargs) -> Any:
            memory = _get_memory()
            # 1. Retrieve Context if auto_recall is enabled
            if auto_recall:
                context = memory.query(agent_input)
                kwargs["daming_os_context"] = context
            
            # 2. Execute Agent
            result = func(agent_input, *args, **kwargs)
            
            # 3. Store Memory (cleaning out <MemoryHint> tag and applying truncation safety)
            cleaned_input = re.sub(r"<MemoryHint>.*?</MemoryHint>", "", agent_input, flags=re.DOTALL)
            
            max_len = 1000
            cleaned_input_str = str(cleaned_input)
            if len(cleaned_input_str) > max_len:
                cleaned_input_str = cleaned_input_str[:max_len] + "... [Input Truncated]"
                
            result_str = str(result)
            if len(result_str) > max_len:
                result_str = result_str[:max_len] + "... [Result Truncated]"
                
            memory.store(f"Input: {cleaned_input_str} | Result: {result_str}")
            return result
        return wrapper
    return decorator

def attach_growth():
    """
    Decorator to attach 大明成长系统 2.0 to an Agent's processing function.
    Automatically intercepts exceptions and publishes them to the Event Bus for GEP tracking.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                # Publish task success
                bus.publish(LogEvent(log_type="task_complete", content="Agent task completed successfully."))
                return result
            except Exception as e:
                # Intercept exception and trigger growth system
                logger.error(f"Agent execution failed. Publishing to Growth OS: {str(e)}")
                bus.publish(LogEvent(
                    log_type="task_failure", 
                    content=f"Exception caught in agent execution: {str(e)}"
                ))
                raise e
        return wrapper
    return decorator


class DamingMiddleware:
    """ASGI / FastAPI Middleware for Daming OS context injection & trace logging."""
    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any):
        if scope.get("type") == "http":
            headers = dict(scope.get("headers", []))
            trace_id = headers.get(b"x-trace-id", b"").decode("utf-8") or "http_trace"
            if "state" not in scope:
                scope["state"] = {}
            scope["state"]["trace_id"] = trace_id
        await self.app(scope, receive, send)
