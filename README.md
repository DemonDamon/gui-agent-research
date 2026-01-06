# GUI Agent 技术深度调研

> **作者**: Damon Li  
> **更新日期**: 2026年1月6日

本仓库包含对主流 GUI 智能体（GUI Agent）技术的深度调研报告，涵盖学术论文分析、开源代码解读、技术架构对比等内容。

## 📚 调研内容概览

### 一、主流开源 GUI Agent 方案对比

| 方案/模型 | 开发者 | 核心优势 | 核心劣势 | 基础模型 | 训练数据 | 训练方法 | 模型尺寸 |
|---|---|---|---|---|---|---|---|
| **UI-TARS** | 字节跳动 | 单模型端到端，性能高 | 依赖自建数据集，复现难 | Qwen2-VL-7B | 自建 GUI 数据集 | SFT | 7B |
| **GELab-Zero** | 阶跃星辰 | 零样本，无需训练，隐私保护 | 性能依赖基础模型 | Qwen3-VL-4B | 无需训练 | 零样本 | 4B |
| **MAI-UI** | 阿里通义 | 全尺寸端云协同，自进化数据管线 | 架构复杂，部署成本高 | Qwen2.5-VL | 自建+在线 RL | SFT + RL | 2B/8B/32B/235B |
| **AgentCPM-GUI** | 清华+面壁 | 中文应用适配好，强化微调 | 依赖特定数据集 | MiniCPM-V | CAGUI (自建) | SFT + RFT | 8B |
| **AutoGLM** | 智谱 AI | 模块化，易于扩展，MIT 协议 | 性能非最优 | GLM-4V | 自建+RL | SFT + RL | 9B |
| **GUI-Owl** | 阿里通义 | 强大的视觉语言模型 | 依赖 Mobile-Agent-v3 框架 | Qwen2.5-VL | 自建 GUI 数据集 | SFT | 7B/32B |
| **Step-GUIEdge** | 阶跃星辰 | 端侧部署，轻量化 | 性能受限 | Step-1.5V | 自建数据集 | SFT | 4B/8B |
| **MobiAgent** | 上交 IPADS | AgentRR 加速，可定制性强 | 依赖多个组件 | Qwen2.5-VL | MobiMind (自建) | SFT | 4B/7B/8B |

**注**：**Mobile-Agent-v3** 是一个多智能体**框架**，它使用 **GUI-Owl** 作为其核心**模型**。因此，在选型时，应将两者视为一个整体方案。

### 二、性能评测对比

| 模型 | ScreenSpot-Pro | AndroidWorld | OSWorld | MobiFlow |
|---|---|---|---|---|
| UI-TARS-7B | 61.6% | 46.6% | 24.6% | - |
| MAI-UI-8B | 73.5% | 76.7% | - | - |
| AgentCPM-GUI | - | 90.2% (AC-Low) | - | - |
| GUI-Owl-32B | 68.2% | 59.7% | 24.5% | - |
| MobiAgent-8B | - | - | - | 78.3% |

### 三、专题深度调研

| 模型/框架名称 | 调研报告 | 代码解构 |
|---|---|---|
| **UI-TARS-7B** | [查看报告](./researches/UI-TARS-7B/README.md) | [代码分析](./researches/UI-TARS-7B/code-analysis.md) |
| **GELab-Zero** | [查看报告](./researches/GELab-Zero/README.md) | [代码分析](./researches/GELab-Zero/code-analysis.md) |
| **MAI-UI** | [查看报告](./researches/MAI-UI/README.md) | [代码分析](./researches/MAI-UI/code-analysis.md) |
| **AgentCPM-GUI** | [查看报告](./researches/AgentCPM-GUI/README.md) | [代码分析](./researches/AgentCPM-GUI/code-analysis.md) |
| **AutoGLM** | [查看报告](./researches/AutoGLM-Phone-9B/README.md) | [代码分析](./researches/autoglm/06-source-code-analysis.md) |
| **GUI-Owl & Mobile-Agent-v3** | [查看报告](./researches/Mobile-Agent/README.md) | [代码分析](./researches/Mobile-Agent/code-analysis.md) |
| **Step-GUIEdge** | [查看报告](./researches/Step-GUIEdge/README.md) | [代码分析](./researches/Step-GUIEdge/code-analysis.md) |
| **MobiAgent** | [查看报告](./researches/MobiAgent/README.md) | [代码分析](./researches/MobiAgent/code-analysis.md) |

## 🏗️ 项目结构

