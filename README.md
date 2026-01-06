# GUI Agent 技术深度调研

> **作者**: Damon Li  
> **更新日期**: 2026年1月

本仓库包含对主流 GUI 智能体（GUI Agent）技术的深度调研报告，涵盖学术论文分析、开源代码解读、技术架构对比等内容。

## 📚 调研内容概览

### 一、主流开源 GUI Agent 模型调研

| 模型名称 | 开发者 | 参数规模 | 核心特点 | 调研报告 | 代码解构 |
|---------|--------|---------|---------|---------|---------|
| **UI-TARS-7B** | 字节跳动 | 7B | 原生GUI智能体架构，端到端设计 | [查看报告](./researches/UI-TARS-7B/README.md) | [代码分析](./researches/UI-TARS-7B/code-analysis.md) |
| **GELab-Zero** | 阶跃星辰 | 4B | 端侧轻量模型，隐私保护 | [查看报告](./researches/GELab-Zero/README.md) | [代码分析](./researches/GELab-Zero/code-analysis.md) |
| **MAI-UI** | 阿里通义 | 2B-235B | 全尺寸端云协同 | [查看报告](./researches/MAI-UI/README.md) | [代码分析](./researches/MAI-UI/code-analysis.md) |
| **AgentCPM-GUI** | 清华THUNLP | 8B | 中文应用适配，精准定位 | [查看报告](./researches/AgentCPM-GUI/README.md) | [代码分析](./researches/AgentCPM-GUI/code-analysis.md) |
| **AutoGLM** | 智谱AI | 9B | 手机端助手框架，MIT协议 | [查看报告](./researches/AutoGLM-Phone-9B/README.md) | [代码分析](./researches/autoglm/06-source-code-analysis.md) |
| **GUI-Owl** | 阿里通义 | 32B | 端到端多模态，全场景支持 | [查看报告](./researches/GUI-Owl/README.md) | [代码分析](./researches/GUI-Owl/code-analysis.md) |
| **Step-GUIEdge** | 阶跃星辰 | 4B/8B | 首个支持手机部署的端侧模型 | [查看报告](./researches/Step-GUIEdge/README.md) | [代码分析](./researches/Step-GUIEdge/code-analysis.md) |
| **Mobile-Agent** | 阿里通义 | 7B/32B | 多智能体协作框架，跨平台支持 | [查看报告](./researches/Mobile-Agent/README.md) | [代码分析](./researches/Mobile-Agent/code-analysis.md) |
| **MobiAgent** | 上海交大IPADS | 4B-8B | 可定制移动智能体系统，AgentRR加速 | [查看报告](./researches/MobiAgent/README.md) | [代码分析](./researches/MobiAgent/code-analysis.md) |

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

### 三、深度代码解构（DeepWiki 风格）

本项目对所有有开源代码的 GUI Agent 模型进行了类似 DeepWiki 的深度代码解构，包括：

- **项目结构分析**：完整的目录结构和模块划分
- **核心模块解读**：关键代码文件的详细注释
- **架构设计解析**：系统架构图和数据流图
- **API 接口文档**：动作空间和调用方式
- **使用示例**：快速开始和部署指南

