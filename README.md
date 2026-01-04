# GUI Agent 技术深度调研

> **作者**: Damon Li  
> **更新日期**: 2025年1月

本仓库包含对主流 GUI 智能体（GUI Agent）技术的深度调研报告，涵盖学术论文分析、开源代码解读、技术架构对比等内容。

## 📚 调研内容概览

### 一、主流开源 GUI Agent 模型调研

| 模型名称 | 开发者 | 参数规模 | 核心特点 | 调研报告 |
|---------|--------|---------|---------|---------|
| **UI-TARS-7B** | 字节跳动 | 7B | 原生GUI智能体架构，端到端设计 | [查看报告](./researches/UI-TARS-7B/README.md) |
| **GELab-Zero** | 阶跃星辰 | 4B | 端侧轻量模型，隐私保护 | [查看报告](./researches/GELab-Zero/README.md) |
| **MAI-UI** | 阿里通义 | 2B-235B | 全尺寸端云协同 | [查看报告](./researches/MAI-UI/README.md) |
| **AgentCPM-GUI** | 清华THUNLP | 8B | 中文应用适配，精准定位 | [查看报告](./researches/AgentCPM-GUI/README.md) |
| **AutoGLM** | 智谱AI | 9B | 手机端助手框架，MIT协议 | [查看报告](./researches/AutoGLM-Phone-9B/README.md) |
| **GUI-Owl** | 阿里通义 | 32B | 端到端多模态，全场景支持 | [查看报告](./researches/GUI-Owl/README.md) |
| **Step-GUIEdge** | 阶跃星辰 | 4B/8B | 首个支持手机部署的端侧模型 | [查看报告](./researches/Step-GUIEdge/README.md) |

### 二、专题深度调研

#### AutoGLM 深度解析（8篇报告）
- [01 - 项目概述与定位](./researches/autoglm/01-overview.md)
- [02 - 架构设计](./researches/autoglm/02-architecture.md)
- [03 - 技术栈拆解](./researches/autoglm/03-tech-stack.md)
- [04 - 多模态模型分析](./researches/autoglm/04-multimodal-model.md)
- [05 - 规划与决策算法](./researches/autoglm/05-planning-algorithm.md)
- [06 - 源码分析](./researches/autoglm/06-source-code-analysis.md)
- [07 - API 设计](./researches/autoglm/07-api-design.md)
- [08 - 性能评测](./researches/autoglm/08-performance-metrics.md)

#### 豆包手机深度解析（6篇报告）
- [01 - 产品概述](./researches/doubao/01-product-overview.md)
- [02 - 硬件集成深度解析](./researches/doubao/02-hardware-integration.md)
- [03 - 端侧AI技术（UI-TARS）](./researches/doubao/03-end-side-ai.md)
- [04 - 端云协同架构](./researches/doubao/04-cloud-collaboration.md)
- [05 - 中兴通讯的贡献](./researches/doubao/05-zte-contribution.md)
- [06 - 与AutoGLM的横向对比](./researches/doubao/06-comparison-with-autoglm.md)

#### 横向对比分析
- [AutoGLM vs 豆包手机 综合对比](./researches/comparison/00-comprehensive-comparison.md)

### 三、技术演示 PPT

本仓库还包含一份 28 页的技术演示 PPT，主题为"GUI 自主智能体技术深度调研"，采用国际化科技风格设计。

📂 **PPT 文件位置**: `./presentation/slides/`

## 🏗️ 项目结构

```
gui-agent-research/
├── README.md                    # 本文件
├── researches/                  # 调研报告目录
│   ├── UI-TARS-7B/             # UI-TARS-7B 模型调研
│   │   ├── README.md
│   │   └── images/
│   ├── GELab-Zero/             # GELab-Zero 模型调研
│   ├── MAI-UI/                 # MAI-UI 模型调研
│   ├── AgentCPM-GUI/           # AgentCPM-GUI 模型调研
│   ├── AutoGLM-Phone-9B/       # AutoGLM 模型调研
│   ├── GUI-Owl/                # GUI-Owl 模型调研
│   ├── Step-GUIEdge/           # Step-GUIEdge 模型调研
│   ├── autoglm/                # AutoGLM 专题深度调研
│   │   ├── 01-overview.md
│   │   ├── ...
│   │   └── diagrams/           # Mermaid 架构图
│   ├── doubao/                 # 豆包手机专题深度调研
│   │   ├── 01-product-overview.md
│   │   ├── ...
│   │   └── diagrams/
│   └── comparison/             # 横向对比分析
├── presentation/               # 技术演示 PPT
│   ├── slides/                 # HTML 幻灯片
│   └── *.png                   # 架构图素材
└── research_notes.md           # 调研笔记
```

## 📊 关键发现

### GUI Agent 技术路线对比

| 维度 | 软件定义路线 (AutoGLM) | 硬件定义路线 (豆包手机) |
|-----|----------------------|---------------------|
| **定位** | 通用 Agent 框架 | AI 原生终端 |
| **生态** | 开源开放 | 软硬一体（封闭） |
| **权限** | 应用层（Accessibility） | 系统层（Root-like） |
| **隐私** | 云端为主 | 端云协同 |
| **扩展性** | 极高 | 受限于硬件 |

### 主流模型性能对比

| 模型 | ScreenSpot-Pro | AndroidWorld | OSWorld |
|-----|---------------|--------------|---------|
| UI-TARS-7B | 61.6% | 46.6% | 24.6% |
| MAI-UI-8B | 73.5% | 76.7% | - |
| AgentCPM-GUI | - | 90.2% (AC-Low) | - |
| GUI-Owl-32B | 68.2% | 59.7% | 24.5% |

## 📖 参考文献

1. [UI-TARS: Pioneering Automated GUI Interaction with Native Agents](https://arxiv.org/abs/2501.12326)
2. [AutoGLM: Autonomous Foundation Agents for GUIs](https://arxiv.org/abs/2411.00820)
3. [MAI-UI Technical Report: Real-World Centric Foundation GUI Agents](https://arxiv.org/abs/2512.22047)
4. [AgentCPM-GUI: Building Mobile-Use Agents with Reinforcement Fine-Tuning](https://arxiv.org/abs/2506.01391)
5. [Step-GUI Technical Report](https://arxiv.org/abs/2512.15431)
6. [GUI-Owl: Advancing Native GUI Agents with Unified Action Modeling](https://arxiv.org/abs/2507.00076)

## 📜 许可证

本项目采用 MIT 许可证。

---

**如有问题或建议，欢迎提交 Issue 或 Pull Request！**
