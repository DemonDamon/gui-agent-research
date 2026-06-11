# Mobile-Agent-v3.5: Multi-platform Fundamental GUI Agents

> 作者：Damon Li | 更新日期：2026年6月11日

## 1. 概述

Mobile-Agent-v3.5 是由阿里通义团队于 2026 年 2 月发布的多平台基础 GUI 智能体框架，其核心驱动模型为 **GUI-Owl-1.5**。该框架旨在解决现有 GUI 智能体在跨平台协作、实时交互以及长视野任务训练效率等方面的挑战。GUI-Owl-1.5 提供了多种尺寸（2B/4B/8B/32B/235B）的 instruct 和 thinking 变体，全面支持桌面端、移动端、浏览器等多种平台，实现了端云协同（cloud-edge collaboration）和实时交互能力 [1]。

## 2. 核心技术与方法

Mobile-Agent-v3.5 和 GUI-Owl-1.5 引入了多项关键创新，以全面提升智能体的基础能力：

### 2.1 混合数据飞轮 (Hybrid Data Flywheel)
为了提高数据收集的效率和质量，研究团队构建了一个基于模拟环境和云端沙箱环境相结合的数据管道。这种混合架构不仅能够快速生成大量的 UI 理解和轨迹生成数据，还能确保数据在真实复杂场景下的有效性。

### 2.2 智能体能力的统一增强 (Unified Enhancement of Agent Capabilities)
GUI-Owl-1.5 采用了一种统一的思维合成管道（thought-synthesis pipeline）来增强模型的推理能力。特别值得注意的是，该模型重点强化了关键的智能体能力，包括工具/MCP（Model Context Protocol）的使用、记忆机制以及多智能体适配能力。

### 2.3 多平台环境 RL 扩展 (Multi-platform Environment RL Scaling)
针对多平台冲突和长视野任务训练效率低下的挑战，研究团队提出了一种全新的环境强化学习算法——**MRPO**。该算法有效解决了在多样化 GUI 环境中进行强化学习时面临的探索空间巨大和奖励稀疏问题。

## 3. 关键成果与对比

GUI-Owl-1.5 在开源模型中展现出了统治级的性能，在超过 20 个 GUI 基准测试中取得了 SOTA 结果：

| 任务类型 | 基准测试 | 性能得分 |
| :--- | :--- | :--- |
| **GUI 自动化** | OSWorld | 56.5 |
| | AndroidWorld | 71.6 |
| | WebArena | 48.4 |
| **Grounding** | ScreenSpotPro | 80.3 |
| **工具调用** | OSWorld-MCP | 47.6 |
| | MobileWorld | 46.8 |
| **记忆与知识** | GUI-Knowledge Bench | 75.5 |

这些结果表明，GUI-Owl-1.5 不仅在传统的点击、滑动等基础操作上表现出色，在更高级的工具调用和知识推理任务上也具备强大的能力。

## 4. 代码与资源

- **论文链接**: [arXiv:2602.16855](https://arxiv.org/abs/2602.16855)
- **开源代码**: [X-PLUG/MobileAgent](https://github.com/X-PLUG/MobileAgent)
- **在线 Demo**: 提供基于云端沙箱的在线演示体验

## 5. 影响与展望

Mobile-Agent-v3.5 和 GUI-Owl-1.5 的发布，标志着 GUI 智能体向着“全能型、跨平台、强推理”的方向迈出了坚实的一步。其引入的混合数据飞轮和 MRPO 算法为解决 GUI 智能体训练中的数据瓶颈和 RL 效率问题提供了新的思路。未来，随着端云协同架构的进一步成熟，我们有望看到更多具备实时交互能力的复杂 GUI 智能体应用落地。

## 6. 参考资料

[1] [Mobile-Agent-v3.5: Multi-platform Fundamental GUI Agents](https://arxiv.org/abs/2602.16855)
