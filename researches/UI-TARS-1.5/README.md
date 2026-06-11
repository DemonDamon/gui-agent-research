# UI-TARS-1.5: Pioneering Automated GUI Interaction with Native Agents

> 作者：Damon Li | 更新日期：2026年6月11日

## 1. 概述

UI-TARS-1.5 是字节跳动 Seed 团队于 2025 年 4 月发布的开源多模态 GUI 智能体模型，建立在强大的视觉语言模型基础之上。作为 UI-TARS 的重大升级版本，UI-TARS-1.5 的核心突破在于集成了强化学习（Reinforcement Learning）以实现高级推理能力。该模型能够在执行动作前通过“思考”过程进行推理（reasoning before action），从而显著提升了其在虚拟世界中执行多样化任务的性能和适应性，特别是在推理时缩放（inference-time scaling）方面表现优异 [1]。

## 2. 核心技术与方法

UI-TARS-1.5 延续了前代模型的原生智能体架构，但在训练范式上进行了重大革新：

### 2.1 强化学习增强的推理能力
模型引入了类似 R1 的强化学习范式，使得智能体在面对复杂的 GUI 任务时，不再是简单的“观察-反应”模式，而是转变为“观察-思考-行动”的审慎推理模式。这种机制允许模型在输出最终动作前，生成一段内部的思维链（Chain-of-Thought），用于分析当前界面状态、评估任务目标并规划后续步骤。

### 2.2 推理时缩放（Inference-Time Scaling）
得益于强化学习带来的推理能力，UI-TARS-1.5 展现出了强大的推理时缩放特性。这意味着在面对更困难的任务时，模型可以通过分配更多的计算资源（即生成更长的思考过程）来提高任务成功率，这与传统模型仅依赖模型参数规模缩放有着本质区别。

### 2.3 跨平台泛化
模型在设计上保持了对多种虚拟环境的兼容性，能够有效处理桌面端、移动端以及 Web 端的 GUI 交互任务，展现出强大的跨平台泛化能力。

## 3. 关键成果与对比

UI-TARS-1.5 在多个标准的 GUI 自动化和 Grounding 基准测试中取得了 SOTA（State-of-the-Art）级别的结果，证明了其强大的推理能力和相较于前代模型的显著改进：

| 基准测试 | 平台/领域 | 表现 |
| :--- | :--- | :--- |
| OSWorld | 桌面端综合 | SOTA |
| Windows Agent Arena | Windows 系统 | SOTA |
| WebVoyager | Web 导航 | SOTA |
| AndroidWorld | 移动端综合 | SOTA |
| ScreenSpot-V2/Pro | GUI Grounding | SOTA |

此外，UI-TARS-1.5 在交互轮数增加时展现出了极强的可扩展性和稳定性，证明了其鲁棒的设计能够有效应对长视野（long-horizon）的 GUI 任务。

## 4. 代码与资源

- **官方主页**: [Introducing UI-TARS-1.5](https://seed.bytedance.com/en/ui-tars)
- **开源代码**: [bytedance/ui-tars](https://github.com/bytedance/ui-tars) (包含 UI-TARS-desktop)
- **模型权重**: [ByteDance-Seed/UI-TARS-1.5-7B](https://huggingface.co/ByteDance-Seed/UI-TARS-1.5-7B) (HuggingFace)

## 5. 影响与展望

UI-TARS-1.5 的发布标志着 GUI 智能体正式迈入“推理增强”时代。通过将强化学习引入 GUI 交互领域，它不仅提升了模型在复杂任务上的成功率，更为未来的基础模型推理能力提升提供了一个极具价值的原型。未来，我们有望看到这种结合了视觉理解、动作执行与深度推理的范式被广泛应用于更复杂的现实世界自动化场景中。

## 6. 参考资料

[1] [Introducing UI-TARS-1.5 - Bytedance Seed](https://seed.bytedance.com/en/ui-tars)
