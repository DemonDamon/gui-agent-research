# UI-TARS 深度代码解构

> **作者**: Damon Li  
> **更新日期**: 2025年1月  
> **源码仓库**: [bytedance/UI-TARS](https://github.com/bytedance/UI-TARS)

## 一、项目概览

UI-TARS 是字节跳动 Seed 团队开发的原生 GUI 智能体模型，能够直接从屏幕截图感知信息并执行类人操作（如键盘和鼠标操作）。本文档将深入解析其开源代码的架构设计和核心实现。

### 1.1 仓库结构

```
UI-TARS/
├── README.md                    # 项目主文档
├── README_deploy.md             # 部署指南
├── README_coordinates.md        # 坐标处理指南
├── README_v1.md                 # V1版本文档
├── UI_TARS_paper.pdf           # 论文PDF
├── codes/                       # 核心代码目录
│   ├── ui_tars/                # 主要模块
│   │   ├── __init__.py
│   │   ├── action_parser.py    # 动作解析器（核心）
│   │   └── prompt.py           # 提示词模板
│   └── tests/                  # 测试用例
│       ├── action_parser_test.py
│       └── inference_test.py
├── data/                        # 数据目录
└── figures/                     # 图片资源
```

### 1.2 技术栈

| 组件 | 技术选型 | 说明 |
|-----|---------|------|
| 基础模型 | Qwen2.5-VL | 视觉语言模型基座 |
| 推理框架 | HuggingFace Transformers | 模型加载与推理 |
| GUI 自动化 | PyAutoGUI | 跨平台 GUI 控制 |
| 剪贴板 | pyperclip | 文本输入优化 |
| 坐标系统 | 绝对坐标 (1000x1000) | 标准化坐标表示 |

---

## 二、核心模块解析

### 2.1 动作解析器 (action_parser.py)

动作解析器是 UI-TARS 的核心组件，负责将模型输出的自然语言动作转换为可执行的 GUI 操作代码。

#### 2.1.1 模块常量定义

```python
IMAGE_FACTOR = 28          # 图像缩放因子
MIN_PIXELS = 100 * 28 * 28 # 最小像素数 (78,400)
MAX_PIXELS = 16384 * 28 * 28 # 最大像素数 (12,845,056)
MAX_RATIO = 200            # 最大宽高比
```

这些常量用于控制图像预处理的边界条件，确保输入图像在合理的尺寸范围内。

#### 2.1.2 坐标转换函数

```python
def convert_point_to_coordinates(text, is_answer=False):
    """
    将 <point>x y</point> 格式转换为 (x, y) 格式
    
    输入: "<point>100 200</point>"
    输出: "(100,200)"
    """
    pattern = r"<point>(\d+)\s+(\d+)</point>"
    # ... 正则匹配和替换逻辑
```

该函数处理模型输出中的点坐标标记，将其转换为标准的元组格式。

#### 2.1.3 智能图像缩放 (smart_resize)

```python
def smart_resize(height: int, width: int, factor: int = IMAGE_FACTOR,
                 min_pixels: int = MIN_PIXELS, max_pixels: int = MAX_PIXELS) -> tuple[int, int]:
    """
    智能缩放图像，满足以下条件：
    1. 高度和宽度都能被 factor 整除
    2. 总像素数在 [min_pixels, max_pixels] 范围内
    3. 尽可能保持原始宽高比
    """
```

这是 Qwen2.5-VL 模型特有的图像预处理要求，确保输入图像符合模型的尺寸约束。

#### 2.1.4 动作解析主函数

```python
def parse_action_to_structure_output(text, factor, origin_resized_height, 
                                     origin_resized_width, model_type="qwen25vl"):
    """
    将模型输出解析为结构化的动作字典
    
    输入示例:
        "Thought: Click the button\nAction: click(start_box='(100,200)')"
    
    输出示例:
        [{
            "reflection": None,
            "thought": "Click the button",
            "action_type": "click",
            "action_inputs": {"start_box": "[0.1, 0.2, 0.1, 0.2]"},
            "text": "..."
        }]
    """
```

**核心处理流程**：

1. **预处理**：统一坐标格式（`start_point` → `start_box`）
2. **思维提取**：使用正则表达式提取 `Thought` 和 `Reflection` 内容
3. **动作解析**：使用 Python AST 解析动作函数调用
4. **坐标转换**：将绝对坐标转换为相对坐标（0-1范围）

#### 2.1.5 PyAutoGUI 代码生成

```python
def parsing_response_to_pyautogui_code(responses, image_height: int, 
                                       image_width: int, input_swap: bool = True) -> str:
    """
    将解析后的动作转换为可执行的 PyAutoGUI 代码
    
    支持的动作类型：
    - hotkey: 组合键操作
    - press/keydown/keyup: 单键操作
    - type: 文本输入（支持剪贴板优化）
    - drag/select: 拖拽操作
    - scroll: 滚动操作
    - click/left_double/right_single/hover: 鼠标点击
    - finished: 任务完成标记
    """
```

**文本输入优化**：

```python
if input_swap:
    # 使用剪贴板方式输入（更快、更可靠）
    pyautogui_code += f"\nimport pyperclip"
    pyautogui_code += f"\npyperclip.copy('{stripped_content}')"
    pyautogui_code += f"\npyautogui.hotkey('ctrl', 'v')"
else:
    # 逐字符输入（兼容性更好）
    pyautogui_code += f"\npyautogui.write('{stripped_content}', interval=0.1)"
```

---

### 2.2 提示词模板 (prompt.py)

UI-TARS 提供三种针对不同场景的提示词模板：

#### 2.2.1 桌面端模板 (COMPUTER_USE)

```python
COMPUTER_USE_DOUBAO = """You are a GUI agent. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.

## Output Format
```
Thought: ...
Action: ...
```

## Action Space
click(point='<point>x1 y1</point>')
left_double(point='<point>x1 y1</point>')
right_single(point='<point>x1 y1</point>')
drag(start_point='<point>x1 y1</point>', end_point='<point>x2 y2</point>')
hotkey(key='ctrl c')
type(content='xxx')
scroll(point='<point>x1 y1</point>', direction='down or up or right or left')
wait()
finished(content='xxx')
...
"""
```

**支持的桌面操作**：
- 单击、双击、右键点击
- 拖拽操作
- 键盘快捷键（最多3键组合）
- 文本输入（支持转义字符）
- 滚动操作
- 等待操作
- 任务完成标记

#### 2.2.2 移动端模板 (MOBILE_USE)

```python
MOBILE_USE_DOUBAO = """...
## Action Space
click(point='<point>x1 y1</point>')
long_press(point='<point>x1 y1</point>')
type(content='')
scroll(point='<point>x1 y1</point>', direction='down or up or right or left')
open_app(app_name='')
drag(start_point='<point>x1 y1</point>', end_point='<point>x2 y2</point>')
press_home()
press_back()
finished(content='xxx')
...
"""
```

**移动端特有操作**：
- 长按 (long_press)
- 打开应用 (open_app)
- Home 键 (press_home)
- 返回键 (press_back)

#### 2.2.3 Grounding 模板

```python
GROUNDING_DOUBAO = """...
## Action Space
click(point='<point>x1 y1</point>')
...
"""
```

仅输出动作，不包含思维过程，用于评估模型的元素定位能力。

---

## 三、数据流架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        UI-TARS 数据流                           │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐
│   屏幕截图    │───▶│  图像预处理   │───▶│     Qwen2.5-VL 模型      │
│  (原始图像)   │    │ smart_resize │    │   (视觉语言理解+推理)     │
└──────────────┘    └──────────────┘    └──────────────────────────┘
                                                    │
                                                    ▼
                                        ┌──────────────────────────┐
                                        │       模型输出            │
                                        │  "Thought: ...\n         │
                                        │   Action: click(...)"    │
                                        └──────────────────────────┘
                                                    │
                                                    ▼
                                        ┌──────────────────────────┐
                                        │  parse_action_to_        │
                                        │  structure_output        │
                                        │  (动作解析)               │
                                        └──────────────────────────┘
                                                    │
                                                    ▼
                                        ┌──────────────────────────┐
                                        │  parsing_response_to_    │
                                        │  pyautogui_code          │
                                        │  (代码生成)               │
                                        └──────────────────────────┘
                                                    │
                                                    ▼
                                        ┌──────────────────────────┐
                                        │      PyAutoGUI 执行       │
                                        │   (GUI 自动化操作)        │
                                        └──────────────────────────┘
```

---

## 四、坐标系统详解

### 4.1 坐标表示方式

UI-TARS 使用 **绝对坐标系统**，基于 Qwen2.5-VL 的坐标输出特性：

| 坐标类型 | 范围 | 说明 |
|---------|------|------|
| 模型输出 | 0-1000 | 相对于 smart_resize 后的图像尺寸 |
| 内部处理 | 0-1 | 归一化坐标 |
| 最终执行 | 实际像素 | 根据原始屏幕分辨率计算 |

### 4.2 坐标转换公式

```python
# 模型输出 → 归一化坐标
if model_type == "qwen25vl":
    # x 坐标
    normalized_x = model_x / smart_resize_width
    # y 坐标
    normalized_y = model_y / smart_resize_height

# 归一化坐标 → 屏幕像素
screen_x = normalized_x * image_width
screen_y = normalized_y * image_height
```

---

## 五、扩展生态

### 5.1 UI-TARS-Desktop

桌面客户端版本，支持在本地个人设备上运行：
- 仓库：[bytedance/UI-TARS-desktop](https://github.com/bytedance/UI-TARS-desktop)

### 5.2 Midscene.js

Web 自动化框架，将 UI-TARS 能力集成到浏览器自动化：
- 仓库：[web-infra-dev/Midscene](https://github.com/web-infra-dev/Midscene)

---

## 六、性能基准

### 6.1 在线基准评测

| 基准类型 | 基准名称 | UI-TARS-1.5 | OpenAI CUA | Claude 3.7 |
|---------|---------|-------------|------------|------------|
| 桌面使用 | OSWorld (100步) | **42.5** | 36.4 | 28 |
| 桌面使用 | Windows Agent Arena | **42.1** | - | - |
| 浏览器 | WebVoyager | 84.8 | **87** | 84.1 |
| 手机使用 | Android World | **64.2** | - | - |

### 6.2 Grounding 能力评测

| 基准 | UI-TARS-1.5 | OpenAI CUA | Claude 3.7 |
|-----|-------------|------------|------------|
| ScreenSpot-V2 | **94.2** | 87.9 | 87.6 |
| ScreenSpotPro | **61.6** | 23.4 | 27.7 |

---

## 七、使用示例

### 7.1 安装

```bash
pip install ui-tars
# 或
uv pip install ui-tars
```

### 7.2 基本使用

```python
from ui_tars.action_parser import parse_action_to_structure_output, parsing_response_to_pyautogui_code

# 模型输出
response = "Thought: Click the button\nAction: click(start_box='(100,200)')"

# 原始图像尺寸
original_image_width, original_image_height = 1920, 1080

# 解析动作
parsed_dict = parse_action_to_structure_output(
    response,
    factor=1000,
    origin_resized_height=original_image_height,
    origin_resized_width=original_image_width,
    model_type="qwen25vl"
)

# 生成 PyAutoGUI 代码
pyautogui_code = parsing_response_to_pyautogui_code(
    responses=parsed_dict,
    image_height=original_image_height,
    image_width=original_image_width
)

print(pyautogui_code)
```

---

## 八、总结

UI-TARS 的代码架构体现了以下设计理念：

1. **端到端设计**：从截图输入到 GUI 操作输出，无需复杂的中间件
2. **跨平台兼容**：通过不同的提示词模板支持桌面和移动端
3. **坐标系统统一**：使用归一化坐标，适配不同分辨率屏幕
4. **可扩展性强**：模块化设计，易于集成到其他项目

核心代码量精简（约500行），但功能完整，是学习 GUI Agent 实现的优秀参考。

---

## 参考文献

1. [UI-TARS: Pioneering Automated GUI Interaction with Native Agents](https://arxiv.org/abs/2501.12326)
2. [UI-TARS-2 Technical Report](https://arxiv.org/abs/2509.02544)
3. [Qwen2.5-VL Technical Report](https://arxiv.org/abs/2409.12191)
