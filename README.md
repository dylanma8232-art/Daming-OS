# Agent OS: Decoupled Memory & Growth Systems
> A fully independent, event-driven OS layer for autonomous agents.

Agent OS abstracts the core concepts of **Memory Management** and **Meta-Learning (Growth)** into two decoupled, plug-and-play subsystems. It is designed to be attached to any LLM Agent framework (AutoGen, CrewAI, LangChain) to provide L1/L2 semantic caching, long-term memory retrieval, and AST-gated self-evolution capabilities.

## Architecture

1. **Memory OS**: Provides 3-Way RRF (Reciprocal Rank Fusion) retrieval across LanceDB (Dense Vectors), SQLite FTS5 (Sparse Text), and Spreading Activation graphs. Features a mathematical L1/L2 cache with Utility-based mixed eviction and Similarity Annealing to prevent catastrophic overfitting.
2. **Growth OS**: A meta-learning engine that tracks "Growth Experience Points" (GEP) via a sliding window. When an agent encounters enough errors or discoveries, it triggers an Evolution Protocol: Dual-agent debate -> AST validation -> Physical Sandbox Smoke Tests -> Human-in-the-Loop Webhook Approval -> Atomic Deployment.

The two systems are completely physically and logically decoupled. They communicate exclusively via a lightweight `EventBus`.

## Quick Start

### Installation

```bash
pip install agent-os
```

### Basic Integration

Use the provided middleware decorators to instantly attach Memory and Growth capabilities to your existing agent loops.

```python
from agent_os import middleware

@middleware.attach_memory()
@middleware.attach_growth()
def my_agent_loop(user_input: str, **kwargs):
    context = kwargs.get("agent_os_context", [])
    print(f"I have {len(context)} memories related to this!")
    
    # If the agent crashes here, the Growth OS automatically intercepts the exception,
    # increases the GEP score, and if threshold is met, begins self-healing evolution!
    # ...
    return "Agent Output"
```

### Configuration

All paths and hyperparameters are controlled via environment variables or the `AgentOSConfig` class. No hardcoded absolute paths exist.

```bash
export AGENT_OS_WORKSPACE="/path/to/your/agent/workspace"
export AGENT_OS_GEP_THRESHOLD="5.0"
export AGENT_OS_SANDBOX_DIR="/tmp/agent_sandbox"
```

## Contributing
Contributions are welcome! Please ensure that no framework-specific tight coupling is introduced. Maintain the strict Event-Driven separation between the Memory and Growth subsystems.

---

# 中文说明

Agent OS 将大明天子的“记忆系统 3.0”与“成长系统 2.0”进行彻底剥离解耦，打造了一个纯净的、事件驱动（Event-Driven）的 Agent 基础设施。

通过解耦：
- **记忆系统**仅负责状态检索与缓存网关，不会越权去管理任何沙箱编译。
- **成长系统**仅负责监控日志（EventBus）、积累 GEP 并执行沙箱演化，不再强绑定特定的 LanceDB 检索逻辑或飞书审批（现已抽象为 `NotificationAdapter`）。
