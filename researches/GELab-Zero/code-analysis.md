# GELab-Zero 深度代码解构

> **作者**: Damon Li  
> **更新日期**: 2026年1月  
> **源码仓库**: [stepfun-ai/gelab-zero](https://github.com/stepfun-ai/gelab-zero)

## 一、项目概览

GELab-Zero 是阶跃星辰（StepFun）开源的首个完整"模型+基础设施"的 GUI Agent 解决方案。它提供即插即用的工程实现，无需云端依赖，支持完全的本地隐私控制。

### 1.1 仓库结构

```
gelab-zero/
├── README.md                    # 英文文档
├── README_CN.md                 # 中文文档
├── LICENSE                      # MIT 许可证
├── requirements.txt             # Python 依赖
├── model_config.yaml            # 模型配置
├── mcp_server_config.yaml       # MCP 服务器配置
├── yadb                         # Android 调试工具
│
├── copilot_agent_client/        # Agent 客户端
│   ├── local_server_based_runner.py
│   ├── mcp_agent_loop.py        # MCP Agent 循环（核心）
│   └── pu_client.py             # 客户端接口
│
├── copilot_agent_server/        # Agent 服务端
│   ├── base_server.py           # 基础服务器
│   ├── local_server.py          # 本地服务器
│   ├── parser_factory.py        # 解析器工厂
│   └── server_factory.py        # 服务器工厂
│
├── copilot_front_end/           # 前端执行器
│   ├── mobile_action_helper.py  # 移动端操作辅助
│   ├── package_map.py           # 应用包名映射
│   └── pu_frontend_executor.py  # 前端动作执行器（核心）
│
├── copilot_tools/               # 工具模块
│   ├── action_tools.py          # 动作工具
│   ├── base_parser.py           # 基础解析器
│   └── parser_0920_summary.py   # 解析器实现
│
├── mcp_server/                  # MCP 服务器
│   ├── simple_gelab_mcp_server.py      # 简单 MCP 服务器
│   ├── detailed_gelab_mcp_server.py    # 详细 MCP 服务器
│   └── mcp_backend_implements.py       # 后端实现
│
├── tools/                       # 辅助工具
│   ├── ask_llm_v2.py           # LLM 调用接口
│   ├── image_tools.py          # 图像处理工具
│   └── prompt_tools.py         # 提示词工具
│
├── examples/                    # 示例代码
│   ├── run_single_task.py      # 单任务运行
│   ├── run_task_via_mcp.py     # MCP 任务运行
│   └── run_test_api.py         # API 测试
│
├── visualization/               # 可视化工具
│   └── main_page.py            # 轨迹可视化
│
├── images/                      # 图片资源
└── report/                      # 报告目录
```

### 1.2 技术栈

| 组件 | 技术选型 | 说明 |
|-----|---------|------|
| 基础模型 | Qwen3-VL-4B-Instruct | 视觉语言模型基座 |
| 推理框架 | Ollama / vLLM | 本地模型推理 |
| 设备控制 | ADB (Android Debug Bridge) | Android 设备控制 |
| MCP 框架 | FastMCP | Model Context Protocol 实现 |
| 图像处理 | PIL / Base64 | 截图处理与传输 |
| 配置管理 | YAML | 配置文件格式 |

---

## 二、核心架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GELab-Zero 系统架构                              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────────┐
│   MCP Client    │────▶│   MCP Server    │────▶│   Agent Server          │
│  (Claude/GPT)   │     │  (FastMCP)      │     │  (LocalServer)          │
└─────────────────┘     └─────────────────┘     └─────────────────────────┘
                                                          │
                                                          ▼
                                               ┌─────────────────────────┐
                                               │   Agent Loop            │
                                               │  (mcp_agent_loop.py)    │
                                               └─────────────────────────┘
                                                          │
                              ┌────────────────────────────┼────────────────────────────┐
                              ▼                            ▼                            ▼
                    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
                    │  截图捕获        │         │  LLM 推理        │         │  动作执行        │
                    │  (ADB screencap)│         │  (Ollama/vLLM)  │         │  (ADB input)    │
                    └─────────────────┘         └─────────────────┘         └─────────────────┘
                              │                            │                            │
                              └────────────────────────────┼────────────────────────────┘
                                                          ▼
                                               ┌─────────────────────────┐
                                               │   Android Device        │
                                               │   (via ADB)             │
                                               └─────────────────────────┘
```

### 2.2 核心设计理念

1. **完全本地化**：所有组件可在消费级硬件上运行，无需云端依赖
2. **MCP 协议支持**：通过 Model Context Protocol 实现与各类 AI 助手的集成
3. **模块化设计**：客户端、服务端、执行器分离，易于扩展
4. **隐私优先**：数据完全在本地处理，保护用户隐私

---

## 三、核心模块解析

### 3.1 MCP Agent Loop (mcp_agent_loop.py)

这是 GELab-Zero 的核心循环，负责协调截图、推理和执行的完整流程。

#### 3.1.1 主循环函数

```python
def gui_agent_loop(
    agent_server,           # Agent 服务器实例
    agent_loop_config: dict, # 循环配置
    device_id: str,         # 设备 ID
    max_steps: int,         # 最大步数
    enable_intermediate_logs: bool = False,
    enable_intermediate_image_caption: bool = False,
    enable_intermediate_screenshots: bool = False,
    enable_final_screenshot: bool = False,
    enable_final_image_caption: bool = False,
    reset_environment: bool = True,
    reflush_app: bool = True,
    reply_mode: str = "pass_to_client",
    task: str = None,
    session_id: str = None,
    extra_info: dict = {},
    reply_from_client: str = None,
):
    """
    在设备上执行任务的主循环
    
    支持的 reply_mode:
    - "auto_reply": 自动回复 INFO 动作
    - "no_reply": 忽略 INFO 动作
    - "manual_reply": 手动回复
    - "pass_to_client": 传递给 MCP 客户端处理
    """
```

#### 3.1.2 执行流程

```python
for step_idx in range(max_steps):
    # 1. 检查屏幕状态
    if not dectect_screen_on(device_id):
        stop_reason = "MANUAL_STOP_SCREEN_OFF"
        break
    
    # 2. 捕获截图
    image_path = capture_screenshot(device_id, "tmp_screenshot")
    image_b64_url = make_b64_url(image_path)
    
    # 3. 可选：异步生成图像描述
    if enable_intermediate_image_caption:
        caption_thread = threading.Thread(
            target=caption_current_screenshot,
            args=(task, image_b64_url, model_config)
        )
        caption_thread.start()
    
    # 4. 构建请求载荷
    payload = {
        "session_id": session_id,
        "observation": {
            "screenshot": {
                "type": "image_url",
                "image_url": {"url": image_b64_url}
            }
        }
    }
    
    # 5. 调用 Agent 服务器获取动作
    server_return = agent_server.automate_step(payload)
    action = server_return['action']
    
    # 6. 执行动作
    # ... 动作执行逻辑
```

#### 3.1.3 自动回复机制

当 Agent 需要用户澄清时，可以自动生成回复：

```python
def auto_reply(current_image_url, task, info_action, model_provider, model_name):
    """
    使用 LLM 自动生成对 Agent 澄清问题的回复
    
    Prompt 模板:
    - 角色：扮演正在使用 GUI Agent 的用户
    - 任务：根据背景信息生成简短直接的回答
    - 要求：极其简短、直接命中核心
    """
    messages_to_ask = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"任务目标: {task}\nAgent 问的问题: {info_action}"},
                {"type": "image_url", "image_url": {"url": current_image_url}},
                {"type": "text", "text": "请简洁直接地回答Agent的问题。"}
            ]
        }
    ]
    return ask_llm_anything(model_provider, model_name, messages_to_ask)
