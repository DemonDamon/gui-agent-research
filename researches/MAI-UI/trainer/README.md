# MAI-UI SFT + RL 训练代码（对齐上游版本）

**作者**: Damon Li  
**日期**: 2026年1月19日

本项目基于 MAI-UI 技术报告，实现了一套完整的 SFT + RL 训练流程，并与上游 MobileWorld 代码库完全对齐。

## 核心特性

- **上游对齐**: 完全对齐上游 `mobile_world` 的动作格式、轨迹日志格式和 Prompt 模板
- **自进化数据管道**: 从 `traj.json` 日志构建 SFT 数据集，支持拒绝采样、人工标注、自动 Agent 执行三种数据源
- **基于 verl 的异步 RL**: 实现严格 on-policy 异步 RL 训练框架，支持大规模并行环境
- **配置驱动**: 所有训练脚本支持 YAML 配置，并允许 CLI 参数覆盖
- **经验回放**: 实现论文中的经验回放机制（仅在无成功轨迹时补充）

## 目录结构

```
trainer/
├── configs/
│   ├── data_config.yaml      # 数据构建配置
│   ├── sft_config.yaml       # SFT 训练配置
│   └── rl_config.yaml        # RL 训练配置
├── data/
│   └── build_data.py         # 数据构建脚本
├── mobile_world/             # 上游 MobileWorld 代码库（已迁移）
├── sft_trainer.py            # SFT 训练脚本
├── rl_trainer.py             # RL 训练脚本（verl 风格）
├── evaluate.py               # 模型评估脚本（使用上游 runner）
├── requirements.txt          # 依赖列表
└── README.md                 # 本文档
```

## 与上游代码对齐

### 动作格式

所有动作使用上游的 `JSONAction` 模型，支持以下动作类型：
- GUI 操作: `click`, `long_press`, `double_tap`, `drag`, `swipe`, `input_text`, `navigate_back`, `navigate_home`, `open_app`, `wait`
- 特殊操作: `ask_user`, `answer`, `finished`, `mcp`

### 轨迹格式

轨迹数据完全对齐上游 `TrajLogger` 格式：
- `traj.json` 包含 `task_goal`, `step`, `prediction`, `action`, `ask_user_response`, `tool_call`
- 截图存储在 `screenshots/` 目录
- 评分存储在 `result.txt`

### Prompt 格式

SFT 数据构建使用上游 `MAI_MOBILE_SYS_PROMPT_ASK_USER_MCP` 格式，包含：
- System prompt（动作空间定义）
- Task goal
- Action history（最近 3 步）
- Current observation（截图）

## 使用流程

### 1. 环境准备

```bash
cd trainer
pip install -r requirements.txt
```

确保上游代码在 `../upstream/src` 目录下可用。

### 2. 数据构建

从上游运行产生的 `traj.json` 日志构建 SFT 数据集：

```bash
# 编辑 configs/data_config.yaml 设置 log_root 路径
python data/build_data.py --config configs/data_config.yaml
```

输出为 JSONL 格式，每行包含：
- `prompt`: 完整的 prompt（包含 system prompt、task goal、history、image）
- `response`: 模型的原始 prediction
- `metadata`: 任务名称、步骤、动作等元数据

### 3. SFT 训练

使用构建的数据进行监督微调：

```bash
# 编辑 configs/sft_config.yaml 设置模型和数据路径
python sft_trainer.py --config configs/sft_config.yaml

# 或使用 CLI 参数覆盖
python sft_trainer.py --config configs/sft_config.yaml \
    --model_name_or_path Tongyi-MAI/MAI-UI-2B \
    --data_path ./data/processed/sft_data.jsonl \
    --output_dir ./models/sft_model
```

### 4. RL 训练（基于 verl 的异步 on-policy）

使用上游环境进行异步 RL 训练：

```bash
# 编辑 configs/rl_config.yaml 设置所有必需参数
python rl_trainer.py --config configs/rl_config.yaml --llm_base_url https://api.openai.com/v1

# 必需配置项：
# - model.sft_model_path: SFT 模型路径
# - llm_base_url: LLM API 基础 URL
# - environment.num_parallel_envs: 并行环境数量
```

