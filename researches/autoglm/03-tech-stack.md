# AutoGLM 技术栈拆解

**发布日期**: 2025年12月16日

**作者**: Damon Li

---

## 1. 概述

AutoGLM 的成功实现，得益于一个精心设计和整合的综合技术栈。该技术栈融合了最新的大型多模态模型、先进的训练策略以及稳健的系统工程实践。本报告将对 AutoGLM 的核心技术栈进行拆解，分析其在模型、训练和部署等层面的关键技术选型。

## 2. 模型层 (Model Layer)

模型层是 AutoGLM 的核心，负责感知、理解和规划。

| 技术组件 | 详细说明 |
| :--- | :--- |
| **基础语言模型** | 基于智谱 AI 的 **ChatGLM** 模型家族，特别是 GLM-4-9B 版本。这为智能体提供了强大的自然语言理解、推理和规划能力 [1]。 |
| **大型多模态模型 (LMM)** | AutoGLM 的核心是大型多模态模型，它能够同时处理文本和视觉输入（即屏幕截图）。这使得智能体能够像人类一样“看到”和“理解”GUI 界面，识别图标、按钮、文本等元素。 |
| **高分辨率视觉输入** | 借鉴了 CogAgent 等研究的经验，AutoGLM 强调高分辨率视觉输入的重要性。高分辨率图像对于精确的元素定位至关重要，特别是在使用 Set-of-Marks (SoM) 等视觉定位技术时 [2]。 |

## 3. 训练层 (Training Layer)

训练层是 AutoGLM 实现能力进化和泛化的关键。由于 GUI 交互的轨迹数据非常稀缺，AutoGLM 采用了一套复杂的混合训练策略来克服这一挑战。

| 训练策略 | 目标与方法 |
| :--- | :--- |
| **预训练 (Pre-training)** | 在大规模互联网语料库上进行预训练，以注入基础的世界知识和语言能力。同时，利用弱监督信号（如网页中的交互元素）来初步培养模型的决策能力。 |
| **行为克隆 (Behavior Cloning)** | 使用高质量的专家演示轨迹进行监督微调 (Supervised Fine-tuning)。这是让模型从零开始学习 GUI 操作的基础步骤。然而，专家数据成本高昂且难以规模化，模型也容易产生“模仿”而非“理解”的问题。 |
| **课程学习 (Curriculum Learning)** | 采用从易到难的渐进式训练方案。例如，模型首先在单步任务上训练，然后逐步过渡到简单的多步任务，最后挑战长期的复杂任务。这种方法有助于模型稳定地构建复杂能力。 |
| **奖励建模 (Reward Modeling)** | 为了在没有明确规则的情况下进行强化学习，AutoGLM 需要构建一个通用的奖励模型。该模型能够评估智能体在开放世界任务中的表现，并提供反馈信号。这包括结果导向的奖励模型 (ORM) 和过程导向的奖励模型 (PRM)。 |
| **在线强化学习 (Online RL)** | 这是 AutoGLM 实现自我进化的核心。通过在真实或模拟环境中进行大量交互（Roll-outs），智能体在奖励模型的指导下不断优化其策略，特别是学习如何从错误中恢复。 |

## 4. 部署与执行层 (Deployment & Execution Layer)

部署与执行层负责将模型的决策转化为物理设备上的实际操作。

| 技术组件 | 详细说明 |
| :--- | :--- |
| **安卓调试桥 (ADB)** | 在 Android 平台上，AutoGLM 通过 ADB (Android Debug Bridge) 与设备进行通信和控制。这允许智能体执行点击、滑动、文本输入等底层操作。 |
| **浏览器插件** | 在 Web 平台上，AutoGLM 的能力被封装在一个浏览器插件（如青言浏览器插件）中，通过浏览器提供的扩展 API 来控制网页交互。 |
| **AccessibilityService** | 在 Android 端，为了实现更底层的系统控制和更广泛的应用兼容性，AutoGLM 利用了 Android 的无障碍服务 (AccessibilityService) 来捕获界面信息和模拟用户操作。 |
| **远程调试** | Open-AutoGLM 框架支持通过 WiFi 或网络进行远程 ADB 调试，这为开发者提供了极大的灵活性，无需 USB 连接即可进行开发和测试。 |

---

### 参考文献

[1] Liu, X., Qin, B., Liang, D., et al. (2024). *AutoGLM: Autonomous Foundation Agents for GUIs*. arXiv:2411.00820. [https://arxiv.org/abs/2411.00820](https://arxiv.org/abs/2411.00820)

[2] Yang, J., Zhang, H., Li, F., et al. (2023). *Set-of-Mark Prompting Unleashes Extraordinary Visual Grounding in GPT-4V*. arXiv:2310.11441. [https://arxiv.org/abs/2310.11441](https://arxiv.org/abs/2310.11441)
