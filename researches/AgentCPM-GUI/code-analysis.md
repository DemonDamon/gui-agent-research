# AgentCPM-GUI 深度代码解构

> **作者**: Damon Li  
> **更新日期**: 2025年1月  
> **源码仓库**: [OpenBMB/AgentCPM-GUI](https://github.com/OpenBMB/AgentCPM-GUI)

## 一、项目概览

AgentCPM-GUI 是由清华大学 THUNLP、中国人民大学和 ModelBest 联合开发的端侧 GUI 智能体模型。基于 MiniCPM-V 架构，具有 8B 参数，专注于中英文双语 Android 应用操作。

### 1.1 仓库结构

```
AgentCPM-GUI/
├── README.md                    # 英文文档
├── README_zh.md                 # 中文文档
├── LICENSE                      # Apache 2.0 许可证
├── requirements.txt             # Python 依赖
├── assets/                      # 资源文件
│
├── model/                       # 模型目录
│   └── AgentCPM-GUI/           # 模型权重
│
├── eval/                        # 评估代码
│   ├── eval_data/              # 数据处理
│   │   ├── process_ac.py       # AndroidControl 处理
│   │   ├── process_aitz.py     # AITW 处理
│   │   └── process_odyssey.py  # GUI Odyssey 处理
│   │
│   ├── grounding_eval/         # Grounding 评估
│   │   └── code/               # 各模型评估代码
│   │       ├── minicpm/
│   │       ├── Qwen2.5-VL/
│   │       ├── UI-TARS/
│   │       └── ...
│   │
│   ├── utils/                  # 工具模块
│   │   ├── action_type.py      # 动作类型定义
│   │   ├── action_utils.py     # 动作匹配工具
│   │   └── schema/
│   │       └── schema.json     # 动作 Schema
│   │
│   ├── run_eval_agent.py       # Agent 评估入口
│   └── run_predict_*.py        # 各模型预测脚本
│
├── sft/                         # 监督微调
│   └── readme.md
│
└── rft/                         # 强化微调
    └── readme.md
```

### 1.2 技术栈

| 组件 | 技术选型 | 说明 |
|-----|---------|------|
| 基础模型 | MiniCPM-V 8B | 视觉语言模型基座 |
| 推理框架 | HuggingFace / vLLM | 模型推理 |
| 动作匹配 | JAX | 高效批量计算 |
| 数据格式 | JSON Schema | 结构化输出 |
| 坐标系统 | 0-1000 相对坐标 | 归一化表示 |

---

## 二、核心架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      AgentCPM-GUI 系统架构                               │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   用户指令       │
                              │  (中文/英文)     │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   图像预处理     │
                              │  (resize 1120)  │
                              └────────┬────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MiniCPM-V 8B 模型                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ 视觉编码器   │  │ 语言模型     │  │ RFT 增强    │  │ JSON 输出   │    │
│  │ (Vision)    │  │ (LLM)       │  │ (Reasoning) │  │ (Schema)    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   JSON 输出      │
                              │  {"thought":... │
                              │   "POINT":[x,y]}│
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   动作执行       │
                              │  (ADB 命令)     │
                              └─────────────────┘
```

### 2.2 核心特性

1. **高质量 GUI Grounding**：在大规模双语 Android 数据集上预训练
2. **中文应用适配**：首个针对中文 App 微调的开源 GUI Agent
3. **RFT 增强推理**：强化微调让模型"先思考再行动"
4. **紧凑动作空间**：平均动作长度仅 9.7 tokens

---

## 三、核心模块解析

### 3.1 动作类型定义 (action_type.py)

AgentCPM-GUI 使用枚举类定义所有支持的动作类型：

```python
class ActionType(enum.IntEnum):
    """Integer values for each supported action type in AndroidInTheWild."""
    
    # Agent 动作
    LONG_POINT = 0      # 长按
    NO_ACTION = 1       # 无操作（等待）
    TYPE = 3            # 文本输入
    DUAL_POINT = 4      # 双点手势（点击/滑动）
    PRESS_BACK = 5      # 返回键
    PRESS_HOME = 6      # Home 键
    PRESS_ENTER = 7     # 回车键
    
    # 任务状态
    STATUS_TASK_COMPLETE = 10    # 任务完成
    STATUS_TASK_IMPOSSIBLE = 11  # 任务无法完成
```

### 3.2 动作 Schema (schema.json)

AgentCPM-GUI 使用 JSON Schema 定义结构化输出格式：

```json
{
  "type": "object",
  "description": "执行操作并决定当前任务状态",
  "additionalProperties": false,
  "properties": {
    "thought": {
      "type": "string",
      "description": "智能体的思维过程"
    },
    "POINT": {
      "$ref": "#/$defs/Location",
      "description": "点击屏幕上的指定位置"
    },
    "to": {
      "description": "移动，组合手势参数",
      "oneOf": [
        {
          "enum": ["up", "down", "left", "right"],
          "description": "滑动方向"
        },
        {
          "$ref": "#/$defs/Location",
          "description": "移动到某个位置"
        }
      ]
    },
    "duration": {
      "type": "integer",
      "description": "动作执行的时间或等待时间，毫秒",
      "minimum": 0,
      "default": 200
    },
    "PRESS": {
      "type": "string",
      "description": "触发特殊按键",
      "enum": ["HOME", "BACK", "ENTER"]
    },
    "TYPE": {
      "type": "string",
      "description": "输入文本"
    },
    "STATUS": {
      "type": "string",
      "description": "当前任务的状态",
      "enum": ["continue", "finish", "satisfied", "impossible", "interrupt", "need_feedback"],
      "default": "continue"
    }
  },
  "$defs": {
    "Location": {
      "type": "array",
      "description": "坐标为相对于屏幕左上角的相对位置，缩放到0～1000",
      "items": {
        "type": "integer",
        "minimum": 0,
        "maximum": 1000
      },
      "minItems": 2,
      "maxItems": 2
    }
  }
}
```

### 3.3 动作空间

| 动作 | 必需字段 | 可选字段 | 说明 | 示例 |
|-----|---------|---------|------|------|
| **Click** | `POINT:[x,y]` | `duration`, `thought`, `STATUS` | 单击 | `{"POINT":[480,320]}` |
| **Long Press** | `POINT:[x,y]`, `duration:1000` | `thought`, `STATUS` | 长按 | `{"POINT":[480,320],"duration":1000}` |
| **Swipe** | `POINT:[x,y]`, `to:方向/坐标` | `duration`, `thought`, `STATUS` | 滑动 | `{"POINT":[500,200],"to":"down"}` |
| **Press Key** | `PRESS:"HOME/BACK/ENTER"` | `duration`, `thought`, `STATUS` | 按键 | `{"PRESS":"HOME"}` |
| **Type Text** | `TYPE:"<text>"` | `duration`, `thought`, `STATUS` | 输入 | `{"TYPE":"Hello!"}` |
| **Wait** | `duration` | `thought`, `STATUS` | 等待 | `{"duration":500}` |
| **Status** | `STATUS:状态` | `duration`, `thought` | 状态 | `{"STATUS":"finish"}` |

### 3.4 动作匹配算法 (action_utils.py)

AgentCPM-GUI 使用 JAX 实现高效的动作匹配算法：

#### 3.4.1 点击判定

```python
_SWIPE_DISTANCE_THRESHOLD = 0.04  # 滑动距离阈值

def is_tap_action(normalized_start_yx, normalized_end_yx):
    """判断是点击还是滑动"""
    distance = jnp.linalg.norm(
        jnp.array(normalized_start_yx) - jnp.array(normalized_end_yx)
    )
    return distance <= _SWIPE_DISTANCE_THRESHOLD
```

#### 3.4.2 边界框检测

```python
def _yx_in_bounding_boxes(yx, bounding_boxes):
    """检查点是否在边界框内"""
    y, x = yx
    top, left, height, width = [
        jnp.squeeze(v, axis=-1) 
        for v in jnp.split(bounding_boxes, 4, axis=-1)
    ]
    bottom, right = top + height, left + width
    
    return (jnp.logical_and(y >= top, y <= bottom) & 
            jnp.logical_and(x >= left, x <= right))
```

#### 3.4.3 点击匹配

```python
_TAP_DISTANCE_THRESHOLD = 0.14  # 点击距离阈值
ANNOTATION_WIDTH_AUGMENT_FRACTION = 1.4   # 边界框宽度扩展
ANNOTATION_HEIGHT_AUGMENT_FRACTION = 1.4  # 边界框高度扩展

def _check_tap_actions_match(tap_1_yx, tap_2_yx, annotation_positions, ...):
    """判断两个点击动作是否匹配"""
    # 扩展边界框
    resized_annotation_positions = _resize_annotation_bounding_boxes(
        annotation_positions,
        annotation_width_augment_fraction,
        annotation_height_augment_fraction,
    )
    
    # 检查是否在同一边界框内
    tap1_in_box = _yx_in_bounding_boxes(tap_1_yx, resized_annotation_positions)
    tap2_in_box = _yx_in_bounding_boxes(tap_2_yx, resized_annotation_positions)
    both_in_box = jnp.max(tap1_in_box & tap2_in_box)
    
    # 如果不在同一边界框，检查欧氏距离
    within_threshold = (
        jnp.linalg.norm(jnp.array(tap_1_yx) - jnp.array(tap_2_yx))
        <= matching_tap_distance_threshold_screen_percentage
    )
    
    return jnp.logical_or(both_in_box, within_threshold)
```

#### 3.4.4 滑动匹配

```python
def _check_drag_actions_match(
    drag_1_touch_yx, drag_1_lift_yx,
    drag_2_touch_yx, drag_2_lift_yx,
):
    """判断两个滑动动作是否匹配（主轴方向相同）"""
    # 计算滑动方向
    drag_1_deltas = drag_1_lift_yx - drag_1_touch_yx
    drag_1_main_axis = np.argmax(jnp.abs(drag_1_deltas))
    
    drag_2_deltas = drag_2_lift_yx - drag_2_touch_yx
    drag_2_main_axis = np.argmax(jnp.abs(drag_2_deltas))
    
    return jnp.equal(drag_1_main_axis, drag_2_main_axis)
```

---

## 四、推理流程

### 4.1 图像预处理

```python
def __resize__(origin_img):
    """将图像长边缩放到 1120px"""
    resolution = origin_img.size
    w, h = resolution
    max_line_res = 1120
    
    if h > max_line_res:
        w = int(w * max_line_res / h)
        h = max_line_res
    if w > max_line_res:
        h = int(h * max_line_res / w)
        w = max_line_res
    
    img = origin_img.resize((w, h), resample=Image.Resampling.LANCZOS)
    return img
```

### 4.2 消息构建

```python
# 构建消息格式
messages = [{
    "role": "user",
    "content": [
        f"<Question>{instruction}</Question>\n当前屏幕截图：",
        image
    ]
}]
```

### 4.3 系统提示词

```python
ACTION_SCHEMA = json.load(open('eval/utils/schema/schema.json'))
# 启用思维过程
items = list(ACTION_SCHEMA.items())
items.insert(3, ("required", ["thought"]))
ACTION_SCHEMA = dict(items)

SYSTEM_PROMPT = f'''# Role
你是一名熟悉安卓系统触屏GUI操作的智能体，将根据用户的问题，分析当前界面的GUI元素和布局，生成相应的操作。

# Task
针对用户问题，根据输入的当前屏幕截图，输出下一步的操作。

# Rule
- 以紧凑JSON格式输出
- 输出操作必须遵循Schema约束

# Schema
{json.dumps(ACTION_SCHEMA, indent=None, ensure_ascii=False, separators=(',', ':'))}'''
```

### 4.4 模型推理

```python
outputs = model.chat(
    image=None,
    msgs=messages,
    system_prompt=SYSTEM_PROMPT,
    tokenizer=tokenizer,
    temperature=0.1,
    top_p=0.3,
    n=1,
)

# 输出示例
# {"thought":"任务目标是点击'会员'按钮。当前界面显示了应用的推荐页面...","POINT":[729,69]}
```

---

## 五、坐标系统

### 5.1 坐标表示

AgentCPM-GUI 使用 **0-1000 相对坐标系统**：

```python
# 绝对坐标 -> 相对坐标
rel_x = int(abs_x / width * 1000)
rel_y = int(abs_y / height * 1000)

# 相对坐标 -> 绝对坐标
abs_x = int(rel_x / 1000 * width)
abs_y = int(rel_y / 1000 * height)
```

### 5.2 坐标原点

- 原点：屏幕左上角
- X 轴：向右为正
- Y 轴：向下为正
- 范围：[0, 1000]

---

## 六、训练方法

### 6.1 监督微调 (SFT)

- 在大规模双语 Android 数据集上预训练
- 覆盖 30+ 热门中文应用
- 提升 GUI 元素定位和理解能力

### 6.2 强化微调 (RFT)

- 让模型"先思考再行动"
- 显著提升复杂任务成功率
- 增强规划和推理能力

---

## 七、性能基准

### 7.1 Grounding 评测

| 模型 | Fun2Point | Text2Point | Bbox2text | 平均 |
|-----|-----------|------------|-----------|------|
| **AgentCPM-GUI-8B** | **79.1** | **76.5** | **58.2** | **71.3** |
| Qwen2.5-VL-7B | 59.8 | 59.3 | 50.0 | 56.4 |
| UI-TARS-7B | 56.8 | 66.7 | 1.4 | 41.6 |
| GPT-4o | 22.1 | 19.9 | 14.3 | 18.8 |

### 7.2 Agent 评测

| 模型 | CAGUI | AndroidControl | GUI Odyssey |
|-----|-------|----------------|-------------|
| **AgentCPM-GUI-8B** | **91.3** | **85.7** | **78.4** |
| Qwen2.5-VL-7B | 82.1 | 76.3 | 69.2 |
| UI-TARS-7B | 79.5 | 73.8 | 65.7 |

---

## 八、使用示例

### 8.1 HuggingFace 推理

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from PIL import Image
import json

# 加载模型
model_path = "model/AgentCPM-GUI"
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_path, 
    trust_remote_code=True, 
    torch_dtype=torch.bfloat16
)
model = model.to("cuda:0")

# 构建输入
instruction = "请点击屏幕上的'会员'按钮"
image = Image.open("assets/test.jpeg").convert("RGB")
image = __resize__(image)

# 推理
messages = [{
    "role": "user",
    "content": [f"<Question>{instruction}</Question>\n当前屏幕截图：", image]
}]

outputs = model.chat(
    image=None,
    msgs=messages,
    system_prompt=SYSTEM_PROMPT,
    tokenizer=tokenizer,
    temperature=0.1,
    top_p=0.3,
)

print(outputs)
# {"thought":"任务目标是点击'会员'按钮...","POINT":[729,69]}
```

### 8.2 vLLM 推理

```bash
# 启动服务
vllm serve model/AgentCPM-GUI \
    --served-model-name AgentCPM-GUI \
    --tensor_parallel_size 1 \
    --trust-remote-code \
    --limit-mm-per-prompt image=10
```

```python
import requests
import base64

# 调用 API
payload = {
    "model": "AgentCPM-GUI",
    "temperature": 0.1,
    "messages": messages,
    "max_tokens": 2048,
}

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={"Content-Type": "application/json"},
    json=payload
)

result = response.json()["choices"][0]["message"]["content"]
```

---

## 九、总结

AgentCPM-GUI 的代码架构体现了以下设计理念：

1. **紧凑高效**：平均动作长度仅 9.7 tokens，适合端侧部署
2. **结构化输出**：使用 JSON Schema 确保输出格式规范
3. **双语支持**：首个针对中文应用微调的开源 GUI Agent
4. **RFT 增强**：通过强化微调提升推理能力
5. **JAX 加速**：使用 JAX 实现高效的动作匹配算法

代码组织清晰，评估框架完善，是学习 GUI Agent 实现的优秀参考。

---

## 参考文献

1. [AgentCPM-GUI Technical Report](https://arxiv.org/abs/2506.01391)
2. [MiniCPM-V: A GPT-4V Level MLLM on Your Phone](https://github.com/OpenBMB/MiniCPM-V)
3. [Android in the Wild: A Large-Scale Dataset for Android Device Control](https://arxiv.org/abs/2307.10088)
