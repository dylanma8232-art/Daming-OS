# 大明天子 OS (Daming OS)

**Daming OS** 是一款为自主智能体 (Autonomous Agents) 打造的工业级底座，包含满血版的**大明记忆系统 (Memory System)** 和**大明成长系统 (Growth System)**。它脱胎于复杂的内部生产环境，被完全解耦为一个轻量、极度安全且即插即用的 Python 包。

任何智能体接入 Daming OS，都将瞬间获得物理级的沙箱防御力与冷温热三层级联的永久记忆力。

## 🌟 核心特性 (Features)

### 🧠 大明记忆系统 3.0
- **三层记忆级联 (Hot/Warm/Cold)**：
  - **Hot (热层)**：采用 `os.replace` 原子锁写入临时 Session，绝对防进程撕裂。
  - **Warm (温层)**：内置 LanceDB 密集向量检索。
  - **Cold (冷层)**：内置 SQLite FTS5 稀疏文本检索。
- **3-Way RRF 检索融合**：基于向量相似度、图谱激活扩散与文本稀疏性的 RRF 综合打分。
- **物理衰减扩散公式**：激活扩散支持深度 BFS 队列与真实的 $\beta$ 传递、$\gamma$ 耗散算法。
- **防爆仓信息密度压缩器**：采用独创的 $ID(i) = \frac{\text{Score}_{\text{final}}(i)}{\text{Len}(i)}$ 公式，残酷裁剪长篇大论，誓死捍卫 LLM 上下文。
- **文件级死锁缓存**：基于 `fcntl.flock` 的高并发持久化 JSON 语义缓存。

### 🧬 大明成长系统 2.0
- **AST 物理安检门**：沙箱代码执行前触发深度抽象语法树 (AST) 安检，无情拦截 `subprocess`、`os.system` 等恶意提权代码。
- **沙箱自愈与静默 GC**：烟雾测试失败后立即捕获 stderr 回传 LLM 进行 2 次重试，并自带后台守护线程清理沙箱废弃目录防硬盘泄漏。
- **内阁辩论协议 (Cabinet Swarm)**：经验提取抛弃单线思考，采用多线程并发拉起“红方黑客、蓝方防守、白方裁判”，三方大模型疯狂博弈后产出最高质量经验。
- **防事件风暴**：引入 5 分钟滑动窗口与 SHA256 去重机制，防御死循环引发的积分风暴。
- **插件化审批与 $<1ms$ 物理回滚**：解耦 HITL 鉴权钩子，部署前自动使用 `shutil.copy2` 进行原子级冷备。

---

## 🚀 首次安装与使用说明

### 1. 安装 Daming OS
请确保您的环境是 Python 3.9+，在项目根目录下执行：
```bash
git clone git@github.com:dylanma8232-art/Daming-OS.git
cd Daming-OS
pip install -e .
```

### 2. 一键初始化脚手架
在您自己的 Agent 项目目录中，使用自带的命令行工具生成骨架：
```bash
daming-os init --dir ./my-agent-workspace
```
这将在该目录下自动生成：
- `.env` (环境变量配置文件)
- `AGENTS.md` (系统规范红线模板)
- `session_status.md` (心跳检查文件)

### 3. 配置环境变量
打开生成的 `.env` 文件，填入您的 API 密钥：
```env
DAMING_OS_WORKSPACE="/path/to/my-agent-workspace"
# 填入您使用的大模型 API KEY (支持 OpenAI, Anthropic, DashScope 等)
OPENAI_API_KEY="<YOUR_OPENAI_API_KEY_HERE>"
```

### 4. 在代码中接入使用
```python
import os
from daming_os.middleware import DamingMiddleware

# 1. 挂载中间件
middleware = DamingMiddleware()

user_input = "帮我写一个 Python 脚本"
# 2. 检索前置经验
context = middleware.before_llm(user_input)

print("提取到的祖传经验:", context)

# 3. LLM 处理完毕后，反写经验
middleware.after_llm(user_input, "这是我写出的脚本...", success=True)
```

## 🔐 安全与免责声明
Daming OS 秉持极端防御主义理念，默认封锁一切越权行为。开发者如需放行特定库，请自行修改 `sandbox.py` 中的 `SafetyVisitor` 黑名单。
