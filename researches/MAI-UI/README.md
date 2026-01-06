# MAI-UI GUI 智能体模型深度调研报告

## 1. 模型概述

| 项目 | 内容 |
| --- | --- |
| **模型名称** | MAI-UI |
| **开发者/机构** | 阿里通义实验室 (Alibaba Tongyi Lab) |
| **发布时间** | 2025年12月 |
| **核心定位** | MAI-UI 是一个面向真实世界场景的全尺寸、端云协同的 GUI 智能体基座模型家族。其核心定位是解决现有 GUI 代理在真实部署中面临的挑战，包括原生用户交互的缺失、纯 UI 操作的局限性、缺乏实用的部署架构以及在动态环境中的脆弱性。 |

## 2. 论文信息

| 项目 | 内容 |
| --- | --- |
| **论文标题** | MAI-UI Technical Report: Real-World Centric Foundation GUI Agents |
| **论文链接** | [https://arxiv.org/abs/2512.22047](https://arxiv.org/abs/2512.22047) |
| **英文摘要** | The development of GUI agents could revolutionize the next generation of human-computer interaction. Motivated by this vision, we present MAI-UI, a family of foundation GUI agents spanning the full spectrum of sizes, including 2B, 8B, 32B, and 235B-A22B variants. We identify four key challenges to realistic deployment: the lack of native agent-user interaction, the limits of UI-only operation, the absence of a practical deployment architecture, and brittleness in dynamic environments. MAI-UI addresses these issues with a unified methodology: a self-evolving data pipeline that expands the navigation data to include user interaction and MCP tool calls, a native device-cloud collaboration system routes execution by task state, and an online RL framework with advanced optimizations to scale parallel environments and context length. MAI-UI establishes new state-of-the-art across GUI grounding and mobile navigation. On grounding benchmarks, it reaches 73.5% on ScreenSpot-Pro, 91.3% on MMBench GUI L2, 70.9% on OSWorld-G, and 49.2% on UI-Vision, surpassing Gemini-3-Pro and Seed1.8 on ScreenSpot-Pro. On mobile GUI navigation, it sets a new SOTA of 76.7% on AndroidWorld, surpassing UI-Tars-2, Gemini-2.5-Pro and Seed1.8. On MobileWorld, MAI-UI obtains 41.7% success rate, significantly outperforming end-to-end GUI models and competitive with Gemini-3-Pro based agentic frameworks. Our online RL experiments show significant gains from scaling parallel environments from 32 to 512 (+5.2 points) and increasing environment step budget from 15 to 50 (+4.3 points). Finally, the native device-cloud collaboration system improves on-device performance by 33%, reduces cloud model calls by over 40%, and preserves user privacy. |

## 3. 开源代码

| 项目 | 内容 |
| --- | --- |
| **GitHub 仓库** | [https://github.com/Tongyi-MAI/MAI-UI](https://github.com/Tongyi-MAI/MAI-UI) |
| **Star 数量** | 1.2k (截至 2026年1月) |
| **许可证** | Apache-2.0 |

## 4. 技术架构

MAI-UI 采用了一套统一的方法论来应对真实世界部署的挑战，其技术架构主要包含三个核心部分：

1.  **自进化数据管线 (Self-Evolving Data Pipeline)**: 该管线将传统的导航数据扩展，融入了用户交互和 MCP (Model-as-a-Tool) 工具调用，从而生成更丰富、更贴近真实场景的训练数据。
2.  **端云协同系统 (Device-Cloud Collaboration System)**: 这是一个原生的协同系统，能够根据任务状态动态路由执行路径。简单的任务可以直接在端侧模型上完成，保护用户隐私并降低成本；复杂的任务则可以调用云端的大模型来完成，保证了任务的成功率。该系统能将端侧性能提升33%，并减少超过40%的云端模型调用。
3.  **在线强化学习框架 (Online RL Framework)**: 采用先进的优化技术，能够扩展并行环境的规模和上下文长度，从而持续提升模型的性能。

**模型规模**: MAI-UI 提供从端到云的全尺寸模型，包括 2B, 8B, 32B, 和 235B-A22B 等多个版本，以适应不同的部署需求。

**训练数据**: 模型主要使用通过自进化数据管线生成的数据进行训练，这些数据包含了UI导航、用户交互和工具调用等多种类型的交互信息。

## 5. 性能评测

MAI-UI 在多个主流的 GUI 基础能力和导航能力基准上取得了业界领先的性能。

| 基准测试 | MAI-UI 得分 | 对比 |
| --- | --- | --- |
| **ScreenSpot-Pro** | 73.5% | 超越 Gemini-3-Pro 和 Seed1.8 |
| **MMBench GUI L2** | 91.3% | SOTA |
| **OSWorld-G** | 70.9% | SOTA |
| **UI-Vision** | 49.2% | SOTA |
| **AndroidWorld** | 76.7% | 超越 UI-Tars-2, Gemini-2.5-Pro, Seed1.8 |
| **MobileWorld** | 41.7% | 显著优于其他端到端模型 |

## 6. 适用场景

| 项目 | 内容 |
| --- | --- |
| **支持平台** | 主要支持 **移动端 (Android)** 平台。 |
| **典型应用场景** | MAI-UI 旨在成为“真实手机生活”的通用 GUI 智能体，能够处理各种复杂的日常任务和工作流程，例如：<br>- **日常生活**: 跨应用购物比价、添加购物车、导航、查询信息等。<br>- **办公场景**: 管理日历、处理会议、在企业通信软件中同步信息等。<br>- **多模态交互**: 利用图片在电商平台进行搜索。 |

## 7. 优势与局限

### 优势

1.  **全尺寸模型覆盖**: 提供从2B到235B的全尺寸模型，实现了端云协同，兼顾了性能、成本和隐私。
2.  **强大的真实世界任务能力**: 通过自进化数据管线和在线强化学习，模型在 MobileWorld 等真实世界基准上表现出色，能够完成复杂的跨应用任务。
3.  **原生用户交互与工具调用**: 模型原生支持与用户进行多轮交互（如询问澄清），并能调用 MCP 工具，极大地扩展了其能力边界，超越了纯 UI 操作的限制。
4.  **卓越的基准性能**: 在 ScreenSpot, AndroidWorld 等多个权威学术基准上刷新了记录，证明了其在 GUI 理解和导航方面的领先水平。

### 局限

1.  **平台局限性**: 目前的资料主要集中在 Android 平台，对于 iOS、桌面或 Web 平台的支持情况尚不明确。
2.  **对新应用的泛化能力**: 尽管模型在多个开源应用上表现优异，但对于未在训练数据中出现过的、全新的商业闭源应用的泛化能力仍有待进一步验证。
3.  **长时程任务的稳定性**: 与所有自主代理一样，在执行需要非常多步骤的超长时程任务时，可能会面临稳定性和任务漂移的挑战。

## 8. 更多深度文档

本目录下还包含以下深度调研文档：

| 文档名称 | 描述 |
| --- | --- |
| [code-analysis.md](./code-analysis.md) | MAI-UI 深度代码解构，分析核心模块和源码实现 |
| [model-features.md](./model-features.md) | MAI-UI 模型层面特点深度分析，包括全尺寸模型家族、自进化数据管线、在线强化学习框架等 |
| [deployment-guide.md](./deployment-guide.md) | MAI-UI 工程化部署全流程指南，从环境准备到客户端集成 |

## 9. 相关图片 URL

*   性能对比图: [https://tongyi-mai.github.io/MAI-UI/main_results.png](https://tongyi-mai.github.io/MAI-UI/main_results.png)
*   数据管线图: [https://tongyi-mai.github.io/MAI-UI/gui_grounding_data.png](https://tongyi-mai.github.io/MAI-UI/gui_grounding_data.png)
*   RL 框架图: [https://tongyi-mai.github.io/MAI-UI/rl_framework.png](https://tongyi-mai.github.io/MAI-UI/rl_framework.png)
*   端云协同架构图: [https://tongyi-mai.github.io/MAI-UI/collaboration_arch.png](https://tongyi-mai.github.io/MAI-UI/collaboration_arch.png)
