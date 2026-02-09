# MAI-UI Cloud Phone Web UI

云手机专用 Web 控制台，通过 `api_adapter` 进行动作映射，保持 MAI-UI 原始提示词不变。

## 文件结构

```
web_ui_cloudphone/
├── __init__.py           # 包初始化
├── api_adapter.py        # 动作映射层（核心）
├── adb_utils.py          # ADB 工具函数
├── agent_runner.py       # Agent 运行器
├── trajectory_utils.py   # 轨迹处理
└── app.py                # Web UI 主入口
```

## 设计原理

### 动作映射流程

```
用户输入任务
    ↓
MAI-UI Agent (使用原始 prompt.py)
    ↓ 模型输出训练时学过的格式
LLM 输出: {"action": "click", "coordinate": [x, y]}
    ↓ api_adapter.py 做映射
云手机 API: {"_metadata": "do", "action": "Tap", "element": [x, y]}
    ↓ adb_utils.py
ADB 命令执行
```

### 为什么这样设计？

1. **保持原始提示词不变**：模型输出训练时学过的格式，减少幻觉
2. **在 api_adapter 层做映射**：集中管理映射逻辑，易于维护
3. **独立文件夹**：不影响原有本地设备代码

## 启动方式

### 方式一：使用启动脚本（推荐）

```bash
cd /Users/hongyizhao/Desktop/CX/MAI-UI-WebUI
python start_cloudphone_ui.py
```

### 方式二：直接运行

```bash
cd /Users/hongyizhao/Desktop/CX/MAI-UI-WebUI/web_ui_cloudphone
python app.py
```

启动后访问：`http://localhost:8867`

## 使用步骤

1. **启动云手机 app**（在你的本地手机上）

2. **检查 ADB 连接**
   - 确保 USB 调试已开启
   - 点击"检查"按钮查看设备状态

3. **配置模型**
   - 选择提供商或填写自定义配置
   - 点击"测试"验证连接

4. **执行任务**
   - 在"任务指令"框中输入任务描述
   - 点击"▶ 执行"开始自动执行

5. **查看轨迹**
   - 右侧实时显示执行轨迹
   - 可导出 PDF 查看完整过程

## 动作映射表

| MAI-UI 原始格式 | 云手机 API 格式 |
|-----------------|----------------|
| `click` | `Tap` + `element` |
| `long_press` | `LongPress` + `element` |
| `swipe` + direction | `Swipe` + `start`/`end` |
| `type` | `Type` + `text` |
| `open`/`awake` | `Launch` + `app` |
| `home` | `Home` |
| `back` | `Back` |
| `enter` | `Enter` |
| `wait` | `Wait` + `duration` |

## 日志输出

各模块使用统一的日志格式：

```
[时间戳] - [模块名] - 级别 - 消息
```

- `[API_ADAPTER]` - 动作映射
- `[AGENT_RUNNER]` - Agent 运行
- `[ADB]` - ADB 命令
- `[WEB_UI]` - Web UI

## 配置文件

模型配置：`../model_config.yaml`

```yaml
local:  # 本地 vLLM
  api_base: "http://localhost:8000/v1"
  default_model: "MAI-UI-8B"
```

## 常见问题

### Q: 动作执行失败？
A: 检查日志输出，查看具体错误原因。可能是：
- 设备未连接
- 坐标超出屏幕范围
- 应用未安装

### Q: 模型响应慢？
A: 可以调整 `agent_runner.py` 中的截图缩放参数：
```python
max_dim = 1024  # 减小可加快速度
```

### Q: 中文输入不正常？
A: 确保 YADB 已安装到设备，`adb_utils.py` 会自动处理。

## 与本地版本的区别

| 特性 | 本地版本 (web_ui/) | 云手机版本 (web_ui_cloudphone/) |
|------|-------------------|-------------------------------|
| 提示词 | `prompt.py` | `prompt.py` (相同) |
| 动作映射 | 无 | `api_adapter.py` |
| ADB 工具 | `adb_utils.py` | `adb_utils.py` (优化) |
| 端口 | 8866 | 8867 |
