# GELab-Zero 调研报告

## 1. 模型概述

*   **模型名称**: GELab-Zero
*   **开发者/机构**: 阶跃星辰 (StepFun)
*   **发布时间**: 2025年11月
*   **核心定位**: 端侧轻量级GUI智能体，支持本地部署与隐私保护。

## 2. 论文信息

*   **论文标题**: Step-GUI Technical Report
*   **arXiv 链接**: https://arxiv.org/abs/2512.15431
*   **摘要（英文）**: 
> Recent advances in multimodal large language models unlock unprecedented opportunities for GUI automation. However, a fundamental challenge remains: how to efficiently acquire high-quality training data while maintaining annotation reliability? We introduce a self-evolving training pipeline powered by the Calibrated Step Reward System, which converts model-generated trajectories into reliable training signals through trajectory-level calibration, achieving >90% annotation accuracy with 10-100x lower cost. Leveraging this pipeline, we introduce Step-GUI, a family of models (4B/8B) that achieves state-of-the-art GUI performance (8B: 80.2% AndroidWorld, 48.5% OSWorld, 62.6% ScreenShot-Pro) while maintaining robust general capabilities. As GUI agent capabilities improve, practical deployment demands standardized interfaces across heterogeneous devices while protecting user privacy. To this end, we propose GUI-MCP, the first Model Context Protocol for GUI automation with hierarchical architecture that combines low-level atomic operations and high-level task delegation to local specialist models, enabling high-privacy execution where sensitive data stays on-device. Finally, to assess whether agents can handle authentic everyday usage, we introduce AndroidDaily, a benchmark grounded in real-world mobile usage patterns with 3146 static actions and 235 end-to-end tasks across high-frequency daily scenarios (8B: static 89.91%, end-to-end 52.50%). Our work advances the development of practical GUI agents and demonstrates strong potential for real-world deployment in everyday digital interactions.

*   **主要贡献**: 
    *   提出了一种自主演进的训练流程，利用校准步骤奖励系统，高效获取高质量训练数据。
    *   发布了Step-GUI模型家族（4B/8B），在多个GUI基准测试中取得领先性能。
    *   提出了首个用于GUI自动化的模型上下文协议（GUI-MCP），支持本地化和隐私保护。
    *   构建了面向真实世界移动使用模式的基准测试AndroidDaily。

## 3. 开源代码

*   **GitHub 仓库地址**: https://github.com/stepfun-ai/gelab-zero
*   **Star 数量**: 1.8k
*   **许可证**: MIT License
*   **主要功能模块**: copilot_agent_client, copilot_agent_server, copilot_front_end, mcp_server

## 4. 技术架构

*   **模型架构**: GELab-Zero-4B-preview基于Qwen3-VL-4B-Instruct，并采用自主演进的训练流程和模型上下文协议（GUI-MCP）。
*   **参数规模**: 4B (另有8B版本)
*   **训练数据**: 使用名为AndroidDaily的新基准进行训练，该基准包含3146个静态动作和235个端到端任务。
*   **核心技术创新**: 
    *   **自主演进训练流程**: 通过校准步骤奖励系统，将模型生成的轨迹转化为可靠的训练信号。
    *   **模型上下文协议 (GUI-MCP)**: 一种分层架构，结合了低级原子操作和高级任务委派，实现了高隐私执行。

## 5. 性能评测

*   **AndroidWorld**: 80.2% (8B model)
*   **OSWorld**: 48.5% (8B model)
*   **ScreenShot-Pro**: 62.6% (8B model)
*   **AndroidDaily**: 静态任务89.91%，端到端任务52.50% (8B model)

## 6. 适用场景

*   **支持的平台**: 移动端 (Android), 桌面端 (macOS, Windows, Linux for agent execution)
*   **典型应用场景**: 推荐、实用任务（如领取补贴、查询地铁）、复杂任务（如多商品购物、信息检索、条件搜索、在线测验）

## 7. 优势与局限

*   **优势**:
    *   完整的“模型+基础设施”开源，易于部署。
    *   支持本地化运行，保护用户隐私。
    *   创新的自主演进训练流程，降低了数据标注成本。
    *   通过GUI-MCP协议解决了移动生态系统的碎片化问题。
*   **局限**:
    *   目前公开的信息中未明确提及模型的局限性。

## 8. 相关图片

*   架构图、性能对比图等图片可在GitHub仓库和技术报告中找到。
