# AgentCPM-GUI 深度调研报告

## 1. 模型概述

*   **模型名称**: AgentCPM-GUI
*   **开发者/机构**: 由清华大学自然语言处理实验室（THUNLP）、中国人民大学和 ModelBest 联合开发。
*   **发布时间**: 2025年5月13日首次开源。
*   **核心定位**: 一款专为移动端（安卓）设计的设备端 GUI 代理，能够接收智能手机截图作为输入，并自主执行用户指定的任务，特别针对中文应用环境进行了优化。

## 2. 论文信息

*   **论文标题**: AgentCPM-GUI: Building Mobile-Use Agents with Reinforcement Fine-Tuning
*   **arXiv 链接**: [https://arxiv.org/abs/2506.01391](https://arxiv.org/abs/2506.01391)
*   **英文摘要**:

> The recent progress of large language model agents has opened new possibilities for automating tasks through graphical user interfaces (GUIs), especially in mobile environments where intelligent interaction can greatly enhance usability. However, practical deployment of such agents remains constrained by several key challenges. Existing training data is often noisy and lack semantic diversity, which hinders the learning of precise grounding and planning. Models trained purely by imitation tend to overfit to seen interface patterns and fail to generalize in unfamiliar scenarios. Moreover, most prior work focuses on English interfaces while overlooks the growing diversity of non-English applications such as those in the Chinese mobile ecosystem. In this work, we present AgentCPM-GUI, an 8B-parameter GUI agent built for robust and efficient on-device GUI interaction. Our training pipeline includes grounding-aware pre-training to enhance perception, supervised fine-tuning on high-quality Chinese and English trajectories to imitate human-like actions, and reinforcement fine-tuning with GRPO to improve reasoning capability. We also introduce a compact action space that reduces output length and supports low-latency execution on mobile devices. AgentCPM-GUI achieves state-of-the-art performance on five public benchmarks and a new Chinese GUI benchmark called CAGUI, reaching 96.9% Type-Match and 91.3% Exact-Match. To facilitate reproducibility and further research, we publicly release all code, model checkpoint, and evaluation data.

*   **主要贡献**:
    *   提出了一个包含感知增强预训练、高质量数据监督微调和强化学习微调的完整训练流程。
    *   首次开源了针对中文应用进行优化的 GUI 代理，填补了非英语应用场景的空白。
    *   设计了紧凑的动作空间，显著降低了模型输出长度，提高了在移动设备上的推理效率。
    *   构建并发布了名为 CAGUI 的中文 GUI 评测基准，包含定位和代理任务，促进了相关研究。

## 3. 开源代码

*   **GitHub 仓库地址**: [https://github.com/OpenBMB/AgentCPM-GUI](https://github.com/OpenBMB/AgentCPM-GUI)
*   **Star 数量**: 1.2k (截至2026年1月)
*   **许可证**: Apache-2.0
*   **主要功能模块**: 代码库主要包含模型实现、SFT（监督微调）、RFT（强化学习微调）以及评测（Evaluation）相关脚本。

## 4. 技术架构

*   **模型架构**: AgentCPM-GUI 基于 8B 参数的 MiniCPM-V 架构构建，是一个视觉语言模型（VLM）。
*   **参数规模**: 8B (80亿)
*   **训练数据**: 训练过程分为三个阶段：
    1.  **感知增强预训练**: 在大规模的双语（中英文）安卓数据集上进行预训练，以增强对常见 GUI 元素的定位和理解能力。
    2.  **监督微调 (SFT)**: 在高质量的中英文操作轨迹数据上进行微调，模仿类似人类的操作行为。
    3.  **强化学习微调 (RFT)**: 使用 GRPO (Grounding-Reinforced Policy Optimization) 算法进行微调，让模型在输出动作前先“思考”，从而提升复杂任务的规划和推理能力。
*   **核心技术创新**: 
    *   **强化学习微调 (RFT)**: 引入“思考”步骤，显著改善了模型的推理能力和在复杂任务上的成功率。
    *   **紧凑的动作空间**: 优化了动作空间和 JSON 输出格式，将平均动作长度减少到 9.7 个 token，实现了低延迟的设备端执行。
    *   **中文原生支持**: 通过在包含30多款流行中文应用的数据集上进行微调，实现了对中文应用环境的良好支持。

## 5. 性能评测

AgentCPM-GUI 在多个主流的 GUI 代理评测基准上取得了领先的性能，尤其在中文任务上表现突出。

| 基准名称 (Benchmark) | 指标 (Metric) | AgentCPM-GUI-8B | UI-TARS-7B | Qwen2.5-VL-7B |
| :--- | :--- | :--- | :--- | :--- |
| Android Control (Low) | Type Match | **94.39%** | 95.24% | 94.14% |
| Android Control (Low) | Exact Match | 90.20% | **91.79%** | 84.96% |
| Android Control (High) | Type Match | 77.70% | **81.63%** | 75.10% |
| Android Control (High) | Exact Match | 69.17% | **74.43%** | 62.90% |
| GUI-Odyssey | Type Match | **90.85%** | 86.06% | 59.54% |
| GUI-Odyssey | Exact Match | **74.96%** | 67.90% | 46.28% |
| CAGUI (中文) | Type Match | **96.86%** | 88.62% | 74.18% |
| CAGUI (中文) | Exact Match | **91.28%** | 70.26% | 55.16% |

*TM: Type Match, EM: Exact Match*

## 6. 适用场景

*   **支持的平台**: 移动端 (Android)
*   **典型应用场景**: 
    *   自动化手机应用操作，如自动打卡、信息查询、商品购买等。
    *   为视障人士或操作不便者提供辅助功能。
    *   自动化应用测试和质量保证流程。
    *   在智能座舱等环境中，通过语音或自然语言指令操控车载应用。

## 7. 优势与局限

### 优势

*   **中文支持领先**: 作为首个为中文应用深度优化的开源模型，在中文 GUI 理解和操作方面具有明显优势。
*   **高效的设备端性能**: 8B 的模型规模和紧凑的动作空间设计，使其能够在移动设备上实现低延迟、高效率的本地运行。
*   **强大的推理能力**: 通过强化学习微调，模型具备了“先思考再行动”的能力，在处理需要多步骤规划的复杂任务时成功率更高。
*   **全面的开源**: 项目不仅开源了模型权重，还提供了完整的训练和评测代码，以及新建的中文评测基准，极大地推动了社区的研究和发展。

### 局限

*   **平台局限性**: 目前模型主要针对安卓平台，尚未支持桌面（Windows, macOS）或 Web 应用的自动化操作。
*   **对新应用泛化能力**: 尽管模型在多种应用上表现出色，但对于训练数据中未覆盖的、界面设计独特的全新应用，其泛化能力仍有待进一步验证。
*   **多模态理解深度**: 模型主要依赖视觉和文本信息，对于需要理解音频、视频或复杂动画交互的场景，能力可能受限。

## 8. 相关图片

*暂未在公开资料中发现明确的架构图或性能对比图。*