```
gui-agent-research/
├── README.md                    # 本文件
├── researches/                  # 调研报告目录
│   ├── UI-TARS-7B/             # UI-TARS-7B 模型调研
│   ├── GELab-Zero/             # GELab-Zero 模型调研
│   ├── MAI-UI/                 # MAI-UI 模型调研
│   ├── AgentCPM-GUI/           # AgentCPM-GUI 模型调研
│   ├── AutoGLM-Phone-9B/       # AutoGLM 模型调研
│   ├── Mobile-Agent/           # GUI-Owl & Mobile-Agent-v3 调研
│   ├── Step-GUIEdge/           # Step-GUIEdge 模型调研
│   ├── MobiAgent/              # MobiAgent 模型调研
│   └── ...
└── presentation/               # 技术演示 PPT
```

## 📖 参考文献

1. [UI-TARS: Pioneering Automated GUI Interaction with Native Agents](https://arxiv.org/abs/2501.12326)
2. [AutoGLM: Autonomous Foundation Agents for GUIs](https://arxiv.org/abs/2411.00820)
3. [MAI-UI Technical Report: Real-World Centric Foundation GUI Agents](https://arxiv.org/abs/2512.22047)
4. [AgentCPM-GUI: Building Mobile-Use Agents with Reinforcement Fine-Tuning](https://arxiv.org/abs/2506.01391)
5. [Step-GUI Technical Report](https://arxiv.org/abs/2512.15431)
6. [GUI-Owl: Advancing Native GUI Agents with Unified Action Modeling](https://arxiv.org/abs/2507.00076)
7. [Mobile-Agent-v3: Foundational Agents for GUI Automation](https://arxiv.org/abs/2508.15144)
8. [MobiAgent: A Customizable Mobile Agent with Accelerated GUI Grounding](https://arxiv.org/abs/2509.12345)

## 📜 许可证

本项目采用 MIT 许可证。

## ☁️ 云手机落地场景选型建议

### 一、选型问卷调查表

在为客户选择合适的 GUI Agent 方案之前，可以通过以下问卷了解其核心需求：

| 维度 | 问题 | 选项 | 备注 |
|---|---|---|---|
| **1. 性能要求** | 您对任务成功率的最低要求是多少？ | A. >90% (追求极致) <br> B. 70-90% (业界领先) <br> C. 50-70% (可用即可) | 决定是否需要 SOTA 模型 |
| **2. 成本预算** | 您对模型推理成本的敏感度如何？ | A. 不敏感 (可接受云端大模型) <br> B. 较敏感 (希望端云协同) <br> C. 非常敏感 (希望纯端侧) | 决定模型尺寸和部署方式 |
| **3. 隐私安全** | 您对数据隐私的要求有多高？ | A. 极高 (数据不能离开本地) <br> B. 较高 (敏感数据本地处理) <br> C. 一般 (可接受云端处理) | 决定是否需要端侧或私有化部署 |
| **4. 任务类型** | 您的主要任务场景是？ | A. 跨应用复杂任务 <br> B. 单应用内重复操作 <br> C. 特定领域的自动化 | 决定是否需要强大的规划能力 |
| **5. 开发能力** | 您的团队二次开发能力如何？ | A. 强 (可深入定制框架) <br> B. 中 (可基于 API 开发) <br> C. 弱 (希望开箱即用) | 决定选择框架型还是模型型方案 |
| **6. 中文支持** | 您的应用是否以中文为主？ | A. 是 <br> B. 否 | 决定是否需要专门的中文优化模型 |

### 二、选型建议

| 客户画像 | 推荐方案 | 理由 |
|---|---|---|
| **追求极致性能，预算充足** | **MAI-UI (235B)** | 业界 SOTA，性能最强，但成本最高。 |
| **中文应用自动化，成功率优先** | **AgentCPM-GUI** | 专门针对中文应用优化，评测分数高。 |
| **需要端侧部署，保护隐私** | **Step-GUIEdge / GELab-Zero** | 轻量化模型，可在本地运行，无需数据上云。 |
| **需要灵活定制和二次开发** | **MobiAgent / Mobile-Agent-v3** | 模块化、可定制的框架，适合有研发能力的团队。 |
| **希望快速验证，开箱即用** | **AutoGLM** | MIT 协议，提供完整的手机端 Demo，上手快。 |
| **性能与成本均衡** | **MAI-UI (8B) / UI-TARS (7B)** | 性能接近大模型，但推理成本更低，是性价比较高的选择。 |

### 三、注意事项

1. **评测数据的局限性**：公开评测集与真实场景存在差异，建议在客户的真实业务场景中进行 POC 测试。
2. **环境依赖**：不同方案对 Android/HarmonyOS 版本、ADB/HDC 工具链有不同要求，需提前确认。
3. **模型授权**：部分模型（如 AutoGLM）采用宽松的 MIT 协议，而其他模型可能有限制，商用前需确认。
4. **工程化挑战**：将 Agent 部署到大规模云手机集群，需要考虑任务调度、状态同步、异常监控等一系列工程问题。
