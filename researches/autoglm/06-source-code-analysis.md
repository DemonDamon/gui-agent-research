# Open-AutoGLM 源码分析

**发布日期**: 2025年12月16日

**作者**: Damon Li

---

## 1. 概述

为了深入理解 AutoGLM 的工程实现，我们对其官方开源项目 **Open-AutoGLM** 的代码库进行了分析 [1]。该项目提供了一个完整的、可运行的 Android GUI 智能体框架，为开发者提供了宝贵的实践参考。本报告将从代码结构、核心逻辑和关键模块三个方面对该项目进行拆解。

## 2. 项目结构

Open-AutoGLM 的项目结构清晰，遵循了良好的模块化设计原则。核心代码位于 `phone_agent` 目录下，而 `main.py` 作为主入口负责协调各个模块。

![Open-AutoGLM 源码结构图](./diagrams/source-structure.png)
*图 1: Open-AutoGLM 源码结构图*

下表对关键目录和文件进行了说明：

| 路径 | 描述 |
| :--- | :--- |
| `main.py` | 项目的主入口 CLI。负责解析命令行参数、检查系统环境（如 ADB、设备连接）、初始化并运行 `PhoneAgent`。 |
| `phone_agent/agent.py` | 定义了核心的 `PhoneAgent` 类。这是整个智能体的总控制器，负责管理状态、调用模型、执行动作，并实现了主要的“感知-思考-行动”循环。 |
| `phone_agent/model/` | 负责与大型多模态模型 (LMM) API 进行交互。`client.py` 封装了 API 请求逻辑，而 `MessageBuilder` 则用于构建符合模型输入格式的 prompt。 |
| `phone_agent/actions/` | 定义了智能体可以执行的所有动作。`handler.py` 中的 `ActionHandler` 负责解析模型返回的动作 JSON，并将其分派给具体的 ADB 命令执行。 |
| `phone_agent/adb/` | 封装了所有与 Android 调试桥 (ADB) 相关的底层操作，如设备连接 (`connection.py`)、屏幕截图 (`screenshot.py`) 和用户输入模拟 (`input.py`)。 |
| `phone_agent/config/` | 存放所有配置信息，包括多语言的系统提示 (`prompts_en.py`, `prompts_zh.py`) 和支持的应用列表 (`apps.py`)。 |
| `examples/` | 提供了一些基础的使用示例，如 `basic_usage.py`，帮助用户快速上手。 |

## 3. 核心工作流程

通过对 `agent.py` 的分析，我们可以梳理出 Open-AutoGLM 的核心工作流程，这与我们在架构分析中描述的“感知-思考-行动”循环高度一致。

1.  **初始化**: `main.py` 根据命令行参数创建 `ModelConfig` 和 `AgentConfig`，并实例化 `PhoneAgent`。
2.  **任务开始**: 用户通过命令行或交互模式输入任务指令。`PhoneAgent.run()` 方法被调用。
3.  **感知 (Perceive)**: 在 `_execute_step()` 方法中，智能体首先通过 `adb.get_screenshot()` 捕获当前屏幕截图，并通过 `adb.get_current_app()` 获取前台应用信息。
4.  **思考 (Think)**: `MessageBuilder` 将用户指令、屏幕截图（Base64 编码）、当前应用信息和历史记录整合成一个完整的 prompt，然后通过 `model_client.request()` 发送给 LMM API。
5.  **决策 (Decide)**: LMM 返回一个包含 `<think>` 和 `<answer>` 标签的响应。`<think>` 标签内是模型的思考过程，而 `<answer>` 标签内是一个结构化的 JSON，定义了要执行的动作（如 `Tap`, `Type`, `Swipe` 等）。
6.  **行动 (Act)**: `ActionHandler.execute()` 方法解析这个 JSON，并调用 `adb` 模块中对应的函数来在设备上执行具体操作。
7.  **循环**: 步骤 3 到 6 会不断重复，直到模型返回一个 `finish` 动作或达到最大步数限制。

## 4. 关键模块分析

### 4.1. `PhoneAgent` 类

这是整个系统的中枢。它维护着一个 `_context` 列表，用于存储与模型的完整对话历史，这对于长程任务的成功至关重要。`run()` 和 `step()` 方法分别提供了全自动执行和单步调试两种模式，体现了良好的工程设计。

### 4.2. `ActionHandler`

该模块是模型决策与物理执行之间的桥梁。它定义了一系列智能体可执行的原子操作，如 `Launch`, `Tap`, `Type`, `Swipe`, `Back`, `Home` 等。特别值得注意的是，它还包含了 `Take_over` 动作，允许智能体在遇到困难时请求人类用户接管，以及 `finish` 动作，用于宣告任务完成。这种人机协作的设计是项目“可部署性”理念的体现。

### 4.3. `ADB` 模块

该模块将底层的 `adb` shell 命令封装成了易于调用的 Python 函数。例如，`screenshot.py` 中的 `get_screenshot()` 函数不仅执行截图命令，还会自动处理截图的拉取、删除和 Base64 编码，为上层模块提供了极大的便利。

## 5. 总结

Open-AutoGLM 的源码展示了一个设计精良、模块化、可扩展的 GUI 智能体框架。其代码结构清晰，核心逻辑明确，充分体现了 AutoGLM 论文中描述的设计思想。对于希望自研或深入理解 GUI Agent 技术的开发者来说，该项目是一个不可多得的学习资源。

---

### 参考文献

[1] ZAI-Org. (2024). *Open-AutoGLM*. GitHub Repository. [https://github.com/zai-org/Open-AutoGLM](https://github.com/zai-org/Open-AutoGLM)