```

---

### 3.2 前端执行器 (pu_frontend_executor.py)

负责将 Agent 输出的抽象动作转换为具体的 ADB 命令并执行。

#### 3.2.1 支持的动作类型

```python
valid_actions = [
    "CLICK",      # 点击
    "LONGPRESS",  # 长按
    "TYPE",       # 文本输入
    "SCROLL",     # 滚动
    "AWAKE",      # 唤醒应用
    "SLIDE",      # 滑动
    "BACK",       # 返回键
    "HOME",       # Home 键
    "COMPLETE",   # 任务完成
    "ABORT",      # 任务中止
    "INFO",       # 信息请求
    "WAIT",       # 等待
    "HOT_KEY"     # 热键
]
```

#### 3.2.2 坐标转换

GELab-Zero 使用 1000x1000 的归一化坐标系统：

```python
def _convert_normalized_point_to_fixed_point(point):
    """
    将归一化坐标 (0.0-1.0) 转换为固定坐标 (0-1000)
    """
    x, y = point
    assert 0.0 <= float(x) <= 1.0
    assert 0.0 <= float(y) <= 1.0
    
    fixed_x = int(float(x) * 1000)
    fixed_y = int(float(y) * 1000)
    return (fixed_x, fixed_y)

def _convert_point_to_realworld_point(point, wm_size):
    """
    将固定坐标 (0-1000) 转换为实际屏幕像素坐标
    """
    x, y = point
    real_x = (float(x) / 1000) * wm_size[0]
    real_y = (float(y) / 1000) * wm_size[1]
    return (real_x, real_y)
