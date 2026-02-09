# OpenClaw MCP 集成配置教程

本文档详细记录了如何将 MAI-UI Headless Agent 通过 MCP 协议接入 OpenClaw，实现在 OpenClaw 对话框中用自然语言端到端操控 Android 手机。

全程实测通过，踩坑点均已标注。

---

## 目录

1. [前置条件](#1-前置条件)
2. [Phase 1：验证 Headless Agent](#2-phase-1验证-headless-agent)
3. [Phase 2：验证 MCP Server](#3-phase-2验证-mcp-server)
4. [Phase 3：接入 OpenClaw](#4-phase-3接入-openclaw)
5. [踩坑记录与解决方案](#5-踩坑记录与解决方案)
6. [最终文件清单](#6-最终文件清单)

---

## 1. 前置条件

开始配置前，请确认以下环境已就绪：

| 依赖项 | 验证方式 | 说明 |
|--------|---------|------|
| Python 3.9+ | `python --version` | 需要知道 Python 的**绝对路径**（`which python`） |
| ADB | `adb devices` | 手机已连接且显示 `device` 状态 |
| vLLM 服务 | `curl http://<your-vllm-host>/v1/models` | MAI-UI-8B 模型已部署 |
| Node.js 18+ | `node --version` | OpenClaw 运行依赖 |
| OpenClaw | `openclaw --version` | 通过 `npm install -g openclaw@latest` 安装 |

### 1.1 安装基础依赖

```bash
# 项目基础依赖
cd /path/to/MAI-UI-WebUI
pip install -r requirements.txt

# MCP 协议依赖
pip install -r openclaw/requirements.txt
# 即 pip install "mcp[cli]"
```

---

## 2. Phase 1：验证 Headless Agent

目标：确认 **截图 → vLLM 推理 → ADB 执行** 核心链路正常。

### 2.1 修改测试指令

编辑 `openclaw/headless_runner.py` 底部的 `__main__` 测试块，将测试指令改为你需要的任务：

```python
# openclaw/headless_runner.py 底部
if __name__ == "__main__":
    ...
    result = agent.run_task("打开设置")  # 改为你的测试指令
```

### 2.2 运行测试

```bash
cd /path/to/MAI-UI-WebUI

# 设置环境变量（替换为你的 vLLM 地址）
export API_BASE_URL="http://192.168.32.119:7777/v1"
export PYTHONPATH="$(pwd)"

# 执行
python openclaw/headless_runner.py
```

### 2.3 验收标准

- 终端输出每步的截图、推理、执行日志
- 手机上能看到对应操作被执行
- 最终输出 `"status": "success"`

> **如果这一步失败**，后续都不用做。先确保 vLLM 服务可达、ADB 连接正常。

---

## 3. Phase 2：验证 MCP Server

目标：确认 MCP 协议封装正确，外部客户端可以调用 `perform_mobile_task` 工具。

### 3.1 启动 MCP Inspector

```bash
cd /path/to/MAI-UI-WebUI
npx @modelcontextprotocol/inspector python openclaw/mai_mcp.py
```

浏览器自动打开 Inspector 界面。

### 3.2 设置环境变量

在 Inspector 左侧展开 **"Environment Variables"**，添加：

| Key | Value |
|-----|-------|
| `API_BASE_URL` | 你的 vLLM 地址，如 `http://192.168.32.119:7777/v1` |
| `PYTHONPATH` | MAI-UI-WebUI 项目的绝对路径 |

点击 **Restart** 重新连接。

### 3.3 测试调用

1. 点击顶部 **"Tools"** 标签
2. 选择 `perform_mobile_task`
3. 勾选 **"Run as Task"**（重要！任务耗时较长）
4. 在 `instruction` 参数中输入测试指令，如 `打开设置`
5. 点击 **Run Tool**

### 3.4 验收标准

- Inspector 左下角显示绿色 `● Connected`
- 服务名显示 `MAI-Mobile-Agent`
- Tool 调用返回包含 `"status": "success"` 的结果
- 手机上执行了对应操作

> **踩坑提醒**：如果 Inspector 报 `SyntaxError: Unexpected token ... is not valid JSON`，
> 说明 Python 代码的 `print()` 输出污染了 MCP 的 stdout JSON 通道。
> 详见 [踩坑 #1](#踩坑-1stdout-污染导致-mcp-json-解析失败)。

---

## 4. Phase 3：接入 OpenClaw

这是最复杂的部分，涉及三个配置环节：安装 mcporter → 注册 MCP 服务 → 创建 Skill。

### 4.1 安装 mcporter

OpenClaw 通过 `mcporter` CLI 工具管理和调用 MCP 服务器。

```bash
npm install -g mcporter
```

验证安装：

```bash
mcporter --help
openclaw skills check 2>&1 | grep mcporter
# 应显示 ✓ ready
```

### 4.2 注册 MCP 服务器

使用 `mcporter config add` 注册 `mai-ui-agent`：

```bash
mcporter config add mai-ui-agent \
  --command /your/python/absolute/path \
  --arg /path/to/MAI-UI-WebUI/openclaw/mai_mcp.py \
  --env PYTHONPATH=/path/to/MAI-UI-WebUI \
  --env API_BASE_URL=http://your-vllm-host:port/v1 \
  --env API_KEY=empty \
  --env MODEL_NAME=MAI-UI-8B \
  --description "MAI-UI Mobile Agent: control Android phone via natural language" \
  --scope home
```

> **关键**：`--command` 必须是 Python 的**绝对路径**（用 `which python` 获取），
> 且该 Python 环境里必须已安装 `mcp[cli]`。

验证注册：

```bash
mcporter list
# 应显示 mai-ui-agent (1 tool, healthy)
```

### 4.3 设置超时时间

手机任务是多步操作，耗时 1-5 分钟。mcporter 默认超时仅 30 秒，必须调高。

编辑 `~/.mcporter/mcporter.json`，在 `mai-ui-agent` 配置中添加 `timeout` 字段：

```json
{
  "mcpServers": {
    "mai-ui-agent": {
      "command": "/opt/anaconda3/bin/python",
      "args": ["/path/to/MAI-UI-WebUI/openclaw/mai_mcp.py"],
      "description": "MAI-UI Mobile Agent: control Android phone via natural language",
      "timeout": 600000,
      "env": {
        "PYTHONPATH": "/path/to/MAI-UI-WebUI",
        "API_BASE_URL": "http://your-vllm-host:port/v1",
        "API_KEY": "empty",
        "MODEL_NAME": "MAI-UI-8B"
      }
    }
  },
  "imports": []
}
```

> `600000` = 10 分钟，足够大多数任务完成。

### 4.4 创建 OpenClaw Skill

OpenClaw 的 Agent 通过 Skill 来了解自己有什么能力。需要创建一个 skill 告诉它如何操控手机。

```bash
mkdir -p ~/.openclaw/workspace/skills/mai-ui-phone
```

创建 `~/.openclaw/workspace/skills/mai-ui-phone/SKILL.md`：

```markdown
---
name: mai-ui-phone
description: Control an Android phone via natural language using the MAI-UI Agent. Use when a user asks to perform any action on their phone, mobile device, or Android device — such as opening apps, sending messages, adjusting settings, navigating UI, etc.
metadata:
  {
    "openclaw":
      {
        "emoji": "📱",
        "requires": { "bins": ["mcporter"] },
      },
  }
---

# MAI-UI Phone Control

Use `mcporter` to control an Android phone via the MAI-UI Agent.

## When to use

Trigger this skill whenever the user mentions:
- "手机" (phone), "手机上" (on the phone)
- "打开App" (open an app), "发消息" (send a message)
- Any Android/mobile device operation

## How to call

**IMPORTANT**: Always use `--timeout 600000` because phone tasks are multi-step and take 1–5 minutes.

```bash
mcporter call mai-ui-agent.perform_mobile_task --timeout 600000 instruction="<user's instruction>"
```

## Examples

```bash
mcporter call mai-ui-agent.perform_mobile_task --timeout 600000 instruction="打开设置"
mcporter call mai-ui-agent.perform_mobile_task --timeout 600000 instruction="打开微信，给张三发消息你好"
mcporter call mai-ui-agent.perform_mobile_task --timeout 600000 instruction="打开设置，把亮度调低"
```

## Notes

- The instruction should be clear and specific in natural language (Chinese or English).
- Each task may take 1–5 minutes depending on complexity.
- The phone must be connected via ADB and the screen must be on.
- Do NOT set timeout lower than 600000ms (10 minutes).
```

### 4.5 配置 TOOLS.md

OpenClaw Agent 每次新 session 都会读取 `~/.openclaw/workspace/TOOLS.md`。在里面加上手机操控说明，确保 Agent 知道自己具备这个能力。

在 `TOOLS.md` 中添加：

```markdown
## 📱 Android Phone Control (MAI-UI Agent)

An Android phone is connected via ADB. You can control it with natural language commands using `mcporter`.

**How to use:**

```bash
mcporter call mai-ui-agent.perform_mobile_task --timeout 600000 instruction="<任务指令>"
```

**Examples:**

```bash
mcporter call mai-ui-agent.perform_mobile_task --timeout 600000 instruction="打开设置"
mcporter call mai-ui-agent.perform_mobile_task --timeout 600000 instruction="打开微信，给张三发消息你好"
```

**Important:**

- Always use `--timeout 600000` (tasks take 1-5 minutes, multiple steps).
- The instruction should be clear natural language (Chinese or English).
- When user mentions "手机", "phone", "打开App", "发消息" or any mobile operation, use this tool.
```

> **为什么 Skill 和 TOOLS.md 都要写？**
> - **Skill**（`SKILL.md`）：定义工具的通用用法，是可共享的
> - **TOOLS.md**：记录你的环境特定信息，是私有的
> - 两者配合才能确保 Agent 在所有场景下都能识别并正确调用

### 4.6 重启并测试

```bash
# 重启 OpenClaw gateway
openclaw gateway restart

# 验证 skill 已加载
openclaw skills list 2>&1 | grep mai-ui
# 应显示 ✓ ready │ 📱 mai-ui-phone
```

在 OpenClaw 仪表盘（`openclaw dashboard`）中：

1. 点击 **"New session"**（必须新开 session 才能加载最新配置）
2. 输入指令，例如：`在手机上打开设置，把亮度调低`
3. Agent 应自动调用 `mcporter call mai-ui-agent.perform_mobile_task`
4. 等待执行完成，Agent 返回执行结果

---

## 5. 踩坑记录与解决方案

### 踩坑 #1：stdout 污染导致 MCP JSON 解析失败

**现象**：Inspector 报错 `SyntaxError: Unexpected token 'M', "Messages ("... is not valid JSON`

**原因**：MCP 协议通过 stdout 传输 JSON-RPC 消息。底层模块（`mai_naivigation_agent.py`、`adb_utils.py`）大量使用 `print()` 输出调试信息到 stdout，MCP 客户端把这些文本当 JSON 解析就会报错。

**错误修法**：`sys.stdout = sys.stderr` —— 这会同时把 MCP 自己的 JSON 输出也重定向掉，导致 MCP 无法通信。

**正确修法**：覆写 `builtins.print`，让 `print()` 默认输出到 stderr，而 `sys.stdout` 保持不动给 MCP 使用。

```python
import builtins
import sys

_builtin_print = builtins.print

def _print_to_stderr(*args, **kwargs):
    kwargs.setdefault("file", sys.stderr)
    _builtin_print(*args, **kwargs)

builtins.print = _print_to_stderr
```

> 此代码已内置在 `mai_mcp.py` 顶部，无需手动修改。

### 踩坑 #2：OpenClaw 不支持 `mcpServers` 顶层配置字段

**现象**：在 `~/.openclaw/openclaw.json` 中添加 `mcpServers` 字段后报错 `Unrecognized key: "mcpServers"`

**原因**：OpenClaw **不**像 Claude Desktop 那样在主配置文件中直接定义 MCP 服务器。它使用 `mcporter` CLI 工具单独管理 MCP 服务器，配置文件位于 `~/.mcporter/mcporter.json`。

**正确做法**：使用 `mcporter config add` 命令注册服务。

### 踩坑 #3：Agent 不调用手机工具，直接说 "我无法控制手机"

**现象**：在 OpenClaw 对话框输入手机操控指令，Agent 回复说无法操作手机。

**原因**：OpenClaw Agent 启动时读取 `TOOLS.md` 和 Skills 来了解自己的能力。如果这些文件里没有提及手机操控，Agent 就不知道自己能做这件事。

**解决方案**：同时在两处添加说明：
1. `~/.openclaw/workspace/TOOLS.md` — Agent 每次 session 必读
2. `~/.openclaw/workspace/skills/mai-ui-phone/SKILL.md` — 通用 skill 定义

### 踩坑 #4：任务执行几步后超时中断

**现象**：手机上开始执行操作了，但只执行了 1-2 步就断开，Agent 报告超时。

**原因**：`mcporter` 默认调用超时为 30 秒，而手机任务通常需要 1-5 分钟（多步操作，每步含截图+推理+执行+等待）。

**解决方案**：三处都要设置超时：

| 文件 | 字段 | 值 |
|------|------|-----|
| `~/.mcporter/mcporter.json` | `"timeout": 600000` | 服务级别超时 |
| `~/.openclaw/workspace/TOOLS.md` | `--timeout 600000` | Agent 命令模板 |
| Skill `SKILL.md` | `--timeout 600000` | Skill 命令模板 |

### 踩坑 #5：修改配置后 Agent 无变化

**现象**：修改了 Skill 或 TOOLS.md 后，Agent 行为没变。

**原因**：OpenClaw Agent 在 session 创建时加载配置，已有 session 不会自动刷新。

**解决方案**：
1. 修改配置后，在 OpenClaw 界面点击 **"New session"**
2. 如果修改了 `mcporter` 配置或安装了新工具，需要先 `openclaw gateway restart`

---

## 6. 最终文件清单

配置完成后，涉及的文件如下：

### 项目代码（`openclaw/` 目录）

```
openclaw/
├── __init__.py                     # 包入口
├── headless_runner.py              # 无头 Agent 核心（观测-推理-执行循环）
├── mai_mcp.py                      # MCP Server（含 stdout 保护）
├── openclaw_config_example.json    # 配置参考模板
├── requirements.txt                # 额外依赖（mcp[cli]）
├── DEVELOPMENT.md                  # 开发过程文档
└── SETUP_GUIDE.md                  # 本配置教程
```

### OpenClaw 侧配置

```
~/.mcporter/mcporter.json          # MCP 服务器注册（mcporter config add 生成）
~/.openclaw/workspace/TOOLS.md     # Agent 能力声明（添加手机操控说明）
~/.openclaw/workspace/skills/
  └── mai-ui-phone/
      └── SKILL.md                 # 手机操控 Skill（教 Agent 何时/如何调用）
```

### 端到端数据流

```
用户（OpenClaw 对话框）
  │
  │  "在手机上打开设置"
  ▼
OpenClaw Agent（Qwen Coder）
  │
  │  读取 TOOLS.md + mai-ui-phone Skill → 识别为手机操控意图
  │  执行 shell 命令:
  │  mcporter call mai-ui-agent.perform_mobile_task --timeout 600000 instruction="打开设置"
  ▼
mcporter CLI
  │
  │  stdio 连接 → 启动 mai_mcp.py 子进程
  ▼
mai_mcp.py（MCP Server）
  │
  │  调用 HeadlessMAIAgent.run_task("打开设置")
  ▼
HeadlessMAIAgent（观测-推理-执行循环）
  │
  ├─→ ADB screencap  → PIL Image（截图）
  ├─→ vLLM API       → action dict（推理）
  └─→ ADB tap/swipe  → 执行动作
  │
  ▼
Android 手机
```
