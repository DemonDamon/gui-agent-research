# MAI-UI 自动化数据采集 Pipeline - 开发文档

## 文档概述

本文档详细说明了MAI-UI自动化数据采集Pipeline的代码结构、模块设计和使用方法。

**版本**: 1.0.0
**最后更新**: 2025-02-06 (Phase 3 完成)

---

## 目录

1. [目录结构](#1-目录结构)
2. [核心模块说明](#2-核心模块说明)
3. [数据结构](#3-数据结构)
4. [使用指南](#4-使用指南)
5. [开发规范](#5-开发规范)

---

## 1. 目录结构

```
MAI-UI-WebUI/
├── automation/                      # 自动化模块（新增）
│   ├── __init__.py                 # 模块初始化
│   ├── config/                     # 配置子模块
│   │   ├── __init__.py
│   │   ├── pipeline_config.py      # 配置数据类定义
│   │   └── pipeline_config.yaml    # 配置文件
│   ├── utils/                      # 工具子模块
│   │   ├── __init__.py
│   │   ├── logger.py              # 日志工具
│   │   └── checkpoint.py          # 检查点管理
│   ├── task_loader.py             # 任务加载器 (P1)
│   ├── task_executor.py           # 任务执行器 (P1)
│   ├── trajectory_judge.py        # LLM打标器 (P2)
│   ├── judge_prompts.py           # 打标提示词模板 (P2)
│   ├── statistics.py              # 数据统计 (P3)
│   ├── data_filter.py             # 数据筛选 (P3)
│   ├── report_generator.py        # 报告生成 (P3)
│   ├── pipeline.py                # 主Pipeline编排
│   └── docs.md                    # 本文档
│
├── tasks/                          # 任务源文件目录（新增）
│   ├── tasks_example.txt          # TXT格式示例
│   └── tasks_example.jsonl        # JSONL格式示例
│
├── data/                           # 数据输出目录（新增）
│   ├── collected/                  # 采集的原始数据（轨迹+截图）
│   │   └── {session_id}/
│   │       ├── step_*.png
│   │       └── trajectory.jsonl
│   ├── labeled/                    # 打标后的数据
│   │   └── {session_id}/
│   │       └── label.json          # 打标结果
│   └── reports/                    # 统计报告
│       ├── summary_*.html         # HTML汇总报告 (P3)
│       └── statistics_*.json       # 统计数据 (P3)
│
├── web_ui/                         # 现有Web UI模块（复用）
├── src/                            # 现有Agent模块（复用）
├── run_pipeline.py                 # Pipeline启动脚本（新增，P1）
├── run_judge.py                    # 打标脚本（新增，P2）
└── run_analyze.py                  # 分析脚本（新增，P3）
```

---

## 2. 核心模块说明

### 2.1 配置模块 (`config/`)

#### `pipeline_config.py`

定义了所有配置相关的数据类：

| 数据类 | 说明 |
|--------|------|
| `PipelineConfig` | 总配置容器 |
| `TaskSourceConfig` | 任务源配置 |
| `ExecutionConfig` | 执行配置 |
| `JudgeConfig` | 打标配置 |
| `ReportingConfig` | 报告配置 |

**主要函数**:
- `load_config(path)` - 从YAML文件加载配置
- `save_config(config, path)` - 保存配置到YAML文件

#### `pipeline_config.yaml`

配置文件，包含所有可配置项。使用YAML格式便于修改。

### 2.2 工具模块 (`utils/`)

#### `logger.py`

统一的日志输出工具。

**主要函数**:
```python
get_logger(name, level, log_file, log_dir) -> Logger
```

**日志格式**:
```
2025-02-06 10:30:00 [INFO] MAI-UI-Pipeline: 开始执行任务
```

#### `checkpoint.py`

检查点管理，用于保存和恢复执行进度。

**主要类**:
```python
class CheckpointData:
    """检查点数据结构"""
    - pipeline_name: Pipeline名称
    - total_tasks: 总任务数
    - completed_tasks: 已完成任务数
    - failed_tasks: 失败任务数
    - current_index: 当前任务索引
    - completed_session_ids: 已完成的session ID列表
    - failed_task_indices: 失败任务索引列表
    - timestamp: 时间戳

class CheckpointManager:
    """检查点管理器"""
    - save(data): 保存检查点
    - load(pipeline_name): 加载检查点
    - delete(pipeline_name): 删除检查点
```

### 2.3 任务加载器 (`task_loader.py`)

负责从文件加载任务列表。

**主要类**:

```python
@dataclass
class Task:
    """任务数据结构"""
    - id: 任务唯一ID (基于instruction的MD5哈希)
    - instruction: 任务指令文本
```

**TaskLoader类**:

| 方法 | 说明 |
|------|------|
| `load_from_file(path, type)` | 从文件加载任务 |
| `_load_txt(path)` | 从TXT文件加载 |
| `_load_jsonl(path)` | 从JSONL文件加载 |
| `get_tasks()` | 获取已加载的任务列表 |
| `get_task_count()` | 获取任务数量 |

**支持的文件格式**:

1. **TXT格式** (每行一个任务):
   ```
   打开微信
   打开抖音
   在抖音搜索人工智能相关视频
   ```

2. **JSONL格式** (每行一个JSON):
   ```json
   {"instruction": "打开微信"}
   {"instruction": "在抖音搜索视频"}
   ```

### 2.4 任务执行器 (`task_executor.py`)

核心执行引擎，复用现有的`AgentRunner`。

**主要数据结构**:

```python
class ExecutionStatus(Enum):
    """任务执行状态"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    SUCCESS = "success"      # 成功完成
    FAILED = "failed"        # 执行失败
    TIMEOUT = "timeout"      # 超时
    ERROR = "error"          # 错误

@dataclass
class ExecutionResult:
    """单个任务执行结果"""
    - task_id: 任务ID
    - task_instruction: 任务指令
    - status: 执行状态
    - session_id: 会话ID
    - start_time: 开始时间
    - end_time: 结束时间
    - duration: 耗时（秒）
    - steps: 执行步数
    - error_message: 错误信息
    - retry_count: 重试次数
```

**TaskExecutor类**:

| 方法 | 说明 |
|------|------|
| `execute_task(task, retry_count)` | 执行单个任务 |
| `execute_batch(tasks, max_retries)` | 批量执行任务 |
| `get_runner()` | 获取底层AgentRunner实例 |
| `reset()` | 重置执行器 |

**执行流程**:
```
1. 初始化 AgentRunner
2. 调用 runner.start_task(instruction)
3. 循环调用 runner.auto_run() 直到完成
4. 检测超时和异常
5. 返回执行结果
```

### 2.5 主Pipeline (`pipeline.py`)

编排整个数据采集流程。

**主要数据结构**:

```python
@dataclass
class PipelineResult:
    """Pipeline执行结果"""
    - total_tasks: 总任务数
    - completed_tasks: 完成任务数
    - failed_tasks: 失败任务数
    - success_rate: 成功率
    - results: 执行结果列表
    - start_time: 开始时间
    - end_time: 结束时间
    - duration: 总耗时
```

**DataCollectionPipeline类**:

| 方法 | 说明 |
|------|------|
| `run(resume)` | 运行完整Pipeline |
| `_load_tasks()` | 加载任务 |
| `_resume_from_checkpoint()` | 从检查点恢复 |
| `_execute_tasks()` | 执行任务 |
| `_save_results()` | 保存结果 |
| `_print_final_report()` | 打印最终报告 |

**Pipeline流程**:
```
┌─────────────────────────────────────────────────────────────┐
│  阶段 1: 加载任务                                            │
│  - 从配置指定的文件加载任务                                  │
│  - 去重、统计                                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 2: 恢复进度 (如果启用)                                 │
│  - 从检查点文件读取进度                                      │
│  - 跳过已完成的任务                                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 3: 执行任务                                            │
│  - 初始化TaskExecutor                                        │
│  - 逐个执行任务                                              │
│  - 失败重试                                                  │
│  - 实时更新进度                                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  保存结果和报告                                              │
│  - 保存执行结果到JSON                                        │
│  - 更新检查点                                                │
│  - 打印最终报告                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.6 LLM打标器 (`trajectory_judge.py`) - Phase 2

使用LLM作为Judge，自动判断任务执行是否成功。

**主要数据结构**:

```python
@dataclass
class JudgmentResult:
    """判断结果"""
    - session_id: Session ID
    - instruction: 任务指令
    - success: 是否成功
    - confidence: 置信度 (0-1)
    - reason: 判断理由
    - quality_score: 质量评分 (0-10)
    - judge_model: 使用的模型
    - timestamp: 判断时间

@dataclass
class JudgeConfig:
    """Judge配置"""
    - enabled: 是否启用
    - provider: 提供商 (openai, etc.)
    - api_base: API地址
    - model: 模型名称
    - api_key: API密钥
    - check_last_n_steps: 检查最后N步
    - require_termination: 是否要求终止动作
    - min_confidence: 最低置信度
    - max_tokens: 最大token数
    - temperature: 温度参数
    - use_vision: 是否使用视觉模型
```

**TrajectoryJudge类**:

| 方法 | 说明 |
|------|------|
| `judge_session(session_id, logs_dir)` | 判断单个session |
| `judge_batch(session_ids, logs_dir)` | 批量判断 |
| `_load_trajectory(session_id, logs_dir)` | 加载轨迹数据 |
| `_analyze_trajectory(logs)` | 分析轨迹统计 |
| `_judge_text_only(...)` | 纯文本判断 |
| `_judge_with_vision(...)` | 视觉模型判断（含截图） |
| `_save_label(result, logs_dir)` | 保存打标结果 |

**判断维度**:
1. 任务完成度：目标是否达成
2. 轨迹质量：操作是否合理、高效
3. 异常检测：有无死循环、重复操作

**打标结果存储** (`data/labeled/{session_id}/label.json`):
```json
{
  "session_id": "20250206_163000",
  "instruction": "打开微信",
  "success": true,
  "confidence": 0.95,
  "reason": "任务成功完成，微信应用已打开",
  "quality_score": 8,
  "judge_model": "gpt-4o",
  "timestamp": "2025-02-06T16:35:00"
}
```

### 2.7 打标提示词 (`judge_prompts.py`) - Phase 2

定义LLM Judge使用的提示词模板。

**JudgePrompts类**:

| 方法 | 说明 |
|------|------|
| `SYSTEM_PROMPT` | 系统提示词常量 |
| `build_user_prompt(...)` | 构建用户提示词 |
| `build_trajectory_summary(...)` | 构建轨迹摘要 |
| `build_vision_prompt(...)` | 构建多模态提示词（含截图） |

**提示词设计要点**:
- 明确评估标准（完成度、质量、异常）
- 要求JSON格式输出
- 提供清晰的评分说明
- 支持多模态输入（可选）

### 2.8 数据统计 (`statistics.py`) - Phase 3

对采集和打标的数据进行统计分析。

**主要数据结构**:

```python
@dataclass
class SessionStats:
    """单个Session的统计信息"""
    - session_id: Session ID
    - instruction: 任务指令
    - has_label: 是否有打标
    - success: 是否成功
    - confidence: 置信度
    - quality_score: 质量分数
    - steps: 执行步数
    - duration: 耗时
    - has_termination: 是否正常终止

@dataclass
class OverallStatistics:
    """总体统计数据"""
    - total_sessions: 总session数
    - labeled_sessions: 已打标数
    - successful_sessions: 成功数
    - failed_sessions: 失败数
    - success_rate: 成功率
    - avg_confidence: 平均置信度
    - avg_quality_score: 平均质量分
    - quality_distribution: 质量分布
    - avg_steps: 平均步数
    - termination_rate: 终止率
```

**DataStatistics类**:

| 方法 | 说明 |
|------|------|
| `analyze()` | 分析所有数据 |
| `_scan_sessions()` | 扫描所有session |
| `get_successful_sessions()` | 获取成功的session列表 |
| `get_failed_sessions()` | 获取失败的session列表 |
| `get_unlabeled_sessions()` | 获取未打标的session列表 |

### 2.9 数据筛选 (`data_filter.py`) - Phase 3

根据条件筛选session。

**FilterCriteria数据类**:

```python
@dataclass
class FilterCriteria:
    has_label: bool          # 是否有打标
    success: bool            # 是否成功
    min_confidence: float    # 最低置信度
    min_quality: int         # 最低质量分
    max_steps: int           # 最大步数
    min_steps: int           # 最小步数
    has_termination: bool    # 是否正常终止
```

**DataFilter类**:

| 方法 | 说明 |
|------|------|
| `filter(session_stats, criteria)` | 根据条件筛选 |
| `export_session_list(...)` | 导出session ID列表 |
| `export_data_list(...)` | 导出详细数据清单CSV |

### 2.10 报告生成 (`report_generator.py`) - Phase 3

生成HTML格式的可视化报告。

**ReportGenerator类**:

| 方法 | 说明 |
|------|------|
| `generate_summary_report(...)` | 生成HTML汇总报告 |
| `generate_statistics_json(...)` | 生成统计JSON |

**报告特点**:
- 统计卡片展示关键指标
- 按状态分组显示session列表
- 质量分可视化进度条
- 支持大量数据的分页显示

---

## 3. 数据结构

### 3.1 任务文件格式

**TXT格式** (`tasks.txt`):
```
# 注释行会被忽略
打开微信
打开抖音
在抖音搜索人工智能相关视频
```

**JSONL格式** (`tasks.jsonl`):
```json
{"instruction": "打开微信"}
{"instruction": "打开抖音"}
{"instruction": "在抖音搜索人工智能相关视频"}
```

### 3.2 执行结果格式

保存在 `data/reports/results_YYYYMMDD_HHMMSS.json`:

```json
[
  {
    "task_id": "task_abc123",
    "task_instruction": "打开微信",
    "status": "success",
    "session_id": "20250206_103000",
    "start_time": "2025-02-06T10:30:00",
    "end_time": "2025-02-06T10:30:15",
    "duration": 15.2,
    "steps": 3,
    "error_message": "",
    "retry_count": 0
  }
]
```

### 3.3 轨迹数据格式

保存在 `data/collected/{session_id}/`:

```
{session_id}/
├── step_001.png              # 每步截图
├── step_002.png
├── ...
└── trajectory.jsonl          # 完整轨迹
```

`trajectory.jsonl` 格式 (每行一个JSON):
```json
{"step_index": 1, "thinking": "...", "action": {...}, "action_type": "click", "success": true, "message": "...", "screenshot_path": "...", "instruction": "...", "timestamp": "..."}

```

---

## 4. 使用指南

### 4.1 基本使用

**1. 准备任务文件**

创建 `tasks/my_tasks.jsonl`:
```json
{"instruction": "打开微信"}
{"instruction": "打开抖音"}
{"instruction": "在抖音搜索人工智能"}
```

**2. 运行Pipeline**

```bash
# 使用默认配置
python run_pipeline.py

# 指定任务文件
python run_pipeline.py --tasks tasks/my_tasks.jsonl

# 从检查点恢复
python run_pipeline.py --resume

# 指定设备
python run_pipeline.py --device emulator-5554

# 指定模型
python run_pipeline.py --model MAI-UI-8B

# 指定输出目录
python run_pipeline.py --output data/my_collection
```

### 4.2 配置文件修改

编辑 `automation/config/pipeline_config.yaml`:

```yaml
pipeline:
  task_source:
    path: "tasks/my_tasks.jsonl"    # 修改任务文件路径
  execution:
    device_id: null                 # 指定设备ID
    max_steps_per_task: 50          # 最大步数
    timeout_per_task: 300           # 超时时间
    model_name: "MAI-UI-2B"         # 模型名称
```

### 4.3 环境变量

```bash
# 设置打标API密钥
export JUDGE_API_KEY="sk-xxx"

# 或使用OpenAI API密钥
export OPENAI_API_KEY="sk-xxx"
```

### 4.4 使用LLM打标 (Phase 2)

**独立打标脚本**:

```bash
# 打标所有已采集的session
python run_judge.py

# 打标指定session
python run_judge.py --session 20250206_163000

# 限制打标数量
python run_judge.py --limit 10

# 指定模型
python run_judge.py --model gpt-4o

# 启用视觉模式（传入截图）
python run_judge.py --vision

# 指定数据目录
python run_judge.py --logs-dir data/collected
```

**在Pipeline中使用打标**:

```python
from automation import DataCollectionPipeline, load_config

config = load_config("automation/config/pipeline_config.yaml")
pipeline = DataCollectionPipeline(config)

# 执行任务
result = pipeline.run()

# 对执行结果进行打标
judgments = pipeline.judge_results()
```

**打标配置** (`automation/config/pipeline_config.yaml`):

```yaml
judge:
  enabled: true
  provider: "openai"
  api_base: "https://api.openai.com/v1"
  model: "gpt-4o"
  api_key: ""
  check_last_n_steps: 3
  require_termination: true
  min_confidence: 0.7
  max_tokens: 1000
  temperature: 0.1
```

**查看打标结果**:

```bash
# 查看所有已打标的session
ls data/labeled/

# 查看某个session的打标结果
cat data/labeled/20250206_163000/label.json
```

### 4.5 数据分析 (Phase 3)

**生成分析报告**:

```bash
# 生成完整报告（HTML + JSON）
python run_analyze.py

# 查看生成的报告
open data/reports/summary_*.html
```

**筛选高质量数据**:

```bash
# 筛选质量分 >= 7 的数据
python run_analyze.py --filter --min-quality 7

# 筛选成功且置信度 >= 0.8 的数据
python run_analyze.py --filter --success true --min-confidence 0.8

# 筛选步数 <= 20 的数据
python run_analyze.py --filter --max-steps 20
```

**导出数据列表**:

```bash
# 导出成功的session列表（用于后续训练）
python run_analyze.py --export-success

# 导出完整数据清单（CSV格式，方便人工审核）
python run_analyze.py --export-list

# 指定导出格式
python run_analyze.py --export-success --export-format json
```

**报告文件说明**:

| 文件 | 说明 |
|------|------|
| `summary_*.html` | 可视化汇总报告，用浏览器打开 |
| `statistics_*.json` | 统计数据JSON |
| `filtered_*.csv` | 筛选后的数据清单 |
| `successful_sessions_*.txt` | 成功的session ID列表 |
| `data_list_*.csv` | 完整数据清单 |

**HTML报告内容**:
- 统计卡片：总数、成功、失败、成功率、平均质量分等
- 成功任务列表：显示所有成功的session
- 失败任务列表：显示所有失败的session
- 未打标任务列表：显示需要人工审核的session
- 每条记录包含：session_id、指令、步数、耗时、质量分等

---

## 5. 开发规范

### 5.1 代码风格

- 使用类型注解
- 添加详细的docstring
- 使用dataclass定义数据结构
- 异常处理要完善
- 日志记录要充分

### 5.2 命名规范

- 类名: PascalCase (如 `TaskLoader`)
- 函数名: snake_case (如 `load_tasks`)
- 常量: UPPER_CASE (如 `MAX_RETRIES`)
- 私有方法: _前缀 (如 `_load_txt`)

### 5.3 错误处理

```python
try:
    # 执行操作
    result = some_operation()
except FileNotFoundError as e:
    logger.error(f"文件不存在: {e}")
    raise
except Exception as e:
    logger.error(f"未知错误: {e}", exc_info=True)
    raise
```

### 5.4 日志规范

```python
logger.info("正常信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.debug("调试信息")
```

### 5.5 扩展指南

**添加新的任务格式**:

在 `TaskLoader` 中添加新方法:
```python
def _load_csv(self, filepath: Path) -> List[Task]:
    # 实现CSV加载逻辑
    pass
```

**添加新的执行策略**:

在 `TaskExecutor` 中扩展 `execute_task` 方法。

**添加新的报告类型**:

在 `Pipeline` 中添加 `_generate_xxx_report` 方法。

---

## 附录

### A. 常见问题

**Q: 如何查看执行进度？**
A: 查看日志文件 `data/reports/pipeline_*.log`

**Q: 如何断点续传？**
A: 使用 `--resume` 参数

**Q: 如何处理任务间干扰？**
A: 设置 `return_to_desktop: true` 每个任务前返回桌面

### B. 依赖检查

```bash
# 检查必要的Python包
pip list | grep -E "gradio|Pillow|openai|pyyaml"
```

### C. ADB连接检查

```bash
# 检查ADB连接
adb devices
```

---

**文档维护**: 请在修改代码时同步更新本文档。
