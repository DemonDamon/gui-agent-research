# UI-TARS-7B Research Report

## 1. 模型概述

*   **模型名称**: UI-TARS-7B
*   **开发者/机构**: 字节跳动
*   **发布时间**: 2025年
*   **核心定位**: 一个原生的GUI智能体模型，能够仅通过感知屏幕截图作为输入，执行类似人类的交互（例如，键盘和鼠标操作）。

## 2. 论文信息

*   **论文标题**: UI-TARS: Pioneering Automated GUI Interaction with Native Agents
*   **arXiv链接**: https://arxiv.org/abs/2501.12326
*   **摘要（英文）**:

> This paper introduces UI-TARS, a native GUI agent model that solely perceives the screenshots as input and performs human-like interactions (e.g., keyboard and mouse operations). Unlike prevailing agent frameworks that depend on heavily wrapped commercial models (e.g., GPT-4o) with expert-crafted prompts and workflows, UI-TARS is an end-to-end model that outperforms these sophisticated frameworks. Experiments demonstrate its superior performance: UI-TARS achieves SOTA performance in 10+ GUI agent benchmarks evaluating perception, grounding, and GUI task execution. Notably, in the OSWorld benchmark, UI-TARS achieves scores of 24.6 with 50 steps and 22.7 with 15 steps, outperforming Claude (22.0 and 14.9 respectively). In AndroidWorld, UI-TARS achieves 46.6, surpassing GPT-4o (34.5). UI-TARS incorporates several key innovations: (1) Enhanced Perception: leveraging a large-scale dataset of GUI screenshots for context-aware understanding of UI elements and precise captioning; (2) Unified Action Modeling, which standardizes actions into a unified space across platforms and achieves precise grounding and interaction through large-scale action traces; (3) System-2 Reasoning, which incorporates deliberate reasoning into multi-step decision making, involving multiple reasoning patterns such as task decomposition, reflection thinking, milestone recognition, etc. (4) Iterative Training with Reflective Online Traces, which addresses the data bottleneck by automatically collecting, filtering, and reflectively refining new interaction traces on hundreds of virtual machines. Through iterative training and reflection tuning, UI-TARS continuously learns from its mistakes and adapts to unforeseen situations with minimal human intervention. We also analyze the evolution path of GUI agents to guide the further development of this domain.

*   **主要贡献**:
    *   提出了一个端到端的原生GUI智能体模型UI-TARS，无需依赖复杂的框架和提示工程。
    *   在多个GUI智能体基准测试中取得了SOTA（State-of-the-art）的性能。
    *   引入了增强感知、统一动作建模、系统-2推理和带反思的在线轨迹迭代训练等关键创新。

## 3. 开源代码

*   **GitHub仓库地址**: https://github.com/bytedance/UI-TARS
*   **Star数量**: 8.8k
*   **许可证**: Apache-2.0
*   **主要功能模块**: 该项目提供了模型的代码、部署指南、使用示例以及性能评估结果。

## 4. 技术架构

*   **模型架构**: UI-TARS-1.5基于一个强大的视觉语言模型，并集成了通过强化学习实现的先进推理能力。其核心架构包括：
    *   **增强感知**: 利用大规模GUI截图数据集，实现对UI元素的上下文感知理解和精确定位。
    *   **统一动作建模**: 将跨平台的操作标准化为统一的动作空间，通过大规模动作轨迹实现精确的 grounding 和交互。
    *   **系统-2推理**: 在多步决策中融入审慎的推理，包括任务分解、反思性思考、里程碑识别等多种推理模式。
*   **参数规模**: 7B (70亿)
*   **训练数据**: 模型使用了大规模的GUI截图数据集和动作轨迹进行训练。通过在数百个虚拟机上自动收集、过滤和反思性地优化新的交互轨迹，实现了迭代训练。
*   **核心技术创新**: 核心创新在于其端到端的原生代理设计，摆脱了对外部模型和复杂工作流的依赖，并通过迭代训练和反思调优，使模型能够从错误中学习并适应新情况。

## 5. 性能评测

UI-TARS在多个主流基准测试中表现出色，以下是部分结果：

**在线基准评估**

| 基准类型 | 基准 | UI-TARS-1.5 | OpenAI CUA | Claude 3.7 | 先前SOTA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **计算机使用** | OSWorld (100步) | **42.5** | 36.4 | 28 | 38.1 (200步) |
| | Windows Agent Arena (50步) | **42.1** | - | - | 29.8 |
| **浏览器使用** | WebVoyager | 84.8 | **87** | 84.1 | 87 |
| | Online-Mind2web | **75.8** | 71 | 62.9 | 71 |
| **手机使用** | Android World | **64.2** | - | - | 59.5 |

**Grounding能力评估**

| 基准 | UI-TARS-1.5 | OpenAI CUA | Claude 3.7 | 先前SOTA |
| :--- | :--- | :--- | :--- | :--- |
| ScreenSpot-V2 | **94.2** | 87.9 | 87.6 | 91.6 |
| ScreenSpotPro | **61.6** | 23.4 | 27.7 | 43.6 |

## 6. 适用场景

*   **支持的平台**: 桌面（Windows, Linux, macOS）、移动设备（Android模拟器）和Web浏览器。
*   **典型应用场景**: 可用于执行各种GUI任务，例如浏览器导航、办公软件交互、文件管理、移动应用操作、玩游戏等。

## 7. 优势与局限

*   **优势**:
    *   **卓越的性能**: 在多个基准测试中超越了包括GPT-4o和Claude在内的先前最先进模型。
    *   **端到端设计**: 作为一个独立的原生模型，它不依赖于外部商业模型或复杂的提示工程，简化了部署和使用。
    *   **强大的推理能力**: 集成了系统-2推理，使其能够在行动前进行思考，从而提高了在复杂任务中的表现和适应性。
    *   **持续学习**: 通过带反思的在线轨迹进行迭代训练，使其能够不断从错误中学习和改进。

*   **局限**:
    *   **滥用风险**: 由于其强大的GUI操作能力，包括成功通过CAPTCHA等身份验证挑战，存在被用于未经授权访问或自动化受保护内容的风险。
    *   **计算资源**: 仍然需要大量的计算资源，特别是在大规模任务或长时间游戏场景中。
    *   **幻觉问题**: 在模糊或不熟悉的环境中，可能会产生不准确的描述、错误识别GUI元素或采取次优操作。
    *   **模型规模**: 发布的UI-TARS-1.5-7B主要侧重于增强通用计算机使用能力，并未针对游戏场景进行特别优化。

## 8. 相关图片

*   架构图、性能对比图等图片可以在GitHub仓库的README文件中找到。