| 模型 | GitHub 仓库 | 代码解构文档 |
|-----|------------|-------------|
| UI-TARS | [bytedance/UI-TARS](https://github.com/bytedance/UI-TARS) | [code-analysis.md](./researches/UI-TARS-7B/code-analysis.md) |
| GELab-Zero | [stepfun-ai/gelab-zero](https://github.com/stepfun-ai/gelab-zero) | [code-analysis.md](./researches/GELab-Zero/code-analysis.md) |
| MAI-UI | [Tongyi-MAI/MAI-UI](https://github.com/Tongyi-MAI/MAI-UI) | [code-analysis.md](./researches/MAI-UI/code-analysis.md) |
| AgentCPM-GUI | [OpenBMB/AgentCPM-GUI](https://github.com/OpenBMB/AgentCPM-GUI) | [code-analysis.md](./researches/AgentCPM-GUI/code-analysis.md) |
| AutoGLM | [zai-org/Open-AutoGLM](https://github.com/zai-org/Open-AutoGLM) | [06-source-code-analysis.md](./researches/autoglm/06-source-code-analysis.md) |
| GUI-Owl | [X-PLUG/MobileAgent](https://github.com/X-PLUG/MobileAgent) | [code-analysis.md](./researches/GUI-Owl/code-analysis.md) |
| Step-GUIEdge | [stepfun-ai/gelab-zero](https://github.com/stepfun-ai/gelab-zero) | [code-analysis.md](./researches/Step-GUIEdge/code-analysis.md) |
| MobiAgent | [IPADS-SAI/MobiAgent](https://github.com/IPADS-SAI/MobiAgent) | [code-analysis.md](./researches/MobiAgent/code-analysis.md) |

### 四、技术演示 PPT

本仓库还包含一份 28 页的技术演示 PPT，主题为"GUI 自主智能体技术深度调研"，采用国际化科技风格设计。

📂 **PPT 文件位置**: `./presentation/slides/`

## 🏗️ 项目结构

```
gui-agent-research/
├── README.md                    # 本文件
├── researches/                  # 调研报告目录
│   ├── UI-TARS-7B/             # UI-TARS-7B 模型调研
│   │   ├── README.md           # 调研报告
│   │   ├── code-analysis.md    # 深度代码解构
│   │   └── images/
│   ├── GELab-Zero/             # GELab-Zero 模型调研
│   │   ├── README.md
│   │   ├── code-analysis.md
│   │   └── images/
│   ├── MAI-UI/                 # MAI-UI 模型调研
│   │   ├── README.md
│   │   ├── code-analysis.md
│   │   └── images/
│   ├── AgentCPM-GUI/           # AgentCPM-GUI 模型调研
│   │   ├── README.md
│   │   ├── code-analysis.md
│   │   └── images/
│   ├── AutoGLM-Phone-9B/       # AutoGLM 模型调研
│   │   └── README.md
│   ├── GUI-Owl/                # GUI-Owl 模型调研
│   │   ├── README.md
│   │   ├── code-analysis.md
│   │   └── images/
│   ├── Step-GUIEdge/           # Step-GUIEdge 模型调研
│   │   ├── README.md
│   │   ├── code-analysis.md
│   │   └── images/
│   ├── MobiAgent/              # MobiAgent 模型调研
│   │   ├── README.md
│   │   ├── code-analysis.md
│   │   └── images/
│   ├── autoglm/                # AutoGLM 专题深度调研
│   │   ├── 01-overview.md
│   │   ├── 02-architecture.md
│   │   ├── 03-tech-stack.md
│   │   ├── 04-multimodal-model.md
│   │   ├── 05-planning-algorithm.md
│   │   ├── 06-source-code-analysis.md
│   │   ├── 07-api-design.md
│   │   ├── 08-performance-metrics.md
│   │   └── diagrams/           # Mermaid 架构图
│   ├── doubao/                 # 豆包手机专题深度调研
│   │   ├── 01-product-overview.md
│   │   ├── 02-hardware-integration.md
│   │   ├── 03-end-side-ai.md
│   │   ├── 04-cloud-collaboration.md
│   │   ├── 05-zte-contribution.md
│   │   ├── 06-comparison-with-autoglm.md
│   │   └── diagrams/
│   └── comparison/             # 横向对比分析
│       └── 00-comprehensive-comparison.md
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

### 代码架构特点总结

| 模型 | 架构模式 | 核心特点 |
|-----|---------|---------|
| UI-TARS | 单模型端到端 | 统一动作空间，坐标归一化 |
| GELab-Zero | MCP 协议 | GUI-MCP 标准化接口 |
| MAI-UI | 记忆增强 | 统一记忆模块，自进化数据管线 |
| AgentCPM-GUI | Schema 驱动 | JSON Schema 动作定义 |
| AutoGLM | 模块化 | 感知-规划-执行分离 |
| GUI-Owl | 多智能体 | Manager-Executor-Notetaker-Reflector |
| Step-GUIEdge | 端侧优化 | 轻量化，隐私保护 |
| MobiAgent | 多智能体+缓存 | AgentRR 加速，DAG 评测 |

## 📖 参考文献

1. [UI-TARS: Pioneering Automated GUI Interaction with Native Agents](https://arxiv.org/abs/2501.12326)
2. [AutoGLM: Autonomous Foundation Agents for GUIs](https://arxiv.org/abs/2411.00820)
3. [MAI-UI Technical Report: Real-World Centric Foundation GUI Agents](https://arxiv.org/abs/2512.22047)
4. [AgentCPM-GUI: Building Mobile-Use Agents with Reinforcement Fine-Tuning](https://arxiv.org/abs/2506.01391)
5. [Step-GUI Technical Report](https://arxiv.org/abs/2512.15431)
6. [GUI-Owl: Advancing Native GUI Agents with Unified Action Modeling](https://arxiv.org/abs/2507.00076)
7. [Mobile-Agent-v3: Foundational Agents for GUI Automation](https://arxiv.org/abs/2508.15144)

## 📜 许可证

本项目采用 MIT 许可证。

---

**如有问题或建议，欢迎提交 Issue 或 Pull Request！**
