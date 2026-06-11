# MobileGUI-RL: Advancing Mobile GUI Agent through Reinforcement Learning in Online Environment

> 作者：Damon Li | 更新日期：2026年6月11日

## 1. 概述

MobileGUI-RL 是由 Yucheng Shi 等人于 2025 年 7 月提出的一种可扩展的在线强化学习框架，专门用于在真实的在线环境中训练移动端 GUI 智能体。现有的大多数 GUI 智能体训练方法依赖于离线环境和预先收集的轨迹数据。这种离线方法不仅限制了模型的可扩展性，容易导致模型对特定 UI 模板的过拟合，而且在面对未见过的环境时，其策略往往显得非常脆弱。MobileGUI-RL 旨在通过在线环境中的强化学习，打破这些局限，赋予智能体更强的泛化能力和鲁棒性 [1]。

## 2. 核心技术与方法

MobileGUI-RL 框架包含两个关键组件，共同解决了在线 GUI 强化学习中的挑战：

### 2.1 基于自探索的课程学习任务合成
在在线环境中，获取高质量的奖励信号和合适的训练任务是一大难题。MobileGUI-RL 通过智能体的自我探索（self-exploration）和过滤机制，自动合成一个由易到难的“可学习任务课程”（curriculum of learnable tasks）。这种机制使得智能体能够从简单的交互开始，逐步掌握复杂的长视野任务，有效缓解了强化学习初期的冷启动问题。

### 2.2 难度自适应的 ADAGRPO 算法
框架的核心是 Difficulty-ADAptive GRPO (ADAGRPO) 算法。该算法对标准的 GRPO 进行了针对 GUI 导航的适配：
- **难度自适应的正向回放与失败课程过滤**：根据任务难度动态调整训练策略，使模型能够适应不同难度的任务。
- **轨迹感知的优势计算**：在计算优势函数时，充分考虑了 GUI 交互轨迹的序列特征。
- **复合奖励机制**：引入了最短路径奖励调整策略，在多轮智能体任务中，根据任务长度重塑奖励。这种复合奖励机制不仅关注任务是否成功，还兼顾了执行效率（即步数的最优化）。

## 3. 关键成果与对比

研究团队将 MobileGUI-RL 框架应用于两个开源模型：Qwen2.5-VL-7B-Instruct 和 GLM-4.1V-9B-Base。实验结果表明，该框架在多个在线移动智能体基准测试中取得了持续的性能提升：

| 模型 | AndroidWorld 成功率 | AndroidLab 成功率 |
| :--- | :--- | :--- |
| **MobileRL-9B** (基于 GLM-4.1V-9B) | **80.2%** (SOTA) | **53.6%** (SOTA) |

这些结果证明，通过结合阶段性推理预热和难度自适应的在线 RL，MobileGUI-RL 能够显著提高样本效率，稳定 RL 训练过程，并在多样化的移动应用和任务中生成强大的性能。

## 4. 代码与资源

- **论文链接**: [arXiv:2507.05720](https://arxiv.org/abs/2507.05720)
- **开源代码**: [THUDM/MobileRL](https://github.com/THUDM/MobileRL)

## 5. 影响与展望

MobileGUI-RL 证明了在真实的在线环境中直接训练 GUI 智能体不仅是可行的，而且能够带来比离线训练更优越的泛化性能。其提出的 ADAGRPO 算法和复合奖励机制为解决 GUI 强化学习中的长视野和稀疏奖励问题提供了有效的工程实践。这为未来构建能够持续学习、自我进化的通用移动 GUI 助手奠定了基础。

## 6. 参考资料

[1] [MobileGUI-RL: Advancing Mobile GUI Agent through Reinforcement Learning in Online Environment](https://arxiv.org/abs/2507.05720)
