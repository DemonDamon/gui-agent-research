# GUI-Owl / Mobile-Agent 深度代码解构

> **作者**: Damon Li  
> **更新日期**: 2025年1月  
> **源码仓库**: [X-PLUG/MobileAgent](https://github.com/X-PLUG/MobileAgent)

## 一、项目概览

GUI-Owl 是阿里巴巴通义实验室开发的原生端到端多模态 GUI 智能体，与 Mobile-Agent-v3 框架配合使用。该项目是一个完整的 GUI Agent 系列，包含从 v1 到 v3 的多个版本，以及 GUI-Critic-R1、PC-Agent、UI-S1 等扩展项目。

### 1.1 仓库结构

```
MobileAgent/
├── README.md                    # 英文文档
├── README_zh.md                 # 中文文档
├── LICENSE                      # MIT 许可证
├── assets/                      # 资源文件
├── index.html                   # 项目主页
│
├── Mobile-Agent-v1/             # 第一代单智能体
│   ├── MobileAgent/            # 核心模块
│   │   ├── api.py              # API 接口
│   │   ├── chat.py             # 对话管理
│   │   ├── controller.py       # 设备控制
│   │   ├── crop.py             # 图像裁剪
│   │   ├── icon_localization.py # 图标定位
│   │   ├── prompt.py           # 提示词
│   │   └── text_localization.py # 文本定位
│   └── run.py                  # 运行入口
│
├── Mobile-Agent-v2/             # 第二代多智能体
│   ├── MobileAgent/            # 核心模块
│   └── run.py
│
├── Mobile-Agent-v3/             # 第三代（GUI-Owl）
│   ├── android_world_v3/       # AndroidWorld 评测
│   │   └── android_world/
│   │       └── agents/
│   │           ├── gui_owl.py           # GUI-Owl 实现
│   │           ├── mobile_agent_v3.py   # v3 主逻辑
│   │           ├── mobile_agent_v3_agent.py # 多智能体定义
│   │           ├── infer_ma3.py         # 推理模块
│   │           └── new_json_action.py   # 动作定义
│   ├── os_world_v3/            # OSWorld 评测
│   ├── mobile_v3/              # 移动端部署
│   └── cookbook/               # 使用示例
│
├── Mobile-Agent-E/              # 自进化版本
├── PC-Agent/                    # PC 端版本
├── GUI-Critic-R1/               # 错误诊断模型
└── UI-S1/                       # 半在线强化学习
```

### 1.2 技术栈

| 组件 | 技术选型 | 说明 |
|-----|---------|------|
| 基础模型 | GUI-Owl-7B/32B | 自研多模态模型 |
| 推理框架 | vLLM / HuggingFace | 模型推理 |
| 设备控制 | ADB | Android 设备控制 |
| 图像处理 | PIL / qwen_vl_utils | 图像预处理 |
| 多智能体 | dataclass | 智能体定义 |

---

## 二、核心架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Mobile-Agent-v3 / GUI-Owl 系统架构                    │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   用户指令       │
                              └────────┬────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           多智能体协作框架                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Manager    │  │  Executor   │  │  Notetaker  │  │  Reflector  │    │
│  │  任务规划    │  │  动作执行    │  │  信息记录    │  │  动作反思    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   InfoPool      │
                              │   信息共享池     │
                              └────────┬────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           GUI-Owl 视觉语言模型                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ 视觉感知     │  │ GUI Grounding│  │ 推理规划    │  │ 动作生成    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   ADB 控制器    │
                              │  click/swipe/...│
                              └─────────────────┘
```

### 2.2 版本演进

| 版本 | 特点 | 论文 |
|-----|------|------|
| **v1** | 单智能体，视觉感知 | ICLR 2024 Workshop |
| **v2** | 多智能体协作，导航增强 | NeurIPS 2024 |
| **v3** | GUI-Owl 基座，端到端 | arXiv 2508.15144 |
| **E** | 自进化能力 | arXiv 2501.11733 |

---

## 三、核心模块解析

### 3.1 信息共享池 (InfoPool)

InfoPool 是多智能体协作的核心数据结构：

```python
@dataclass
class InfoPool:
    """Keeping track of all information across the agents."""
    
    # 用户输入 / 累积知识
    instruction: str = ""                    # 用户指令
    task_name: str = ""                      # 任务名称
    additional_knowledge_manager: str = ""   # Manager 额外知识
    additional_knowledge_executor: str = ""  # Executor 额外知识
    add_info_token = "[add_info]"           # 信息占位符
    
    # UI 元素
    ui_elements_list_before: str = ""       # 动作前 UI 元素
    ui_elements_list_after: str = ""        # 动作后 UI 元素
    action_pool: list = field(default_factory=list)
    
    # 工作记忆
    summary_history: list = field(default_factory=list)    # 动作描述历史
    action_history: list = field(default_factory=list)     # 动作历史
    action_outcomes: list = field(default_factory=list)    # 动作结果
    error_descriptions: list = field(default_factory=list) # 错误描述
    
    last_summary: str = ""          # 上一步描述
    last_action: str = ""           # 上一步动作
    last_action_thought: str = ""   # 上一步思考
    important_notes: str = ""       # 重要笔记
    
    # 错误处理
    error_flag_plan: bool = False           # 错误标志
    error_description_plan: bool = False    # 错误描述
    err_to_manager_thresh: int = 2          # 错误上报阈值
    
    # 规划
    plan: str = ""                  # 当前计划
    completed_plan: str = ""        # 已完成计划
    progress_status: str = ""       # 进度状态
    progress_status_history: list = field(default_factory=list)
    finish_thought: str = ""        # 完成思考
    current_subgoal: str = ""       # 当前子目标
    
    # 未来任务
    future_tasks: list = field(default_factory=list)
```

### 3.2 Manager 智能体

Manager 负责任务规划和进度管理：

```python
class Manager(BaseAgent):
    
    def get_prompt(self, info_pool: InfoPool) -> str:
        prompt = "You are an agent who can operate an Android phone on behalf of a user. "
        prompt += "Your goal is to track progress and devise high-level plans.\n\n"
        
        prompt += "### User Request ###\n"
        prompt += f"{info_pool.instruction}\n\n"
        
        if info_pool.plan == "":
            # 首次规划
            prompt += "Make a high-level plan to achieve the user's request. "
            prompt += "If the request is complex, break it down into subgoals.\n"
            prompt += "IMPORTANT: For requests that require an answer, "
            prompt += "always add 'perform the `answer` action' as the last step!\n\n"
            
            prompt += "### Guidelines ###\n"
            prompt += "1. Use the `open_app` action whenever you want to open an app\n"
            prompt += "2. Use search to quickly find a file or entry\n\n"
            
            prompt += "Provide your output in the following format:\n"
            prompt += "### Thought ###\n"
            prompt += "A detailed explanation of your rationale.\n\n"
            prompt += "### Plan ###\n"
            prompt += "1. first subgoal\n"
            prompt += "2. second subgoal\n"
            prompt += "...\n"
        else:
            # 更新规划
            prompt += "### Historical Operations ###\n"
            prompt += f"{info_pool.completed_plan}\n\n"
            prompt += "### Plan ###\n"
            prompt += f"{info_pool.plan}\n\n"
            prompt += f"### Last Action ###\n"
            prompt += f"{info_pool.last_action}\n\n"
            
            # 错误处理
            if info_pool.error_flag_plan:
                prompt += "### Potentially Stuck! ###\n"
                prompt += "You have encountered several failed attempts:\n"
                # 显示最近的错误记录
                
        return prompt
    
    def parse_response(self, response: str) -> dict:
        thought = response.split("### Thought")[-1].split("### Plan")[0].strip()
        plan = response.split("### Plan")[-1].strip()
        return {"thought": thought, "plan": plan}
```

### 3.3 Executor 智能体

Executor 负责具体动作执行：

```python
class Executor(BaseAgent):
    
    def get_prompt(self, info_pool: InfoPool) -> str:
        prompt = "You are an agent who can operate an Android phone.\n\n"
        prompt += "### User Request ###\n"
        prompt += f"{info_pool.instruction}\n\n"
        prompt += "### Plan ###\n"
        prompt += f"{info_pool.plan}\n\n"
        prompt += "### Current Subgoal ###\n"
        prompt += f"{info_pool.current_subgoal}\n\n"
        
        # 动作空间定义
        prompt += "### Action Space ###\n"
        prompt += "- click: Click on an element\n"
        prompt += "- long_press: Long press on an element\n"
        prompt += "- type: Input text\n"
        prompt += "- swipe: Swipe in a direction\n"
        prompt += "- open_app: Open an application\n"
        prompt += "- system_button: Press system button (Home/Back/Enter)\n"
        prompt += "- answer: Answer user's question\n"
        prompt += "- done: Task completed\n\n"
        
        return prompt
```

### 3.4 Notetaker 智能体

Notetaker 负责记录重要信息：

```python
class Notetaker(BaseAgent):
    
    def get_prompt(self, info_pool: InfoPool) -> str:
        prompt = "You are a note-taking agent.\n\n"
        prompt += "### User Request ###\n"
        prompt += f"{info_pool.instruction}\n\n"
        prompt += "### Last Action ###\n"
        prompt += f"{info_pool.last_action}\n\n"
        prompt += "### Last Action Description ###\n"
        prompt += f"{info_pool.last_summary}\n\n"
        
        prompt += "Record any important information from the current screen "
        prompt += "that might be useful for completing the task.\n"
        
        return prompt
```

### 3.5 ActionReflector 智能体

ActionReflector 负责动作反思和错误诊断：

```python
class ActionReflector(BaseAgent):
    
    def get_prompt(self, info_pool: InfoPool) -> str:
        prompt = "You are a reflection agent.\n\n"
        prompt += "### Last Action ###\n"
        prompt += f"{info_pool.last_action}\n\n"
        prompt += "### Expected Outcome ###\n"
        prompt += f"{info_pool.last_summary}\n\n"
        
        prompt += "Compare the before and after screenshots. "
        prompt += "Determine if the action was successful.\n"
        prompt += "If failed, explain why and suggest corrections.\n"
        
        return prompt
```

---

## 四、动作系统

### 4.1 动作类型定义

```python
# new_json_action.py

# 基础动作
CLICK = "click"
LONG_PRESS = "long_press"
INPUT_TEXT = "type"
SWIPE = "swipe"
OPEN_APP = "open_app"
KEYBOARD_ENTER = "keyboard_enter"
NAVIGATE_HOME = "navigate_home"
NAVIGATE_BACK = "navigate_back"
WAIT = "wait"
ANSWER = "answer"
STATUS = "status"

# 目标状态
GOAL_STATUS = "complete"
GOAL_INFEASIBLE = "infeasible"
```

### 4.2 动作转换

```python
def convert_fc_action_to_json_action(dummy_action) -> JSONAction:
    """将模型输出转换为标准动作格式"""
    action_json = json.loads(dummy_action)
    action_type = action_json['action']
    
    x, y, text, direction, goal_status, app_name = None, None, None, None, None, None
    
    if action_type == 'open_app':
        action_type = OPEN_APP
        app_name = action_json['text']
    elif action_type == 'click':
        action_type = CLICK
        x, y = action_json['coordinate'][0], action_json['coordinate'][1]
    elif action_type == 'long_press':
        action_type = LONG_PRESS
        x, y = action_json['coordinate'][0], action_json['coordinate'][1]
    elif action_type == 'type':
        action_type = INPUT_TEXT
        text = action_json['text']
    elif action_type == 'swipe':
        action_type = SWIPE
        start_x, start_y = action_json['coordinate']
        end_x, end_y = action_json['coordinate2']
        direction = [start_x, start_y, end_x, end_y]
    elif action_type == 'system_button':
        button = action_json['button'].lower()
        if button == 'enter':
            action_type = KEYBOARD_ENTER
        elif button == 'back':
            action_type = NAVIGATE_BACK
        elif button == 'home':
            action_type = NAVIGATE_HOME
    elif action_type == 'answer':
        action_type = ANSWER
        text = action_json['text']
    elif action_type in ('done', 'terminate'):
        action_type = STATUS
        goal_status = GOAL_STATUS
    
    return JSONAction(
        action_type=action_type,
        x=x, y=y,
        text=text,
        direction=direction,
        goal_status=goal_status,
        app_name=app_name,
    )
```

### 4.3 动作签名

```python
ATOMIC_ACTION_SIGNITURES_noxml = {
    ANSWER: {
        "description": "Answer user's question",
        "params": {"text": "answer text"}
    },
    CLICK: {
        "description": "Click on an element",
        "params": {"coordinate": "[x, y]"}
    },
    LONG_PRESS: {
        "description": "Long press on an element",
        "params": {"coordinate": "[x, y]"}
    },
    INPUT_TEXT: {
        "description": "Type text into a field",
        "params": {"text": "text to type"}
    },
    SWIPE: {
        "description": "Swipe gesture",
        "params": {
            "coordinate": "[start_x, start_y]",
            "coordinate2": "[end_x, end_y]"
        }
    },
    OPEN_APP: {
        "description": "Open an application",
        "params": {"text": "app name"}
    },
    NAVIGATE_HOME: {
        "description": "Navigate to home screen",
        "params": {}
    },
    NAVIGATE_BACK: {
        "description": "Navigate back",
        "params": {}
    },
    KEYBOARD_ENTER: {
        "description": "Press Enter key",
        "params": {}
    },
    STATUS: {
        "description": "Report task status",
        "params": {"goal_status": "complete/infeasible"}
    },
}
```

---

## 五、执行流程

### 5.1 主循环

```python
class MobileAgentV3_M3A(base_agent.EnvironmentInteractingAgent):
    
    def __init__(self, env, vllm, name='MobileAgentV3_M3A', ...):
        super().__init__(env, name)
        self.vllm = vllm
        
        # 初始化信息池
        self.info_pool = InfoPool(
            additional_knowledge_manager="",
            additional_knowledge_executor=DETAILED_TIPS,
            err_to_manager_thresh=2
        )
        
        # 隐藏自动化 UI
        self.env.hide_automation_ui()
    
    def step(self, goal: str) -> AgentInteractionResult:
        # 初始化智能体
        manager = Manager()
        executor = Executor()
        notetaker = Notetaker()
        action_reflector = ActionReflector()
        
        self.info_pool.instruction = goal
        step_idx = len(self.info_pool.action_history)
        
        # 1. 感知：获取截图
        state = self.get_post_transition_state()
        before_screenshot = state.pixels.copy()
        
        # 2. Manager：任务规划
        if self.should_call_manager():
            manager_prompt = manager.get_prompt(self.info_pool)
            manager_response = self.vllm.call(manager_prompt, before_screenshot)
            parsed = manager.parse_response(manager_response)
            self.info_pool.plan = parsed['plan']
        
        # 3. Executor：动作执行
        executor_prompt = executor.get_prompt(self.info_pool)
        executor_response = self.vllm.call(executor_prompt, before_screenshot)
        action = executor.parse_response(executor_response)
        
        # 4. 执行动作
        json_action = convert_fc_action_to_json_action(action)
        self.execute_action(json_action)
        
        # 5. 获取执行后截图
        after_state = self.get_post_transition_state()
        after_screenshot = after_state.pixels.copy()
        
        # 6. ActionReflector：动作反思
        reflector_prompt = action_reflector.get_prompt(self.info_pool)
        reflection = self.vllm.call(reflector_prompt, 
                                    [before_screenshot, after_screenshot])
        
        # 7. Notetaker：记录信息
        notetaker_prompt = notetaker.get_prompt(self.info_pool)
        notes = self.vllm.call(notetaker_prompt, after_screenshot)
        
        # 8. 更新信息池
        self.update_info_pool(action, reflection, notes)
        
        return result
```

### 5.2 错误处理

```python
def should_call_manager(self):
    """判断是否需要调用 Manager 重新规划"""
    # 首次调用
    if self.info_pool.plan == "":
        return True
    
    # 错误累积超过阈值
    err_count = sum(1 for o in self.info_pool.action_outcomes[-self.info_pool.err_to_manager_thresh:] 
                    if o == "failed")
    if err_count >= self.info_pool.err_to_manager_thresh:
        self.info_pool.error_flag_plan = True
        return True
    
    return False
```

---

## 六、GUI-Owl 模型

### 6.1 模型特点

- **原生端到端**：单模型集成感知、定位、推理、执行
- **跨平台支持**：移动端/桌面/Web 全场景
- **多轮决策**：支持显式中间推理
- **7B/32B 双版本**：平衡性能与效率

### 6.2 模型使用

```python
# 加载模型
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "mPLUG/GUI-Owl-32B",
    trust_remote_code=True,
    torch_dtype=torch.bfloat16
)
tokenizer = AutoTokenizer.from_pretrained("mPLUG/GUI-Owl-32B")

