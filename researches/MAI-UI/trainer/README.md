# MAI-UI SFT + RL 训练流程

> **作者**: Damon Li  
> **日期**: 2026年1月19日

本目录包含一套完整的、基于 MAI-UI 技术报告实现的 SFT (监督微调) 和 RL (强化学习) 训练代码，用于微调 MAI-UI-2B 模型。

## 1. 流程概览

训练流程分为三个主要阶段：

1.  **数据构建**: 从真实的设备交互中收集 GUI 轨迹数据，并将其格式化为训练所需的样本。
2.  **SFT (监督微调)**: 使用收集到的高质量轨迹数据，对预训练的 MAI-UI-2B 模型进行微调，使其学习基本的 GUI 操作和指令跟随能力。
3.  **RL (强化学习)**: 在 SFT 模型的基础上，通过与真实 Android 环境的在线交互进行强化学习 (PPO)，进一步提升模型的鲁棒性和任务成功率。

## 2. 目录结构

```
trainer/
├── README.md                # 本文档
├── requirements.txt         # 训练所需依赖
│
├── data/                    # 数据处理模块
│   ├── build_data.py        # 数据收集与格式化脚本
│   ├── raw/                 # 原始轨迹数据 (示例)
│   └── processed/           # 处理后的训练数据 (示例)
│
├── configs/                 # 配置文件
│   ├── sft_config.yaml      # SFT 训练配置
│   └── rl_config.yaml       # RL 训练配置
│
├── sft_trainer.py           # SFT 训练脚本
├── rl_trainer.py            # RL 训练脚本 (PPO)
└── evaluate.py              # 模型评估脚本
```

## 3. 使用指南

### 3.1 环境准备

首先，安装所有必要的依赖：

```bash
pip install -r requirements.txt
```

同时，确保您已正确安装和配置了 Android 环境，包括 Android SDK, ADB, 以及一个可用的模拟器 (AVD)。

### 3.2 数据构建

1.  **收集数据**: 使用 `data/build_data.py` 中的 `TrajectoryCollector` 类（或您自己的工具）从设备上收集交互轨迹。原始数据应包含截图和对应的用户动作。
2.  **格式化数据**: 运行 `build_data.py` 脚本，将原始数据转换为 SFT 训练所需的 JSON 格式。

    ```bash
    python data/build_data.py
    ```

### 3.3 SFT 训练

使用 `sft_trainer.py` 脚本和 `sft_config.yaml` 配置文件进行监督微调。

```bash
python sft_trainer.py --config configs/sft_config.yaml
```

训练完成后，微调过的模型将保存在 `configs/sft_config.yaml` 中指定的 `output_dir` 目录下。

### 3.4 RL 训练

在 SFT 模型的基础上，使用 `rl_trainer.py` 进行强化学习。

```bash
python rl_trainer.py --config configs/rl_config.yaml
```

**注意**: RL 训练需要一个正在运行的 Android 模拟器，其 AVD 名称应与 `rl_config.yaml` 中的 `avd_name` 匹配。

### 3.5 模型评估

使用 `evaluate.py` 脚本在指定的基准任务上评估您训练好的模型。

```bash
python evaluate.py --model_path ./models/mai-ui-2b-rl --task_path ./data/benchmarks/android_world_sample.textproto
```

## 4. 注意事项

-   **依赖库**: 本代码实现依赖 `transformers`, `trl`, `datasets`, `torch` 以及 `android_env` 等库。
-   **占位符实现**: `build_data.py` 和 `evaluate.py` 中的部分函数（如 `format_prompt`, `parse_action`）是概念性实现，需要根据您的具体数据格式和模型输入输出进行适配。
-   **资源要求**: 训练，特别是 RL 训练，需要较高的计算资源（GPU 显存和算力）。
