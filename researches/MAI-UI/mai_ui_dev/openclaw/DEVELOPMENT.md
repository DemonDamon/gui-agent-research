# OpenClaw - MAI-UI Headless Agent & MCP Integration

## 1. 项目背景

本模块将 `MAI-UI-WebUI` 仓库中原有的 GUI Agent 核心逻辑（`web_ui/agent_runner.py`）进行解耦，剥离 Gradio 等 UI 依赖，封装为**无头（Headless）Python 服务**，并通过 **Model Context Protocol (MCP)** 标准协议接入 OpenClaw，实现通过自然语言端到端控制 Android 设备。

### 1.1 核心目标

| 阶段 | 产出 | 说明 |
|------|------|------|
| Phase 1 | `headless_runner.py` | 从 `agent_runner.py` 剥离 UI 依赖，构建 `HeadlessMAIAgent` 类 |
| Phase 2 | `mai_mcp.py` | 开发 MCP Server，将手机操控能力暴露为标准 Tool |
| Phase 3 | `openclaw_config_example.json` | 提供 OpenClaw 集成配置模板 |

### 1.2 数据流

```
User (OpenClaw)
    │
    ▼ MCP Protocol (stdio)
mai_mcp.py ─── perform_mobile_task(instruction)
    │
    ▼
HeadlessMAIAgent.run_task(instruction)
    │
    ├──→ _get_observation()  ──→ ADB screencap  ──→ PIL Image
    ├──→ _predict()          ──→ vLLM API       ──→ action dict
    └──→ _execute_action()   ──→ ADB tap/swipe/type/...
    │
    ▼
Android Device
```

---

## 2. 原始代码库分析

在动手编码前，我们深度阅读了以下核心文件：

### 2.1 `web_ui/agent_runner.py` — 原始 Agent 运行器

**职责**：整合 MAI-UI 模型推理与 ADB 设备操作，驱动 观测→推理→执行 循环。

**关键发现**：

1. **Gradio 强耦合**：`AgentRunner` 使用了 `threading.Lock`、`is_paused`、`waiting_for_input` 等状态管理，大量围绕 Gradio Web UI 的交互需求设计（暂停/恢复/用户输入）。这些在无头模式下均不需要。
2. **坐标转换**：模型输出的归一化坐标 `(0.0-1.0)` 通过 `int(coords[0] * img_width)` 映射回截图的实际像素坐标，而非设备物理分辨率。这一点至关重要——截图尺寸即是坐标参考系。
3. **截图缩放**：在送入模型前，会将截图缩放到 `max_dim=1200` 以控制 Token 消耗，但坐标映射仍基于**原始截图尺寸**（非缩放后尺寸）。
4. **终止条件**：`action_type == "terminate"` 或 `action_type == "answer"` 表示任务结束。

### 2.2 `src/mai_naivigation_agent.py` — 模型推理核心

**职责**：封装 vLLM 调用逻辑，包括 Prompt 构建、历史管理、响应解析。

**关键发现**：

1. **System Prompt 敏感**：模型对 Prompt 格式极度敏感，`MAI_MOBILE_SYS_PROMPT` 定义了严格的 XML 输出格式（`<thinking>` + `<tool_call>`），任何修改都可能导致模型输出异常。
2. **坐标 SCALE_FACTOR=999**：模型输出的坐标范围是 `[0, 999]`，解析时除以 999 归一化到 `[0, 1]`。
3. **历史上下文**：通过 `TrajMemory` 维护多步对话历史，每次请求将历史截图和响应拼入 messages 列表。
4. **重试机制**：LLM 调用内置 3 次重试，解析失败会 fallback。

### 2.3 `web_ui/adb_utils.py` — ADB 操作工具集

**职责**：提供 Android 设备的底层操作接口。

**关键发现**：

1. **两种截图模式**：流模式（`exec-out screencap`）和文件模式（先存 `/sdcard` 再 `pull`），文件模式更适合慢速网络。
2. **设备缓存**：`DeviceCache` 类缓存设备 ID 和分辨率，30 秒 TTL。
3. **中文输入支持**：通过 `yadb` 工具实现（自动推送到设备 `/data/local/tmp/yadb`）。
4. **可直接复用**：该模块无 UI 依赖，可原样在无头模式中使用。

### 2.4 `src/prompt.py` — Prompt 模板

**关键点**：严格复用，不做任何修改。`HeadlessMAIAgent` 通过实例化 `MAIUINaivigationAgent` 间接使用这些 Prompt。

---

## 3. 开发过程

### 3.1 Phase 1: `headless_runner.py` — HeadlessMAIAgent

**设计思路**：

- **最小化重写**：不重新实现推理逻辑，而是直接实例化 `MAIUINaivigationAgent` 作为内部引擎，确保 Prompt、解析、历史管理与原始行为完全一致。
- **职责清晰**：`HeadlessMAIAgent` 只负责三件事：(1) 截图 (2) 转发给 Agent 推理 (3) 执行 ADB 动作。
- **去 UI 化**：移除所有 Gradio 相关概念（暂停/恢复/回调/线程锁/用户输入等待）。

**类结构**：

