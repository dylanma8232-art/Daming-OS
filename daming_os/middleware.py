import functools
import logging
from typing import Callable, Any
from .memory.core import MemorySystem
from .events import bus, LogEvent

logger = logging.getLogger("daming_os.middleware")

# Global instances for the decorators to use
_global_memory = MemorySystem()

def attach_memory():
    """
    Decorator to attach 大明记忆系统 3.0 to an Agent's processing function.
    Automatically injects context before the function runs and stores the result after.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(agent_input: str, *args, **kwargs) -> Any:
            # 1. Retrieve Context
            context = _global_memory.query(agent_input)
            kwargs["daming_os_context"] = context
            
            # 2. Execute Agent
            result = func(agent_input, *args, **kwargs)
            
            # 3. Store Memory
            _global_memory.store(f"Input: {agent_input} | Result: {result}")
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