# 推理
messages = [{
    "role": "user",
    "content": [
        {"type": "image", "image": screenshot},
        {"type": "text", "text": instruction}
    ]
}]

response = model.chat(messages, tokenizer)
```

---

## 七、性能基准

### 7.1 AndroidWorld 评测

| 模型 | 成功率 |
|-----|--------|
| **GUI-Owl-32B + v3** | **64.2%** |
| GUI-Owl-7B + v3 | 58.7% |
| GPT-4o | 34.5% |
| Claude 3.5 | 31.2% |

### 7.2 OSWorld 评测

| 模型 | 成功率 |
|-----|--------|
| **GUI-Owl-32B** | **24.6%** |
| GPT-4o | 22.0% |
| Claude 3.7 | 22.0% |

### 7.3 Grounding 评测

| 模型 | ScreenSpot | OSWorld-G |
|-----|------------|-----------|
| **GUI-Owl-32B** | **76.2%** | **72.4%** |
| GUI-Owl-7B | 73.5% | 70.9% |
| GPT-4o | 71.8% | 68.3% |

---

## 八、扩展项目

### 8.1 GUI-Critic-R1

预操作错误诊断模型，在动作执行前预测潜在错误：

```python
# 使用 GUI-Critic-R1 进行错误预测
critic_response = gui_critic.predict(
    screenshot=current_screenshot,
    action=proposed_action
)