```

#### 3.2.3 动作执行实现

```python
def act_on_device(frontend_action, device_id, wm_size, print_command=False, reflush_app=True):
    """
    在设备上执行前端动作
    """
    action_type = frontend_action["action_type"]
    
    if action_type == "CLICK":
        # 检测屏幕方向
        orientation = _detect_screen_orientation(device_id)
        if orientation in [1, 3]:  # 横屏
            wm_size = (wm_size[1], wm_size[0])
        
        x, y = _convert_point_to_realworld_point(frontend_action["point"], wm_size)
        cmd = f"adb -s {device_id} shell input tap {x} {y}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result
    
    elif action_type == "LONGPRESS":
        x, y = _convert_point_to_realworld_point(frontend_action["point"], wm_size)
        duration = frontend_action["duration"]
        # 使用 yadb 工具实现精确的长按
        cmd = f"adb -s {device_id} shell app_process -Djava.class.path=/data/local/tmp/yadb /data/local/tmp com.ysbing.yadb.Main -touch {x} {y} {int(duration * 1000)}"
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    elif action_type == "TYPE":
        value = frontend_action["value"]
        # 使用 yadb 工具实现中文输入
        cmd = f'adb -s {device_id} shell app_process -Djava.class.path=/data/local/tmp/yadb /data/local/tmp com.ysbing.yadb.Main -keyboard "{value}"'
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # ... 其他动作类型
```

---

### 3.3 MCP Server (simple_gelab_mcp_server.py)

基于 FastMCP 框架实现的 MCP 服务器，提供标准化的工具接口。

#### 3.3.1 服务器初始化

```python
from fastmcp import FastMCP

mcp = FastMCP(
    name="Gelab-MCP-Server",
    instructions="""
    This MCP server provides tools to interact with connected mobile devices using a GUI agent.
    """
)
```

#### 3.3.2 工具定义

**列出连接设备**：

```python
@mcp.tool
def list_connected_devices() -> list:
    """
    List all connected mobile devices.
    
    Returns:
        list: A list of connected device IDs.
    """
    devices = get_device_list()
    return devices
```

**执行任务**：

```python
@mcp.tool
def ask_agent(
    device_id: Annotated[str, Field(description="ID of the device")],
    task: Annotated[str | None, Field(description="The task to perform")],
    max_steps: Annotated[int, Field(description="Maximum steps")] = 20,
) -> dict:
    """
    Ask GUI Agent to start performing a new task on a connected device.
    
    ## Agent 能力限制:
    1. 任务必须与已安装的应用相关
    2. 任务必须简单具体，一次一个应用一件事
    3. 不支持复杂的多步推理任务
    4. 不支持多模态输入
    
    ## 使用指南:
    1. 不要让 Agent 直接支付或下单
    2. 遇到人机验证时，让用户手动处理
    3. 任务失败或切换应用时，重新开始新任务
    """
    return execute_task(
        device_id=device_id,
        task=task,
        reset_environment=True,
        max_steps=max_steps,
        # ... 其他参数
    )
```

#### 3.3.3 服务器启动

```python
with open("mcp_server_config.yaml", "r") as f:
    mcp_server_config = yaml.safe_load(f)