```python
class HeadlessMAIAgent:
    def __init__(model_url, api_key, model_name, device_id, ...)
    def run_task(instruction, max_steps=15) -> dict    # 主入口
    def _auto_detect_device()                           # ADB 设备自动发现
    def _init_agent()                                   # 初始化底层 Agent
    def _get_observation() -> Image                     # 截图
    def _predict(instruction, screenshot) -> (str, dict)# 推理
    def _execute_action(action, screenshot) -> (bool, str)# 执行
```

**关键决策记录**：

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 是否复用 `MAIUINaivigationAgent` | 复用 | 避免重复实现 Prompt 构建和响应解析，降低出错风险 |
| 坐标映射基准 | 原始截图尺寸 | 与原 `agent_runner.py` 一致，模型看到的是截图，坐标是相对截图的 |
| 历史管理 | 委托给 `MAIUINaivigationAgent` | 它内部已有 `TrajMemory` 滑动窗口机制 |
| `ask_user` 处理 | 记录日志后跳过 | 无头模式无交互能力，避免阻塞 |

### 3.2 Phase 2: `mai_mcp.py` — MCP Server

**设计思路**：

- **全局单例**：`HeadlessMAIAgent` 使用全局单例模式，避免每次 MCP 调用都重新连接 ADB。
- **Tool 描述详尽**：`perform_mobile_task` 的 docstring 详细描述了功能和用法，OpenClaw 依赖此描述进行意图路由。
- **结果格式化**：将 JSON 结果转为人类可读的文本，便于 OpenClaw 展示给用户。

**配置方式**：所有可变参数通过环境变量注入，不硬编码：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `API_BASE_URL` | `http://localhost:8000/v1` | vLLM 服务地址 |
| `API_KEY` | `empty` | API 密钥 |
| `MODEL_NAME` | `MAI-UI-8B` | 模型名称 |
| `DEVICE_ID` | 自动检测 | ADB 设备 ID |

### 3.3 Phase 3: OpenClaw 配置

提供 `openclaw_config_example.json` 配置模板，用户需根据实际环境修改路径和地址。

---

## 4. 文件清单

```
openclaw/
├── __init__.py                     # 包入口，导出 HeadlessMAIAgent
├── headless_runner.py              # Phase 1: 无头 Agent 核心
├── mai_mcp.py                      # Phase 2: MCP Server 入口
├── openclaw_config_example.json    # Phase 3: OpenClaw 配置模板
├── requirements.txt                # 额外依赖（mcp[cli]）
└── DEVELOPMENT.md                  # 本文档
```

---

## 5. 使用指南

### 5.1 环境准备

```bash
# 1. 安装基础依赖
pip install -r requirements.txt

# 2. 安装 MCP 依赖
pip install -r openclaw/requirements.txt

# 3. 确保 ADB 可用
adb devices

# 4. 确保 vLLM 服务运行中
# （需要提前部署 MAI-UI-8B 模型）
```

### 5.2 独立测试（Phase 1 验收）

```bash
# 设置环境变量（按需修改）
export API_BASE_URL="http://localhost:8000/v1"
export PYTHONPATH="/path/to/MAI-UI-WebUI"

# 运行测试
python openclaw/headless_runner.py
```

预期行为：手机上打开"设置"应用。

### 5.3 MCP Inspector 调试（Phase 2 验收）

```bash
npx @modelcontextprotocol/inspector python openclaw/mai_mcp.py
```

在 Inspector 界面中应能看到 `perform_mobile_task` 工具，输入指令即可调用。

### 5.4 OpenClaw 端到端集成（Phase 3 验收）

1. 将 `openclaw_config_example.json` 中的配置合并到 OpenClaw 的 `config.json`
2. 修改 `PYTHONPATH` 为本项目的实际绝对路径
3. 修改 `python` 为虚拟环境中的 Python 绝对路径（推荐）
4. 在 OpenClaw 对话框输入 "把手机亮度调低"，等待执行完成

---

## 6. 技术约束与注意事项

1. **Prompt 刚性**：严禁修改 `src/prompt.py` 中的 System Prompt 和 `<|image|>` 标记位置，模型对格式极度敏感。
2. **Context 长度**：`MAIUINaivigationAgent` 内部通过 `history_n` 参数控制上下文窗口，默认保留 1 步历史。如遇 Context 溢出，可降低此值。
3. **ADB 并发安全**：MCP Server 默认单进程单线程运行（stdio 传输），天然避免 ADB 指令冲突。如需扩展为多客户端，需额外加锁。
4. **零 UI 依赖**：`headless_runner.py` 不引入 `gradio` 或任何 GUI 框架，import 链已验证无间接依赖。

---

## 7. 与原代码库的关系

| 模块 | 策略 | 说明 |
|------|------|------|
| `web_ui/adb_utils.py` | **直接复用** | 无 UI 依赖，通过 `sys.path` 导入 |
| `src/mai_naivigation_agent.py` | **直接复用** | 实例化使用，不修改 |
| `src/prompt.py` | **严格复用** | 通过 Agent 间接使用，不直接 import |
| `src/base.py` / `src/unified_memory.py` / `src/utils.py` | **间接依赖** | 被 Agent 内部使用 |
| `web_ui/agent_runner.py` | **参考但不依赖** | 逻辑重构为 `headless_runner.py` |
| `web_ui/package_map.py` | **间接使用** | 通过 `adb_utils.open_app()` 调用 |