**RL 训练特性**：
- **异步 Rollout**: 使用线程池管理环境池，异步执行 rollout
- **严格 On-Policy**: 每轮更新仅使用当前策略的 rollout 轨迹
- **经验回放**: 维护成功轨迹缓冲，仅在无成功轨迹时补充
- **奖励设计**: 任务完成奖励 + 动作重复惩罚
- **DAPO 风格**: 支持非对称裁剪（当前使用对称裁剪，可扩展）

**混合并行支持**：
- 当前实现预留了混合并行接口（`hybrid_parallelism` 配置项）
- 实际 TP/PP/CP 需要集成 Megatron-LM 或其他框架
- 长序列训练可通过调整 `max_step` 和 batch 大小适配

### 5. 模型评估

使用上游 runner 进行评测：

```bash
python evaluate.py \
    --agent_type mai_ui_agent \
    --model_name Tongyi-MAI/MAI-UI-2B \
    --llm_base_url https://api.openai.com/v1 \
    --log_root ./eval_logs \
    --tasks task1,task2,task3 \
    --max_step 50 \
    --enable_mcp  # 如果任务需要 MCP 工具
```

评估脚本完全复用上游 `run_agent_with_evaluation`，确保：
- 动作解析与训练时一致
- 轨迹日志格式统一
- 评分逻辑一致

## 配置说明

### data_config.yaml

- `data_sources.log_root`: 上游日志根目录
- `filtering.min_score`: 最小成功分数阈值
- `image_processing.image_format`: 图片格式（`path` 或 `base64`）
- `output.output_path`: 输出 JSONL 文件路径

### sft_config.yaml

- `model.path`: 预训练模型路径
- `data.path`: SFT 数据 JSONL 路径
- `training.*`: 训练超参数（batch size、learning rate 等）

### rl_config.yaml

- `model.sft_model_path`: SFT 模型路径
- `llm_base_url`: LLM API 基础 URL（必需）
- `environment.num_parallel_envs`: 并行环境数量
- `ppo.*`: PPO 超参数
- `replay_buffer_size`: 经验回放缓冲大小（每任务最多轨迹数）

## 关键实现要点（与 verl 对齐）

### 严格 On-Policy

- 每轮更新仅使用当前策略 rollout 的轨迹
- 经验回放缓冲仅在 rollout 组中无成功轨迹时补充（论文策略）

### 异步 Rollout

- 环境池管理：维护固定数量的环境实例，重置和重用而非销毁
- 线程池执行：使用 Python threading 实现异步环境交互
- 失败恢复：环境失败时自动替换（需要实现备用会话机制）

### 混合并行

- 当前实现预留接口，不强制依赖外部框架
- 可通过配置 `hybrid_parallelism` 指定并行策略
- 长序列训练建议调整 batch size 和 gradient accumulation

### 奖励与惩罚

- 任务完成奖励：基于上游 `get_task_score` 的二进制奖励
- 动作重复惩罚：检测单步重复和 3-5 步循环模式
- 验证器支持：预留规则验证和 MLLM-as-a-Judge 接口

## 验证与回归

### 训练侧

- ✅ 配置驱动可启动
- ✅ 数据构建可输出标准 JSONL
- ✅ RL rollout 可生成符合上游轨迹格式的 `traj.json`
- ✅ 动作格式与上游完全对齐

### 评测侧

- ✅ 使用上游 runner，确保动作解析一致
- ✅ 支持 MCP 工具调用
- ✅ 支持 `ask_user` 交互
- ⚠️ Zoom-In 策略：当前评估脚本使用上游 runner，Zoom-In 需在 agent 层面实现

## 依赖说明

### 必需依赖

- `torch >= 2.0.0`
- `transformers >= 4.35.0`
- `datasets >= 2.14.0`
- `trl >= 0.7.0`
- `pyyaml >= 6.0`
- `pillow >= 10.0.0`
- `tqdm >= 4.66.0`

### 上游依赖

训练脚本直接使用 `trainer/mobile_world` 目录下的代码，无需额外配置。

## 参考资料

- MAI-UI 技术报告: `../MAI-UI 技术报告： 面向现实世界的基础型 GUI 智能体_2025.12_通义实验室.pdf`
- 上游代码: `../upstream/src/mobile_world/`
- verl 文档: https://verl.readthedocs.io/

## 致谢

感谢 MAI-UI 团队（阿里巴巴通义实验室）提供的详细技术报告和开源模型。
