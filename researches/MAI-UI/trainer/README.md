# MAI-UI SFT + RL 训练代码 (增强版)

**作者**: Damon Li  
**日期**: 2026年1月19日

本项目基于 MAI-UI 技术报告，实现了一套完整的 SFT + RL 训练流程，并根据论文细节进行了深度优化。

## 核心特性

- **自进化数据管道**: 实现了拒绝采样、人工标注、自动 Agent 执行三种数据源的融合。
- **在线强化学习**: 基于 TRL 和 PPO，支持大规模并行环境和长程任务训练。
- **系统级优化**: 支持 500+ 并行环境、异步执行、混合并行。
- **高级策略**: 实现了 Zoom-In 策略、MCP 工具调用、Agent-User 交互逻辑。
- **课程学习**: 自动调整任务难度，防止训练崩溃。
- **混合验证**: 结合基于规则的验证器和 MLLM-as-a-Judge 框架。

## 目录结构

```
.
├── configs/
│   ├── sft_config.yaml
│   └── rl_config.yaml
├── data/
│   └── build_data.py
├── sft_trainer.py
├── rl_trainer.py
├── evaluate.py
├── requirements.txt
└── README.md
```

## 使用流程

### 1. 环境准备

```bash
pip install -r requirements.txt
```

### 2. 数据构建

```bash
python data/build_data.py --config configs/data_config.yaml
```

### 3. SFT 训练

```bash
python sft_trainer.py --config configs/sft_config.yaml
```

### 4. RL 训练

```bash
python rl_trainer.py --config configs/rl_config.yaml
```

### 5. 模型评估

```bash
python evaluate.py --model_path ./models/mai-ui-2b-rl --task_path ./data/benchmarks/sample.textproto --use_zoom_in
```

## 详细配置

请参考 `configs/` 目录下的 YAML 文件，根据您的硬件环境和数据路径进行修改。