mcp.run(
    transport="http",
    port=mcp_server_config['server_config'].get("mcp_server_port", 8702)
)
```

---

### 3.4 动作格式转换

GELab-Zero 支持多种动作格式的转换：

#### 3.4.1 UI-TARS 格式转换

```python
def uiTars_to_frontend_action(ui_action):
    """
    将 UI-TARS 格式的动作转换为前端动作格式
    """
    action_type = ui_action.get("action") or ui_action.get("action_type")
    ui_action['action_type'] = action_type
    
    if action_type == "WAIT":
        seconds = float(ui_action.get("value", 5))
        ui_action["seconds"] = seconds
    elif action_type == "LONGPRESS":
        duration = ui_action.get("duration", 1.5)
        ui_action["duration"] = float(duration)
    
    return ui_action
```

#### 3.4.2 Step API 格式转换

```python
def step_api_to_frontend_action(step_api_action, default_duration=1.5):
    """
    将 Step API 格式转换为前端动作格式
    """
    action_type_map = {
        "Click": "CLICK",
        "Type": "TYPE",
        "Complete": "COMPLETE",
        "Pop": "INFO",
        "Wait": "WAIT",
        "Awake": "AWAKE",
        "Abort": "ABORT",
        "Scroll": "SLIDE",
        "LongPress": "LONGPRESS",
    }
    
    action_type = step_api_action.get("action") or step_api_action.get("action_type")
    frontend_action_type = action_type_map[action_type]
    
    frontend_action = {"action_type": frontend_action_type}
    
    if action_type == "CLICK":
        point = _convert_normalized_point_to_fixed_point(
            step_api_action["args"]["normalized_point"]
        )
        frontend_action["point"] = point
    
    # ... 其他动作类型处理
    
    return frontend_action
```

---

## 四、配置系统

### 4.1 模型配置 (model_config.yaml)

```yaml
model_name: "GELab-Zero-4B-preview"
model_provider: "ollama"  # 或 "vllm"
```

### 4.2 MCP 服务器配置 (mcp_server_config.yaml)

```yaml
server_config:
  mcp_server_port: 8702
  
agent_loop_config:
  task_type: "mobile"
  delay_after_capture: 2
  model_config:
    model_name: "GELab-Zero-4B-preview"
    model_provider: "ollama"
  caption_config:
    model_config:
      model_name: "GELab-Zero-4B-preview"
      model_provider: "ollama"
```

---

## 五、部署指南

### 5.1 环境要求

- Python 3.12+
- Android 设备（已开启开发者模式）
- ADB 工具
- Ollama 或 vLLM（用于模型推理）

### 5.2 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/stepfun-ai/gelab-zero.git
cd gelab-zero

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装模型（使用 Ollama）
ollama pull stepfun-ai/GELab-Zero-4B-preview

# 4. 连接 Android 设备
adb devices

# 5. 运行示例
python examples/run_single_task.py
```

---

## 六、性能基准

### 6.1 开源基准评测

| 基准 | GELab-Zero-4B | 其他开源模型 |
|-----|--------------|-------------|
| AndroidWorld | **80.2%** (8B) | - |
| OSWorld | **48.5%** (8B) | - |
| ScreenSpot-Pro | **62.6%** (8B) | - |
| AndroidDaily (静态) | **89.91%** (8B) | - |
| AndroidDaily (端到端) | **52.50%** (8B) | - |

### 6.2 硬件要求

| 配置 | 推荐规格 |
|-----|---------|
| Mac | M1/M2/M3 系列 |
| NVIDIA GPU | RTX 4060 及以上 |
| 内存 | 16GB+ |
| 存储 | 20GB+ 可用空间 |

---

## 七、总结

GELab-Zero 的代码架构体现了以下设计理念：

1. **完全开源**：首个同时开源模型和基础设施的 GUI Agent 项目
2. **本地优先**：所有组件可在消费级硬件上运行
3. **MCP 集成**：通过标准协议与各类 AI 助手集成
4. **模块化设计**：客户端、服务端、执行器分离，易于定制
5. **隐私保护**：数据完全在本地处理

核心代码组织清晰，文档完善，是学习 GUI Agent 工程实现的优秀参考。

---

## 参考文献

1. [Step-GUI Technical Report](https://arxiv.org/abs/2512.15431)
2. [GELab-Engine (NeurIPS 2025)](https://github.com/summoneryhl/gelab-engine)
3. [Model Context Protocol Specification](https://modelcontextprotocol.io/)
4. [FastMCP Documentation](https://github.com/jlowin/fastmcp)
