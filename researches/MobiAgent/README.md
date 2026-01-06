# MobiAgent 深度调研报告

> **作者**: Damon Li  
> **更新日期**: 2026年1月6日

## 1. 项目概述

MobiAgent 是一个功能强大且可定制的移动智能体系统，由上海交通大学 IPADS 实验室开发。它旨在提供一个完整的移动端智能体解决方案，涵盖了从模型、加速框架到评测基准的全链路。该项目在 GitHub 上开源，并提供了详细的文档和示例。

### 1.1 核心组件

MobiAgent 系统包含三大核心组件：

| 组件 | 描述 |
|---|---|
| **MobiMind** | 一个专为移动端设计的智能体模型家族，包含多个不同规模和功能的模型。 |
| **AgentRR** | 一个创新的智能体加速框架，通过记录和回放（Record & Replay）机制来提升任务执行效率。 |
| **MobiFlow** | 一个基于有向无环图（DAG）的移动智能体评测基准，用于离线验证任务执行的正确性。 |

### 1.2 系统架构

MobiAgent 的系统架构设计清晰，各组件协同工作，形成一个完整的闭环系统。

![MobiAgent 架构图](images/arch.png)

该架构展示了从用户输入到任务执行，再到评测和优化的全过程。MobiMind 模型负责理解用户意图并做出决策，AgentRR 框架负责加速重复性任务，而 MobiFlow 则为整个系统的性能提供量化评估。

## 2. MobiMind 模型家族

MobiMind 是 MobiAgent 项目的核心，包含一系列针对不同场景优化的模型。这些模型在 HuggingFace 上开源，方便研究人员和开发者使用。

### 2.1 模型列表

| 模型名称 | 参数规模 | 类型 | 特点 |
|---|---|---|---|
| MobiMind-Decider-7B | 8B | Image-Text-to-Text | 负责决策 |
| MobiMind-Grounder-3B | 4B | Image-Text-to-Text | 负责定位 |
| MobiMind-Grounder-7B | 8B | Image-Text-to-Text | 负责定位 |
| MobiMind-Mixed-7B | 8B | Image-Text-to-Text | 混合决策和定位 |
| MobiMind-Mixed-4B-1031 | 4B | Image-Text-to-Text | 混合决策和定位 |
| MobiMind-Reasoning-4B-1208 | 4B | - | 增强推理能力 |
| MobiMind-Reasoning-4B-1208-AWQ | 4B (量化) | - | 量化版本，适合端侧部署 |

### 2.2 性能评测

MobiAgent 在多个主流基准上取得了优异的性能，尤其是在 AgentRR 加速框架的加持下，重复任务的执行效率显著提升。

![评测结果1](images/result1.png)
![评测结果2](images/result2.png)
![评测结果3](images/result3.png)

AgentRR 框架的性能提升尤为突出，能够在重复任务中实现高达 90% 以上的加速效果。

![AgentRR 性能](images/result_agentrr.png)

## 3. AgentRR 加速框架

AgentRR (Agent Record & Replay) 是 MobiAgent 的一大创新。它通过记录首次任务执行时的成功动作序列，并在后续遇到相似任务时进行回放，从而大幅减少了模型的调用次数，降低了延迟和成本。

### 3.1 核心思想

- **记录 (Record)**: 在首次执行任务时，记录下每一步的 UI 状态、模型决策和执行动作，形成一个“动作树”（Action Tree）。
- **回放 (Replay)**: 当再次遇到相似任务时，通过匹配当前 UI 状态和任务描述，在动作树中查找缓存的动作序列，并直接执行，无需再次调用大模型。

### 3.2 视频演示

下面的视频展示了 AgentRR 在实际任务中的加速效果。左侧是首次执行任务，右侧是第二次执行，可以看到明显的加速。

[AgentRR Demo 视频](https://github.com/user-attachments/assets/ef5268a2-2e9c-489c-b8a7-828f00ec3ed1)

## 4. MobiFlow 评测基准

MobiFlow 是一个基于 DAG 的离线评测框架，它通过定义任务的“里程碑”节点和它们之间的依赖关系，来判断一次任务执行是否成功。

### 4.1 核心特性

- **多层级条件检查**: 支持文本匹配、正则表达式、UI 状态、图标检测、OCR、LLM 推理等多种验证方式。
- **双语义依赖**: 支持 `deps` (AND 语义) 和 `next` (OR 语义)，可以灵活定义复杂的任务流程。
- **路径感知验证**: 智能的帧分配机制，避免了多路径任务中可能出现的验证冲突。

## 5. 部署与使用

MobiAgent 提供了两种使用方式：

1.  **MobiAgent APP**: 用户可以直接下载安装 Android 应用，快速体验 MobiAgent 的功能。
2.  **Python 脚本**: 开发者可以通过 Python 脚本，利用 ADB (Android Debug Bridge) 来控制手机，并与 MobiAgent 系统进行交互。

### 5.1 工程化部署流程

1.  **环境准备**: 创建 Python 虚拟环境并安装依赖。
2.  **模型部署**: 使用 vLLM 部署 MobiMind 模型服务。
3.  **设备连接**: 通过 USB 连接 Android 设备并开启 ADB 调试。
4.  **启动 Agent Runner**: 运行 `runner/mobiagent/mobiagent.py` 脚本，指定模型服务地址和任务文件。

### 5.2 内存系统

MobiAgent 还支持三种内存系统来增强智能体的性能：

- **用户画像内存 (User Profile Memory)**: 提供个性化的上下文信息。
- **经验内存 (Experience Memory)**: 检索和使用过去相似任务的执行经验。
- **动作内存 (Action Memory / AgentRR)**: 缓存和重用成功的动作序列。

## 6. 参考文献

1.  [MobiAgent: A Systematic Framework for Customizable Mobile Agents](https://arxiv.org/abs/2509.00531)
2.  [Beyond Training: Enabling Self-Evolution of Agents with MOBIMEM](https://arxiv.org/abs/2512.15784)
3.  [MobiAgent GitHub Repository](https://github.com/IPADS-SAI/MobiAgent)
4.  [MobiMind HuggingFace Collection](https://huggingface.co/collections/IPADS-SAI/mobimind-68b2aad150ccafd9d9e10e4d)