if critic_response['error_probability'] > 0.5:
    # 重新规划
    pass
```

### 8.2 UI-S1

半在线强化学习方法，提升 GUI 自动化能力：

- 使用真实环境交互数据
- 半在线训练策略
- 显著提升任务成功率

### 8.3 PC-Agent

PC 端多智能体框架：

- 层次化多智能体协作
- 支持复杂 PC 任务
- ICLR 2025 Workshop 接收

---

## 九、总结

GUI-Owl / Mobile-Agent 的代码架构体现了以下设计理念：

1. **多智能体协作**：Manager、Executor、Notetaker、Reflector 分工明确
2. **信息共享池**：InfoPool 统一管理所有状态信息
3. **端到端模型**：GUI-Owl 单模型完成全部任务
4. **错误处理机制**：自动检测错误并上报 Manager 重新规划
5. **跨平台支持**：移动端、桌面、Web 全场景覆盖

代码组织清晰，扩展性强，是学习多智能体 GUI Agent 实现的优秀参考。

---

## 参考文献

1. [Mobile-Agent-v3: Foundational Agents for GUI Automation](https://arxiv.org/abs/2508.15144)
2. [Mobile-Agent-v2: Mobile Device Operation Assistant with Effective Navigation via Multi-Agent Collaboration](https://arxiv.org/abs/2406.01014)
3. [Mobile-Agent: Autonomous Multi-Modal Mobile Device Agent with Visual Perception](https://arxiv.org/abs/2401.16158)
4. [UI-S1: Advancing GUI Automation via Semi-online Reinforcement Learning](https://arxiv.org/abs/2509.11543)
5. [GUI-Critic-R1: Look Before You Leap](https://arxiv.org/abs/2506.04614)
