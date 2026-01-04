# Step-GUIEdge 深度代码解构

> **作者**: Damon Li  
> **更新日期**: 2025年1月  
> **源码仓库**: [stepfun-ai/gelab-zero](https://github.com/stepfun-ai/gelab-zero)

## 一、项目概览

Step-GUIEdge（原名 GELab-Zero）是阶跃星辰开发的业内首个支持手机部署的开源端侧 GUI Agent 模型。该模型基于 Qwen3-VL-4B-Instruct，支持本地部署和隐私保护，是 Step-GUI 系列的端侧版本。

### 1.1 命名演进

| 时间 | 名称 | 说明 |
|-----|------|------|
| 2025.11 | GELab-Zero-4B | 首个开源版本 |
| 2025.12 | Step-GUI Edge | 正式命名，升级为 4B/8B 双版本 |

### 1.2 仓库结构

```
gelab-zero/
├── README.md                    # 项目文档
├── LICENSE                      # MIT 许可证
├── requirements.txt             # Python 依赖
│
├── copilot_agent_client/        # Agent 客户端
│   ├── mcp_agent_loop.py       # MCP Agent 主循环
│   └── ...
│
├── copilot_front_end/           # 前端执行器
│   ├── pu_frontend_executor.py # PU 前端执行器
│   └── ...
│
├── copilot_tools/               # 工具模块
│   ├── base_parser.py          # 动作解析器
│   └── ...
│
├── mcp_server/                  # MCP 服务器
│   ├── simple_gelab_mcp_server.py # 简单 MCP 服务器
│   └── ...
│
├── models/                      # 模型相关
│   └── ...
│
└── scripts/                     # 脚本
    └── ...
```

### 1.3 技术栈

| 组件 | 技术选型 | 说明 |
|-----|---------|------|
| 基础模型 | Qwen3-VL-4B/8B | 视觉语言模型基座 |
| 协议 | GUI-MCP | 首个 GUI Agent MCP 协议 |
| 推理框架 | vLLM / HuggingFace | 模型推理 |
| 部署 | 端侧/云端 | 支持手机本地部署 |

---

## 二、核心架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Step-GUIEdge 系统架构                               │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   用户指令       │
                              └────────┬────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MCP Agent Loop                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ 任务解析     │  │ 截图获取     │  │ 模型推理     │  │ 动作执行     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         GUI-MCP 协议层                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ 工具注册     │  │ 动作定义     │  │ 状态管理     │  │ 错误处理     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Step-GUIEdge 4B/8B 模型                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ 视觉编码器   │  │ UI 理解     │  │ 动作生成     │  │ 坐标预测     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   设备执行层     │
                              │  ADB / 本地API  │
                              └─────────────────┘
```

### 2.2 端云协同架构

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
           │  Step-GUI Edge  │                    │   Step-GUI      │
           │   端侧 4B/8B    │                    │   云端大模型     │
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
- 端侧部署：隐私数据本地处理
- 10分钟部署：GUI-MCP 协议快速集成
- 200+ App 适配：广泛的应用支持
```

---

## 三、核心模块解析

### 3.1 MCP Agent Loop (mcp_agent_loop.py)

MCP Agent Loop 是 Step-GUIEdge 的核心执行循环：

```python
class MCPAgentLoop:
    """MCP Agent 主循环"""
    
    def __init__(self, model_client, mcp_server, config):
        self.model_client = model_client
        self.mcp_server = mcp_server
        self.config = config
        self.history = []
        
    async def run(self, task: str):
        """执行任务主循环"""
        self.history = []
        
        while True:
            # 1. 获取当前截图
            screenshot = await self.mcp_server.get_screenshot()
            
            # 2. 构建提示词
            prompt = self.build_prompt(task, screenshot)
            
            # 3. 模型推理
            response = await self.model_client.generate(prompt, screenshot)
            
            # 4. 解析动作
            action = self.parse_action(response)
            
            # 5. 检查是否完成
            if action['type'] == 'finish':
                return action.get('result', 'Task completed')
            
            # 6. 执行动作
            result = await self.mcp_server.execute_action(action)
            
            # 7. 更新历史
            self.history.append({
                'action': action,
                'result': result,
                'screenshot': screenshot
            })
            
            # 8. 等待屏幕稳定
            await asyncio.sleep(self.config.get('wait_time', 1.0))
    
    def build_prompt(self, task: str, screenshot) -> str:
        """构建提示词"""
        prompt = f"Task: {task}\n\n"
        
        if self.history:
            prompt += "History:\n"
            for i, h in enumerate(self.history[-5:]):  # 最近5步
                prompt += f"Step {i+1}: {h['action']}\n"
        
        prompt += "\nBased on the current screenshot, what action should be taken next?"
        
        return prompt
```

### 3.2 动作解析器 (base_parser.py)

```python
class BaseActionParser:
    """动作解析基类"""
    
    # 支持的动作类型
    ACTION_TYPES = [
        'click',        # 点击
        'long_press',   # 长按
        'swipe',        # 滑动
        'type',         # 输入文本
        'scroll',       # 滚动
        'back',         # 返回
        'home',         # 主页
        'finish',       # 完成
    ]
    
    def parse(self, response: str) -> dict:
        """解析模型输出为动作字典"""
        # 尝试 JSON 解析
        try:
            action = json.loads(response)
            return self.validate_action(action)
        except json.JSONDecodeError:
            pass
        
        # 尝试正则解析
        return self.parse_with_regex(response)
    
    def parse_with_regex(self, response: str) -> dict:
        """使用正则表达式解析"""
        # 解析动作类型
        action_match = re.search(r'action[:\s]+(\w+)', response, re.I)
        if not action_match:
            raise ValueError("Cannot parse action type")
        
        action_type = action_match.group(1).lower()
        
        # 解析坐标
        coord_match = re.search(r'\[(\d+),\s*(\d+)\]', response)
        if coord_match:
            x, y = int(coord_match.group(1)), int(coord_match.group(2))
        else:
            x, y = None, None
        
        # 解析文本
        text_match = re.search(r'text[:\s]+"([^"]+)"', response, re.I)
        text = text_match.group(1) if text_match else None
        
        return {
            'type': action_type,
            'x': x,
            'y': y,
            'text': text
        }
    
    def validate_action(self, action: dict) -> dict:
        """验证动作格式"""
        if action.get('type') not in self.ACTION_TYPES:
            raise ValueError(f"Unknown action type: {action.get('type')}")
        
        # 验证坐标范围
        if action.get('x') is not None:
            action['x'] = max(0, min(1000, action['x']))
        if action.get('y') is not None:
            action['y'] = max(0, min(1000, action['y']))
        
        return action
```

### 3.3 前端执行器 (pu_frontend_executor.py)

```python
class PUFrontendExecutor:
    """PU 前端执行器"""
    
    def __init__(self, device_id=None):
        self.device_id = device_id
        self.adb = ADBController(device_id)
        
    async def execute(self, action: dict) -> dict:
        """执行动作"""
        action_type = action['type']
        
        if action_type == 'click':
            return await self.click(action['x'], action['y'])
        elif action_type == 'long_press':
            return await self.long_press(action['x'], action['y'])
        elif action_type == 'swipe':
            return await self.swipe(
                action['start_x'], action['start_y'],
                action['end_x'], action['end_y']
            )
        elif action_type == 'type':
            return await self.type_text(action['text'])
        elif action_type == 'scroll':
            return await self.scroll(action['direction'])
        elif action_type == 'back':
            return await self.press_back()
        elif action_type == 'home':
            return await self.press_home()
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    async def click(self, x: int, y: int) -> dict:
        """点击操作"""
        # 坐标转换：0-1000 -> 实际像素
        screen_width, screen_height = await self.get_screen_size()
        abs_x = int(x / 1000 * screen_width)
        abs_y = int(y / 1000 * screen_height)
        
        await self.adb.tap(abs_x, abs_y)
        return {'success': True, 'action': 'click', 'x': abs_x, 'y': abs_y}
    
    async def long_press(self, x: int, y: int, duration: int = 1000) -> dict:
        """长按操作"""
        screen_width, screen_height = await self.get_screen_size()
        abs_x = int(x / 1000 * screen_width)
        abs_y = int(y / 1000 * screen_height)
        
        await self.adb.long_press(abs_x, abs_y, duration)
        return {'success': True, 'action': 'long_press'}
    
    async def swipe(self, start_x, start_y, end_x, end_y, duration=300) -> dict:
        """滑动操作"""
        screen_width, screen_height = await self.get_screen_size()
        
        abs_start_x = int(start_x / 1000 * screen_width)
        abs_start_y = int(start_y / 1000 * screen_height)
        abs_end_x = int(end_x / 1000 * screen_width)
        abs_end_y = int(end_y / 1000 * screen_height)
        
        await self.adb.swipe(abs_start_x, abs_start_y, abs_end_x, abs_end_y, duration)
        return {'success': True, 'action': 'swipe'}
    
    async def type_text(self, text: str) -> dict:
        """输入文本"""
        await self.adb.input_text(text)
        return {'success': True, 'action': 'type', 'text': text}
    
    async def scroll(self, direction: str) -> dict:
        """滚动操作"""
        screen_width, screen_height = await self.get_screen_size()
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        if direction == 'up':
            await self.adb.swipe(center_x, center_y + 300, center_x, center_y - 300)
        elif direction == 'down':
            await self.adb.swipe(center_x, center_y - 300, center_x, center_y + 300)
        elif direction == 'left':
            await self.adb.swipe(center_x + 300, center_y, center_x - 300, center_y)
        elif direction == 'right':
            await self.adb.swipe(center_x - 300, center_y, center_x + 300, center_y)
        
        return {'success': True, 'action': 'scroll', 'direction': direction}
```

### 3.4 MCP 服务器 (simple_gelab_mcp_server.py)

```python
class SimpleGELabMCPServer:
    """简单的 GELab MCP 服务器"""
    
    def __init__(self, executor):
        self.executor = executor
        self.tools = self.register_tools()
    
    def register_tools(self) -> list:
        """注册 MCP 工具"""
        return [
            {
                "name": "click",
                "description": "Click on a specific position on the screen",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X coordinate (0-1000)"},
                        "y": {"type": "integer", "description": "Y coordinate (0-1000)"}
                    },
                    "required": ["x", "y"]
                }
            },
            {
                "name": "long_press",
                "description": "Long press on a specific position",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"},
                        "duration": {"type": "integer", "default": 1000}
                    },
                    "required": ["x", "y"]
                }
            },
            {
                "name": "swipe",
                "description": "Swipe from one position to another",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_x": {"type": "integer"},
                        "start_y": {"type": "integer"},
                        "end_x": {"type": "integer"},
                        "end_y": {"type": "integer"}
                    },
                    "required": ["start_x", "start_y", "end_x", "end_y"]
                }
            },
            {
                "name": "type",
                "description": "Type text into the current input field",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "scroll",
                "description": "Scroll the screen in a direction",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down", "left", "right"]
                        }
                    },
                    "required": ["direction"]
                }
            },
            {
                "name": "back",
                "description": "Press the back button",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "home",
                "description": "Press the home button",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "get_screenshot",
                "description": "Get the current screenshot",
                "parameters": {"type": "object", "properties": {}}
            }
        ]
    
    async def execute_action(self, action: dict) -> dict:
        """执行动作"""
        return await self.executor.execute(action)
    
    async def get_screenshot(self):
        """获取截图"""
        return await self.executor.adb.screenshot()
```

---

## 四、GUI-MCP 协议

### 4.1 协议概述

GUI-MCP 是阶跃星辰推出的首个面向 GUI Agent 的 MCP（Model Context Protocol）协议，旨在标准化 GUI Agent 与设备的交互接口。

### 4.2 协议特点

1. **标准化接口**：统一的工具定义和调用格式
2. **快速部署**：10分钟完成 AI 手机部署
3. **跨平台支持**：Android / iOS / Desktop
4. **隐私保护**：端侧处理，数据不出设备

### 4.3 工具定义格式

```json
{
  "name": "click",
  "description": "Click on a specific position on the screen",
  "parameters": {
    "type": "object",
    "properties": {
      "x": {
        "type": "integer",
        "description": "X coordinate (0-1000)",
        "minimum": 0,
        "maximum": 1000
      },
      "y": {
        "type": "integer",
        "description": "Y coordinate (0-1000)",
        "minimum": 0,
        "maximum": 1000
      }
    },
    "required": ["x", "y"]
  }
}
```

---

## 五、坐标系统

### 5.1 坐标表示

Step-GUIEdge 使用 **0-1000 相对坐标系统**：

```python
# 相对坐标 -> 绝对坐标
abs_x = int(rel_x / 1000 * screen_width)
abs_y = int(rel_y / 1000 * screen_height)

# 绝对坐标 -> 相对坐标
rel_x = int(abs_x / screen_width * 1000)
rel_y = int(abs_y / screen_height * 1000)
```

### 5.2 坐标原点

- 原点：屏幕左上角
- X 轴：向右为正
- Y 轴：向下为正
- 范围：[0, 1000]

---

## 六、模型版本

### 6.1 Step-GUI Edge 4B

- **基座模型**：Qwen3-VL-4B-Instruct
- **参数量**：4B
- **特点**：轻量级，支持手机端侧部署
- **适用场景**：简单任务，隐私敏感场景

### 6.2 Step-GUI Edge 8B

- **基座模型**：Qwen3-VL-8B-Instruct
- **参数量**：8B
- **特点**：更强的理解和推理能力
- **适用场景**：复杂任务，需要更高准确率

---

## 七、性能基准

### 7.1 Grounding 评测

| 模型 | ScreenSpot | OSWorld-G |
|-----|------------|-----------|
| **Step-GUI Edge 8B** | **75.8%** | **71.2%** |
| Step-GUI Edge 4B | 72.3% | 68.5% |
| GELab-Zero-4B | 71.5% | 67.8% |

### 7.2 Agent 评测

| 模型 | AndroidControl | GUI Odyssey |
|-----|----------------|-------------|
| **Step-GUI Edge 8B** | **88.2%** | **85.3%** |
| Step-GUI Edge 4B | 85.6% | 82.1% |
| GELab-Zero-4B | 84.2% | 80.5% |

### 7.3 端侧性能

| 指标 | Step-GUI Edge 4B | Step-GUI Edge 8B |
|-----|------------------|------------------|
| 推理延迟 | ~200ms | ~400ms |
| 内存占用 | ~4GB | ~8GB |
| 首 token 延迟 | ~100ms | ~200ms |

---

## 八、使用示例

### 8.1 快速开始

```python
from gelab_zero import MCPAgentLoop, SimpleGELabMCPServer, PUFrontendExecutor

# 初始化执行器
executor = PUFrontendExecutor(device_id="your_device_id")

# 初始化 MCP 服务器
mcp_server = SimpleGELabMCPServer(executor)

# 初始化模型客户端
model_client = ModelClient(
    model_name="Step-GUI-Edge-4B",
    base_url="http://localhost:8000/v1"
)

# 初始化 Agent Loop
agent = MCPAgentLoop(model_client, mcp_server, config={
    'wait_time': 1.0,
    'max_steps': 50
})

# 执行任务
result = await agent.run("打开微信，发送消息给张三")
print(result)
```

### 8.2 vLLM 部署

```bash
# 启动 vLLM 服务
vllm serve stepfun-ai/Step-GUI-Edge-4B \
    --served-model-name Step-GUI-Edge-4B \
    --tensor_parallel_size 1 \
    --trust-remote-code \
    --max_model_len 4096
```

### 8.3 手机端侧部署

```bash
# 1. 安装依赖
pip install gelab-zero

# 2. 配置设备
adb connect your_device_ip:5555

# 3. 启动服务
python -m gelab_zero.server --device your_device_id --port 8080

# 4. 调用 API
curl -X POST http://localhost:8080/run \
    -H "Content-Type: application/json" \
    -d '{"task": "打开设置，开启蓝牙"}'
```

---

## 九、与 GELab-Zero 的关系

Step-GUIEdge 是 GELab-Zero 的升级版本：

| 特性 | GELab-Zero | Step-GUIEdge |
|-----|------------|--------------|
| 模型版本 | 4B | 4B / 8B |
| MCP 协议 | 基础版 | GUI-MCP 完整版 |
| 部署方式 | 本地 | 端侧 + 云端 |
| App 适配 | 100+ | 200+ |
| 性能优化 | 基础 | 深度优化 |

---

## 十、总结

Step-GUIEdge 的代码架构体现了以下设计理念：

1. **端侧优先**：业内首个支持手机部署的开源端侧模型
2. **GUI-MCP 协议**：标准化的 GUI Agent 交互协议
3. **隐私保护**：本地运行，数据不出设备
4. **快速部署**：10分钟完成 AI 手机部署
5. **广泛适配**：200+ App 场景支持

代码组织清晰，协议设计规范，是学习端侧 GUI Agent 实现的优秀参考。

---

## 参考文献

1. [STEP-GUI: The top GUI agent solution in the galaxy](https://github.com/stepfun-ai/gelab-zero)
2. [阶跃星辰发布全新AI Agent系列模型Step-GUI](https://m.36kr.com/newsflashes/3599560321155328)
3. [GELab-Zero: A SOTA open-source GUI Agent](https://huggingface.co/stepfun-ai/GELab-Zero-4B-preview)
