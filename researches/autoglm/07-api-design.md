> # AutoGLM API 设计
> 
> **发布日期**: 2025年12月16日
> 
> **作者**: Damon Li
> 
> ---
> 
> ## 1. 概述
> 
> Open-AutoGLM 框架通过一个清晰、标准的 API 与后端的大型多模态模型 (LMM) 进行通信。这个 API 设计遵循了 OpenAI 的 `chat/completions` 接口规范，这使得该框架具有良好的兼容性，可以方便地替换或接入任何遵循此规范的模型服务，无论是本地部署的模型还是云端 API [1]。
> 
> 本报告将详细分析该 API 的交互流程、数据格式以及其在整个系统中的作用。
> 
> ## 2. API 交互流程
> 
> API 的交互是一个典型的客户端-服务器请求-响应模式。客户端（即 `Open-AutoGLM` 框架）负责收集上下文信息并构建请求，服务器端（即 LMM 后端）则负责处理请求并返回决策。
> 
> ![AutoGLM API 交互流程图](./diagrams/api-interaction.png)
> *图 1: AutoGLM API 交互流程图*
> 
> 整个流程可以分解为以下几个步骤：
> 
> 1.  **构建 Prompt**: `PhoneAgent` 在每个决策步骤中，会调用 `MessageBuilder` 来构建一个包含多条消息的列表。这个列表通常包括：
>     *   一条 `system` 消息，定义了智能体的角色、能力和输出格式要求。
>     *   多条 `user` 和 `assistant` 消息，构成了到目前为止的完整对话历史。
>     *   最新的一条 `user` 消息，其中包含了当前的屏幕截图（以 Base64 格式编码）和任务指令。
> 
> 2.  **发送请求**: `ModelClient` 将构建好的消息列表作为请求体，向配置的 API Endpoint (默认为 `http://localhost:8000/v1/chat/completions`) 发送一个 HTTP POST 请求。
> 
> 3.  **模型处理**: 服务器端接收到请求后，LMM 会处理其中的文本和图像信息，进行“思考”，并决定下一步要执行的动作。
> 
> 4.  **返回响应**: LMM 生成一个包含思考过程和具体动作的响应。这个响应被格式化为一个 JSON 对象并返回给客户端。
> 
> 5.  **解析与执行**: `ModelClient` 接收并解析这个 JSON 响应，提取出动作部分，然后交由 `ActionHandler` 去执行。
> 
> ## 3. API 数据格式
> 
> ### 3.1. 请求格式
> 
> 请求体遵循 OpenAI 的 `ChatCompletion` 格式，核心是 `messages` 字段，它是一个消息对象数组。一个典型的 `user` 消息对象结构如下：
> 
> ```json
> {
>   "role": "user",
>   "content": [
>     {
>       "type": "text",
>       "text": "这是任务指令和屏幕信息。"
>     },
>     {
>       "type": "image_url",
>       "image_url": {
>         "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
>       }
>     }
>   ]
> }
> ```
> 
> ### 3.2. 响应格式
> 
> 模型被要求以特定的格式返回响应，通常包含 `<think>` 和 `<answer>` 两个部分。`Open-AutoGLM` 的代码会解析这个响应字符串，提取出 `answer` 部分的 JSON 内容。
> 
> 一个典型的成功响应中的 `answer` JSON 结构如下，定义了一个“点击”动作：
> 
> ```json
> {
>   "action": "Tap",
>   "args": {
>     "area": [100, 250] 
>   },
>   "thought": "我需要点击这个区域来进入下一步。"
> }
> ```
> 
> | 字段 | 描述 |
> | :--- | :--- |
> | `action` | 必需。要执行的动作名称，如 `Tap`, `Type`, `Swipe`, `Finish` 等。 |
> | `args` | 可选。执行该动作所需的参数。例如，`Tap` 需要 `area`，`Type` 需要 `text`。 |
> | `thought` | 可选。模型在做出该决策时的思考过程，用于调试和日志记录。 |
> 
> ## 4. 设计优势与意义
> 
> 采用标准化的 API 设计为 Open-AutoGLM 带来了多重优势：
> 
> - **解耦与模块化**: 将智能体逻辑与模型实现完全解耦。开发者可以专注于智能体的行为和流程，而无需关心底层模型的具体实现。
> - **灵活性与可扩展性**: 可以轻松切换不同的模型后端。只需修改 `base_url` 和 `model_name` 等配置，就可以从本地的 GLM-4-9B 切换到 OpenAI 的 GPT-4V 或其他任何兼容的 API 服务。
> - **易于调试**: 标准的请求和响应格式使得调试过程变得简单。开发者可以轻易地检查发送给模型的输入和模型返回的输出，从而快速定位问题。
> 
> 综上所述，Open-AutoGLM 的 API 设计是其框架成功的关键因素之一，它为构建一个健壮、灵活且易于维护的 GUI 智能体系统奠定了坚实的基础。
> 
> ---
> 
> ### 参考文献
> 
> [1] ZAI-Org. (2024). *Open-AutoGLM*. GitHub Repository. [https://github.com/zai-org/Open-AutoGLM](https://github.com/zai-org/Open-AutoGLM)
