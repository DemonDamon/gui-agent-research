# MAI-UI 深度代码解构

> **作者**: Damon Li  
> **更新日期**: 2025年1月  
> **源码仓库**: [Tongyi-MAI/MAI-UI](https://github.com/Tongyi-MAI/MAI-UI)

## 一、项目概览

MAI-UI 是阿里巴巴通义团队开发的面向真实世界的基础 GUI 智能体系列，提供从 2B 到 235B 的全尺寸模型，支持端云协同架构和 MCP 工具调用。

### 1.1 仓库结构

```
MAI-UI/
├── README.md                    # 项目文档
├── LICENSE                      # Apache 2.0 许可证
├── NOTICE                       # 第三方组件声明
├── requirements.txt             # Python 依赖
│
├── src/                         # 核心源码
│   ├── base.py                  # 基础 Agent 类
│   ├── mai_grounding_agent.py   # Grounding Agent
│   ├── mai_naivigation_agent.py # Navigation Agent（核心）
│   ├── prompt.py                # 提示词模板
│   ├── unified_memory.py        # 统一记忆结构
│   └── utils.py                 # 工具函数
│
├── cookbook/                    # 示例 Notebook
│   ├── grounding.ipynb          # Grounding 示例
│   └── run_agent.ipynb          # Navigation 示例
│
├── assets/                      # 资源文件
│   ├── img/                     # 图片
│   └── gif/                     # 演示动图
│
├── resources/                   # 资源目录
└── site/                        # 网站资源
```

### 1.2 技术栈

| 组件 | 技术选型 | 说明 |
|-----|---------|------|
| 基础模型 | MAI-UI-2B/8B/32B/235B | 自研多尺寸模型 |
| 推理框架 | vLLM | 高性能模型推理 |
| API 接口 | OpenAI Compatible | 标准化 API |
| MCP 支持 | Jinja2 模板 | 动态工具注入 |
| 图像处理 | PIL | 截图处理 |
| 数据结构 | dataclasses | 类型安全的数据定义 |

---

## 二、核心架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MAI-UI 系统架构                                  │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   用户指令       │
                              └────────┬────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MAI Navigation Agent                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ 历史管理     │  │ 图像处理     │  │ 消息构建     │  │ 动作解析     │    │
│  │ TrajMemory  │  │ PIL/Base64  │  │ OpenAI API  │  │ JSON Parse  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
           ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
           │  端侧模型    │    │  云端模型    │    │  MCP 工具   │
           │  (2B/8B)    │    │ (32B/235B)  │    │  (高德等)   │
           └─────────────┘    └─────────────┘    └─────────────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       ▼
                              ┌─────────────────┐
                              │   动作执行       │
                              │ click/swipe/... │
                              └─────────────────┘
```

### 2.2 端云协同架构

MAI-UI 的核心创新之一是端云协同架构：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         端云协同决策流程                                  │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   任务输入       │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   任务复杂度     │
                              │   评估器        │
                              └────────┬────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │                                      │
                    ▼                                      ▼
           ┌─────────────────┐                    ┌─────────────────┐
           │   简单任务       │                    │   复杂任务       │
           │   (单应用)       │                    │   (跨应用)       │
           └────────┬────────┘                    └────────┬────────┘
                    │                                      │
                    ▼                                      ▼
           ┌─────────────────┐                    ┌─────────────────┐
           │   端侧执行       │                    │   云端执行       │
           │   MAI-UI-2B/8B  │                    │   MAI-UI-32B+   │
           │   本地推理       │                    │   API 调用      │
           └────────┬────────┘                    └────────┬────────┘
                    │                                      │
                    └──────────────────┬──────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   结果返回       │
                              └─────────────────┘

优势：
- 端侧性能提升 33%
- 云端 API 调用减少 40%+
- 隐私数据本地处理
```

---

## 三、核心模块解析

### 3.1 Navigation Agent (mai_naivigation_agent.py)

这是 MAI-UI 的核心 Agent 类，负责处理截图、生成动作。

#### 3.1.1 类定义

```python
class MAIUINaivigationAgent(BaseAgent):
    """
    Mobile automation agent using vision-language models.
    
    Attributes:
        llm_base_url: Base URL for the LLM API endpoint.
        model_name: Name of the model to use for predictions.
        runtime_conf: Configuration dictionary for runtime parameters.
        history_n: Number of history steps to include in context.
    """
    
    def __init__(
        self,
        llm_base_url: str,
        model_name: str,
        runtime_conf: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,  # MCP 工具
    ):
        # 默认配置
        default_conf = {
            "history_n": 3,      # 历史图像数量
            "temperature": 0.0,  # 采样温度
            "top_k": -1,
            "top_p": 1.0,
            "max_tokens": 2048,
        }
        self.runtime_conf = {**default_conf, **(runtime_conf or {})}
        
        # 初始化 OpenAI 兼容客户端
        self.llm = OpenAI(
            base_url=self.llm_base_url,
            api_key="empty",
        )
```

#### 3.1.2 动态系统提示词

```python
@property
def system_prompt(self) -> str:
    """
    Generate the system prompt based on available MCP tools.
    """
    if self.tools:
        # 有 MCP 工具时，使用带工具的模板
        tools_str = "\n".join(
            [json.dumps(tool, ensure_ascii=False) for tool in self.tools]
        )
        return MAI_MOBILE_SYS_PROMPT_ASK_USER_MCP.render(tools=tools_str)
    # 无工具时，使用基础模板
    return MAI_MOBILE_SYS_PROMPT
```

#### 3.1.3 历史响应格式化

```python
@property
def history_responses(self) -> List[str]:
    """
    Generate formatted history responses for context.
    """
    history_responses = []
    
    for step in self.traj_memory.steps:
        thinking = step.thought
        action_json = copy.deepcopy(step.structured_action.get("action_json", {}))
        
        # 坐标反归一化：[0,1] -> [0, 999]
        if "coordinate" in action_json:
            coordinates = action_json.get("coordinate", [])
            point_x, point_y = coordinates
            action_json["coordinate"] = [
                int(point_x * SCALE_FACTOR),  # SCALE_FACTOR = 999
                int(point_y * SCALE_FACTOR),
            ]
        
        # 构建标准格式
        tool_call_dict = {
            "name": "mobile_use",
            "arguments": action_json,
        }
        tool_call_json = json.dumps(tool_call_dict, separators=(",", ":"))
        history_responses.append(
            f"<thinking>\n{thinking}\n</thinking>\n<tool_call>\n{tool_call_json}\n</tool_call>"
        )
    
    return history_responses
```

#### 3.1.4 输出解析

```python
def parse_action_to_structure_output(text: str) -> Dict[str, Any]:
    """
    Parse model output text into structured action format.
    
    输入示例:
        <thinking>
        I need to click the search button.
        </thinking>
        <tool_call>
        {"name": "mobile_use", "arguments": {"action": "click", "coordinate": [500, 300]}}
        </tool_call>
    
    输出示例:
        {
            "thinking": "I need to click the search button.",
            "action_json": {
                "action": "click",
                "coordinate": [0.5005, 0.3003]  # 归一化后
            }
        }
    """
    results = parse_tagged_text(text)
    thinking = results["thinking"]
    tool_call = results["tool_call"]
    action = tool_call["arguments"]
    
    # 坐标归一化：[0, 999] -> [0, 1]
    if "coordinate" in action:
        coordinates = action["coordinate"]
        if len(coordinates) == 2:
            point_x, point_y = coordinates
        elif len(coordinates) == 4:
            # 支持 bbox 格式
            x1, y1, x2, y2 = coordinates
            point_x = (x1 + x2) / 2
            point_y = (y1 + y2) / 2
        
        point_x = point_x / SCALE_FACTOR
        point_y = point_y / SCALE_FACTOR
        action["coordinate"] = [point_x, point_y]
    
    return {
        "thinking": thinking,
        "action_json": action,
    }
```

---

### 3.2 提示词系统 (prompt.py)

MAI-UI 使用结构化的提示词模板，支持多种场景。

#### 3.2.1 基础导航提示词

```python
MAI_MOBILE_SYS_PROMPT = """You are a GUI agent. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.

## Output Format
For each function call, return the thinking process in <thinking> </thinking> tags, and a json object with function name and arguments within <tool_call></tool_call> XML tags:
```
<thinking>
...
</thinking>
<tool_call>
{"name": "mobile_use", "arguments": <args-json-object>}
</tool_call>
```

## Action Space

{"action": "click", "coordinate": [x, y]}
{"action": "long_press", "coordinate": [x, y]}
{"action": "type", "text": ""}
{"action": "swipe", "direction": "up or down or left or right", "coordinate": [x, y]}
{"action": "open", "text": "app_name"}
{"action": "drag", "start_coordinate": [x1, y1], "end_coordinate": [x2, y2]}
{"action": "system_button", "button": "button_name"} # Options: back, home, menu, enter
{"action": "wait"}
{"action": "terminate", "status": "success or fail"}
{"action": "answer", "text": "xxx"}

## Note
- Write a small plan and finally summarize your next action in <thinking></thinking> part.
- Available Apps: `["Camera","Chrome","Clock","Contacts",...]`.
"""
```

#### 3.2.2 MCP 工具增强提示词

```python
MAI_MOBILE_SYS_PROMPT_ASK_USER_MCP = Template(
    """You are a GUI agent...

## Action Space
...
{"action": "ask_user", "text": "xxx"} # you can ask user for more information
{"action": "double_click", "coordinate": [x, y]}

{% if tools -%}
## MCP Tools
You are also provided with MCP tools, you can use them to complete the task.
{{ tools }}

If you want to use MCP tools, you must output as the following format:
```
<thinking>
...
</thinking>
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>
```
{% endif -%}
...
"""
)
```

#### 3.2.3 Grounding 提示词

```python
MAI_MOBILE_SYS_PROMPT_GROUNDING = """
You are a GUI grounding agent. 
## Task
Given a screenshot and the user's grounding instruction. Your task is to accurately locate a UI element based on the user's instructions.

## Output Format
Return a json object with a reasoning process in <grounding_think></grounding_think> tags, a [x,y] format coordinate within <answer></answer> XML tags:
<grounding_think>...</grounding_think>
<answer>
{"coordinate": [x,y]}
</answer>
"""
```

---

### 3.3 统一记忆结构 (unified_memory.py)

MAI-UI 使用 dataclass 定义类型安全的记忆结构。

#### 3.3.1 轨迹步骤

```python
@dataclass
class TrajStep:
    """
    Represents a single step in an agent's trajectory.
    """
    screenshot: Image.Image           # 截图
    accessibility_tree: Optional[Dict] # 无障碍树
    prediction: str                   # 原始预测
    action: Dict[str, Any]            # 解析后的动作
    conclusion: str                   # 步骤结论
    thought: str                      # 思维过程
    step_index: int                   # 步骤索引
    agent_type: str                   # Agent 类型
    model_name: str                   # 模型名称
    screenshot_bytes: Optional[bytes] = None
    structured_action: Optional[Dict] = None
```

#### 3.3.2 轨迹记忆

```python
@dataclass
class TrajMemory:
    """
    Container for a complete trajectory of agent steps.
    """
    task_goal: str                    # 任务目标
    task_id: str                      # 任务 ID
    steps: List[TrajStep] = field(default_factory=list)
```

---

### 3.4 动作空间

MAI-UI 支持丰富的动作类型：

| 动作类型 | 参数 | 说明 |
|---------|------|------|
| `click` | `coordinate: [x, y]` | 单击指定坐标 |
| `long_press` | `coordinate: [x, y]` | 长按指定坐标 |
| `double_click` | `coordinate: [x, y]` | 双击指定坐标 |
| `type` | `text: str` | 输入文本 |
| `swipe` | `direction: str, coordinate?: [x, y]` | 滑动操作 |
| `drag` | `start_coordinate, end_coordinate` | 拖拽操作 |
| `open` | `text: str` | 打开应用 |
| `system_button` | `button: str` | 系统按钮 |
| `wait` | - | 等待 |
| `terminate` | `status: str` | 终止任务 |
| `answer` | `text: str` | 返回答案 |
| `ask_user` | `text: str` | 询问用户 |

---

## 四、坐标系统

### 4.1 坐标表示

MAI-UI 使用 **999 缩放因子** 的坐标系统：

```python
SCALE_FACTOR = 999

# 模型输出：[0, 999] 范围的整数坐标
# 内部处理：[0, 1] 范围的归一化坐标
# 最终执行：根据屏幕分辨率计算实际像素
```

### 4.2 坐标转换

```python
# 模型输出 -> 归一化
point_x = model_x / SCALE_FACTOR  # 500 -> 0.5005
point_y = model_y / SCALE_FACTOR

# 归一化 -> 模型输出（历史记录）
model_x = int(point_x * SCALE_FACTOR)  # 0.5 -> 499
model_y = int(point_y * SCALE_FACTOR)
```

---

## 五、MCP 工具集成

### 5.1 工具定义格式

```python
tools = [
    {
        "name": "amap_navigation",
        "description": "使用高德地图进行导航规划",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "起点"},
                "destination": {"type": "string", "description": "终点"},
                "mode": {"type": "string", "enum": ["driving", "walking", "transit"]}
            },
            "required": ["origin", "destination"]
        }
    }
]
```

### 5.2 工具调用流程

```
1. 用户指令 -> Agent 分析
2. Agent 决定使用 MCP 工具
3. 输出 <tool_call>{"name": "amap_navigation", "arguments": {...}}</tool_call>
4. 系统执行工具调用
5. 结果返回 Agent
6. Agent 继续任务
```

---

## 六、使用示例

### 6.1 Grounding Agent

```python
from mai_grounding_agent import MAIGroundingAgent

agent = MAIGroundingAgent(
    llm_base_url="http://localhost:8000/v1",
    model_name="MAI-UI-8B",
    runtime_conf={
        "history_n": 3,
        "temperature": 0.0,
        "max_tokens": 2048,
    },
)

# 定位元素
result = agent.ground(
    screenshot=screenshot_image,
    instruction="点击搜索按钮"
)
print(result)  # {"coordinate": [0.5, 0.3]}
```

### 6.2 Navigation Agent

```python
from mai_naivigation_agent import MAIUINaivigationAgent

agent = MAIUINaivigationAgent(
    llm_base_url="http://localhost:8000/v1",
    model_name="MAI-UI-8B",
    runtime_conf={
        "history_n": 3,
        "temperature": 0.0,
    },
    tools=[...]  # 可选 MCP 工具
)

# 执行任务
agent.reset(task_goal="打开微信发送消息给张三", task_id="task_001")
action = agent.step(screenshot_bytes)
print(action)
# {
#     "thinking": "I need to open WeChat app first.",
#     "action_json": {"action": "open", "text": "WeChat"}
# }
```

---

## 七、性能基准

### 7.1 Grounding 评测

| 基准 | MAI-UI-8B | MAI-UI-32B | Gemini-3-Pro |
|-----|-----------|------------|--------------|
| ScreenSpot-Pro | 73.5% | **76.2%** | 71.8% |
| MMBench GUI L2 | 91.3% | **93.1%** | 89.5% |
| OSWorld-G | 70.9% | **72.4%** | 68.3% |
| UI-Vision | 49.2% | **51.8%** | 47.6% |

### 7.2 Navigation 评测

| 基准 | MAI-UI-8B | MAI-UI-32B | UI-TARS-2 |
|-----|-----------|------------|-----------|
| AndroidWorld | 76.7% | **78.3%** | 64.2% |
| MobileWorld | 41.7% | **44.2%** | 38.5% |

### 7.3 在线强化学习

| 配置 | 成功率提升 |
|-----|-----------|
| 并行环境 32→512 | +5.2% |
| 步数预算 15→50 | +4.3% |

---

## 八、总结

MAI-UI 的代码架构体现了以下设计理念：

1. **全尺寸覆盖**：从 2B 到 235B，适配不同算力场景
2. **端云协同**：智能路由，平衡性能与成本
3. **MCP 原生支持**：通过 Jinja2 模板动态注入工具
4. **类型安全**：使用 dataclass 定义数据结构
5. **OpenAI 兼容**：标准化 API 接口，易于集成

代码组织清晰，模块化程度高，是学习 GUI Agent 实现的优秀参考。

---

## 参考文献

1. [MAI-UI Technical Report: Real-World Centric Foundation GUI Agents](https://arxiv.org/abs/2512.22047)
2. [UI-Ins: Enhancing GUI Grounding with Multi-Perspective Instruction-as-Reasoning](https://arxiv.org/abs/2510.20286)
3. [MobileWorld: Benchmarking Autonomous Mobile Agents](https://arxiv.org/abs/2512.19432)
